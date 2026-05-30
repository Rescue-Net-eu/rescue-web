"""Mission room WebSocket (manual section 14.2).

Clients connect to ``/ws/missions/{mission_id}?token=...`` and receive the
mission's realtime events (member join/leave, chat, location, status,
closure). Authentication is via the access token in the query string since
browsers cannot set headers on WebSocket connections. Events are sourced
from Redis pub/sub so they fan out across API instances.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..enums import UserRole
from ..models import Mission, MissionMember, User
from ..security import TokenError, decode_token

router = APIRouter(tags=["missions"])

# Close codes (4xxx are application-defined).
_UNAUTHORIZED = 4401
_FORBIDDEN = 4403
_NOT_FOUND = 4404
_UNAVAILABLE = 1011

_STAFF_READ = {
    UserRole.PLATFORM_ADMIN,
    UserRole.ORG_ADMIN,
    UserRole.DISPATCHER,
    UserRole.AUDITOR,
}


async def _authorize(session: AsyncSession, mission_id: uuid.UUID, token: str | None):
    """Return (user, mission) if the token grants read access, else a close code."""
    if not token:
        return None, _UNAUTHORIZED
    try:
        claims = decode_token(token)
        user_id = uuid.UUID(str(claims.get("sub")))
    except (TokenError, ValueError, TypeError):
        return None, _UNAUTHORIZED

    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        return None, _UNAUTHORIZED

    mission = await session.get(Mission, mission_id)
    if mission is None:
        return None, _NOT_FOUND

    if UserRole(user.role) in _STAFF_READ or mission.lead_user_id == user.id:
        return user, None
    member = await session.execute(
        select(MissionMember.id).where(
            MissionMember.mission_id == mission_id,
            MissionMember.user_id == user.id,
            MissionMember.left_at.is_(None),
        )
    )
    if member.first() is None:
        return None, _FORBIDDEN
    return user, None


@router.websocket("/ws/missions/{mission_id}")
async def mission_ws(
    websocket: WebSocket,
    mission_id: uuid.UUID,
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> None:
    _user, close_code = await _authorize(session, mission_id, token)

    if close_code is not None:
        await websocket.close(code=close_code)
        return

    broker = websocket.app.state.broker
    if not broker.enabled:
        await websocket.close(code=_UNAVAILABLE)
        return

    await websocket.accept()

    async def _send_ready() -> None:
        await websocket.send_json({"type": "connection.ready", "mission_id": str(mission_id)})

    try:
        async for event in broker.subscribe(mission_id, on_ready=_send_ready):
            await websocket.send_json(event)
    except Exception:  # noqa: BLE001 - client disconnects surface here; just stop
        return
