# Auto Makah — Skills Marketplace Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.skills import marketplace, Skill

router = APIRouter()


class InstallRequest(BaseModel):
    agent_name: str
    skill_name: str


@router.get("")
async def list_skills(domain: str = None, search: str = None):
    if search:
        return JSONResponse(marketplace.search(search))
    if domain:
        return JSONResponse(marketplace.list_by_domain(domain))
    return JSONResponse(marketplace.list_all())


@router.post("/install")
async def install_skill(req: InstallRequest):
    ok = marketplace.install(req.agent_name, req.skill_name)
    if not ok:
        raise HTTPException(404, f"Skill '{req.skill_name}' or agent '{req.agent_name}' not found")
    return JSONResponse({"status": "installed", "agent": req.agent_name, "skill": req.skill_name})


@router.get("/installed/{agent_name}")
async def installed_skills(agent_name: str):
    return JSONResponse({"agent": agent_name, "skills": marketplace.get_installed(agent_name)})
