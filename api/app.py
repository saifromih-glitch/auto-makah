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

# 🔁 Lopp Step 5: Self-waking health loop (starts on app startup)
@app.on_event("startup")
async def start_health_loop():
    try:
        from core.health_loop import HealthLoop
        hl = HealthLoop()
        hl.start()
        import logging
        logging.getLogger("auto_makah").info("🫀 Health Loop started")
    except Exception as e:
        import logging
        logging.getLogger("auto_makah").warning(f"Health Loop failed to start: {e}")

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
    reg_tools = registry.list_all() if not category else registry.list_by_category(category)
    # Convert registry dict to list
    if isinstance(reg_tools, dict):
        tool_list = [{"name": k, **v} for k, v in reg_tools.items()]
    else:
        tool_list = reg_tools
    # Add Kimi tools
    kimi_list = [{"name": t["name"], "display": t["display"], "desc": t["description"], "category": "kimi"} for t in KIMI_TOOLS.values()]
    return JSONResponse({"tools": tool_list + kimi_list, "count": len(tool_list) + len(kimi_list)})


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

# ═══ 🔁 Loop Engineering — Auto Makah ═══
@app.get("/api/loops")
async def loops_health():
    """Loop Engineering health dashboard — all project loops."""
    try:
        from core.loop_engineering import apply_to_auto_makah
        orch = apply_to_auto_makah()
        return JSONResponse(orch.get_project_health())
    except Exception as e:
        return JSONResponse({"error": str(e), "status": "loop_engine_not_ready"}, status_code=500)

@app.get("/api/loops/{loop_id}")
async def loop_state(loop_id: str):
    """Get state for a specific loop."""
    from core.loop_engineering import load_state, apply_to_auto_makah
    orch = apply_to_auto_makah()
    state = load_state(loop_id, orch.project)
    return JSONResponse(state.to_dict())

@app.post("/api/loops/{loop_id}/run")
async def trigger_loop(loop_id: str):
    """Manually trigger a loop."""
    from core.loop_engineering import apply_to_auto_makah
    orch = apply_to_auto_makah()
    result = orch.run_loop(loop_id, lambda: {"status": "manual_trigger"})
    return JSONResponse(result)

# ═══ 📚 Skill Files — Lopp Step 7 ═══
@app.get("/api/agent-skills")
async def list_skill_files():
    """List all reusable Lopp skill files (.skill format)."""
    try:
        from core.skill_loader import list_skills
        return JSONResponse({"skills": list_skills()})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/agent-skills/{name}")
async def get_skill(name: str):
    """Load a specific Lopp skill file."""
    from core.skill_loader import load_skill
    content = load_skill(name)
    if not content:
        return JSONResponse({"error": "skill not found"}, status_code=404)
    return JSONResponse({"name": name, "content": content})

# ═══ 🏗️ BRV Pipeline Status ═══
@app.get("/api/brv/status")
async def brv_status():
    """Builder/Reviewer/Verifier pipeline health."""
    from core.loop_engineering import load_state
    state = load_state("brv_chat", "auto_makah")
    return JSONResponse({
        "pipeline": "Builder → Reviewer → Verifier",
        "total_runs": state.total_runs,
        "success_rate": round((state.successful_runs / max(state.total_runs, 1)) * 100, 1),
        "last_error": state.last_error,
    })

# ═══ 🌳 Worktree Isolation — Lopp Step 6 ═══
@app.get("/api/worktrees")
async def worktree_status():
    """List all agent workspaces."""
    from core.worktree import get_worktree_manager
    mgr = get_worktree_manager()
    return JSONResponse({"workspaces": mgr.get_all_snapshots(), "count": len(mgr.workspaces)})

@app.get("/api/worktrees/{agent_id}")
async def agent_workspace(agent_id: str):
    """Get workspace files for a specific agent."""
    from core.worktree import get_worktree_manager
    mgr = get_worktree_manager()
    ws = mgr.get_workspace(agent_id)
    return JSONResponse({"agent_id": agent_id, "files": ws.list_files()})

@app.get("/api/worktrees/{agent_a}/diff/{agent_b}")
async def worktree_diff(agent_a: str, agent_b: str):
    """Compare files between two agent workspaces."""
    from core.worktree import get_worktree_manager
    mgr = get_worktree_manager()
    return JSONResponse(mgr.check_conflicts(agent_a, agent_b))

# ═══ 🛡️ Controlled Autonomy — Lopp Step 14 ═══
@app.get("/api/autonomy")
async def autonomy_status():
    """Get autonomy gate status — pending approvals."""
    from core.autonomy_gate import get_autonomy_gate
    gate = get_autonomy_gate()
    return JSONResponse(gate.get_stats())

@app.post("/api/autonomy/request")
async def request_approval(action: str = None, requested_by: str = "system"):
    """Request human approval for a critical action."""
    from core.autonomy_gate import get_autonomy_gate
    if not action:
        return JSONResponse({"error": "action parameter required"}, status_code=400)
    gate = get_autonomy_gate()
    check = gate.needs_approval(action)
    if not check["needs_approval"]:
        return JSONResponse({"auto_approved": True, **check})
    approval_id = gate.request_approval(action, requested_by)
    return JSONResponse({"needs_approval": True, "approval_id": approval_id, **check})

@app.post("/api/autonomy/{approval_id}/approve")
async def approve_action(approval_id: str, approved_by: str = "admin"):
    """Approve a pending action."""
    from core.autonomy_gate import get_autonomy_gate
    gate = get_autonomy_gate()
    ok = gate.approve(approval_id, approved_by)
    return JSONResponse({"approved": ok, "approval_id": approval_id})

@app.post("/api/autonomy/{approval_id}/deny")
async def deny_action(approval_id: str, denied_by: str = "admin", reason: str = ""):
    """Deny a pending action."""
    from core.autonomy_gate import get_autonomy_gate
    gate = get_autonomy_gate()
    ok = gate.deny(approval_id, denied_by, reason)
    return JSONResponse({"denied": ok, "approval_id": approval_id})

# ═══ 💳 Comprehension Debt — Lopp Step 13 ═══
@app.get("/api/debt")
async def debt_status():
    """Get comprehension debt tracker status."""
    from core.loop_engineering import get_comprehension_debt
    debt = get_comprehension_debt("auto_makah")
    unpaid = [d for d in debt if not hasattr(d, 'understood') or not d.understood]
    return JSONResponse({
        "total_debt": len(debt),
        "unpaid": len(unpaid),
        "entries": [{
            "timestamp": d.timestamp,
            "file": d.file_path,
            "description": d.change_description,
            "understood": d.understood,
            "risk": d.risk_level,
            "deadline": d.review_deadline,
        } for d in debt[-10:]]  # Last 10 entries
    })
