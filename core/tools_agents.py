"""
Always-on Scheduler + RAG Pipeline
"""
import os, httpx, asyncio, json

ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")

async def _call(prompt: str, system: str = "", max_tokens: int = 3000) -> str:
    if not ZENMUX_KEY: return "Error: No key"
    msgs = []
    if system: msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(ZENMUX_URL, headers={
                "Authorization": f"Bearer {ZENMUX_KEY}", "Content-Type": "application/json",
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": max_tokens, "temperature": 0.5})
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else f"Error: {d}"
    except Exception as e:
        return f"Error: {str(e)}"

# ═══ Comparative Analysis ═══
async def compare(items: list, criteria: list = None) -> dict:
    """Compare items across criteria — like the Recruitment Agent pattern."""
    if not criteria: criteria = ["التكلفة", "الجودة", "الوقت", "المخاطر", "العائد"]
    items_str = "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
    crit_str = "، ".join(criteria)
    prompt = f"""قارن بين:
{items_str}
المعايير: {crit_str}
قدم: 1. جدول مقارنة 2. نقاط القوة والضعف 3. التوصية 4. الترتيب"""
    analysis = await _call(prompt, "أنت محلل ومقارن خبير. إجاباتك منظمة بالعربية.")
    return {"items": items, "analysis": analysis}

# ═══ Data Analysis ═══
async def analyze_data(data_description: str) -> dict:
    """Analyze data patterns — like the Data Analysis Agent."""
    prompt = f"""حلل البيانات التالية:
{data_description}
قدم: 1. ملخص 2. اتجاهات 3. نقاط مهمة 4. توصيات"""
    analysis = await _call(prompt, "أنت محلل بيانات خبير. إجاباتك دقيقة ومنظمة بالعربية.")
    return {"analysis": analysis}

# ═══ Meeting Notes ═══
async def meeting_notes(transcript: str) -> dict:
    """Generate meeting summary — like the Meeting Agent."""
    prompt = f"""لخص الاجتماع التالي:
{transcript[:4000]}
قدم: 1. ملخص 2. القرارات 3. المهام (مع المسؤولين) 4. النقاط العالقة"""
    analysis = await _call(prompt, "أنت مساعد إداري خبير. ملخصاتك دقيقة ومنظمة بالعربية.")
    return {"analysis": analysis}

# ═══ Project Planner ═══
async def project_plan(goal: str, constraints: str = "") -> dict:
    """Create project plan — like the Project Planner skill."""
    ctx = f"\nالقيود: {constraints}" if constraints else ""
    prompt = f"""خطط لمشروع:
الهدف: {goal}{ctx}
قدم: 1. مراحل 2. مهام 3. جدول زمني 4. موارد 5. مخاطر"""
    analysis = await _call(prompt, "أنت مدير مشاريع خبير. خططك عملية ومنظمة بالعربية.")
    return {"goal": goal, "analysis": analysis}

# ═══ Content Creator ═══
async def create_content(topic: str, format: str = "blog", audience: str = "عام") -> dict:
    """Generate content — like the Content Creator skill."""
    prompt = f"""اكتب محتوى:
الموضوع: {topic}
النوع: {format}
الجمهور: {audience}
اكتب محتوى جاهزاً للنشر بالعربية."""
    analysis = await _call(prompt, "أنت كاتب محتوى خبير. كتابتك احترافية وجذابة بالعربية.", max_tokens=4000)
    return {"topic": topic, "format": format, "content": analysis}
