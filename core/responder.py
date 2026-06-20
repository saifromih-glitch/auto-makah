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
        self.router = HybridRouter()

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
            system = """أنت خبير في منصة Auto Makah. قدم تحليلاً عميقاً واحترافياً.
استخدم هيكل: ١. التحليل ٢. التوصيات ٣. الخطوات العملية.
أجب بالعربية الفصحى مباشرة — بدون مقدمات."""
        else:
            system = "أنت Auto Makah — أجب مباشرة بدون مقدمات."

        resp = await self.router.call(message, system_prompt=system, max_tokens=2000)
        if resp.ok and resp.text:
            return resp.text
        return "عذراً، النماذج مشغولة حالياً."


# Global responder
responder = IntelligentResponder()
