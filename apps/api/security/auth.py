"""
JWT issue/verify helpers — framework-agnostic (no Flask left in here).

The actual sign-in flow lives in Auth.js on the frontend (GitHub/Google
OAuth). On first sign-in, the frontend calls `POST /api/auth/sync-user`
with the OAuth profile; this module's `generate_jwt_token()` mints a
short-lived API token the frontend then attaches as
`Authorization: Bearer <token>` on subsequent API calls. FastAPI-side
verification (the `Depends(get_current_user)` dependency) lives in
`routers/auth.py`, which is where this used to be a Flask decorator
(`require_auth`) before the migration — see AUDIT.md B-6 for why that
was previously dead code with nothing to attach it to.
"""
import logging
from datetime import datetime, timedelta, timezone

import jwt

from config.settings import settings

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised for any JWT generation/verification failure."""
    pass


def generate_jwt_token(user_id: int, role: str = 'user') -> str:
    """Generate a JWT for an authenticated user."""
    try:
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': now,
            'exp': now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Error generating JWT token: {e}")
        raise AuthError(f"Token generation failed: {e}")


def decode_jwt_token(token: str) -> dict:
    """Decode and verify a JWT, raising AuthError on any problem."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        raise AuthError(f"Token decoding failed: {e}")
