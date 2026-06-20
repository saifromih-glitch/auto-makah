# Auto Makah — Channels Routes
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from channels.telegram import router as telegram_router

router = APIRouter()

# Mount Telegram webhook routes
router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])


class ChannelConfig(BaseModel):
    type: str  # telegram, whatsapp
    config: dict


@router.post("/connect")
async def connect_channel(req: ChannelConfig):
    """Register a communication channel."""
    return JSONResponse({"status": "connected", "type": req.type})


@router.get("")
async def list_channels():
    return JSONResponse({"channels": []})
