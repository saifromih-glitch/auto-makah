"""
Swarm Orchestrator — lightweight parallel-agent execution, expert routing, and
round-table deliberation for the Auto Makah platform.

Pure orchestration logic — no external API calls.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from auto_makah.agents.experts.orchestrator import (
    DeliberationResult,
    Expert,
    ExpertOrchestrator,
    ExpertOutput,
)

# ── Type aliases ───────────────────────────────────────────────────────

AgentFn = Callable[..., Any]  # async callable that processes a message

# ── Keyword → domain routing table ─────────────────────────────────────

_ROUTING_TABLE: Dict[str, List[str]] = {
    # ── Accounting / Finance ──
    "accounting": ["حسابات", "ميزانية", "تسوية", "إهلاك", "تدفق نقدي", "قائمة دخل",
                   "ميزان مراجعة", "ضريبة", "زكاة", "IFRS", "SOCPA", "محاسبة",
                   "budget", "balance sheet", "cash flow", "income statement",
                   "depreciation", "amortization", "tax", "vat", "zakat", "audit"],
    # ── Legal ──
    "legal": ["قانون", "نظام", "لائحة", "مخالفة", "عقد", "شرط جزائي", "محكمة",
              "دعوى", "ترخيص", "سجل تجاري", "عمال", "عمل", "تأمينات", "GOSI",
              "نطاقات", "مكتب العمل", "تظلم", "law", "regulation", "contract",
              "litigation", "compliance", "license", "permit"],
    # ── Marketing / Growth ──
    "marketing": ["تسويق", "حملة", "إعلان", "سوق", "عملاء", "مستخدمين", "نمو",
                  "AARRR", "GSTIC", "funnel", "conversion", "SEO", "content",
                  "brand", "social media", "سوشيال ميديا", "حصة سوقية", "منافس"],
    # ── Engineering ──
    "engineering": ["هيدروليك", "ميكانيكا", "تصنيع", "CNC", "لحام", "خراطة",
                    "سباكة", "solidworks", "CAD", "DFM", "ورشة", "مادة",
                    "hydraulic", "machining", "welding", "lathe", "workshop",
                    "manufacturing", "tolerance", "material"],
    # ── HR ──
    "hr": ["موظف", "راتب", "توظيف", "تدريب", "أداء", "تقييم", "مغادرة",
           "إجازة", "سعودة", "نطاقات", "تأمين اجتماعي", "شؤون موظفين",
           "HR", "people", "payroll", "hiring", "onboarding", "turnover",
           "performance", "employee", "recruitment"],
    # ── Stock / Finance advanced ──
    "finance": ["سهم", "تداول", "محفظة", "مؤشر", "تاسي", "TASI", "DCF",
                "ربحية", "P/E", "stock", "equity", "dividend", "EPS",
                "technical analysis", "تحليل فني", "chart", "شموع"],
    # ── Strategy / Vision 2030 ──
    "strategy": ["رؤية 2030", "PIF", "نيوم", "قدية", "روشن", "استراتيجية",
                 "منتج", "MVP", "JTBD", "نموذج عمل", "business model",
                 "جدوى", "feasibility", "vision 2030", "giga-project"],
}

# Compile patterns once
_COMPILED_TABLE: Dict[str, List[re.Pattern[str]]] = {
    domain: [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
    for domain, keywords in _ROUTING_TABLE.items()
}


# ── Data structures ────────────────────────────────────────────────────


@dataclass
class AgentTask:
    """Represents a dispatched agent task."""

    agent_name: str
    agent_fn: AgentFn
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from a single agent execution."""

    agent_name: str
    output: Any
    error: Optional[str] = None
    success: bool = True

    @property
    def is_ok(self) -> bool:
        """True if the agent completed without error."""
        return self.success and self.error is None


# ── Routing helpers ─────────────────────────────────────────────────────


def _score_domain(message: str, domain: str) -> float:
    """Score how well *message* matches a *domain* based on keyword hits."""
    patterns = _COMPILED_TABLE.get(domain, [])
    if not patterns:
        return 0.0
    hits = sum(1 for p in patterns if p.search(message))
    return hits / len(patterns)


