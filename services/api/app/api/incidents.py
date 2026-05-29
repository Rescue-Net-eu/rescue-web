"""Incident endpoints (manual section 14.1).

Skeleton stubs: list endpoints return empty collections and mutating
endpoints advertise the contract but are not yet implemented. Business
logic (geospatial responder search, alerting, mission creation) lands in
the dedicated feature work described in manual section 27.
"""

from __future__ import annotations

from fastapi import APIRouter, status

router = APIRouter(prefix="/incidents", tags=["incidents"])

_NOT_IMPLEMENTED = "Not implemented in the skeleton; see manual section 27."


@router.get("")
async def list_incidents() -> list[dict]:
    return []


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_incident() -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.get("/{incident_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_incident(incident_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{incident_id}/alerts", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def trigger_alerts(incident_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{incident_id}/create-mission", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_mission(incident_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}


@router.post("/{incident_id}/close", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def close_incident(incident_id: str) -> dict[str, str]:
    return {"detail": _NOT_IMPLEMENTED}
