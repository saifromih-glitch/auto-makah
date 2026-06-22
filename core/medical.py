"""
Medical Agent — health info, post-surgery guidance
"""
import os, httpx, asyncio

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
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": tokens, "temperature": 0.3})
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else f"Error: {d}"
    except Exception as e: return f"Error: {str(e)}"

async def post_surgery_guide(surgery_type: str) -> dict:
    """Post-surgery recovery guidance."""
    system = "أنت طبيب استشاري. إرشاداتك طبية دقيقة ومبنية على أدلة. تبدأ كل إجابة بـ'هذه إرشادات عامة — استشر طبيبك المعالج دائماً.'"
    prompt = f"""قدم إرشادات ما بعد العملية الجراحية:
نوع العملية: {surgery_type}
قدم:
1. الرعاية بالجرح
2. الأدوية والمسكنات
3. علامات الخطر (متى تذهب للطوارئ)
4. النظام الغذائي
5. النشاط والحركة
6. مواعيد المتابعة
ملاحظة: هذه إرشادات عامة — استشر طبيبك المعالج دائماً"""
    a = await _ai(prompt, system, 4000)
    return {"surgery": surgery_type, "guide": a}

async def medical_terms_explain(terms: str) -> dict:
    """Explain medical terms in Arabic."""
    system = "أنت طبيب يشرح المصطلحات الطبية بالعربية المبسطة."
    prompt = f"""اشرح هذه المصطلحات الطبية بالعربية المبسطة:
{terms}
لكل مصطلح: 1. المعنى بالعربية 2. شرح مبسط 3. الأعراض/الأسباب (إن وجدت)"""
    a = await _ai(prompt, system)
    return {"terms": terms, "explanation": a}
