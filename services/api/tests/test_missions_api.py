"""Integration tests for mission creation and management (requires a database)."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login, make_responder, user_id


async def _alerted_incident(client: AsyncClient, dispatcher: str, admin: str) -> tuple[str, str]:
    """Create an incident, alert one responder; return (incident_id, responder_token)."""
    responder_token = await dev_login(client, "resp@example.org", "responder")
    await make_responder(client, admin, email="resp@example.org", lat=45.02, lng=25.0)
    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Mission", "latitude": 45.0, "longitude": 25.0, "radius_m": 50000},
        )
    ).json()["id"]
    send = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    alert_id = send.json()["alert_ids"][0]
    await client.post(
        f"/alerts/{alert_id}/respond",
        headers=auth_header(responder_token),
        json={"response": "yes"},
    )
    return incident_id, responder_token


async def test_create_mission_adds_accepted_and_lead(client: AsyncClient) -> None:
    admin = await dev_login(client, "ma@example.org", "platform_admin")
    dispatcher = await dev_login(client, "md@example.org", "dispatcher")
    lead_token = await dev_login(client, "lead@example.org", "team_lead")
    lead_id = await user_id(client, lead_token)

    incident_id, responder_token = await _alerted_incident(client, dispatcher, admin)
    responder_id = await user_id(client, responder_token)

    create = await client.post(
        f"/incidents/{incident_id}/create-mission",
        headers=auth_header(dispatcher),
        json={"lead_user_id": lead_id},
    )
    assert create.status_code == 201, create.text
    mission = create.json()
    assert mission["status"] == "pending"
    assert mission["lead_user_id"] == lead_id

    roles = {m["user_id"]: m["role_in_mission"] for m in mission["members"]}
    assert roles.get(lead_id) == "team_lead"
    assert roles.get(responder_id) == "responder"

    # Incident transitioned to mission_created.
    incident = await client.get(f"/incidents/{incident_id}", headers=auth_header(dispatcher))
    assert incident.json()["status"] == "mission_created"


async def test_mission_visibility(client: AsyncClient) -> None:
    admin = await dev_login(client, "va@example.org", "platform_admin")
    dispatcher = await dev_login(client, "vd@example.org", "dispatcher")
    incident_id, responder_token = await _alerted_incident(client, dispatcher, admin)
    mission_id = (
        await client.post(
            f"/incidents/{incident_id}/create-mission", headers=auth_header(dispatcher), json={}
        )
    ).json()["id"]

    # Member responder can see it; a non-member responder cannot.
    member_view = await client.get(f"/missions/{mission_id}", headers=auth_header(responder_token))
    assert member_view.status_code == 200

    outsider = await dev_login(client, "outsider@example.org", "responder")
    outsider_view = await client.get(f"/missions/{mission_id}", headers=auth_header(outsider))
    assert outsider_view.status_code == 403

    # Listing reflects membership.
    assert len((await client.get("/missions", headers=auth_header(responder_token))).json()) == 1
    assert (await client.get("/missions", headers=auth_header(outsider))).json() == []
    assert len((await client.get("/missions", headers=auth_header(dispatcher))).json()) == 1


async def test_mission_status_update_permissions(client: AsyncClient) -> None:
    admin = await dev_login(client, "sa@example.org", "platform_admin")
    dispatcher = await dev_login(client, "sd@example.org", "dispatcher")
    lead_token = await dev_login(client, "slead@example.org", "team_lead")
    lead_id = await user_id(client, lead_token)
    incident_id, _ = await _alerted_incident(client, dispatcher, admin)
    mission_id = (
        await client.post(
            f"/incidents/{incident_id}/create-mission",
            headers=auth_header(dispatcher),
            json={"lead_user_id": lead_id},
        )
    ).json()["id"]

    # Team lead can advance the mission; started_at gets set on activation.
    activate = await client.patch(
        f"/missions/{mission_id}", headers=auth_header(lead_token), json={"status": "active"}
    )
    assert activate.status_code == 200
    assert activate.json()["status"] == "active"
    assert activate.json()["started_at"] is not None

    # An unrelated responder cannot.
    outsider = await dev_login(client, "sout@example.org", "responder")
    denied = await client.patch(
        f"/missions/{mission_id}", headers=auth_header(outsider), json={"status": "closed"}
    )
    assert denied.status_code == 403


async def test_create_mission_requires_dispatcher(client: AsyncClient) -> None:
    dispatcher = await dev_login(client, "cd@example.org", "dispatcher")
    responder = await dev_login(client, "cr@example.org", "responder")
    incident_id = (
        await client.post("/incidents", headers=auth_header(dispatcher), json={"title": "X"})
    ).json()["id"]
    resp = await client.post(
        f"/incidents/{incident_id}/create-mission", headers=auth_header(responder), json={}
    )
    assert resp.status_code == 403
