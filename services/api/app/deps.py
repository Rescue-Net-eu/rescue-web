"""Shared FastAPI dependencies: authentication and role-based access control.

Every protected endpoint resolves the caller via :func:`get_current_user`
and authorizes with :func:`require_roles` (manual sections 15.1, 15.2 and
the role matrix in section 6).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .enums import UserRole
from .models import User
from .security import TokenError, decode_token

# auto_error=False so we can return a consistent 401 with a WWW-Authenticate header.
_bearer = HTTPBearer(auto_error=False)

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user from a verified bearer token."""
    if credentials is None or not credentials.credentials:
        raise _UNAUTHENTICATED
    try:
        claims = decode_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = claims.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from exc

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return user


def require_roles(*roles: UserRole) -> Callable[..., Awaitable[User]]:
    """Dependency factory enforcing that the caller holds one of ``roles``."""
    allowed = {UserRole(r) for r in roles}

    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if UserRole(user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )
        return user

    return _dependency


# Convenience bundles matching the manual's role groupings.
require_dispatcher = require_roles(
    UserRole.DISPATCHER, UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN
)
require_admin = require_roles(UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
