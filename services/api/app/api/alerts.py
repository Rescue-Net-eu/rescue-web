"""Alert endpoints (manual section 14.1).

Skeleton stubs — see :mod:`app.api.incidents` for the convention.
"""

from __future__ import annotations

from fastapi import APIRouter, status

router = APIRouter(prefix="/alerts", tags=["alerts"])

_NOT_IMPLEMENTED = "Not implemented in the skeleton; see manual section 27."


@router.get("")
async def list_alerts() -> list[dict]:
    return []


@router.get("/{alert_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_alert(alert_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{alert_id}/respond", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def respond_to_alert(alert_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}
