"""
TwitBoost — Niche Agent
========================
Two entry-points:

  ``get_trending(niche_id, hours)``
      Search Brave for trending tweets in the given niche, then score and
      rank them with Gemini 2.5 Pro.  Returns a list of ``ScoredTweet`` dicts.

  ``generate_reply(tweet_text, niche_id)``
      Generate three engagement-optimised Turkish replies for a tweet in
      the given niche.  Each reply is run through the legal-safety filter
      before being returned.  Raises ``NicheReplyBlockedError`` if all
      three are blocked.

Design notes
------------
- Niche config is always fetched from ``config.niches.get_niche()`` — no
  niche identifiers are hardcoded here.
- System prompts live in ``backend/prompts/``.  Placeholders use
  ``{{double_braces}}`` so they cannot accidentally collide with Python
  f-string or Jinja syntax.
- Legal-safety filter runs AFTER generation, per COMMON_MISTAKES.md.
- Gemini API calls are capped at 1 500 output tokens (scorer) and 800
  tokens (reply generator) to stay within budget.
- ``asyncio.gather(return_exceptions=True)`` is used wherever parallel
  Brave calls happen so a single failure doesn't abort the whole request.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import TypedDict

from google import genai
from google.genai import types

from config.niches import get_niche
from services.brave_search import search
from services.legal_safety_filter import check_reply

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-pro"
_SCORER_MAX_TOKENS = 1500
_REPLY_MAX_TOKENS = 800
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# How many Brave results to fetch per search query.
_RESULTS_PER_QUERY = 10

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class ScoredTweet(TypedDict):
    url: str
    text: str
    score: int       # 0–10
    reason: str      # Turkish, ≤20 words


class NicheReply(TypedDict):
    text: str
    hook_type: str   # "question" | "opinion" | "fact"


class NicheAgentError(Exception):
    """Raised for unrecoverable errors inside the niche agent."""


class NicheReplyBlockedError(NicheAgentError):
    """Raised when all generated replies are blocked by the legal-safety filter."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_prompt(filename: str) -> str:
    """Load a system prompt from the prompts directory."""
    path = _PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise NicheAgentError(
            f"Prompt dosyası bulunamadı: {path}. "
            "Lütfen backend/prompts/ dizinini kontrol edin."
        )


