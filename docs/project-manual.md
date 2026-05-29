# rescue-net.eu Project Manual

- **Version:** 0.1
- **Status:** MVP planning manual
- **Project type:** European volunteer rescue alerting and mission coordination platform
- **Primary objective:** Real-time coordination of verified volunteers during emergency-support missions

---

## 1. Executive Summary

rescue-net.eu is a European-scale emergency-support and volunteer coordination platform inspired by community rescue models such as "Există un erou în fiecare dintre voi" and "Rescue 4x4 România".

The platform is designed to connect dispatchers, coordinators, team leads, and verified volunteers during incidents where rapid local support is needed. Its core value is not to replace official emergency services, but to provide a structured, auditable, and privacy-aware digital coordination layer for volunteer-based interventions.

The MVP focuses on four main capabilities:

- Real-time incident creation and alerting.
- Geolocation-based volunteer discovery and notification.
- Mission tracking with responder status and live location.
- Structured mission closure, reporting, and audit history.

The platform must be built with European legal, privacy, and operational realities in mind. It should support GDPR principles from the start, including consent-based location sharing, data minimization, role-based access, clear retention rules, and traceable administrative actions.

The MVP should launch in one country first, using a limited group of verified volunteers and dispatchers, then scale gradually to additional regions and countries.

## 2. Project Vision

The long-term vision of rescue-net.eu is to create a trusted volunteer response network across Europe.

The platform should allow local communities, rescue groups, 4x4 volunteers, logistics volunteers, medical support volunteers, drone operators, translators, and other specialized responders to participate in coordinated support operations.

The platform should eventually support:

- Local volunteer organizations.
- Regional coordination hubs.
- Cross-border assistance.
- Integration with local authorities where legally and operationally possible.
- Disaster response scenarios.
- Severe weather support.
- Search and support missions.
- Road accessibility support.
- Vulnerable-person support.
- Logistics and supply delivery.
- Evacuation assistance when formally authorized.
- Technical support such as drones, mapping, radio, and communications.

The project should be treated as a safety-critical coordination platform. The first version does not need to be complex, but it must be reliable, controlled, secure, and auditable.

## 3. Important Positioning

rescue-net.eu must not present itself as a replacement for official emergency numbers such as 112.

The correct positioning is:

- A volunteer coordination platform.
- A mission tracking system.
- A support layer for community-based intervention.
- A tool that can interoperate with authorities if a formal relationship exists.
- A platform that helps organize available people and resources during incidents.

The platform must not encourage users to bypass police, ambulance, fire brigade, mountain rescue, civil protection, or any other official emergency authority.

Recommended public disclaimer:

> "rescue-net.eu is a volunteer coordination platform. In life-threatening emergencies, users must contact the official emergency number first. The platform is intended to support structured volunteer response and coordination where appropriate."

## 4. MVP Scope

The MVP should be deliberately narrow. The goal is to validate the operational model, not to build every possible feature.

### 4.1 MVP Users

The MVP includes three core user types:

- Dispatcher
- Team Lead
- Responder

Optional administrative roles:

- Organization Admin
- Platform Admin
- Auditor

### 4.2 MVP Features

The first MVP should include:

- User registration and identity verification workflow.
- Role-based access control.
- Incident creation by dispatchers.
- Incident location using point and radius.
- Optional polygon-based incident area.
- Alerting of nearby responders.
- Responder availability response: Yes, No, Timeout.
- Mission creation from an incident.
- Team Lead assignment.
- Mission member list.
- Live location sharing during active mission only.
- Basic mission chat.
- Mission status tracking.
- Task assignment.
- Mission closure.
- Mission report.
- Audit log.

### 4.3 Out of Scope for MVP

These should not be part of the first production MVP unless there is a strong operational requirement:

- Automatic public emergency intake.
- Public panic button.
- AI dispatching.
- Complex authority integration.
- Payment system.
- Volunteer ranking system.
- Public social media sharing.
- Drone fleet management.
- Full offline mesh communication.
- Cross-border legal workflows.
- Medical triage logic.
- Automatic emergency service escalation.

These can be added later after the core operational model is proven.

## 5. Core Use Cases

### 5.1 Create an Incident

A dispatcher receives information about a situation requiring volunteer support.

The dispatcher enters:

- Incident title.
- Incident type.
- Description.
- Location.
- Radius or polygon.
- Priority.
- Required skills.
- Required resources.
- Safety notes.
- Contact point.
- Internal notes.

The system creates an incident and identifies nearby eligible responders.

