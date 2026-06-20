# ═══════════════════════════════════════════
# 🕋 Auto Makah — Model Connectors
# ═══════════════════════════════════════════

import os
import json
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelResponse:
    """Standardized model response."""
    text: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class ModelConnector:
    """Base class for model connectors."""

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        raise NotImplementedError


class GLM4Connector(ModelConnector):
    """Zhipu GLM-4 connector — free tier."""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY", "")

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        import time, httpx
        start = time.time()

        if not self.api_key:
            return ModelResponse(text="", model="glm-4", error="No API key")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "glm-4",
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                )
                data = resp.json()

                if "choices" in data:
                    return ModelResponse(
                        text=data["choices"][0]["message"]["content"],
                        model="glm-4",
                        tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
                        tokens_out=data.get("usage", {}).get("completion_tokens", 0),
                        latency_ms=int((time.time() - start) * 1000),
                    )
                return ModelResponse(text="", model="glm-4", error=str(data))
        except Exception as e:
            return ModelResponse(text="", model="glm-4", error=str(e))


class GPT4oMiniConnector(ModelConnector):
    """OpenRouter GPT-4o-mini — paid, precise."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        import time, httpx
        start = time.time()

        if not self.api_key:
            return ModelResponse(text="", model="gpt-4o-mini", error="No API key")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://auto-makah.sa",
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                )
                data = resp.json()

                if "choices" in data:
                    return ModelResponse(
                        text=data["choices"][0]["message"]["content"],
                        model="gpt-4o-mini",
                        tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
                        tokens_out=data.get("usage", {}).get("completion_tokens", 0),
                        latency_ms=int((time.time() - start) * 1000),
                    )
                return ModelResponse(text="", model="gpt-4o-mini", error=str(data))
        except Exception as e:
            return ModelResponse(text="", model="gpt-4o-mini", error=str(e))


class NemotronConnector(ModelConnector):
    """NVIDIA Nemotron 120B — free on OpenRouter."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        import time, httpx
        start = time.time()

        if not self.api_key:
            return ModelResponse(text="", model="nemotron", error="No API key")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://auto-makah.sa",
                    },
                    json={
                        "model": "nvidia/nemotron-3-super-120b-a12b:free",
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                )
                data = resp.json()

                if "choices" in data:
                    return ModelResponse(
                        text=data["choices"][0]["message"]["content"],
                        model="nemotron-120b",
                        tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
                        tokens_out=data.get("usage", {}).get("completion_tokens", 0),
                        latency_ms=int((time.time() - start) * 1000),
                    )
                return ModelResponse(text="", model="nemotron", error=str(data))
        except Exception as e:
            return ModelResponse(text="", model="nemotron", error=str(e))


class FallbackChain:
    """Chain models: try each until one succeeds."""

    def __init__(self):
        self.models: list[ModelConnector] = []
        self.default_model_name = "fallback-chain"

    def add(self, connector: ModelConnector) -> "FallbackChain":
        self.models.append(connector)
        return self

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        for model in self.models:
            resp = await model.call(prompt, system_prompt, max_tokens)
            if resp.ok:
                return resp
        return ModelResponse(text="", model=self.default_model_name, error="All models failed")


class ZenMuxConnector(ModelConnector):
    """ZenMux API — 136+ models, GLM-5.2-free, GPT-4o-mini."""

    BASE_URL = "https://zenmux.ai/api/v1/chat/completions"

    def __init__(self, api_key: str = None, model: str = "z-ai/glm-5.2-free"):
        self.api_key = api_key or os.getenv("ZENMUX_API_KEY", "")
        self.model = model

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        import time, httpx
        start = time.time()

        if not self.api_key:
            return ModelResponse(text="", model=self.model, error="No ZenMux API key")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                )
                data = resp.json()

                if "choices" in data:
                    msg = data["choices"][0]["message"]
                    text = msg.get("content") or msg.get("reasoning", "")
                    return ModelResponse(
                        text=text,
                        model=self.model,
                        tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
                        tokens_out=data.get("usage", {}).get("completion_tokens", 0),
                        latency_ms=int((time.time() - start) * 1000),
                    )
                return ModelResponse(text="", model=self.model, error=str(data))
        except Exception as e:
            return ModelResponse(text="", model=self.model, error=str(e))


