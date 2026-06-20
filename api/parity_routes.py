# ═══════════════════════════════════════════
# 🕋 Auto Makah — Parity Tools API
# Browser + Image + ACP routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/parity", tags=["parity-tools"])


class FetchRequest(BaseModel):
    url: str = ""


class SearchRequest(BaseModel):
    query: str = ""
    engine: str = "duckduckgo"


class ExtractRequest(BaseModel):
    url: str = ""


class ImageRequest(BaseModel):
    image_url: str = ""


class CodeFixRequest(BaseModel):
    code: str = ""
    description: str = ""
    test: str | None = None


@router.post("/browser/fetch")
async def browser_fetch(req: FetchRequest):
    """Fetch and preview webpage content."""
    from core.parity_tools import BrowserAutomation
    result = await BrowserAutomation.fetch_page(req.url)
    return JSONResponse(result)


@router.post("/browser/search")
async def browser_search(req: SearchRequest):
    """Search the web."""
    from core.parity_tools import BrowserAutomation
    result = await BrowserAutomation.search_web(req.query, req.engine)
    return JSONResponse(result)


@router.post("/browser/extract")
async def browser_extract(req: ExtractRequest):
    """Extract readable text from webpage."""
    from core.parity_tools import BrowserAutomation
    result = await BrowserAutomation.extract_text(req.url)
    return JSONResponse(result)


@router.post("/image/describe")
async def image_describe(req: ImageRequest):
    """Describe an image using AI."""
    from core.parity_tools import ImageAnalyzer
    result = await ImageAnalyzer.describe(req.image_url)
    return JSONResponse(result)


@router.post("/code/fix")
async def code_fix(req: CodeFixRequest):
    """Fix and test code iteratively (ACP-lite)."""
    from core.parity_tools import ACPLite
    result = await ACPLite.fix_and_test(req.code, req.test, req.description)
    return JSONResponse(result)


@router.get("/tools")
async def list_parity_tools():
    """List all parity tools."""
    from core.parity_tools import PARITY_TOOLS
    return JSONResponse({
        "tools": [
            {"name": t["name"], "display": t["display"], "description": t["description"]}
            for t in PARITY_TOOLS.values()
        ]
    })
