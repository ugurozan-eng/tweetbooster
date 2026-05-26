"""
TwitBoost — Subscription Service
==================================
Business logic for LemonSqueezy subscription lifecycle.

Public API:
    activate_plan(user_id, customer_id, subscription_id, variant_id)  → None
    cancel_plan(user_id)                                               → None
    get_active_plan(user_id)                                           → str

All functions are synchronous and use the Supabase service-role client
(consistent with the rest of the codebase — see auth_service.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from services.supabase_client import get_service_client

__all__ = [
    "SubscriptionServiceError",
    "activate_plan",
    "cancel_plan",
    "get_active_plan",
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SubscriptionServiceError(Exception):
    """Raised when a subscription DB operation fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_plan_map() -> dict[str, str]:
    """Build variant_id → plan_name mapping from environment variables.

    Called lazily (not at module load time) so test monkeypatches work
    correctly.

    Returns:
        A dict mapping each variant ID string to its plan name.
        Entries whose env var is unset are omitted — callers must handle
        unknown variant IDs gracefully.
    """
    mapping: dict[str, str] = {}
    for env_key, plan_name in [
        ("LEMONSQUEEZY_VARIANT_NICHE_ID",      "niche"),
        ("LEMONSQUEEZY_VARIANT_OPPOSITION_ID", "opposition"),
        ("LEMONSQUEEZY_VARIANT_FULL_ID",       "full"),
    ]:
        variant_id = os.environ.get(env_key, "").strip()
        if variant_id:
            mapping[variant_id] = plan_name
    return mapping


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def activate_plan(
    user_id: str,
    customer_id: str,
    subscription_id: str,
    variant_id: str,
) -> None:
    """Activate or upgrade a user's plan after a successful LemonSqueezy payment.

    Sets:
        - ``plan`` = name looked up from variant_id (or "full" as safe default)
        - ``lemonsqueezy_customer_id`` = customer_id
        - ``lemonsqueezy_subscription_id`` = subscription_id
        - ``plan_expires_at`` = now (UTC) + 31 days

    Args:
        user_id:         Our internal UUID for the user.
        customer_id:     LemonSqueezy customer ID string.
        subscription_id: LemonSqueezy subscription ID string.
        variant_id:      LemonSqueezy variant ID — used to look up the plan name.

    Raises:
        SubscriptionServiceError: on DB failure.
    """
    plan_map = _build_plan_map()
    plan_name = plan_map.get(variant_id, "full")  # safe default if unknown variant

    expires_at = (
        datetime.now(tz=timezone.utc) + timedelta(days=31)
    ).isoformat()

    try:
        client = get_service_client()
        (
            client.table("users")
            .upsert(
                {
                    "id":                            user_id,
                    "plan":                          plan_name,
                    "lemonsqueezy_customer_id":      customer_id,
                    "lemonsqueezy_subscription_id":  subscription_id,
                    "plan_expires_at":               expires_at,
                },
                on_conflict="id",
            )
            .execute()
        )
    except EnvironmentError:
        raise
    except Exception as exc:
        raise SubscriptionServiceError(
            f"Plan aktivasyonu başarısız (user_id={user_id}): {exc}"
        ) from exc


def cancel_plan(user_id: str) -> None:
    """Downgrade a user to the free trial plan.

    Clears all LemonSqueezy fields and sets plan = 'trial'.
    Called by the webhook handler when a subscription is cancelled or expired,
    and also internally by get_active_plan when plan_expires_at has passed.

    Args:
        user_id: Our internal UUID for the user.

    Raises:
        SubscriptionServiceError: on DB failure.
    """
    try:
        client = get_service_client()
        (
            client.table("users")
            .update(
                {
                    "plan":                          "trial",
                    "lemonsqueezy_subscription_id":  None,
                    "plan_expires_at":               None,
                }
            )
            .eq("id", user_id)
            .execute()
        )
    except EnvironmentError:
        raise
    except Exception as exc:
        raise SubscriptionServiceError(
            f"Plan iptali başarısız (user_id={user_id}): {exc}"
        ) from exc


def get_active_plan(user_id: str) -> str:
    """Return the user's current plan, auto-downgrading if expired.

    If ``plan_expires_at`` is set and is in the past, this function calls
    ``cancel_plan()`` to clear the subscription and returns ``"trial"``.

    Args:
        user_id: Our internal UUID for the user.

    Returns:
        The plan string: ``"trial"``, ``"niche"``, ``"opposition"``, or ``"full"``.
        Returns ``"trial"`` if the user row doesn't exist.

    Raises:
        SubscriptionServiceError: on DB failure.
    """
    try:
        client = get_service_client()
        resp: Any = (
            client.table("users")
            .select("plan, plan_expires_at")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except EnvironmentError:
        raise
    except Exception as exc:
        raise SubscriptionServiceError(
            f"Aktif plan sorgusu başarısız (user_id={user_id}): {exc}"
        ) from exc

    if resp.data is None:
        return "trial"

    plan: str        = resp.data.get("plan") or "trial"
    expires_at_raw: str | None = resp.data.get("plan_expires_at")

    # Auto-downgrade if subscription has expired
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
            # Make naive datetimes timezone-aware (Supabase returns UTC)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(tz=timezone.utc):
                cancel_plan(user_id)
                return "trial"
        except ValueError:
            # Malformed timestamp — treat as expired for safety
            cancel_plan(user_id)
            return "trial"

    return plan
