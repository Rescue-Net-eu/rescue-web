"""Integration tests for the alerting flow (requires a database)."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login, execute_sql, make_responder


async def _incident_with_area(client: AsyncClient, token: str, *, priority: str = "medium") -> str:
    resp = await client.post(
        "/incidents",
        headers=auth_header(token),
        json={
            "title": "Alerting incident",
            "priority": priority,
            "latitude": 45.0,
            "longitude": 25.0,
            "radius_m": 50000,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_send_alerts_and_respond(client: AsyncClient) -> None:
    admin = await dev_login(client, "a@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d@example.org", "dispatcher")
    responder_token = await dev_login(client, "near@example.org", "responder")
    responder_id = await make_responder(
        client, admin, email="near@example.org", lat=45.05, lng=25.0
    )

    incident_id = await _incident_with_area(client, dispatcher)
    send = await client.post(
        f"/incidents/{incident_id}/alerts",
        headers=auth_header(dispatcher),
        json={"alert_type": "availability_request"},
    )
    assert send.status_code == 201, send.text
    assert send.json()["recipients"] == 1

    # Incident moved to "alerting".
    incident = await client.get(f"/incidents/{incident_id}", headers=auth_header(dispatcher))
    assert incident.json()["status"] == "alerting"

    # The responder sees the alert in their inbox.
    inbox = await client.get("/alerts", headers=auth_header(responder_token))
    assert inbox.status_code == 200
    alerts = inbox.json()
    assert len(alerts) == 1
    assert alerts[0]["status"] == "sent"
    alert_id = alerts[0]["id"]
    assert alerts[0]["user_id"] == responder_id

    # And can accept it.
    respond = await client.post(
        f"/alerts/{alert_id}/respond",
        headers=auth_header(responder_token),
        json={"response": "yes"},
    )
    assert respond.status_code == 200
    assert respond.json()["response"] == "yes"
    assert respond.json()["status"] == "responded"


async def test_resend_skips_already_alerted(client: AsyncClient) -> None:
    admin = await dev_login(client, "a2@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d2@example.org", "dispatcher")
    await make_responder(client, admin, email="r2@example.org", lat=45.01, lng=25.0)
    incident_id = await _incident_with_area(client, dispatcher)

    first = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    assert first.json()["recipients"] == 1
    second = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    assert second.json()["recipients"] == 0


async def test_high_priority_requires_reason(client: AsyncClient) -> None:
    admin = await dev_login(client, "a3@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d3@example.org", "dispatcher")
    await make_responder(client, admin, email="r3@example.org", lat=45.01, lng=25.0)
    incident_id = await _incident_with_area(client, dispatcher, priority="high")

    no_reason = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    assert no_reason.status_code == 422

    with_reason = await client.post(
        f"/incidents/{incident_id}/alerts",
        headers=auth_header(dispatcher),
        json={"reason": "Person trapped, urgent"},
    )
    assert with_reason.status_code == 201


async def test_expired_alert_cannot_be_answered(client: AsyncClient) -> None:
    admin = await dev_login(client, "a4@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d4@example.org", "dispatcher")
    responder_token = await dev_login(client, "r4@example.org", "responder")
    await make_responder(client, admin, email="r4@example.org", lat=45.01, lng=25.0)
    incident_id = await _incident_with_area(client, dispatcher)

    send = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    alert_id = send.json()["alert_ids"][0]

    # Backdate expiry to simulate timeout.
    execute_sql(
        "UPDATE alerts SET expiry_at = now() - interval '1 hour' WHERE id = CAST(:id AS uuid)",
        id=alert_id,
    )

    inbox = await client.get("/alerts", headers=auth_header(responder_token))
    assert inbox.json()[0]["status"] == "timeout"

    respond = await client.post(
        f"/alerts/{alert_id}/respond",
        headers=auth_header(responder_token),
        json={"response": "yes"},
    )
    assert respond.status_code == 409


async def test_only_recipient_can_respond(client: AsyncClient) -> None:
    admin = await dev_login(client, "a5@example.org", "platform_admin")
    dispatcher = await dev_login(client, "d5@example.org", "dispatcher")
    await make_responder(client, admin, email="r5@example.org", lat=45.01, lng=25.0)
    other = await dev_login(client, "other@example.org", "responder")
    incident_id = await _incident_with_area(client, dispatcher)
    send = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    alert_id = send.json()["alert_ids"][0]

    resp = await client.post(
        f"/alerts/{alert_id}/respond", headers=auth_header(other), json={"response": "no"}
    )
    assert resp.status_code == 403


async def test_responder_cannot_send_alerts(client: AsyncClient) -> None:
    dispatcher = await dev_login(client, "d6@example.org", "dispatcher")
    responder = await dev_login(client, "r6@example.org", "responder")
    incident_id = await _incident_with_area(client, dispatcher)
    resp = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(responder), json={}
    )
    assert resp.status_code == 403
