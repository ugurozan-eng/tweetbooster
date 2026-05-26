"""
TwitBoost — FastAPI Backend
Phase 2: Auth + usage limits added on top of Phase 1 pipeline.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------

_LS_VARS = [
    "LEMONSQUEEZY_API_KEY",
    "LEMONSQUEEZY_STORE_ID",
    "LEMONSQUEEZY_WEBHOOK_SECRET",
    "LEMONSQUEEZY_VARIANT_NICHE_ID",
    "LEMONSQUEEZY_VARIANT_OPPOSITION_ID",
    "LEMONSQUEEZY_VARIANT_FULL_ID",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log warnings for critical missing env vars at startup."""
    if not os.environ.get("GEMINI_API_KEY"):
        logging.warning("[startup] GEMINI_API_KEY is not set. AI features will not work.")
    for var in _LS_VARS:
        if not os.environ.get(var):
            logging.warning("[startup] %s is not set. Billing features will not work.", var)
    yield


app = FastAPI(
    title="TwitBoost API",
    description="AI-powered Twitter reply tool — Opposition & Niche modes",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — development allows all origins; tighten in Phase 2 production deploy
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO(Phase 2): restrict to Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from routers.research import router as research_router      # Sprint 1.2
from routers.opposition import router as opposition_router  # Sprint 1.3
from routers.niche import router as niche_router            # Sprint 1.4
from routers.auth import router as auth_router              # Sprint 2.1
from routers.billing import router as billing_router        # Sprint 2.2
from routers.webhooks import router as webhooks_router      # Sprint 2.2

app.include_router(research_router)
app.include_router(opposition_router)
app.include_router(niche_router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(webhooks_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness probe — returns API version and status."""
    return {"status": "ok", "version": "0.1.0"}
