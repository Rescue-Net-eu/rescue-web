"""Test helpers."""

from __future__ import annotations

from httpx import AsyncClient


async def dev_login(client: AsyncClient, email: str, role: str) -> str:
    """Log in via the dev endpoint and return a bearer token."""
    resp = await client.post("/auth/dev/login", json={"email": email, "role": role})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
