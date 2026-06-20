# 🕋 Auto Makah — Agent Tool Executor
# Bridges the gap: Agent ↔ 23 Tools

from typing import Dict, Any, Optional
from core.agent import runtime
from core.tools import registry


class ToolExecutor:
    """Execute tools on behalf of agents."""

    def execute(self, agent_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool for a specific agent."""
        agent = runtime.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found", "tool": tool_name}

        tool = registry.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found", "available": list(registry._tools.keys())[:10]}

        try:
            result = tool(**kwargs)
            return {"agent": agent_name, "tool": tool_name, "result": result, "status": "success"}
        except Exception as e:
            return {"agent": agent_name, "tool": tool_name, "error": str(e), "status": "failed"}

    def get_agent_tools(self, agent_name: str) -> Dict[str, Any]:
        """List tools available to an agent."""
        agent = runtime.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}

        return {
            "agent": agent_name,
            "registered_tools": list(agent.tools.keys()),
            "all_available": registry.list_all(),
            "total_available": registry.count(),
        }

    def route_and_execute(self, agent_name: str, user_message: str) -> Dict[str, Any]:
        """Smart routing: detect what tool is needed and execute it."""
        msg = user_message.lower()

        # File generation
        if any(kw in msg for kw in ["إكسيل", "excel", "xlsx", "جدول"]):
            return self.execute(agent_name, "create_xlsx", title="بيانات", data=[])
        if any(kw in msg for kw in ["pdf", "بي دي إف"]):
            return self.execute(agent_name, "create_pdf", title="تقرير", content="")
        if any(kw in msg for kw in ["csv", "سي إس في"]):
            return self.execute(agent_name, "create_csv", filename="export.csv", data=[])

        # Calculations
        if "زكاة" in msg:
            return self.execute(agent_name, "calculate_zakat",
                cash=0, receivables=0, inventory=0, short_term_debt=0)
        if "vat" in msg or "ضريبة" in msg:
            return self.execute(agent_name, "calculate_vat", amount=0)
        if "تعادل" in msg or "break" in msg:
            return self.execute(agent_name, "calculate_break_even",
                fixed_costs=0, revenue=0, variable_costs=0)

        # Web
        if any(kw in msg for kw in ["بحث", "search", "ابحث"]):
            return self.execute(agent_name, "web_search", query=user_message)
        if "طقس" in msg or "weather" in msg:
            return self.execute(agent_name, "get_weather", city="Jeddah")

        return {"status": "no_tool_matched", "message": user_message, "agent": agent_name}


executor = ToolExecutor()
