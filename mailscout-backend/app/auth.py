import logging
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _get_supabase() -> Client:
    """Lazy singleton Supabase client (avoids import-time failures in tests)."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@dataclass
class CurrentUser:
    user_id: str
    email: str | None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """Validate Supabase JWT and return authenticated user."""
    token = credentials.credentials
    try:
        response = _get_supabase().auth.get_user(token)
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return CurrentUser(
            user_id=str(response.user.id),
            email=response.user.email,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Auth failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
