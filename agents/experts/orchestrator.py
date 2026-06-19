"""
Expert Orchestrator — registers domain experts, dispatches questions, and runs
round-table deliberation to produce a single consensus answer.

Pure orchestration logic — no external API calls.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from auto_makah.agents.experts.profiles import ExpertProfile


# ── Data structures ────────────────────────────────────────────────────


@dataclass
class Expert:
    """A registered expert with its profile and execution hook."""

    name: str
    domain: str
    system_prompt: str
    tools: List[str] = field(default_factory=list)
    # Callable that accepts a question (str) and returns an answer (str).
    # Typically an async LLM call; here it is swappable / mockable.
    handler: Optional[Callable[..., Any]] = None


@dataclass
class ExpertOutput:
    """Result from a single expert after answering a question."""

    expert_name: str
    domain: str
    question: str
    answer: str
    confidence: float = 1.0  # 0.0 – 1.0, set by the expert or orchestrator


@dataclass
class DeliberationResult:
    """Final output after round-table deliberation."""

    consensus: str
    individual_outputs: List[ExpertOutput] = field(default_factory=list)
    dissenting_opinions: List[str] = field(default_factory=list)
    confidence: float = 1.0


# ── Orchestrator ───────────────────────────────────────────────────────


class ExpertOrchestrator:
    """Register, dispatch, and deliberate among domain experts.

    Typical usage::

        orchestrator = ExpertOrchestrator()
        orchestrator.register_from_profile(profiles.ACCOUNTING_EXPERT, handler=my_llm_fn)
        orchestrator.register_from_profile(profiles.LEGAL_EXPERT, handler=my_llm_fn)

        outputs = await orchestrator.dispatch(
            "Should I form an LLC or a joint-stock company in Saudi Arabia?",
            required_domains=["legal", "accounting"],
        )
        result = await orchestrator.deliberate(outputs)
        print(result.consensus)
    """

    def __init__(self) -> None:
        self._experts: Dict[str, Expert] = {}

    # Register ...........................................................

    def register_expert(
        self,
        name: str,
        domain: str,
        system_prompt: str,
        tools: Optional[List[str]] = None,
        handler: Optional[Callable[..., Any]] = None,
    ) -> Expert:
        """Register a single expert by hand.

        Args:
            name: Unique key for the expert (e.g. ``"legal_expert"``).
            domain: Primary domain (``"legal"``, ``"accounting"``, …).
            system_prompt: Role instructions fed to the expert's LLM.
            tools: Tool names available to the expert (default empty list).
            handler: Async callable ``(question: str, **kwargs) -> str``.

        Returns:
            The newly created ``Expert`` instance.

        Raises:
            ValueError: If *name* is already registered.
        """
        if name in self._experts:
            raise ValueError(f"Expert '{name}' is already registered.")
        expert = Expert(
            name=name,
            domain=domain,
            system_prompt=system_prompt,
            tools=tools or [],
            handler=handler,
        )
        self._experts[name] = expert
        return expert

    def register_from_profile(
        self,
        profile: ExpertProfile,
        handler: Optional[Callable[..., Any]] = None,
    ) -> Expert:
        """Register an expert from an ``ExpertProfile`` dict.

        Convenience wrapper around ``register_expert``.
        """
        return self.register_expert(
            name=profile["name"],
            domain=profile["domain"],
            system_prompt=profile["system_prompt"],
            tools=profile.get("tools", []),
            handler=handler,
        )

    def unregister(self, name: str) -> None:
        """Remove a previously registered expert."""
        self._experts.pop(name, None)

    def get_expert(self, name: str) -> Optional[Expert]:
        """Return an expert by name, or ``None`` if not found."""
        return self._experts.get(name)

    def list_experts(self) -> List[Expert]:
        """Return all registered experts (shallow copy)."""
        return list(self._experts.values())

    # Dispatch ..........................................................

    async def _run_expert(self, expert: Expert, question: str) -> ExpertOutput:
        """Call a single expert's handler and wrap the result."""
        if expert.handler is None:
            return ExpertOutput(
                expert_name=expert.name,
                domain=expert.domain,
                question=question,
                answer=f"[{expert.name}] No handler registered — cannot answer.",
                confidence=0.0,
            )

        try:
            answer = await expert.handler(question, system_prompt=expert.system_prompt)
            return ExpertOutput(
                expert_name=expert.name,
                domain=expert.domain,
                question=question,
                answer=str(answer),
                confidence=0.9,
            )
        except Exception as exc:
            return ExpertOutput(
                expert_name=expert.name,
                domain=expert.domain,
                question=question,
                answer=f"[{expert.name}] Error: {exc}",
                confidence=0.0,
            )

    async def dispatch(
        self,
        question: str,
        required_domains: Optional[Sequence[str]] = None,
        required_experts: Optional[Sequence[str]] = None,
    ) -> List[ExpertOutput]:
        """Dispatch a question to relevant experts in parallel.

        Experts are selected by *required_domains* (matches ``expert.domain``)
        **or** *required_experts* (matches ``expert.name``).  If both are
        ``None``, **all** registered experts are consulted.

        Experts run concurrently via ``asyncio.gather``.

        Args:
            question: The user's question.
            required_domains: Limit to experts whose ``domain`` is in this list.
            required_experts: Limit to experts whose ``name`` is in this list.

        Returns:
            A list of ``ExpertOutput``, one per selected expert.
        """
        if required_domains is None and required_experts is None:
            selected = list(self._experts.values())
        else:
            selected = []
            for expert in self._experts.values():
                if required_domains and expert.domain in required_domains:
                    selected.append(expert)
                elif required_experts and expert.name in required_experts:
                    selected.append(expert)

        tasks = [self._run_expert(expert, question) for expert in selected]
        return list(await asyncio.gather(*tasks))

    # Deliberation ......................................................

    @staticmethod
    def _build_deliberation_prompt(outputs: List[ExpertOutput]) -> str:
        """Build a deliberation prompt from expert outputs (for use with a lead expert)."""
        lines: List[str] = [
            "━━━ Round-Table Deliberation ━━━",
            "",
            "You are the lead orchestrator. Below are answers from domain experts. ",
            "Synthesize them into a single, coherent, evidence-anchored consensus. ",
            "If experts disagree, note the disagreement and explain the trade-off. ",
            "If one expert's view is clearly more applicable, say so and explain why.",
            "",
        ]
        for i, out in enumerate(outputs, 1):
            lines.append(f"── Expert {i}: {out.expert_name} ({out.domain})")
            lines.append(out.answer)
            lines.append("")
        return "\n".join(lines)

    async def deliberate(
        self,
        outputs: List[ExpertOutput],
        lead_expert_name: Optional[str] = None,
    ) -> DeliberationResult:
        """Run round-table deliberation: the lead expert reviews all outputs
        and produces a final consensus answer.

        If *lead_expert_name* is provided and that expert has a handler,
        the handler is called with the deliberation prompt.  Otherwise a
        heuristic merge is performed locally (no LLM call).

        Args:
            outputs: Expert outputs from a prior ``dispatch`` call.
            lead_expert_name: Name of the expert to act as lead synthesizer.

        Returns:
            A ``DeliberationResult`` with the consensus answer.
        """
        if not outputs:
            return DeliberationResult(
                consensus="No expert outputs to deliberate on.",
                confidence=0.0,
            )

        # ── Try lead-expert LLM path ──
        if lead_expert_name:
            lead = self._experts.get(lead_expert_name)
            if lead and lead.handler:
                prompt = self._build_deliberation_prompt(outputs)
                try:
                    answer = await lead.handler(prompt, system_prompt=lead.system_prompt)
                    return DeliberationResult(
                        consensus=str(answer),
                        individual_outputs=outputs,
                        confidence=0.85,
                    )
                except Exception:
                    pass  # fall through to heuristic merge

        # ── Heuristic merge (no LLM) ──
        merged = self._heuristic_merge(outputs)
        return merged

    @staticmethod
    def _heuristic_merge(outputs: List[ExpertOutput]) -> DeliberationResult:
        """Fallback: merge expert outputs with simple heuristics.

        * Highest-confidence answer becomes the lead narrative.
        * Dissenting answers are appended as notes.
        """
        if len(outputs) == 1:
            return DeliberationResult(
                consensus=outputs[0].answer,
                individual_outputs=outputs,
                confidence=outputs[0].confidence,
            )

        # Sort by confidence desc
        sorted_outputs = sorted(outputs, key=lambda o: o.confidence, reverse=True)
        lead = sorted_outputs[0]
        dissenters = sorted_outputs[1:]

        consensus_parts = [
            f"【{lead.expert_name} — {lead.domain}】",
            lead.answer,
        ]

        if dissenters:
            consensus_parts.append("\n── Dissenting / Supplementary Views ──\n")
            for d in dissenters:
                consensus_parts.append(f"▸ {d.expert_name} ({d.domain}): {d.answer}")
                consensus_parts.append("")

        avg_confidence = sum(o.confidence for o in outputs) / len(outputs)

        return DeliberationResult(
            consensus="\n".join(consensus_parts),
            individual_outputs=outputs,
            confidence=round(avg_confidence, 2),
        )


__all__ = [
    "Expert",
    "ExpertOutput",
    "DeliberationResult",
    "ExpertOrchestrator",
]
