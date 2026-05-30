"""Smoke tests for health/meta endpoints (no database required)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

client = TestClient(create_app())


def test_healthz() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_without_infra(monkeypatch: pytest.MonkeyPatch) -> None:
    # Exercise the "no dependencies configured" branch regardless of any
    # DATABASE_URL/REDIS_URL set in the surrounding (CI) environment.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert body["checks"]["database"] == "not_configured"
        assert body["checks"]["redis"] == "not_configured"
    finally:
        get_settings.cache_clear()


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
