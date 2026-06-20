# ═══════════════════════════════════════════
# 🕋 Auto Makah — FastAPI Application
# ═══════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Auto Makah",
    description="🕋 AI Agent Platform — Twin of OpenClaw — Saudi Arabia",
    version="0.1.0",
)

# CORS — allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    from core.tools import registry
    from core.agent import runtime
    return JSONResponse({
        "status": "operational",
        "platform": "Auto Makah",
        "version": "0.1.0",
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
from api.routes import agents, tools, channels, tenants, factory_routes

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(factory_routes.router, prefix="/api/factory", tags=["factory"])
