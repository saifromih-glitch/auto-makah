# ═══════════════════════════════════════════
# 🕋 Auto Makah — Developer Platform (Phase 4)
# OpenAI-Compatible API + Keys + Usage
# ═══════════════════════════════════════════

import os
import json
import uuid
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(tags=["developer-platform"])

# ═══════════════════════════════════════════
# API Key Store (file-based, upgrade to DB)
# ═══════════════════════════════════════════
KEYS_FILE = Path(__file__).parent.parent / "data" / "api_keys.json"
USAGE_FILE = Path(__file__).parent.parent / "data" / "api_usage.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


class APIKeyManager:
    """Manage developer API keys."""

    @staticmethod
    def generate(owner: str, plan: str = "free") -> dict:
        keys = _load_json(KEYS_FILE)
        kid = f"amk-{uuid.uuid4().hex[:24]}"
        api_key = f"amk-{uuid.uuid4().hex}"
        keys[kid] = {
            "key": api_key,
            "owner": owner,
            "plan": plan,
            "created": datetime.utcnow().isoformat(),
            "active": True,
            "usage": {"requests": 0, "tokens": 0},
        }
        _save_json(KEYS_FILE, keys)
        return {"id": kid, "key": api_key, "plan": plan}

    @staticmethod
    def validate(api_key: str) -> Optional[dict]:
        keys = _load_json(KEYS_FILE)
        for k, v in keys.items():
            if v.get("key") == api_key:
                if not v.get("active", True):
                    return None
                # Plan limits
                limits = {"free": 100, "pro": 1000, "business": 10000}
                usage = v.get("usage", {}).get("requests", 0)
                if usage >= limits.get(v.get("plan", "free"), 100):
                    return None  # Rate limited
                return {"id": k, **v}
        return None

    @staticmethod
    def record_usage(api_key: str, tokens: int = 0):
        keys = _load_json(KEYS_FILE)
        for k, v in keys.items():
            if v.get("key") == api_key:
                v.setdefault("usage", {"requests": 0, "tokens": 0})
                v["usage"]["requests"] += 1
                v["usage"]["tokens"] += tokens
                break
        _save_json(KEYS_FILE, keys)

    @staticmethod
    def list_keys() -> list:
        keys = _load_json(KEYS_FILE)
        return [
            {"id": k, "owner": v.get("owner"), "plan": v.get("plan"),
             "active": v.get("active", True), "requests": v.get("usage", {}).get("requests", 0),
             "created": v.get("created")}
            for k, v in keys.items()
        ]

    @staticmethod
    def revoke(kid: str) -> bool:
        keys = _load_json(KEYS_FILE)
        if kid not in keys:
            return False
        keys[kid]["active"] = False
        _save_json(KEYS_FILE, keys)
        return True


# ═══════════════════════════════════════════
# Models Pydantic (OpenAI-compatible)
# ═══════════════════════════════════════════

class Message(BaseModel):
    role: str = "user"
    content: str = ""


class ChatCompletionRequest(BaseModel):
    model: str = "auto-makah"
    messages: list[Message]
    max_tokens: int = 2000
    temperature: float = 0.7
    stream: bool = False
    user: str | None = None


# ═══════════════════════════════════════════
# OpenAI-Compatible Endpoints
# ═══════════════════════════════════════════

AVAILABLE_MODELS = {
    "auto-makah": {"name": "Auto Makah Default", "pricing": "$0.00/1M tokens"},
    "auto-makah-pro": {"name": "Auto Makah Pro (Swarm)", "pricing": "$0.15/1M tokens"},
    "kimi-k2.7-code": {"name": "Kimi K2.7 Code", "pricing": "Requires KIMI_API_KEY"},
    "glm-5.2": {"name": "GLM-5.2 (Free)", "pricing": "Free"},
}


