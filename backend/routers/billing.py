"""
TwitBoost — Billing Router
============================
Endpoints for plan discovery, LemonSqueezy checkout creation, and subscription status.

Routes:
    GET  /api/billing/plans    — public; list all available plans + prices
    POST /api/billing/checkout — auth required; create a hosted checkout URL
    GET  /api/billing/status   — auth required; return current user plan info
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from middleware.auth_middleware import UserClaims, get_current_user
from services.lemonsqueezy_client import LemonSqueezyError, create_checkout
from services.subscription_service import SubscriptionServiceError, get_active_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Static plan catalogue
# ---------------------------------------------------------------------------

# Plan metadata displayed to the UI — prices and limits must match docs/PRD.md
_PLANS = [
    {
        "id":          "niche",
        "name":        "Niş Mod",
        "price_try":   54.99,
        "daily_limit": 20,
        "modes":       ["niche"],
        "description": "Günlük 20 kullanım · Niş mod",
    },
    {
        "id":          "opposition",
        "name":        "Muhalefet Modu",
        "price_try":   109.99,
        "daily_limit": 15,
        "modes":       ["opposition"],
        "description": "Günlük 15 kullanım · Muhalefet modu",
    },
    {
        "id":          "full",
        "name":        "Tam Erişim",
        "price_try":   149.99,
        "daily_limit": 30,
        "modes":       ["niche", "opposition"],
        "description": "Günlük 30 kullanım · Her iki mod",
    },
]

# Maps plan name → variant ID env var — used to look up the variant for checkout
_PLAN_VARIANT_ENV: dict[str, str] = {
    "niche":      "LEMONSQUEEZY_VARIANT_NICHE_ID",
    "opposition": "LEMONSQUEEZY_VARIANT_OPPOSITION_ID",
    "full":       "LEMONSQUEEZY_VARIANT_FULL_ID",
}


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    plan_id: str  # "niche" | "opposition" | "full"


class CheckoutResponse(BaseModel):
    checkout_url: str


class BillingStatusResponse(BaseModel):
    plan:    str
    user_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/plans")
async def get_plans() -> list[dict]:
    """Return the full plan catalogue (no auth required).

    Each entry includes id, name, price_try, daily_limit, modes, description.
    Variant IDs are NOT included — the client never needs them.
    """
    return _PLANS


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    user: UserClaims = Depends(get_current_user),
) -> CheckoutResponse:
    """Create a LemonSqueezy hosted checkout for the requested plan.

    The ``user_id`` is embedded in ``custom_data`` so the webhook can
    activate the plan without a redirect callback.

    Args:
        body.plan_id: One of "niche", "opposition", "full".

    Returns:
        CheckoutResponse with the hosted checkout URL to redirect the browser to.

    Raises:
        HTTP 400 — unknown plan_id
        HTTP 500 — LemonSqueezy API unavailable or missing env vars
    """
    if body.plan_id not in _PLAN_VARIANT_ENV:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bilinmeyen plan: '{body.plan_id}'. Geçerli planlar: {list(_PLAN_VARIANT_ENV)}",
        )

    # Resolve IDs from environment — never hardcode
    store_id = os.environ.get("LEMONSQUEEZY_STORE_ID", "").strip()
    variant_id = os.environ.get(_PLAN_VARIANT_ENV[body.plan_id], "").strip()

    if not store_id or not variant_id:
        logger.error(
            "LemonSqueezy env vars eksik: LEMONSQUEEZY_STORE_ID=%r variant_env=%s variant_id=%r",
            store_id,
            _PLAN_VARIANT_ENV[body.plan_id],
            variant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ödeme sistemi yapılandırılmamış. Lütfen daha sonra tekrar deneyin.",
        )

    try:
        url = await create_checkout(
            store_id=store_id,
            variant_id=variant_id,
            user_email=user["email"],
            user_id=user["user_id"],
        )
    except LemonSqueezyError as exc:
        logger.error("LemonSqueezy checkout hatası: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ödeme sayfası oluşturulamadı. Lütfen daha sonra tekrar deneyin.",
        ) from exc

    return CheckoutResponse(checkout_url=url)


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    user: UserClaims = Depends(get_current_user),
) -> BillingStatusResponse:
    """Return the authenticated user's current plan.

    Plan expiry is checked on each call — if expired the user is automatically
    downgraded to 'trial' before the response is returned.

    Returns:
        BillingStatusResponse with plan and user_id.
    """
    try:
        plan = get_active_plan(user["user_id"])
    except EnvironmentError as exc:
        # Supabase not configured (dev environment) — fall back to JWT-embedded plan
        logger.warning("Supabase yapılandırılmamış, JWT planı kullanılıyor: %s", exc)
        plan = user.get("plan", "trial")
    except SubscriptionServiceError as exc:
        logger.error("Plan durumu sorgulanamadı (user_id=%s): %s", user["user_id"], exc)
        plan = user.get("plan", "trial")

    return BillingStatusResponse(plan=plan, user_id=user["user_id"])
