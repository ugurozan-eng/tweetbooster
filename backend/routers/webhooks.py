"""
TwitBoost — LemonSqueezy Webhook Handler
=========================================
Receives and processes LemonSqueezy subscription lifecycle events.

Security:
    Every request is verified with an HMAC-SHA256 signature produced from the
    raw request body and LEMONSQUEEZY_WEBHOOK_SECRET.  Requests with a missing
    or invalid signature are rejected with HTTP 401 immediately.

Reliability:
    Internal errors (bad payload shape, DB failure, …) are caught and logged
    but the endpoint always returns HTTP 200 so LemonSqueezy does not retry.

Supported events:
    subscription_created  → activate_plan
    subscription_updated  → activate_plan (when status == "active") or cancel_plan
    subscription_cancelled → cancel_plan
    subscription_expired   → cancel_plan
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request, Response

from services.subscription_service import activate_plan, cancel_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def _verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """Return True if the HMAC-SHA256 of raw_body matches signature_header.

    Args:
        raw_body:          The unmodified bytes of the HTTP request body.
        signature_header:  The hex digest from the ``X-Signature`` header.

    Returns:
        True if the computed digest matches; False otherwise.
        Also returns False when LEMONSQUEEZY_WEBHOOK_SECRET is not set.
    """
    secret = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "").strip()
    if not secret:
        logger.error("LEMONSQUEEZY_WEBHOOK_SECRET tanımlı değil — webhook imzası doğrulanamıyor.")
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

def _extract_fields(payload: dict) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Extract the five fields we need from a LemonSqueezy webhook payload.

    Returns:
        (event_name, user_id, subscription_id, customer_id, variant_id, status)
        Any value may be None if the key is missing or cannot be coerced.
    """
    meta       = payload.get("meta",       {}) or {}
    data       = payload.get("data",       {}) or {}
    attrs      = data.get("attributes",    {}) or {}
    custom     = meta.get("custom_data",   {}) or {}

    event_name:      str | None = meta.get("event_name")
    user_id:         str | None = custom.get("user_id")
    subscription_id: str | None = str(data["id"]) if data.get("id") is not None else None
    customer_id:     str | None = (
        str(attrs["customer_id"]) if attrs.get("customer_id") is not None else None
    )
    variant_id: str | None = (
        str(attrs["variant_id"]) if attrs.get("variant_id") is not None else None
    )
    status: str | None = attrs.get("status")

    return event_name, user_id, subscription_id, customer_id, variant_id, status


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
) -> Response:
    """Receive LemonSqueezy subscription lifecycle events.

    Always returns HTTP 200 after signature validation so LemonSqueezy stops
    retrying.  Internal errors are logged but not surfaced.
    """
    # ── Read raw body (required for HMAC) ────────────────────────────────
    raw_body: bytes = await request.body()

    # ── Signature check — fail fast with 401 ────────────────────────────
    if not x_signature or not _verify_signature(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Geçersiz webhook imzası.")

    # ── Parse JSON ───────────────────────────────────────────────────────
    try:
        payload: dict = await request.json()
    except Exception as exc:
        logger.error("Webhook JSON ayrıştırılamadı: %s", exc)
        # Return 200 — malformed payload is not retryable
        return Response(status_code=200)

    # ── Extract fields ───────────────────────────────────────────────────
    try:
        event_name, user_id, subscription_id, customer_id, variant_id, status = _extract_fields(payload)
    except Exception as exc:
        logger.error("Webhook alanları çıkarılamadı: %s", exc)
        return Response(status_code=200)

    logger.info("Webhook alındı: event=%s user_id=%s sub=%s", event_name, user_id, subscription_id)

    # ── Guard: user_id is required for all events ─────────────────────────
    if not user_id:
        logger.warning("Webhook custom_data içinde user_id bulunamadı — görmezden geliniyor.")
        return Response(status_code=200)

    # ── Route event ──────────────────────────────────────────────────────
    try:
        if event_name == "subscription_created":
            if subscription_id and customer_id and variant_id:
                activate_plan(user_id, customer_id, subscription_id, variant_id)
            else:
                logger.warning(
                    "subscription_created: eksik alan(lar) — sub=%s customer=%s variant=%s",
                    subscription_id, customer_id, variant_id,
                )

        elif event_name == "subscription_updated":
            # Only activate when the subscription is actually active
            if status == "active" and subscription_id and customer_id and variant_id:
                activate_plan(user_id, customer_id, subscription_id, variant_id)
            elif status in ("cancelled", "expired", "paused", "past_due"):
                cancel_plan(user_id)
            else:
                logger.info("subscription_updated: status=%s — eylem yok.", status)

        elif event_name in ("subscription_cancelled", "subscription_expired"):
            cancel_plan(user_id)

        else:
            logger.info("Bilinmeyen event türü '%s' — görmezden geliniyor.", event_name)

    except Exception as exc:
        # Log but always return 200 — do not let LemonSqueezy retry
        logger.error(
            "Webhook işlenirken hata (event=%s user_id=%s): %s",
            event_name, user_id, exc,
        )

    return Response(status_code=200)
