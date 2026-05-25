"""
TwitBoost — Auth Router
========================
Endpoint:
  POST /api/auth/me  — Return current user info + plan + today's usage count

Requires a valid Bearer JWT (same as all protected endpoints).
Called by the frontend on load to populate the session context.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from middleware.auth_middleware import UserClaims, get_current_user
from services.auth_service import AuthServiceError, create_user_if_not_exists
from services.supabase_client import get_service_client

router = APIRouter(prefix="/api/auth", tags=["auth"])

_ISTANBUL = ZoneInfo("Europe/Istanbul")


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class MeResponse(BaseModel):
    user_id: str
    email: str
    plan: str
    usage_today: int   # total requests today (UTC+3)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/me",
    response_model=MeResponse,
    summary="Current user info + plan + today's usage",
)
async def me(user: UserClaims = Depends(get_current_user)) -> MeResponse:
    """
    Return the authenticated user's profile.

    Also ensures the user row exists in public.users (idempotent upsert on
    first login — so the frontend can call this right after Supabase Auth
    sign-in and we'll create the DB row automatically).

    Returns:
        user_id     — Supabase Auth UUID
        email       — from JWT
        plan        — 'trial' | 'niche' | 'opposition' | 'full'
        usage_today — total requests made today (Istanbul time)
    """
    # ── Ensure user row exists (first-login upsert) ───────────────────────
    try:
        create_user_if_not_exists(user["user_id"], user["email"])
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # ── Fetch today's usage from daily_usage view ─────────────────────────
    today_istanbul = datetime.now(tz=_ISTANBUL).date().isoformat()
    usage_today = 0
    try:
        client = get_service_client()
        resp = (
            client.table("daily_usage")
            .select("total_count")
            .eq("user_id", user["user_id"])
            .eq("day", today_istanbul)
            .maybe_single()
            .execute()
        )
        if resp.data is not None:
            usage_today = int(resp.data.get("total_count", 0))
    except EnvironmentError:
        raise
    except Exception:
        # Usage count is informational — don't fail /me for a DB hiccup
        pass

    return MeResponse(
        user_id=user["user_id"],
        email=user["email"],
        plan=user["plan"],
        usage_today=usage_today,
    )