### 5.2 Alert Nearby Responders

The platform identifies responders who match:

- Geographic proximity.
- Availability.
- Verification status.
- Required skills.
- Resource type.
- Organization scope.
- Legal or operational eligibility.

Responders receive a push notification.

Responder options:

- Accept.
- Decline.
- Ask for more information.
- Ignore, resulting in timeout.

The dispatcher sees live response statistics.

### 5.3 Start a Mission

When enough responders accept, the dispatcher creates a mission from the incident.

A Team Lead is assigned.

The mission room becomes active.

The mission room includes:

- Map.
- Responders.
- Live location.
- Chat.
- Tasks.
- Incident details.
- Safety notes.
- Status timeline.

### 5.4 Track Mission Progress

During the mission, responders can:

- Share live location.
- Send status updates.
- Send chat messages.
- Receive task assignments.
- Mark task progress.
- Report blocked access or unsafe conditions.
- Leave the mission if needed.

The Team Lead can:

- Assign tasks.
- Update mission status.
- Request additional responders.
- Report risk escalation.
- Close operational tasks.

The dispatcher can:

- Monitor all mission activity.
- Send instructions.
- Escalate.
- Close or suspend the mission.

### 5.5 Close Mission

Mission closure requires:

- Final status.
- Summary.
- Participants.
- Timeline.
- Issues encountered.
- Safety notes.
- Follow-up actions.
- Optional attachments.

After closure:

- Live location sharing stops.
- Mission becomes read-only except for authorized edits.
- Audit log remains available.
- Location retention policy starts.

## 6. Roles and Permissions

### 6.1 Platform Admin

Responsible for platform-wide configuration.

Permissions:

- Manage organizations.
- Manage roles.
- Manage system settings.
- View audit logs.
- Configure integrations.
- Suspend users.
- Manage retention settings.
- Review security events.

### 6.2 Organization Admin

Responsible for one volunteer organization or region.

Permissions:

- Manage organization members.
- Approve responders.
- Assign responder skills.
- View organization missions.
- Manage local dispatchers and team leads.
- Review local audit logs.

### 6.3 Dispatcher

Responsible for incident intake and mission creation.

Permissions:

- Create incidents.
- Edit active incidents.
- Trigger responder alerts.
- Create missions.
- Assign Team Leads.
- Monitor missions.
- Close missions.
- Add mission notes.

### 6.4 Team Lead

Responsible for field coordination.

Permissions:

- View assigned missions.
- Manage mission members.
- Assign tasks.
- Update mission status.
- Send operational messages.
- Request more responders.
- Submit field report.

### 6.5 Responder

Volunteer participating in missions.

Permissions:

- View assigned alerts.
- Accept or decline alerts.
- Join missions.
- Share live location during active missions.
- Send mission chat messages.
- Update own status.
- Complete assigned tasks.
- Leave mission.

### 6.6 Auditor

Responsible for compliance and review.

Permissions:

- View closed incidents.
- View closed missions.
- View audit logs.
- Export reports.
- Cannot modify operational data.

## 7. Incident Lifecycle

The incident lifecycle should be simple and strict.

Recommended statuses:

- Draft
- Open
- Alerting
- Mission Created
- Active
- Suspended
- Closed
- Cancelled

### 7.1 Draft

Incident is being prepared but not yet visible to responders.

### 7.2 Open

Incident is created and visible to dispatchers and authorized coordinators.

### 7.3 Alerting

Responder notifications are being sent.

### 7.4 Mission Created

A mission has been created from the incident, but it may not yet be active.

### 7.5 Active

Mission is operational. Responders may share location and receive tasking.

### 7.6 Suspended

Mission is paused due to safety, weather, authority request, or operational uncertainty.

### 7.7 Closed

Mission is completed. No live tracking remains active.

### 7.8 Cancelled

Incident or mission was cancelled before completion.

## 8. Mission Lifecycle

Recommended mission statuses:

- Pending
- Mobilizing
- Active
- Waiting
- Returning
- Closed
- Cancelled

### 8.1 Pending

Mission is created but not yet started.

### 8.2 Mobilizing

Responders are moving toward the mission area.

### 8.3 Active

Field activity is ongoing.

### 8.4 Waiting

Mission is temporarily waiting for instructions, authority clearance, weather change, or additional information.

### 8.5 Returning

Responders are leaving the mission area.

### 8.6 Closed

Mission is complete.

### 8.7 Cancelled

Mission was stopped before execution.

## 9. Alerting Model

The alerting system is one of the most important parts of the platform.

