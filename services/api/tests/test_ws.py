"""WebSocket mission-room tests (manual section 14.2).

Uses Starlette's sync TestClient (httpx cannot drive WebSockets). Each test
builds its own app with the test database so its async engine binds to the
TestClient's event loop. Requires a reachable Redis and PostGIS.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.websockets import WebSocketDisconnect

from app.db import get_session
from app.main import create_app

from .conftest import TEST_DATABASE_URL


def _build_test_client() -> TestClient:
    engine = create_async_engine(TEST_DATABASE_URL)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with sessionmaker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


def _dispatcher_and_mission(tc: TestClient) -> tuple[str, str]:
    token = tc.post(
        "/auth/dev/login", json={"email": "ws-d@example.org", "role": "dispatcher"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    incident_id = tc.post("/incidents", headers=headers, json={"title": "WS"}).json()["id"]
    mission_id = tc.post(
        f"/incidents/{incident_id}/create-mission", headers=headers, json={}
    ).json()["id"]
    return token, mission_id


def test_ws_streams_chat_event(_clean: None) -> None:
    tc = _build_test_client()
    with tc:
        token, mission_id = _dispatcher_and_mission(tc)
        headers = {"Authorization": f"Bearer {token}"}
        with tc.websocket_connect(f"/ws/missions/{mission_id}?token={token}") as ws:
            # Wait for the subscription to be live before publishing.
            ready = ws.receive_json()
            assert ready["type"] == "connection.ready"

            tc.post(
                f"/missions/{mission_id}/messages",
                headers=headers,
                json={"message": "hello room"},
            )
            event = ws.receive_json()
            assert event["type"] == "mission.chat_message"
            assert event["data"]["message"] == "hello room"


def test_ws_rejects_without_token(_clean: None) -> None:
    tc = _build_test_client()
    with tc:
        _token, mission_id = _dispatcher_and_mission(tc)
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/ws/missions/{mission_id}") as ws:
                ws.receive_json()


def test_ws_rejects_non_member(_clean: None) -> None:
    tc = _build_test_client()
    with tc:
        _token, mission_id = _dispatcher_and_mission(tc)
        outsider = tc.post(
            "/auth/dev/login", json={"email": "ws-out@example.org", "role": "responder"}
        ).json()["access_token"]
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/ws/missions/{mission_id}?token={outsider}") as ws:
                ws.receive_json()
