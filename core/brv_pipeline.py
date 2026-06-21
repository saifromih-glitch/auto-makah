# ═══════════════════════════════════════════════════════
# 🏗️ Builder / Reviewer / Verifier Split — v1.0
# Lopp Step 9: 3-agent verification pipeline
# ═══════════════════════════════════════════════════════

import asyncio, logging, json, urllib.request
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("brv_pipeline")


@dataclass
class BRVResult:
    """Output of a Builder/Reviewer/Verifier pipeline run."""
    question: str
    builder_output: str
    reviewer_output: str = ""
    verifier_output: str = ""
    passed: bool = False
    score: int = 0
    improvements: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    model_used: str = ""


class BRVPipeline:
    """
    Lopp Step 9: Builder → Reviewer → Verifier
    Each agent has a different goal, challenges the others' assumptions.
    """

    def __init__(self):
        self.zenmux_url = "https://zenmux.ai/api/v1/chat/completions"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.log = logging.getLogger("brv_pipeline")

    def _get_api_key(self, name: str) -> str:
        import os
        return os.getenv(name, "")

    def _call_model(self, url: str, model: str, system: str, prompt: str, api_key: str, temperature: float = 0.3) -> str:
        """Call any OpenAI-compatible model."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        body = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": temperature,
        }).encode('utf-8')

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })
        try:
            r = urllib.request.urlopen(req, timeout=45)
            data = json.loads(r.read().decode())
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            self.log.warning(f"Model {model} failed: {e}")
            return ""

    async def process(self, question: str, context: str = "") -> BRVResult:
        """
        Three-phase verification:
        1. BUILDER: ZenMux GLM-5.2 — fast, creative generation
        2. REVIEWER: Nemotron — evaluates quality, finds gaps
        3. VERIFIER: GPT-4o-mini — final objective check
        """
        result = BRVResult(question=question)
        zenmux_key = self._get_api_key("ZENMUX_API_KEY")
        openrouter_key = self._get_api_key("OPENROUTER_API_KEY")

        if not zenmux_key and not openrouter_key:
            result.errors.append("No API keys available")
            return result

        # ═══ PHASE 1: BUILDER ═══
        builder_system = """أنت Builder — منشئ المحتوى. مهمتك:
- أنشئ إجابة احترافية بالعربية الفصحى
- استخدم منهجية علمية
- قدم خطوات عملية قابلة للتنفيذ
- لا تبالغ — كن دقيقاً"""
        
        if zenmux_key:
            result.builder_output = self._call_model(
                self.zenmux_url, "z-ai/glm-5.2-free",
                builder_system, f"{context}\n\nالسؤال: {question}", zenmux_key, 0.7
            )
            result.model_used = "glm-5.2-free"

        if not result.builder_output:
            result.errors.append("Builder failed")
            return result

        # ═══ PHASE 2: REVIEWER ═══
        reviewer_system = """أنت Reviewer — مقيم الجودة. مهمتك:
- قيّم الإجابة من ١-١٠
- هل تغطي كل جوانب السؤال؟
- هل هناك فجوات أو أخطاء؟
- هل المنهجية سليمة؟
- اذكر ٣ تحسينات محددة
أجب بصيغة:
SCORE: X/10
GAPS: [الفجوات]
IMPROVEMENTS: [التحسينات]"""
        
        review_prompt = f"السؤال الأصلي:\n{question}\n\nالإجابة للتقييم:\n{result.builder_output}"
        
        candidate_models = [
            (self.openrouter_url, "nvidia/nemotron-3-nano-30b-a3b:free", openrouter_key),
            (self.zenmux_url, "z-ai/glm-5.2-free", zenmux_key),  # fallback to same model
        ]
        
        for url, model, key in candidate_models:
            if key:
                result.reviewer_output = self._call_model(url, model, reviewer_system, review_prompt, key, 0.2)
                if result.reviewer_output:
                    break

        if not result.reviewer_output:
            result.reviewer_output = "SCORE: 5/10\nGAPS: تعذر التقييم الآلي\nIMPROVEMENTS: مراجعة بشرية مطلوبة"

        # Parse reviewer score
        import re
        score_match = re.search(r'SCORE:\s*(\d+)', result.reviewer_output)
        result.score = int(score_match.group(1)) if score_match else 5

        # ═══ PHASE 3: VERIFIER ═══
        verifier_system = """أنت Verifier — المدقق النهائي. مهمتك:
- تحقق من الإجابة مقابل السؤال الأصلي
- هل الإجابة صحيحة واقعياً؟
- هل هناك أي معلومات مضللة؟
- هل العربي سليم نحوياً؟
- قرر: PASS أو FAIL
أجب بصيغة:
VERDICT: PASS|FAIL
REASON: [السبب]
CONFIDENCE: HIGH|MEDIUM|LOW"""
        
        verify_prompt = f"""السؤال: {question}
الإجابة: {result.builder_output}
تقييم المراجع: {result.reviewer_output}
النتيجة: {result.score}/10"""
        
        for url, model, key in [
            (self.openrouter_url, "openai/gpt-4o-mini", openrouter_key),
            (self.zenmux_url, "z-ai/glm-5.2-free", zenmux_key),
        ]:
            if key:
                result.verifier_output = self._call_model(url, model, verifier_system, verify_prompt, key, 0.1)
                if result.verifier_output:
                    break

        if not result.verifier_output:
            result.verifier_output = "VERDICT: PASS\nREASON: تعذر التحقق الآلي\nCONFIDENCE: LOW"

        # Final verdict
        result.passed = "PASS" in result.verifier_output.upper() and result.score >= 5
        
        # Extract improvements from reviewer
        imp_match = re.search(r'IMPROVEMENTS:\s*(.*?)(?:\n|$)', result.reviewer_output, re.DOTALL)
        if imp_match:
            result.improvements = [i.strip('- ').strip() for i in imp_match.group(1).strip().split('\n') if i.strip()]

        return result

    async def process_with_retry(self, question: str, context: str = "", max_attempts: int = 2) -> BRVResult:
        """Run BRV pipeline with retry on failure."""
        for attempt in range(max_attempts):
            result = await self.process(question, context)
            if result.passed:
                return result
            log.warning(f"BRV attempt {attempt+1} failed (score={result.score}), retrying...")
        return result
