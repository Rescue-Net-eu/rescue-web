# rescue-net.eu

European volunteer rescue alerting and mission coordination platform.

> rescue-net.eu is a **volunteer coordination platform**. In life-threatening
> emergencies, contact your official emergency number (e.g. 112) first. It is
> not a replacement for official emergency services.

This repository is the **monorepo** for the platform. It currently contains
the MVP **skeleton** — all apps are scaffolded with working health endpoints,
a reference docker-compose stack and CI; feature logic lands incrementally
following the development priorities in the [project manual](docs/project-manual.md) (§27).

## Repository layout

```
apps/
  web/        Next.js dispatcher console
  mobile/     Flutter responder app
services/
  api/        FastAPI backend (PostGIS data model, health probes, route surface)
packages/
  shared/     OpenAPI contract / shared types
infra/
  docker/     reference docker-compose stack
  terraform/  cloud infrastructure (placeholder)
  ansible/    node bootstrap & hardening (placeholder)
docs/         project manual and other documentation
.github/
  workflows/  CI for api, web and mobile
index.html    legacy static landing page (served as-is)
```

## Quick start

Run the full stack with Docker:

```bash
docker compose -f infra/docker/docker-compose.yml up --build
# API  -> http://localhost:8000/healthz   (docs at /docs)
# Web  -> http://localhost:3000
```

Or run a single app — see each app's README:

- [`services/api`](services/api/README.md) — FastAPI backend
- [`apps/web`](apps/web/README.md) — Next.js console
- [`apps/mobile`](apps/mobile/README.md) — Flutter responder app

## Documentation

- [Project Manual](docs/project-manual.md) — the rescue-net.eu MVP planning
  manual covering vision, scope, roles, data model, API design, security,
  GDPR, deployment, and roadmap.
