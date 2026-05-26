"""
Tests for services/person_identifier.py

Coverage
--------
- Happy path: Gemini returns clean JSON → PersonIdentification returned
- Fenced JSON: Gemini wraps output in ```json … ``` → still parsed
- Unidentified person: confidence='low', name=None → PersonNotFoundError raised
- Unknown confidence value: normalised to "low"; name present → result returned
- Empty name/handle with confidence=low → PersonNotFoundError raised
- Bad JSON from Gemini: PersonIdentifierError raised
- Gemini API error: PersonIdentifierError raised
- Missing API key: EnvironmentError raised
- Missing system prompt file: FileNotFoundError raised
- twitter_handle provided → Gemini NOT called, handle used directly
- twitter_handle with leading '@' → stripped correctly
- whitespace-only twitter_handle → falls through to Gemini
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.person_identifier import (
    PersonIdentifierError,
    PersonNotFoundError,
    _parse_claude_json,
    identify_person,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gemini_response(text: str) -> MagicMock:
    """Build a minimal mock that looks like a Gemini GenerateContentResponse."""
    response = MagicMock()
    response.text = text
    return response


def _mock_gemini(monkeypatch: pytest.MonkeyPatch, response_text: str) -> AsyncMock:
    """
    Patch genai.Client so aio.models.generate_content returns a mock response.
    Returns the AsyncMock so callers can inspect call args.
    """
    generate_mock = AsyncMock(return_value=_make_gemini_response(response_text))

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = generate_mock

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "services.person_identifier.genai.Client",
        lambda **kwargs: mock_client,
    )
    return generate_mock


# ---------------------------------------------------------------------------
# _parse_claude_json unit tests (no I/O, pure function)
# ---------------------------------------------------------------------------


def test_parse_bare_json() -> None:
    raw = '{"name": "Ali Yılmaz", "handle": "aliyilmaz", "topic": "ekonomi", "confidence": "high"}'
    result = _parse_claude_json(raw)
    assert result["name"] == "Ali Yılmaz"
    assert result["confidence"] == "high"


def test_parse_fenced_json() -> None:
    raw = '```json\n{"name": "Veli Demir", "handle": null, "topic": "siyaset", "confidence": "medium"}\n```'
    result = _parse_claude_json(raw)
    assert result["name"] == "Veli Demir"
    assert result["handle"] is None


def test_parse_fenced_json_no_language_tag() -> None:
    raw = '```\n{"name": "X", "handle": null, "topic": "t", "confidence": "low"}\n```'
    result = _parse_claude_json(raw)
    assert result["name"] == "X"


def test_parse_invalid_json_raises() -> None:
    with pytest.raises(json.JSONDecodeError):
        _parse_claude_json("this is not json at all")


# ---------------------------------------------------------------------------
# identify_person — happy path
# ---------------------------------------------------------------------------


async def test_identify_person_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns correct PersonIdentification when Gemini responds with clean JSON."""
    generate_mock = _mock_gemini(
        monkeypatch,
        '{"name": "Ahmet Yılmaz", "handle": "ahmetyilmaz", "topic": "enflasyon politikası", "confidence": "high"}',
    )

    result = await identify_person("@ahmetyilmaz Enflasyon konusunda ne düşünüyorsunuz?")

    assert result["name"] == "Ahmet Yılmaz"
    assert result["handle"] == "ahmetyilmaz"
    assert result["topic"] == "enflasyon politikası"
    assert result["confidence"] == "high"

    # Verify Gemini was called once
    generate_mock.assert_awaited_once()


async def test_identify_person_fenced_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parses correctly when Gemini wraps JSON in markdown code fences."""
    _mock_gemini(
        monkeypatch,
        '```json\n{"name": "Mehmet Çelik", "handle": null, "topic": "bütçe açığı", "confidence": "medium"}\n```',
    )

    result = await identify_person("Maliye Bakanı bütçe konusunda açıklama yaptı.")

    assert result["name"] == "Mehmet Çelik"
    assert result["handle"] is None
    assert result["confidence"] == "medium"


# ---------------------------------------------------------------------------
# identify_person — unidentified person → PersonNotFoundError
# ---------------------------------------------------------------------------


async def test_identify_person_unidentified(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises PersonNotFoundError when Gemini cannot identify the person (confidence=low, name=None)."""
    _mock_gemini(
        monkeypatch,
        '{"name": null, "handle": null, "topic": "genel siyaset", "confidence": "low"}',
    )

    with pytest.raises(PersonNotFoundError):
        await identify_person("Bu adam her şeyi biliyor sanki.")


