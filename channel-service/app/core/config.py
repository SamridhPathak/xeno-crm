"""
Channel Service configuration loaded from environment variables.

Uses pydantic-settings for validation. The channel service runs
as a separate deployment from the CRM backend and needs its own
config for Redis (Celery broker) and the CRM callback URL.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration for the Channel Service.

    Environment variables:
        APP_NAME:          Service identifier in logs and health checks.
        DEBUG:             Enable verbose logging when True.
        REDIS_URL:         Redis connection string used as Celery broker + backend.
        CRM_CALLBACK_URL:  Base URL of the CRM backend for posting delivery receipts.
                           Receipts are POSTed to {CRM_CALLBACK_URL}/api/receipts.
        CORS_ORIGINS:      Comma-separated allowed origins (mainly for the /docs UI).
    """

    APP_NAME: str = "BrewBox Channel Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


    # ── CRM Backend ─────────────────────────────────────────────
    CRM_CALLBACK_URL: str = "http://localhost:8000"

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def receipts_endpoint(self) -> str:
        """Full URL for posting delivery receipts to the CRM."""
        return f"{self.CRM_CALLBACK_URL}/api/receipts"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
