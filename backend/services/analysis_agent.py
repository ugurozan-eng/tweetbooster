"""
TwitBoost — Analysis Agent
============================
Orchestrates the two-stage AI pipeline for Opposition Mode:

  Stage 1 — Inconsistency Analysis
    Calls Gemini with ``inconsistency_analyzer.txt`` to find contradictions
    between the current tweet and the research results.

  Stage 2 — Reply Generation (parallel)
    Calls Gemini three times concurrently (one per tone: cold / sharp / thread)
    using the matching ``reply_generator_<tone>.txt`` prompt.
    After generation, every reply is passed through the legal safety filter.
    Any reply that fails the filter is set to ``None`` in the output.

Token budget (ARCHITECTURE.md §6 / COMMON_MISTAKES.md)
-------------------------------------------------------
  • Inconsistency analysis : max_tokens = 1500
  • Each reply generator   : max_tokens = 1000
  • Model for all calls    : gemini-2.5-pro
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Literal, TypedDict

from google import genai
from google.genai import types

from services.legal_safety_filter import check_reply, check_thread
from services.research_agent import ResearchResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-pro"
_ANALYSIS_MAX_TOKENS = 1500
_REPLY_MAX_TOKENS = 1000
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_VALID_TONES: tuple[str, ...] = ("cold", "sharp", "thread")

# ---------------------------------------------------------------------------
# Public TypedDicts
# ---------------------------------------------------------------------------


class ContradictionItem(TypedDict):
    statement_a: str
    statement_b: str
    date_a: str | None
    date_b: str | None
    source_url: str
    confidence: Literal["high", "medium", "low"]
    summary: str


class ReplyVariant(TypedDict):
    tweet_text: str
    thread: list[str]
    evidence_note: str
    disclaimer: str


class AnalysisOutput(TypedDict):
    person_name: str
    contradictions: list[ContradictionItem]
    replies: dict[str, ReplyVariant | None]   # keys: "cold", "sharp", "thread"
    sources: list[ResearchResult]
    status: Literal["ok", "no_contradictions_found"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AnalysisAgentError(Exception):
    """Raised when a Gemini API call in the analysis pipeline fails."""


class AnalysisTimeoutError(AnalysisAgentError):
    """Raised when a Gemini API call exceeds the 25-second timeout threshold."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"System prompt not found: {path}. "
            f"Ensure backend/prompts/{filename} exists."
        )


def _parse_json_response(raw: str, context: str) -> dict:
    """
    Parse JSON from a Gemini response, tolerating markdown code-fence wrapping.
    ``context`` is used only in error messages.
    """
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            inner = parts[1]
            if inner.startswith("json"):
                inner = inner[4:]
            try:
                return json.loads(inner.strip())
            except json.JSONDecodeError:
                pass
    raise AnalysisAgentError(
        f"Could not parse JSON from Gemini response [{context}]: {text[:300]}"
    )


def _format_sources_for_analysis(sources: list[ResearchResult]) -> str:
    """Format research results as a numbered list for the analysis prompt."""
    lines: list[str] = []
    for i, s in enumerate(sources, 1):
        date_str = s.get("date") or "tarih bilinmiyor"
        lines.append(
            f"{i}. [{s['query_source']}] {s['title']} ({date_str})\n"
            f"   URL: {s['url']}\n"
            f"   Özet: {s['description']}"
        )
    return "\n".join(lines) if lines else "(Kaynak bulunamadı)"


def _format_contradictions_for_reply(contradictions: list[ContradictionItem]) -> str:
    """Format the contradiction map as a numbered list for reply generators."""
    if not contradictions:
        return "(Çelişki bulunamadı)"
    lines: list[str] = []
    for i, c in enumerate(contradictions, 1):
        date_a = c.get("date_a") or "tarih bilinmiyor"
        date_b = c.get("date_b") or "tarih bilinmiyor"
        lines.append(
            f"{i}. {c['summary']} (Güven: {c['confidence']})\n"
            f"   - Eski beyan ({date_a}): {c['statement_a']}\n"
            f"   - Yeni beyan ({date_b}): {c['statement_b']}\n"
            f"   - Kaynak: {c['source_url']}"
        )
    return "\n".join(lines)


