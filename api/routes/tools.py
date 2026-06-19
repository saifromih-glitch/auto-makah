# Auto Makah — Tools Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.tools import registry, ToolCategory

router = APIRouter()


class ToolCallRequest(BaseModel):
    tool: str
    args: dict = {}


@router.get("")
async def list_tools(category: str = None):
    if category:
        return JSONResponse(registry.list_by_category(category))
    return JSONResponse(registry.list_all())


@router.get("/search")
async def search_tools(q: str):
    return JSONResponse(registry.search(q))


@router.post("/call")
async def call_tool(req: ToolCallRequest):
    tool = registry.get(req.tool)
    if not tool:
        raise HTTPException(404, f"Tool '{req.tool}' not found")
    try:
        result = tool(**req.args)
        return JSONResponse({"tool": req.tool, "result": result})
    except Exception as e:
        raise HTTPException(500, f"Tool error: {str(e)}")
