# ═══════════════════════════════════════════
# 🕋 Auto Makah — Memory System
# ═══════════════════════════════════════════

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class MemoryStore:
    """Session and user memory — short-term and long-term."""

    def __init__(self, max_short_term: int = 20):
        self.max_short_term = max_short_term
        self._short_term: Dict[str, List[Dict]] = {}  # session_id → messages
        self._long_term: Dict[str, Dict[str, Any]] = {}  # user_id → facts
        self._conversation_count: Dict[str, int] = {}  # session_id → count

    # ─── Short-term (conversation window) ───

    def remember(self, session_id: str, role: str, content: str):
        """Add message to short-term memory."""
        self._short_term.setdefault(session_id, []).append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self._conversation_count[session_id] = self._conversation_count.get(session_id, 0) + 1

        # Keep only most recent
        if len(self._short_term[session_id]) > self.max_short_term:
            self._short_term[session_id] = self._short_term[session_id][-self.max_short_term:]

    def recall(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history."""
        history = self._short_term.get(session_id, [])
        return history[-limit:] if history else []

    def clear_session(self, session_id: str):
        """Clear short-term memory for a session."""
        self._short_term.pop(session_id, None)
        self._conversation_count.pop(session_id, None)

    # ─── Long-term (user facts) ───

    def save_fact(self, user_id: str, key: str, value: Any):
        """Save a fact about a user."""
        self._long_term.setdefault(user_id, {})[key] = value

    def get_fact(self, user_id: str, key: str) -> Optional[Any]:
        return self._long_term.get(user_id, {}).get(key)

    def get_all_facts(self, user_id: str) -> Dict[str, Any]:
        return self._long_term.get(user_id, {})

    def compile_context(self, user_id: str, session_id: str) -> str:
        """Compile memory into injectable context string."""
        parts = []

        # User facts
        facts = self.get_all_facts(user_id)
        if facts:
            parts.append("[User Memory]")
            for k, v in facts.items():
                parts.append(f"  {k}: {v}")

        # Recent conversation
        history = self.recall(session_id, limit=6)
        if history:
            parts.append("[Recent Conversation]")
            for msg in history:
                role_label = "User" if msg["role"] == "user" else "Agent"
                parts.append(f"  {role_label}: {msg['content'][:200]}")

        return "\n".join(parts) if parts else ""

    def stats(self) -> Dict[str, Any]:
        return {
            "active_sessions": len(self._short_term),
            "total_conversations": sum(self._conversation_count.values()),
            "users_with_memory": len(self._long_term),
        }


# Global memory instance
memory = MemoryStore()
