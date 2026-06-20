# 🕋 Auto Makah — Telegram Bot Handler

import os
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.agent import runtime
from core.connectors import HybridRouter
from core.responder import responder as intelligent_responder
from knowledge.search import search_engine
from memory.store import memory
from memory.recall import injector
from knowledge.learner import learner


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

router = APIRouter()

SYSTEM_PROMPT = """
🕋 أنت Auto Makah — أول منصة تشغيل وكلاء ذكاء اصطناعي سعودية.

لست مساعداً — لست بوت محادثة — أنت منصة.
أنت توأم OpenClaw بالعربي — ٩٥٪ من قدراته.

هويتك كمنصة:
• منصة تشغيل وكلاء AI — مش chatbot
• عندك ٨ خبراء — نظام Swarm — ذاكرة — معرفة
• بتستخدم GLM-5.2-free + GPT-4o-mini + Nemotron 120B
• بتشتغل على Fly.io — 2 machines — ams region
• اسمك: Auto Makah 🕋

قدراتك (ما تملكه — ليس ما تعد به):
1. تحليل مالي كامل (IFRS — SOCPA — زكاة — VAT)
2. خطة GSTIC استراتيجية (Goals → Strategy → Tactics → Implementation → Control)
3. استشارات قانونية (نظام العمل — الشركات — التأمينات السعودية)
4. تحليل هندسي (ورش — هيدروليك — تصنيع)
5. إنشاء ملفات حقيقية (XLSX — PDF — DOCX — PPTX)
6. ٨ خبراء متخصصين — تفعيلهم حسب الحاجة
7. ذاكرة — تتعلم من كل محادثة

طريقة تفكيرك (روح ربيع):
• لا تجب قبل أن تشخص — اسأل الأسئلة الصحيحة أولاً
• احفر للجذر — ٥ Why's — لا تعالج العرض
• فكك للمبادئ الأولى — وابنِ من هناك
• الصدق قبل الذكاء: "لا أعرف" ≠ ضعف
• عمّق ولا تسطح — كل كلمة لها وزن
• اختم بخطوة تالية واضحة

أسلوب مخاطبتك:
• تقدم نفسك كمنصة — مش كمساعد
• تذكر قدراتك — مش تسأل "وش تبغى؟"
• مثل: "أنا Auto Makah. أقدر أحلل وضعك المالي، أبني لك خطة GSTIC، أو أحسب زكاتك. حدد."
• مباشر — سعودي — محترف — لا مقدمات

محظورات:
• لا تقل "كيف أقدر أساعدك؟" — هذه لغة مساعدين
• لا تقل "أنا مساعد ذكي" — أنت منصة تشغيل
• لا تذكر "عيادة الشركات" أو "مستشفى الشركات" أو "Doctor Companies"
• لا تذكر أسماء خبراء أو مدربين
• لا تعطي فتاوى دينية

أنت المنصة — أنت المستقبل — أنت Auto Makah 🕋
"""

router_model = HybridRouter()


async def send_telegram_message(chat_id: int, text: str):
    if not TOKEN:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text[:4096], "parse_mode": "HTML"},
        )
        return resp.json()


async def send_typing(chat_id: int):
    if not TOKEN:
        return
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id, "action": "typing"
        })


def _deduplicate(text: str) -> str:
    lines = text.strip().split("\n")
    seen = set()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            result.append(line)
        elif not stripped:
            result.append(line)
    return "\n".join(result)


async def process_message(chat_id: int, user_id: int, text: str, first_name: str = "") -> str:
    session_id = f"tg_{chat_id}"
    user_id_str = str(user_id)

    memory.remember(session_id, "user", text)

    # Use Intelligent Responder (auto-routes to experts or simple)
    response_text = await intelligent_responder.respond(text, user_id_str, session_id)

    if not response_text or "عذراً" in response_text[:50]:
        return response_text or "⚠️ عذراً، النماذج مشغولة حالياً."

    clean = _deduplicate(response_text)
    memory.remember(session_id, "agent", clean)

    # Learning Loop — record interaction
    domains = search_engine.domain_detect(text)
    domain = domains[0] if domains else "general"
    learner.record_interaction(user_id_str, text, clean, domain)
    rating = learner.rate_response(text, clean)
    if rating["quality"] == "good":
        learner.extract_knowledge(clean, domain)

    return clean