### 9.1 Alert Candidate Selection

The platform should select responders based on:

- Distance from incident.
- Availability status.
- Verification status.
- Required skills.
- Vehicle type.
- Equipment type.
- Organization or region.
- Current mission participation.
- Safety restrictions.

### 9.2 Alert Types

MVP alert types:

- Informational alert.
- Availability request.
- Mission invitation.
- Urgent support request.

### 9.3 Alert Responses

Responder response options:

- Yes, available.
- No, unavailable.
- Need more details.
- Timeout.

### 9.4 Alert Expiry

Each alert should have an expiry time.

Recommended default:

- Low priority: 30 minutes.
- Medium priority: 15 minutes.
- High priority: 5 minutes.

Expired alerts should no longer allow mission joining unless manually reactivated by a dispatcher.

### 9.5 Anti-Abuse Controls

The alerting system must prevent misuse.

Controls:

- Only authorized dispatchers can alert responders.
- Rate limits per dispatcher.
- Alert reason required.
- Audit log for every alert campaign.
- Responder opt-out and quiet hours.
- Emergency override only for authorized roles.
- Alert preview before sending.

## 10. Volunteer Profile

Each responder should have a structured profile.

Recommended fields:

- Full name.
- Display name.
- Email.
- Phone number.
- Region.
- Verification status.
- Organization membership.
- Skills.
- Certifications.
- Vehicle type.
- Equipment.
- Availability preferences.
- Emergency contact, optional.
- Consent status.
- Device notification token.

### 10.1 Skills

Example responder skills:

- 4x4 driving.
- First aid.
- Logistics.
- Drone operation.
- Radio communication.
- Translation.
- Mapping.
- Mechanical support.
- Medical support, verified only.
- Search support.
- Evacuation support, authorized only.
- Animal rescue.
- IT and communications.

### 10.2 Equipment

Example equipment:

- 4x4 vehicle.
- Winch.
- Tow rope.
- Chains.
- Snow shovel.
- Generator.
- First aid kit.
- Radio.
- Drone.
- Thermal camera.
- GPS device.
- Power bank.
- Trailer.
- Boat.
- Chainsaw, if legally allowed and trained.

Equipment should be self-declared initially, then verified later if needed.

## 11. Technical Architecture

The MVP architecture should be modular, simple, and production-ready.

Recommended stack:

- Mobile app: Flutter.
- Web console: Next.js.
- API backend: FastAPI.
- Database: PostgreSQL with PostGIS.
- Cache and realtime broker: Redis.
- Authentication: Authentik using OIDC.
- Push notifications: Firebase Cloud Messaging.
- Reverse proxy: Traefik.
- DNS and edge security: Cloudflare.
- Object storage: S3-compatible EU storage.
- Infrastructure: Hetzner Cloud EU or equivalent EU provider.
- Observability: Grafana, Loki, Prometheus, Alertmanager or managed monitoring.

### 11.1 High-Level Architecture

```
Responder Mobile App
        |
        | HTTPS, WebSocket, Push Notifications
        |
Cloudflare DNS, WAF, DDoS Protection
        |
Traefik Reverse Proxy
        |
        +--------------------+
        |                    |
Next.js Web Console      FastAPI Backend
                             |
          +------------------+------------------+
          |                  |                  |
     PostgreSQL + PostGIS   Redis           S3 Storage
          |
     Backups and Retention
```

### 11.2 Component Responsibilities

**Mobile App**

Responsible for:

- Responder login.
- Alert display.
- Availability response.
- Mission participation.
- Location sharing during active missions.
- Mission chat.
- Task updates.
- Consent handling.

**Web Console**

Responsible for:

- Dispatcher interface.
- Incident creation.
- Mission monitoring.
- Map view.
- Team Lead assignment.
- Responder status.
- Mission closure.
- Reports.

**API Backend**

Responsible for:

- Business logic.
- Authentication validation.
- Authorization enforcement.
- Incident management.
- Mission management.
- Alert candidate selection.
- Location ingestion.
- Chat handling.
- Audit logging.
- Data retention jobs.

**Database**

Responsible for:

- Persistent operational data.
- Geospatial queries.
- Mission history.
- Audit records.
- Consent records.

**Redis**

Responsible for:

- WebSocket fan-out.
- Short-lived session state.
- Alert queues.
- Rate limiting.
- Temporary mission state.

**Object Storage**

Responsible for:

- Attachments.
- Photos.
- Reports.
- Export files.

## 12. Repository Structure

Recommended monorepo structure:

