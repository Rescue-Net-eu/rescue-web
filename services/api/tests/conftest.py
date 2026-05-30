"""Pytest fixtures.

Integration tests run against a real PostGIS database (the geospatial
responder search cannot be faithfully exercised otherwise). The database
URL comes from ``TEST_DATABASE_URL`` or ``DATABASE_URL``; if no database is
reachable the integration tests are skipped rather than failed, so the
pure-unit suite still runs anywhere.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401 - register models on Base.metadata
from app.db import Base, get_session
from app.main import create_app

TEST_DATABASE_URL = (
    os.environ.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql+asyncpg://rescuenet:rescuenet@127.0.0.1:5432/rescuenet_test"
)

# Enable the broker for realtime tests. Default to a local Redis; tests that
# need it skip cleanly via the broker being unreachable only if explicitly
# checked (the REST flows tolerate a down broker).
TEST_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_URL", TEST_REDIS_URL)


def _sync_url(url: str) -> str:
    return url.replace("+asyncpg", "+psycopg2")


@pytest.fixture(scope="session")
def _schema() -> None:
    """Ensure the schema exists; skip the whole suite if no DB is reachable."""
    engine = create_engine(_sync_url(TEST_DATABASE_URL))
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            Base.metadata.create_all(conn)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"test database not available: {exc}", allow_module_level=False)
    finally:
        engine.dispose()


@pytest.fixture()
def _clean(_schema: None) -> None:
    """Truncate all tables before each test for isolation."""
    engine = create_engine(_sync_url(TEST_DATABASE_URL))
    tables = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    engine.dispose()


@pytest_asyncio.fixture()
async def client(_clean: None) -> AsyncClient:
    engine = create_async_engine(TEST_DATABASE_URL)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with sessionmaker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await app.state.broker.close()
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(_clean: None):
    """A direct async session for unit-testing service functions (retention)."""
    engine = create_async_engine(TEST_DATABASE_URL)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
    await engine.dispose()
