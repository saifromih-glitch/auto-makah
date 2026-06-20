# 🕋 Auto Makah — Intelligent Response Engine
# Routes complex questions through the Expert Swarm

import asyncio
from typing import Dict, Any, Optional

from core.connectors import HybridRouter, ModelResponse
from agents.swarm import SwarmOrchestrator, route_to_expert, AgentTask, AgentResult
from agents.experts.orchestrator import ExpertOrchestrator, Expert, ExpertOutput
from agents.experts.profiles import EXPERT_PROFILES
from knowledge.search import search_engine
from knowledge.trainer import train_expert_prompt
from memory.store import memory
from memory.recall import injector


class IntelligentResponder:
    """Decides how to answer: simple text or expert deliberation."""

    def __init__(self):
        self.orch = ExpertOrchestrator()
        self.router = HybridRouter()
        self._init_experts()

    def _init_experts(self):
        """Load and train all experts."""
        for name, profile in EXPERT_PROFILES.items():
            domain = profile.get("domain", "general")
            trained = train_expert_prompt(domain)
            p = dict(profile)
            if trained:
                p["system_prompt"] = p.get("system_prompt", "") + "\n\n" + trained
            self.orch.register_from_profile(p)

    def _needs_experts(self, message: str) -> bool:
        """Determine if this question needs expert deliberation."""
        expert_triggers = [
            "حلل", "خطة", "استراتيجية", "زكاة", "ضريبة",
            "نظام", "قانون", "ميزانية", "تكاليف", "تعادل",
            "تسويق", "نمو", "رواتب", "تأمينات", "موظفين",
            "هيدروليك", "ورشة", "تصنيع", "معدات",
            "analyze", "strategy", "plan", "calculate",
        ]
        return any(t in message.lower() for t in expert_triggers) or len(message) > 150

    async def respond(self, message: str, user_id: str, session_id: str) -> str:
        """Smart response: simple or expert-based."""

        if self._needs_experts(message):
            return await self._expert_response(message, user_id, session_id)
        return await self._simple_response(message, user_id, session_id)

    async def _simple_response(self, message: str, user_id: str, session_id: str) -> str:
        """Quick text response from primary model."""
        context = injector.inject(message, user_id=user_id, session_id=session_id)
        system = "أنت Auto Makah — أجب مباشرة بدون مقدمات."
        if context:
            system += f"\n\n[Context]\n{context}"

        resp = await self.router.call(message, system_prompt=system, max_tokens=1000)
        return resp.text if resp.ok else "عذراً، النماذج مشغولة."

    async def _expert_response(self, message: str, user_id: str, session_id: str) -> str:
        """Route through expert swarm with deliberation."""

        experts = self.orch.list_experts()
        matched = route_to_expert(message, experts)

        if not matched:
            return await self._simple_response(message, user_id, session_id)

        # Step 1: Dispatch to matched experts in parallel
        outputs = await self.orch.dispatch(
            message,
            required_experts=[e.name for e in matched]
        )

        if not outputs:
            return await self._simple_response(message, user_id, session_id)

        # Step 2: Deliberate — lead expert synthesizes
        result = self.orch.deliberate(outputs)

        # Step 3: Format the final answer
        response_parts = []

        if result.consensus:
            response_parts.append(result.consensus)

        # Add expert attribution
        if result.contributing_experts:
            names = ", ".join(result.contributing_experts)
            response_parts.append(f"\n\n⚡ تحليل: {names}")

        if result.dissenting_views:
            response_parts.append(f"\n⚠️ رأي مختلف: {result.dissenting_views[:300]}")

        if result.confidence:
            response_parts.append(f"\n🎯 مستوى الثقة: {result.confidence}")

        return "\n".join(response_parts) if response_parts else "لم يتم التوصل إلى نتيجة."


# Global responder
responder = IntelligentResponder()
