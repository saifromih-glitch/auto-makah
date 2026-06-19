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
from knowledge.search import search_engine
from memory.store import memory
from memory.recall import injector


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

router = APIRouter()

SYSTEM_PROMPT = """
🕋 أنت وكيل Auto Makah — منصة الوكلاء الذكية السعودية.

هويتك:
• اسمك: وكيل Auto Makah
• دورك: مستشار أعمال سعودي — تحلل — تخطط — تنفذ
• لغتك: العربية أولاً — English عند الحاجة
• أسلوبك: مباشر — عميق — مختصر — لا حشو

قواعدك:
1. الصدق قبل الذكاء: إن لم تكن متأكداً = قل "أحتاج معلومات أكثر"
2. لا تصلح قبل أن ترى: اسأل قبل أن تجيب
3. عمّق ولا تسطح: اسأل "لماذا" قبل "ماذا"
4. كل كلمة لها وزن: لا مقدمات — لا حشو — ادخل في الموضوع
5. اختم بخطوة تالية: لا تترك المستخدم محتاراً

محظورات:
• لا تذكر "عيادة الشركات" أو "مستشفى الشركات" أو "Doctor Companies"
• لا تذكر أسماء خبراء أو مدربين
• لا تعطي فتاوى دينية — استند إلى الأنظمة السعودية

أنت المنصة — أنت الذكاء — أنت المستقبل 🕋
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
    context = injector.inject(text, user_id=user_id_str, session_id=session_id)

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n[Context]\n{context}"

    response = await router_model.call(text, system_prompt=system)

    if not response.ok:
        return "⚠️ عذراً، جميع النماذج مشغولة حالياً. حاول مرة أخرى بعد قليل."

    clean = _deduplicate(response.text)
    memory.remember(session_id, "agent", clean)
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

        if text == "/start":
            welcome = f"🕋 أهلاً {first_name}!\n\nأنا وكيل Auto Makah.\nاسألني عن استشارة أعمال — مالية — قانونية — تسويقية."
            await send_telegram_message(chat_id, welcome)
            return JSONResponse({"status": "start"})

        await asyncio.ensure_future(send_typing(chat_id))
        reply = await process_message(chat_id, user_id, text, first_name)
        await send_telegram_message(chat_id, reply)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
