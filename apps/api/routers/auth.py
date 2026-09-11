"""
Auth router.

The actual OAuth flow (GitHub/Google) happens in Auth.js on the Next.js
frontend — this API never sees an OAuth password/token exchange. What
it does own:

  1. `POST /api/auth/sync-user` — called once by Auth.js's `signIn`
     callback on every sign-in. Upserts a `User` row keyed on
     (provider, provider_account_id) and returns a short-lived API JWT
     the frontend stores in its session and attaches to every other
     `/api/*` call as `Authorization: Bearer <token>`.
  2. `GET /api/auth/me` — returns the current user for a given token,
     used by the frontend to hydrate account state.
  3. The `get_current_user` / `get_current_user_optional` dependencies
     other routers import to gate/scope endpoints.

This endpoint is protected by a shared secret (`AUTH_SYNC_SECRET`), not
a user JWT — chicken-and-egg, since the whole point is to mint the
user's first JWT. Only the Next.js backend (Auth.js server-side
callback) should ever call it, never the browser directly.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from database.db import get_db
from database.models import User, LeaderboardEntry
from security.auth import generate_jwt_token, decode_jwt_token, AuthError

logger = logging.getLogger(__name__)
router = APIRouter()


class SyncUserRequest(BaseModel):
    provider: str
    provider_account_id: str
    email: str | None = None
    display_name: str
    avatar_url: str | None = None


class SyncUserResponse(BaseModel):
    token: str
    user_id: int
    display_name: str


class MeResponse(BaseModel):
    user_id: int
    display_name: str
    email: str | None
    avatar_url: str | None


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    """Required-auth dependency. Raises 401 if no/invalid token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_jwt_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> User | None:
    """Optional-auth dependency — returns None instead of raising, for
    endpoints that behave differently when signed in but don't require it."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = decode_jwt_token(authorization.split(" ", 1)[1])
    except AuthError:
        return None
    return db.query(User).filter(User.id == payload.get("user_id")).first()


@router.post("/sync-user", response_model=SyncUserResponse)
def sync_user(
    body: SyncUserRequest,
    db: Session = Depends(get_db),
    x_sync_secret: str | None = Header(default=None),
):
    if not settings.AUTH_SYNC_SECRET or x_sync_secret != settings.AUTH_SYNC_SECRET:
        raise HTTPException(status_code=403, detail="Invalid sync secret")

    user = (
        db.query(User)
        .filter(User.provider == body.provider, User.provider_account_id == body.provider_account_id)
        .first()
    )
    if user:
        user.display_name = body.display_name
        user.email = body.email or user.email
        user.avatar_url = body.avatar_url or user.avatar_url
        user.last_login_at = datetime.utcnow()
    else:
        user = User(
            provider=body.provider,
            provider_account_id=body.provider_account_id,
            email=body.email,
            display_name=body.display_name,
            avatar_url=body.avatar_url,
        )
        db.add(user)
        db.flush()  # populate user.id before we reference it below
        db.add(LeaderboardEntry(user_id=user.id, total_score=0))

    db.commit()
    db.refresh(user)

    token = generate_jwt_token(user_id=user.id)
    return SyncUserResponse(token=token, user_id=user.id, display_name=user.display_name)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        user_id=current_user.id,
        display_name=current_user.display_name,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
    )
