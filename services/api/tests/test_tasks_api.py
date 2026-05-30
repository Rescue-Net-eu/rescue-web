"""Integration tests for mission tasks (manual sections 5.4, 13.10)."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login, make_responder, user_id


async def _mission_with_member(client: AsyncClient) -> dict:
    """Incident → alert → accept → mission with a Team Lead and one responder."""
    admin = await dev_login(client, "tk-admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "tk-disp@example.org", "dispatcher")
    lead_token = await dev_login(client, "tk-lead@example.org", "team_lead")
    lead_id = await user_id(client, lead_token)
    responder_token = await dev_login(client, "tk-resp@example.org", "responder")
    responder_id = await make_responder(
        client, admin, email="tk-resp@example.org", lat=45.02, lng=25.0
    )

    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Tasks", "latitude": 45.0, "longitude": 25.0, "radius_m": 50000},
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
            json={"lead_user_id": lead_id},
        )
    ).json()["id"]
    return {
        "dispatcher": dispatcher,
        "lead_token": lead_token,
        "lead_id": lead_id,
        "responder_token": responder_token,
        "responder_id": responder_id,
        "mission_id": mission_id,
    }


async def test_lead_creates_and_assigns_task(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    create = await client.post(
        f"/missions/{ctx['mission_id']}/tasks",
        headers=auth_header(ctx["lead_token"]),
        json={"title": "Clear road", "assigned_to": ctx["responder_id"], "priority": "high"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["status"] == "open"
    assert body["assigned_to"] == ctx["responder_id"]
    assert body["priority"] == "high"


async def test_responder_cannot_create_task(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    resp = await client.post(
        f"/missions/{ctx['mission_id']}/tasks",
        headers=auth_header(ctx["responder_token"]),
        json={"title": "nope"},
    )
    assert resp.status_code == 403


async def test_assignee_must_be_member(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    outsider = await dev_login(client, "tk-out@example.org", "responder")
    outsider_id = await user_id(client, outsider)
    resp = await client.post(
        f"/missions/{ctx['mission_id']}/tasks",
        headers=auth_header(ctx["lead_token"]),
        json={"title": "x", "assigned_to": outsider_id},
    )
    assert resp.status_code == 422


async def test_responder_updates_own_task_status_only(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    task_id = (
        await client.post(
            f"/missions/{ctx['mission_id']}/tasks",
            headers=auth_header(ctx["lead_token"]),
            json={"title": "Survey", "assigned_to": ctx["responder_id"]},
        )
    ).json()["id"]

    # Status update allowed; completed_at set when done.
    done = await client.patch(
        f"/missions/{ctx['mission_id']}/tasks/{task_id}",
        headers=auth_header(ctx["responder_token"]),
        json={"status": "done"},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "done"
    assert done.json()["completed_at"] is not None

    # Editing other fields is forbidden for the assignee.
    retitle = await client.patch(
        f"/missions/{ctx['mission_id']}/tasks/{task_id}",
        headers=auth_header(ctx["responder_token"]),
        json={"title": "hijack"},
    )
    assert retitle.status_code == 403


async def test_responder_cannot_touch_others_task(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    # Task assigned to the lead, not the responder.
    task_id = (
        await client.post(
            f"/missions/{ctx['mission_id']}/tasks",
            headers=auth_header(ctx["lead_token"]),
            json={"title": "Lead task", "assigned_to": ctx["lead_id"]},
        )
    ).json()["id"]
    resp = await client.patch(
        f"/missions/{ctx['mission_id']}/tasks/{task_id}",
        headers=auth_header(ctx["responder_token"]),
        json={"status": "done"},
    )
    assert resp.status_code == 403


async def test_list_tasks_membership_scoped(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    await client.post(
        f"/missions/{ctx['mission_id']}/tasks",
        headers=auth_header(ctx["lead_token"]),
        json={"title": "T1"},
    )
    member = await client.get(
        f"/missions/{ctx['mission_id']}/tasks", headers=auth_header(ctx["responder_token"])
    )
    assert member.status_code == 200
    assert len(member.json()) == 1

    outsider = await dev_login(client, "tk-out2@example.org", "responder")
    denied = await client.get(
        f"/missions/{ctx['mission_id']}/tasks", headers=auth_header(outsider)
    )
    assert denied.status_code == 403


async def test_no_tasks_on_closed_mission(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    await client.post(
        f"/missions/{ctx['mission_id']}/close",
        headers=auth_header(ctx["dispatcher"]),
        json={},
    )
    resp = await client.post(
        f"/missions/{ctx['mission_id']}/tasks",
        headers=auth_header(ctx["lead_token"]),
        json={"title": "late"},
    )
    assert resp.status_code == 409
