# TwitBoost

AI-powered Twitter reply assistant for Turkish Twitter users.

**Opposition Mode** — paste a tweet, get contradictions from the person's own past statements + legally-safe counter-replies with source citations.
**Niche Mode** — browse trending tweets in a niche (food, football, economy, politics), generate high-engagement replies.

**Status: Phase 1 complete** — personal use MVP, no auth, no payments. See [docs/ROADMAP.md](docs/ROADMAP.md).

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI (Python 3.14) |
| AI Core | Claude Sonnet (`claude-sonnet-4-20250514`) |
| Web Search | Brave Search API |
| Database | Supabase (Phase 2+) |
| Payments | LemonSqueezy in TRY (Phase 2+) |
| Deploy | Vercel (frontend) + Railway (backend) |

## Local Development

### 1. Environment variables

```bash
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, BRAVE_SEARCH_API_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/health
```

### 3. Frontend

```bash
cd frontend
npm install
cp env.local.example .env.local  # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

### 4. Tests

```bash
cd backend
.venv\Scripts\pytest             # Windows
# .venv/bin/pytest               # macOS/Linux
```

## Project Structure

```
tweetboost/
├── frontend/              # Next.js app
│   ├── app/               # Pages: /, /opposition, /niche
│   └── lib/api.ts         # Single API client (all backend calls go here)
├── backend/
│   ├── main.py            # FastAPI app + router registration
│   ├── routers/           # opposition.py, niche.py, research.py
│   ├── services/          # analysis_agent, niche_agent, brave_search, …
│   ├── prompts/           # Claude system prompts (.txt files)
│   └── config/niches.py   # Niche definitions — single source of truth
├── docs/                  # PRD, Architecture, Roadmap, Decisions
└── .env.example           # Required environment variables
```

## Legal

AI output references only publicly available statements, always with source URLs. No insults, unverified claims, or automated posting. See [docs/PRD.md §8](docs/PRD.md).
