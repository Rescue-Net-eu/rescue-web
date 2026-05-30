"""Integration tests for incident CRUD, RBAC, geospatial search and audit."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login


async def _user_id(client: AsyncClient, token: str) -> str:
    resp = await client.get("/me", headers=auth_header(token))
    return resp.json()["id"]


async def _make_responder(
    client: AsyncClient,
    admin_token: str,
    *,
    email: str,
    lat: float,
    lng: float,
    verified: bool,
    skills: list[str] | None = None,
) -> str:
    token = await dev_login(client, email, "responder")
    user_id = await _user_id(client, token)
    resp = await client.post(
        "/responders",
        headers=auth_header(admin_token),
        json={
            "user_id": user_id,
            "latitude": lat,
            "longitude": lng,
            "verification_status": "verified" if verified else "unverified",
            "skills": skills or [],
        },
    )
    assert resp.status_code == 201, resp.text
    return user_id


# --- CRUD + RBAC ----------------------------------------------------------


async def test_create_get_close_incident(client: AsyncClient) -> None:
    token = await dev_login(client, "d@example.org", "dispatcher")
    create = await client.post(
        "/incidents",
        headers=auth_header(token),
        json={
            "title": "Stranded vehicle",
            "priority": "high",
            "latitude": 45.0,
            "longitude": 25.0,
            "radius_m": 50000,
        },
    )
    assert create.status_code == 201, create.text
    incident = create.json()
    assert incident["status"] == "open"
    assert incident["latitude"] == 45.0 and incident["longitude"] == 25.0
    incident_id = incident["id"]

    got = await client.get(f"/incidents/{incident_id}", headers=auth_header(token))
    assert got.status_code == 200
    assert got.json()["title"] == "Stranded vehicle"

    closed = await client.post(f"/incidents/{incident_id}/close", headers=auth_header(token))
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    again = await client.post(f"/incidents/{incident_id}/close", headers=auth_header(token))
    assert again.status_code == 409


async def test_patch_incident(client: AsyncClient) -> None:
    token = await dev_login(client, "d2@example.org", "dispatcher")
    create = await client.post(
        "/incidents", headers=auth_header(token), json={"title": "Initial"}
    )
    incident_id = create.json()["id"]
    patch = await client.patch(
        f"/incidents/{incident_id}",
        headers=auth_header(token),
        json={"title": "Updated", "status": "alerting"},
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Updated"
    assert patch.json()["status"] == "alerting"


async def test_responder_cannot_create_incident(client: AsyncClient) -> None:
    token = await dev_login(client, "r@example.org", "responder")
    resp = await client.post(
        "/incidents", headers=auth_header(token), json={"title": "Nope"}
    )
    assert resp.status_code == 403


async def test_list_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/incidents")).status_code == 401


async def test_incomplete_coordinates_rejected(client: AsyncClient) -> None:
    token = await dev_login(client, "d3@example.org", "dispatcher")
    resp = await client.post(
        "/incidents",
        headers=auth_header(token),
        json={"title": "Bad", "latitude": 45.0},
    )
    assert resp.status_code == 422


# --- Geospatial candidate search -----------------------------------------


async def test_responder_candidate_search(client: AsyncClient) -> None:
    admin = await dev_login(client, "admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "disp@example.org", "dispatcher")

    near = await _make_responder(
        client, admin, email="near@example.org", lat=45.05, lng=25.0,
        verified=True, skills=["first_aid"],
    )
    far_but_in = await _make_responder(
        client, admin, email="far@example.org", lat=45.2, lng=25.0,
        verified=True, skills=["4x4_driving"],
    )
    # Outside the 50 km radius.
    await _make_responder(
        client, admin, email="outside@example.org", lat=46.0, lng=25.0, verified=True,
    )
    # Inside radius but not verified.
    await _make_responder(
        client, admin, email="unverified@example.org", lat=45.01, lng=25.0, verified=False,
    )

    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Search", "latitude": 45.0, "longitude": 25.0, "radius_m": 50000},
        )
    ).json()["id"]

    resp = await client.get(
        f"/incidents/{incident_id}/candidates", headers=auth_header(dispatcher)
    )
    assert resp.status_code == 200
    candidates = resp.json()
    ids = [c["user_id"] for c in candidates]
    # Verified + within radius, nearest first; unverified and out-of-radius excluded.
    assert ids == [near, far_but_in]
    assert candidates[0]["distance_m"] < candidates[1]["distance_m"]

    # Skill filter narrows to the first-aid responder only.
    filtered = await client.get(
        f"/incidents/{incident_id}/candidates",
        headers=auth_header(dispatcher),
        params={"skills": ["first_aid"]},
    )
    assert [c["user_id"] for c in filtered.json()] == [near]

    # Including unverified responders adds the in-radius unverified one.
    unverified_included = await client.get(
        f"/incidents/{incident_id}/candidates",
        headers=auth_header(dispatcher),
        params={"verified_only": "false"},
    )
    assert len(unverified_included.json()) == 3


async def test_candidates_requires_search_area(client: AsyncClient) -> None:
    token = await dev_login(client, "d4@example.org", "dispatcher")
    incident_id = (
        await client.post("/incidents", headers=auth_header(token), json={"title": "No area"})
    ).json()["id"]
    resp = await client.get(f"/incidents/{incident_id}/candidates", headers=auth_header(token))
    assert resp.status_code == 422


# --- Audit ----------------------------------------------------------------


async def test_actions_are_audited(client: AsyncClient) -> None:
    admin = await dev_login(client, "auditor-admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d5@example.org", "dispatcher")
    await client.post(
        "/incidents", headers=auth_header(dispatcher), json={"title": "Audited"}
    )

    logs = await client.get("/admin/audit-logs", headers=auth_header(admin))
    assert logs.status_code == 200
    actions = {entry["action"] for entry in logs.json()}
    assert "incident.create" in actions


async def test_audit_logs_forbidden_for_responder(client: AsyncClient) -> None:
    token = await dev_login(client, "r2@example.org", "responder")
    resp = await client.get("/admin/audit-logs", headers=auth_header(token))
    assert resp.status_code == 403
