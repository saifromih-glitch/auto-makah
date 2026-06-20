# ═══════════════════════════════════════════
# 🕋 Auto Makah — Kimi Tools API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.kimi_tools import SlidesGenerator, CodeRunner, RethinkEngine

router = APIRouter(prefix="/api/kimi", tags=["kimi-tools"])


class SlidesRequest(BaseModel):
    title: str
    content: str
    theme: str = "makkah"


class RethinkRequest(BaseModel):
    notes: str
    method: str = "mindmap"  # mindmap, outline, categories, swot, pros-cons


class CodeRunRequest(BaseModel):
    code: str
    language: str = "python"  # python, javascript


@router.post("/slides")
async def create_slides(req: SlidesRequest):
    """Generate an HTML slide deck from text."""
    sd = SlidesGenerator.generate(req.title, req.content, req.theme)
    return {
        "title": sd.title,
        "slides_count": len(sd.slides),
        "slides": sd.slides,
        "html": sd.html,
    }


@router.post("/rethink")
async def rethink_ideas(req: RethinkRequest):
    """Organize scattered thoughts into structured format."""
    if req.method not in ["mindmap", "outline", "categories", "swot", "pros-cons"]:
        raise HTTPException(400, f"Unknown method: {req.method}")
    result = RethinkEngine.organize(req.notes, req.method)
    return result


@router.post("/code/run")
async def run_code(req: CodeRunRequest):
    """Execute code in sandboxed environment."""
    if req.language == "javascript":
        result = await CodeRunner.run_javascript(req.code)
    else:
        result = await CodeRunner.run_python(req.code)
    return result


@router.get("/list")
async def list_kimi_tools():
    """List available Kimi-inspired tools."""
    from core.kimi_tools import KIMI_TOOLS
    return {
        "tools": [
            {"name": t["name"], "display": t["display"], "description": t["description"]}
            for t in KIMI_TOOLS.values()
        ]
    }
