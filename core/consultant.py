"""
Consultant Agent — Business consulting with 5 frameworks
Uses ZenMux GLM-5.2-free (free model)
"""
import os, httpx, json, asyncio

ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")

FRAMEWORKS = {
    "swot": "نقاط القوة والضعف والفرص والتهديدات",
    "porter": "تحليل القوى الخمس لبورتر",
    "pestel": "التحليل السياسي والاقتصادي والاجتماعي والتقني والبيئي والقانوني",
    "bmc": "نموذج العمل التجاري (9 مكونات)",
    "value_prop": "تصميم عرض القيمة",
}

async def _call_ai(prompt: str, system: str = "", max_tokens: int = 3000) -> str:
    """Call ZenMux AI and return text response."""
    if not ZENMUX_KEY:
        return "Error: No ZENMUX_API_KEY configured"
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                ZENMUX_URL,
                headers={
                    "Authorization": f"Bearer {ZENMUX_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "z-ai/glm-5.2-free",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            return f"API error: {data}"
    except Exception as e:
        return f"Connection error: {str(e)}"

async def consult(topic: str, framework: str = "swot", context: str = "") -> dict:
    """
    Run a business consulting analysis.
    
    Args:
        topic: Business topic to analyze
        framework: swot, porter, pestel, bmc, value_prop
        context: Additional context
    
    Returns:
        dict with analysis results
    """
    if framework not in FRAMEWORKS:
        framework = "swot"
    
    fw_desc = FRAMEWORKS[framework]
    
    system = f"أنت مستشار أعمال خبير ومدير استراتيجي. تقدم تحليلات منظمة بالعربية."
    
    prompt = f"""استخدم {fw_desc} لتحليل الموضوع التالي.

الموضوع: {topic}
{f'السياق: {context}' if context else ''}

قدم تحليلاً منظماً يشمل:
1. التحليل باستخدام الإطار المحدد
2. 3-5 توصيات قابلة للتنفيذ
3. خريطة طريق (خطوات محددة)
4. المخاطر الرئيسية وكيفية تجنبها

كن دقيقاً ومحدداً. استخدم لغة عربية واضحة."""

    analysis = await _call_ai(prompt, system)
    
    return {
        "topic": topic,
        "framework": framework,
        "analysis": analysis,
    }

async def compare(items: list, criteria: list = None) -> dict:
    """Compare multiple items."""
    if not criteria:
        criteria = ["التكلفة", "الجودة", "الوقت", "المخاطر", "العائد"]
    
    items_str = "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
    criteria_str = "، ".join(criteria)
    
    prompt = f"""قارن بين العناصر التالية:
{items_str}

معايير المقارنة: {criteria_str}

قدم:
1. جدول مقارنة منظم
2. نقاط القوة والضعف لكل عنصر
3. التوصية النهائية مع تبرير
4. ترتيب حسب الأولوية"""

    analysis = await _call_ai(prompt, "أنت محلل أعمال خبير. قدم تحليلات منظمة بالعربية.")
    
    return {
        "items": items,
        "criteria": criteria,
        "analysis": analysis,
    }

# Strategy frameworks
async def hedgehog(company: str, context: str = "") -> dict:
    """Jim Collins' Hedgehog Concept."""
    prompt = f"""طبق مفهوم القنفذ (Hedgehog Concept) لجيم كولينز على:
الشركة: {company}
{f'السياق: {context}' if context else ''}

أجب عن الأسئلة الثلاثة:
1. ما الذي أنت شغوف به بشدة؟
2. ما الذي يمكنك أن تكون الأفضل فيه في العالم؟
3. ما الذي يحرك محركك الاقتصادي؟
4. نقطة التقاطع بين الثلاث دوائر (Hedgehog Concept)"""
    
    analysis = await _call_ai(prompt, "أنت مستشار استراتيجي خبير.")
    return {"framework": "hedgehog", "analysis": analysis}

async def blue_ocean(industry: str, context: str = "") -> dict:
    """Blue Ocean Strategy."""
    prompt = f"""طبق استراتيجية المحيط الأزرق على:
الصناعة: {industry}
{f'السياق: {context}' if context else ''}

حلل:
1. عوامل التنافس الحالية (المحيط الأحمر)
2. عوامل يمكن حذفها
3. عوامل يمكن خفضها
4. عوامل يمكن رفعها
5. عوامل جديدة يمكن ابتكارها
6. منحنى القيمة الجديد"""
    
    analysis = await _call_ai(prompt, "أنت مستشار استراتيجي خبير.")
    return {"framework": "blue_ocean", "analysis": analysis}
