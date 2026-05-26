"""
Shared pytest fixtures for TwitBoost backend tests.
"""

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(autouse=True)
def reset_brave_rate_limiter():
    """Reset the brave_search module-level rate-limiter between tests."""
    import services.brave_search as bs

    bs._rate_limiter = None
    yield
    bs._rate_limiter = None


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Reset the auth_service JWKS cache between tests.

    Prevents a monkeypatched _fetch_jwks from one test leaking into the next.
    """
    import services.auth_service as aa

    aa._jwks_cache = None
    aa._jwks_cache_expiry = 0.0
    yield
    aa._jwks_cache = None
    aa._jwks_cache_expiry = 0.0
