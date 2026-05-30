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
- **Audit logging** — every high-risk action is recorded; `GET /admin/audit-logs`.

The mission room (WebSocket), chat, tasks, live location and mission closure are the
next increments.

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
