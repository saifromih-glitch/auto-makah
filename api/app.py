# ═══════════════════════════════════════════
# 🕋 Auto Makah — FastAPI Application
# ═══════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
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
    return HTMLResponse("<h1>Kimi UI not found</h1>")


@app.get("/", response_class=HTMLResponse)
async def dashboard_root():
    """Serve the main dashboard."""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "index.html")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Auto Makah 🕋</h1>")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    from core.tools import registry
    from core.agent import runtime
    return JSONResponse({
        "status": "operational",
        "platform": "Auto Makah",
        "version": "0.4.0",
        "agents": len(runtime.agents),
        "tools": registry.count(),
        "categories": registry.categories(),
    })


@app.get("/api/tools")
async def list_tools(category: str = None):
    """List all registered tools."""
    from core.tools import registry
    if category:
        return JSONResponse(registry.list_by_category(category))
    return JSONResponse(registry.list_all())


@app.get("/api/agents")
async def list_agents():
    """List all registered agents."""
    from core.agent import runtime
    return JSONResponse(runtime.list_agents())


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
