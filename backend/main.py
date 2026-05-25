"""
TwitBoost — FastAPI Backend
Phase 2: Auth + usage limits added on top of Phase 1 pipeline.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="TwitBoost API",
    description="AI-powered Twitter reply tool — Opposition & Niche modes",
    version="0.1.0",
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

app.include_router(research_router)
app.include_router(opposition_router)
app.include_router(niche_router)
app.include_router(auth_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness probe — returns API version and status."""
    return {"status": "ok", "version": "0.1.0"}