```
rescue-net/
  apps/
    web/
      Next.js dispatcher console
    mobile/
      Flutter responder app

  services/
    api/
      FastAPI backend

  packages/
    shared/
      OpenAPI schema
      shared DTOs
      generated clients

  infra/
    terraform/
      cloud infrastructure
    ansible/
      optional node bootstrap
    docker/
      production compose files

  docs/
    architecture/
    operations/
    security/
    compliance/
    user-manuals/

  .github/
    workflows/
      CI/CD pipelines
```

## 13. Data Model

The MVP database should include the following entities.

### 13.1 Users

Stores account identity.

Fields:

- id
- email
- phone
- full_name
- role
- status
- created_at
- updated_at
- last_login_at

### 13.2 Organizations

Stores volunteer groups or regional entities.

Fields:

- id
- name
- country
- region
- status
- created_at

### 13.3 Responders

Stores volunteer-specific information.

Fields:

- id
- user_id
- organization_id
- display_name
- verification_status
- home_region
- home_location
- skills
- equipment
- availability_status
- created_at

### 13.4 Incidents

Stores incident records.

Fields:

- id
- title
- description
- type
- priority
- status
- created_by
- center_point
- radius_m
- polygon_area
- created_at
- updated_at
- closed_at

### 13.5 Alerts

Stores alert campaigns and individual responder responses.

Fields:

- id
- incident_id
- user_id
- alert_type
- status
- sent_at
- responded_at
- response
- expiry_at

### 13.6 Missions

Stores mission records.

Fields:

- id
- incident_id
- lead_user_id
- status
- started_at
- closed_at
- closure_summary
- created_at

### 13.7 Mission Members

Stores mission participation.

Fields:

- id
- mission_id
- user_id
- role_in_mission
- joined_at
- left_at
- live_location_enabled

### 13.8 Locations

Stores mission location samples.

Fields:

- id
- mission_id
- user_id
- timestamp
- point
- accuracy_m
- speed
- heading

### 13.9 Chat Messages

Stores mission chat.

Fields:

- id
- mission_id
- user_id
- message
- created_at
- edited_at
- deleted_at

### 13.10 Tasks

Stores mission tasks.

Fields:

- id
- mission_id
- assigned_to
- created_by
- title
- description
- status
- priority
- due_at
- completed_at

### 13.11 Audit Logs

Stores security and operational audit records.

Fields:

- id
- actor_user_id
- action
- entity_type
- entity_id
- timestamp
- ip_address
- user_agent
- metadata

### 13.12 Consent Records

Stores privacy consent history.

Fields:

- id
- user_id
- consent_type
- consent_version
- accepted_at
- revoked_at
- ip_address

## 14. API Design

The API should be REST-first for simplicity, with WebSockets for realtime mission updates.

### 14.1 Core REST Endpoints

**Authentication:**

```
GET    /healthz
GET    /readyz
GET    /me
POST   /auth/mobile/start
POST   /auth/mobile/verify
```

**Incidents:**

```
GET    /incidents
POST   /incidents
GET    /incidents/{incident_id}
PATCH  /incidents/{incident_id}
POST   /incidents/{incident_id}/alerts
POST   /incidents/{incident_id}/create-mission
POST   /incidents/{incident_id}/close
```

**Alerts:**

```
GET    /alerts
GET    /alerts/{alert_id}
POST   /alerts/{alert_id}/respond
```

**Missions:**

```
GET    /missions
GET    /missions/{mission_id}
PATCH  /missions/{mission_id}
POST   /missions/{mission_id}/join
POST   /missions/{mission_id}/leave
POST   /missions/{mission_id}/close
```

**Mission chat:**

```
GET    /missions/{mission_id}/messages
POST   /missions/{mission_id}/messages
```

**Locations:**

```
POST   /missions/{mission_id}/locations
GET    /missions/{mission_id}/locations/live
```

**Tasks:**

```
GET    /missions/{mission_id}/tasks
POST   /missions/{mission_id}/tasks
PATCH  /missions/{mission_id}/tasks/{task_id}
```

**Admin:**

```
GET    /admin/users
PATCH  /admin/users/{user_id}
GET    /admin/audit-logs
GET    /admin/organizations
POST   /admin/organizations
```

### 14.2 WebSocket Endpoints

```
/ws/missions/{mission_id}
```

WebSocket event types:

- mission.member_joined
- mission.member_left
- mission.location_updated
- mission.chat_message
- mission.task_created
- mission.task_updated
- mission.status_changed
- mission.closed
- alert.response_updated

