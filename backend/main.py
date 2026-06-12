import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.database.session import engine, Base
from app.utils.logger import setup_logging

# Import models so Base.metadata knows about them
import app.models  # noqa: F401

from app.api.warehouses import router as warehouse_router
from app.api.cameras import router as camera_router
from app.api.occupancy import router as occupancy_router
from app.scheduler.scheduler_service import start_scheduler, shutdown_scheduler

# ── Centralized Logging ───────────────────────────────────────────────────────
# Must be called before any logger.getLogger() usage in other modules.
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler — startup and shutdown hooks."""
    logger.info("=" * 60)
    logger.info(f"  Starting {settings.APP_NAME}")
    logger.info(f"  Environment : {settings.APP_ENV}")
    logger.info(f"  Database    : {settings.DATABASE_URL}")
    logger.info("=" * 60)

    logger.info("Startup: Initialising background scheduler...")
    start_scheduler()
    yield

    logger.info("Shutdown: Stopping background scheduler...")
    shutdown_scheduler()
    logger.info("Shutdown complete.")


# ── FastAPI Application ────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Multi-Warehouse Occupancy Estimation Platform",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS — allow all origins for local Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(warehouse_router, prefix="/api")
app.include_router(camera_router,    prefix="/api")
app.include_router(occupancy_router, prefix="/api")


@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Health check endpoint — confirms API and scheduler are running."""
    return {
        "status":      "healthy",
        "app_name":    settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug_mode":  settings.DEBUG,
        "version":     "1.0.0",
    }
