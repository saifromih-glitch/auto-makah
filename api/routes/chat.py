# ═══════════════════════════════════════════
# 🕋 Auto Makah — Chat API for Web UI
# ═══════════════════════════════════════════

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_default"
    agent: str | None = None
    tool: str | None = None


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Process chat message from web UI."""
    try:
        from core.connectors import HybridRouter

        router = HybridRouter()
        system = "أنت Auto Makah — منصة عربية هجينة (OpenClaw × Kimi). أجب بدقة واحترافية."

        if req.agent:
            system += f"\nأنت الآن خبير في مجال: {req.agent}"
        if req.tool:
            if req.tool == "code_run":
                system += "\nأنشئ كود Python جاهز للتشغيل."
            elif req.tool == "slides":
                system += "\nنظم الرد كشرائح عرض (Slides)."
            elif req.tool == "rethink":
                system += "\nنظم الرد بشكل SWOT أو Mindmap حسب السياق."

        resp = await router.call(req.message, system_prompt=system)
        return JSONResponse({
            "reply": resp.text if resp.ok else "عذراً، النماذج مشغولة.",
            "model": resp.model,
            "latency_ms": resp.latency_ms,
            "tokens": resp.tokens_in + resp.tokens_out,
        })
    except Exception as e:
        return JSONResponse({"reply": "", "error": str(e)}, status_code=500)
