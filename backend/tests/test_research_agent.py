"""
Tests for services/research_agent.py

Coverage
--------
- Happy path: 4 queries return results → merged list returned
- Deduplication: same URL in multiple query results → only first kept
- query_source label: each result carries the correct A/B/C/D label
- Partial failure: one query raises an exception → other results still returned
- All queries fail: returns empty list (no crash)
- Parallel execution: asyncio.gather is used (all 4 search calls initiated)
- Query strings: correct Turkish query strings built from name + topic
"""

from __future__ import annotations

from unittest.mock import AsyncMock, call, patch

import pytest

from services.research_agent import ResearchResult, run_research


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(url: str, title: str = "Title", query_source: str = "A"):
    """Build a minimal SearchResult dict for test fixtures."""
    return {"title": title, "url": url, "description": "Açıklama.", "date": "2024-01-01"}


def _patch_search(monkeypatch: pytest.MonkeyPatch, side_effects: list):
    """
    Replace services.brave_search.search with an AsyncMock whose successive
    return values are given by ``side_effects``.

    Each element can be:
    - a list[dict]  → returned as the query result
    - an Exception  → raised as if the search failed
    """
    call_index = 0
    results = side_effects

    async def fake_search(query: str, count: int = 10):
        nonlocal call_index
        effect = results[call_index]
        call_index += 1
        if isinstance(effect, BaseException):
            raise effect
        return effect

    mock = AsyncMock(side_effect=fake_search)
    monkeypatch.setattr("services.research_agent.search", mock)
    return mock


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_run_research_merges_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """All four queries return results; merged list contains all unique URLs."""
    mock = _patch_search(
        monkeypatch,
        [
            [_make_result("https://a.com/1"), _make_result("https://a.com/2")],  # A
            [_make_result("https://b.com/1")],                                   # B
            [_make_result("https://c.com/1")],                                   # C
            [_make_result("https://d.com/1")],                                   # D
        ],
    )

    results = await run_research("Ahmet Yılmaz", "ekonomi politikası")

    assert len(results) == 5
    urls = [r["url"] for r in results]
    assert "https://a.com/1" in urls
    assert "https://b.com/1" in urls
    assert "https://c.com/1" in urls
    assert "https://d.com/1" in urls


async def test_run_research_query_source_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each result carries the label of the query that first found it."""
    _patch_search(
        monkeypatch,
        [
            [_make_result("https://a.com/1")],  # A
            [_make_result("https://b.com/1")],  # B
            [_make_result("https://c.com/1")],  # C
            [_make_result("https://d.com/1")],  # D
        ],
    )

    results = await run_research("Test Kişi", "siyaset")

    labels = {r["url"]: r["query_source"] for r in results}
    assert labels["https://a.com/1"] == "A"
    assert labels["https://b.com/1"] == "B"
    assert labels["https://c.com/1"] == "C"
    assert labels["https://d.com/1"] == "D"


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


async def test_run_research_deduplication(monkeypatch: pytest.MonkeyPatch) -> None:
    """URLs that appear in multiple query results are kept only once (first wins)."""
    duplicate_url = "https://shared.com/article"

    _patch_search(
        monkeypatch,
        [
            [_make_result(duplicate_url, title="From A")],  # A — first occurrence
            [_make_result(duplicate_url, title="From B")],  # B — duplicate, must be dropped
            [_make_result("https://unique.com/1")],          # C
            [],                                              # D — empty
        ],
    )

    results = await run_research("Test", "konu")

    urls = [r["url"] for r in results]
    assert urls.count(duplicate_url) == 1

    # The A-result (first occurrence) must win
    dup = next(r for r in results if r["url"] == duplicate_url)
    assert dup["query_source"] == "A"
    assert dup["title"] == "From A"


async def test_run_research_empty_urls_excluded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Results with an empty URL string are silently excluded."""
    _patch_search(
        monkeypatch,
        [
            [{"title": "No URL", "url": "", "description": "X", "date": None}],
            [], [], [],
        ],
    )

    results = await run_research("Test", "konu")
    assert results == []


# ---------------------------------------------------------------------------
# Resilience — partial failures
# ---------------------------------------------------------------------------


async def test_run_research_one_query_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """One failing query does not abort the pipeline; other results are returned."""
    from services.brave_search import BraveSearchTimeoutError

    _patch_search(
        monkeypatch,
        [
            [_make_result("https://a.com/1")],              # A — OK
            BraveSearchTimeoutError("query B timed out"),   # B — fail
            [_make_result("https://c.com/1")],              # C — OK
            [_make_result("https://d.com/1")],              # D — OK
        ],
    )

    results = await run_research("Test", "konu")

    assert len(results) == 3
    urls = [r["url"] for r in results]
    assert "https://a.com/1" in urls
    assert "https://c.com/1" in urls
    assert "https://d.com/1" in urls


async def test_run_research_all_queries_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns an empty list (not an exception) when all 4 queries fail."""
    from services.brave_search import BraveSearchError

    _patch_search(
        monkeypatch,
        [
            BraveSearchError("fail A"),
            BraveSearchError("fail B"),
            BraveSearchError("fail C"),
            BraveSearchError("fail D"),
        ],
    )

    results = await run_research("Test", "konu")
    assert results == []


# ---------------------------------------------------------------------------
# Parallel execution & query strings
# ---------------------------------------------------------------------------


async def test_run_research_calls_search_4_times(monkeypatch: pytest.MonkeyPatch) -> None:
    """search() is called exactly 4 times (once per query)."""
    mock = _patch_search(monkeypatch, [[], [], [], []])

    await run_research("Ali Veli", "futbol")

    assert mock.await_count == 4


async def test_run_research_query_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    """The correct Turkish query strings are passed to search()."""
    mock = _patch_search(monkeypatch, [[], [], [], []])

    await run_research("Ahmet Yılmaz", "ekonomi")

    called_queries = [c.args[0] for c in mock.await_args_list]
    assert called_queries[0] == "Ahmet Yılmaz açıklama beyanat"
    assert called_queries[1] == "Ahmet Yılmaz twitter"
    assert called_queries[2] == "Ahmet Yılmaz çelişki tutarsızlık"
    assert called_queries[3] == "Ahmet Yılmaz ekonomi"
