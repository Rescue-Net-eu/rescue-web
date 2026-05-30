"""Tests for GDPR retention sweeps and erasure (manual sections 16.2, 16.4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import func, select

from app import retention
from app.models import AuditLog, ChatMessage, Location, MissionArchive, User
from app.privacy import erase_user

from ._util import auth_header, dev_login, make_responder, user_id


async def _closed_mission_with_activity(client: AsyncClient) -> dict:
    """Build a mission with a member, location, chat and a task, then close it."""
    admin = await dev_login(client, "rt-admin@example.org", "platform_admin")
    dispatcher = await dev_login(client, "rt-disp@example.org", "dispatcher")
    responder_token = await dev_login(client, "rt-resp@example.org", "responder")
    responder_id = await make_responder(
        client, admin, email="rt-resp@example.org", lat=45.02, lng=25.0, skills=["first_aid"]
    )
    incident_id = (
        await client.post(
            "/incidents",
            headers=auth_header(dispatcher),
            json={"title": "Ret", "type": "flood", "latitude": 45.0, "longitude": 25.0,
                  "radius_m": 50000},
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
    # Join with consent, post a location and a chat message.
    await client.post(
        f"/missions/{mission_id}/join",
        headers=auth_header(responder_token),
        json={"live_location_enabled": True},
    )
    await client.post(
        f"/missions/{mission_id}/locations",
        headers=auth_header(responder_token),
        json={"latitude": 45.01, "longitude": 25.0},
    )
    await client.post(
        f"/missions/{mission_id}/messages",
        headers=auth_header(responder_token),
        json={"message": "arrived on scene"},
    )
    await client.post(
        f"/missions/{mission_id}/close", headers=auth_header(dispatcher), json={}
    )
    return {"mission_id": mission_id, "responder_id": responder_id,
            "responder_token": responder_token}


async def _count(session, model, **filters) -> int:
    stmt = select(func.count()).select_from(model)
    for attr, val in filters.items():
        stmt = stmt.where(getattr(model, attr) == val)
    return int((await session.execute(stmt)).scalar_one())


async def test_archive_is_created_and_idempotent(client: AsyncClient, db_session) -> None:
    ctx = await _closed_mission_with_activity(client)
    mission_id = uuid.UUID(ctx["mission_id"])

    n1 = await retention.archive_closed_missions(db_session)
    await db_session.commit()
    assert n1 == 1

    archive = (
        await db_session.execute(
            select(MissionArchive).where(MissionArchive.mission_id == mission_id)
        )
    ).scalar_one()
    assert archive.responder_count == 1
    assert archive.accepted_count == 1
    assert archive.chat_message_count == 1
    assert archive.location_sample_count == 1
    assert archive.incident_type == "flood"
    assert "first_aid" in archive.skills_used

    # Re-running archives nothing new.
    n2 = await retention.archive_closed_missions(db_session)
    await db_session.commit()
    assert n2 == 0


async def test_locations_purged_only_after_window_and_archived_first(
    client: AsyncClient, db_session
) -> None:
    ctx = await _closed_mission_with_activity(client)
    mission_id = uuid.UUID(ctx["mission_id"])

    # Within the window: nothing purged.
    purged_now = await retention.purge_expired_locations(db_session, now=datetime.now(UTC))
    await db_session.commit()
    assert purged_now == 0
    assert await _count(db_session, Location, mission_id=mission_id) == 1

    # Simulate 31 days passing via the injected clock.
    future = datetime.now(UTC) + timedelta(days=31)
    purged = await retention.purge_expired_locations(db_session, now=future)
    await db_session.commit()
    assert purged == 1
    assert await _count(db_session, Location, mission_id=mission_id) == 0

    # Archive exists and preserved the sample count before deletion.
    archive = (
        await db_session.execute(
            select(MissionArchive).where(MissionArchive.mission_id == mission_id)
        )
    ).scalar_one()
    assert archive.location_sample_count == 1


async def test_participation_anonymized_after_window(client: AsyncClient, db_session) -> None:
    ctx = await _closed_mission_with_activity(client)
    mission_id = uuid.UUID(ctx["mission_id"])

    future = datetime.now(UTC) + timedelta(days=1100)
    processed = await retention.anonymize_old_participation(db_session, now=future)
    await db_session.commit()
    assert processed == 1

    msg = (
        await db_session.execute(
            select(ChatMessage).where(ChatMessage.mission_id == mission_id)
        )
    ).scalar_one()
    assert msg.message == ""
    assert msg.deleted_at is not None
    # Count is preserved in the archive.
    archive = (
        await db_session.execute(
            select(MissionArchive).where(MissionArchive.mission_id == mission_id)
        )
    ).scalar_one()
    assert archive.chat_message_count == 1


async def test_audit_logs_purged_past_window(client: AsyncClient, db_session) -> None:
    await dev_login(client, "audit-gen@example.org", "dispatcher")  # generates audit rows
    before = await _count(db_session, AuditLog)
    assert before > 0

    future = datetime.now(UTC) + timedelta(days=1100)
    purged = await retention.purge_old_audit_logs(db_session, now=future)
    await db_session.commit()
    assert purged == before
    assert await _count(db_session, AuditLog) == 0


async def test_erase_user_removes_pii_keeps_history(client: AsyncClient, db_session) -> None:
    ctx = await _closed_mission_with_activity(client)
    responder_id = uuid.UUID(ctx["responder_id"])

    summary = await erase_user(db_session, responder_id)
    assert summary["locations_deleted"] == 1
    assert summary["chats_blanked"] == 1
    assert summary["missions_archived"] == 1

    db_session.expire_all()
    user = await db_session.get(User, responder_id)
    assert user.status == "deleted"
    assert user.full_name is None
    assert user.email == f"deleted+{responder_id}@anonymized.invalid"

    # Raw personal data gone; anonymized history kept.
    assert await _count(db_session, Location, user_id=responder_id) == 0
    assert await _count(db_session, MissionArchive) == 1
    # Audit trail retained (erasure itself is audited).
    erase_logged = await _count(db_session, AuditLog, action="user.erase")
    assert erase_logged == 1


async def test_run_all_returns_counts(client: AsyncClient, db_session) -> None:
    await _closed_mission_with_activity(client)
    counts = await retention.run_all(db_session, now=datetime.now(UTC) + timedelta(days=40))
    assert counts["archived"] >= 1
    assert counts["locations_purged"] >= 1
    assert set(counts) == {
        "archived",
        "locations_purged",
        "participation_anonymized",
        "audit_logs_purged",
    }


# --- Admin endpoints ------------------------------------------------------


async def test_admin_retention_run_requires_platform_admin(client: AsyncClient) -> None:
    responder = await dev_login(client, "ar-resp@example.org", "responder")
    denied = await client.post("/admin/retention/run", headers=auth_header(responder))
    assert denied.status_code == 403

    admin = await dev_login(client, "ar-admin@example.org", "platform_admin")
    ok = await client.post("/admin/retention/run", headers=auth_header(admin))
    assert ok.status_code == 200
    assert "archived" in ok.json()


async def test_admin_erase_user_endpoint(client: AsyncClient) -> None:
    admin = await dev_login(client, "ae-admin@example.org", "platform_admin")
    victim = await dev_login(client, "ae-victim@example.org", "responder")
    victim_id = await user_id(client, victim)

    resp = await client.post(
        f"/admin/users/{victim_id}/erase", headers=auth_header(admin)
    )
    assert resp.status_code == 200

    # The erased user can no longer authenticate (status != active).
    me = await client.get("/me", headers=auth_header(victim))
    assert me.status_code == 403


async def test_admin_erase_unknown_user_404(client: AsyncClient) -> None:
    admin = await dev_login(client, "ae-admin2@example.org", "platform_admin")
    resp = await client.post(
        f"/admin/users/{uuid.uuid4()}/erase", headers=auth_header(admin)
    )
    assert resp.status_code == 404
