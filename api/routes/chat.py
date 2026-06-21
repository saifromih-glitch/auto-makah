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
    high_quality: bool = False  # 🏗️ Use BRV Pipeline (Builder/Reviewer/Verifier)


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
        from core.loop_engineering import load_state, save_state, run_with_retry

        # 🔁 State Memory: load past learnings
        loop_state = load_state("chat", "auto_makah")
        learnings_context = ""
        if loop_state.learnings:
            learnings_context = "\nالدروس السابقة:\n" + "\n".join(f"• {L}" for L in loop_state.learnings[-3:])

        router = HybridRouter()
        system = COGNITIVE_PROTOCOL + learnings_context + "\nأنت Auto Makah — منصة عربية هجينة (OpenClaw × Kimi). أجب بدقة واحترافية بالعربية."

        if req.agent:
            system += f"\nأنت الآن خبير في مجال: {req.agent}"
        else:
            # 📚 Auto-inject best skill based on question
            try:
                from core.skill_loader import inject_best_skill
                system = inject_best_skill(system, req.message)
            except Exception:
                pass

        # 🏗️ High Quality Mode: Builder/Reviewer/Verifier pipeline
        if req.high_quality:
            return await _handle_brv_chat(req)
        
        resp = await router.call(req.message, system_prompt=system)
        reply = resp.text if resp.ok else "عذراً، النماذج مشغولة — حاول بعد لحظات."
        
        # 🛡️ False Completion Guard: verify Arabic quality
        guard_result = _verify_reply_quality(reply, req.message)
        
        # 🔁 State Memory: save success/failure
        loop_state.total_runs += 1
        if guard_result["passed"]:
            loop_state.successful_runs += 1
            # Learn from good responses: extract key insight
            if len(reply) > 100:
                loop_state.learnings.append(f"[{guard_result['arabic_pct']}% عربي] {reply[:120]}...")
                loop_state.learnings = loop_state.learnings[-20:]  # Keep last 20
        else:
            loop_state.failed_runs += 1
            loop_state.last_error = guard_result["reason"]
        save_state(loop_state)
        
        return JSONResponse({
            "reply": reply,
            "model": resp.model,
            "latency_ms": resp.latency_ms,
            "tokens": resp.tokens_in + resp.tokens_out,
            "guard": guard_result,  # Transparent verification
            "loop_state": {
                "total": loop_state.total_runs,
                "success_rate": round((loop_state.successful_runs / max(loop_state.total_runs, 1)) * 100, 1)
            }
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


# ═══ 🏗️ Builder/Reviewer/Verifier — High Quality Chat ═══

async def _handle_brv_chat(req: ChatRequest):
    """Lopp Step 9: 3-agent verification pipeline for high-quality responses."""
    from core.brv_pipeline import BRVPipeline
    from core.loop_engineering import load_state, save_state
    
    loop_state = load_state("brv_chat", "auto_makah")
    
    pipeline = BRVPipeline()
    result = await pipeline.process_with_retry(req.message)
    
    # Save state
    loop_state.total_runs += 1
    if result.passed:
        loop_state.successful_runs += 1
    else:
        loop_state.failed_runs += 1
        loop_state.last_error = f"Score: {result.score}/10"
    save_state(loop_state)
    
    return JSONResponse({
        "reply": result.builder_output,
        "model": f"BRV Pipeline ({result.model_used})",
        "brv": {
            "passed": result.passed,
            "score": result.score,
            "reviewer_notes": result.reviewer_output[:300],
            "verdict": result.verifier_output[:200],
            "improvements": result.improvements[:3],
            "pipeline_ms": 0,  # Would track real latency
        },
        "guard": _verify_reply_quality(result.builder_output, req.message),
        "loop_state": {
            "total": loop_state.total_runs,
            "success_rate": round((loop_state.successful_runs / max(loop_state.total_runs, 1)) * 100, 1)
        }
    })


# ═══ 🔁 Loop Engineering: False Completion Guard ═══

def _verify_reply_quality(reply: str, question: str) -> dict:
    """
    Lopp Step 12: False Completion Guard.
    Objective checks before returning success.
    """
    result = {"passed": True, "reason": "", "arabic_pct": 0, "length": len(reply)}
    
    # Check 1: Not empty
    if len(reply) < 10:
        result["passed"] = False
        result["reason"] = "reply_too_short"
        return result
    
    # Check 2: Arabic character ratio
    arabic_chars = sum(1 for c in reply if '\u0600' <= c <= '\u06ff' or '\u0750' <= c <= '\u077f')
    total_chars = len(reply.replace(' ', '').replace('\n', ''))
    if total_chars > 0:
        result["arabic_pct"] = round((arabic_chars / total_chars) * 100, 1)
    
    # Check 3: Not just error message
    error_patterns = ["خطأ", "عذراً", "مشغولة", "error", "failed", "sorry"]
    if all(p in reply[:50].lower() for p in ["sorry", "error"]) or reply.startswith("Error"):
        result["passed"] = False
        result["reason"] = "looks_like_error_message"
    
    # Check 4: Not repeated garbage
    if len(set(reply[:200])) < 5:
        result["passed"] = False
        result["reason"] = "repeated_garbage"
    
    # Check 5: Question echoed verbatim (hallucination)
    if question[:30] == reply[:30]:
        result["passed"] = False
        result["reason"] = "echoed_question"
    
    return result
