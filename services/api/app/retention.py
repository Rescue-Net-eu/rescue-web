"""GDPR data-retention sweeps (manual section 16.2).

Implements the two-tier retention model:

* **Personal data** (raw GPS samples, chat text, per-person participation) is
  purged or anonymized on the schedules in :class:`app.config.Settings`.
* **Anonymized history** is preserved in :class:`app.models.MissionArchive`,
  an aggregate, non-personal record kept for long-term reporting (manual
  section 23). Because it contains no personal data it is exempt from GDPR's
  storage-limitation principle (Recital 26), so deleting the personal data and
  retaining the archive are not in conflict.

Every sweep is **archive-first**: a mission's anonymized aggregate is written
before any of its personal data is removed, so nothing of reporting value is
lost. All functions are pure (no request context) and take an injectable
``now`` so they can be tested deterministically, mirroring ``app.alerting``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .models import (
    Alert,
    ChatMessage,
    Incident,
    Location,
    Mission,
    MissionArchive,
    MissionMember,
    Responder,
    Task,
)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


async def archive_mission(session: AsyncSession, mission: Mission) -> MissionArchive | None:
    """Build the anonymized aggregate for a closed mission. Idempotent.

    Returns the new ``MissionArchive`` row, or ``None`` if one already exists.
    Holds only counts and operational metadata — never user ids, coordinates
    or free text.
    """
    existing = (
        await session.execute(
            select(MissionArchive).where(MissionArchive.mission_id == mission.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return None

    incident = await session.get(Incident, mission.incident_id)

    responder_count = (
        await session.execute(
            select(func.count(func.distinct(MissionMember.user_id))).where(
                MissionMember.mission_id == mission.id
            )
        )
    ).scalar_one()
    accepted_count = (
        await session.execute(
            select(func.count())
            .select_from(Alert)
            .where(Alert.incident_id == mission.incident_id, Alert.response == "yes")
        )
    ).scalar_one()
    task_total = (
        await session.execute(
            select(func.count()).select_from(Task).where(Task.mission_id == mission.id)
        )
    ).scalar_one()
    task_completed = (
        await session.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.mission_id == mission.id, Task.status == "done")
        )
    ).scalar_one()
    chat_count = (
        await session.execute(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.mission_id == mission.id)
        )
    ).scalar_one()
    location_count = (
        await session.execute(
            select(func.count()).select_from(Location).where(Location.mission_id == mission.id)
        )
    ).scalar_one()

    # Union of skills across participating responders (aggregate, not per-person).
    skill_rows = (
        await session.execute(
            select(Responder.skills)
            .join(MissionMember, MissionMember.user_id == Responder.user_id)
            .where(MissionMember.mission_id == mission.id)
        )
    ).scalars().all()
    skills_used = sorted({s for row in skill_rows if row for s in row})

    duration = None
    if mission.started_at and mission.closed_at:
        duration = int((mission.closed_at - mission.started_at).total_seconds())

    archive = MissionArchive(
        mission_id=mission.id,
        incident_type=incident.type if incident else None,
        priority=incident.priority if incident else None,
        region=None,  # incidents carry no region in the MVP schema
        final_status=str(mission.status),
        year=mission.closed_at.year if mission.closed_at else None,
        started_at=mission.started_at,
        closed_at=mission.closed_at,
        duration_seconds=duration,
        responder_count=responder_count,
        accepted_count=accepted_count,
        task_total=task_total,
        task_completed=task_completed,
        chat_message_count=chat_count,
        location_sample_count=location_count,
        skills_used=skills_used,
    )
    session.add(archive)
    await session.flush()
    return archive


async def archive_closed_missions(
    session: AsyncSession, *, now: datetime | None = None
) -> int:
    """Archive every closed mission that lacks an archive row. Returns count."""
    archived_ids = select(MissionArchive.mission_id)
    missions = (
        await session.execute(
            select(Mission)
            .where(Mission.status == "closed", Mission.id.notin_(archived_ids))
        )
    ).scalars().all()
    count = 0
    for mission in missions:
        if await archive_mission(session, mission) is not None:
            count += 1
    return count


async def purge_expired_locations(
    session: AsyncSession, *, now: datetime | None = None, settings: Settings | None = None
) -> int:
    """Delete raw location samples for missions closed beyond the window.

    Archive-first: the mission's aggregate (which records the sample count) is
    written before the raw points are deleted (manual section 16.2: "Raw
    location samples: 30 days after mission closure").
    """
    settings = settings or get_settings()
    cutoff = _now(now) - timedelta(days=settings.location_retention_days)

    missions = (
        await session.execute(
            select(Mission).where(Mission.status == "closed", Mission.closed_at < cutoff)
        )
    ).scalars().all()
    deleted = 0
    for mission in missions:
        await archive_mission(session, mission)  # idempotent
        result = await session.execute(
            delete(Location).where(Location.mission_id == mission.id)
        )
        deleted += result.rowcount or 0
    return deleted


async def anonymize_old_participation(
    session: AsyncSession, *, now: datetime | None = None, settings: Settings | None = None
) -> int:
    """Strip free text from participation older than the retention window.

    Chat bodies are blanked (and tombstoned) and task descriptions cleared for
    missions closed beyond ``participation_retention_days``. Aggregate counts
    already live in the archive, so reporting is unaffected. Returns the number
    of missions processed.
    """
    settings = settings or get_settings()
    cutoff = _now(now) - timedelta(days=settings.participation_retention_days)

    missions = (
        await session.execute(
            select(Mission.id).where(Mission.status == "closed", Mission.closed_at < cutoff)
        )
    ).scalars().all()
    for mission_id in missions:
        # Ensure history is captured before stripping detail.
        mission = await session.get(Mission, mission_id)
        if mission is not None:
            await archive_mission(session, mission)
        await session.execute(
            update(ChatMessage)
            .where(ChatMessage.mission_id == mission_id, ChatMessage.deleted_at.is_(None))
            .values(message="", deleted_at=_now(now))
        )
        await session.execute(
            update(Task)
            .where(Task.mission_id == mission_id, Task.description.isnot(None))
            .values(description=None)
        )
    return len(missions)


async def purge_old_audit_logs(
    session: AsyncSession, *, now: datetime | None = None, settings: Settings | None = None
) -> int:
    """Delete audit logs older than the retention window.

    Note: a legal hold or compliance requirement may extend this; configure
    ``audit_retention_days`` accordingly (manual section 16.2).
    """
    from .models import AuditLog

    settings = settings or get_settings()
    cutoff = _now(now) - timedelta(days=settings.audit_retention_days)
    result = await session.execute(delete(AuditLog).where(AuditLog.timestamp < cutoff))
    return result.rowcount or 0


async def run_all(
    session: AsyncSession, *, now: datetime | None = None, settings: Settings | None = None
) -> dict[str, int]:
    """Run every retention sweep in a safe order and commit. Returns counts."""
    settings = settings or get_settings()
    counts = {
        "archived": await archive_closed_missions(session, now=now),
        "locations_purged": await purge_expired_locations(session, now=now, settings=settings),
        "participation_anonymized": await anonymize_old_participation(
            session, now=now, settings=settings
        ),
        "audit_logs_purged": await purge_old_audit_logs(session, now=now, settings=settings),
    }
    await session.commit()
    return counts
