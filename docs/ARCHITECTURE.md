# ARCHITECTURE.md — TwitBoost Technical Architecture

**Version:** 1.0
**Date:** May 2026

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (Vercel)                   │
│              Next.js 15 + TypeScript + Tailwind         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / REST
┌────────────────────────▼────────────────────────────────┐
│                    BACKEND (Railway)                    │
│                      FastAPI (Python)                   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Research   │  │   Analysis   │  │   Generation  │  │
│  │   Agent     │  │    Agent     │  │     Agent     │  │
│  │(Brave API)  │  │ (Claude API) │  │ (Claude API)  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                                                         │
└────────────┬──────────────────────┬─────────────────────┘
             │                      │
┌────────────▼──────┐   ┌──────────▼────────────────────┐
│  Supabase         │   │  External APIs                │
│  - PostgreSQL     │   │  - Brave Search API           │
│  - Auth           │   │  - Claude API (Anthropic)     │
│  - Storage        │   │  - LemonSqueezy (Phase 2)     │
└───────────────────┘   │  - Twitter API v2 (Phase 3)  │
                        └──────────────────────────────┘
```

---

## 2. Core Pipeline

### 2.1 Opposition Mode Pipeline

```
INPUT: Raw tweet text (pasted by user)
         │
         ▼
[Step 1] PERSON IDENTIFICATION
  - Extract name/handle from tweet text (Claude)
  - Brave Search: "{name} site:twitter.com OR site:haberler.com OR site:cnnturk.com"
  - Output: person profile (name, role, party/affiliation)
         │
         ▼
[Step 2] PARALLEL RESEARCH (Brave Search — 4 concurrent queries)
  Query A: "{name} eski açıklama beyanat" (past statements)
  Query B: "{name} twitter geçmiş" (twitter history via web)
  Query C: "{name} çelişki tutarsızlık" (contradictions)
  Query D: "{name} {current tweet topic}" (topic-specific history)
  - Output: list of URLs + snippets with dates
         │
         ▼
[Step 3] CONTENT EXTRACTION
  - Fetch full text from top 5 most relevant URLs (Brave extract)
  - Filter: keep only content with dates
  - Output: structured list of statements with dates and sources
         │
         ▼
[Step 4] INCONSISTENCY ANALYSIS (Claude Sonnet)
  - System prompt: legal safety rules, factual-only mode
  - Input: current tweet + historical statements
  - Output: contradiction map with confidence scores
         │
         ▼
[Step 5] REPLY GENERATION (Claude Sonnet)
  - Input: contradiction map + tone selection
  - Output: 3 reply variants (Cold/Sharp/Thread)
  - Each variant: tweet text + evidence footnotes + source URLs
         │
         ▼
OUTPUT: Reply package (text + sources + web images)
```

### 2.2 Niche Mode Pipeline

```
INPUT: User selects niche + time window (default: last 1 hour)
         │
         ▼
[Step 1] TRENDING TWEET DISCOVERY (Brave Search)
  - Query: "{niche keywords} lang:tr" with date filter
  - Output: top 10 tweet URLs + engagement signals
         │
         ▼
[Step 2] TWEET CONTENT FETCH
  - Extract tweet text + author info from URLs
  - Sort by estimated engagement
         │
         ▼
[Step 3] USER SELECTS TARGET TWEET
         │
         ▼
[Step 4] REPLY GENERATION (Claude Sonnet)
  - System prompt: follower growth optimization
  - Rules: add value, invite engagement, sound human, < 240 chars
  - Output: 3 reply options
         │
         ▼
OUTPUT: 3 ready-to-copy replies
```

---

## 3. Database Schema (Supabase / PostgreSQL)

```sql
-- Phase 2+ only. Phase 1 has no persistent storage.

-- Users (managed by Supabase Auth)
users (
  id uuid PRIMARY KEY,
  email text,
  plan text CHECK (plan IN ('niche', 'opposition', 'full', 'trial')),
  created_at timestamptz
)

-- Usage Tracking
usage_logs (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  mode text CHECK (mode IN ('opposition', 'niche')),
  created_at timestamptz DEFAULT now()
)

-- Daily Limits View
daily_usage (
  user_id uuid,
  date date,
  opposition_count int,
  niche_count int,
  total_count int
)

-- Research Cache (avoid re-searching same person)
research_cache (
  id uuid PRIMARY KEY,
  person_identifier text UNIQUE,
  data jsonb,
  fetched_at timestamptz,
  expires_at timestamptz
)
```

---

## 4. API Endpoints

Full contracts in `docs/API_CONTRACTS.md`

### Core endpoints (Phase 1):

```
POST /api/opposition/analyze
  Body: { tweet_text: string, tone: "cold"|"sharp"|"thread" }
  Returns: { reply_variants: [], sources: [], images: [] }

POST /api/niche/trending
  Body: { niche: "food"|"football"|"economy"|"politics", hours: number }
  Returns: { tweets: [{ text, url, estimated_engagement }] }

POST /api/niche/reply
  Body: { tweet_text: string, niche: string }
  Returns: { reply_variants: [] }
```

---

## 5. Environment Variables

```bash
# AI
ANTHROPIC_API_KEY=

# Search
BRAVE_SEARCH_API_KEY=

# Supabase (Phase 2)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Payments (Phase 2)
LEMONSQUEEZY_API_KEY=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_WEBHOOK_SECRET=

# Twitter (Phase 3)
TWITTER_BEARER_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=
```

---

## 6. Claude API Usage

**Model:** `claude-sonnet-4-20250514` for all tasks
**Max tokens per request:** 1500 output
**System prompts:** stored in `/backend/prompts/` as `.txt` files — never hardcoded

### Token budget per pipeline run:

| Step | Estimated Tokens | Cost (USD) |
|------|-----------------|-----------|
| Person identification | ~500 | ~$0.001 |
| Inconsistency analysis | ~2000 | ~$0.004 |
| Reply generation | ~1500 | ~$0.003 |
| **Total per run** | **~4000** | **~$0.008** |

At 100 daily requests: ~$0.80/day → ~$24/month

---

## 7. Brave Search API Usage

- **Endpoint:** `https://api.search.brave.com/res/v1/web/search`
- **Per opposition run:** 4-6 queries
- **Per niche run:** 1-2 queries
- **Rate limit:** 1 req/second on free tier
- **Plan needed:** Startup ($30/month) for production

---

## 8. Deployment

### Frontend (Vercel)
```bash
vercel --prod
# Auto-deploys on git push to main
```

### Backend (Railway)
```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

---

## 9. Phase 3 Architecture Additions

When Twitter API is added:
- New service: `TwitterService` — handles user timeline fetch, search
- BYOK option: users bring their own Twitter API key (stored encrypted in Supabase)
- Rate limiting: per-user Twitter API quota tracking

When image generation is added:
- New service: `ImageService` — Flux API integration
- Storage: Supabase Storage bucket for generated images
- Output: image URL added to reply package
