"""
TwitBoost — Person Identifier Service
======================================
Uses Gemini 2.5 Pro to extract the subject's identity from raw tweet text.

The service loads its system prompt from
``backend/prompts/person_identifier.txt`` — never from a hardcoded string.

Model & token budget (ARCHITECTURE.md §6)
-----------------------------------------
- Model   : gemini-2.5-pro
- Max out : 512 tokens  (identification response is tiny; conserve budget)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-pro"
_MAX_TOKENS = 512  # identification response is small
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

Confidence = Literal["high", "medium", "low"]


class PersonIdentification(TypedDict):
    name: str | None
    handle: str | None
    topic: str
    confidence: Confidence


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PersonIdentifierError(Exception):
    """Raised when the Gemini API call fails or returns unparseable output."""


class PersonNotFoundError(Exception):
    """
    Raised when the tweet contains no identifiable person.

    Triggered when ``confidence == 'low'`` *and* ``name is None``.
    The opposition router catches this and returns HTTP 422 so the UI can
    show a user-friendly yellow warning instead of a generic red error.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_system_prompt() -> str:
    """Load the person-identifier system prompt from disk."""
    path = _PROMPTS_DIR / "person_identifier.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"System prompt not found at: {path}\n"
            "Ensure backend/prompts/person_identifier.txt exists."
        )


def _parse_claude_json(raw: str) -> dict:
    """
    Parse JSON from a Gemini response, tolerating markdown code-fence wrapping.

    Gemini occasionally wraps JSON in triple-backtick fences even when
    instructed not to.  This function strips those fences before parsing.
    """
    text = raw.strip()

    # Fast path — valid bare JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (``` or ```json … ```)
    if "```" in text:
        parts = text.split("```")
        # parts[1] is the content between the first pair of fences
        if len(parts) >= 3:
            inner = parts[1]
            # Remove optional language tag (e.g. "json\n")
            if inner.startswith("json"):
                inner = inner[4:]
            try:
                return json.loads(inner.strip())
            except json.JSONDecodeError:
                pass

    raise json.JSONDecodeError(f"Cannot parse JSON from Gemini output: {text[:300]}", text, 0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def identify_person(
    tweet_text: str,
    twitter_handle: str | None = None,
) -> PersonIdentification:
    """
    Extract the person's identity from a raw tweet.

    Args:
        tweet_text:      Raw tweet text pasted by the user (any language).
        twitter_handle:  Optional. When supplied the Gemini name-extraction
                         step is skipped entirely — the cleaned handle is used
                         as both ``name`` and ``handle`` for downstream search.

    Returns:
        :class:`PersonIdentification` dict with ``name``, ``handle``,
        ``topic``, and ``confidence``.

    Raises:
        EnvironmentError:       ``GEMINI_API_KEY`` is not set (fast-path bypasses this).
        FileNotFoundError:      System prompt file is missing (fast-path bypasses this).
        PersonIdentifierError:  Gemini API call failed or returned bad JSON.
        PersonNotFoundError:    Tweet contains no identifiable person
                                (confidence='low', name=None). Caller should
                                return HTTP 422 with a user-friendly message.
    """
    # ── Fast path: caller already knows the handle → skip Gemini entirely ──
    if twitter_handle:
        clean = twitter_handle.lstrip("@").strip()
        if clean:
            return PersonIdentification(
                name=clean,
                handle=clean,
                topic="",
                confidence="high",
            )

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example to .env and fill in your Gemini API key."
        )

    system_prompt = _load_system_prompt()
    client = genai.Client(api_key=api_key)

    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=f"Tweet metni:\n\n{tweet_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=_MAX_TOKENS,
            ),
        )
    except Exception as exc:
        raise PersonIdentifierError(
            f"Gemini API error during person identification: {exc}"
        ) from exc

    raw = response.text or ""

    try:
        data = _parse_claude_json(raw)
    except json.JSONDecodeError as exc:
        raise PersonIdentifierError(
            f"Could not parse JSON from Gemini response: {exc}"
        ) from exc

    # Normalise confidence — default to "low" for any unexpected value
    raw_confidence = str(data.get("confidence", "low")).lower()
    confidence: Confidence = raw_confidence if raw_confidence in ("high", "medium", "low") else "low"  # type: ignore[assignment]

    result = PersonIdentification(
        name=data.get("name") or None,        # coerce empty string → None
        handle=data.get("handle") or None,
        topic=str(data.get("topic", "")),
        confidence=confidence,
    )

    # Early exit when the tweet has no identifiable person.
    # Prevents wasteful Brave Search queries downstream.
    if result["confidence"] == "low" and result["name"] is None:
        raise PersonNotFoundError(
            "Tweet'te tanımlanabilir bir kişi bulunamadı."
        )

    return result
