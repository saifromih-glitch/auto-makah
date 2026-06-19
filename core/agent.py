# ═══════════════════════════════════════════
# 🕋 Auto Makah — Core Agent Runtime
# ═══════════════════════════════════════════

from typing import Optional, Dict, Any, List, Callable
import json
import asyncio
from datetime import datetime


class Agent:
    """Core Agent — manages tools, prompts, context, and execution."""

    def __init__(self, name: str, profile: Dict[str, Any] = None):
        self.name = name
        self.profile = profile or {}
        self.tools: Dict[str, Callable] = {}
        self.system_prompt: str = ""
        self.session_context: Dict[str, Any] = {}
        self._user_context: str = ""
        self.created_at = datetime.utcnow().isoformat()

    def register_tool(self, name: str, func: Callable, description: str = ""):
        """Register a tool the agent can call."""
        self.tools[name] = func
        return self

    def set_system_prompt(self, prompt: str):
        """Set the core system prompt."""
        self.system_prompt = prompt

    def add_knowledge(self, domain: str, content: str):
        """Inject domain-specific knowledge."""
        self.session_context.setdefault("knowledge", {})[domain] = content

    def add_memory(self, key: str, value: Any):
        """Inject user/context memory."""
        self.session_context["memory"] = self.session_context.get("memory", {})
        self.session_context["memory"][key] = value

    async def execute(self, message: str, task_type: str = "chat") -> Dict[str, Any]:
        """Execute a task — the core dispatch loop."""
        return {
            "agent": self.name,
            "message": message,
            "task_type": task_type,
            "tools_available": list(self.tools.keys()),
            "context": {
                "knowledge_domains": list(self.session_context.get("knowledge", {}).keys()),
                "memory_keys": list(self.session_context.get("memory", {}).keys()),
            },
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "profile": self.profile,
            "tools_count": len(self.tools),
            "created_at": self.created_at,
        }


class AgentRuntime:
    """Manages multiple agents — registration, lifecycle, dispatch."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.default_tools: Dict[str, Callable] = {}

    def create_agent(self, name: str, profile: Dict[str, Any] = None) -> Agent:
        agent = Agent(name, profile)
        # Inherit default tools
        for tname, tfunc in self.default_tools.items():
            agent.register_tool(tname, tfunc)
        self.agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[Agent]:
        return self.agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.agents.values()]

    def register_global_tool(self, name: str, func: Callable):
        self.default_tools[name] = func


# ═══════════════════════════════
# Global Runtime Singleton
# ═══════════════════════════════
runtime = AgentRuntime()
