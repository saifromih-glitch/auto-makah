# Auto Makah — Tenants Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()


class CreateTenantRequest(BaseModel):
    name: str
    email: str
    plan: str = "free"


@router.post("")
async def create_tenant(req: CreateTenantRequest):
    return JSONResponse({"tenant": req.name, "status": "created"}, status_code=201)


@router.get("")
async def list_tenants():
    return JSONResponse({"tenants": []})