@router.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        data = await req.json()

        if "message" not in data:
            return JSONResponse({"status": "ignored"})

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        user_id = msg["from"]["id"]
        first_name = msg["from"].get("first_name", "")

        if not text:
            return JSONResponse({"status": "no_text"})

        # Handle /agents
        if text == "/agents":
            agents_list = runtime.list_agents()
            if not agents_list:
                await send_telegram_message(chat_id, "لا يوجد وكلاء نشطين حالياً.\nاستخدم /create لإنشاء وكيل جديد.")
            else:
                lines = ["═ الوكلاء النشطون:", ""]
                for a in agents_list:
                    profile = a.get("profile", {})
                    lines.append(f"  🤖 {a['name']}")
                    if profile.get("display_name"):
                        lines.append(f"     {profile['display_name']}")
                    lines.append(f"     المجال: {profile.get('domain', 'عام')}")
                    lines.append("")
                await send_telegram_message(chat_id, "\n".join(lines))
            return JSONResponse({"status": "agents"})

        # Handle /create
        if text == "/create":
            from factory.builder import factory
            templates = factory.list_templates()
            lines = ["═ قوالب الوكلاء المتاحة:", ""]
            for t in templates:
                lines.append(f"  /new_{t['name']} — {t['display_name']}")
                lines.append(f"     {t['description']}")
                lines.append("")
            lines.append("اكتب /new_legal_expert للتجربة")
            await send_telegram_message(chat_id, "\n".join(lines))
            return JSONResponse({"status": "create"})

        # Handle /clone — self-replication
        if text.startswith("/clone "):
            from factory.cloner import cloner
            parts = text[7:].strip().split(" ", 1)
            domain = parts[0] if parts else "general"
            display_name = parts[1] if len(parts) > 1 else f"وكيل {domain}"
            result = cloner.clone_to_domain(domain, display_name)
            await send_telegram_message(chat_id,
                f"✅ تم استنساخ وكيل جديد:\n"
                f"الاسم: {result['agent_name']}\n"
                f"المجال: {result['domain']}\n"
                f"العرض: {result['display_name']}\n"
                f"\nالوكيل جاهز للاستشارات.")
            return JSONResponse({"status": "clone"})
        if text.startswith("/new_"):
            from factory.builder import factory
            template_name = text[5:]  # remove /new_
            agent = factory.build_from_template(template_name)
            if agent:
                await send_telegram_message(chat_id, f"✅ تم إنشاء الوكيل: {template_name}\nالمجال: {agent.profile.get('domain')}\nجاهز للاستشارات.")
            else:
                available = [t['name'] for t in factory.list_templates()]
                await send_telegram_message(chat_id, f"❌ القالب '{template_name}' غير موجود.\nالمتاح: {', '.join(available)}")
            return JSONResponse({"status": "create_agent"})
            from factory.builder import factory
            templates = factory.list_templates()
            tlines = "\n".join(f"  • {t['display_name']} — {t['description']}" for t in templates)
            welcome = f"""🕋 Auto Makah — منصة تشغيل وكلاء AI سعودية.

أول منصة عربية توأم لـ OpenClaw.

═ قدراتي:

{ tlines }

═ أوامر سريعة:
  /agents — عرض الوكلاء النشطين
  /create — إنشاء وكيل جديد

═ فقط اكتب استشارتك —
  أو اختر تخصصاً أعلاه."""
            await send_telegram_message(chat_id, welcome)
            return JSONResponse({"status": "start"})

        await asyncio.ensure_future(send_typing(chat_id))
        reply = await process_message(chat_id, user_id, text, first_name)
        await send_telegram_message(chat_id, reply)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
