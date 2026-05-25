"""
Auth service — JWT verification + user/plan operations.

verify_jwt(token)              → UserClaims TypedDict
get_user_plan(user_id)         → plan string or 'trial' if not found
create_user_if_not_exists()    → upsert into public.users

All Supabase errors are caught and re-raised as AuthServiceError so callers
don't need to import supabase exceptions directly.
"""

from __future__ import annotations

import os
from typing import TypedDict

from jose import JWTError, jwt
from supabase import Client

from services.supabase_client import get_service_client

__all__ = [
    "AuthServiceError",
    "UserClaims",
    "verify_jwt",
    "get_user_plan",
    "create_user_if_not_exists",
]

_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AuthServiceError(Exception):
    """Base for auth service failures (JWT invalid, DB errors, …)."""


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class UserClaims(TypedDict):
    user_id: str
    email: str
    plan: str


# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------

def _get_jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        raise EnvironmentError(
            "SUPABASE_JWT_SECRET ortam değişkeni tanımlı değil."
        )
    return secret


def verify_jwt(token: str) -> UserClaims:
    """Decode and verify a Supabase-issued JWT.

    Returns UserClaims with user_id, email, and plan fetched from DB.
    Raises AuthServiceError on any failure (expired, tampered, missing env).
    """
    try:
        secret = _get_jwt_secret()
    except EnvironmentError as exc:
        raise AuthServiceError(str(exc)) from exc

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},  # Supabase uses 'authenticated' audience
        )
    except JWTError as exc:
        raise AuthServiceError(f"Geçersiz veya süresi dolmuş oturum: {exc}") from exc

    user_id: str = payload.get("sub", "")
    email: str = payload.get("email", "")

    if not user_id:
        raise AuthServiceError("JWT içinde kullanıcı kimliği bulunamadı.")

    plan = get_user_plan(user_id)
    return UserClaims(user_id=user_id, email=email, plan=plan)


# ---------------------------------------------------------------------------
# User / plan DB operations
# ---------------------------------------------------------------------------

def get_user_plan(user_id: str) -> str:
    """Look up the user's plan in public.users.

    Returns the plan string, or 'trial' if the user row doesn't exist yet.
    Raises AuthServiceError on unexpected DB errors.
    """
    try:
        client: Client = get_service_client()
        resp = (
            client.table("users")
            .select("plan")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if resp.data is None:
            return "trial"
        return str(resp.data.get("plan", "trial"))
    except EnvironmentError:
        raise
    except Exception as exc:
        raise AuthServiceError(
            f"Kullanıcı planı alınırken hata oluştu: {exc}"
        ) from exc


def create_user_if_not_exists(user_id: str, email: str) -> None:
    """Upsert a user row into public.users on first login.

    Uses ON CONFLICT DO NOTHING so repeated calls are idempotent.
    Raises AuthServiceError on DB failure.
    """
    try:
        client: Client = get_service_client()
        (
            client.table("users")
            .upsert(
                {"id": user_id, "email": email, "plan": "trial"},
                on_conflict="id",
                ignore_duplicates=True,
            )
            .execute()
        )
    except EnvironmentError:
        raise
    except Exception as exc:
        raise AuthServiceError(
            f"Kullanıcı kaydı oluşturulurken hata oluştu: {exc}"
        ) from exc
