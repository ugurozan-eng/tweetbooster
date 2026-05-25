"""
TwitBoost — Niche Mode Router
==============================
Endpoints:
  POST /api/niche/trending  — Fetch and score trending tweets for a niche
  POST /api/niche/reply     — Generate engagement replies for a tweet

All error messages to the client are in Turkish.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.niches import VALID_NICHE_IDS
from services.niche_agent import (
    NicheAgentError,
    NicheReplyBlockedError,
    NicheReply,
    ScoredTweet,
    generate_reply,
    get_trending,
)

router = APIRouter(prefix="/api/niche", tags=["niche"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class TrendingRequest(BaseModel):
    niche_id: str = Field(
        ...,
        description="Niş kimliği: food, football, economy veya politics",
    )
    hours: int = Field(
        default=1,
        ge=1,
        le=24,
        description="Aranacak zaman penceresi (saat, 1–24)",
    )


class TrendingResponse(BaseModel):
    niche_id: str
    tweets: list[ScoredTweet]


class ReplyRequest(BaseModel):
    tweet_text: str = Field(
        ...,
        min_length=1,
        max_length=2800,
        description="Yanıt verilecek tweet metni",
    )
    niche_id: str = Field(
        ...,
        description="Niş kimliği: food, football, economy veya politics",
    )


class ReplyResponse(BaseModel):
    niche_id: str
    replies: list[NicheReply]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _validate_niche_id(niche_id: str) -> None:
    """Raise HTTP 422 with a Turkish message if *niche_id* is unknown."""
    if niche_id not in VALID_NICHE_IDS:
        valid = ", ".join(sorted(VALID_NICHE_IDS))
        raise HTTPException(
            status_code=422,
            detail=f"Geçersiz niş kimliği: '{niche_id}'. Geçerli değerler: {valid}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/trending", response_model=TrendingResponse)
async def trending(body: TrendingRequest) -> TrendingResponse:
    """
    Fetch trending tweet candidates for the given niche, score them with
    Claude, and return them ranked by engagement potential.

    - ``niche_id`` must be one of ``food``, ``football``, ``economy``,
      ``politics``.
    - ``hours`` is a recency hint (1–24).  Currently informational.

    Returns an empty ``tweets`` list if no results are found.
    """
    _validate_niche_id(body.niche_id)

    try:
        scored = await get_trending(body.niche_id, hours=body.hours)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except NicheAgentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return TrendingResponse(niche_id=body.niche_id, tweets=scored)


@router.post("/reply", response_model=ReplyResponse)
async def reply(body: ReplyRequest) -> ReplyResponse:
    """
    Generate up to three legally-safe Turkish engagement replies for the
    provided tweet text within the given niche context.

    - Replies are run through the legal-safety filter before being
      returned.
    - Returns HTTP 400 if all generated replies are blocked.
    - Returns HTTP 422 if ``niche_id`` is not recognised.
    """
    _validate_niche_id(body.niche_id)

    try:
        replies = await generate_reply(body.tweet_text, body.niche_id)
    except NicheReplyBlockedError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except NicheAgentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ReplyResponse(niche_id=body.niche_id, replies=replies)
