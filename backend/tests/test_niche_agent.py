"""
Tests for services/niche_agent.py

Coverage
--------
- get_trending happy path: Brave returns results → Gemini scores them → sorted list
- get_trending empty: all Brave calls return empty → get_trending returns []
- get_trending partial Brave failure: one query raises, others succeed → merged
- get_trending invalid niche_id → ValueError (before any HTTP call)
- get_trending missing GEMINI_API_KEY → EnvironmentError
- get_trending Gemini returns 0 scored tweets → empty list
- generate_reply happy path: all 3 replies pass filter
- generate_reply partial block: 1 reply fails filter → 2 returned
- generate_reply all blocked → NicheReplyBlockedError raised
- generate_reply invalid niche_id → ValueError
- generate_reply missing GEMINI_API_KEY → EnvironmentError
- generate_reply missing prompt file → NicheAgentError
- Helper: _parse_json_response bare JSON
- Helper: _parse_json_response fenced JSON
- Helper: _parse_json_response invalid → NicheAgentError
- Helper: _fill_template replaces all placeholders
- Helper: _build_tweets_json filters empty URLs, truncates text
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.niche_agent as na
from services.niche_agent import (
    NicheAgentError,
    NicheReplyBlockedError,
    ScoredTweet,
    _build_tweets_json,
    _fill_template,
    _parse_json_response,
    generate_reply,
    get_trending,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SCORED_RESPONSE = json.dumps({
    "scored_tweets": [
        {
            "url": "https://twitter.com/a/1",
            "text": "Bugün yemek tariflerim çok beğenildi.",
            "score": 9,
            "reason": "Yüksek etkileşim potansiyeli olan güncel içerik.",
        },
        {
            "url": "https://twitter.com/b/2",
            "text": "Türk mutfağının en iyi tarifleri burada.",
            "score": 6,
            "reason": "Niş uyumlu ama etkileşim fırsatı orta düzeyde.",
        },
    ]
})

_REPLY_RESPONSE = json.dumps({
    "replies": [
        {"text": "Bu tarifi denemek istiyorum, hangi pişirme süresi daha iyi?", "hook_type": "question"},
        {"text": "Bence buradaki sır malzemeyi son anda eklemek.", "hook_type": "opinion"},
        {"text": "Türk mutfağında bu yöntem 200 yıllık bir gelenekten geliyor.", "hook_type": "fact"},
    ]
})

_EMPTY_SCORED_RESPONSE = json.dumps({"scored_tweets": []})

_BRAVE_RESULT_1 = {
    "url": "https://twitter.com/a/1",
    "title": "Yemek tarifi",
    "description": "Bugün yemek tariflerim çok beğenildi.",
}

_BRAVE_RESULT_2 = {
    "url": "https://twitter.com/b/2",
    "title": "Mutfak",
    "description": "Türk mutfağının en iyi tarifleri burada.",
}

# ---------------------------------------------------------------------------
# Helpers for building mock clients
# ---------------------------------------------------------------------------


def _make_response(text: str) -> MagicMock:
    """Build a minimal mock that looks like a Gemini GenerateContentResponse."""
    response = MagicMock()
    response.text = text
    return response


def _mock_gemini_client(responses: list[str]) -> MagicMock:
    """
    Build a mock genai.Client that returns each response in order.
    """
    msgs = [_make_response(r) for r in responses]
    idx = 0

    async def _create(*args, **kwargs):
        nonlocal idx
        r = msgs[idx]
        idx += 1
        return r

    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=_create)
    return client


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------


def test_parse_json_bare() -> None:
    assert _parse_json_response('{"a": 1}', "ctx") == {"a": 1}


def test_parse_json_fenced() -> None:
    raw = '```json\n{"x": 2}\n```'
    assert _parse_json_response(raw, "ctx") == {"x": 2}


def test_parse_json_invalid_raises() -> None:
    with pytest.raises(NicheAgentError, match="JSON"):
        _parse_json_response("not json at all", "ctx")


def test_fill_template_single() -> None:
    assert _fill_template("Hello {{name}}!", name="World") == "Hello World!"


def test_fill_template_multiple() -> None:
    result = _fill_template("{{a}} + {{b}}", a="1", b="2")
    assert result == "1 + 2"


def test_build_tweets_json_filters_empty_url() -> None:
    results = [
        {"url": "", "description": "no url"},
        {"url": "https://t.co/1", "description": "has url"},
    ]
    data = json.loads(_build_tweets_json(results))
    assert len(data) == 1
    assert data[0]["url"] == "https://t.co/1"


def test_build_tweets_json_truncates_text() -> None:
    long_desc = "x" * 300
    results = [{"url": "https://t.co/1", "description": long_desc}]
    data = json.loads(_build_tweets_json(results))
    assert len(data[0]["text"]) <= 200


# ---------------------------------------------------------------------------
# get_trending — happy path
# ---------------------------------------------------------------------------


async def test_get_trending_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Brave returns 2 results → Gemini scores them → sorted list returned."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    monkeypatch.setattr(
        "services.niche_agent.search",
        AsyncMock(return_value=[_BRAVE_RESULT_1, _BRAVE_RESULT_2]),
    )

    mock_client = _mock_gemini_client([_SCORED_RESPONSE])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    result = await get_trending("food")

    assert len(result) == 2
    assert result[0]["score"] == 9
    assert result[1]["score"] == 6
    assert result[0]["url"] == "https://twitter.com/a/1"


# ---------------------------------------------------------------------------
# get_trending — empty Brave results
# ---------------------------------------------------------------------------


async def test_get_trending_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """All Brave queries return empty lists → get_trending returns []."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    monkeypatch.setattr(
        "services.niche_agent.search",
        AsyncMock(return_value=[]),
    )

    mock_client = _mock_gemini_client([])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    result = await get_trending("food")

    assert result == []
    # Gemini should NOT have been called (empty input short-circuit)
    assert mock_client.aio.models.generate_content.await_count == 0


