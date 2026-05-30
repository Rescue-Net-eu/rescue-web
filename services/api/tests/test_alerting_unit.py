"""Unit tests for alerting policy helpers (no database required)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.alerting import (
    ALERT_TTL_MINUTES,
    effective_status,
    expiry_for_priority,
    is_expired,
)
from app.models import Alert


def test_expiry_matches_priority_policy() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert expiry_for_priority("high", now=now) == now + timedelta(minutes=5)
    assert expiry_for_priority("medium", now=now) == now + timedelta(minutes=15)
    assert expiry_for_priority("low", now=now) == now + timedelta(minutes=30)
    # Unknown priority falls back to the medium default.
    assert expiry_for_priority("weird", now=now) == now + timedelta(
        minutes=ALERT_TTL_MINUTES["medium"]
    )


def test_effective_status_times_out_unanswered_expired() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    alert = Alert(status="sent", expiry_at=now - timedelta(minutes=1), responded_at=None)
    assert effective_status(alert, now=now) == "timeout"
    assert is_expired(alert, now=now) is True


def test_effective_status_keeps_answered_alert() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    alert = Alert(
        status="responded",
        expiry_at=now - timedelta(minutes=1),
        responded_at=now - timedelta(minutes=2),
    )
    assert effective_status(alert, now=now) == "responded"
