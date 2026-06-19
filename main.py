# ═══════════════════════════════════════════
# 🕋 Auto Makah — Main Entry Point
# ═══════════════════════════════════════════

import sys
import os

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import app
from core.agent import runtime
from core.tools import registry


def init():
    """Initialize Auto Makah platform."""
    print("🕋 Auto Makah — Initializing...")
    print(f"   Agents: {len(runtime.agents)}")
    print(f"   Tools: {registry.count()}")
    print(f"   Categories: {registry.categories()}")
    print("   Ready. B-ismillah.")


if __name__ == "__main__":
    import uvicorn
    init()
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
