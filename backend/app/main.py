"""
XenoCRM Backend — FastAPI Application Entry Point.

Configures CORS, registers all API routers, seeds the database
on first startup, and exposes a health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

# Import all models so SQLAlchemy metadata is populated before init_db.
from app.models.customer import Customer  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.segment import Segment  # noqa: F401
from app.models.campaign import Campaign  # noqa: F401
from app.models.communication import Communication  # noqa: F401
from app.models.event import CampaignEvent  # noqa: F401

# Import routers.
from app.api.routes.customers import router as customers_router
from app.api.routes.segments import router as segments_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.receipts import router as receipts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.communications import router as communications_router
from app.api.routes.chat import router as chat_router
from app.api.routes.insights import router as insights_router


# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup:
        1. Create database tables if they don't exist.
        2. Seed 500 BrewBox customers on first run.
    On shutdown:
        Clean up resources (if any).
    """
    logger.info("🚀 Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Create tables.
    await init_db()
    logger.info("✅ Database tables ensured.")

    # Seed data on first run.
    from app.seed.seed_data import seed_database
    await seed_database()

    yield  # ← Application is running.

    logger.info("👋 Shutting down %s", settings.APP_NAME)


# ── FastAPI Application ──────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-native Mini CRM for BrewBox — segment shoppers, "
        "launch campaigns, and track delivery in real time."
    ),
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ────────────────────────────────────────────

app.include_router(customers_router)
app.include_router(segments_router)
app.include_router(campaigns_router)
app.include_router(receipts_router)
app.include_router(analytics_router)
app.include_router(communications_router)
app.include_router(chat_router)
app.include_router(insights_router)



# ── Health Check ─────────────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Basic health check endpoint for monitoring and deploy probes."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
