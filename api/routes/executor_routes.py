# Auto Makah — Tool Executor Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.executor import executor

router = APIRouter()


class ExecuteRequest(BaseModel):
    agent_name: str
    tool_name: str
    kwargs: dict = {}


class SmartExecuteRequest(BaseModel):
    agent_name: str
    message: str


@router.post("/execute")
async def execute_tool(req: ExecuteRequest):
    """Execute a specific tool for an agent."""
    result = executor.execute(req.agent_name, req.tool_name, **req.kwargs)
    return JSONResponse(result)


@router.get("/{agent_name}/tools")
async def agent_tools(agent_name: str):
    """List tools for an agent."""
    result = executor.get_agent_tools(agent_name)
    return JSONResponse(result)


@router.post("/smart")
async def smart_execute(req: SmartExecuteRequest):
    """Auto-detect and execute the right tool."""
    result = executor.route_and_execute(req.agent_name, req.message)
    return JSONResponse(result)