# ---------------------------------------------------------------------------
# get_trending — partial Brave failure
# ---------------------------------------------------------------------------


async def test_get_trending_partial_brave_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """One Brave query raises; the others succeed — results are still merged."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    call_count = 0

    async def _search_side_effect(query: str, count: int = 10):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Brave rate limit")
        return [_BRAVE_RESULT_1]

    monkeypatch.setattr("services.niche_agent.search", _search_side_effect)

    # Scorer will see 1 result (deduplicated across successful queries).
    # But 'food' has 3 queries, so calls 2 and 3 each return _BRAVE_RESULT_1
    # (same URL — deduplicated to one).
    single_score = json.dumps({
        "scored_tweets": [
            {
                "url": _BRAVE_RESULT_1["url"],
                "text": _BRAVE_RESULT_1["description"],
                "score": 7,
                "reason": "Tek sonuç ama niş uyumlu.",
            }
        ]
    })
    mock_client = _mock_gemini_client([single_score])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    result = await get_trending("food")

    # Despite one failure, we get at least one result
    assert len(result) >= 1
    assert result[0]["score"] == 7


# ---------------------------------------------------------------------------
# get_trending — invalid niche_id
# ---------------------------------------------------------------------------


async def test_get_trending_invalid_niche_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid niche_id raises ValueError immediately — no HTTP calls made."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    search_mock = AsyncMock()
    monkeypatch.setattr("services.niche_agent.search", search_mock)

    with pytest.raises(ValueError, match="Geçersiz niş"):
        await get_trending("invalid_niche")

    search_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_trending — missing GEMINI_API_KEY
# ---------------------------------------------------------------------------


async def test_get_trending_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        await get_trending("food")


# ---------------------------------------------------------------------------
# get_trending — Gemini scores 0 tweets
# ---------------------------------------------------------------------------


async def test_get_trending_zero_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gemini returns empty scored_tweets → get_trending returns []."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    monkeypatch.setattr(
        "services.niche_agent.search",
        AsyncMock(return_value=[_BRAVE_RESULT_1]),
    )

    mock_client = _mock_gemini_client([_EMPTY_SCORED_RESPONSE])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    result = await get_trending("food")
    assert result == []


# ---------------------------------------------------------------------------
# generate_reply — happy path
# ---------------------------------------------------------------------------


async def test_generate_reply_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """All 3 replies are clean → all 3 returned."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_client = _mock_gemini_client([_REPLY_RESPONSE])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    replies = await generate_reply("Bugün yeni bir tarif denedim!", "food")

    assert len(replies) == 3
    hook_types = [r["hook_type"] for r in replies]
    assert "question" in hook_types
    assert "opinion" in hook_types
    assert "fact" in hook_types


