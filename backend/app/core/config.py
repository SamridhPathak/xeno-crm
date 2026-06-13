"""
Application configuration loaded from environment variables.

Uses pydantic-settings to validate and type-cast all env vars at startup.
A single `settings` instance is exported for use across the application.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central configuration for the XenoCRM backend.

    All values are read from environment variables (or a .env file).
    Defaults are provided for local development where sensible.
    """

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "XenoCRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database (async PostgreSQL via asyncpg) ──────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/xenocrm"

    # ── CORS ─────────────────────────────────────────────────────
    # Comma-separated origins, parsed into a list below.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Google Gemini AI ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Channel Service ──────────────────────────────────────────
    CHANNEL_SERVICE_URL: str = "http://localhost:8001"

    # ── CRM callback URL (used by channel service to post receipts) ─
    CRM_CALLBACK_URL: str = "http://localhost:8000"

    # ── Redis (used by channel service; included here for reference) ─
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Helpers ──────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list, splitting the comma-separated env var."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache ensures environment variables are read only once,
    and the same object is reused across the application lifetime.
    """
    return Settings()


# Convenience singleton — import this directly in most modules.
settings = get_settings()
