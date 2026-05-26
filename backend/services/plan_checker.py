"""
Plan checker — permission + daily-limit enforcement.

Two entry points called by routers before executing any analysis:

    check_permission(user_id, plan, mode)  → raises HTTP 403 if plan can't use mode
    check_daily_limit(user_id, plan, mode) → raises HTTP 429 if today's limit hit

Daily limit resets at midnight Istanbul time (UTC+3 / Europe/Istanbul).

Plan limits (from docs/PRD.md §4):
    trial      → 3 total/day, both modes
    niche      → 20/day, niche mode only
    opposition → 15/day, opposition mode only
    full       → 30/day, both modes
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from services.supabase_client import get_service_client

__all__ = [
    "PlanCheckerError",
    "check_permission",
    "check_daily_limit",
    "log_usage",
    "PLAN_PERMISSIONS",
    "DAILY_LIMITS",
]

# ---------------------------------------------------------------------------
# Plan configuration
# ---------------------------------------------------------------------------

# Maps plan → set of allowed modes
PLAN_PERMISSIONS: dict[str, set[str]] = {
    "trial":      {"opposition", "niche"},
    "niche":      {"niche"},
    "opposition": {"opposition"},
    "full":       {"opposition", "niche"},
}

# Maps plan → daily request limit (total across modes for trial/full,
# per-mode for niche/opposition plans since they only have one mode)
DAILY_LIMITS: dict[str, int] = {
    "trial":      3,
    "niche":      20,
    "opposition": 15,
    "full":       30,
}

_ISTANBUL = ZoneInfo("Europe/Istanbul")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PlanCheckerError(Exception):
    """Internal error that couldn't be mapped to an HTTP response."""


# ---------------------------------------------------------------------------
# Permission check (sync — no DB needed)
# ---------------------------------------------------------------------------

def check_permission(user_id: str, plan: str, mode: str) -> None:
    """Raise HTTP 403 if the plan is not allowed to use the requested mode.

    Args:
        user_id: Used only for potential future logging.
        plan:    'trial' | 'niche' | 'opposition' | 'full'
        mode:    'opposition' | 'niche'
    """
    allowed = PLAN_PERMISSIONS.get(plan, set())
    if mode not in allowed:
        _plan_labels = {
            "trial":      "Deneme",
            "niche":      "Niş Modu",
            "opposition": "Muhalefet Modu",
            "full":       "Tam Erişim",
        }
        _mode_labels = {
            "opposition": "Muhalefet Modu",
            "niche":      "Niş Modu",
        }
        plan_tr = _plan_labels.get(plan, plan)
        mode_tr = _mode_labels.get(mode, mode)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"'{plan_tr}' planınız {mode_tr} özelliğini desteklemiyor. "
                "Planınızı yükseltmek için ayarlara gidin."
            ),
        )


# ---------------------------------------------------------------------------
# Daily limit check (async — DB lookup)
# ---------------------------------------------------------------------------

async def check_daily_limit(user_id: str, plan: str, mode: str) -> None:
    """Raise HTTP 429 if the user has hit today's daily request limit.

    Uses the daily_usage view (grouped by Istanbul date).
    Falls back gracefully to 0 if the view returns no row.

    Raises:
        HTTP 429 — limit reached
        PlanCheckerError — unexpected DB error
    """
    limit = DAILY_LIMITS.get(plan, 3)  # default trial limit if unknown plan
    today_istanbul = datetime.now(tz=_ISTANBUL).date().isoformat()

    try:
        client = get_service_client()
        resp = (
            client.table("daily_usage")
            .select("total_count")
            .eq("user_id", user_id)
            .eq("day", today_istanbul)
            .maybe_single()
            .execute()
        )
    except EnvironmentError:
        # Supabase not configured (dev environment) — skip limit check and allow request
        return
    except Exception as exc:
        raise PlanCheckerError(
            f"Günlük kullanım verisi alınırken hata oluştu: {exc}"
        ) from exc

    total_today: int = 0
    if resp.data is not None:
        total_today = int(resp.data.get("total_count", 0))

    if total_today >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Bugünkü kullanım limitinize ({limit} istek) ulaştınız. "
                "Limit her gece yarısı İstanbul saatiyle sıfırlanır."
            ),
        )


# ---------------------------------------------------------------------------
# Usage logging (called after successful analysis)
# ---------------------------------------------------------------------------

async def log_usage(user_id: str, mode: str) -> None:
    """Insert a usage_logs row for the completed request.

    Called server-side after a successful analysis — never trust frontend
    to report its own usage.

    Silently ignores DB errors (don't fail the response for a logging fault).
    """
    try:
        client = get_service_client()
        client.table("usage_logs").insert(
            {"user_id": user_id, "mode": mode}
        ).execute()
    except Exception:
        # Logging failure is non-fatal — the analysis already succeeded
        pass