## 15. Security Requirements

Security must be included from the first version.

### 15.1 Identity and Access Management

Requirements:

- OIDC-based login for web console.
- Strong role-based access control.
- Short-lived access tokens.
- Refresh tokens for web sessions.
- Mobile token renewal.
- MFA required for dispatchers and admins.
- Admin accounts separated from responder accounts where possible.

### 15.2 Authorization

Every API endpoint must enforce:

- User identity.
- User role.
- Organization scope.
- Mission membership where applicable.
- Entity ownership or assignment.

High-risk endpoints require strict authorization:

- Alert sending.
- Mission closing.
- User verification.
- Role changes.
- Data export.
- Audit log access.

### 15.3 Audit Logging

Audit logs must capture:

- Login events.
- Failed login attempts.
- Incident creation.
- Incident updates.
- Alert sending.
- Alert response.
- Mission creation.
- Mission status changes.
- User role changes.
- Permission changes.
- Data exports.
- Admin actions.
- Consent changes.

### 15.4 API Security

Required controls:

- HTTPS only.
- CORS restricted to known domains.
- Rate limiting.
- Request validation.
- Strong input validation.
- Output encoding.
- File upload validation.
- Maximum file size limits.
- Malware scanning for attachments if possible.
- No direct object access without authorization.
- Protection against IDOR issues.
- Security headers on web console.

### 15.5 Infrastructure Security

Required controls:

- Cloudflare in front of public endpoints.
- Firewall allowing HTTP and HTTPS only from Cloudflare IP ranges.
- SSH restricted to admin IPs or VPN.
- No password SSH login.
- Automatic security updates.
- Container images scanned before deployment.
- Secrets outside source code.
- Backups encrypted.
- Database access restricted by IP and credentials.
- Principle of least privilege.

## 16. GDPR and Privacy Requirements

The platform processes personal data and location data. Location data is sensitive in practice, even when not formally classified as special category data.

### 16.1 Privacy Principles

The system must follow:

- Data minimization.
- Purpose limitation.
- Consent for live location sharing.
- Clear retention periods.
- Access control.
- Auditability.
- Right to access.
- Right to deletion where legally possible.
- Right to correction.
- Security by design.
- Privacy by design.

### 16.2 Location Data Rules

Mandatory rules:

- No continuous background tracking outside active missions.
- Live location sharing must be explicit.
- Location sharing must stop automatically when the mission is closed or the responder leaves.
- Responder must be able to disable location sharing.
- Dispatchers must see only mission-relevant locations.
- Closed mission location history should have limited retention.
- Location samples should be downsampled or deleted after operational need expires.

Recommended retention:

- Live mission location: active mission only.
- Raw location samples: 30 days after mission closure.
- Mission participation metadata: 3 years.
- Audit logs: 3 years or based on legal/compliance requirement.
- Deleted user account: anonymize where deletion conflicts with operational audit requirements.

### 16.3 Consent Types

The platform should track consent for:

- Terms of use.
- Privacy policy.
- Live location during missions.
- Push notifications.
- Volunteer participation rules.
- Data processing by organization.

### 16.4 Data Subject Requests

The platform should support:

- Export my data.
- Correct my data.
- Delete my account.
- Revoke consent.
- Disable location sharing.
- Disable notifications.

### 16.5 Data Processing Agreements

Before production use, the project should prepare:

- Privacy policy.
- Terms of use.
- Volunteer participation agreement.
- Dispatcher acceptable use policy.
- Data processing agreement with hosting providers.
- Data processing agreement with organizations using the system.
- Incident liability disclaimer.
- Retention policy.

> This manual is not legal advice. A qualified EU privacy lawyer should review the final policy documents before public launch.

## 17. Production Environment

The first production environment should be small but properly controlled.

### 17.1 Recommended Domains

Recommended DNS structure:

```
rescue-net.eu
www.rescue-net.eu
console.rescue-net.eu
api.rescue-net.eu
auth.rescue-net.eu
status.rescue-net.eu
docs.rescue-net.eu
```

### 17.2 Environment Separation

Use separate environments:

```
dev.rescue-net.eu
staging.rescue-net.eu
console.rescue-net.eu
api.rescue-net.eu
```

Minimum environments:

- Development, local.
- Staging, cloud.
- Production, cloud.

### 17.3 Hosting

Recommended MVP hosting:

- Cloudflare for DNS, WAF, TLS edge, DDoS protection.
- Hetzner Cloud EU for application nodes.
- Managed PostgreSQL with PostGIS in EU.
- Redis container for MVP or managed Redis in EU.
- S3-compatible EU object storage.