async def test_identify_person_empty_name_coerced_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty string name with confidence=low raises PersonNotFoundError (empty → None, low+None → error)."""
    _mock_gemini(
        monkeypatch,
        '{"name": "", "handle": "", "topic": "bilinmiyor", "confidence": "low"}',
    )

    with pytest.raises(PersonNotFoundError):
        await identify_person("Bilinmeyen biri bir şey söyledi.")


# ---------------------------------------------------------------------------
# identify_person — confidence normalisation
# ---------------------------------------------------------------------------


async def test_identify_person_unknown_confidence_normalised(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unrecognised confidence value is normalised to 'low'; name present → result returned."""
    _mock_gemini(
        monkeypatch,
        '{"name": "Test Kişisi", "handle": null, "topic": "test konusu", "confidence": "very_high"}',
    )

    # name is not None, so PersonNotFoundError is NOT raised despite confidence='low'
    result = await identify_person("Test tweet")
    assert result["name"] == "Test Kişisi"
    assert result["confidence"] == "low"


# ---------------------------------------------------------------------------
# identify_person — error cases
# ---------------------------------------------------------------------------


async def test_identify_person_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises PersonIdentifierError when Gemini returns unparseable output."""
    _mock_gemini(monkeypatch, "Üzgünüm, bunu yapamam.")

    with pytest.raises(PersonIdentifierError, match="parse JSON"):
        await identify_person("Test tweet")


async def test_identify_person_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises PersonIdentifierError when the Gemini API call fails."""
    generate_mock = AsyncMock(side_effect=Exception("quota exceeded"))

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = generate_mock

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "services.person_identifier.genai.Client",
        lambda **kwargs: mock_client,
    )

    with pytest.raises(PersonIdentifierError, match="Gemini API error"):
        await identify_person("Test tweet")


async def test_identify_person_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises EnvironmentError when GEMINI_API_KEY is not set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        await identify_person("Test tweet")


async def test_identify_person_missing_prompt_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Raises FileNotFoundError when the system prompt file is missing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    # Redirect _PROMPTS_DIR to an empty temp directory
    monkeypatch.setattr("services.person_identifier._PROMPTS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="person_identifier.txt"):
        await identify_person("Test tweet")


# ---------------------------------------------------------------------------
# identify_person — twitter_handle fast-path (skips Gemini)
# ---------------------------------------------------------------------------


async def test_identify_person_with_handle_skips_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When twitter_handle is supplied, Gemini is NOT called."""
    generate_mock = _mock_gemini(
        monkeypatch,
        '{"name": "Should Not Appear", "handle": "other", "topic": "x", "confidence": "high"}',
    )

    result = await identify_person("Bazı tweet metni", twitter_handle="@rdoganoglu")

    assert result["handle"] == "rdoganoglu"
    assert result["name"] == "rdoganoglu"
    assert result["confidence"] == "high"
    # Gemini must NOT have been called
    generate_mock.assert_not_awaited()


async def test_identify_person_handle_at_prefix_stripped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leading '@' characters are stripped from the handle."""
    generate_mock = _mock_gemini(monkeypatch, "{}")

    result = await identify_person("Tweet", twitter_handle="@kamuoyundaki")

    assert result["handle"] == "kamuoyundaki"
    assert result["name"] == "kamuoyundaki"
    generate_mock.assert_not_awaited()


async def test_identify_person_whitespace_handle_falls_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A whitespace-only handle is ignored and Gemini is called as normal."""
    generate_mock = _mock_gemini(
        monkeypatch,
        '{"name": "Ahmet", "handle": "ahmet", "topic": "siyaset", "confidence": "high"}',
    )

    result = await identify_person("Tweet about Ahmet", twitter_handle="   ")

    assert result["name"] == "Ahmet"
    generate_mock.assert_awaited_once()
