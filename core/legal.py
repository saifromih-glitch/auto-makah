"""
Legal Agent Team — Saudi law specialized multi-agent analysis
"""
import os, httpx, asyncio, json

ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")

DOMAINS = {
    "labor": "نظام العمل السعودي",
    "companies": "نظام الشركات السعودي", 
    "commercial": "الأنظمة التجارية السعودية",
    "zakat": "نظام الزكاة والضرائب",
    "realestate": "الأنظمة العقارية السعودية",
}

async def _call(prompt: str, system: str = "", max_tokens: int = 3000) -> str:
    if not ZENMUX_KEY:
        return "Error: No ZENMUX_API_KEY configured"
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

async def research(question: str, domain: str = "labor") -> dict:
    """Legal research — find relevant laws and regulations."""
    dom = DOMAINS.get(domain, "النظام السعودي")
    system = "أنت باحث قانوني سعودي خبير. تقدم نصوصاً نظامية دقيقة مع مصادرها."
    prompt = f"""السؤال القانوني: {question}
المجال: {dom}

قدم بحثاً قانونياً منظماً يتضمن:
1. النصوص النظامية ذات الصلة (مع أرقام المواد إن أمكن)
2. اللوائح التنفيذية المرتبطة
3. السوابق القضائية أو الاجتهادات (إن وجدت)
4. خلاصة قانونية واضحة"""
    analysis = await _call(prompt, system)
    return {"question": question, "domain": domain, "research": analysis}

async def analyze(question: str, research_text: str = "", domain: str = "labor") -> dict:
    """Legal analysis — evaluate situation against the law."""
    dom = DOMAINS.get(domain, "النظام السعودي")
    system = "أنت محلل قانوني سعودي خبير. تقدم تحليلات دقيقة مع تقييم المخاطر."
    ctx = f"\nنتائج البحث القانوني:\n{research_text[:2000]}" if research_text else ""
    prompt = f"""السؤال: {question}
المجال: {dom}{ctx}

قدم تحليلاً قانونياً:
1. مدى انطباق النصوص القانونية على الحالة
2. جوانب المخالفة أو الالتزام
3. تقدير المخاطر القانونية (منخفض/متوسط/عالي)
4. التوصيات العملية"""
    analysis = await _call(prompt, system)
    return {"analysis": analysis}

async def full_pipeline(question: str, domain: str = "labor") -> dict:
    """Complete legal pipeline: research + analysis."""
    research_result = await research(question, domain)
    analysis_result = await analyze(question, research_result.get("research", ""), domain)
    return {
        "question": question,
        "domain": domain,
        "domain_name": DOMAINS.get(domain, ""),
        "research": research_result.get("research", ""),
        "analysis": analysis_result.get("analysis", ""),
    }
