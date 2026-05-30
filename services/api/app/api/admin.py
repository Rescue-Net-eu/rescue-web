"""Administrative endpoints (manual sections 6.1, 6.6, 14.1).

Audit-log access is restricted to admins and auditors (manual section 15.2
lists audit-log access as a high-risk endpoint).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import require_roles
from ..enums import UserRole
from ..models import AuditLog

router = APIRouter(prefix="/admin", tags=["admin"])

require_audit_reader = require_roles(
    UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN, UserRole.AUDITOR
)


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
