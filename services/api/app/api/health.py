"""Liveness and readiness probes (manual section 14.1)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from ..config import get_settings
from ..db import get_engine

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe — always cheap, no external dependencies."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> dict[str, object]:
    """Readiness probe — reports configured dependency health."""
    settings = get_settings()
    checks: dict[str, str] = {}

    if settings.database_url:
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:  # noqa: BLE001 - readiness must never raise
            checks["database"] = "unavailable"
    else:
        checks["database"] = "not_configured"

    checks["redis"] = "ok" if settings.redis_url else "not_configured"

    ready = "unavailable" not in checks.values()
    return {"status": "ready" if ready else "degraded", "checks": checks}
