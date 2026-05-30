"""On-demand data-subject erasure (manual section 16.4 "Delete my account").

Erasing a user removes their personal data while keeping the operational and
audit trail intact, per the manual's rule to "anonymize where deletion
conflicts with operational audit requirements" (section 16.2):

* The ``users`` row is **tombstoned** — email/name/phone are cleared (email is
  replaced with a unique non-routable placeholder so the UNIQUE constraint
  holds) and ``status`` is set to ``deleted`` so the account can no longer
  authenticate.
* Genuinely personal granular data is **deleted**: the user's raw location
  samples and responder geolocation/display name; their chat message bodies
  are blanked.
* Structural rows that carry no standalone PII — ``mission_members``,
  ``alerts`` and ``audit_logs`` — are **kept**. Once the ``users`` row is
  tombstoned, the ``user_id`` they reference is a random UUID with no reverse
  map to a person, so the remaining trail is effectively anonymized while
  staying useful for audit and aggregate reporting.

Closed missions the user touched are archived first, so their contribution
survives in the anonymized historical tier (see ``app.retention``).

Caveat: this is anonymization-by-tombstoning, not row deletion. UUID linkage
between rows remains, but it is non-identifying once all PII is gone. This is
the documented compliance posture for an auditable safety-critical system.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .audit import record_audit
from .models import ChatMessage, Location, Mission, MissionMember, Responder, User
from .retention import archive_mission


class UserNotFound(Exception):
    """Raised when erasure targets a user id that does not exist."""


async def erase_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Erase a user's personal data, preserving anonymized history and audit.

    Returns a summary of what was removed. Commits the transaction.
    """
    now = now or datetime.now(UTC)
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFound(str(user_id))

    # 1. Preserve history: archive closed missions this user participated in,
    #    so their (anonymized) contribution survives the erasure.
    mission_ids = (
        await session.execute(
            select(MissionMember.mission_id)
            .where(MissionMember.user_id == user_id)
            .distinct()
        )
    ).scalars().all()
    archived = 0
    for mid in mission_ids:
        mission = await session.get(Mission, mid)
        if mission is not None and str(mission.status) == "closed":
            if await archive_mission(session, mission) is not None:
                archived += 1

    # 2. Delete genuinely personal granular data.
    locations_deleted = (
        await session.execute(delete(Location).where(Location.user_id == user_id))
    ).rowcount or 0

    chats_blanked = (
        await session.execute(
            update(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.deleted_at.is_(None))
            .values(message="", deleted_at=now)
        )
    ).rowcount or 0

    await session.execute(
        update(Responder)
        .where(Responder.user_id == user_id)
        .values(display_name=None, home_location=None, home_region=None)
    )

    # 3. Tombstone the user row (removes PII, blocks login). The placeholder
    #    email keeps the UNIQUE constraint satisfied and is non-routable.
    user.email = f"deleted+{user_id}@anonymized.invalid"
    user.full_name = None
    user.phone = None
    user.status = "deleted"

    # 4. mission_members / alerts / audit_logs are intentionally retained.
    await record_audit(
        session,
        action="user.erase",
        actor_user_id=actor_user_id or user_id,
        entity_type="user",
        entity_id=user_id,
        metadata={
            "locations_deleted": locations_deleted,
            "chats_blanked": chats_blanked,
            "missions_archived": archived,
        },
    )
    await session.commit()
    return {
        "locations_deleted": locations_deleted,
        "chats_blanked": chats_blanked,
        "missions_archived": archived,
    }
