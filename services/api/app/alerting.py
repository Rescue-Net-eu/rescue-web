"""Alerting policy helpers (manual section 9).

Holds the expiry policy (section 9.4), the per-dispatcher anti-abuse rate
limit (section 9.5) and the effective-status derivation that turns an
unanswered, expired alert into a timeout (section 9.4 / 21.1).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Alert, AuditLog

# Expiry per incident priority (manual section 9.4).
ALERT_TTL_MINUTES: dict[str, int] = {"low": 30, "medium": 15, "high": 5}
DEFAULT_TTL_MINUTES = 15

# Anti-abuse: a dispatcher may launch at most this many alert campaigns per
# window (manual section 9.5 "Rate limits per dispatcher").
RATE_LIMIT_CAMPAIGNS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

ALERT_SEND_ACTION = "alert.send"


def expiry_for_priority(priority: str, *, now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    minutes = ALERT_TTL_MINUTES.get(priority, DEFAULT_TTL_MINUTES)
    return now + timedelta(minutes=minutes)


def effective_status(alert: Alert, *, now: datetime | None = None) -> str:
    """An unanswered alert past its expiry reads as ``timeout``."""
    now = now or datetime.now(UTC)
    if alert.responded_at is None and alert.expiry_at is not None and now >= alert.expiry_at:
        return "timeout"
    return alert.status


def is_expired(alert: Alert, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    return alert.expiry_at is not None and now >= alert.expiry_at


async def recent_campaign_count(session: AsyncSession, actor_user_id, *, now=None) -> int:
    """Count this dispatcher's alert campaigns within the rate-limit window."""
    now = now or datetime.now(UTC)
    since = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    stmt = select(func.count()).select_from(AuditLog).where(
        AuditLog.actor_user_id == actor_user_id,
        AuditLog.action == ALERT_SEND_ACTION,
        AuditLog.timestamp >= since,
    )
    return int((await session.execute(stmt)).scalar_one())
