# TwitBoost

TwitBoost is an AI-powered Twitter reply assistant built for Turkish Twitter users, offering two modes: **Opposition Mode** (*Muhalif Mod*), which researches a target account's public statements via web search, identifies inconsistencies using Claude AI, and generates legally-safe, evidence-backed counter-replies with source citations; and **Niche Mode**, which discovers trending tweets in user-selected niches (food, football, economy, politics) and generates high-engagement replies optimised for follower growth — all without direct posting, keeping the user in full control.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (latest), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| AI Core | Claude Sonnet (Anthropic API) |
| Web Search | Brave Search API |
| Database | Supabase (Phase 2+) |
| Payments | LemonSqueezy in TRY (Phase 2+) |
| Deploy | Vercel (frontend) + Railway (backend) |

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # fill in your keys
uvicorn main:app --reload
# → http://localhost:8000/health
```

### Frontend
```bash
cd frontend
npm install
cp ../.env.example .env.local  # add NEXT_PUBLIC_* vars as needed
npm run dev
# → http://localhost:3000
```

## Project Structure

```
tweetboost/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
│   ├── main.py
│   ├── routers/       # Route handlers (Sprint 1.2+)
│   ├── services/      # Business logic (Sprint 1.2+)
│   ├── prompts/       # Claude system prompts as .txt files
│   └── requirements.txt
├── docs/              # PRD, Architecture, Roadmap, Decisions
├── .env.example       # All required environment variables
└── CLAUDE.md          # AI session memory
```

## Current Phase

**Phase 1 — MVP** (personal use, no auth, no payments).
See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full sprint plan.

## Legal

AI-generated output references only publicly available statements by the subject, always with source URLs. No insults, unverified claims, or automated posting. See [`docs/PRD.md §8`](docs/PRD.md) for the full legal disclaimer.
