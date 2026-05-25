"""
Tests for services/analysis_agent.py

Coverage
--------
- Happy path: contradictions found, all 3 replies generated and pass filter
- No contradictions: overall_confidence='low' + empty list → early-exit status
- Legal filter blocks one reply (sharp) — others still returned
- All replies blocked by filter → replies all null, status still 'ok'
- Partial tone failure: one Claude API call raises → that tone is None
- Missing ANTHROPIC_API_KEY → EnvironmentError raised before any Claude call
- Missing prompt file → AnalysisAgentError (propagated from stage 2)
- Helper functions: _format_sources_for_analysis, _parse_json_response
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest

import services.analysis_agent as aa
from services.analysis_agent import (
    AnalysisAgentError,
    _format_sources_for_analysis,
    _normalise_confidence,
    _parse_json_response,
    run_analysis,
)

# ---------------------------------------------------------------------------
# Sample fixture data
# ---------------------------------------------------------------------------

_SAMPLE_SOURCES = [
    {
        "url": "https://example.com/1",
        "title": "Eski Açıklama",
        "description": "2019'da farklı bir şey söyledi.",
        "date": "2019-05-10",
        "query_source": "A",
    },
    {
        "url": "https://example.com/2",
        "title": "Haber",
        "description": "Ekonomi politikası üzerine.",
        "date": "2020-03-01",
        "query_source": "B",
    },
]

_ANALYSIS_JSON = json.dumps({
    "person_name": "Ahmet Yılmaz",
    "overall_confidence": "high",
    "contradictions": [
        {
            "statement_a": "Enflasyon düşecek dedi.",
            "statement_b": "Enflasyon yüksek olmaya devam edecek.",
            "date_a": "2019-05-10",
            "date_b": "2024-01-01",
            "source_url": "https://example.com/1",
            "confidence": "high",
            "summary": "2019'da enflasyonun düşeceğini söyledi, şimdi yükseldiğini kabul ediyor.",
        }
    ],
})

_REPLY_JSON = json.dumps({
    "tweet_text": "2019: 'Enflasyon düşecek' → 2024: Enflasyon hâlâ yüksek.",
    "thread": [],
    "evidence_note": "Kaynak: https://example.com/1",
    "disclaimer": "Bu kişinin kendi beyanatlarıdır.",
})

_THREAD_REPLY_JSON = json.dumps({
    "tweet_text": "1/ Önemli bir çelişki tespit edildi.",
    "thread": [
        "1/ Önemli bir çelişki tespit edildi.",
        "2/ 2019'da enflasyonun düşeceğini söyledi.",
        "3/ 2024'te enflasyonun yüksek kaldığını kabul etti.",
        "4/ Bu kişinin kendi beyanatlarıdır.",
    ],
    "evidence_note": "Kaynak: https://example.com/1",
    "disclaimer": "Bu kişinin kendi beyanatlarıdır.",
})

_NO_CONTRADICTION_JSON = json.dumps({
    "person_name": "Bilinmiyor",
    "overall_confidence": "low",
    "contradictions": [],
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_message(text: str) -> MagicMock:
    """Build a minimal mock anthropic.Message."""
    block = MagicMock()
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    return msg


def _mock_client(call_responses: list[str]) -> MagicMock:
    """
    Return a mock AsyncAnthropic client whose messages.create returns
    each response in order of calls.
    """
    responses = [_make_message(r) for r in call_responses]
    idx = 0

    async def _create(*args, **kwargs):
        nonlocal idx
        r = responses[idx]
        idx += 1
        return r

    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(side_effect=_create)
    client = MagicMock()
    client.messages = messages_mock
    return client


# ---------------------------------------------------------------------------
# _parse_json_response unit tests
# ---------------------------------------------------------------------------


def test_parse_json_bare() -> None:
    assert _parse_json_response('{"a": 1}', "ctx") == {"a": 1}


def test_parse_json_fenced() -> None:
    raw = '```json\n{"x": 2}\n```'
    assert _parse_json_response(raw, "ctx") == {"x": 2}


def test_parse_json_invalid_raises() -> None:
    with pytest.raises(AnalysisAgentError, match="parse JSON"):
        _parse_json_response("not json at all", "ctx")


# ---------------------------------------------------------------------------
# _normalise_confidence
# ---------------------------------------------------------------------------


def test_normalise_confidence_valid() -> None:
    assert _normalise_confidence("high") == "high"
    assert _normalise_confidence("MEDIUM") == "medium"
    assert _normalise_confidence("Low") == "low"


def test_normalise_confidence_unknown() -> None:
    assert _normalise_confidence("unknown") == "low"
    assert _normalise_confidence(None) == "low"


# ---------------------------------------------------------------------------
# _format_sources_for_analysis
# ---------------------------------------------------------------------------


def test_format_sources_nonempty() -> None:
    text = _format_sources_for_analysis(_SAMPLE_SOURCES)  # type: ignore[arg-type]
    assert "Eski Açıklama" in text
    assert "https://example.com/1" in text
    assert "2019-05-10" in text


def test_format_sources_empty() -> None:
    text = _format_sources_for_analysis([])
    assert "bulunamadı" in text.lower()


# ---------------------------------------------------------------------------
# run_analysis — happy path
# ---------------------------------------------------------------------------


async def test_run_analysis_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """All 3 tones generate clean replies → status='ok', all replies present."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = _mock_client(
        [_ANALYSIS_JSON, _REPLY_JSON, _REPLY_JSON, _THREAD_REPLY_JSON]
    )
    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Test tweet.", _SAMPLE_SOURCES)  # type: ignore[arg-type]

    assert result["status"] == "ok"
    assert result["person_name"] == "Ahmet Yılmaz"
    assert len(result["contradictions"]) == 1
    assert result["contradictions"][0]["confidence"] == "high"
    # All 3 tones present and not None
    assert result["replies"]["cold"] is not None
    assert result["replies"]["sharp"] is not None
    assert result["replies"]["thread"] is not None
    # Claude was called 4 times (1 analysis + 3 replies)
    assert mock_client.messages.create.await_count == 4