def _fill_template(template: str, **kwargs: str) -> str:
    """Replace ``{{key}}`` placeholders in *template* with *kwargs* values."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


def _parse_json_response(raw: str, context: str) -> dict:
    """
    Parse a JSON string from Gemini, stripping any markdown code fences.

    Args:
        raw: Raw text from Gemini's response.
        context: Short description used in error messages.

    Raises:
        NicheAgentError: If the text cannot be parsed as JSON.
    """
    text = raw.strip()
    if text.startswith("```"):
        # Strip ```json ... ``` or ``` ... ```
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise NicheAgentError(
            f"Gemini yanıtı JSON olarak çözümlenemedi ({context}): {exc}. "
            f"Ham yanıt: {raw[:200]}"
        )


def _build_tweets_json(search_results: list[dict]) -> str:
    """
    Convert a flat list of Brave search results into the JSON block that
    the scorer prompt expects.
    """
    items = [
        {
            "url": r.get("url", ""),
            "text": (r.get("description") or r.get("title") or "")[:200],
        }
        for r in search_results
        if r.get("url")
    ]
    return json.dumps(items, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Stage 1 — collect raw results from Brave
# ---------------------------------------------------------------------------


async def _fetch_search_results(niche_id: str) -> list[dict]:
    """
    Run all search queries for the given niche in parallel and return a
    deduplicated list of Brave results.
    """
    niche = get_niche(niche_id)  # raises ValueError for unknown niche_id
    queries = niche["search_queries"]

    raw_results = await asyncio.gather(
        *[search(q, count=_RESULTS_PER_QUERY) for q in queries],
        return_exceptions=True,
    )

    seen_urls: set[str] = set()
    merged: list[dict] = []
    for batch in raw_results:
        if isinstance(batch, Exception):
            # Log as warning but continue — other queries may have succeeded.
            continue
        for item in batch:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)

    return merged


# ---------------------------------------------------------------------------
# Stage 2 — score with Gemini
# ---------------------------------------------------------------------------


async def _score_tweets(
    search_results: list[dict],
    niche_id: str,
    client: genai.Client,
) -> list[ScoredTweet]:
    """
    Ask Gemini to score each search result and return them sorted by score
    descending.

    Returns an empty list if *search_results* is empty.
    """
    if not search_results:
        return []

    niche = get_niche(niche_id)
    template = _load_prompt("niche_tweet_scorer.txt")
    prompt = _fill_template(
        template,
        niche_id=niche_id,
        reply_goal=niche["reply_goal"],
        tweets_json=_build_tweets_json(search_results),
    )

    response = await client.aio.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=_SCORER_MAX_TOKENS,
        ),
    )
    raw = response.text or ""
    data = _parse_json_response(raw, "niche_tweet_scorer")

    scored: list[ScoredTweet] = []
    for item in data.get("scored_tweets", []):
        try:
            scored.append(
                ScoredTweet(
                    url=str(item["url"]),
                    text=str(item["text"]),
                    score=int(item["score"]),
                    reason=str(item["reason"]),
                )
            )
        except (KeyError, ValueError, TypeError):
            # Skip malformed entries rather than aborting.
            continue

    # Ensure descending order (Gemini should already do this, but be safe).
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Public API — get_trending
# ---------------------------------------------------------------------------


async def get_trending(niche_id: str, hours: int = 1) -> list[ScoredTweet]:
    """
    Return trending tweet candidates for *niche_id*, scored and ranked by
    engagement potential.

    Args:
        niche_id: One of the valid niche identifiers (``food``, ``football``,
                  ``economy``, ``politics``).
        hours: Recency window hint passed to search queries (currently
               informational — Brave does not support time-range filtering
               in the free tier).

    Returns:
        Scored and ranked list of tweets; may be empty if Brave returns no
        results or Gemini scores everything 0.

    Raises:
        ValueError: *niche_id* is not recognised (propagated from
                    ``get_niche``).
        EnvironmentError: ``BRAVE_SEARCH_API_KEY`` or
                          ``GEMINI_API_KEY`` is missing.
        NicheAgentError: Prompt file missing or Gemini response
                         unparseable.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY ortam değişkeni tanımlı değil."
        )

    # Validate niche_id eagerly so bad input fails fast (before any HTTP).
    get_niche(niche_id)

    client = genai.Client(api_key=api_key)
    search_results = await _fetch_search_results(niche_id)
    return await _score_tweets(search_results, niche_id, client)


# ---------------------------------------------------------------------------
# Public API — generate_reply
# ---------------------------------------------------------------------------


async def generate_reply(
    tweet_text: str,
    niche_id: str,
) -> list[NicheReply]:
    """
    Generate up to three legally-safe Turkish engagement replies for
    *tweet_text* in the context of *niche_id*.

    Each of the three generated replies is run through the legal-safety
    filter.  Replies that fail the filter are silently dropped.

    Args:
        tweet_text: The full text of the tweet to reply to.
        niche_id: One of the valid niche identifiers.

    Returns:
        List of ``NicheReply`` dicts that passed the filter.  May contain
        0–3 items.

    Raises:
        ValueError: *niche_id* is not recognised.
        EnvironmentError: ``GEMINI_API_KEY`` is missing.
        NicheAgentError: Prompt file missing or Gemini response
                         unparseable.
        NicheReplyBlockedError: All generated replies were blocked by the
                                legal-safety filter.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY ortam değişkeni tanımlı değil."
        )

    niche = get_niche(niche_id)  # raises ValueError for unknown niche_id

    template = _load_prompt("niche_reply_generator.txt")
    prompt = _fill_template(
        template,
        niche_id=niche_id,
        tone_instructions=niche["tone_instructions"],
        reply_goal=niche["reply_goal"],
        tweet_text=tweet_text,
    )

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=_REPLY_MAX_TOKENS,
        ),
    )
    raw = response.text or ""
    data = _parse_json_response(raw, "niche_reply_generator")

    # Parse and filter replies.
    passed_replies: list[NicheReply] = []
    for item in data.get("replies", []):
        try:
            text = str(item["text"])
            hook_type = str(item["hook_type"])
        except (KeyError, TypeError):
            continue

        filter_result = check_reply(text)
        if filter_result["passed"]:
            passed_replies.append(NicheReply(text=text, hook_type=hook_type))

    if not passed_replies:
        raise NicheReplyBlockedError(
            "Tüm oluşturulan yanıtlar hukuki güvenlik filtresi tarafından engellendi."
        )

    return passed_replies
