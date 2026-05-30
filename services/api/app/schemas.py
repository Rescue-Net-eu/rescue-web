"""Request/response schemas (manual sections 13 and 14)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enums import (
    AlertResponse,
    AlertType,
    IncidentStatus,
    MissionStatus,
    UserRole,
    VerificationStatus,
)

Priority = Literal["low", "medium", "high"]


# --- Auth -----------------------------------------------------------------


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DevLoginRequest(BaseModel):
    """Developer-only login: upserts a user and returns a token."""

    email: EmailStr
    role: UserRole = UserRole.RESPONDER
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    status: str


# --- Incidents ------------------------------------------------------------


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, max_length=64)
    priority: Priority = "medium"
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_m: int | None = Field(default=None, ge=0, le=500_000)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, max_length=64)
    priority: Priority | None = None
    status: IncidentStatus | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_m: int | None = Field(default=None, ge=0, le=500_000)


class IncidentOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    type: str | None
    priority: str
    status: IncidentStatus
    created_by: uuid.UUID
    latitude: float | None
    longitude: float | None
    radius_m: int | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


# --- Responders -----------------------------------------------------------


class ResponderCreate(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    display_name: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    home_region: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    skills: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    availability_status: str = "unknown"


class ResponderOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None
    display_name: str | None
    verification_status: VerificationStatus
    home_region: str | None
    latitude: float | None
    longitude: float | None
    skills: list[str]
    equipment: list[str]
    availability_status: str


class ResponderCandidate(ResponderOut):
    """A responder matched by the alert candidate search, with distance."""

    distance_m: float


# --- Alerts ---------------------------------------------------------------


class AlertSendRequest(BaseModel):
    alert_type: AlertType = AlertType.AVAILABILITY_REQUEST
    # Required for high-priority incidents (manual section 22.1).
    reason: str | None = Field(default=None, max_length=500)
    verified_only: bool = True
    skills: list[str] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=500)


class AlertSendResult(BaseModel):
    incident_id: uuid.UUID
    alert_type: AlertType
    expiry_at: datetime
    recipients: int
    alert_ids: list[uuid.UUID]


class AlertOut(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    user_id: uuid.UUID
    alert_type: AlertType
    status: str
    response: AlertResponse | None
    sent_at: datetime
    responded_at: datetime | None
    expiry_at: datetime | None


class AlertRespondRequest(BaseModel):
    # Timeout is system-assigned, not a user response.
    response: Literal["yes", "no", "need_details"]


# --- Missions -------------------------------------------------------------


class MissionCreateRequest(BaseModel):
    lead_user_id: uuid.UUID | None = None
    # Add responders who accepted an alert for this incident as mission members.
    auto_add_accepted: bool = True


class MissionMemberOut(BaseModel):
    user_id: uuid.UUID
    role_in_mission: str
    joined_at: datetime
    left_at: datetime | None
    live_location_enabled: bool


class MissionOut(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    lead_user_id: uuid.UUID | None
    status: MissionStatus
    started_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    members: list[MissionMemberOut]


class MissionUpdate(BaseModel):
    status: MissionStatus
