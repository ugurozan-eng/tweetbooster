"""
Tests for routers/webhooks.py

Coverage
--------
- Valid signature + subscription_created  → activate_plan called
- Valid signature + subscription_updated (active) → activate_plan called
- Valid signature + subscription_updated (cancelled) → cancel_plan called
- Valid signature + subscription_cancelled → cancel_plan called
- Valid signature + subscription_expired  → cancel_plan called
- Valid signature + unknown event         → 200, no plan function called
- Invalid signature                       → HTTP 401
- Missing X-Signature header              → HTTP 401
- Missing LEMONSQUEEZY_WEBHOOK_SECRET     → HTTP 401
- Missing user_id in custom_data          → 200, no plan function called
- Internal error in activate_plan         → HTTP 200 (never retry)
- Valid signature + subscription_updated (paused) → cancel_plan called
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    import os
    os.environ.setdefault("LEMONSQUEEZY_WEBHOOK_SECRET", "test-webhook-secret")
    from main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECRET = "test-webhook-secret"


def _sign(body: bytes, secret: str = _SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _payload(
    event_name: str,
    status: str = "active",
    user_id: str = "user-uuid-1",
    sub_id: str = "sub-123",
    customer_id: str = "cust-456",
    variant_id: str = "variant-789",
) -> dict:
    return {
        "meta": {
            "event_name": event_name,
            "custom_data": {"user_id": user_id},
        },
        "data": {
            "id": sub_id,
            "attributes": {
                "status":      status,
                "customer_id": customer_id,
                "variant_id":  variant_id,
            },
        },
    }


def _post(client, payload: dict, secret: str = _SECRET, header: str | None = None):
    body = json.dumps(payload).encode()
    sig  = _sign(body, secret) if header is None else header
    headers = {"X-Signature": sig} if sig is not None else {}
    return client.post("/api/webhooks/lemonsqueezy", content=body, headers=headers)


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------

class TestSignatureValidation:

    def test_invalid_signature_returns_401(self, client):
        p = _payload("subscription_created")
        resp = _post(client, p, secret="wrong-secret")
        assert resp.status_code == 401

    def test_missing_signature_header_returns_401(self, client):
        body = json.dumps(_payload("subscription_created")).encode()
        resp = client.post(
            "/api/webhooks/lemonsqueezy",
            content=body,
            headers={},          # no X-Signature
        )
        assert resp.status_code == 401

    def test_missing_webhook_secret_env_returns_401(self, client, monkeypatch):
        monkeypatch.delenv("LEMONSQUEEZY_WEBHOOK_SECRET", raising=False)
        # Need to reload module so it picks up missing env var
        import importlib
        import routers.webhooks as wh
        importlib.reload(wh)
        p = _payload("subscription_created")
        resp = _post(client, p)
        assert resp.status_code == 401
        # Restore
        monkeypatch.setenv("LEMONSQUEEZY_WEBHOOK_SECRET", _SECRET)
        importlib.reload(wh)


# ---------------------------------------------------------------------------
# Event routing
# ---------------------------------------------------------------------------

class TestEventRouting:

    def test_subscription_created_calls_activate(self, client):
        p = _payload("subscription_created")
        with patch("routers.webhooks.activate_plan") as mock_activate:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_activate.assert_called_once_with(
            "user-uuid-1", "cust-456", "sub-123", "variant-789"
        )

    def test_subscription_updated_active_calls_activate(self, client):
        p = _payload("subscription_updated", status="active")
        with patch("routers.webhooks.activate_plan") as mock_activate:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_activate.assert_called_once()

    def test_subscription_updated_cancelled_calls_cancel(self, client):
        p = _payload("subscription_updated", status="cancelled")
        with patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_cancel.assert_called_once_with("user-uuid-1")

    def test_subscription_updated_paused_calls_cancel(self, client):
        p = _payload("subscription_updated", status="paused")
        with patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_cancel.assert_called_once_with("user-uuid-1")

    def test_subscription_cancelled_calls_cancel(self, client):
        p = _payload("subscription_cancelled")
        with patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_cancel.assert_called_once_with("user-uuid-1")

    def test_subscription_expired_calls_cancel(self, client):
        p = _payload("subscription_expired")
        with patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_cancel.assert_called_once_with("user-uuid-1")

    def test_unknown_event_returns_200_no_call(self, client):
        p = _payload("order_created")
        with patch("routers.webhooks.activate_plan") as mock_activate, \
             patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_activate.assert_not_called()
        mock_cancel.assert_not_called()


# ---------------------------------------------------------------------------
# Reliability — internal errors must not trigger retries
# ---------------------------------------------------------------------------

class TestReliability:

    def test_internal_error_still_returns_200(self, client):
        """If activate_plan raises, the endpoint still returns 200."""
        p = _payload("subscription_created")
        with patch("routers.webhooks.activate_plan", side_effect=RuntimeError("DB kaboom")):
            resp = _post(client, p)
        assert resp.status_code == 200

    def test_missing_user_id_returns_200_no_action(self, client):
        """Missing user_id in custom_data → 200, no plan call."""
        p = _payload("subscription_created", user_id=None)
        p["meta"]["custom_data"] = {}        # no user_id key at all
        with patch("routers.webhooks.activate_plan") as mock_activate, \
             patch("routers.webhooks.cancel_plan") as mock_cancel:
            resp = _post(client, p)
        assert resp.status_code == 200
        mock_activate.assert_not_called()
        mock_cancel.assert_not_called()
