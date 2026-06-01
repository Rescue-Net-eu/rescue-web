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
from ..deps import require_admin, require_roles
from ..enums import UserRole
from ..models import AuditLog, Organization, User
from ..privacy import UserNotFound, erase_user
from ..schemas import OrganizationCreate, OrganizationOut, UserAdminUpdate, UserOut

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


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    role: UserRole | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if role is not None:
        stmt = stmt.where(User.role == role.value)
    return list((await session.execute(stmt)).scalars().all())


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Change a user's role or suspend/reactivate them (manual sections 6.1, 6.2)."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update"
        )
    if "role" in fields and fields["role"] is not None:
        user.role = UserRole(fields["role"])
    if "status" in fields and fields["status"] is not None:
        user.status = fields["status"]

    await record_audit(
        session,
        action="user.update",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
        metadata={"fields": sorted(fields.keys())},
    )
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[Organization]:
    stmt = select(Organization).order_by(Organization.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


@router.post(
    "/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    payload: OrganizationCreate,
    request: Request,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_session),
) -> Organization:
    org = Organization(name=payload.name, country=payload.country, region=payload.region)
    session.add(org)
    await session.flush()
    await record_audit(
        session,
        action="organization.create",
        actor_user_id=admin.id,
        entity_type="organization",
        entity_id=org.id,
        request=request,
        metadata={"name": org.name},
    )
    await session.commit()
    await session.refresh(org)
    return org


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
