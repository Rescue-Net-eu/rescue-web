# rescue-net.eu API

FastAPI backend for the rescue-net.eu volunteer coordination platform.
See [`docs/project-manual.md`](../../docs/project-manual.md) for the full
specification (data model in §13, API design in §14).

## Status

Implemented (manual §27 priorities 1–6):

- **Authentication** — bearer JWT verification (`get_current_user`), `/me`, and a
  non-production `/auth/dev/login` for end-to-end testing before Authentik/OIDC.
- **Role-based access control** — `require_roles` enforcing the §6 role matrix.
- **Incident CRUD** — create / get / list / patch / close, RBAC-guarded.
- **Geospatial responder search** — `GET /incidents/{id}/candidates` finds nearby
  verified responders within the incident radius (PostGIS `ST_DWithin`), ordered by
  distance, filterable by skills.
- **Alerting** (§9) — `POST /incidents/{id}/alerts` selects candidates and sends alerts
  with priority-based expiry (§9.4), a reason requirement for high-priority incidents
  (§22.1) and a per-dispatcher rate limit (§9.5); responders see `GET /alerts` and answer
  via `POST /alerts/{id}/respond` (expired alerts read as `timeout` and cannot be answered).
- **Mission creation** (§5.3) — `POST /incidents/{id}/create-mission` assigns a Team Lead
  and enrolls responders who accepted; `GET /missions`, `GET /missions/{id}` (membership-
  scoped) and `PATCH /missions/{id}` for status transitions (§8).
- **Mission room** (§5.4, §14.2) — join/leave with explicit live-location consent (§16.2),
  chat (`/missions/{id}/messages`), live location ingestion + latest-per-member
  (`/missions/{id}/locations`, `/locations/live`), and closure (`/missions/{id}/close`,
  which stops all live sharing and locks the mission). Realtime events fan out over
  **Redis pub/sub** to a WebSocket at `ws://…/ws/missions/{id}?token=…`.
- **Mission tasks** (§5.4, §13.10) — `GET/POST /missions/{id}/tasks` and
  `PATCH /missions/{id}/tasks/{task_id}`. Staff or the Team Lead create/assign and edit
  tasks; an assigned responder may update only their own task's status (and `completed_at`
  is set automatically on `done`). Emits `mission.task_created` / `mission.task_updated`.
- **Audit logging** — every high-risk action is recorded; `GET /admin/audit-logs`.
- **GDPR retention** (§16.2, §16.4) — see below.

### Data retention & GDPR (two-tier)

GDPR governs *personal* data; anonymized data is out of scope (Recital 26). We use this to
satisfy "delete on schedule **and** keep ~10 years of history":

- **Personal tier** — purged/anonymized on schedule (configurable in `Settings`): raw
  location samples 30 days after mission close, participation free-text after 3 years, audit
  logs after 3 years (extend for legal hold).
- **Historical tier** — `mission_archive`, an **anonymized aggregate** per mission (counts,
  durations, skills-used, region, no user ids / coordinates / free text). Non-personal, so it
  is GDPR-exempt and retained ~10 years. Every purge is **archive-first**, so nothing of
  reporting value is lost. Long-term reports run *only* on this table; per-volunteer
  ("volunteer activity", §23.2) reporting is personal data and is limited to the 3-year window.
- **Erasure** (§16.4 "Delete my account") — tombstones the user (clears email/name/phone,
  blocks login), deletes their raw locations and responder geo, blanks their chat text, but
  keeps `mission_members` / `alerts` / `audit_logs` (now referencing a non-identifying UUID)
  for the operational and audit trail — "anonymize where deletion conflicts with audit
  requirements" (§16.2).

Run sweeps via the CLI (cron / k8s CronJob — the manual's "retention cleanup job"):

```bash
python -m app run                # all sweeps
python -m app purge-locations    # individual sweeps: archive, anonymize, purge-audit
python -m app erase-user --id <uuid>
```

…or on demand as a platform admin: `POST /admin/retention/run`,
`POST /admin/users/{id}/erase`.

Mobile is the next increment.

## Local development

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the API (boots without a database; /readyz reports dependencies).
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the interactive OpenAPI UI.

### Trying the API

```bash
# Dev login returns a bearer token (non-production only).
TOKEN=$(curl -s localhost:8000/auth/dev/login \
  -H 'content-type: application/json' \
  -d '{"email":"dispatcher@example.org","role":"dispatcher"}' | jq -r .access_token)

curl -s localhost:8000/me -H "authorization: Bearer $TOKEN"
curl -s localhost:8000/incidents -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"Stranded vehicle","latitude":45.0,"longitude":25.0,"radius_m":50000}'
```

### Tests and lint

```bash
ruff check .
# Integration tests need PostGIS; they skip automatically if no DB is reachable.
# Point TEST_DATABASE_URL (or DATABASE_URL) at a PostGIS instance to run them:
DATABASE_URL=postgresql+asyncpg://rescuenet:rescuenet@localhost:5432/rescuenet_test pytest -q
```

## Database migrations

Models live in `app/models.py` (manual §13). Migrations use Alembic:

```bash
# Requires a running PostgreSQL+PostGIS and DATABASE_URL set.
alembic upgrade head                      # apply migrations
alembic revision --autogenerate -m "..."  # generate from model changes
```

The initial migration enables the PostGIS extension.

## Configuration

Copy `.env.example` to `.env`. All variables are optional in the skeleton
so the service boots without infrastructure.
