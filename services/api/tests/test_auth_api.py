"""Integration tests for authentication and `/me` (requires a database)."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login


async def test_dev_login_and_me(client: AsyncClient) -> None:
    token = await dev_login(client, "dispatcher@example.org", "dispatcher")
    resp = await client.get("/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "dispatcher@example.org"
    assert body["role"] == "dispatcher"


async def test_me_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get("/me")
    assert resp.status_code == 401


async def test_invalid_token_rejected(client: AsyncClient) -> None:
    resp = await client.get("/me", headers=auth_header("not-a-real-token"))
    assert resp.status_code == 401


async def test_dev_login_is_idempotent_and_updates_role(client: AsyncClient) -> None:
    await dev_login(client, "person@example.org", "responder")
    token = await dev_login(client, "person@example.org", "team_lead")
    resp = await client.get("/me", headers=auth_header(token))
    assert resp.json()["role"] == "team_lead"
