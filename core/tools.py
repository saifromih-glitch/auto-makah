# ═══════════════════════════════════════════
# 🕋 Auto Makah — Tool Registry
# ═══════════════════════════════════════════

from typing import Callable, Dict, Any, Optional
from enum import Enum
import json


class ToolCategory(str, Enum):
    CORE = "core"
    FILE = "file"
    SEARCH = "search"
    CODING = "coding"
    DEPLOY = "deploy"
    COMMUNICATION = "communication"
    KNOWLEDGE = "knowledge"
    UTILITY = "utility"


class Tool:
    """Tool definition with metadata."""

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: ToolCategory = ToolCategory.CORE,
        parameters: Dict[str, Any] = None,
    ):
        self.name = name
        self.func = func
        self.description = description
        self.category = category
        self.parameters = parameters or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": self.parameters,
        }

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class ToolRegistry:
    """Central tool registry — discoverable and queryable."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._by_category: Dict[str, Dict[str, Tool]] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        self._tools[tool.name] = tool
        cat = tool.category.value
        self._by_category.setdefault(cat, {})[tool.name] = tool
        return self

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_all(self) -> Dict[str, Any]:
        return {name: t.to_dict() for name, t in self._tools.items()}

    def list_by_category(self, category: ToolCategory) -> Dict[str, Any]:
        return {
            name: t.to_dict()
            for name, t in self._by_category.get(category.value, {}).items()
        }

    def search(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        return {
            name: t.to_dict()
            for name, t in self._tools.items()
            if query_lower in name.lower() or query_lower in t.description.lower()
        }

    def count(self) -> int:
        return len(self._tools)

    def categories(self) -> list:
        return list(self._by_category.keys())


# ═══════════════════════════════
# Global Registry
# ═══════════════════════════════
registry = ToolRegistry()


# ═══════════════════════════════
# Built-in Core Tools
# ═══════════════════════════════

def tool_get_time() -> dict:
    """Return current timestamp."""
    from datetime import datetime
    return {"timestamp": datetime.utcnow().isoformat(), "tool": "get_time"}


def tool_get_status() -> dict:
    """Return system status."""
    return {
        "status": "operational",
        "agents_count": 0,
        "tools_count": registry.count(),
        "categories": registry.categories(),
        "tool": "get_status",
    }


# Register core tools
registry.register(Tool("get_time", tool_get_time, "Get current UTC time", ToolCategory.CORE))
registry.register(Tool("get_status", tool_get_status, "Get system status", ToolCategory.CORE))