def _build_reply_user_message(
    person_name: str,
    current_tweet: str,
    contradictions: list[ContradictionItem],
    sources: list[ResearchResult],
) -> str:
    """Build the user-turn message sent to every reply generator."""
    return (
        f"Kişi adı: {person_name}\n\n"
        f"Güncel tweet:\n{current_tweet}\n\n"
        f"Tespit edilen çelişkiler:\n"
        f"{_format_contradictions_for_reply(contradictions)}\n\n"
        f"Kullanılabilecek kaynaklar:\n"
        f"{_format_sources_for_analysis(sources[:5])}"   # top 5 sources
    )


def _normalise_confidence(value: object) -> Literal["high", "medium", "low"]:
    v = str(value).lower()
    return v if v in ("high", "medium", "low") else "low"  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Stage 1 — Inconsistency analysis
# ---------------------------------------------------------------------------


async def _analyze_inconsistencies(
    client: genai.Client,
    current_tweet: str,
    sources: list[ResearchResult],
) -> tuple[str, list[ContradictionItem], Literal["high", "medium", "low"]]:
    """
    Call Gemini to find contradictions between ``current_tweet`` and ``sources``.

    Returns:
        (person_name, contradictions, overall_confidence)
    """
    system_prompt = _load_prompt("inconsistency_analyzer.txt")
    user_msg = (
        f"Güncel tweet:\n{current_tweet}\n\n"
        f"Geçmiş kaynaklar ({len(sources)} kaynak):\n"
        f"{_format_sources_for_analysis(sources)}"
    )

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=_MODEL,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=_ANALYSIS_MAX_TOKENS,
                ),
            ),
            timeout=25.0,
        )
    except asyncio.TimeoutError as exc:
        raise AnalysisTimeoutError(
            "Gemini analiz çağrısı zaman aşımına uğradı (25 saniye). "
            "Lütfen daha sonra tekrar deneyin."
        ) from exc
    except Exception as exc:
        raise AnalysisAgentError(
            f"Gemini API error in inconsistency analysis: {exc}"
        ) from exc

    data = _parse_json_response(response.text or "", "inconsistency_analyzer")

    person_name: str = data.get("person_name") or "Bilinmiyor"
    overall_conf = _normalise_confidence(data.get("overall_confidence", "low"))

    raw_contradictions: list[dict] = data.get("contradictions") or []
    contradictions: list[ContradictionItem] = []
    for item in raw_contradictions:
        contradictions.append(
            ContradictionItem(
                statement_a=str(item.get("statement_a", "")),
                statement_b=str(item.get("statement_b", "")),
                date_a=item.get("date_a") or None,
                date_b=item.get("date_b") or None,
                source_url=str(item.get("source_url", "")),
                confidence=_normalise_confidence(item.get("confidence", "low")),
                summary=str(item.get("summary", "")),
            )
        )

    return person_name, contradictions, overall_conf


# ---------------------------------------------------------------------------
# Stage 2 — Reply generation (one tone)
# ---------------------------------------------------------------------------


