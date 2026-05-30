"""Domain enumerations from the project manual.

Roles (section 6), incident lifecycle (section 7), mission lifecycle
(section 8) and alert responses (section 9.3).
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    DISPATCHER = "dispatcher"
    TEAM_LEAD = "team_lead"
    RESPONDER = "responder"
    AUDITOR = "auditor"


class IncidentStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    ALERTING = "alerting"
    MISSION_CREATED = "mission_created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MissionStatus(StrEnum):
    PENDING = "pending"
    MOBILIZING = "mobilizing"
    ACTIVE = "active"
    WAITING = "waiting"
    RETURNING = "returning"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class AlertType(StrEnum):
    INFORMATIONAL = "informational"
    AVAILABILITY_REQUEST = "availability_request"
    MISSION_INVITATION = "mission_invitation"
    URGENT_SUPPORT = "urgent_support"


class AlertResponse(StrEnum):
    YES = "yes"
    NO = "no"
    NEED_DETAILS = "need_details"
    TIMEOUT = "timeout"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"
