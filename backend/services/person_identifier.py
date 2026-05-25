"""
TwitBoost — Person Identifier Service
======================================
Uses Claude Sonnet to extract the subject's identity from raw tweet text.

The service loads its system prompt from
``backend/prompts/person_identifier.txt`` — never from a hardcoded string.

Model & token budget (ARCHITECTURE.md §6)
-----------------------------------------
- Model   : claude-sonnet-4-20250514
- Max out : 512 tokens  (identification response is tiny; conserve budget)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "claude-sonnet-4-20250514"
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
    """Raised when the Claude API call fails or returns unparseable output."""


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
    Parse JSON from a Claude response, tolerating markdown code-fence wrapping.

    Claude occasionally wraps JSON in triple-backtick fences even when
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

    raise json.JSONDecodeError(f"Cannot parse JSON from Claude output: {text[:300]}", text, 0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def identify_person(tweet_text: str) -> PersonIdentification:
    """
    Extract the person's identity from a raw tweet.

    Args:
        tweet_text: Raw tweet text pasted by the user (any language).

    Returns:
        :class:`PersonIdentification` dict with ``name``, ``handle``,
        ``topic``, and ``confidence``.  When the person cannot be identified
        ``name`` is ``None`` and ``confidence`` is ``"low"``.

    Raises:
        EnvironmentError:       ``ANTHROPIC_API_KEY`` is not set.
        FileNotFoundError:      System prompt file is missing.
        PersonIdentifierError:  Claude API call failed or returned bad JSON.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and fill in your Anthropic API key."
        )

    system_prompt = _load_system_prompt()
    client = anthropic.AsyncAnthropic(api_key=api_key)

    try:
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Tweet metni:\n\n{tweet_text}",
                }
            ],
        )
    except anthropic.APIError as exc:
        raise PersonIdentifierError(
            f"Claude API error during person identification: {exc}"
        ) from exc

    raw = message.content[0].text

    try:
        data = _parse_claude_json(raw)
    except json.JSONDecodeError as exc:
        raise PersonIdentifierError(
            f"Could not parse JSON from Claude response: {exc}"
        ) from exc

    # Normalise confidence — default to "low" for any unexpected value
    raw_confidence = str(data.get("confidence", "low")).lower()
    confidence: Confidence = raw_confidence if raw_confidence in ("high", "medium", "low") else "low"  # type: ignore[assignment]

    return PersonIdentification(
        name=data.get("name") or None,        # coerce empty string → None
        handle=data.get("handle") or None,
        topic=str(data.get("topic", "")),
        confidence=confidence,
    )
