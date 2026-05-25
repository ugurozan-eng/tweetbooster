"""
TwitBoost — Research Router
=============================
Exposes the research pipeline as HTTP endpoints.

Endpoints
---------
POST /api/research/identify
    Identify the person in a raw tweet (Claude only, no search).

POST /api/research/run
    Full pipeline: identify person → 4 parallel Brave searches.
    Returns person profile + deduplicated source list.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.person_identifier import (
    PersonIdentifierError,
    identify_person,
)
from services.research_agent import ResearchResult, run_research

router = APIRouter(prefix="/api/research", tags=["research"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class TweetInput(BaseModel):
    tweet_text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Raw tweet text pasted by the user.",
    )


class PersonResponse(BaseModel):
    name: str | None
    handle: str | None
    topic: str
    confidence: str


class ResearchResultItem(BaseModel):
    url: str
    title: str
    description: str
    date: str | None
    query_source: str


class RunResearchResponse(BaseModel):
    person: PersonResponse
    results: list[ResearchResultItem]
    total_sources: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/identify",
    response_model=PersonResponse,
    summary="Identify person in a tweet",
)
async def identify(body: TweetInput) -> PersonResponse:
    """
    Run **person identification only** on the supplied tweet text.

    Uses Claude Sonnet to extract name, Twitter handle, topic, and confidence.
    Does **not** perform any web search.
    """
    try:
        person = await identify_person(body.tweet_text)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (PersonIdentifierError, FileNotFoundError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return PersonResponse(**person)


@router.post(
    "/run",
    response_model=RunResearchResponse,
    summary="Full research pipeline",
)
async def run(body: TweetInput) -> RunResearchResponse:
    """
    Run the **full research pipeline**:

    1. Identify the person in the tweet (Claude Sonnet).
    2. Run 4 parallel Brave Search queries for that person.
    3. Deduplicate results and return the consolidated source list.

    Returns HTTP 422 with a Turkish error message if the person cannot be
    identified — the pipeline cannot proceed without a name.
    """
    # ── Step 1: identify ──────────────────────────────────────────────────
    try:
        person = await identify_person(body.tweet_text)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (PersonIdentifierError, FileNotFoundError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if not person["name"]:
        raise HTTPException(
            status_code=422,
            detail=(
                "Kişi tespit edilemedi. "
                "Lütfen tweet metninin kişiye ait açık bir isim veya kullanıcı adı içerdiğinden emin olun."
            ),
        )

    # ── Step 2: run research ──────────────────────────────────────────────
    try:
        sources = await run_research(person["name"], person["topic"])
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Arama sırasında beklenmedik bir hata oluştu: {exc}",
        )

    return RunResearchResponse(
        person=PersonResponse(**person),
        results=[ResearchResultItem(**r) for r in sources],
        total_sources=len(sources),
    )
