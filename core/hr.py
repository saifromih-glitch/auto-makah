"""
HR & Recruitment Agent — job descriptions, interviews, evaluation
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

async def job_description(role: str, industry: str = "", level: str = "متوسط") -> dict:
    """Generate professional job description."""
    system = "أنت خبير موارد بشرية. توصيفاتك الوظيفية احترافية بالعربية."
    prompt = f"""اكتب وصفاً وظيفياً:
المسمى: {role}
القطاع: {industry}
المستوى: {level}
قدم:
1. المسمى الوظيفي
2. المسؤوليات
3. المؤهلات المطلوبة
4. المهارات
5. نطاق الراتب التقريبي (للسوق السعودي)"""
    a = await _ai(prompt, system)
    return {"role": role, "job_description": a}

async def interview_questions(role: str, focus: str = "تقني وسلوكي") -> dict:
    """Generate interview questions."""
    system = "أنت خبير توظيف. أسئلتك ذكية وتكشف القدرات الحقيقية بالعربية."
    prompt = f"""أعدد أسئلة مقابلة:
الوظيفة: {role}
التركيز: {focus}
قدم:
1. أسئلة تقنية (٥)
2. أسئلة سلوكية (٥)
3. أسئلة ذكاء عاطفي (٣)
4. نموذج إجابة متوقع لكل سؤال
5. معايير التقييم"""
    a = await _ai(prompt, system)
    return {"role": role, "questions": a}

async def employee_evaluation(role: str, performance: str) -> dict:
    """Evaluate employee performance."""
    system = "أنت خبير تقييم أداء. تقييماتك عادلة وبناءة بالعربية."
    prompt = f"""قيم أداء الموظف:
الوظيفة: {role}
الأداء: {performance}
قدم:
1. نقاط القوة
2. مجالات التحسين
3. تقييم رقمي (من ١٠)
4. خطة تطوير
5. توصية (ترقية/مكافأة/تدريب)"""
    a = await _ai(prompt, system)
    return {"role": role, "evaluation": a}

async def cv_analyzer(cv_text: str) -> dict:
    """Analyze CV/resume."""
    system = "أنت خبير توظيف. تحليلاتك دقيقة وعملية بالعربية."
    prompt = f"""حلل السيرة الذاتية:
{cv_text[:4000]}
قدم:
1. ملخص عام
2. نقاط القوة
3. نقاط الضعف/الفجوات
4. مدى ملاءمتها للسوق السعودي
5. توصيات للتحسين"""
    a = await _ai(prompt, system)
    return {"analysis": a}
