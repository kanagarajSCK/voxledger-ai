import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.session import init_db, get_db, engine
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import check_health
from app.schemas.health import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voxledger.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await engine.dispose()
    logger.info("Database engine connections closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multilingual AI Voice Accounting Platform for Kirana & Retail Businesses across India.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set debug flag on state for error formatting
app.state.debug = settings.DEBUG

# Register Structured Error Handlers
register_error_handlers(app)

# Configure CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Direct /api/health endpoint requirement
@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check (unversioned alias)",
)
async def api_health_alias(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    return await check_health(db)


# Root info endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Root Service Info",
)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "api_v1_url": settings.API_V1_STR,
        "health_check": "/api/health",
    }


# Include Versioned API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