# ---------------------------------------------------------------------------
# generate_reply — one reply blocked by filter
# ---------------------------------------------------------------------------


async def test_generate_reply_partial_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sharp/dirty second reply is filtered out; question and fact remain."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    dirty_response = json.dumps({
        "replies": [
            {"text": "Bu tarifi denemek istiyorum, nasıl yapılıyor?", "hook_type": "question"},
            {"text": "Bu orospu çocuğu yemek yapmasını bilmiyor.", "hook_type": "opinion"},  # PROFANITY
            {"text": "Türk mutfağında bu yöntem 200 yıllık bir gelenekten geliyor.", "hook_type": "fact"},
        ]
    })

    mock_client = _mock_gemini_client([dirty_response])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    replies = await generate_reply("Test tweet.", "food")

    assert len(replies) == 2
    hook_types = [r["hook_type"] for r in replies]
    assert "question" in hook_types
    assert "fact" in hook_types
    assert "opinion" not in hook_types


# ---------------------------------------------------------------------------
# generate_reply — all replies blocked
# ---------------------------------------------------------------------------


async def test_generate_reply_all_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """All 3 replies fail the filter → NicheReplyBlockedError raised."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    all_dirty = json.dumps({
        "replies": [
            {"text": "Bu adam bir hırsızdır.", "hook_type": "question"},       # ACCUSATION
            {"text": "Onu linç edin hemen!", "hook_type": "opinion"},           # INCITEMENT
            {"text": "Şerefsizin teki bu.", "hook_type": "fact"},               # INSULT
        ]
    })

    mock_client = _mock_gemini_client([all_dirty])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    with pytest.raises(NicheReplyBlockedError):
        await generate_reply("Test tweet.", "food")


# ---------------------------------------------------------------------------
# generate_reply — invalid niche_id
# ---------------------------------------------------------------------------


async def test_generate_reply_invalid_niche_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid niche_id raises ValueError — no Gemini call made."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_client = _mock_gemini_client([])
    monkeypatch.setattr(
        "services.niche_agent.genai.Client",
        lambda **kwargs: mock_client,
    )

    with pytest.raises(ValueError, match="Geçersiz niş"):
        await generate_reply("Test tweet.", "not_a_real_niche")

    assert mock_client.aio.models.generate_content.await_count == 0


# ---------------------------------------------------------------------------
# generate_reply — missing GEMINI_API_KEY
# ---------------------------------------------------------------------------


async def test_generate_reply_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        await generate_reply("Test tweet.", "food")


# ---------------------------------------------------------------------------
# generate_reply — missing prompt file
# ---------------------------------------------------------------------------


async def test_generate_reply_missing_prompt_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If the prompt file is missing, NicheAgentError is raised."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    # Point _PROMPTS_DIR at a temp directory that has no .txt files.
    monkeypatch.setattr("services.niche_agent._PROMPTS_DIR", tmp_path)

    with pytest.raises(NicheAgentError, match="Prompt dosyası bulunamadı"):
        await generate_reply("Test tweet.", "food")
