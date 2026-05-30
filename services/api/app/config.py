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

    # Local JWT signing/verification. HS256 with a shared secret covers local
    # development and the controlled pilot; OIDC (RS256 via OIDC_JWKS_URL) is the
    # production path documented in manual section 15.1 and slots into the same
    # verification layer.
    jwt_secret: str = "dev-insecure-change-me-please-set-a-real-secret"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30

    # Enables the developer login/token endpoints. MUST stay false in production
    # (guarded again at runtime by app_env).
    auth_dev_login: bool = True

    # CORS — restricted to known origins (manual section 15.4).
    allowed_origins: str = "http://localhost:3000"

    # Object storage
    s3_endpoint: str | None = None
    s3_bucket: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def dev_login_enabled(self) -> bool:
        """Developer auth shortcuts are only ever available outside production."""
        return self.auth_dev_login and not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()
