"""Integration tests for reporting endpoints (manual section 23)."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login, make_responder


async def _mission_with_activity(client: AsyncClient) -> dict:
    admin = await dev_login(client, "rp-admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "rp-disp@example.org", "dispatcher")
    responder_token = await dev_login(client, "rp-resp@example.org", "responder")
    responder_id = await make_responder(
        client, admin, email="rp-resp@example.org", lat=45.02, lng=25.0, skills=["first_aid"]
    )
    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Report incident", "type": "flood", "latitude": 45.0,
                  "longitude": 25.0, "radius_m": 50000},
        )
    ).json()["id"]
    send = await client.post(
        f"/incidents/{incident_id}/alerts", headers=auth_header(dispatcher), json={}
    )
    await client.post(
        f"/alerts/{send.json()['alert_ids'][0]}/respond",
        headers=auth_header(responder_token),
        json={"response": "yes"},
    )
    mission_id = (
        await client.post(
            f"/incidents/{incident_id}/create-mission",
            headers=auth_header(dispatcher),
            json={},
        )
    ).json()["id"]
    await client.post(
        f"/missions/{mission_id}/messages",
        headers=auth_header(responder_token),
        json={"message": "en route"},
    )
    await client.post(
        f"/missions/{mission_id}/tasks",
        headers=auth_header(dispatcher),
        json={"title": "Survey", "assigned_to": responder_id},
    )
    return {
        "admin": admin,
        "dispatcher": dispatcher,
        "responder_token": responder_token,
        "responder_id": responder_id,
        "mission_id": mission_id,
    }


async def test_mission_report(client: AsyncClient) -> None:
    ctx = await _mission_with_activity(client)
    resp = await client.get(
        f"/reports/missions/{ctx['mission_id']}", headers=auth_header(ctx["dispatcher"])
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["incident_title"] == "Report incident"
    assert body["incident_type"] == "flood"
    assert ctx["responder_id"] in body["responders"]
    assert body["task_total"] == 1
    assert body["chat_message_count"] == 1


async def test_mission_report_forbidden_for_outsider(client: AsyncClient) -> None:
    ctx = await _mission_with_activity(client)
    outsider = await dev_login(client, "rp-out@example.org", "responder")
    resp = await client.get(
        f"/reports/missions/{ctx['mission_id']}", headers=auth_header(outsider)
    )
    assert resp.status_code == 403


async def test_volunteer_activity_self_and_staff(client: AsyncClient) -> None:
    ctx = await _mission_with_activity(client)
    # Staff can view anyone.
    staff_view = await client.get(
        f"/reports/volunteers/{ctx['responder_id']}", headers=auth_header(ctx["dispatcher"])
    )
    assert staff_view.status_code == 200
    body = staff_view.json()
    assert body["alerts_received"] == 1
    assert body["alerts_accepted"] == 1
    assert body["missions_joined"] == 1
    assert "first_aid" in body["skills"]

    # The volunteer can view their own.
    self_view = await client.get(
        f"/reports/volunteers/{ctx['responder_id']}", headers=auth_header(ctx["responder_token"])
    )
    assert self_view.status_code == 200


async def test_volunteer_activity_forbidden_for_other_responder(client: AsyncClient) -> None:
    ctx = await _mission_with_activity(client)
    other = await dev_login(client, "rp-other@example.org", "responder")
    resp = await client.get(
        f"/reports/volunteers/{ctx['responder_id']}", headers=auth_header(other)
    )
    assert resp.status_code == 403


async def test_historical_summary_from_archive(client: AsyncClient) -> None:
    ctx = await _mission_with_activity(client)
    # Close the mission and run retention so it lands in the archive.
    await client.post(
        f"/missions/{ctx['mission_id']}/close", headers=auth_header(ctx["dispatcher"]), json={}
    )
    await client.post("/admin/retention/run", headers=auth_header(ctx["admin"]))

    resp = await client.get("/reports/historical", headers=auth_header(ctx["dispatcher"]))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 1
    assert sum(r["missions"] for r in rows) >= 1


async def test_historical_summary_requires_staff(client: AsyncClient) -> None:
    responder = await dev_login(client, "rp-resp2@example.org", "responder")
    resp = await client.get("/reports/historical", headers=auth_header(responder))
    assert resp.status_code == 403
