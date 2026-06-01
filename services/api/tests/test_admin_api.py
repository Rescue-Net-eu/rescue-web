"""Integration tests for admin user/org management & responder verification."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from ._util import auth_header, dev_login, make_responder, user_id


async def test_list_users_requires_admin(client: AsyncClient) -> None:
    responder = await dev_login(client, "au-resp@example.org", "responder")
    assert (await client.get("/admin/users", headers=auth_header(responder))).status_code == 403

    admin = await dev_login(client, "au-admin@example.org", "platform_admin")
    resp = await client.get("/admin/users", headers=auth_header(admin))
    assert resp.status_code == 200
    assert any(u["email"] == "au-admin@example.org" for u in resp.json())


async def test_update_user_role_and_status(client: AsyncClient) -> None:
    admin = await dev_login(client, "au-admin2@example.org", "platform_admin")
    victim = await dev_login(client, "au-victim@example.org", "responder")
    victim_id = await user_id(client, victim)

    promote = await client.patch(
        f"/admin/users/{victim_id}", headers=auth_header(admin), json={"role": "team_lead"}
    )
    assert promote.status_code == 200
    assert promote.json()["role"] == "team_lead"

    suspend = await client.patch(
        f"/admin/users/{victim_id}", headers=auth_header(admin), json={"status": "suspended"}
    )
    assert suspend.status_code == 200
    assert suspend.json()["status"] == "suspended"

    # Suspended user can no longer authenticate.
    me = await client.get("/me", headers=auth_header(victim))
    assert me.status_code == 403


async def test_update_user_not_found(client: AsyncClient) -> None:
    admin = await dev_login(client, "au-admin3@example.org", "platform_admin")
    resp = await client.patch(
        f"/admin/users/{uuid.uuid4()}", headers=auth_header(admin), json={"role": "dispatcher"}
    )
    assert resp.status_code == 404


async def test_organization_create_and_list(client: AsyncClient) -> None:
    admin = await dev_login(client, "au-admin4@example.org", "platform_admin")
    create = await client.post(
        "/admin/organizations",
        headers=auth_header(admin),
        json={"name": "Rescue 4x4 RO", "country": "RO", "region": "Cluj"},
    )
    assert create.status_code == 201, create.text
    assert create.json()["name"] == "Rescue 4x4 RO"

    listed = await client.get("/admin/organizations", headers=auth_header(admin))
    assert listed.status_code == 200
    assert any(o["country"] == "RO" for o in listed.json())


async def test_org_create_requires_platform_admin(client: AsyncClient) -> None:
    org_admin = await dev_login(client, "au-orgadmin@example.org", "org_admin")
    resp = await client.post(
        "/admin/organizations", headers=auth_header(org_admin), json={"name": "X"}
    )
    assert resp.status_code == 403


async def test_responder_verification(client: AsyncClient) -> None:
    admin = await dev_login(client, "au-admin5@example.org", "platform_admin")
    # make_responder creates a verified responder; create an unverified one here.
    rtoken = await dev_login(client, "au-newresp@example.org", "responder")
    rid_user = await user_id(client, rtoken)
    created = await client.post(
        "/responders",
        headers=auth_header(admin),
        json={"user_id": rid_user, "verification_status": "pending"},
    )
    responder_id = created.json()["id"]
    assert created.json()["verification_status"] == "pending"

    verify = await client.patch(
        f"/responders/{responder_id}/verification",
        headers=auth_header(admin),
        json={"verification_status": "verified"},
    )
    assert verify.status_code == 200
    assert verify.json()["verification_status"] == "verified"


async def test_verification_requires_admin(client: AsyncClient) -> None:
    admin = await dev_login(client, "au-admin6@example.org", "platform_admin")
    responder_user = await make_responder(
        client, admin, email="au-vresp@example.org", lat=45.0, lng=25.0
    )
    # Find the responder id.
    responders = (await client.get("/responders", headers=auth_header(admin))).json()
    responder_id = next(r["id"] for r in responders if r["user_id"] == responder_user)

    plain = await dev_login(client, "au-plain@example.org", "responder")
    resp = await client.patch(
        f"/responders/{responder_id}/verification",
        headers=auth_header(plain),
        json={"verification_status": "suspended"},
    )
    assert resp.status_code == 403
