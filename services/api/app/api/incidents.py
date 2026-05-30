"""Incident endpoints (manual sections 5.1, 9.1, 14.1).

Implements incident CRUD, closure, and geospatial responder candidate
search. All mutating actions are RBAC-guarded and audited. Alerting and
mission creation from an incident remain stubs in this increment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..alerting import (
    ALERT_SEND_ACTION,
    RATE_LIMIT_CAMPAIGNS,
    expiry_for_priority,
    recent_campaign_count,
)
from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user, require_dispatcher
from ..enums import AlertResponse, IncidentStatus, MissionStatus, VerificationStatus
from ..geo import latitude_of, longitude_of, make_point
from ..models import Alert, Incident, Mission, MissionMember, User
from ..queries import find_candidates
from ..schemas import (
    AlertSendRequest,
    AlertSendResult,
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
    MissionCreateRequest,
    MissionOut,
    ResponderCandidate,
)
from .missions import mission_out

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _incident_out(
    incident: Incident, latitude: float | None, longitude: float | None
) -> IncidentOut:
    return IncidentOut(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        type=incident.type,
        priority=incident.priority,
        status=IncidentStatus(incident.status),
        created_by=incident.created_by,
        latitude=latitude,
        longitude=longitude,
        radius_m=incident.radius_m,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        closed_at=incident.closed_at,
    )


_SELECT_WITH_COORDS = select(
    Incident,
    latitude_of(Incident.center_point).label("lat"),
    longitude_of(Incident.center_point).label("lng"),
)


async def _load_incident(
    session: AsyncSession, incident_id: uuid.UUID
) -> tuple[Incident, float | None, float | None]:
    result = await session.execute(_SELECT_WITH_COORDS.where(Incident.id == incident_id))
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return row[0], row[1], row[2]


@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[IncidentOut]:
    stmt = _SELECT_WITH_COORDS.order_by(Incident.created_at.desc()).limit(limit)
    if status_filter is not None:
        stmt = stmt.where(Incident.status == status_filter.value)
    rows = (await session.execute(stmt)).all()
    return [_incident_out(inc, lat, lng) for inc, lat, lng in rows]


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    request: Request,
    user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    if (payload.latitude is None) != (payload.longitude is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="latitude and longitude must be provided together",
        )

    incident = Incident(
        title=payload.title,
        description=payload.description,
        type=payload.type,
        priority=payload.priority,
        status=IncidentStatus.OPEN,
        created_by=user.id,
        radius_m=payload.radius_m,
    )
    if payload.latitude is not None and payload.longitude is not None:
        incident.center_point = make_point(payload.longitude, payload.latitude)
    session.add(incident)
    await session.flush()

    await record_audit(
        session,
        action="incident.create",
        actor_user_id=user.id,
        entity_type="incident",
        entity_id=incident.id,
        request=request,
        metadata={"title": incident.title, "priority": incident.priority},
    )
    await session.commit()
    await session.refresh(incident)
    return _incident_out(incident, payload.latitude, payload.longitude)


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: uuid.UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    incident, lat, lng = await _load_incident(session, incident_id)
    return _incident_out(incident, lat, lng)


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    request: Request,
    user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    incident, lat, lng = await _load_incident(session, incident_id)

    fields = payload.model_dump(exclude_unset=True)
    for attr in ("title", "description", "type", "priority", "radius_m"):
        if attr in fields:
            setattr(incident, attr, fields[attr])
    if "status" in fields and fields["status"] is not None:
        incident.status = IncidentStatus(fields["status"])

    if "latitude" in fields or "longitude" in fields:
        new_lat = fields.get("latitude", lat)
        new_lng = fields.get("longitude", lng)
        if (new_lat is None) != (new_lng is None):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="latitude and longitude must be set together",
            )
        incident.center_point = make_point(new_lng, new_lat) if new_lat is not None else None
        lat, lng = new_lat, new_lng

    await record_audit(
        session,
        action="incident.update",
        actor_user_id=user.id,
        entity_type="incident",
        entity_id=incident.id,
        request=request,
        metadata={"fields": sorted(fields.keys())},
    )
    await session.commit()
    await session.refresh(incident)
    return _incident_out(incident, lat, lng)


@router.post("/{incident_id}/close", response_model=IncidentOut)
async def close_incident(
    incident_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    incident, lat, lng = await _load_incident(session, incident_id)
    if incident.status == IncidentStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident already closed")

    incident.status = IncidentStatus.CLOSED
    incident.closed_at = datetime.now(UTC)
    await record_audit(
        session,
        action="incident.close",
        actor_user_id=user.id,
        entity_type="incident",
        entity_id=incident.id,
        request=request,
    )
    await session.commit()
    await session.refresh(incident)
    return _incident_out(incident, lat, lng)


@router.get("/{incident_id}/candidates", response_model=list[ResponderCandidate])
async def responder_candidates(
    incident_id: uuid.UUID,
    _user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
    verified_only: bool = Query(default=True),
    skills: list[str] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ResponderCandidate]:
    """Find responders near the incident, ordered by distance (manual 9.1).

    Geographic proximity uses the incident's centre point and radius; the
    result can be further narrowed by verification status and required skills.
    """
    incident, lat, lng = await _load_incident(session, incident_id)
    if lat is None or lng is None or incident.radius_m is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incident has no centre point and radius to search within",
        )

    rows = await find_candidates(
        session,
        longitude=lng,
        latitude=lat,
        radius_m=incident.radius_m,
        verified_only=verified_only,
        skills=skills,
        limit=limit,
    )
    return [
        ResponderCandidate(
            id=r.id,
            user_id=r.user_id,
            organization_id=r.organization_id,
            display_name=r.display_name,
            verification_status=VerificationStatus(r.verification_status),
            home_region=r.home_region,
            latitude=r_lat,
            longitude=r_lng,
            skills=list(r.skills or []),
            equipment=list(r.equipment or []),
            availability_status=r.availability_status,
            distance_m=float(dist),
        )
        for r, dist, r_lat, r_lng in rows
    ]


@router.post(
    "/{incident_id}/alerts",
    response_model=AlertSendResult,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_alerts(
    incident_id: uuid.UUID,
    payload: AlertSendRequest,
    request: Request,
    user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
) -> AlertSendResult:
    """Alert nearby responders for an incident (manual sections 5.2, 9).

    Selects candidates by proximity/skills, creates one alert per recipient
    with a priority-based expiry, and moves the incident to ``alerting``.
    """
    incident, lat, lng = await _load_incident(session, incident_id)
    if incident.status in {IncidentStatus.CLOSED, IncidentStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident is not active")
    if lat is None or lng is None or incident.radius_m is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incident has no centre point and radius to alert within",
        )
    # High-priority alerts must carry a reason (manual section 22.1).
    if incident.priority == "high" and not (payload.reason and payload.reason.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A reason is required for high-priority alerts",
        )

    # Anti-abuse rate limit per dispatcher (manual section 9.5).
    if await recent_campaign_count(session, user.id) >= RATE_LIMIT_CAMPAIGNS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Alert rate limit exceeded; please wait before sending more",
        )

    rows = await find_candidates(
        session,
        longitude=lng,
        latitude=lat,
        radius_m=incident.radius_m,
        verified_only=payload.verified_only,
        skills=payload.skills or None,
        limit=payload.limit,
    )

    # Skip responders who already have an outstanding alert for this incident.
    existing = (
        await session.execute(
            select(Alert.user_id).where(
                Alert.incident_id == incident_id, Alert.status == "sent"
            )
        )
    ).scalars().all()
    already = set(existing)

    expiry = expiry_for_priority(incident.priority)
    created: list[Alert] = []
    for responder, *_ in rows:
        if responder.user_id in already:
            continue
        alert = Alert(
            incident_id=incident_id,
            user_id=responder.user_id,
            alert_type=payload.alert_type,
            status="sent",
            expiry_at=expiry,
        )
        session.add(alert)
        created.append(alert)

    if incident.status != IncidentStatus.ALERTING:
        incident.status = IncidentStatus.ALERTING
    await session.flush()

    await record_audit(
        session,
        action=ALERT_SEND_ACTION,
        actor_user_id=user.id,
        entity_type="incident",
        entity_id=incident_id,
        request=request,
        metadata={
            "alert_type": payload.alert_type,
            "recipients": len(created),
            "reason": payload.reason,
        },
    )
    await session.commit()

    return AlertSendResult(
        incident_id=incident_id,
        alert_type=payload.alert_type,
        expiry_at=expiry,
        recipients=len(created),
        alert_ids=[a.id for a in created],
    )


@router.post(
    "/{incident_id}/create-mission",
    response_model=MissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_mission(
    incident_id: uuid.UUID,
    payload: MissionCreateRequest,
    request: Request,
    user: User = Depends(require_dispatcher),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    """Create a mission from an incident and assign an optional Team Lead.

    Responders who accepted an alert for the incident are added as mission
    members (manual section 5.3).
    """
    incident, _lat, _lng = await _load_incident(session, incident_id)
    if incident.status in {IncidentStatus.CLOSED, IncidentStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident is not active")

    if payload.lead_user_id is not None:
        lead = await session.get(User, payload.lead_user_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead user not found")

    mission = Mission(
        incident_id=incident_id,
        lead_user_id=payload.lead_user_id,
        status=MissionStatus.PENDING,
    )
    session.add(mission)
    await session.flush()

    member_user_ids: set[uuid.UUID] = set()
    if payload.lead_user_id is not None:
        session.add(
            MissionMember(
                mission_id=mission.id,
                user_id=payload.lead_user_id,
                role_in_mission="team_lead",
            )
        )
        member_user_ids.add(payload.lead_user_id)

    if payload.auto_add_accepted:
        accepted = (
            await session.execute(
                select(Alert.user_id).where(
                    Alert.incident_id == incident_id, Alert.response == AlertResponse.YES
                )
            )
        ).scalars().all()
        for accepted_user in accepted:
            if accepted_user in member_user_ids:
                continue
            session.add(
                MissionMember(
                    mission_id=mission.id, user_id=accepted_user, role_in_mission="responder"
                )
            )
            member_user_ids.add(accepted_user)

    incident.status = IncidentStatus.MISSION_CREATED
    await record_audit(
        session,
        action="mission.create",
        actor_user_id=user.id,
        entity_type="mission",
        entity_id=mission.id,
        request=request,
        metadata={"incident_id": str(incident_id), "members": len(member_user_ids)},
    )
    await session.commit()
    return await mission_out(session, mission.id)
