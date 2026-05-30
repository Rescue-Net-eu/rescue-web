"""Alert endpoints (manual sections 9.3, 9.4, 14.1).

Responders see their own alerts and respond Yes / No / Need details. An
alert past its expiry reads as a timeout and can no longer be answered
(manual section 9.4).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..alerting import effective_status, is_expired
from ..audit import record_audit
from ..db import get_session
from ..deps import get_current_user
from ..enums import AlertResponse, AlertType, UserRole
from ..models import Alert, User
from ..schemas import AlertOut, AlertRespondRequest

router = APIRouter(prefix="/alerts", tags=["alerts"])

_STAFF_ROLES = {UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN, UserRole.DISPATCHER, UserRole.AUDITOR}


def _alert_out(alert: Alert) -> AlertOut:
    return AlertOut(
        id=alert.id,
        incident_id=alert.incident_id,
        user_id=alert.user_id,
        alert_type=AlertType(alert.alert_type),
        status=effective_status(alert),
        response=AlertResponse(alert.response) if alert.response else None,
        sent_at=alert.sent_at,
        responded_at=alert.responded_at,
        expiry_at=alert.expiry_at,
    )


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AlertOut]:
    """List the current user's alerts (their responder inbox)."""
    stmt = (
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.sent_at.desc())
        .limit(limit)
    )
    alerts = (await session.execute(stmt)).scalars().all()
    return [_alert_out(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AlertOut:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.user_id != user.id and UserRole(user.role) not in _STAFF_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert")
    return _alert_out(alert)


@router.post("/{alert_id}/respond", response_model=AlertOut)
async def respond_to_alert(
    alert_id: uuid.UUID,
    payload: AlertRespondRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AlertOut:
    """Record the recipient's response (manual section 9.3)."""
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can respond"
        )
    if is_expired(alert) and alert.responded_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Alert has expired"
        )

    alert.response = AlertResponse(payload.response)
    alert.responded_at = datetime.now(UTC)
    alert.status = "responded"

    await record_audit(
        session,
        action="alert.respond",
        actor_user_id=user.id,
        entity_type="alert",
        entity_id=alert.id,
        request=request,
        metadata={"response": payload.response},
    )
    await session.commit()
    await session.refresh(alert)
    return _alert_out(alert)
