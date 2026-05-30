"""Integration tests for the mission room: chat, live location, join/leave, closure."""

from __future__ import annotations

from httpx import AsyncClient

from ._util import auth_header, dev_login, make_responder, user_id


async def _mission_with_member(client: AsyncClient) -> dict:
    """Set up an incident → alert → accept → mission with one responder member.

    Returns a dict of tokens/ids for use in tests.
    """
    admin = await dev_login(client, "rm-admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "rm-disp@example.org", "dispatcher")
    responder_token = await dev_login(client, "rm-resp@example.org", "responder")
    responder_id = await make_responder(
        client, admin, email="rm-resp@example.org", lat=45.02, lng=25.0
    )

    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Room", "latitude": 45.0, "longitude": 25.0, "radius_m": 50000},
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
    return {
        "dispatcher": dispatcher,
        "responder_token": responder_token,
        "responder_id": responder_id,
        "mission_id": mission_id,
    }


async def test_chat_post_and_list(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id, responder = ctx["mission_id"], ctx["responder_token"]

    post = await client.post(
        f"/missions/{mission_id}/messages",
        headers=auth_header(responder),
        json={"message": "On my way"},
    )
    assert post.status_code == 201, post.text
    assert post.json()["message"] == "On my way"

    listed = await client.get(f"/missions/{mission_id}/messages", headers=auth_header(responder))
    assert listed.status_code == 200
    assert [m["message"] for m in listed.json()] == ["On my way"]


async def test_non_member_cannot_chat_or_read(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id = ctx["mission_id"]
    outsider = await dev_login(client, "rm-out@example.org", "responder")

    assert (
        await client.get(f"/missions/{mission_id}/messages", headers=auth_header(outsider))
    ).status_code == 403
    assert (
        await client.post(
            f"/missions/{mission_id}/messages",
            headers=auth_header(outsider),
            json={"message": "hi"},
        )
    ).status_code == 403


async def test_live_location_requires_consent_then_works(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id, responder = ctx["mission_id"], ctx["responder_token"]

    # Accepted member has not enabled live location yet → 403.
    blocked = await client.post(
        f"/missions/{mission_id}/locations",
        headers=auth_header(responder),
        json={"latitude": 45.01, "longitude": 25.0},
    )
    assert blocked.status_code == 403

    # Join with explicit consent, then posting works.
    join = await client.post(
        f"/missions/{mission_id}/join",
        headers=auth_header(responder),
        json={"live_location_enabled": True},
    )
    assert join.status_code == 200

    posted = await client.post(
        f"/missions/{mission_id}/locations",
        headers=auth_header(responder),
        json={"latitude": 45.01, "longitude": 25.0, "accuracy_m": 8.0},
    )
    assert posted.status_code == 201

    live = await client.get(
        f"/missions/{mission_id}/locations/live", headers=auth_header(ctx["dispatcher"])
    )
    assert live.status_code == 200
    points = live.json()
    assert len(points) == 1
    assert points[0]["user_id"] == ctx["responder_id"]
    assert abs(points[0]["latitude"] - 45.01) < 1e-6


async def test_leave_stops_location_sharing(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id, responder = ctx["mission_id"], ctx["responder_token"]
    await client.post(
        f"/missions/{mission_id}/join",
        headers=auth_header(responder),
        json={"live_location_enabled": True},
    )
    await client.post(f"/missions/{mission_id}/leave", headers=auth_header(responder))

    blocked = await client.post(
        f"/missions/{mission_id}/locations",
        headers=auth_header(responder),
        json={"latitude": 45.01, "longitude": 25.0},
    )
    assert blocked.status_code == 403


async def test_close_locks_mission_and_stops_sharing(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id, responder, dispatcher = (
        ctx["mission_id"],
        ctx["responder_token"],
        ctx["dispatcher"],
    )
    await client.post(
        f"/missions/{mission_id}/join",
        headers=auth_header(responder),
        json={"live_location_enabled": True},
    )

    closed = await client.post(
        f"/missions/{mission_id}/close",
        headers=auth_header(dispatcher),
        json={"closure_summary": "All clear"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert all(not m["live_location_enabled"] for m in closed.json()["members"])

    # Mission is read-only now.
    assert (
        await client.post(
            f"/missions/{mission_id}/messages",
            headers=auth_header(responder),
            json={"message": "late"},
        )
    ).status_code == 409
    assert (
        await client.post(
            f"/missions/{mission_id}/locations",
            headers=auth_header(responder),
            json={"latitude": 45.0, "longitude": 25.0},
        )
    ).status_code == 409

    # Double close is rejected.
    assert (
        await client.post(
            f"/missions/{mission_id}/close", headers=auth_header(dispatcher), json={}
        )
    ).status_code == 409


async def test_uninvited_user_cannot_join(client: AsyncClient) -> None:
    ctx = await _mission_with_member(client)
    mission_id = ctx["mission_id"]
    stranger = await dev_login(client, "rm-stranger@example.org", "responder")
    resp = await client.post(
        f"/missions/{mission_id}/join",
        headers=auth_header(stranger),
        json={"live_location_enabled": True},
    )
    assert resp.status_code == 403
