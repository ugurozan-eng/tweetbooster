"""
Tests for services/brave_search.py

Coverage
--------
- Happy path: 200 response with results
- Zero results: 200 response with empty results list
- Timeout: httpx raises TimeoutException
- Non-200 response: API returns 429 / 500
- Missing API key: EnvironmentError raised before any HTTP call
- Rate-limit delay: asyncio.sleep(1) is called once per request
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from services.brave_search import (
    BraveSearchError,
    BraveSearchTimeoutError,
    search,
)

_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure BRAVE_SEARCH_API_KEY is always present in these tests."""
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-brave-key-abc")


@pytest.fixture()
def mock_sleep(mocker) -> AsyncMock:
    """Patch asyncio.sleep so tests don't actually wait 1 second each."""
    return mocker.patch("services.brave_search.asyncio.sleep", new_callable=AsyncMock)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_returns_results(mock_sleep: AsyncMock) -> None:
    """Returns a list of SearchResult dicts when API responds with results."""
    respx.get(_BRAVE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": "Ahmet Yılmaz Açıklaması",
                            "url": "https://example.com/haber/1",
                            "description": "Ahmet Yılmaz bugün açıkladı...",
                            "page_age": "2024-03-15T00:00:00",
                        },
                        {
                            "title": "İkinci Haber",
                            "url": "https://example.com/haber/2",
                            "description": "Devam eden gelişmeler...",
                            "page_age": None,
                            "age": "2 months ago",
                        },
                    ]
                }
            },
        )
    )

    results = await search("Ahmet Yılmaz açıklama")

    assert len(results) == 2
    assert results[0]["title"] == "Ahmet Yılmaz Açıklaması"
    assert results[0]["url"] == "https://example.com/haber/1"
    assert results[0]["description"] == "Ahmet Yılmaz bugün açıkladı..."
    assert results[0]["date"] == "2024-03-15T00:00:00"
    # Second result: page_age is None, falls back to "age"
    assert results[1]["date"] == "2 months ago"

    # Rate-limit sleep must be called exactly once
    mock_sleep.assert_awaited_once_with(1)


# ---------------------------------------------------------------------------
# Zero results
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_zero_results(mock_sleep: AsyncMock) -> None:
    """Returns an empty list when the API finds no results."""
    respx.get(_BRAVE_URL).mock(
        return_value=httpx.Response(
            200,
            json={"web": {"results": []}},
        )
    )

    results = await search("xyzzy impossible query 99999")

    assert results == []
    mock_sleep.assert_awaited_once_with(1)


@respx.mock
async def test_search_missing_web_key(mock_sleep: AsyncMock) -> None:
    """Returns empty list when response JSON has no 'web' key."""
    respx.get(_BRAVE_URL).mock(
        return_value=httpx.Response(200, json={"type": "search"})
    )

    results = await search("anything")
    assert results == []


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_timeout_raises(mock_sleep: AsyncMock) -> None:
    """Raises BraveSearchTimeoutError when the HTTP request times out."""
    respx.get(_BRAVE_URL).mock(side_effect=httpx.TimeoutException("read timed out"))

    with pytest.raises(BraveSearchTimeoutError, match="timed out"):
        await search("some query")

    # sleep should NOT be called — we never reached it
    mock_sleep.assert_not_awaited()


# ---------------------------------------------------------------------------
# Non-200 responses
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_429_raises(mock_sleep: AsyncMock) -> None:
    """Raises BraveSearchError when the API returns HTTP 429."""
    respx.get(_BRAVE_URL).mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )

    with pytest.raises(BraveSearchError, match="HTTP 429"):
        await search("test")


@respx.mock
async def test_search_500_raises(mock_sleep: AsyncMock) -> None:
    """Raises BraveSearchError when the API returns HTTP 500."""
    respx.get(_BRAVE_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(BraveSearchError, match="HTTP 500"):
        await search("test")


# ---------------------------------------------------------------------------
# Missing API key
# ---------------------------------------------------------------------------


async def test_search_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises EnvironmentError before making any HTTP call when key is absent."""
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="BRAVE_SEARCH_API_KEY"):
        await search("test")


async def test_search_empty_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises EnvironmentError when key is an empty string."""
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "   ")

    with pytest.raises(EnvironmentError, match="BRAVE_SEARCH_API_KEY"):
        await search("test")
