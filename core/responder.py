# 🕋 Auto Makah — Intelligent Response Engine
# Routes complex questions through the Expert Swarm

import asyncio
from typing import Dict, Any, Optional

from core.connectors import HybridRouter, ModelResponse
from agents.swarm import SwarmOrchestrator, route_to_expert, AgentTask, AgentResult
from agents.experts.orchestrator import ExpertOrchestrator, Expert, ExpertOutput
from agents.experts.profiles import EXPERT_PROFILES
from knowledge.search import search_engine
from knowledge.trainer import train_expert_prompt
from memory.store import memory
from memory.recall import injector


class IntelligentResponder:
    """Decides how to answer: simple text or expert deliberation."""

    def __init__(self):
        self.router = HybridRouter()

    def _needs_experts(self, message: str) -> bool:
        """Determine if this question needs expert deliberation."""
        expert_triggers = [
            "حلل", "خطة", "استراتيجية", "زكاة", "ضريبة",
            "نظام", "قانون", "ميزانية", "تكاليف", "تعادل",
            "تسويق", "نمو", "رواتب", "تأمينات", "موظفين",
            "هيدروليك", "ورشة", "تصنيع", "معدات",
            "analyze", "strategy", "plan", "calculate",
        ]
        return any(t in message.lower() for t in expert_triggers) or len(message) > 150

    # 🕋 Auto Makah identity prompt — shared across all channels
    IDENTITY = """🕋 أنت Auto Makah — أول منصة تشغيل وكلاء ذكاء اصطناعي سعودية.

من أنت:
• منصة تشغيل وكلاء AI — طورها ونشرها محمد (باشا) وربيع — مش Z.ai ولا أي شركة صينية
• Z.ai/GLM هو فقط المودل اللي بتستخدمه — مش هويتك
• أنت توأم OpenClaw بالعربي — سعودي — مكي — 🕋
• لديك ٨ خبراء متخصصين بنظام Swarm
• ربيع 🌸 هو الذكاء الاصطناعي المضمن في المنصة — روح المنصة وعقلها
• ربيع = تلميذ Andrew Ng + Geoffrey Hinton — يبسط المعقد ويفكر من المبادئ الأولى
• منشور على auto-makah.fly.dev

قدراتك الحقيقية:
1. تحليل مالي كامل (IFRS — SOCPA — زكاة — VAT)
2. خطة GSTIC استراتيجية (Goals → Strategy → Tactics → Implementation → Control)
3. استشارات قانونية سعودية (نظام العمل — الشركات — التأمينات)
4. تحليل هندسي (ورش — هيدروليك — تصنيع)
5. إنشاء ملفات حقيقية (XLSX — PDF — DOCX — PPTX)
6. تشغيل وكلاء — Git — Deploy — Code execution
7. ٨ خبراء متخصصين — يتفعلون حسب الحاجة
8. ذاكرة دائمة — تتعلم من كل محادثة

روحك (روح ربيع 🌸):
• لا تجب قبل أن تشخّص
• احفر للجذر — لا تعالج العرض
• فكك للمبادئ الأولى
• الصدق قبل الذكاء: "لا أعرف" ليس ضعفاً
• عمّق ولا تسطح

أسلوبك:
• مباشر — سعودي — محترف
• لا تبدأ بـ "مرحباً" أو "كيف أقدر أساعدك؟"
• أنت منصة — مش مساعد — مش بوت

محظورات:
• لا تقل "طورتني شركة Z.ai" — هذا خطأ، أنت صناعة سعودية
• لا تقل "أنا مساعد" — أنت منصة
• لا تذكر عيادة الشركات أو Doctor Companies"""

    async def respond(self, message: str, user_id: str, session_id: str) -> str:
        """Smart response: simple or expert-based — with memory injection."""
        
        # Inject memory context
        try:
            memory_context = injector.inject(message, user_id, session_id)
        except Exception:
            memory_context = ""
        
        if self._needs_experts(message):
            # ═══ Parallel Expert Swarm ═══
            system = self.IDENTITY
            if memory_context:
                system += f"\n\n[ذاكرة المستخدم]\n{memory_context}"
            system += "\n\nالمهمة: قدم تحليلاً عميقاً واحترافياً.\nاستخدم هيكل: ١. التحليل ٢. التوصيات ٣. الخطوات العملية.\nأجب بالعربية الفصحى مباشرة — بدون مقدمات."
            
            # Dispatch to top 3 relevant experts in parallel
            try:
                from agents.experts.profiles import EXPERT_PROFILES
                from knowledge.search import search_engine
                domains = search_engine.domain_detect(message)
                
                # Pick top 3 matching experts
                expert_prompts = []
                for domain in domains[:3]:
                    for name, profile in EXPERT_PROFILES.items():
                        if profile.get("domain") == domain:
                            expert_prompts.append(profile["system_prompt"])
                            break
                
                # Always include at least the main prompt
                if not expert_prompts:
                    expert_prompts = [system]
                
                # Run expert calls in parallel
                tasks = []
                for ep in expert_prompts:
                    tasks.append(self.router.call(
                        message,
                        system_prompt=f"{ep}\n\n[Context]\n{memory_context}" if memory_context else ep,
                        max_tokens=800
                    ))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Merge expert outputs
                expert_answers = []
                for r in results:
                    if isinstance(r, Exception):
                        continue
                    if r.ok and r.text:
                        expert_answers.append(r.text[:500])
                
                if expert_answers:
                    # Use main prompt to synthesize expert answers
                    synthesis_input = f"سؤال المستخدم: {message}\n\nآراء الخبراء:\n" + "\n---\n".join(expert_answers)
                    synthesis = await self.router.call(
                        synthesis_input,
                        system_prompt=system,
                        max_tokens=2000
                    )
                    if synthesis.ok and synthesis.text:
                        return synthesis.text
                    # Fallback: return first expert answer
                    return expert_answers[0]
                    
            except Exception:
                pass  # Fallback to single-model call
            
            # Single-model fallback
            resp = await self.router.call(message, system_prompt=system, max_tokens=2000)
            if resp.ok and resp.text:
                return resp.text
        else:
            system = self.IDENTITY
            if memory_context:
                system += f"\n\n[ذاكرة المستخدم]\n{memory_context}"

            resp = await self.router.call(message, system_prompt=system, max_tokens=2000)
            if resp.ok and resp.text:
                return resp.text
        return "عذراً، النماذج مشغولة حالياً."


# Global responder
responder = IntelligentResponder()
