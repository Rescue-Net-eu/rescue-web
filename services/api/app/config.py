"""Application configuration loaded from the environment.

Mirrors the environment variables documented in the project manual
(section 18.6 "Deploy API").
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "rescue-net-api"

    # Connectivity (optional in the skeleton so the app boots without infra).
    database_url: str | None = None
    redis_url: str | None = None

    # Auth / OIDC
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    oidc_jwks_url: str | None = None

    # CORS — restricted to known origins (manual section 15.4).
    allowed_origins: str = "http://localhost:3000"

    # Object storage
    s3_endpoint: str | None = None
    s3_bucket: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
