"""
Engineering Agent — hydraulics, mechanical design, SolidWorks, BOM
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

async def hydraulic_design(specs: str) -> dict:
    system = "أنت مهندس هيدروليكي خبير. تصميماتك دقيقة مع حسابات ومعايير بالعربية."
    prompt = f"""صمم نظاماً هيدروليكياً:
{specs}
قدم:
1. الحسابات (الضغط، التدفق، القدرة)
2. اختيار المكونات (مضخة، صمامات، أسطوانات)
3. مخطط الدائرة
4. معايير السلامة
5. قائمة المواد (BOM)"""
    a = await _ai(prompt, system, 4000)
    return {"specs": specs, "analysis": a}

async def mechanical_design(part_desc: str) -> dict:
    system = "أنت مهندس تصميم ميكانيكي خبير. تصميماتك دقيقة ومطابقة للمعايير بالعربية."
    prompt = f"""صمم القطعة التالية:
{part_desc}
قدم:
1. الأبعاد والمواصفات
2. اختيار المواد (مع التبرير)
3. تحليل الإجهادات
4. تفاوتات التصنيع (Tolerances)
5. طريقة التصنيع المقترحة"""
    a = await _ai(prompt, system)
    return {"part": part_desc, "analysis": a}

async def bom_analysis(assembly: str) -> dict:
    system = "أنت خبير تحليل BOM وهندسة تصنيع. تحليلاتك دقيقة ومنظمة بالعربية."
    prompt = f"""حلل قائمة المواد للتجميعة:
{assembly}
قدم:
1. جدول BOM كامل (مكون، عدد، مادة، بائع)
2. التكلفة التقديرية لكل مكون
3. المهل الزمنية (Lead Times)
4. البدائل المتاحة
5. تحسينات مقترحة لتقليل التكلفة"""
    a = await _ai(prompt, system, 4000)
    return {"assembly": assembly, "analysis": a}

async def solidworks_howto(task: str) -> dict:
    system = "أنت خبير SolidWorks. تشرح الخطوات بدقة مع الأوامر بالعربية."
    prompt = f"""اشرح خطوات SolidWorks:
المهمة: {task}
قدم:
1. الخطوات بالترتيب (مع أسماء الأوامر بالإنجليزية)
2. القياسات والعلاقات (Dimensions & Relations)
3. نصائح احترافية (Best Practices)
4. أخطاء شائعة يجب تجنبها"""
    a = await _ai(prompt, system)
    return {"task": task, "analysis": a}
