"""
Auth service — JWT verification + user/plan operations.

verify_jwt(token)              → UserClaims TypedDict
get_user_plan(user_id)         → plan string or 'trial' if not found
create_user_if_not_exists()    → upsert into public.users

JWT verification uses Supabase's JWKS endpoint (supports ES256 / ECC P-256,
the default since Supabase projects created mid-2025+).
The JWKS is fetched once on first call and cached for 1 hour — no secret needed.

All Supabase errors are caught and re-raised as AuthServiceError so callers
don't need to import supabase exceptions directly.
"""

from __future__ import annotations

import os
import time
from typing import TypedDict

import httpx
from jose import JWTError, jwt
from supabase import Client

from services.supabase_client import get_service_client

__all__ = [
    "AuthServiceError",
    "UserClaims",
    "verify_jwt",
    "get_user_plan",
    "create_user_if_not_exists",
    "_fetch_jwks",       # exposed for test mocking
]

_JWKS_CACHE_TTL = 3600.0   # seconds — refresh once per hour

# Module-level cache (reset between tests via conftest fixture)
_jwks_cache: dict | None = None
_jwks_cache_expiry: float = 0.0


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
# JWKS — fetch and cache public signing keys
# ---------------------------------------------------------------------------

def _fetch_jwks() -> dict:
    """Fetch and cache the JWKS from Supabase Auth.

    Returns a dict with shape {"keys": [...]}.
    Cached for _JWKS_CACHE_TTL seconds (1 hour) to avoid a network round-trip
    on every request.

    Raises:
        EnvironmentError — SUPABASE_URL not set
        AuthServiceError — network or unexpected error
    """
    global _jwks_cache, _jwks_cache_expiry

    now = time.monotonic()
    if _jwks_cache is not None and now < _jwks_cache_expiry:
        return _jwks_cache

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    if not supabase_url:
        raise EnvironmentError("SUPABASE_URL ortam değişkeni tanımlı değil.")

    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        resp = httpx.get(jwks_url, timeout=10)
        resp.raise_for_status()
        data: dict = resp.json()
    except EnvironmentError:
        raise
    except Exception as exc:
        raise AuthServiceError(
            f"JWT imza anahtarları alınamadı ({jwks_url}): {exc}"
        ) from exc

    _jwks_cache = data
    _jwks_cache_expiry = now + _JWKS_CACHE_TTL
    return data


def _get_signing_key(kid: str | None, jwks: dict) -> dict:
    """Return the JWK entry whose 'kid' matches, or the first key if no kid."""
    keys: list[dict] = jwks.get("keys", [])
    if not keys:
        raise AuthServiceError("JWKS'de imza anahtarı bulunamadı.")
    if kid:
        for k in keys:
            if k.get("kid") == kid:
                return k
    # Fallback: first key (handles kidless tokens and rotation edge cases)
    return keys[0]


# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------

def verify_jwt(token: str) -> UserClaims:
    """Decode and verify a Supabase-issued JWT using the project's JWKS.

    Supports ES256 (ECC P-256, default for new Supabase projects) and
    RS256 / HS256 (legacy). The algorithm is read from the token header.

    Returns UserClaims with user_id, email, and plan fetched from DB.
    Raises AuthServiceError on any failure (expired, tampered, unreachable JWKS).
    """
    # ── Parse header to find algorithm + key ID ───────────────────────────
    try:
        header = jwt.get_unverified_header(token)
        kid: str | None = header.get("kid")
        alg: str = header.get("alg", "ES256")
    except JWTError as exc:
        raise AuthServiceError(f"Geçersiz token formatı: {exc}") from exc

    # ── Fetch JWKS and select the matching key ────────────────────────────
    try:
        jwks = _fetch_jwks()
    except EnvironmentError:
        raise
    except AuthServiceError:
        raise

    try:
        signing_key = _get_signing_key(kid, jwks)
    except AuthServiceError:
        raise

    # ── Verify signature + claims ─────────────────────────────────────────
    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[alg, "ES256", "RS256", "HS256"],
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
    """Return the user's active plan, auto-downgrading if the subscription expired.

    Delegates to subscription_service.get_active_plan() which handles expiry
    logic.  Returns 'trial' if the user row doesn't exist yet.

    Local import is used to avoid circular imports at module load time.
    Raises AuthServiceError on unexpected DB errors.
    """
    try:
        # Local import prevents circular dependency at module level
        from services.subscription_service import (  # noqa: PLC0415
            get_active_plan,
            SubscriptionServiceError,
        )
        return get_active_plan(user_id)
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
