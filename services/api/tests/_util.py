"""Test helpers."""

from __future__ import annotations

import os

from httpx import AsyncClient
from sqlalchemy import create_engine, text

_TEST_DATABASE_URL = (
    os.environ.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql+asyncpg://rescuenet:rescuenet@127.0.0.1:5432/rescuenet_test"
)


async def dev_login(client: AsyncClient, email: str, role: str) -> str:
    """Log in via the dev endpoint and return a bearer token."""
    resp = await client.post("/auth/dev/login", json={"email": email, "role": role})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def user_id(client: AsyncClient, token: str) -> str:
    resp = await client.get("/me", headers=auth_header(token))
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def make_responder(
    client: AsyncClient,
    admin_token: str,
    *,
    email: str,
    lat: float,
    lng: float,
    verified: bool = True,
    skills: list[str] | None = None,
) -> str:
    """Create a user + responder profile; return the user id."""
    token = await dev_login(client, email, "responder")
    uid = await user_id(client, token)
    resp = await client.post(
        "/responders",
        headers=auth_header(admin_token),
        json={
            "user_id": uid,
            "latitude": lat,
            "longitude": lng,
            "verification_status": "verified" if verified else "unverified",
            "skills": skills or [],
        },
    )
    assert resp.status_code == 201, resp.text
    return uid


def execute_sql(sql: str, **params: object) -> None:
    """Run a statement against the test database (for test setup only)."""
    engine = create_engine(_TEST_DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    with engine.begin() as conn:
        conn.execute(text(sql), params)
    engine.dispose()
