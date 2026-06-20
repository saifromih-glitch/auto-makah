# 🕋 Auto Makah — Auth & Rate Limiting Middleware

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import hashlib
import os
from typing import Dict


# ═══════════════════════════════
# Simple API Key Auth
# ═══════════════════════════════

ADMIN_KEY = os.getenv("ADMIN_API_KEY", hashlib.sha256(b"auto-makah-admin").hexdigest())


def verify_admin(request: Request):
    """Verify admin API key from header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        if token == ADMIN_KEY:
            return True
    return False


# ═══════════════════════════════
# Rate Limiter
# ═══════════════════════════════

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._clients: Dict[str, list] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        self._clients.setdefault(client_id, [])
        # Clean old entries
        self._clients[client_id] = [t for t in self._clients[client_id] if now - t < self.window]
        # Check
        if len(self._clients[client_id]) >= self.max_requests:
            return False
        self._clients[client_id].append(now)
        return True

    def remaining(self, client_id: str) -> int:
        now = time.time()
        self._clients.setdefault(client_id, [])
        self._clients[client_id] = [t for t in self._clients[client_id] if now - t < self.window]
        return max(0, self.max_requests - len(self._clients[client_id]))


rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for FastAPI."""
    # Skip health check
    if request.url.path == "/api/health":
        return await call_next(request)

    client_id = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    if not rate_limiter.is_allowed(client_id):
        return JSONResponse(
            {"error": "rate_limit_exceeded", "retry_after": 60},
            status_code=429,
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.remaining(client_id))
    return response
