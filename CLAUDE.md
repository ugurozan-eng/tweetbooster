# CLAUDE.md — TwitBoost Project Memory

> This file is loaded at the start of every session. Keep it under 500 lines.
> Full details live in /docs/. Load them only when relevant.

---

## Project Identity

**Product:** TwitBoost (working name)
**Purpose:** AI-powered Twitter reply tool with two modes:
1. **Opposition Mode** — Research a public figure's past statements, find inconsistencies, generate legally-safe counter-replies
2. **Niche Mode** — Monitor trending tweets in a chosen niche, generate high-engagement replies to grow followers

**Target Market:** Turkish Twitter users
**Business Model:** SaaS, subscription in TRY

---

## Current Phase

**Phase 1 — MVP: COMPLETE** (as of Sprint 1.6, 2026-05-26)
- Both modes working end-to-end
- 85/85 backend tests passing
- No auth, no payments (Phase 2 scope)

**Next:** Phase 2 — SaaS (auth + payments + usage limits)
See full roadmap: `docs/ROADMAP.md`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js **16.2.6**, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI (Python 3.14) |
| Database | Supabase (Phase 2+) |
| AI Core | Claude API (`claude-sonnet-4-20250514`) |
| Web Search | Brave Search API |
| Payments | LemonSqueezy (TRY support) — Phase 2+ |
| Deploy | Vercel (frontend) + Railway (backend) |

> Note: Next.js 16.2.6 is the current latest (May 2026). PRD says "15" — that is outdated.

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

## Core Rules — Never Break These

1. **No hardcoded secrets.** All keys in `.env`. Update `.env.example` on every new variable.
2. **Write tests** for every new API endpoint before moving on.
3. **Legal safety first.** AI output must never contain insults or false accusations. Only quote the subject's own words with source links.
4. **Usage limits are enforced server-side**, never only on frontend.
5. **Turkish language support** is required in all user-facing strings.
6. **No Twitter API calls in Phase 1.** Use Brave Search + manual input only.
7. **No auth or payment code in Phase 1.** Phase 2 starts fresh.

---

## Architecture at a Glance

```
User Input (tweet text)
        ↓
[FastAPI Backend]
        ↓
Step 1: Person Identification (Claude Sonnet)
Step 2: Research Agent (Brave Search — 4 parallel queries)
Step 3: Inconsistency Analysis (Claude Sonnet)
Step 4: Content Generation (Claude Sonnet × tones)
Step 5: Legal Safety Filter (pure regex — no Claude)
        ↓
Output: Text + Source URLs
```

**Niche Mode pipeline:**
```
User selects niche + hours
        ↓
Brave Search (3 parallel queries from niches.py)
        ↓
Claude: score + rank tweets (0–10)
        ↓
User clicks tweet → Claude: generate 3 replies
        ↓
Legal Safety Filter → return passing replies
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
| `backend/config/niches.py` | **Single source of truth** for all niche configs |
| `frontend/lib/api.ts` | **Single source of truth** for all frontend API calls |

---

## Session Startup Checklist

When starting a new session:
1. Read this file
2. Read `.claude/HANDOFF.md` to see exactly where the last session ended
3. Check `docs/ROADMAP.md` for phase context if needed
4. Never start coding without knowing which phase/sprint task you're in

## Session End — MANDATORY

At the end of EVERY session, before the final push, update `.claude/HANDOFF.md` with:
- Last completed sprint name and number
- Next sprint name and number
- Total test count (passing/total)
- Last commit hash
- Any blockers, edge cases, or notes for next session

This is non-negotiable. Every session ends with a HANDOFF.md update and push.

---

## Skills in Use

| Skill | When to Load |
|-------|-------------|
| `gsd-setup` | Phase transitions, large tasks |
| `token-optimizer` | Every ~5 sessions or if context > 60% |
| `frontend-backend` | During API connection phase |
| `frontend-design` | During UI component work |
| `llm-council` | Critical architecture decisions |