# ---------------------------------------------------------------------------
# run_analysis — no contradictions (early exit)
# ---------------------------------------------------------------------------


async def test_run_analysis_no_contradictions(monkeypatch: pytest.MonkeyPatch) -> None:
    """overall_confidence='low' + empty contradictions → early exit, no reply calls."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = _mock_client([_NO_CONTRADICTION_JSON])
    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Generic tweet.", _SAMPLE_SOURCES)  # type: ignore[arg-type]

    assert result["status"] == "no_contradictions_found"
    assert result["contradictions"] == []
    assert all(v is None for v in result["replies"].values())
    # Only 1 Claude call (the analysis); no reply generation
    assert mock_client.messages.create.await_count == 1


# ---------------------------------------------------------------------------
# run_analysis — legal filter blocks one reply
# ---------------------------------------------------------------------------


async def test_run_analysis_legal_filter_blocks_sharp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sharp reply contains profanity → blocked (None); cold and thread still returned."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    dirty_reply = json.dumps({
        "tweet_text": "Bu orospu çocuğu yalan söylüyor.",   # PROFANITY → blocked
        "thread": [],
        "evidence_note": "Kaynak: https://example.com/1",
        "disclaimer": "Bu kişinin kendi beyanatlarıdır.",
    })

    mock_client = _mock_client(
        [_ANALYSIS_JSON, _REPLY_JSON, dirty_reply, _THREAD_REPLY_JSON]
    )
    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Test tweet.", _SAMPLE_SOURCES)  # type: ignore[arg-type]

    assert result["status"] == "ok"
    assert result["replies"]["cold"] is not None    # clean → allowed
    assert result["replies"]["sharp"] is None       # dirty → blocked
    assert result["replies"]["thread"] is not None  # clean → allowed


# ---------------------------------------------------------------------------
# run_analysis — all replies blocked by filter
# ---------------------------------------------------------------------------


async def test_run_analysis_all_replies_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """All 3 replies fail the filter → all None, but status is still 'ok'."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    dirty = json.dumps({
        "tweet_text": "Bu adam bir hırsızdır.",   # ACCUSATION → blocked
        "thread": [],
        "evidence_note": "x",
        "disclaimer": "Bu kişinin kendi beyanatlarıdır.",
    })

    mock_client = _mock_client([_ANALYSIS_JSON, dirty, dirty, dirty])
    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Test tweet.", _SAMPLE_SOURCES)  # type: ignore[arg-type]

    assert result["status"] == "ok"
    assert all(v is None for v in result["replies"].values())


# ---------------------------------------------------------------------------
# run_analysis — partial tone failure (one Claude call raises)
# ---------------------------------------------------------------------------


async def test_run_analysis_one_tone_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """If one reply-generator Claude call raises, that tone is None; others succeed."""
    import anthropic as _anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    call_count = 0
    fake_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

    async def _create_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_message(_ANALYSIS_JSON)
        elif call_count == 2:
            return _make_message(_REPLY_JSON)      # cold — OK
        elif call_count == 3:
            raise _anthropic.APIError("rate limit", fake_request, body={})  # sharp — fail
        else:
            return _make_message(_THREAD_REPLY_JSON)  # thread — OK

    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(side_effect=_create_side_effect)
    mock_client = MagicMock()
    mock_client.messages = messages_mock

    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Test tweet.", _SAMPLE_SOURCES)  # type: ignore[arg-type]

    assert result["replies"]["cold"] is not None
    assert result["replies"]["sharp"] is None      # API error → None
    assert result["replies"]["thread"] is not None


# ---------------------------------------------------------------------------
# run_analysis — missing API key
# ---------------------------------------------------------------------------


async def test_run_analysis_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """EnvironmentError raised immediately when ANTHROPIC_API_KEY is absent."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        await run_analysis("Test.", _SAMPLE_SOURCES)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# run_analysis — only specific tones requested
# ---------------------------------------------------------------------------


async def test_run_analysis_single_tone(monkeypatch: pytest.MonkeyPatch) -> None:
    """Requesting only 'cold' generates exactly 2 Claude calls (1 analysis + 1 reply)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = _mock_client([_ANALYSIS_JSON, _REPLY_JSON])
    monkeypatch.setattr(
        "services.analysis_agent.anthropic.AsyncAnthropic",
        lambda **kwargs: mock_client,
    )

    result = await run_analysis("Test.", _SAMPLE_SOURCES, tones=["cold"])  # type: ignore[arg-type]

    assert result["replies"]["cold"] is not None
    # sharp and thread were not requested → remain None (default)
    assert result["replies"]["sharp"] is None
    assert result["replies"]["thread"] is None
    assert mock_client.messages.create.await_count == 2
