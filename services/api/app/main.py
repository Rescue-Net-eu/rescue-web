"""rescue-net.eu FastAPI application entrypoint.

Wires the application together: CORS (restricted to known origins per
manual section 15.4), the health probes and the feature routers. Auth,
RBAC, incident CRUD and geospatial responder search are implemented;
alerting and mission features are landing incrementally (manual section 27).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import admin, alerts, auth, health, incidents, missions, responders
from .config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="rescue-net.eu API",
        version=__version__,
        description=(
            "Volunteer rescue alerting and mission coordination platform. "
            "This is the MVP skeleton — see docs/project-manual.md."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(incidents.router)
    app.include_router(responders.router)
    app.include_router(alerts.router)
    app.include_router(missions.router)
    app.include_router(admin.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "version": __version__, "status": "ok"}

    return app


app = create_app()