class KimiAPIConnector(ModelConnector):
    """Kimi Direct API — K2.7 Code (best coding), K2.6 (multimodal).
    OpenAI-compatible — base_url: https://api.moonshot.cn/v1"""

    BASE_URL = "https://api.moonshot.cn/v1/chat/completions"

    MODELS = {
        "k2.7-code": "kimi-k2.7-code",
        "k2.7-code-highspeed": "kimi-k2.7-code-highspeed",
        "k2.6": "kimi-k2.6",
        "k2.5": "kimi-k2.5",
    }

    def __init__(self, api_key: str = None, model: str = "k2.7-code"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY", "")
        self.model = self.MODELS.get(model, model)

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        import time, httpx
        start = time.time()

        if not self.api_key:
            return ModelResponse(text="", model=f"kimi/{self.model}", error="No KIMI_API_KEY")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.3,
                    },
                )
                data = resp.json()

                if "choices" in data:
                    msg = data["choices"][0]["message"]
                    text = msg.get("content", "")
                    return ModelResponse(
                        text=text,
                        model=f"kimi/{self.model}",
                        tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
                        tokens_out=data.get("usage", {}).get("completion_tokens", 0),
                        latency_ms=int((time.time() - start) * 1000),
                    )
                return ModelResponse(text="", model=f"kimi/{self.model}", error=str(data))
        except httpx.HTTPStatusError as e:
            return ModelResponse(text="", model=f"kimi/{self.model}", error=f"HTTP {e.response.status_code}")
        except Exception as e:
            return ModelResponse(text="", model=f"kimi/{self.model}", error=str(e))


class HybridRouter:
    """Route to different models based on task type."""

    ROUTE_ACCOUNTING_KEYWORDS = [
        "زكاة", "ضريبة", "vat", "قيد", "ميزانية", "أرباح", "إهلاك",
        "تدفق", "ميزان", "محاسبة", "ifrs", "socpa", "محاسب",
        "balance sheet", "cash flow", "depreciation", "tax", "audit",
    ]

    ROUTE_FILE_KEYWORDS = [
        "إكسيل", "xlsx", "ملف", "excel", "pdf", "csv", "جدول",
        "مستند", "docx", "pptx", "بوربوينت", "رسم", "chart",
    ]

    ROUTE_CODE_KEYWORDS = [
        "كود", "code", "python", "برنامج", "script", "html", "css",
        "js", "javascript", "api", "json", "sql", "دالة", "function",
        "class", "import", "npm", "pip", "git", "docker", "build",
    ]

    def __init__(self):
        self.zenmux = ZenMuxConnector()
        self.kimi_direct = KimiAPIConnector()
        self.kimi_zenmux = ZenMuxConnector(model="moonshotai/kimi-k2.7-code")
        self.glm4 = GLM4Connector()
        self.gpt4o = GPT4oMiniConnector()
        self.nemotron = NemotronConnector()

        # Model selection rules
        self.text_chain = FallbackChain().add(self.zenmux).add(self.nemotron)
        # Code: try direct Kimi → ZenMux Kimi → ZenMux general → Nemotron
        self.code_chain = FallbackChain().add(self.kimi_direct).add(self.kimi_zenmux).add(self.zenmux)
        self.file_chain = FallbackChain().add(self.gpt4o).add(self.nemotron).add(self.zenmux)
        self.accounting_chain = FallbackChain().add(self.gpt4o).add(self.nemotron)

    def detect_route(self, message: str) -> str:
        """Detect routing: text / file / accounting / code."""
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in self.ROUTE_CODE_KEYWORDS):
            return "code"
        if any(kw in msg_lower for kw in self.ROUTE_FILE_KEYWORDS):
            return "file"
        if any(kw in msg_lower for kw in self.ROUTE_ACCOUNTING_KEYWORDS):
            return "accounting"
        return "text"

    async def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> ModelResponse:
        route = self.detect_route(prompt)
        if route == "code":
            return await self.code_chain.call(prompt, system_prompt, max_tokens)
        if route == "file":
            return await self.file_chain.call(prompt, system_prompt, max_tokens)
        elif route == "accounting":
            return await self.accounting_chain.call(prompt, system_prompt, max_tokens)
        return await self.text_chain.call(prompt, system_prompt, max_tokens)
