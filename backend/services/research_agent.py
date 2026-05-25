"""
TwitBoost — Research Agent
===========================
Runs four parallel Brave Search queries for a named person, merges the
results, deduplicates by URL, and returns a single consolidated source list.

Parallelism & rate-limiting
----------------------------
``asyncio.gather`` starts all four queries concurrently from the caller's
perspective, but the module-level ``asyncio.Semaphore(1)`` inside
``brave_search.search()`` ensures the actual HTTP requests are serialised at
1 request/second.  This satisfies both requirements:
  • fast (non-blocking from the caller's perspective)
  • rate-limit-safe (Brave free tier: 1 req/sec)

Resilience
----------
``asyncio.gather(return_exceptions=True)`` means a single failing query
(timeout, 429, etc.) does NOT abort the entire pipeline.  Partial results
from the other three queries are still returned; the failed query is skipped
and logged to stderr.
"""

from __future__ import annotations

import asyncio
import sys
from typing import TypedDict

from services.brave_search import search, SearchResult

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class ResearchResult(TypedDict):
    url: str
    title: str
    description: str
    date: str | None
    query_source: str  # "A" | "B" | "C" | "D"  — which query surfaced this URL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_research(name: str, topic: str) -> list[ResearchResult]:
    """
    Run four parallel Brave Search queries for ``name`` and ``topic``.

    Queries
    -------
    A — ``"{name} açıklama beyanat"``         (past public statements)
    B — ``"{name} twitter"``                   (Twitter presence via web)
    C — ``"{name} çelişki tutarsızlık"``       (contradictions / inconsistencies)
    D — ``"{name} {topic}"``                   (topic-specific history)

    Args:
        name:  Person's full name (from :func:`~services.person_identifier.identify_person`).
        topic: Tweet topic in Turkish (from the same source).

    Returns:
        Deduplicated list of :class:`ResearchResult`.  Results from query A come
        first, then B, C, D; duplicate URLs are dropped (first occurrence wins).
        Returns an empty list if all queries fail or return nothing.

    Raises:
        EnvironmentError: ``BRAVE_SEARCH_API_KEY`` is not set (propagated from
        ``brave_search.search`` before the first HTTP call).
    """
    queries: list[tuple[str, str]] = [
        (f"{name} açıklama beyanat",   "A"),
        (f"{name} twitter",             "B"),
        (f"{name} çelişki tutarsızlık", "C"),
        (f"{name} {topic}",             "D"),
    ]

    # Fire all four queries concurrently; brave_search serialises internally.
    # return_exceptions=True: a single failing query yields a BaseException
    # object in the results list rather than aborting gather().
    raw: list[list[SearchResult] | BaseException] = await asyncio.gather(
        *[search(q) for q, _ in queries],
        return_exceptions=True,
    )

    # Merge + deduplicate by URL (first occurrence wins)
    seen_urls: set[str] = set()
    merged: list[ResearchResult] = []

    for (query_str, label), outcome in zip(queries, raw):
        if isinstance(outcome, BaseException):
            # Log failed query but don't abort — return partial results
            print(
                f"[research_agent] query {label} failed "
                f"({type(outcome).__name__}: {outcome}) — skipping",
                file=sys.stderr,
            )
            continue

        for item in outcome:
            url = item["url"]
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(
                    ResearchResult(
                        url=url,
                        title=item["title"],
                        description=item["description"],
                        date=item["date"],
                        query_source=label,
                    )
                )

    return merged
