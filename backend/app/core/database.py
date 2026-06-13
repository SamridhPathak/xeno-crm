"""
Async SQLAlchemy engine and session setup for PostgreSQL.

Exports:
    - engine: the async engine bound to DATABASE_URL
    - async_session_maker: a factory for AsyncSession instances
    - Base: declarative base for all ORM models
    - get_db: FastAPI dependency that yields an async session
    - init_db: creates all tables (used at startup / seed time)
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ── Async Engine ─────────────────────────────────────────────────
# pool_pre_ping keeps connections healthy across Render cold starts.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


# ── Session Factory ──────────────────────────────────────────────
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models in XenoCRM."""
    pass


# ── FastAPI Dependency ───────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    Yield an async database session for a single request lifecycle.

    The session is committed on success and rolled back + closed on error,
    ensuring no leaked connections.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Table Initialization ────────────────────────────────────────
async def init_db() -> None:
    """
    Create all tables that don't yet exist in the database.

    Called once at application startup (and during seeding).
    Uses the engine directly with `run_sync` because `create_all`
    is a synchronous DDL operation.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