async def _generate_reply(
    client: genai.Client,
    tone: str,
    person_name: str,
    current_tweet: str,
    contradictions: list[ContradictionItem],
    sources: list[ResearchResult],
) -> ReplyVariant | None:
    """
    Generate a single reply variant for ``tone``.

    Returns ``None`` if the Gemini call fails OR the legal filter blocks it.
    Errors are printed to stderr but do not propagate (resilient design).
    """
    prompt_file = f"reply_generator_{tone}.txt"
    try:
        system_prompt = _load_prompt(prompt_file)
    except FileNotFoundError as exc:
        print(f"[analysis_agent] missing prompt for tone '{tone}': {exc}", file=sys.stderr)
        return None

    user_msg = _build_reply_user_message(person_name, current_tweet, contradictions, sources)

    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=_REPLY_MAX_TOKENS,
            ),
        )
    except Exception as exc:
        print(
            f"[analysis_agent] Gemini API error for tone '{tone}': {exc}",
            file=sys.stderr,
        )
        return None

    try:
        data = _parse_json_response(response.text or "", f"reply_generator_{tone}")
    except AnalysisAgentError as exc:
        print(f"[analysis_agent] JSON parse error for tone '{tone}': {exc}", file=sys.stderr)
        return None

    reply = ReplyVariant(
        tweet_text=str(data.get("tweet_text", "")),
        thread=list(data.get("thread") or []),
        evidence_note=str(data.get("evidence_note", "")),
        disclaimer=str(data.get("disclaimer", "Bu kişinin kendi beyanatlarıdır.")),
    )

    # ── Legal safety filter ───────────────────────────────────────────────
    # Check both tweet_text and all thread items (COMMON_MISTAKES: filter runs AFTER generation)
    texts_to_check = [reply["tweet_text"]] + reply["thread"]
    filter_result = check_thread(texts_to_check)

    if not filter_result["passed"]:
        print(
            f"[analysis_agent] tone '{tone}' BLOCKED by legal filter: "
            f"{filter_result['violations']}",
            file=sys.stderr,
        )
        return None

    return reply


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_analysis(
    current_tweet: str,
    research_results: list[ResearchResult],
    tones: list[str] | None = None,
) -> AnalysisOutput:
    """
    Run the full Opposition Mode analysis pipeline.

    Args:
        current_tweet:    Raw tweet text pasted by the user.
        research_results: Output of :func:`~services.research_agent.run_research`.
        tones:            Which reply tones to generate. Defaults to all three
                          (``["cold", "sharp", "thread"]``). Unknown tones are ignored.

    Returns:
        :class:`AnalysisOutput` with person name, contradictions, replies,
        source list, and a status flag.

    Raises:
        EnvironmentError:   ``GEMINI_API_KEY`` is not set.
        AnalysisAgentError: The inconsistency-analysis Gemini call failed fatally.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example to .env and fill in your Gemini API key."
        )

    requested_tones = [t for t in (tones or list(_VALID_TONES)) if t in _VALID_TONES]
    client = genai.Client(api_key=api_key)

    # ── Stage 1: inconsistency analysis ──────────────────────────────────
    person_name, contradictions, overall_conf = await _analyze_inconsistencies(
        client, current_tweet, research_results
    )

    # ── Early exit: no useful contradictions ─────────────────────────────
    if overall_conf == "low" and not contradictions:
        return AnalysisOutput(
            person_name=person_name,
            contradictions=[],
            replies={t: None for t in _VALID_TONES},
            sources=research_results,
            status="no_contradictions_found",
        )

    # ── Stage 2: reply generation (all requested tones in parallel) ───────
    raw_replies: list[ReplyVariant | None | BaseException] = await asyncio.gather(
        *[
            _generate_reply(client, tone, person_name, current_tweet, contradictions, research_results)
            for tone in requested_tones
        ],
        return_exceptions=True,
    )

    replies: dict[str, ReplyVariant | None] = {t: None for t in _VALID_TONES}
    for tone, outcome in zip(requested_tones, raw_replies):
        if isinstance(outcome, BaseException):
            print(
                f"[analysis_agent] unexpected error for tone '{tone}': {outcome}",
                file=sys.stderr,
            )
            replies[tone] = None
        else:
            replies[tone] = outcome   # already None if filtered/failed

    return AnalysisOutput(
        person_name=person_name,
        contradictions=contradictions,
        replies=replies,
        sources=research_results,
        status="ok",
    )
