"""
TwitBoost — LemonSqueezy API Client
=====================================
Singleton httpx.AsyncClient for all LemonSqueezy REST calls.

Public API:
    get_subscription(subscription_id)                               → raw dict
    create_checkout(store_id, variant_id, user_email, user_id)      → checkout_url str

The client is lazily initialised on first use and re-used across requests.
Reset _client = None between tests to force re-initialisation.
"""

from __future__ import annotations

import os

import httpx

__all__ = [
    "LemonSqueezyError",
    "get_subscription",
    "create_checkout",
    "_reset_client",   # exposed for test isolation
]

_BASE_URL = "https://api.lemonsqueezy.com/v1"

# Module-level singleton — reset between tests via _reset_client()
_client: httpx.AsyncClient | None = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LemonSqueezyError(Exception):
    """Raised when the LemonSqueezy API returns an error or is unreachable."""


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

def _get_client() -> httpx.AsyncClient:
    """Return the module-level AsyncClient, creating it on first call."""
    global _client
    if _client is None:
        api_key = os.environ.get("LEMONSQUEEZY_API_KEY", "").strip()
        if not api_key:
            raise EnvironmentError(
                "LEMONSQUEEZY_API_KEY is not set. "
                "Copy .env.example to .env and fill in your LemonSqueezy API key."
            )
        _client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            timeout=30.0,
        )
    return _client


def _reset_client() -> None:
    """Discard the cached client. Call this in test teardown."""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_subscription(subscription_id: str) -> dict:
    """Fetch a subscription object from LemonSqueezy.

    Args:
        subscription_id: The LemonSqueezy subscription ID (numeric string).

    Returns:
        The full JSON response dict (``{"data": {...}, "links": {...}}``)

    Raises:
        EnvironmentError:      API key not set.
        LemonSqueezyError:     HTTP error or network failure.
    """
    client = _get_client()
    try:
        resp = await client.get(f"/subscriptions/{subscription_id}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise LemonSqueezyError(
            f"LemonSqueezy API error fetching subscription {subscription_id}: "
            f"HTTP {exc.response.status_code} — {exc.response.text[:200]}"
        ) from exc
    except httpx.RequestError as exc:
        raise LemonSqueezyError(
            f"Network error fetching subscription {subscription_id}: {exc}"
        ) from exc


async def create_checkout(
    store_id: str,
    variant_id: str,
    user_email: str,
    user_id: str,
) -> str:
    """Create a LemonSqueezy hosted checkout and return the checkout URL.

    The ``user_id`` is passed as ``custom_data`` so the webhook can identify
    which user completed the purchase.

    Args:
        store_id:    LemonSqueezy store ID (from LEMONSQUEEZY_STORE_ID).
        variant_id:  Product variant ID for the chosen plan.
        user_email:  Pre-fill the checkout form with the user's email.
        user_id:     Our internal user UUID — forwarded in webhook custom_data.

    Returns:
        Hosted checkout URL string (redirect the browser here).

    Raises:
        EnvironmentError:      API key not set.
        LemonSqueezyError:     API returned an error or unexpected response shape.
    """
    client = _get_client()
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {"user_id": user_id},
                },
            },
            "relationships": {
                "store": {
                    "data": {"type": "stores", "id": str(store_id)},
                },
                "variant": {
                    "data": {"type": "variants", "id": str(variant_id)},
                },
            },
        }
    }
    try:
        resp = await client.post("/checkouts", json=payload)
        resp.raise_for_status()
        data = resp.json()
        url: str = data["data"]["attributes"]["url"]
        return url
    except (KeyError, TypeError) as exc:
        raise LemonSqueezyError(
            f"Unexpected response shape from LemonSqueezy checkout API: {exc}"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise LemonSqueezyError(
            f"LemonSqueezy checkout API error: "
            f"HTTP {exc.response.status_code} — {exc.response.text[:200]}"
        ) from exc
    except httpx.RequestError as exc:
        raise LemonSqueezyError(
            f"Network error creating LemonSqueezy checkout: {exc}"
        ) from exc
