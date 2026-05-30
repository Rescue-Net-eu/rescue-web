"""Mission endpoints (manual sections 5.3, 5.4, 8, 14.1).

Implements mission listing, retrieval and status transitions. Membership
governs visibility for non-staff roles. The mission room (WebSocket), chat,
tasks, live location and closure land in later increments and remain stubs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user
from ..enums import MissionStatus, UserRole
from ..models import Mission, MissionMember, User
from ..schemas import MissionMemberOut, MissionOut, MissionUpdate

router = APIRouter(prefix="/missions", tags=["missions"])

# Roles that may see and manage every mission (manual section 6).
_STAFF_ROLES = {
    UserRole.PLATFORM_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.DISPATCHER,
    UserRole.AUDITOR,
}


async def mission_out(session: AsyncSession, mission_id: uuid.UUID) -> MissionOut:
    """Serialize a mission with its current members."""
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    members = (
        await session.execute(
            select(MissionMember).where(MissionMember.mission_id == mission_id)
        )
    ).scalars().all()
    return MissionOut(
        id=mission.id,
        incident_id=mission.incident_id,
        lead_user_id=mission.lead_user_id,
        status=MissionStatus(mission.status),
        started_at=mission.started_at,
        closed_at=mission.closed_at,
        created_at=mission.created_at,
        members=[
            MissionMemberOut(
                user_id=m.user_id,
                role_in_mission=m.role_in_mission,
                joined_at=m.joined_at,
                left_at=m.left_at,
                live_location_enabled=m.live_location_enabled,
            )
            for m in members
        ],
    )


async def _is_member(session: AsyncSession, mission_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    found = await session.execute(
        select(MissionMember.id).where(
            MissionMember.mission_id == mission_id, MissionMember.user_id == user_id
        )
    )
    return found.first() is not None


@router.get("", response_model=list[MissionOut])
async def list_missions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MissionOut]:
    stmt = select(Mission.id).order_by(Mission.created_at.desc()).limit(limit)
    if UserRole(user.role) not in _STAFF_ROLES:
        # Non-staff see only missions they lead or belong to.
        member_missions = select(MissionMember.mission_id).where(
            MissionMember.user_id == user.id
        )
        stmt = stmt.where(
            (Mission.lead_user_id == user.id) | (Mission.id.in_(member_missions))
        )
    ids = (await session.execute(stmt)).scalars().all()
    return [await mission_out(session, mid) for mid in ids]


@router.get("/{mission_id}", response_model=MissionOut)
async def get_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    if UserRole(user.role) not in _STAFF_ROLES:
        is_member = await _is_member(session, mission_id, user.id)
        if mission.lead_user_id != user.id and not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not a mission member"
            )
    return await mission_out(session, mission_id)


@router.patch("/{mission_id}", response_model=MissionOut)
async def update_mission(
    mission_id: uuid.UUID,
    payload: MissionUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Update mission status. Allowed for staff or the assigned Team Lead."""
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    is_lead = mission.lead_user_id == user.id
    if UserRole(user.role) not in _STAFF_ROLES and not is_lead:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff or the Team Lead can update the mission",
        )

    previous = mission.status
    mission.status = payload.status
    if payload.status == MissionStatus.ACTIVE and mission.started_at is None:
        mission.started_at = datetime.now(UTC)

    await record_audit(
        session,
        action="mission.status_changed",
        actor_user_id=user.id,
        entity_type="mission",
        entity_id=mission.id,
        request=request,
        metadata={"from": str(previous), "to": str(payload.status)},
    )
    await session.commit()
    return await mission_out(session, mission_id)


# --- Deferred to later increments (mission room, chat, tasks, closure) -----

_NOT_IMPLEMENTED = "Not implemented in this increment; see manual section 27."


@router.post("/{mission_id}/join", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def join_mission(mission_id: uuid.UUID) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{mission_id}/leave", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def leave_mission(mission_id: uuid.UUID) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{mission_id}/close", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def close_mission(mission_id: uuid.UUID) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.get("/{mission_id}/messages")
async def list_messages(mission_id: uuid.UUID) -> list[dict]:
    return []


@router.get("/{mission_id}/tasks")
async def list_tasks(mission_id: uuid.UUID) -> list[dict]:
    return []
