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
from sqlalchemy.sql.functions import func

from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user, require_dispatcher
from ..enums import IncidentStatus, VerificationStatus
from ..geo import latitude_of, longitude_of, make_point
from ..models import Incident, Responder, User
from ..schemas import (
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
    ResponderCandidate,
)

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

    center = make_point(lng, lat)
    distance = func.ST_Distance(Responder.home_location, center)
    stmt = (
        select(
            Responder,
            distance.label("distance_m"),
            latitude_of(Responder.home_location).label("lat"),
            longitude_of(Responder.home_location).label("lng"),
        )
        .where(Responder.home_location.isnot(None))
        .where(func.ST_DWithin(Responder.home_location, center, incident.radius_m))
        .order_by(distance.asc())
        .limit(limit)
    )
    if verified_only:
        stmt = stmt.where(Responder.verification_status == VerificationStatus.VERIFIED.value)
    if skills:
        stmt = stmt.where(Responder.skills.op("&&")(skills))

    rows = (await session.execute(stmt)).all()
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


# --- Stubs deferred to the next increment (alerting + mission creation) ----

_NOT_IMPLEMENTED = "Not implemented in this increment; see manual section 27."


@router.post("/{incident_id}/alerts", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def trigger_alerts(incident_id: uuid.UUID) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{incident_id}/create-mission", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_mission(incident_id: uuid.UUID) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}
