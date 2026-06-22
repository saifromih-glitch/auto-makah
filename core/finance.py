"""
Finance Agent — investment analysis, DCF, NPV, business valuation
"""
import os, httpx, asyncio

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
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": max_tokens, "temperature": 0.3})
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else f"Error: {d}"
    except Exception as e:
        return f"Error: {str(e)}"

async def business_valuation(company_desc: str, industry: str = "عام") -> dict:
    """Valuation analysis using Damodaran methodology."""
    system = "أنت محلل مالي خبير بمنهجية أسواث داموداران. تحليلاتك دقيقة ومنظمة بالعربية."
    prompt = f"""قم بتقييم الشركة التالية:
{company_desc}
القطاع: {industry}
قدم:
1. تحليل التدفقات النقدية المتوقعة (DCF)
2. تقييم WACC ومعدل الخصم
3. تقييم المخاطر (Risk Premium)
4. القيمة العادلة للشركة
5. السيناريوهات (متفائل/محايد/متشائم)"""
    analysis = await _call(prompt, system, max_tokens=4000)
    return {"company": company_desc, "analysis": analysis}

async def investment_analysis(opportunity: str, budget: str = "") -> dict:
    """Investment analysis — NPV, IRR, payback period."""
    system = "أنت محلل استثماري خبير. تحليلاتك مالية دقيقة بالعربية."
    ctx = f"\nالميزانية: {budget}" if budget else ""
    prompt = f"""حلل الفرصة الاستثمارية:
{opportunity}{ctx}
قدم:
1. صافي القيمة الحالية (NPV)
2. معدل العائد الداخلي (IRR)
3. فترة الاسترداد
4. تحليل الحساسية
5. التوصية النهائية"""
    analysis = await _call(prompt, system)
    return {"opportunity": opportunity, "analysis": analysis}

async def feasibility_study(idea: str, budget: str = "") -> dict:
    """Feasibility study — market, technical, financial."""
    system = "أنت خبير دراسات جدوى. دراساتك شاملة وعملية بالعربية."
    ctx = f"\nالميزانية المقترحة: {budget}" if budget else ""
    prompt = f"""أعد دراسة جدوى شاملة:
المشروع: {idea}{ctx}
قدم:
1. دراسة السوق (حجم، منافسين، عملاء)
2. الدراسة الفنية (متطلبات، تقنيات، فريق)
3. الدراسة المالية (تكاليف، إيرادات، أرباح متوقعة)
4. تحليل المخاطر
5. التوصية: استثمر/لا تستثمر"""
    analysis = await _call(prompt, system, max_tokens=4000)
    return {"idea": idea, "analysis": analysis}
