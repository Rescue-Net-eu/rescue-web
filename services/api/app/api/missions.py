"""Mission endpoints — the mission room (manual sections 5.3, 5.4, 5.5, 8, 14).

Covers mission listing/retrieval, status transitions, membership (join/leave
with explicit live-location consent), chat, live location ingestion and
closure. Realtime updates are published to Redis (manual section 14.2) for
WebSocket fan-out; see ``app/api/ws.py``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import events
from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user
from ..enums import AlertResponse, MissionStatus, UserRole
from ..geo import latitude_of, longitude_of, make_point
from ..models import Alert, ChatMessage, Location, Mission, MissionMember, User
from ..schemas import (
    ChatMessageCreate,
    ChatMessageOut,
    LocationCreate,
    LocationOut,
    MissionCloseRequest,
    MissionJoinRequest,
    MissionMemberOut,
    MissionOut,
    MissionUpdate,
)

router = APIRouter(prefix="/missions", tags=["missions"])

# Staff who can see every mission (manual section 6). Auditors read but never
# modify operational data (section 6.6), so they are excluded from write roles.
_STAFF_READ = {
    UserRole.PLATFORM_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.DISPATCHER,
    UserRole.AUDITOR,
}
_STAFF_WRITE = {UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN, UserRole.DISPATCHER}

_TERMINAL = {MissionStatus.CLOSED, MissionStatus.CANCELLED}


# --- Serialization & lookups ---------------------------------------------


async def mission_out(session: AsyncSession, mission_id: uuid.UUID) -> MissionOut:
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


async def _get_mission(session: AsyncSession, mission_id: uuid.UUID) -> Mission:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


async def _active_member(
    session: AsyncSession, mission_id: uuid.UUID, user_id: uuid.UUID
) -> MissionMember | None:
    result = await session.execute(
        select(MissionMember).where(
            MissionMember.mission_id == mission_id,
            MissionMember.user_id == user_id,
            MissionMember.left_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _ensure_can_read(session: AsyncSession, mission: Mission, user: User) -> None:
    if UserRole(user.role) in _STAFF_READ or mission.lead_user_id == user.id:
        return
    if await _active_member(session, mission.id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a mission member")


def _ensure_writable(mission: Mission) -> None:
    if MissionStatus(mission.status) in _TERMINAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Mission is closed"
        )


async def _publish(request: Request, mission_id: uuid.UUID, event_type: str, data: dict) -> None:
    await request.app.state.broker.publish(mission_id, event_type, data)


# --- Listing & retrieval --------------------------------------------------


@router.get("", response_model=list[MissionOut])
async def list_missions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MissionOut]:
    stmt = select(Mission.id).order_by(Mission.created_at.desc()).limit(limit)
    if UserRole(user.role) not in _STAFF_READ:
        member_missions = select(MissionMember.mission_id).where(MissionMember.user_id == user.id)
        stmt = stmt.where((Mission.lead_user_id == user.id) | (Mission.id.in_(member_missions)))
    ids = (await session.execute(stmt)).scalars().all()
    return [await mission_out(session, mid) for mid in ids]


@router.get("/{mission_id}", response_model=MissionOut)
async def get_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    mission = await _get_mission(session, mission_id)
    await _ensure_can_read(session, mission, user)
    return await mission_out(session, mission_id)


@router.patch("/{mission_id}", response_model=MissionOut)
async def update_mission(
    mission_id: uuid.UUID,
    payload: MissionUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Update mission status. Allowed for write-staff or the assigned Team Lead."""
    mission = await _get_mission(session, mission_id)
    is_lead = mission.lead_user_id == user.id
    if UserRole(user.role) not in _STAFF_WRITE and not is_lead:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff or the Team Lead can update the mission",
        )
    _ensure_writable(mission)

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
    await _publish(
        request, mission_id, events.STATUS_CHANGED, {"status": str(payload.status)}
    )
    return await mission_out(session, mission_id)


# --- Membership -----------------------------------------------------------


