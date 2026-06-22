"""
Marketing & Growth Agent — AARRR, campaigns, market research
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
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": tokens, "temperature": 0.5})
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else f"Error: {d}"
    except Exception as e: return f"Error: {str(e)}"

async def aarrr_analysis(product: str) -> dict:
    """Pirate Metrics (AARRR) — Sean Ellis methodology."""
    system = "أنت خبير نمو بمنهجية Sean Ellis. تحليلاتك مبنية على البيانات بالعربية."
    prompt = f"""حلل المنتج باستخدام AARRR (Pirate Metrics):
المنتج: {product}
قدم تحليلاً لكل مرحلة:
1. اكتساب (Acquisition) — مصادر الجذب
2. تفعيل (Activation) — أول تجربة إيجابية
3. احتفاظ (Retention) — عودة المستخدم
4. إحالة (Referral) — مشاركة المستخدمين
5. إيراد (Revenue) — نموذج الدخل"""
    a = await _ai(prompt, system)
    return {"product": product, "analysis": a}

async def marketing_plan(product: str, budget: str = "", audience: str = "") -> dict:
    system = "أنت خبير تسويق. خططك عملية ومرتبطة بأهداف قابلة للقياس بالعربية."
    ctx = f"\nالميزانية: {budget}" if budget else ""
    ctx2 = f"\nالجمهور المستهدف: {audience}" if audience else ""
    prompt = f"""ضع خطة تسويقية:
المنتج: {product}{ctx}{ctx2}
قدم:
1. تحليل السوق والمنافسين
2. استراتيجية المحتوى
3. القنوات التسويقية (مع تحديد الميزانية لكل قناة)
4. KPIs ومؤشرات القياس
5. جدول زمني (٩٠ يوم)"""
    a = await _ai(prompt, system, 4000)
    return {"product": product, "analysis": a}

async def campaign_idea(product: str, channel: str = "منصات التواصل") -> dict:
    system = "أنت مبدع حملات تسويقية. أفكارك مبتكرة وقابلة للتنفيذ بالعربية."
    prompt = f"""صمم حملة تسويقية:
المنتج: {product}
القناة: {channel}
قدم:
1. اسم الحملة وشعارها
2. الفكرة الإبداعية
3. المحتوى (نص + مرئيات مقترحة)
4. خطة النشر
5. قياس النجاح"""
    a = await _ai(prompt, system)
    return {"product": product, "channel": channel, "analysis": a}
