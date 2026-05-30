"""Responder profile endpoints (manual sections 10, 6.2).

Organization/platform admins register and list responder profiles. Skills
and equipment are self-declared (manual section 10.2); verification status
is set by an admin (section 6.2 "Approve responders").
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user, require_admin
from ..enums import VerificationStatus
from ..geo import latitude_of, longitude_of, make_point
from ..models import Responder, User
from ..schemas import ResponderCreate, ResponderOut

router = APIRouter(prefix="/responders", tags=["responders"])

_SELECT_WITH_COORDS = select(
    Responder,
    latitude_of(Responder.home_location).label("lat"),
    longitude_of(Responder.home_location).label("lng"),
)


def _responder_out(r: Responder, lat: float | None, lng: float | None) -> ResponderOut:
    return ResponderOut(
        id=r.id,
        user_id=r.user_id,
        organization_id=r.organization_id,
        display_name=r.display_name,
        verification_status=VerificationStatus(r.verification_status),
        home_region=r.home_region,
        latitude=lat,
        longitude=lng,
        skills=list(r.skills or []),
        equipment=list(r.equipment or []),
        availability_status=r.availability_status,
    )


@router.get("", response_model=list[ResponderOut])
async def list_responders(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ResponderOut]:
    rows = (await session.execute(_SELECT_WITH_COORDS.limit(limit))).all()
    return [_responder_out(r, lat, lng) for r, lat, lng in rows]


@router.post("", response_model=ResponderOut, status_code=status.HTTP_201_CREATED)
async def create_responder(
    payload: ResponderCreate,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponderOut:
    if (payload.latitude is None) != (payload.longitude is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="latitude and longitude must be provided together",
        )

    target = await session.get(User, payload.user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = await session.execute(
        select(Responder).where(Responder.user_id == payload.user_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Responder profile already exists for this user",
        )

    responder = Responder(
        user_id=payload.user_id,
        organization_id=payload.organization_id,
        display_name=payload.display_name,
        verification_status=payload.verification_status,
        home_region=payload.home_region,
        skills=payload.skills,
        equipment=payload.equipment,
        availability_status=payload.availability_status,
    )
    if payload.latitude is not None and payload.longitude is not None:
        responder.home_location = make_point(payload.longitude, payload.latitude)
    session.add(responder)
    await session.flush()

    await record_audit(
        session,
        action="responder.create",
        actor_user_id=admin.id,
        entity_type="responder",
        entity_id=responder.id,
        request=request,
        metadata={"verification_status": responder.verification_status},
    )
    await session.commit()
    await session.refresh(responder)
    return _responder_out(responder, payload.latitude, payload.longitude)
