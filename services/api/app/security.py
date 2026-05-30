"""Token issuance and verification.

The verification layer accepts a bearer JWT and returns its claims. Two
modes are supported behind one interface:

* **Local HS256** (default) — signed with ``JWT_SECRET``; used for local
  development and the controlled pilot, and for minting test tokens.
* **OIDC RS256** — when ``OIDC_JWKS_URL`` is configured the token is
  verified against the provider's published keys (manual section 15.1).

Only the local mode is wired up in this increment; the OIDC branch raises
a clear error so the extension point is explicit rather than silent.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from .config import Settings, get_settings


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired or untrusted."""


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> str:
    """Mint a short-lived HS256 access token for ``subject`` (a user id)."""
    settings = settings or get_settings()
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    if settings.jwt_issuer:
        claims["iss"] = settings.jwt_issuer
    if settings.jwt_audience:
        claims["aud"] = settings.jwt_audience
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, settings: Settings | None = None) -> dict[str, Any]:
    """Verify a bearer token and return its claims, or raise :class:`TokenError`."""
    settings = settings or get_settings()

    if settings.oidc_jwks_url:
        # Production OIDC verification lands with the Authentik integration.
        raise TokenError("OIDC verification is not yet implemented")

    options = {"require": ["exp", "sub"]}
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience if settings.jwt_audience else None,
            issuer=settings.jwt_issuer if settings.jwt_issuer else None,
            options=options,
        )
    except jwt.PyJWTError as exc:  # noqa: TRY003 - message is surfaced to the caller
        raise TokenError(str(exc)) from exc
