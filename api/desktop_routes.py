# ═══════════════════════════════════════════
# 🕋 Auto Makah — Desktop Tools API
# Bridges local desktop agent to cloud
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter(prefix="/api/desktop", tags=["desktop-agent"])

HOME = Path.home()


class FileRequest(BaseModel):
    path: str = "."


class WriteRequest(BaseModel):
    path: str
    content: str


class CommandRequest(BaseModel):
    command: str
    timeout: int = 30


class SearchRequest(BaseModel):
    query: str
    directory: str = "."


@router.get("/status")
async def desktop_status():
    """Check if desktop agent is available (local) or cloud-mode."""
    is_local = os.getenv("DESKTOP_AGENT", "false").lower() == "true"
    return JSONResponse({
        "mode": "local" if is_local else "cloud",
        "home": str(HOME),
        "features": {
            "file_system": True,
            "commands": True,
            "watcher": True,
            "notifications": is_local,
            "system_tray": is_local,
        },
        "setup_instructions": {
            "install": "pip install pystray pillow httpx",
            "run": "python agents/desktop_agent.py start",
            "config": f"Edit {HOME}/.auto-makah/config.json",
        }
    })


@router.post("/files/list")
async def list_files(req: FileRequest):
    """List files in a directory (cloud-safe, limited to allowed paths)."""
    try:
        from agents.desktop_agent import DesktopAgent
        return JSONResponse(DesktopAgent.list_directory(req.path))
    except ImportError:
        return JSONResponse({"error": "Desktop agent not available"})


@router.get("/system/info")
async def system_info():
    """Get system information."""
    try:
        from agents.desktop_agent import DesktopAgent
        return JSONResponse(DesktopAgent.get_system_info())
    except ImportError:
        import platform
        return JSONResponse({
            "os": platform.system(),
            "python": platform.python_version(),
            "hostname": platform.node(),
            "note": "Limited — install desktop agent for full features",
        })


@router.post("/command/run")
async def run_command(req: CommandRequest):
    """Execute a local command (requires desktop agent running)."""
    try:
        from agents.desktop_agent import DesktopAgent
        return JSONResponse(DesktopAgent.run_command(req.command, req.timeout))
    except ImportError:
        return JSONResponse({"error": "Desktop agent not available"})


@router.post("/files/search")
async def search_files(req: SearchRequest):
    """Search for files."""
    try:
        from agents.desktop_agent import DesktopAgent
        return JSONResponse(DesktopAgent.search_files(req.query, req.directory))
    except ImportError:
        return JSONResponse({"error": "Desktop agent not available"})