@router.post("/{mission_id}/join", response_model=MissionOut)
async def join_mission(
    mission_id: uuid.UUID,
    payload: MissionJoinRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Join a mission and optionally enable live location (explicit consent)."""
    mission = await _get_mission(session, mission_id)
    _ensure_writable(mission)

    member = (
        await session.execute(
            select(MissionMember).where(
                MissionMember.mission_id == mission_id, MissionMember.user_id == user.id
            )
        )
    ).scalar_one_or_none()

    if member is None:
        # Only responders who were invited (accepted an alert for the incident)
        # may self-join (manual section 5.3, 22.2).
        accepted = await session.execute(
            select(Alert.id).where(
                Alert.incident_id == mission.incident_id,
                Alert.user_id == user.id,
                Alert.response == AlertResponse.YES,
            )
        )
        if accepted.first() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You were not invited to this mission",
            )
        member = MissionMember(mission_id=mission_id, user_id=user.id, role_in_mission="responder")
        session.add(member)
    else:
        member.left_at = None

    if payload.live_location_enabled and not member.live_location_enabled:
        await _record_consent(session, user.id, request)
    member.live_location_enabled = payload.live_location_enabled

    await record_audit(
        session,
        action="mission.join",
        actor_user_id=user.id,
        entity_type="mission",
        entity_id=mission_id,
        request=request,
        metadata={"live_location_enabled": payload.live_location_enabled},
    )
    await session.commit()
    await _publish(
        request,
        mission_id,
        events.MEMBER_JOINED,
        {"user_id": str(user.id), "live_location_enabled": payload.live_location_enabled},
    )
    return await mission_out(session, mission_id)


@router.post("/{mission_id}/leave", response_model=MissionOut)
async def leave_mission(
    mission_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Leave a mission; live location sharing stops immediately (manual §16.2)."""
    mission = await _get_mission(session, mission_id)
    member = await _active_member(session, mission_id, user.id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not an active member")

    member.left_at = datetime.now(UTC)
    member.live_location_enabled = False

    await record_audit(
        session,
        action="mission.leave",
        actor_user_id=user.id,
        entity_type="mission",
        entity_id=mission_id,
        request=request,
    )
    await session.commit()
    await _publish(request, mission_id, events.MEMBER_LEFT, {"user_id": str(user.id)})
    return await mission_out(session, mission_id)


# --- Closure --------------------------------------------------------------


@router.post("/{mission_id}/close", response_model=MissionOut)
async def close_mission(
    mission_id: uuid.UUID,
    payload: MissionCloseRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Close a mission: stop all live location sharing and lock it (manual §5.5)."""
    mission = await _get_mission(session, mission_id)
    is_lead = mission.lead_user_id == user.id
    if UserRole(user.role) not in _STAFF_WRITE and not is_lead:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff or the Team Lead can close the mission",
        )
    if MissionStatus(mission.status) == MissionStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mission already closed")

    now = datetime.now(UTC)
    mission.status = MissionStatus.CLOSED
    mission.closed_at = now
    mission.closure_summary = payload.closure_summary

    # Stop live location for everyone (manual section 16.2).
    members = (
        await session.execute(
            select(MissionMember).where(MissionMember.mission_id == mission_id)
        )
    ).scalars().all()
    for member in members:
        member.live_location_enabled = False

    await record_audit(
        session,
        action="mission.close",
        actor_user_id=user.id,
        entity_type="mission",
        entity_id=mission_id,
        request=request,
    )
    await session.commit()
    await _publish(request, mission_id, events.CLOSED, {})
    return await mission_out(session, mission_id)


# --- Chat -----------------------------------------------------------------


@router.get("/{mission_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ChatMessageOut]:
    mission = await _get_mission(session, mission_id)
    await _ensure_can_read(session, mission, user)
    rows = (
        await session.execute(
            select(ChatMessage)
            .where(ChatMessage.mission_id == mission_id, ChatMessage.deleted_at.is_(None))
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        ChatMessageOut(
            id=m.id,
            mission_id=m.mission_id,
            user_id=m.user_id,
            message=m.message,
            created_at=m.created_at,
        )
        for m in rows
    ]


@router.post(
    "/{mission_id}/messages",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    mission_id: uuid.UUID,
    payload: ChatMessageCreate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatMessageOut:
    mission = await _get_mission(session, mission_id)
    _ensure_writable(mission)
    await _ensure_can_write_room(session, mission, user)

    message = ChatMessage(mission_id=mission_id, user_id=user.id, message=payload.message)
    session.add(message)
    await session.commit()
    await session.refresh(message)

    out = ChatMessageOut(
        id=message.id,
        mission_id=message.mission_id,
        user_id=message.user_id,
        message=message.message,
        created_at=message.created_at,
    )
    await _publish(request, mission_id, events.CHAT_MESSAGE, out.model_dump(mode="json"))
    return out


# --- Live location --------------------------------------------------------


@router.post(
    "/{mission_id}/locations",
    response_model=LocationOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_location(
    mission_id: uuid.UUID,
    payload: LocationCreate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LocationOut:
    """Ingest a live location sample (active membership + explicit consent)."""
    mission = await _get_mission(session, mission_id)
    _ensure_writable(mission)

    member = await _active_member(session, mission_id, user.id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an active member")
    if not member.live_location_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live location sharing is not enabled; join with consent first",
        )

    location = Location(
        mission_id=mission_id,
        user_id=user.id,
        point=make_point(payload.longitude, payload.latitude),
        accuracy_m=payload.accuracy_m,
        speed=payload.speed,
        heading=payload.heading,
    )
    session.add(location)
    await session.commit()
    await session.refresh(location)

    out = LocationOut(
        user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
        speed=payload.speed,
        heading=payload.heading,
        timestamp=location.timestamp,
    )
    await _publish(request, mission_id, events.LOCATION_UPDATED, out.model_dump(mode="json"))
    return out


@router.get("/{mission_id}/locations/live", response_model=list[LocationOut])
async def live_locations(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LocationOut]:
    """Latest known location per member (manual section 5.4)."""
    mission = await _get_mission(session, mission_id)
    await _ensure_can_read(session, mission, user)
    rows = (
        await session.execute(
            select(
                Location.user_id,
                latitude_of(Location.point).label("lat"),
                longitude_of(Location.point).label("lng"),
                Location.accuracy_m,
                Location.speed,
                Location.heading,
                Location.timestamp,
            )
            .where(Location.mission_id == mission_id)
            .order_by(Location.user_id, Location.timestamp.desc())
            .distinct(Location.user_id)
        )
    ).all()
    return [
        LocationOut(
            user_id=r.user_id,
            latitude=r.lat,
            longitude=r.lng,
            accuracy_m=r.accuracy_m,
            speed=r.speed,
            heading=r.heading,
            timestamp=r.timestamp,
        )
        for r in rows
    ]


@router.get("/{mission_id}/tasks")
async def list_tasks(mission_id: uuid.UUID) -> list[dict]:
    # Task management lands in a later increment (manual section 27).
    return []


# --- Helpers --------------------------------------------------------------


async def _ensure_can_write_room(session: AsyncSession, mission: Mission, user: User) -> None:
    """Chat/operational writes: write-staff, the lead, or an active member."""
    if UserRole(user.role) in _STAFF_WRITE or mission.lead_user_id == user.id:
        return
    if await _active_member(session, mission.id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a mission member")


async def _record_consent(session: AsyncSession, user_id: uuid.UUID, request: Request) -> None:
    """Record explicit live-location consent (manual sections 16.2, 16.3)."""
    from ..models import ConsentRecord

    session.add(
        ConsentRecord(
            user_id=user_id,
            consent_type="live_location",
            consent_version="1.0",
            accepted_at=datetime.now(UTC),
            ip_address=request.client.host if request.client else None,
        )
    )
