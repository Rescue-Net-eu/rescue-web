"""Reporting endpoints (manual section 23).

Three report types:

* **Mission report** (§23.1) — operational detail for one mission, for staff
  or the mission's Team Lead.
* **Volunteer activity** (§23.2) — per-volunteer participation. This is
  personal data, so it is built from live tables and is only meaningful within
  the participation-retention window (3y); it is deliberately *not* a public
  leaderboard.
* **Historical summary** (§23/§16.2) — anonymized, aggregate counts drawn from
  ``mission_archive``. Non-personal, so it covers the full ~10-year horizon.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import get_current_user, require_roles
from ..enums import AlertResponse, MissionStatus, UserRole
from ..models import (
    Alert,
    ChatMessage,
    Incident,
    Mission,
    MissionArchive,
    MissionMember,
    Responder,
    Task,
)
from ..schemas import (
    HistoricalSummaryRow,
    MissionReport,
    VolunteerActivityReport,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_STAFF = {
    UserRole.PLATFORM_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.DISPATCHER,
    UserRole.AUDITOR,
}
require_staff = require_roles(*_STAFF)


@router.get("/missions/{mission_id}", response_model=MissionReport)
async def mission_report(
    mission_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionReport:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    if UserRole(user.role) not in _STAFF and mission.lead_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this report"
        )

    incident = await session.get(Incident, mission.incident_id)
    responders = (
        await session.execute(
            select(MissionMember.user_id)
            .where(MissionMember.mission_id == mission_id)
            .distinct()
        )
    ).scalars().all()
    task_total = (
        await session.execute(
            select(func.count()).select_from(Task).where(Task.mission_id == mission_id)
        )
    ).scalar_one()
    task_completed = (
        await session.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.mission_id == mission_id, Task.status == "done")
        )
    ).scalar_one()
    chat_count = (
        await session.execute(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.mission_id == mission_id)
        )
    ).scalar_one()

    return MissionReport(
        mission_id=mission.id,
        incident_id=mission.incident_id,
        incident_title=incident.title if incident else None,
        incident_type=incident.type if incident else None,
        priority=incident.priority if incident else None,
        status=MissionStatus(mission.status),
        lead_user_id=mission.lead_user_id,
        started_at=mission.started_at,
        closed_at=mission.closed_at,
        closure_summary=mission.closure_summary,
        responders=list(responders),
        task_total=task_total,
        task_completed=task_completed,
        chat_message_count=chat_count,
    )


@router.get("/volunteers/{user_id}", response_model=VolunteerActivityReport)
async def volunteer_activity(
    user_id: uuid.UUID,
    requester=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VolunteerActivityReport:
    """Per-volunteer activity. Staff, or the volunteer about themselves (§16.4
    "export my data")."""
    if UserRole(requester.role) not in _STAFF and requester.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this report"
        )

    missions_joined = (
        await session.execute(
            select(func.count(func.distinct(MissionMember.mission_id))).where(
                MissionMember.user_id == user_id
            )
        )
    ).scalar_one()
    received = (
        await session.execute(
            select(func.count()).select_from(Alert).where(Alert.user_id == user_id)
        )
    ).scalar_one()
    accepted = (
        await session.execute(
            select(func.count())
            .select_from(Alert)
            .where(Alert.user_id == user_id, Alert.response == AlertResponse.YES)
        )
    ).scalar_one()
    declined = (
        await session.execute(
            select(func.count())
            .select_from(Alert)
            .where(Alert.user_id == user_id, Alert.response == AlertResponse.NO)
        )
    ).scalar_one()
    responder = (
        await session.execute(select(Responder).where(Responder.user_id == user_id))
    ).scalar_one_or_none()

    return VolunteerActivityReport(
        user_id=user_id,
        missions_joined=missions_joined,
        alerts_received=received,
        alerts_accepted=accepted,
        alerts_declined=declined,
        skills=list(responder.skills or []) if responder else [],
        home_region=responder.home_region if responder else None,
    )


@router.get("/historical", response_model=list[HistoricalSummaryRow])
async def historical_summary(
    _staff=Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> list[HistoricalSummaryRow]:
    """Anonymized aggregate counts by year from the long-term archive.

    Drawn only from ``mission_archive`` (no personal data), so it spans the
    full ~10-year retention horizon (manual sections 16.2, 23).
    """
    rows = (
        await session.execute(
            select(
                MissionArchive.year,
                func.count().label("missions"),
                func.coalesce(func.sum(MissionArchive.responder_count), 0).label("responders"),
                func.coalesce(func.sum(MissionArchive.duration_seconds), 0).label("duration"),
            )
            .group_by(MissionArchive.year)
            .order_by(MissionArchive.year.desc())
        )
    ).all()
    return [
        HistoricalSummaryRow(
            year=r.year,
            missions=r.missions,
            total_responders=int(r.responders),
            total_duration_seconds=int(r.duration),
        )
        for r in rows
    ]