@router.get("/v1/models")
async def list_models():
    """OpenAI-compatible models list."""
    return JSONResponse({
        "object": "list",
        "data": [
            {"id": mid, "object": "model", "owned_by": "auto-makah", **info}
            for mid, info in AVAILABLE_MODELS.items()
        ]
    })


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """OpenAI-compatible chat completions endpoint."""
    # Authenticate
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": {"message": "Missing API key", "type": "auth_error"}}, 401)

    api_key = auth[7:]
    key_info = APIKeyManager.validate(api_key)
    if not key_info:
        return JSONResponse({"error": {"message": "Invalid or rate-limited API key", "type": "auth_error"}}, 403)

    # Build prompt
    system = ""
    user_msg = ""
    for m in req.messages:
        if m.role == "system":
            system = m.content
        elif m.role == "user":
            user_msg = m.content

    if not user_msg:
        return JSONResponse({"error": {"message": "No user message", "type": "invalid_request"}}, 400)

    # Route to model
    from core.connectors import HybridRouter
    router_model = HybridRouter()

    resp = await router_model.call(user_msg, system_prompt=system, max_tokens=req.max_tokens)

    # Record usage
    APIKeyManager.record_usage(api_key, resp.tokens_in + resp.tokens_out)

    # OpenAI-compatible response format
    created = int(time.time())
    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": created,
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": resp.text if resp.ok else "Error: " + (resp.error or "unknown"),
            },
            "finish_reason": "stop" if resp.ok else "error",
        }],
        "usage": {
            "prompt_tokens": resp.tokens_in,
            "completion_tokens": resp.tokens_out,
            "total_tokens": resp.tokens_in + resp.tokens_out,
        },
    })


# ═══════════════════════════════════════════
# API Key Management
# ═══════════════════════════════════════════

class KeyCreateRequest(BaseModel):
    owner: str
    plan: str = "free"


@router.post("/api/keys/create")
async def create_api_key(req: KeyCreateRequest):
    """Generate a new API key."""
    if req.plan not in ["free", "pro", "business"]:
        raise HTTPException(400, "Invalid plan. Use: free, pro, business")
    result = APIKeyManager.generate(req.owner, req.plan)
    return JSONResponse(result)


@router.get("/api/keys/list")
async def list_api_keys():
    """List all API keys."""
    return JSONResponse({"keys": APIKeyManager.list_keys()})


@router.post("/api/keys/revoke")
async def revoke_api_key(kid: str):
    """Revoke an API key."""
    success = APIKeyManager.revoke(kid)
    return JSONResponse({"revoked": success})


@router.get("/api/keys/usage")
async def get_usage():
    """Get usage stats."""
    return JSONResponse({"keys": APIKeyManager.list_keys()})


# ═══════════════════════════════════════════
# API Playground (HTML)
# ═══════════════════════════════════════════

@router.get("/playground")
async def api_playground():
    """Interactive API playground — like platform.kimi.ai/playground."""
    return JSONResponse({
        "message": "API Playground",
        "curl_example": """curl -X POST https://auto-makah.fly.dev/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"auto-makah","messages":[{"role":"user","content":"مرحبا"}]}'""",
        "python_example": """import openai
client = openai.OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://auto-makah.fly.dev/v1"
)
response = client.chat.completions.create(
    model="auto-makah",
    messages=[{"role":"user","content":"مرحبا"}]
)
print(response.choices[0].message.content)""",
    })


@router.get("/api/developer")
async def developer_docs():
    """Developer documentation summary."""
    return JSONResponse({
        "platform": "Auto Makah Developer Platform",
        "version": "0.1.0",
        "openai_compatible": True,
        "endpoints": {
            "models": "GET /v1/models",
            "chat": "POST /v1/chat/completions",
            "keys_create": "POST /api/keys/create",
            "keys_list": "GET /api/keys/list",
            "keys_revoke": "POST /api/keys/revoke",
            "playground": "GET /playground",
        },
        "models": list(AVAILABLE_MODELS.keys()),
        "pricing": {
            "free": "100 requests/day",
            "pro": "1,000 requests/day",
            "business": "10,000 requests/day",
        },
    })
