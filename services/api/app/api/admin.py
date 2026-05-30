"""Administrative endpoints (manual sections 6.1, 6.6, 14.1).

Audit-log access is restricted to admins and auditors (manual section 15.2
lists audit-log access as a high-risk endpoint).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import retention
from ..audit import record_audit
from ..db import get_session
from ..deps import require_roles
from ..enums import UserRole
from ..models import AuditLog, User
from ..privacy import UserNotFound, erase_user

router = APIRouter(prefix="/admin", tags=["admin"])

require_audit_reader = require_roles(
    UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN, UserRole.AUDITOR
)
require_platform_admin = require_roles(UserRole.PLATFORM_ADMIN)


class AuditLogOut(BaseModel):
    id: int
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str | None
    entity_id: str | None
    timestamp: datetime


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    _reader=Depends(require_audit_reader),
    session: AsyncSession = Depends(get_session),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    return list((await session.execute(stmt)).scalars().all())


@router.post("/retention/run")
async def run_retention(
    request: Request,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Run the GDPR retention sweeps on demand (platform admin; manual §16.2).

    Also available as a cron job via ``python -m app run``.
    """
    counts = await retention.run_all(session)
    # run_all commits the sweeps; record the trigger in its own transaction.
    await record_audit(
        session,
        action="retention.run",
        actor_user_id=admin.id,
        request=request,
        metadata=counts,
    )
    await session.commit()
    return counts


@router.post("/users/{user_id}/erase", status_code=status.HTTP_200_OK)
async def erase_user_account(
    user_id: uuid.UUID,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Erase a user's personal data (manual §16.4 "Delete my account")."""
    try:
        return await erase_user(session, user_id, actor_user_id=admin.id)
    except UserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from exc
