# ═══════════════════════════════════════════
# 🕋 Auto Makah — FastAPI Application
# ═══════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
import os

app = FastAPI(
    title="Auto Makah",
    description="🕋 AI Agent Platform — Twin of OpenClaw — Saudi Arabia",
    version="0.4.0",
)

# CORS — allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https:"
        return response
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
from api.middleware import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)


@app.get("/kimi", response_class=HTMLResponse)
async def kimi_ui():
    """Serve the Kimi-style hybrid interface."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "kimi-ui.html")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Kimi UI not found</h1>", status_code=404)


@app.get("/robots.txt")
async def robots():
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "dashboard", "robots.txt")
    if os.path.isfile(path):
        return FileResponse(path)
    return Response("User-agent: *\nAllow: /\n", media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap():
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "dashboard", "sitemap.xml")
    if os.path.isfile(path):
        return FileResponse(path)
    return Response("", status_code=404)


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Landing page — Auto Makah AI Platform."""
    import os
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "dashboard", "landing.html")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    # Fallback: redirect to Kimi UI
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/kimi")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    from core.tools import registry
    from core.agent import runtime
    from core.kimi_tools import KIMI_TOOLS
    # Count all tools: registry + Kimi tools + parity tools
    total_tools = registry.count() + len(KIMI_TOOLS)
    total_agents = len(runtime.agents) if runtime.agents else 8  # 8 built-in agents
    return JSONResponse({
        "status": "operational",
        "platform": "Auto Makah",
        "version": "0.4.0",
        "agents": total_agents,
        "tools": total_tools,
        "categories": registry.categories(),
    })


@app.get("/api/tools")
async def list_tools(category: str = None):
    """List all registered tools including Kimi tools."""
    from core.tools import registry
    from core.kimi_tools import KIMI_TOOLS
    tools = registry.list_all() if not category else registry.list_by_category(category)
    # Add Kimi tools
    kimi = [{"name": t["name"], "display": t["display"], "desc": t["description"], "category": "kimi"} for t in KIMI_TOOLS.values()]
    return JSONResponse({"tools": tools + kimi, "count": len(tools) + len(kimi)})


@app.get("/api/agents")
async def list_agents():
    """List all registered agents + template agents."""
    from core.agent import runtime
    agents = runtime.list_agents()
    if not agents:
        agents = [
            {"id": "azmi", "name": "استراتيجي", "icon": "🧭", "role": "Porter · 5 Forces", "status": "ready"},
            {"id": "analyst", "name": "محلل مالي", "icon": "💰", "role": "Damodaran · DCF/WACC", "status": "ready"},
            {"id": "ops", "name": "مهندس تشغيلي", "icon": "⚙️", "role": "Goldratt · TOC", "status": "ready"},
            {"id": "legal", "name": "مستشار قانوني", "icon": "⚖️", "role": "Susskind · LegalTech", "status": "ready"},
            {"id": "growth", "name": "خبير نمو", "icon": "📈", "role": "Ellis · AARRR", "status": "ready"},
            {"id": "data", "name": "عالم بيانات", "icon": "📊", "role": "Patil · Data Jujitsu", "status": "ready"},
            {"id": "tech", "name": "مهندس برمجيات", "icon": "💻", "role": "Fowler · CI/CD", "status": "ready"},
            {"id": "hr", "name": "مستشار HR", "icon": "👥", "role": "Bock · People Analytics", "status": "ready"},
        ]
    return JSONResponse({"agents": agents, "count": len(agents)})


# Import route modules
from api.routes import agents, tools, channels, tenants, factory_routes, executor_routes, skills_routes, chat
from api import kimi_tools, developer, desktop_routes, parity_routes

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(factory_routes.router, prefix="/api/factory", tags=["factory"])
app.include_router(executor_routes.router, prefix="/api/execute", tags=["execute"])
app.include_router(skills_routes.router, prefix="/api/skills", tags=["skills"])
app.include_router(kimi_tools.router, tags=["kimi-tools"])
app.include_router(chat.router, tags=["chat"])
app.include_router(developer.router, tags=["developer-platform"])
app.include_router(desktop_routes.router, tags=["desktop-agent"])
app.include_router(parity_routes.router, tags=["parity-tools"])

# ═══ 404 Catch-All — must be LAST ═══
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all for 404 — serves 404 page or returns 404."""
    base = os.path.dirname(os.path.dirname(__file__))
    error_path = os.path.join(base, "dashboard", "404.html")
    if os.path.isfile(error_path):
        with open(error_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read(), status_code=404)
    return HTMLResponse("<h1>٤٠٤ — الصفحة غير موجودة 🕋</h1>", status_code=404)
