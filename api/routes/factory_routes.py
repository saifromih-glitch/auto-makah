# Auto Makah — Agent Factory API Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from factory.builder import factory
from factory.cloner import cloner

router = APIRouter()


class CreateFromTemplate(BaseModel):
    template: str


class CustomAgentConfig(BaseModel):
    name: str
    display_name: str = ""
    domain: str = "general"
    description: str = ""
    system_prompt: str = ""
    knowledge_domains: list = []


class CloneRequest(BaseModel):
    domain: str
    display_name: str
    system_prompt: str = ""


@router.get("/templates")
async def list_templates():
    """List available agent templates."""
    return JSONResponse(factory.list_templates())


@router.post("/create")
async def create_from_template(req: CreateFromTemplate):
    """Create agent from template: legal_expert, accounting_expert, etc."""
    agent = factory.build_from_template(req.template)
    if not agent:
        available = [t["name"] for t in factory.list_templates()]
        raise HTTPException(404, f"Template '{req.template}' not found. Available: {available}")
    return JSONResponse(agent.to_dict(), status_code=201)


@router.post("/create/custom")
async def create_custom(req: CustomAgentConfig):
    """Create custom agent from full config."""
    agent = factory.build_custom(req.dict())
    if not agent:
        raise HTTPException(400, "Agent name is required")
    return JSONResponse(agent.to_dict(), status_code=201)


@router.get("/status")
async def factory_status():
    """Get factory status."""
    return JSONResponse(factory.status())


@router.post("/clone")
async def clone_agent(req: CloneRequest):
    """Clone platform into domain-specific agent."""
    result = cloner.clone_to_domain(req.domain, req.display_name, req.system_prompt)
    return JSONResponse(result, status_code=201)


@router.get("/clones")
async def clone_status():
    """Get cloner status."""
    return JSONResponse(cloner.status())


@router.get("/learning")
async def learning_status():
    """Get learning loop stats."""
    from knowledge.learner import learner
    return JSONResponse(learner.stats())
