"""
Tests for services/plan_checker.py

Coverage
--------
check_permission:
  - trial + opposition → allowed (no raise)
  - trial + niche → allowed
  - niche + niche → allowed
  - niche + opposition → HTTP 403
  - opposition + opposition → allowed
  - opposition + niche → HTTP 403
  - full + opposition → allowed
  - full + niche → allowed
  - unknown plan + any mode → HTTP 403 (defaults to empty set)

check_daily_limit:
  - Under limit → allowed
  - Exactly at limit → HTTP 429
  - Over limit → HTTP 429
  - No usage row yet (None) → allowed (counts as 0)
  - DB error → PlanCheckerError

log_usage:
  - Happy path: insert called with correct data
  - DB error: silently swallowed (no raise)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import services.plan_checker as pc
from services.plan_checker import (
    PlanCheckerError,
    check_daily_limit,
    check_permission,
    log_usage,
)


# ---------------------------------------------------------------------------
# check_permission (synchronous — no DB)
# ---------------------------------------------------------------------------


def test_permission_trial_opposition() -> None:
    check_permission("uid", "trial", "opposition")  # must not raise


def test_permission_trial_niche() -> None:
    check_permission("uid", "trial", "niche")


def test_permission_niche_niche() -> None:
    check_permission("uid", "niche", "niche")


def test_permission_niche_opposition_blocked() -> None:
    with pytest.raises(HTTPException) as exc_info:
        check_permission("uid", "niche", "opposition")
    assert exc_info.value.status_code == 403
    assert "Muhalefet" in exc_info.value.detail


def test_permission_opposition_opposition() -> None:
    check_permission("uid", "opposition", "opposition")


def test_permission_opposition_niche_blocked() -> None:
    with pytest.raises(HTTPException) as exc_info:
        check_permission("uid", "opposition", "niche")
    assert exc_info.value.status_code == 403
    assert "Niş" in exc_info.value.detail


def test_permission_full_opposition() -> None:
    check_permission("uid", "full", "opposition")


def test_permission_full_niche() -> None:
    check_permission("uid", "full", "niche")


def test_permission_unknown_plan_blocked() -> None:
    """Unknown plan has empty permissions → 403 for any mode."""
    with pytest.raises(HTTPException) as exc_info:
        check_permission("uid", "unknown_plan", "niche")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# check_daily_limit (async — mocked DB)
# ---------------------------------------------------------------------------


def _mock_usage_client(total_count: int | None) -> MagicMock:
    """Return a mock Supabase client whose daily_usage query returns total_count."""
    mock_resp = MagicMock()
    mock_resp.data = None if total_count is None else {"total_count": total_count}

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_resp
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain
    return mock_client


async def test_daily_limit_under_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """2 requests used, limit is 3 (trial) → no raise."""
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(2))
    await check_daily_limit("uid", "trial", "opposition")  # limit = 3, used = 2 → OK


async def test_daily_limit_exactly_at_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """3 requests used, limit is 3 (trial) → HTTP 429."""
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(3))
    with pytest.raises(HTTPException) as exc_info:
        await check_daily_limit("uid", "trial", "opposition")
    assert exc_info.value.status_code == 429
    assert "3" in exc_info.value.detail  # limit shown in message


async def test_daily_limit_over_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """20 requests used, limit is 20 (niche) → HTTP 429."""
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(20))
    with pytest.raises(HTTPException) as exc_info:
        await check_daily_limit("uid", "niche", "niche")
    assert exc_info.value.status_code == 429


async def test_daily_limit_no_row_yet(monkeypatch: pytest.MonkeyPatch) -> None:
    """No usage_logs row yet (None from DB) → treated as 0 → allowed."""
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(None))
    await check_daily_limit("uid", "full", "opposition")  # limit = 30, used = 0 → OK


async def test_daily_limit_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DB raises unexpected exception → PlanCheckerError."""
    mock_chain = MagicMock()
    mock_chain.execute.side_effect = RuntimeError("DB down")
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(pc, "get_service_client", lambda: mock_client)

    with pytest.raises(PlanCheckerError, match="hata"):
        await check_daily_limit("uid", "trial", "niche")


# ---------------------------------------------------------------------------
# Daily limits per plan
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("plan,limit", [
    ("trial", 3),
    ("niche", 20),
    ("opposition", 15),
    ("full", 30),
])
async def test_daily_limits_values(
    plan: str, limit: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify exact daily limit values for each plan."""
    # At limit → 429
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(limit))
    with pytest.raises(HTTPException) as exc_info:
        await check_daily_limit("uid", plan, "niche")
    assert exc_info.value.status_code == 429

    # One under limit → OK
    monkeypatch.setattr(pc, "get_service_client", lambda: _mock_usage_client(limit - 1))
    await check_daily_limit("uid", plan, "niche")  # no raise


# ---------------------------------------------------------------------------
# log_usage
# ---------------------------------------------------------------------------


async def test_log_usage_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful insert — correct mode and user_id written."""
    mock_chain = MagicMock()
    mock_chain.execute.return_value = MagicMock()
    mock_chain.insert.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(pc, "get_service_client", lambda: mock_client)

    await log_usage("user-abc", "opposition")

    mock_client.table.assert_called_once_with("usage_logs")
    inserted = mock_chain.insert.call_args.args[0]
    assert inserted["user_id"] == "user-abc"
    assert inserted["mode"] == "opposition"


async def test_log_usage_db_error_silenced(monkeypatch: pytest.MonkeyPatch) -> None:
    """DB error during log_usage is swallowed — no exception raised."""
    mock_chain = MagicMock()
    mock_chain.execute.side_effect = RuntimeError("DB connection lost")
    mock_chain.insert.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(pc, "get_service_client", lambda: mock_client)

    await log_usage("user-abc", "niche")  # must not raise