### 17.4 Production Services

Minimum production services:

- Traefik reverse proxy.
- API backend.
- Web console.
- Redis.
- Promtail.
- Node exporter.
- Backup job.
- Retention cleanup job.

Managed services:

- PostgreSQL.
- Object storage.
- Email provider.
- Push notification provider.

## 18. Deployment Manual

### 18.1 Prepare Accounts

Create or configure:

- Cloudflare account.
- Hetzner Cloud project.
- Managed PostgreSQL provider.
- S3-compatible storage provider.
- Firebase project.
- Authentik instance.
- GitHub organization or repository.

### 18.2 Prepare DNS

Create records:

```
console.rescue-net.eu  -> application ingress
api.rescue-net.eu      -> application ingress
auth.rescue-net.eu     -> Authentik
status.rescue-net.eu   -> monitoring/status page
```

Use Cloudflare proxy for public web endpoints.

### 18.3 Provision Compute

Create one production VM first.

Recommended minimum:

- 2 vCPU.
- 4 GB RAM.
- 40 GB disk.
- EU region.
- Ubuntu LTS or Debian stable.
- Private networking enabled.

For higher availability:

- Two app VMs.
- Load balancer.
- Managed Redis.
- Managed database.

### 18.4 Secure the Server

Required steps:

1. Create a non-root deployment user.
2. Disable SSH password login.
3. Enable SSH key authentication only.
4. Install Docker and Docker Compose.
5. Install fail2ban.
6. Configure firewall.
7. Allow SSH only from trusted IPs.
8. Allow 80 and 443 only from Cloudflare IP ranges.
9. Enable automatic security updates.
10. Configure log rotation.

### 18.5 Deploy Reverse Proxy

Use Traefik.

Responsibilities:

- TLS termination.
- Routing.
- HTTP to HTTPS redirect.
- Security headers.
- Service discovery.
- Certificate renewal.

### 18.6 Deploy API

The API should be deployed as a Docker container.

Required environment variables:

```
APP_ENV=production
DATABASE_URL=
REDIS_URL=
JWT_ISSUER=
JWT_AUDIENCE=
OIDC_JWKS_URL=
ALLOWED_ORIGINS=https://console.rescue-net.eu
S3_ENDPOINT=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
FCM_PROJECT_ID=
FCM_CREDENTIALS_FILE=
```

### 18.7 Deploy Web Console

The web console should be deployed as a Docker container.

Required environment variables:

```
NEXT_PUBLIC_API_URL=https://api.rescue-net.eu
NEXTAUTH_URL=https://console.rescue-net.eu
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_ISSUER=
```

### 18.8 Run Database Migrations

Before starting the production API:

1. Connect to PostgreSQL.
2. Enable PostGIS.
3. Run migrations.
4. Create indexes.
5. Verify health endpoint.
6. Verify readiness endpoint.

Required indexes:

- Incident center geospatial index.
- Incident polygon geospatial index.
- Mission status index.
- Location mission timestamp index.
- Audit log timestamp index.
- Alert user status index.

### 18.9 Configure Backups

Minimum backup policy:

- Daily database backup.
- 7 daily backups retained.
- 4 weekly backups retained.
- Monthly backup retained for 12 months if cost allows.
- Object storage versioning enabled.
- Backup restore tested monthly.

### 18.10 Configure Monitoring

Minimum monitoring:

- API uptime.
- Web console uptime.
- Database availability.
- Disk usage.
- CPU usage.
- Memory usage.
- Container restarts.
- Error rate.
- Failed login rate.
- Alert sending failures.
- Push notification failures.

Recommended alert channels:

- Email.
- Telegram or Signal group.
- Pager-style alerting later.

## 19. CI/CD Requirements

The project should use GitHub Actions.

### 19.1 API Pipeline

Steps:

- Checkout.
- Install dependencies.
- Run linting.
- Run unit tests.
- Run security scan.
- Build Docker image.
- Scan Docker image.
- Push image to GitHub Container Registry.
- Deploy to staging.
- Run smoke tests.
- Manual approval for production.
- Deploy to production.

### 19.2 Web Pipeline

Steps:

- Checkout.
- Install dependencies.
- Run linting.
- Run type checking.
- Run tests.
- Build Next.js app.
- Build Docker image.
- Scan Docker image.
- Push image.
- Deploy.

### 19.3 Mobile Pipeline

Steps:

