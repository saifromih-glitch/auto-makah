# ═══════════════════════════════════════════
# 🕋 Auto Makah — Agent Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class CreateAgentRequest(BaseModel):
    name: str
    profile: Optional[Dict[str, Any]] = None


class AgentMessage(BaseModel):
    message: str
    task_type: str = "chat"


@router.post("")
async def create_agent(req: CreateAgentRequest):
    """Create a new AI agent."""
    from core.agent import runtime
    agent = runtime.create_agent(req.name, req.profile)
    return JSONResponse(agent.to_dict(), status_code=201)


@router.get("/{name}")
async def get_agent(name: str):
    """Get agent details."""
    from core.agent import runtime
    agent = runtime.get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return JSONResponse(agent.to_dict())


@router.post("/{name}/chat")
async def chat_with_agent(name: str, req: AgentMessage):
    """Send message to an agent."""
    from core.agent import runtime
    agent = runtime.get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    result = await agent.execute(req.message, req.task_type)
    return JSONResponse(result)
