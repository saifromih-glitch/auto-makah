"""Chat API — Real tool execution + LLM responses (v0.4.0 — No more simulation)"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/api/chat", tags=["chat"])
log = logging.getLogger("chat")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_default"
    agent: str | None = None
    tool: str | None = None


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Process chat message — real tool execution OR LLM response."""
    try:
        # ═══ REAL TOOL EXECUTION (not simulation!) ═══
        if req.tool == "slides":
            return await _handle_slides(req)
        elif req.tool == "code_run":
            return await _handle_code_run(req)
        elif req.tool == "rethink":
            return await _handle_rethink(req)
        
        # ═══ LLM CHAT (with agent context if specified) ═══
        from core.connectors import HybridRouter
        from core.cognitive_protocol import COGNITIVE_PROTOCOL

        router = HybridRouter()
        system = COGNITIVE_PROTOCOL + "\nأنت Auto Makah — منصة عربية هجينة (OpenClaw × Kimi). أجب بدقة واحترافية بالعربية."

        if req.agent:
            system += f"\nأنت الآن خبير في مجال: {req.agent}"

        resp = await router.call(req.message, system_prompt=system)
        return JSONResponse({
            "reply": resp.text if resp.ok else "عذراً، النماذج مشغولة — حاول بعد لحظات.",
            "model": resp.model,
            "latency_ms": resp.latency_ms,
            "tokens": resp.tokens_in + resp.tokens_out,
        })
    except Exception as e:
        log.error(f"Chat error: {e}")
        return JSONResponse({"reply": "❌ خطأ في المعالجة — جاري الإصلاح", "error": str(e)}, status_code=500)


async def _handle_slides(req: ChatRequest):
    """Real slides generation — not simulated."""
    from core.kimi_tools import SlidesGenerator
    try:
        # Use first line as title, rest as content
        lines = req.message.strip().split('\n', 1)
        title = lines[0][:80]
        content = lines[1] if len(lines) > 1 else req.message
        deck = SlidesGenerator.generate(title, content, theme="makkah")
        return JSONResponse({
            "reply": f"✅ **تم إنشاء {len(deck.slides)} شرائح**\n\n📝 العنوان: {deck.title}\n🎨 القالب: Makkah Dark\n\n🖨️ العرض جاهز — HTML كامل بمسافة {len(deck.html):,} حرف",
            "model": "Slides Generator",
            "latency_ms": 0,
            "tokens": len(deck.html),
            "html": deck.html[:2000],  # Send preview
        })
    except Exception as e:
        return JSONResponse({"reply": f"❌ فشل إنشاء الشرائح: {e}", "error": str(e)}, status_code=500)


async def _handle_code_run(req: ChatRequest):
    """Real code execution — not simulated."""
    from core.kimi_tools import CodeRunner
    try:
        code = req.message.strip()
        # Detect language from first line comments
        lang = "python"
        if code.startswith("//") or code.startswith("/*"):
            lang = "javascript"
        
        if lang == "javascript":
            result = await CodeRunner.run_javascript(code)
        else:
            result = await CodeRunner.run_python(code)
        
        if result["success"]:
            reply = f"✅ **تم التشغيل بنجاح**\n\n```\n{result['output'][:2000]}\n```\n🟢 Exit code: {result['exit_code']}"
        else:
            reply = f"❌ **خطأ في التشغيل**\n\n```\n{result.get('error', result.get('output', 'Unknown error'))[:2000]}\n```\n🔴 Exit code: {result['exit_code']}"
        
        return JSONResponse({
            "reply": reply,
            "model": "Code Runner",
            "latency_ms": 0,
            "tokens": len(code),
        })
    except Exception as e:
        return JSONResponse({
            "reply": f"❌ فشل تشغيل الكود: {e}\n\n⚠️ تأكد من وجود Python/Node على السيرفر",
            "error": str(e)
        }, status_code=500)


async def _handle_rethink(req: ChatRequest):
    """Real idea organization — not simulated."""
    from core.kimi_tools import RethinkEngine
    try:
        notes = req.message.strip()
        # Auto-detect method from content
        method = "mindmap"
        if any(w in notes.lower() for w in ['swot', 'قوة', 'ضعف', 'فرص', 'تهديد']):
            method = "swot"
        elif any(w in notes.lower() for w in ['إيجابيات', 'سلبيات', 'pros', 'cons']):
            method = "pros-cons"
        
        result = RethinkEngine.organize(notes, method)
        
        # Format the result nicely
        if method == "mindmap":
            branches_text = "\n".join([
                f"  {chr(9679)} **{b['title']}**\n" + 
                "\n".join([f"    - {item}" for item in b.get('items', [])])
                for b in result.get('branches', [])
            ])
            reply = f"🧠 **خريطة ذهنية**\n\n🎯 المركز: **{result.get('central', '')}**\n\n{branches_text}"
        elif method == "swot":
            a = result['analysis']
            reply = f"📊 **تحليل SWOT**\n\n✅ **نقاط القوة:**\n" + "\n".join(f"  • {s}" for s in a.get('strengths',[])) + "\n\n⚠️ **نقاط الضعف:**\n" + "\n".join(f"  • {w}" for w in a.get('weaknesses',[])) + "\n\n🌟 **الفرص:**\n" + "\n".join(f"  • {o}" for o in a.get('opportunities',[])) + "\n\n🚨 **التهديدات:**\n" + "\n".join(f"  • {t}" for t in a.get('threats',[]))
        else:
            reply = f"📋 **{method}**\n\n{str(result)[:2000]}"
        
        return JSONResponse({
            "reply": reply,
            "model": "Rethink Engine",
            "latency_ms": 0,
            "tokens": len(notes),
        })
    except Exception as e:
        return JSONResponse({"reply": f"❌ فشل تنظيم الأفكار: {e}", "error": str(e)}, status_code=500)
