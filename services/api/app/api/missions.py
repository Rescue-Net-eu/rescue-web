"""Mission endpoints (manual section 14.1).

Skeleton stubs — see :mod:`app.api.incidents` for the convention.
"""

from __future__ import annotations

from fastapi import APIRouter, status

router = APIRouter(prefix="/missions", tags=["missions"])

_NOT_IMPLEMENTED = "Not implemented in the skeleton; see manual section 27."


@router.get("")
async def list_missions() -> list[dict]:
    return []


@router.get("/{mission_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_mission(mission_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{mission_id}/join", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def join_mission(mission_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{mission_id}/leave", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def leave_mission(mission_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{mission_id}/close", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def close_mission(mission_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.get("/{mission_id}/messages")
async def list_messages(mission_id: str) -> list[dict]:
    return []


@router.get("/{mission_id}/tasks")
async def list_tasks(mission_id: str) -> list[dict]:
    return []
