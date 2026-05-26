"""
TwitBoost — Opposition Router
================================
Exposes the full Opposition Mode pipeline as a single HTTP endpoint.

Endpoint
--------
POST /api/opposition/analyze
    Full pipeline: person_identifier → research_agent → analysis_agent
    Body  : { tweet_text, tones (optional) }
    Returns: AnalysisOutput (person, contradictions, replies, sources, status)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from middleware.auth_middleware import UserClaims, get_current_user
from services.analysis_agent import (
    AnalysisAgentError,
    AnalysisOutput,
    AnalysisTimeoutError,
    ContradictionItem,
    ReplyVariant,
    run_analysis,
)
from services.person_identifier import PersonIdentifierError, PersonNotFoundError, identify_person
from services.plan_checker import check_daily_limit, check_permission, log_usage
from services.research_agent import run_research

router = APIRouter(prefix="/api/opposition", tags=["opposition"])

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

_VALID_TONES = {"cold", "sharp", "thread"}


class AnalyzeRequest(BaseModel):
    tweet_text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Raw tweet text pasted by the user.",
    )
    tones: list[str] = Field(
        default=["cold", "sharp", "thread"],
        description="Which reply tones to generate. Valid values: cold, sharp, thread.",
    )
    twitter_handle: str | None = Field(
        default=None,
        max_length=50,
        description="Optional Twitter handle (e.g. '@username'). When provided the AI "
                    "name-extraction step is skipped and the handle is used directly.",
    )


class ContradictionResponse(BaseModel):
    statement_a: str
    statement_b: str
    date_a: str | None
    date_b: str | None
    source_url: str
    confidence: str
    summary: str


class ReplyVariantResponse(BaseModel):
    tweet_text: str
    thread: list[str]
    evidence_note: str
    disclaimer: str


class AnalyzeResponse(BaseModel):
    person_name: str
    contradictions: list[ContradictionResponse]
    replies: dict[str, ReplyVariantResponse | None]
    sources: list[str]   # source URLs for display in the UI
    status: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Full Opposition Mode pipeline",
)
async def analyze(
    body: AnalyzeRequest,
    user: UserClaims = Depends(get_current_user),
) -> AnalyzeResponse:
    """
    Run the complete Opposition Mode pipeline for a tweet.

    Steps:
    1. Verify user plan allows opposition mode.
    2. Check daily request limit (UTC+3 reset).
    3. Identify the person in the tweet (Claude Sonnet).
    4. Run 4 parallel Brave Search queries for that person.
    5. Analyze contradictions between current tweet and research (Claude Sonnet).
    6. Generate up to 3 reply variants (Claude Sonnet × tones requested).
    7. Apply legal safety filter to each reply; blocked replies are returned as null.
    8. Log the request to usage_logs.

    Returns the contradiction map, all replies, and source list.
    Returns ``status: "no_contradictions_found"`` when research yields no usable evidence.
    """
    # ── Auth: plan permission + daily limit ───────────────────────────────
    check_permission(user["user_id"], user["plan"], "opposition")
    await check_daily_limit(user["user_id"], user["plan"], "opposition")

    # ── Validate tones ────────────────────────────────────────────────────
    requested_tones = [t for t in body.tones if t in _VALID_TONES]
    if not requested_tones:
        raise HTTPException(
            status_code=422,
            detail=f"Geçersiz ton değerleri. Geçerli değerler: {sorted(_VALID_TONES)}",
        )

    # ── Step 1: person identification ─────────────────────────────────────
    try:
        person = await identify_person(body.tweet_text, twitter_handle=body.twitter_handle)
    except PersonNotFoundError:
        # Tweet has no identifiable person — user guidance, not a system error.
        raise HTTPException(
            status_code=422,
            detail="Tweet'te tanımlanabilir bir kişi bulunamadı. Lütfen bir kişiye ait tweet yapıştırın.",
        )
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (PersonIdentifierError, FileNotFoundError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # ── Step 2: research ─────────────────────────────────────────────────
    try:
        research_results = await run_research(person["name"], person["topic"])
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Arama sırasında hata oluştu: {exc}",
        )

    # ── Steps 3-5: analysis + generation + filter ─────────────────────────
    try:
        result = await run_analysis(body.tweet_text, research_results, requested_tones)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AnalysisTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))
    except AnalysisAgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Analiz sırasında beklenmedik hata: {exc}",
        )

    # ── Build response ────────────────────────────────────────────────────
    replies_out: dict[str, ReplyVariantResponse | None] = {}
    for tone, variant in result["replies"].items():
        replies_out[tone] = (
            ReplyVariantResponse(**variant) if variant is not None else None
        )

    # Collect unique source URLs for the UI to display as clickable links.
    source_urls: list[str] = []
    seen: set[str] = set()
    for r in result["sources"]:
        url = str(r.get("url", "")).strip()
        if url and url not in seen:
            seen.add(url)
            source_urls.append(url)

    # ── Log usage (non-fatal if DB is down) ──────────────────────────────
    await log_usage(user["user_id"], "opposition")

    return AnalyzeResponse(
        person_name=result["person_name"],
        contradictions=[ContradictionResponse(**c) for c in result["contradictions"]],
        replies=replies_out,
        sources=source_urls,
        status=result["status"],
    )
