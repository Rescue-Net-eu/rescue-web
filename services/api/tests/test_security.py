"""Unit tests for token issuance/verification (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import Settings
from app.security import TokenError, create_access_token, decode_token


def _settings() -> Settings:
    return Settings(jwt_secret="unit-test-secret", app_env="test")


def test_token_round_trip() -> None:
    settings = _settings()
    subject = str(uuid.uuid4())
    token = create_access_token(subject, settings=settings)
    claims = decode_token(token, settings=settings)
    assert claims["sub"] == subject
    assert "exp" in claims


def test_decode_rejects_wrong_secret() -> None:
    token = create_access_token("abc", settings=_settings())
    other = Settings(jwt_secret="different-secret", app_env="test")
    with pytest.raises(TokenError):
        decode_token(token, settings=other)


def test_decode_rejects_expired() -> None:
    settings = _settings()
    expired = jwt.encode(
        {"sub": "abc", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenError):
        decode_token(expired, settings=settings)


def test_decode_requires_subject() -> None:
    settings = _settings()
    no_sub = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenError):
        decode_token(no_sub, settings=settings)
