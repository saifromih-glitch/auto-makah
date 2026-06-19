# ═══════════════════════════════════════════
# 🕋 Auto Makah — Context Injector
# ═══════════════════════════════════════════

from typing import Dict, Any
from .store import memory
from knowledge.search import search_engine


class ContextInjector:
    """Injects relevant context into agent prompts before execution."""

    def __init__(self):
        self.memory = memory
        self.search = search_engine

    def inject(self, message: str, user_id: str = None, session_id: str = None) -> str:
        """Build a context injection string."""
        parts = []

        # 1. Memory context
        if user_id and session_id:
            mem_context = self.memory.compile_context(user_id, session_id)
            if mem_context:
                parts.append(mem_context)

        # 2. Knowledge context (domain-specific)
        knowledge = self.search.search_and_compile(message, max_chars=2000)
        if knowledge:
            parts.append(f"[Domain Knowledge]\n{knowledge}")

        return "\n\n".join(parts) if parts else ""

    def for_agent(self, message: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Return structured context for agent execution."""
        return {
            "message": message,
            "memory_available": bool(user_id and session_id and self.memory.get_all_facts(user_id)),
            "knowledge_domains": self.search.domain_detect(message),
            "injected_context": self.inject(message, user_id, session_id),
        }


# Global injector
injector = ContextInjector()
