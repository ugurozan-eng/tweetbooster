"""
Shared pytest fixtures for TwitBoost backend tests.
"""

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(autouse=True)
def reset_brave_rate_limiter():
    """
    Reset the brave_search module-level rate-limiter between tests.

    Each test gets a fresh Semaphore so there are no cross-test ordering
    effects and no semaphore state leaked from a previously failed test.
    """
    import services.brave_search as bs

    bs._rate_limiter = None
    yield
    bs._rate_limiter = None
