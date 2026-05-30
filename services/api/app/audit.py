"""Audit logging (manual section 15.3).

A single helper records security- and operationally-relevant actions. It
is deliberately append-only and never raises into the request path: an
audit write must not break the operation it is recording, but failures are
surfaced to logs for follow-up.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog

logger = logging.getLogger("rescue_net.audit")


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    actor_user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | uuid.UUID | None = None,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append an audit record within the caller's transaction.

    The row is flushed (not committed) so it shares the fate of the action
    being audited — if the surrounding transaction rolls back, so does the
    audit entry, keeping the log consistent with what actually happened.
    """
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        audit_metadata=metadata,
    )
    session.add(entry)
    try:
        await session.flush()
    except Exception:  # noqa: BLE001 - auditing must not mask the primary action
        logger.exception("failed to write audit log for action=%s", action)
