# CLAUDE.md — TwitBoost Project Memory

> This file is loaded at the start of every session. Keep it under 500 lines.
> Full details live in /docs/. Load them only when relevant.

---

## Project Identity

**Product:** TwitBoost (working name)
**Purpose:** AI-powered Twitter reply tool with two modes:
1. **Opposition Mode** — Research a troll's past statements, find inconsistencies, generate legally-safe counter-replies
2. **Niche Mode** — Monitor trending tweets in a chosen niche, generate high-engagement replies to grow followers

**Target Market:** Turkish Twitter users
**Business Model:** SaaS, subscription in TRY

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL + Auth + Storage) |
| AI Core | Claude API (claude-sonnet-4-20250514) |
| Web Search | Brave Search API |
| Payments | LemonSqueezy (TRY support) |
| Deploy | Vercel (frontend) + Railway (backend) |

**Deferred (Phase 3+):** Twitter API v2, AI image generation (Flux)

---

## Pricing Plans

| Plan | Price | Features |
|------|-------|----------|
| Niche Only | 54.99 TL/month | Niche mode, 4 niches available |
| Opposition | 109.99 TL/month | Opposition mode only |
| Full Access | 149.99 TL/month | Both modes |

All plans have daily usage limits (defined in docs/PRD.md).

---

## Phase Overview

- **Phase 1 (MVP):** Personal use only. Manual tweet input. No auth. Core AI pipeline.
- **Phase 2 (SaaS):** Auth, payments, usage limits, UI polish.
- **Phase 3:** Twitter API integration, AI image generation.

Current phase: **Phase 1**
See full roadmap: `docs/ROADMAP.md`

---

## Core Rules — Never Break These

1. **No hardcoded secrets.** All keys in `.env`. Update `.env.example` on every new variable.
2. **Write tests** for every new API endpoint before moving on.
3. **Legal safety first.** AI output must never contain insults or false accusations. Only quote the subject's own words with source links.
4. **Usage limits are enforced server-side**, never only on frontend.
5. **Turkish language support** is required in all user-facing strings.
6. **No Twitter API calls in Phase 1.** Use Brave Search + manual input only.

---

## Architecture at a Glance

```
User Input (tweet text)
        ↓
[FastAPI Backend]
        ↓
Phase 1: Person Identification (Brave Search)
Phase 2: Research Agent (Brave Search — parallel queries)
Phase 3: Inconsistency Analysis (Claude Sonnet)
Phase 4: Content Generation (Claude Sonnet)
        ↓
Output: Text + Source URLs (+ images from web in Phase 1)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `docs/PRD.md` | Full product requirements |
| `docs/ARCHITECTURE.md` | Detailed technical architecture |
| `docs/ROADMAP.md` | Phase breakdown and sprint plan |
| `docs/DECISIONS.md` | Why we chose X over Y |
| `docs/API_CONTRACTS.md` | All endpoint definitions |
| `.claude/COMMON_MISTAKES.md` | Known bugs and pitfalls |

---

## Session Startup Checklist

When starting a new session:
1. Read this file
2. Run `/gsd:resume-work` to see current task
3. Check `docs/ROADMAP.md` for phase context if needed
4. Never start coding without knowing which phase task you're in

---

## Skills in Use

| Skill | When to Load |
|-------|-------------|
| `gsd-setup` | Phase transitions, large tasks |
| `token-optimizer` | Every ~5 sessions or if context > 60% |
| `frontend-backend` | During API connection phase |
| `frontend-design` | During UI component work |
| `llm-council` | Critical architecture decisions |
