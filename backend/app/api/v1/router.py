from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.websocket.voice_ws import router as voice_ws_router

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(voice_ws_router, tags=["Realtime Voice Streaming"])
