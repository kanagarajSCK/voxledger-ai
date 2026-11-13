import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System and Database Health Check",
    description="Returns detailed health metrics including database connectivity, latency, and service metadata.",
)
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_connected = False
    latency_ms = None

    try:
        start_time = time.perf_counter()
        result = await db.execute(text("SELECT 1"))
        _ = result.scalar()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        db_connected = True
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(timezone.utc),
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        database_latency_ms=latency_ms,
        api_version=settings.API_V1_STR,
        websocket_endpoint=f"{settings.API_V1_STR}/ws/voice",
    )