- Run Flutter analyze.
- Run tests.
- Build Android APK for internal testing.
- Build iOS later when Apple Developer account is available.
- Distribute through internal testing channel.

## 20. Operational Procedures

### 20.1 Incident Creation Procedure

Dispatcher steps:

1. Login to console.
2. Create new incident.
3. Enter location.
4. Select radius or polygon.
5. Select priority.
6. Select required responder skills.
7. Add safety notes.
8. Preview affected responders.
9. Send alert.
10. Monitor responses.
11. Create mission if enough responders are available.

### 20.2 Mission Monitoring Procedure

Dispatcher or Team Lead steps:

1. Open active mission.
2. Confirm assigned Team Lead.
3. Confirm participating responders.
4. Monitor live map.
5. Monitor chat.
6. Assign tasks.
7. Update mission status.
8. Escalate if needed.
9. Close mission when complete.
10. Submit final report.

### 20.3 Responder Procedure

Responder steps:

1. Receive alert.
2. Read mission summary and safety notes.
3. Accept or decline.
4. If accepted, join mission room.
5. Enable location sharing only for the mission.
6. Follow Team Lead instructions.
7. Update task status.
8. Report safety issues.
9. Leave mission when released.
10. Confirm mission closure.

### 20.4 Mission Closure Procedure

Required closure fields:

- Final status.
- Closure summary.
- Participating responders.
- Tasks completed.
- Issues encountered.
- Safety incidents.
- External authority contact, if applicable.
- Attachments, if applicable.
- Follow-up required.

## 21. Reliability Requirements

MVP reliability targets:

- 99.5 percent monthly availability.
- API p95 response time under 300 ms for normal read operations.
- Alert creation under 5 seconds for small responder groups.
- WebSocket reconnection supported.
- Mobile polling fallback for missed push notifications.
- Database backups tested.
- Basic disaster recovery documented.

### 21.1 Failure Handling

The platform must handle:

- Push notification failure.
- WebSocket disconnect.
- Database temporary unavailability.
- Redis restart.
- API container crash.
- Mobile app offline state.
- Duplicate alert response.
- Duplicate location sample.
- Mission close while responder is still active.

### 21.2 Mobile Offline Behavior

Mobile app should support:

- Display last received mission details.
- Queue status updates briefly.
- Retry failed requests.
- Stop location sharing if mission token expires.
- Show clear connection status.

## 22. Abuse and Safety Controls

The platform must prevent misuse.

### 22.1 False Incidents

Controls:

- Only verified dispatchers can create alerts.
- Dispatchers must belong to an organization.
- All alert campaigns are audited.
- High-priority alerts require reason.
- Suspicious dispatcher activity triggers admin review.

### 22.2 Volunteer Safety

Controls:

- Safety notes required for high-risk missions.
- Responders must explicitly accept participation.
- Responders can leave a mission.
- Location sharing can be disabled.
- Team Lead can mark unsafe conditions.
- Mission can be suspended.
- No responder should be sent into dangerous areas without appropriate authorization.

### 22.3 Data Abuse

Controls:

- Role-based access.
- Audit logging.
- Access review.
- Export logging.
- Sensitive endpoint rate limits.
- Admin MFA.
- Data access minimization.

## 23. Reporting

The MVP should provide basic reports.

### 23.1 Mission Report

Includes:

- Incident title.
- Incident type.
- Location.
- Timeline.
- Dispatcher.
- Team Lead.
- Responders.
- Tasks.
- Status changes.
- Chat summary, optional.
- Attachments.
- Closure notes.

### 23.2 Volunteer Activity Report

Includes:

- Missions joined.
- Missions declined.
- Total active time.
- Skills used.
- Region activity.

> This should not become a public leaderboard in the MVP. Incentive systems can create bad behavior if introduced too early.

### 23.3 Audit Report

Includes:

- Admin actions.
- Dispatcher actions.
- Alert history.
- Role changes.
- Data exports.
- Failed access attempts.

## 24. Roadmap

### 24.1 MVP, Phase 1

Core:

- Auth.
- Roles.
- Incidents.
- Alerts.
- Mission room.
- Live location.
- Chat.
- Closure report.
- Audit log.
- Basic admin.

### 24.2 Phase 2

Add:

- Organization management.
- Advanced responder verification.
- Skills and equipment validation.
- Better mobile offline mode.
- Richer maps.
- Multi-region support.
- Better notification templates.
- Public status page.

### 24.3 Phase 3

Add:

- Authority integration.
- Multi-country support.
- Language localization.
- Advanced reporting.
- Volunteer training records.
- Resource inventory.
- Asset tracking.
- Drone support.
- Radio integration.
- External GIS layers.

