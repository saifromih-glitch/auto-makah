"""
Advanced Features — Pipeline, Voice, Export, File Analysis
"""
import os, httpx, asyncio, json, base64, io

ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")

async def _ai(prompt: str, system: str = "", tokens: int = 3000) -> str:
    if not ZENMUX_KEY: return "Error: No key"
    msgs = [{"role": "system", "content": system}] if system else []
    msgs.append({"role": "user", "content": prompt})
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(ZENMUX_URL, headers={
                "Authorization": f"Bearer {ZENMUX_KEY}", "Content-Type": "application/json",
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": tokens, "temperature": 0.5})
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else f"Error: {d}"
    except Exception as e: return f"Error: {str(e)}"

# ═══ Multi-Agent Pipeline ═══
# Chain multiple agents: Research → Analyze → Report

PIPELINES = {
    "business_launch": {
        "name": "إطلاق مشروع جديد",
        "steps": [
            {"agent": "feasibility", "prompt": "ادرس جدوى المشروع: {input}", "key": "feasibility"},
            {"agent": "swot", "prompt": "حلل SWOT: {input}\nبناء على دراسة الجدوى:\n{feasibility}", "key": "swot"},
            {"agent": "plan", "prompt": "ضع خطة مشروع لـ: {input}\nالجدوى: {feasibility}\nSWOT: {swot}", "key": "plan"},
            {"agent": "finance", "prompt": "حلل مادياً: {input}\nالخطة: {plan}", "key": "finance"},
        ],
    },
    "company_analysis": {
        "name": "تحليل شركة شامل",
        "steps": [
            {"agent": "swot", "prompt": "حلل SWOT: {input}", "key": "swot"},
            {"agent": "porter", "prompt": "حلل القوى الخمس لبورتر: {input}\nSWOT: {swot}", "key": "porter"},
            {"agent": "valuation", "prompt": "قيم الشركة: {input}\nSWOT: {swot}\nPorter: {porter}", "key": "valuation"},
            {"agent": "recommend", "prompt": "قدم توصيات استراتيجية لـ: {input}\nSWOT: {swot}\nPorter: {porter}\nالتقييم: {valuation}", "key": "recommendation"},
        ],
    },
    "content_marketing": {
        "name": "حملة تسويقية كاملة",
        "steps": [
            {"agent": "aarrr", "prompt": "حلل AARRR للمنتج: {input}", "key": "aarrr"},
            {"agent": "plan", "prompt": "خطة تسويق: {input}\nتحليل AARRR: {aarrr}", "key": "plan"},
            {"agent": "content", "prompt": "اكتب محتوى تسويقي لـ: {input}\nالخطة: {plan}", "key": "content"},
            {"agent": "calendar", "prompt": "تقويم نشر لـ: {input}\nالخطة: {plan}\nالمحتوى: {content}", "key": "calendar"},
        ],
    },
    "legal_hr": {
        "name": "توظيف وقانوني",
        "steps": [
            {"agent": "jd", "prompt": "وصف وظيفي: {input}", "key": "jd"},
            {"agent": "interview", "prompt": "أسئلة مقابلة: {input}\nالوصف: {jd}", "key": "questions"},
            {"agent": "legal", "prompt": "الجوانب القانونية للتوظيف: {input} في السعودية\nالوصف: {jd}", "key": "legal"},
            {"agent": "contract", "prompt": "بنود العقد لـ: {input}\nالقانوني: {legal}\nالوصف: {jd}", "key": "contract"},
        ],
    },
}

async def run_pipeline(pipeline_name: str, input_text: str) -> dict:
    """Execute a multi-step agent pipeline."""
    if pipeline_name not in PIPELINES:
        return {"error": f"Unknown pipeline: {pipeline_name}", "available": list(PIPELINES.keys())}
    
    pipe = PIPELINES[pipeline_name]
    results = {}
    context = {"input": input_text}
    step_results = []
    
    for step in pipe["steps"]:
        # Build prompt with accumulated context
        prompt = step["prompt"].format(**{**context, **results})
        
        system_prompts = {
            "feasibility": "أنت خبير دراسات جدوى.",
            "swot": "أنت محلل SWOT استراتيجي.",
            "porter": "أنت خبير استراتيجي بمنهجية مايكل بورتر.",
            "valuation": "أنت محلل مالي بمنهجية داموداران.",
            "recommend": "أنت مستشار استراتيجي.",
            "plan": "أنت مخطط مشاريع ومحلل استراتيجي.",
            "finance": "أنت محلل مالي واستثماري.",
            "aarrr": "أنت خبير نمو بمنهجية Sean Ellis.",
            "content": "أنت كاتب محتوى تسويقي محترف.",
            "calendar": "أنت استراتيجي محتوى.",
            "jd": "أنت خبير موارد بشرية.",
            "interview": "أنت خبير توظيف.",
            "legal": "أنت مستشار قانوني سعودي.",
            "contract": "أنت خبير عقود وموارد بشرية.",
        }
        
        system = system_prompts.get(step["agent"], "أنت خبير.")
        analysis = await _ai(prompt, system, 2500)
        results[step["key"]] = analysis
        step_results.append({"step": step["agent"], "result": analysis[:300] + "..."})
        context.update(results)
    
    return {
        "pipeline": pipe["name"],
        "input": input_text,
        "steps_completed": len(pipe["steps"]),
        "step_summaries": step_results,
        "final_report": results,
    }

# ═══ Brainstorming Engine ═══

async def brainstorm(topic: str, method: str = "scamper") -> dict:
    """Generate creative ideas using structured brainstorming."""
    methods = {
        "scamper": "SCAMPER (بدّل، ادمج، كيف، عدّل، استخدم، احذف، اعكس)",
        "sixhats": "قبعات التفكير الست (أبيض، أحمر، أسود، أصفر، أخضر، أزرق)",
        "firstprinciples": "التفكير من المبادئ الأولى",
        "random": "الترابط العشوائي للإبداع",
    }
    system = f"أنت مبدع ومبتكر. تستخدم منهجية {methods.get(method, method)} لتوليد أفكار جديدة."
    prompt = f"""استخدم منهجية {methods.get(method, method)} لتوليد أفكار حول:
{topic}
قدم ١٠ أفكار مبتكرة وقابلة للتنفيذ"""
    a = await _ai(prompt, system, 4000)
    return {"topic": topic, "method": method, "ideas": a}

# ═══ Executive Summary ═══

async def executive_summary(topic: str, length: str = "موجز") -> dict:
    """Generate C-level executive summary."""
    system = "أنت مساعد تنفيذي للمدير العام. ملخصاتك موجزة ودقيقة ومباشرة."
    limits = {"موجز": "فقرة واحدة (١٠٠ كلمة)", "متوسط": "٣ فقرات (٣٠٠ كلمة)", "مفصل": "٥ فقرات (٥٠٠ كلمة)"}
    prompt = f"""اكتب ملخصاً تنفيذياً:
الموضوع: {topic}
الطول: {limits.get(length, length)}
قدم: 1. الخلاصة 2. الأرقام الرئيسية 3. التوصية"""
    a = await _ai(prompt, system)
    return {"topic": topic, "summary": a}

# ═══ Pitch Deck Outline ═══

async def pitch_deck(company: str, audience: str = "مستثمرين") -> dict:
    """Create pitch deck structure."""
    system = "أنت خبير عروض تقديمية للمستثمرين."
    prompt = f"""صمم هيكل Pitch Deck:
الشركة: {company}
الجمهور: {audience}
قدم ١٢ شريحة: 1. الغلاف 2. المشكلة 3. الحل 4. السوق 5. المنتج 6. نموذج العمل
7. المنافسة 8. الفريق 9. الجذب 10. المالية 11. الطلب 12. الخاتمة"""
    a = await _ai(prompt, system, 4000)
    return {"company": company, "pitch": a}
