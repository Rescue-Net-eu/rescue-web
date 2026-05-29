# rescue-net.eu API

FastAPI backend for the rescue-net.eu volunteer coordination platform.
See [`docs/project-manual.md`](../../docs/project-manual.md) for the full
specification (data model in §13, API design in §14).

## Status

MVP **skeleton**. Health/readiness probes and the route surface are in
place; feature business logic is implemented incrementally following the
development priorities in manual §27.

## Local development

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the API (boots without a database; /readyz reports dependencies).
uvicorn app.main:app --reload

# Run tests and lint.
pytest
ruff check .
```

Visit http://localhost:8000/docs for the interactive OpenAPI UI.

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
