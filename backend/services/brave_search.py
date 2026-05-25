"""
TwitBoost — Brave Search Service
=================================
Async wrapper around the Brave Web Search API.

Rate-limiting strategy
----------------------
Brave's free tier allows 1 request/second.  A module-level asyncio.Semaphore(1)
serialises concurrent callers so asyncio.gather() in the research agent stays safe.
asyncio.sleep(1) is called *inside* the semaphore block so the lock is held for at
least 1 second, guaranteeing the next caller waits the full interval.

Python 3.12+ note: asyncio primitives are no longer bound to a specific event loop;
the module-level _rate_limiter is lazily created and is safe across test event loops.

API docs: https://api.search.brave.com/app/documentation/web-search
"""

from __future__ import annotations

import asyncio
import os
from typing import TypedDict

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_TIMEOUT = 10.0  # seconds

# Module-level rate limiter — lazily initialised (see _get_rate_limiter).
_rate_limiter: asyncio.Semaphore | None = None


def _get_rate_limiter() -> asyncio.Semaphore:
    """Return (and lazily create) the module-level rate-limit semaphore."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = asyncio.Semaphore(1)
    return _rate_limiter


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class SearchResult(TypedDict):
    title: str
    url: str
    description: str
    date: str | None  # ISO-8601 date string, or None when unavailable


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BraveSearchError(Exception):
    """Raised when the Brave Search API returns an error or an unexpected response."""


class BraveSearchTimeoutError(BraveSearchError):
    """Raised when the Brave Search API request exceeds the timeout threshold."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search(query: str, count: int = 10) -> list[SearchResult]:
    """
    Search the web via the Brave Web Search API.

    Args:
        query:  Search query string.
        count:  Number of results to request (clamped to Brave's max of 20).

    Returns:
        List of :class:`SearchResult` dicts.  Empty list when no results are found.

    Raises:
        EnvironmentError:        ``BRAVE_SEARCH_API_KEY`` is not set in the environment.
        BraveSearchTimeoutError: The request timed out after ``_REQUEST_TIMEOUT`` seconds.
        BraveSearchError:        The API returned a non-200 status or a non-JSON body.
    """
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "BRAVE_SEARCH_API_KEY is not set. "
            "Copy .env.example to .env and fill in your Brave Search API key."
        )

    limiter = _get_rate_limiter()

    async with limiter:
        # ── HTTP request ──────────────────────────────────────────────────
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                response = await client.get(
                    _BRAVE_API_URL,
                    params={"q": query, "count": min(count, 20)},
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": api_key,
                    },
                )
        except httpx.TimeoutException as exc:
            raise BraveSearchTimeoutError(
                f"Brave Search timed out after {_REQUEST_TIMEOUT}s "
                f"for query: {query!r}"
            ) from exc

        # ── Enforce 1 req/sec before releasing the semaphore ──────────────
        await asyncio.sleep(1)

    # ── Validate response (outside semaphore — no I/O here) ───────────────
    if response.status_code != 200:
        raise BraveSearchError(
            f"Brave Search returned HTTP {response.status_code} "
            f"for query {query!r}: {response.text[:300]}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise BraveSearchError(
            f"Brave Search returned a non-JSON body for query {query!r}"
        ) from exc

    web_results: list[dict] = data.get("web", {}).get("results", [])

    if not web_results:
        return []

    results: list[SearchResult] = []
    for item in web_results:
        results.append(
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                description=item.get("description", ""),
                # Brave exposes publication date as "page_age" (ISO string)
                # and relative age as "age" (e.g. "3 months ago").
                date=item.get("page_age") or item.get("age") or None,
            )
        )

    return results
