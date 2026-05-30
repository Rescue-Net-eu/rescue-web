"""Authentication endpoints (manual section 14.1).

`/me` returns the authenticated user. `/auth/dev/login` is a developer-only
shortcut that upserts a user and returns a signed token so the API can be
exercised end-to-end before the Authentik/OIDC integration lands; it is
disabled in production. The mobile OTP endpoints remain stubs pending the
SMS provider.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit import record_audit
from ..config import get_settings
from ..db import get_session
from ..deps import get_current_user, get_user_by_email
from ..models import User
from ..schemas import DevLoginRequest, Token, UserOut
from ..security import create_access_token

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/auth/dev/login", response_model=Token)
async def dev_login(
    payload: DevLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Upsert a user by email and return an access token. Non-production only."""
    settings = get_settings()
    if not settings.dev_login_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not available"
        )

    user = await get_user_by_email(session, payload.email)
    if user is None:
        user = User(email=payload.email, full_name=payload.full_name, role=payload.role)
        session.add(user)
        await session.flush()
        created = True
    else:
        user.role = payload.role
        if payload.full_name:
            user.full_name = payload.full_name
        created = False

    await record_audit(
        session,
        action="auth.dev_login",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
        metadata={"created": created, "role": user.role},
    )
    await session.commit()

    token = create_access_token(str(user.id), settings=settings)
    return Token(access_token=token)


@router.post("/auth/mobile/start", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def mobile_start() -> dict[str, str]:
    return {"detail": "Mobile OTP start is not implemented; see manual section 27."}


@router.post("/auth/mobile/verify", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def mobile_verify() -> dict[str, str]:
    return {"detail": "Mobile OTP verify is not implemented; see manual section 27."}
