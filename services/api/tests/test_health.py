"""Smoke tests for the API skeleton."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_healthz() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_without_infra() -> None:
    # With no DATABASE_URL/REDIS_URL configured the probe reports them as
    # not configured but the service is still considered ready.
    resp = client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "not_configured"
    assert body["checks"]["redis"] == "not_configured"


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_incidents_empty() -> None:
    resp = client.get("/incidents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_incident_not_implemented() -> None:
    resp = client.post("/incidents")
    assert resp.status_code == 501