### 24.4 Phase 4

Add:

- Federation between organizations.
- Cross-border response support.
- Advanced routing.
- AI-assisted summarization.
- Predictive responder availability.
- Disaster scenario planning.
- Integration with civil protection systems where legally possible.

## 25. MVP Acceptance Criteria

The MVP is considered ready for controlled production pilot when:

- Dispatcher can create an incident.
- System can find nearby responders.
- Responders receive alerts.
- Responders can accept or decline.
- Dispatcher can create mission.
- Team Lead can manage mission.
- Mobile app can share live location only during active mission.
- Web console shows responder locations.
- Mission chat works.
- Mission can be closed.
- Audit log records critical actions.
- GDPR consent is recorded.
- Backups are configured.
- Monitoring is active.
- Production deployment is repeatable.
- Basic security testing has been completed.

## 26. Initial Production Checklist

Before pilot launch:

1. Domain configured.
2. TLS working.
3. Cloudflare WAF enabled.
4. App server hardened.
5. Database encrypted and backed up.
6. PostGIS enabled.
7. Authentik configured.
8. MFA enabled for admins and dispatchers.
9. API deployed.
10. Web console deployed.
11. Mobile test build installed.
12. FCM push tested.
13. Alert flow tested.
14. Mission flow tested.
15. Location sharing tested.
16. Mission closure tested.
17. Audit logging tested.
18. Backup restore tested.
19. Privacy policy prepared.
20. Terms of use prepared.
21. Volunteer agreement prepared.
22. Incident disclaimer prepared.
23. Pilot users trained.
24. Emergency escalation rules documented.
25. Support contact available.

## 27. Development Priorities

The first implementation should follow this order:

1. Repository skeleton.
2. Database schema.
3. Authentication.
4. Role-based access.
5. Incident CRUD.
6. Geospatial responder search.
7. Alerting.
8. Mobile alert response.
9. Mission creation.
10. Mission room.
11. Live location.
12. Chat.
13. Mission closure.
14. Audit logging.
15. Monitoring.
16. Deployment automation.
17. Security hardening.
18. Pilot testing.

## 28. Key Risks

### 28.1 Legal Risk

**Risk:** The platform may be interpreted as an unofficial emergency service.

**Mitigation:**

- Clear disclaimers.
- No public emergency replacement claims.
- Formal partnerships where possible.
- Dispatcher-only incident creation in MVP.
- Legal review before public launch.

### 28.2 Privacy Risk

**Risk:** Improper handling of live location data.

**Mitigation:**

- Explicit consent.
- Mission-only tracking.
- Automatic stop.
- Short retention.
- Access control.
- Audit logs.

### 28.3 Operational Risk

**Risk:** Untrained volunteers may expose themselves or others to danger.

**Mitigation:**

- Verification process.
- Safety notes.
- Team Lead control.
- Mission suspension.
- Training records in later phases.
- Clear participation rules.

### 28.4 Technical Risk

**Risk:** Push notifications may be delayed or missed.

**Mitigation:**

- Push plus app polling.
- Alert expiry.
- Delivery status tracking.
- Retry logic.
- SMS fallback in later phase.

### 28.5 Trust Risk

**Risk:** Bad actors may attempt to join as responders.

**Mitigation:**

- Verification.
- Organization approval.
- Role restrictions.
- Audit logs.
- Suspension process.

## 29. Recommended First Pilot

The first pilot should be small.

Recommended pilot structure:

- One country.
- One region.
- One organization.
- 2 to 3 dispatchers.
- 2 team leads.
- 20 to 50 responders.
- 2 test missions.
- 1 simulated operational mission.
- No public self-dispatching.
- No automatic authority integration.

Pilot objectives:

- Validate alert delivery.
- Validate responder response flow.
- Validate live tracking.
- Validate dispatcher usability.
- Validate privacy expectations.
- Validate mission closure.
- Identify operational gaps.

## 30. Final Notes

rescue-net.eu should be built as an operational coordination system first, not as a social app.

The MVP must prove:

- Can the right people be alerted quickly?
- Can they accept or decline safely?
- Can coordinators see who is available?
- Can field activity be tracked without privacy abuse?
- Can missions be closed and audited?
- Can the system operate reliably under real pressure?

The correct first goal is not scale. The correct first goal is controlled, trustworthy, repeatable operation with a small verified responder group.

Once that works, the platform can expand into additional organizations, regions, countries, and integrations.
