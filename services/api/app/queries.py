"""Reusable query helpers.

Geospatial responder candidate selection (manual section 9.1) is shared by
the incident candidates endpoint and the alert-send flow.
"""

from __future__ import annotations

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import func

from .enums import VerificationStatus
from .geo import latitude_of, longitude_of, make_point
from .models import Responder


async def find_candidates(
    session: AsyncSession,
    *,
    longitude: float,
    latitude: float,
    radius_m: int,
    verified_only: bool = True,
    skills: list[str] | None = None,
    limit: int = 50,
) -> list[Row]:
    """Return responder rows within ``radius_m`` of the point, nearest first.

    Each row is ``(Responder, distance_m, latitude, longitude)``. Selection
    mirrors manual section 9.1: proximity, verification status and skills.
    """
    center = make_point(longitude, latitude)
    distance = func.ST_Distance(Responder.home_location, center)
    stmt = (
        select(
            Responder,
            distance.label("distance_m"),
            latitude_of(Responder.home_location).label("lat"),
            longitude_of(Responder.home_location).label("lng"),
        )
        .where(Responder.home_location.isnot(None))
        .where(func.ST_DWithin(Responder.home_location, center, radius_m))
        .order_by(distance.asc())
        .limit(limit)
    )
    if verified_only:
        stmt = stmt.where(Responder.verification_status == VerificationStatus.VERIFIED.value)
    if skills:
        stmt = stmt.where(Responder.skills.op("&&")(skills))

    return list((await session.execute(stmt)).all())
