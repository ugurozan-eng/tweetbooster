"""
Tests for services/subscription_service.py

Coverage
--------
- activate_plan: upserts correct row with plan name, IDs, and expiry date
- activate_plan: unknown variant_id falls back to "full"
- activate_plan: DB error → SubscriptionServiceError
- cancel_plan:   clears subscription fields and sets plan = "trial"
- cancel_plan:   DB error → SubscriptionServiceError
- get_active_plan: active plan returned unchanged
- get_active_plan: plan_expires_at in the past → cancel_plan called, "trial" returned
- get_active_plan: plan_expires_at in the future → plan returned unchanged
- get_active_plan: user row not found → "trial" returned
- get_active_plan: DB error → SubscriptionServiceError
- get_active_plan: malformed plan_expires_at → treated as expired → "trial"
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_supabase_mock() -> MagicMock:
    """Return a mock that mimics supabase.Client's chainable query builder."""
    mock = MagicMock()
    # Make every builder method return the mock itself so chains work
    mock.table.return_value = mock
    mock.upsert.return_value = mock
    mock.update.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.maybe_single.return_value = mock
    mock.execute.return_value = MagicMock(data=None)
    return mock


# ---------------------------------------------------------------------------
# activate_plan
# ---------------------------------------------------------------------------

class TestActivatePlan:

    def test_activate_plan_known_variant(self, monkeypatch):
        """Upserts with correct plan name when variant is in env."""
        monkeypatch.setenv("LEMONSQUEEZY_VARIANT_NICHE_ID",      "111")
        monkeypatch.setenv("LEMONSQUEEZY_VARIANT_OPPOSITION_ID", "222")
        monkeypatch.setenv("LEMONSQUEEZY_VARIANT_FULL_ID",       "333")

        supabase_mock = _make_supabase_mock()
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import activate_plan
            activate_plan(
                user_id="user-1",
                customer_id="cust-99",
                subscription_id="sub-77",
                variant_id="111",  # → "niche"
            )

        upsert_call = supabase_mock.upsert.call_args
        data: dict = upsert_call.args[0]
        assert data["plan"] == "niche"
        assert data["lemonsqueezy_customer_id"] == "cust-99"
        assert data["lemonsqueezy_subscription_id"] == "sub-77"
        assert data["id"] == "user-1"
        # Expiry should be in the future (≈31 days out)
        expires_dt = datetime.fromisoformat(data["plan_expires_at"])
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        assert expires_dt > now + timedelta(days=29)
        assert expires_dt < now + timedelta(days=33)

    def test_activate_plan_unknown_variant_defaults_full(self, monkeypatch):
        """Unknown variant ID defaults to 'full'."""
        monkeypatch.delenv("LEMONSQUEEZY_VARIANT_NICHE_ID",      raising=False)
        monkeypatch.delenv("LEMONSQUEEZY_VARIANT_OPPOSITION_ID", raising=False)
        monkeypatch.delenv("LEMONSQUEEZY_VARIANT_FULL_ID",       raising=False)

        supabase_mock = _make_supabase_mock()
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import activate_plan
            activate_plan("user-2", "cust-1", "sub-1", "unknown-variant-999")

        data = supabase_mock.upsert.call_args.args[0]
        assert data["plan"] == "full"

    def test_activate_plan_db_error_raises(self, monkeypatch):
        """DB failure → SubscriptionServiceError."""
        monkeypatch.setenv("LEMONSQUEEZY_VARIANT_NICHE_ID", "111")

        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.side_effect = RuntimeError("DB down")
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import (
                SubscriptionServiceError,
                activate_plan,
            )
            with pytest.raises(SubscriptionServiceError):
                activate_plan("user-3", "c", "s", "111")


# ---------------------------------------------------------------------------
# cancel_plan
# ---------------------------------------------------------------------------

class TestCancelPlan:

    def test_cancel_plan_clears_fields(self):
        """Sets plan='trial' and clears subscription fields."""
        supabase_mock = _make_supabase_mock()
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import cancel_plan
            cancel_plan("user-4")

        update_call = supabase_mock.update.call_args
        data: dict = update_call.args[0]
        assert data["plan"] == "trial"
        assert data["lemonsqueezy_subscription_id"] is None
        assert data["plan_expires_at"] is None
        # eq("id", "user-4") was called
        supabase_mock.eq.assert_called_with("id", "user-4")

    def test_cancel_plan_db_error_raises(self):
        """DB failure → SubscriptionServiceError."""
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.side_effect = RuntimeError("DB down")
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import (
                SubscriptionServiceError,
                cancel_plan,
            )
            with pytest.raises(SubscriptionServiceError):
                cancel_plan("user-5")


# ---------------------------------------------------------------------------
# get_active_plan
# ---------------------------------------------------------------------------

class TestGetActivePlan:

    def test_returns_plan_when_not_expired(self):
        """Returns the stored plan when plan_expires_at is in the future."""
        future = (datetime.now(tz=timezone.utc) + timedelta(days=15)).isoformat()
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.return_value = MagicMock(
            data={"plan": "niche", "plan_expires_at": future}
        )
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import get_active_plan
            plan = get_active_plan("user-6")

        assert plan == "niche"

    def test_auto_downgrades_when_expired(self):
        """When plan_expires_at is in the past, cancel_plan is called and 'trial' returned."""
        past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
        supabase_mock = _make_supabase_mock()
        # First execute() = select query; subsequent calls = update (cancel)
        supabase_mock.execute.return_value = MagicMock(
            data={"plan": "opposition", "plan_expires_at": past}
        )
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import get_active_plan
            plan = get_active_plan("user-7")

        assert plan == "trial"
        # update() must have been called (cancel_plan path)
        supabase_mock.update.assert_called_once()

    def test_returns_trial_when_no_row(self):
        """Returns 'trial' when user row does not exist."""
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.return_value = MagicMock(data=None)
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import get_active_plan
            plan = get_active_plan("user-8")

        assert plan == "trial"

    def test_returns_trial_when_no_expiry(self):
        """Returns the plan when plan_expires_at is NULL (never-expiring row)."""
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.return_value = MagicMock(
            data={"plan": "full", "plan_expires_at": None}
        )
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import get_active_plan
            plan = get_active_plan("user-9")

        assert plan == "full"

    def test_malformed_expiry_treated_as_expired(self):
        """Malformed plan_expires_at string → treated as expired → 'trial'."""
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.return_value = MagicMock(
            data={"plan": "niche", "plan_expires_at": "not-a-date"}
        )
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import get_active_plan
            plan = get_active_plan("user-10")

        assert plan == "trial"

    def test_db_error_raises(self):
        """DB failure on select → SubscriptionServiceError."""
        supabase_mock = _make_supabase_mock()
        supabase_mock.execute.side_effect = RuntimeError("DB down")
        with patch("services.subscription_service.get_service_client", return_value=supabase_mock):
            from services.subscription_service import (
                SubscriptionServiceError,
                get_active_plan,
            )
            with pytest.raises(SubscriptionServiceError):
                get_active_plan("user-11")
