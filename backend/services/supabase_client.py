"""
Supabase client — singleton pattern.

Provides two clients:
- `get_anon_client()`          — uses SUPABASE_ANON_KEY (public operations)
- `get_service_client()`       — uses SUPABASE_SERVICE_ROLE_KEY (server-side writes)

Both raise EnvironmentError if the required env vars are missing.
Call `get_service_client()` for usage_logs writes and user lookups.
Never expose the service role key to the frontend.
"""

from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client

__all__ = ["get_anon_client", "get_service_client"]


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EnvironmentError(
            f"{name} ortam değişkeni tanımlı değil. "
            f"Lütfen .env dosyasını kontrol edin."
        )
    return value


@lru_cache(maxsize=1)
def get_anon_client() -> Client:
    """Return a cached Supabase client using the public anon key."""
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    """Return a cached Supabase client using the service role key.

    This client bypasses Row Level Security — use only for trusted
    server-side operations (usage logging, user look-ups).
    Never pass this client to anything that could be influenced by
    user-supplied data.
    """
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)
