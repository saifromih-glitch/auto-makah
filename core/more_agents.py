"""
Agents Hall — lists all agents + API docs, Translation, Email, Social
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

# ═══ Translation ═══

async def translate(text: str, from_lang: str = "ar", to_lang: str = "en") -> dict:
    """Professional Arabic ↔ English translation."""
    system = "أنت مترجم محترف. تترجم بدقة مع مراعاة السياق والثقافة."
    prompt = f"ترجم النص التالي من {from_lang} إلى {to_lang}:\n\n{text}"
    a = await _ai(prompt, system)
    return {"from": from_lang, "to": to_lang, "original": text, "translation": a}

async def localize(text: str, target_region: str = "السعودية") -> dict:
    """Localize text to Saudi/Arabic context."""
    system = "أنت خبير تعريب وتوطين المحتوى للسوق السعودي."
    prompt = f"""موطِّن (Localize) النص التالي ليناسب السوق السعودي (وليس مجرد ترجمة):
{text}
المنطقة: {target_region}"""
    a = await _ai(prompt, system)
    return {"region": target_region, "original": text, "localized": a}

# ═══ Email Composer ═══

async def compose_email(purpose: str, tone: str = "رسمي", recipient: str = "") -> dict:
    """Draft professional emails."""
    system = "أنت كاتب رسائل محترف. رسائلك مهذبة وواضحة وفعالة."
    prompt = f"""اكتب بريداً إلكترونياً:
الغرض: {purpose}
النبرة: {tone}
المستلم: {recipient}
قدم: 1. العنوان 2. التحية 3. المتن 4. الخاتمة 5. التوقيع"""
    a = await _ai(prompt, system)
    return {"purpose": purpose, "email": a}

# ═══ Social Media ═══

async def social_post(topic: str, platform: str = "twitter", tone: str = "احترافي") -> dict:
    """Create social media posts optimized per platform."""
    limits = {"twitter": "٢٨٠ حرف", "linkedin": "٣٠٠٠ حرف", "instagram": "٢٢٠٠ حرف", "tiktok": "١٥٠ كلمة"}
    system = f"أنت خبير تواصل اجتماعي. تنشئ محتوى محسن لكل منصة بالعربية."
    prompt = f"""اكتب منشوراً لـ {platform}:
الموضوع: {topic}
النبرة: {tone}
الحد الأقصى: {limits.get(platform, 'حر')}
قدم: 1. النص 2. الهاشتاقات 3. أفضل وقت للنشر 4. دعوة للتفاعل (CTA)"""
    a = await _ai(prompt, system)
    return {"platform": platform, "topic": topic, "post": a}

async def content_calendar(business: str, days: int = 7) -> dict:
    """Generate content calendar."""
    system = "أنت استراتيجي محتوى. تخطط منشورات فعالة لكل منصة."
    prompt = f"""خطط تقويماً للمحتوى:
النشاط التجاري: {business}
عدد الأيام: {days}
قدم جدولاً: اليوم | المنصة | الموضوع | نوع المحتوى | أفضل وقت"""
    a = await _ai(prompt, system, 4000)
    return {"business": business, "days": days, "calendar": a}

# ═══ Hall of Agents ═══

def hall_of_agents() -> dict:
    """List all available agents with their endpoints."""
    return {
        "platform": "Auto Makah",
        "url": "https://auto-makah.fly.dev",
        "total_agents": 20,
        "categories": {
            "استشارات وأعمال": [
                {"name": "Consultant", "endpoint": "POST /api/consult", "frameworks": "swot,porter,pestel,bmc,value_prop"},
                {"name": "Strategy", "endpoint": "POST /api/strategy/{framework}", "frameworks": "hedgehog,blue_ocean"},
                {"name": "Compare", "endpoint": "POST /api/compare", "desc": "مقارنة متعددة العناصر"},
                {"name": "Feasibility", "endpoint": "POST /api/feasibility", "desc": "دراسة جدوى"},
            ],
            "مالية واستثمار": [
                {"name": "Valuation", "endpoint": "POST /api/valuation", "desc": "تقييم شركات DCF/WACC"},
                {"name": "Investment", "endpoint": "POST /api/invest", "desc": "تحليل NPV/IRR"},
            ],
            "موارد بشرية": [
                {"name": "Job Description", "endpoint": "POST /api/hr/job-description"},
                {"name": "Interview", "endpoint": "POST /api/hr/interview"},
                {"name": "Evaluation", "endpoint": "POST /api/hr/evaluate"},
                {"name": "CV Analysis", "endpoint": "POST /api/hr/cv"},
            ],
            "هندسة": [
                {"name": "Hydraulic", "endpoint": "POST /api/engineering/hydraulic"},
                {"name": "Mechanical", "endpoint": "POST /api/engineering/mechanical"},
                {"name": "BOM", "endpoint": "POST /api/engineering/bom"},
                {"name": "SolidWorks", "endpoint": "POST /api/engineering/solidworks"},
            ],
            "تسويق": [
                {"name": "AARRR", "endpoint": "POST /api/marketing/aarrr"},
                {"name": "Marketing Plan", "endpoint": "POST /api/marketing/plan"},
                {"name": "Campaign", "endpoint": "POST /api/marketing/campaign"},
            ],
            "أدوات إسلامية": [
                {"name": "Zakat", "endpoint": "POST /api/zakat"},
                {"name": "Inheritance", "endpoint": "POST /api/inheritance"},
            ],
            "أدوات عامة": [
                {"name": "Currency", "endpoint": "POST /api/currency"},
                {"name": "Units", "endpoint": "POST /api/units"},
                {"name": "Password", "endpoint": "POST /api/password"},
                {"name": "QR Code", "endpoint": "POST /api/qr"},
                {"name": "Translate", "endpoint": "POST /api/translate"},
                {"name": "Email", "endpoint": "POST /api/email"},
                {"name": "Social Post", "endpoint": "POST /api/social"},
                {"name": "Content Calendar", "endpoint": "POST /api/content-calendar"},
            ],
            "تحليل وتطوير": [
                {"name": "Evolver", "endpoint": "GET /api/evolve/code"},
                {"name": "Legal", "endpoint": "POST /api/legal"},
                {"name": "Data Analysis", "endpoint": "POST /api/analyze-data"},
                {"name": "Meeting Notes", "endpoint": "POST /api/meeting-notes"},
                {"name": "Project Plan", "endpoint": "POST /api/project-plan"},
                {"name": "Content Creator", "endpoint": "POST /api/create-content"},
                {"name": "Medical", "endpoint": "POST /api/medical/surgery-guide"},
            ],
        }
    }
