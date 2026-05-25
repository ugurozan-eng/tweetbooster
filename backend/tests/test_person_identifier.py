"""
Tests for services/person_identifier.py

Coverage
--------
- Happy path: Claude returns clean JSON → PersonIdentification returned
- Fenced JSON: Claude wraps output in ```json … ``` → still parsed
- Unidentified person: name is null, confidence is "low"
- Unknown confidence value: normalised to "low"
- Empty name/handle: coerced to None
- Bad JSON from Claude: PersonIdentifierError raised
- Claude API error: PersonIdentifierError raised
- Missing API key: EnvironmentError raised
- Missing system prompt file: FileNotFoundError raised
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.person_identifier import (
    PersonIdentifierError,
    _parse_claude_json,
    identify_person,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claude_response(text: str):
    """Build a minimal mock that looks like an anthropic.Message."""
    content_block = MagicMock()
    content_block.text = text
    message = MagicMock()
    message.content = [content_block]
    return message


def _mock_claude(monkeypatch: pytest.MonkeyPatch, response_text: str) -> AsyncMock:
    """
    Patch anthropic.AsyncAnthropic so messages.create returns a mock message.
    Returns the AsyncMock so callers can inspect call args.
    """
    create_mock = AsyncMock(return_value=_make_claude_response(response_text))

    mock_messages = MagicMock()
    mock_messages.create = create_mock

    mock_client = MagicMock()
    mock_client.messages = mock_messages

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setattr(
        "services.person_identifier.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )
    return create_mock


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
    """Returns correct PersonIdentification when Claude responds with clean JSON."""
    create_mock = _mock_claude(
        monkeypatch,
        '{"name": "Ahmet Yılmaz", "handle": "ahmetyilmaz", "topic": "enflasyon politikası", "confidence": "high"}',
    )

    result = await identify_person("@ahmetyilmaz Enflasyon konusunda ne düşünüyorsunuz?")

    assert result["name"] == "Ahmet Yılmaz"
    assert result["handle"] == "ahmetyilmaz"
    assert result["topic"] == "enflasyon politikası"
    assert result["confidence"] == "high"

    # Verify Claude was called once
    create_mock.assert_awaited_once()


async def test_identify_person_fenced_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parses correctly when Claude wraps JSON in markdown code fences."""
    _mock_claude(
        monkeypatch,
        '```json\n{"name": "Mehmet Çelik", "handle": null, "topic": "bütçe açığı", "confidence": "medium"}\n```',
    )

    result = await identify_person("Maliye Bakanı bütçe konusunda açıklama yaptı.")

    assert result["name"] == "Mehmet Çelik"
    assert result["handle"] is None
    assert result["confidence"] == "medium"


# ---------------------------------------------------------------------------
# identify_person — unidentified person
# ---------------------------------------------------------------------------


async def test_identify_person_unidentified(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns name=None, confidence='low' when Claude cannot identify the person."""
    _mock_claude(
        monkeypatch,
        '{"name": null, "handle": null, "topic": "genel siyaset", "confidence": "low"}',
    )

    result = await identify_person("Bu adam her şeyi biliyor sanki.")

    assert result["name"] is None
    assert result["handle"] is None
    assert result["confidence"] == "low"


async def test_identify_person_empty_name_coerced_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty string name/handle are coerced to None."""
    _mock_claude(
        monkeypatch,
        '{"name": "", "handle": "", "topic": "bilinmiyor", "confidence": "low"}',
    )

    result = await identify_person("Bilinmeyen biri bir şey söyledi.")

    assert result["name"] is None
    assert result["handle"] is None


# ---------------------------------------------------------------------------
# identify_person — confidence normalisation
# ---------------------------------------------------------------------------


async def test_identify_person_unknown_confidence_normalised(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unrecognised confidence value is normalised to 'low'."""
    _mock_claude(
        monkeypatch,
        '{"name": "Test", "handle": null, "topic": "test konusu", "confidence": "very_high"}',
    )

    result = await identify_person("Test tweet")
    assert result["confidence"] == "low"


# ---------------------------------------------------------------------------
# identify_person — error cases
# ---------------------------------------------------------------------------


async def test_identify_person_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises PersonIdentifierError when Claude returns unparseable output."""
    _mock_claude(monkeypatch, "Üzgünüm, bunu yapamam.")

    with pytest.raises(PersonIdentifierError, match="parse JSON"):
        await identify_person("Test tweet")


async def test_identify_person_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises PersonIdentifierError when the Anthropic API call fails."""
    import httpx
    import anthropic as _anthropic

    fake_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    create_mock = AsyncMock(
        side_effect=_anthropic.APIError("rate limit exceeded", fake_request, body={})
    )

    mock_messages = MagicMock()
    mock_messages.create = create_mock
    mock_client = MagicMock()
    mock_client.messages = mock_messages

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        "services.person_identifier.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    with pytest.raises(PersonIdentifierError, match="Claude API error"):
        await identify_person("Test tweet")


async def test_identify_person_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises EnvironmentError when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        await identify_person("Test tweet")


async def test_identify_person_missing_prompt_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Raises FileNotFoundError when the system prompt file is missing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Redirect PROMPTS_DIR to an empty temp directory
    monkeypatch.setattr("services.person_identifier._PROMPTS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="person_identifier.txt"):
        await identify_person("Test tweet")