def route_to_expert(
    message: str,
    experts: Sequence[Expert],
    threshold: float = 0.10,
    max_experts: int = 4,
) -> List[Expert]:
    """Auto-route a message to the most relevant experts.

    Detection works by scoring each expert's domain against a keyword
    table (Arabic + English).  Experts whose domain-score exceeds
    *threshold* are selected, capped at *max_experts* (highest score first).

    If no domain scores above the threshold, a default set of generalist
    experts (accounting + legal) is returned.

    Args:
        message: The user's message / question.
        experts: All available experts (e.g. from ``ExpertOrchestrator``).
        threshold: Minimum domain hit ratio (0.0 – 1.0) to qualify.
        max_experts: Maximum number of experts to route to.

    Returns:
        Selected experts (never empty).
    """
    scored: List[Tuple[Expert, float]] = []
    for expert in experts:
        score = _score_domain(message, expert.domain)
        if score >= threshold:
            scored.append((expert, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    selected = [expert for expert, _ in scored[:max_experts]]

    if not selected:
        # Fallback: return legal + accounting as default generalists
        defaults = [e for e in experts if e.domain in ("legal", "accounting")]
        if defaults:
            return defaults[:max_experts]
        # Ultimate fallback: first expert
        if experts:
            return [experts[0]]

    return selected


# ── Swarm Orchestrator ─────────────────────────────────────────────────


class SwarmOrchestrator:
    """Orchestrate multiple async agents in parallel, collect results,
    route questions to domain experts, and run round-table deliberation.

    Typical usage::

        swarm = SwarmOrchestrator(max_parallel=4)

        # Execute multiple agents in parallel
        tasks = [AgentTask("agent1", my_agent_fn, ("hello",))]
        results = await swarm.execute_parallel(tasks)
        for r in results:
            print(r.output)

        # Route a message then deliberate
        matched = route_to_expert("What tax do I owe?", orchestrator.list_experts())
        outputs = await orchestrator.dispatch("What tax do I owe?", required_experts=[e.name for e in matched])
        final = await orchestrator.deliberate(outputs)
        print(final.consensus)
    """

    def __init__(self, max_parallel: int = 4) -> None:
        if max_parallel < 1:
            raise ValueError("max_parallel must be >= 1")
        self.max_parallel = max_parallel
        self._expert_orchestrator = ExpertOrchestrator()

    # ── Expert orchestrator passthrough ──

    @property
    def expert_orchestrator(self) -> ExpertOrchestrator:
        """The underlying ``ExpertOrchestrator`` instance."""
        return self._expert_orchestrator

    # ── Parallel execution ──

    @staticmethod
    async def _safe_run(task: AgentTask) -> AgentResult:
        """Execute a single agent task, capturing errors."""
        try:
            # Support both sync and async callables
            result = task.agent_fn(*task.args, **task.kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return AgentResult(agent_name=task.agent_name, output=result)
        except Exception as exc:
            return AgentResult(
                agent_name=task.agent_name,
                output=None,
                error=str(exc),
                success=False,
            )

    async def _run_batch(self, batch: List[AgentTask]) -> List[AgentResult]:
        """Run a single batch of up to max_parallel tasks concurrently."""
        coros = [self._safe_run(task) for task in batch]
        return list(await asyncio.gather(*coros))

    async def execute_parallel(
        self,
        tasks: Sequence[AgentTask],
    ) -> List[AgentResult]:
        """Execute agent tasks in parallel, respecting ``max_parallel``.

        Tasks are batched into groups of at most ``max_parallel`` and
        each batch runs via ``asyncio.gather``.  This limits concurrency
        while still running as many as allowed at once.

        Args:
            tasks: Sequence of ``AgentTask`` descriptors.

        Returns:
            List of ``AgentResult``, one per task (preserving input order).
        """
        if not tasks:
            return []

        all_results: List[AgentResult] = []
        task_list = list(tasks)

        for i in range(0, len(task_list), self.max_parallel):
            batch = task_list[i : i + self.max_parallel]
            batch_results = await self._run_batch(batch)
            all_results.extend(batch_results)

        return all_results

    # ── Result aggregation ──

    @staticmethod
    def collect_results(
        results: Sequence[AgentResult],
    ) -> Dict[str, Any]:
        """Aggregate a list of ``AgentResult`` into a summary dict.

        Returns::

            {
                "successes": [result, ...],    # all ok results
                "failures": [result, ...],     # errored results
                "success_rate": 0.75,           # fraction of successes
                "all_outputs": [str, ...],      # output strings
                "all_errors": [str, ...],       # error messages
            }
        """
        successes = [r for r in results if r.is_ok]
        failures = [r for r in results if not r.is_ok]
        total = len(results)

        return {
            "successes": successes,
            "failures": failures,
            "success_rate": len(successes) / total if total else 0.0,
            "all_outputs": [str(r.output) for r in results if r.output is not None],
            "all_errors": [r.error for r in results if r.error],
        }

    # ── Route + dispatch + deliberate combined ──

    async def roundtable_deliberation(
        self,
        message: str,
        experts: Optional[Sequence[Expert]] = None,
        threshold: float = 0.10,
        lead_expert_name: Optional[str] = None,
    ) -> DeliberationResult:
        """Full pipeline: route → dispatch → deliberate.

        1. Auto-route *message* to relevant experts using keyword matching.
        2. Dispatch the message to those experts in parallel.
        3. Run round-table deliberation to produce a consensus answer.

        Args:
            message: The user's question / message.
            experts: Expert pool (defaults to experts registered in the
                     internal ``ExpertOrchestrator``).
            threshold: Keyword hit threshold for auto-routing.
            lead_expert_name: Name of the expert to act as lead synthesizer
                              during deliberation.

        Returns:
            ``DeliberationResult`` with consensus and individual outputs.
        """
        if experts is None:
            experts = self._expert_orchestrator.list_experts()

        if not experts:
            return DeliberationResult(
                consensus="No experts available.",
                confidence=0.0,
            )

        # Step 1 — Route
        matched = route_to_expert(message, experts, threshold=threshold)
        if not matched:
            return DeliberationResult(
                consensus="No suitable expert matched the query.",
                confidence=0.0,
            )

        # Step 2 — Dispatch
        outputs = await self._expert_orchestrator.dispatch(
            message,
            required_experts=[e.name for e in matched],
        )

        # Step 3 — Deliberate
        return await self._expert_orchestrator.deliberate(
            outputs,
            lead_expert_name=lead_expert_name,
        )


__all__ = [
    "AgentTask",
    "AgentResult",
    "AgentFn",
    "route_to_expert",
    "SwarmOrchestrator",
]
