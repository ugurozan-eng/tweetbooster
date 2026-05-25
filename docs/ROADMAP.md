# ROADMAP.md — TwitBoost Development Roadmap

**Version:** 1.1
**Updated:** 2026-05-26

---

## Phase Overview

| Phase | Name | Goal | Status |
|-------|------|------|--------|
| 1 | MVP | Working pipeline, personal use | ✅ Complete (2026-05-26) |
| 2 | SaaS | Auth + payments + multi-user | 🔜 Next |
| 3 | Power Features | Twitter API + image gen | ⏳ Planned |

---

## PHASE 1 — MVP ✅ COMPLETE

**Completed:** 2026-05-26
**Note:** Phase 1 complete — personal use validated. Both modes (Opposition + Niche) working end-to-end.

### Sprint 1.1 — Project Setup ✅
- [x] Initialize Next.js project (frontend) — v16.2.6
- [x] Initialize FastAPI project (backend)
- [x] Set up `.env` and `.env.example`
- [x] Basic health check endpoints (`GET /health`)
- [x] Project structure + README

### Sprint 1.2 — Research Agent ✅
- [x] Brave Search API integration with rate limiting (1 req/sec semaphore)
- [x] Person identification from tweet text (Claude Sonnet)
- [x] Parallel search queries (4 concurrent via asyncio.gather)
- [x] Structured output: `SearchResult` TypedDict with dates + sources

### Sprint 1.3 — Analysis + Generation ✅
- [x] Inconsistency analysis prompt (`inconsistency_analyzer.txt`)
- [x] Reply generation with 3 tone variants (cold / sharp / thread)
- [x] Legal safety filter — pure regex, zero Claude calls (TCK §125-131)
- [x] Source URL + date formatting in output

### Sprint 1.4 — Niche Mode ✅
- [x] Niche config single source of truth (`config/niches.py`)
- [x] 4 niche configurations (food, football, economy, politics)
- [x] Tweet scoring prompt + niche reply generation prompt
- [x] `get_trending()` + `generate_reply()` with safety filter
- [x] `POST /api/niche/trending` + `POST /api/niche/reply`

### Sprint 1.5 — Frontend ✅
- [x] Next.js 16 + TypeScript + Tailwind v4
- [x] Single API client (`frontend/lib/api.ts`) — all backend calls centralized
- [x] Opposition Mode page — tweet input, tone selector, results + copy
- [x] Niche Mode page — niche picker, trending list, inline reply generation
- [x] Dark UI, Turkish language throughout, mobile responsive

### Sprint 1.6 — Polish + Testing ✅
- [x] End-to-end routing and validation verified against live backend
- [x] 30-second AbortController timeout on every frontend fetch
- [x] Network-down error → Turkish message (not raw JS error)
- [x] `AnalysisTimeoutError` — 25s Claude timeout → HTTP 504
- [x] Bug fix: `AnalyzeResponse` now returns `sources: list[str]` (was `total_sources: int`)
- [x] All 85 backend tests passing
- [x] TypeScript `tsc --noEmit` clean
- [x] `next build` clean

**Phase 1 Done Criteria:**
- ✅ Both modes working (routing, validation, error handling verified)
- ✅ Pipeline under 30 seconds (timeout enforced at both backend and frontend)
- ✅ No crashes on bad input (422 Turkish messages for all invalid inputs)
- ✅ Legal safety filter running on every AI output

---

## PHASE 2 — SaaS

**Goal:** Real users, real payments, real data.

### Sprint 2.1 — Auth ✅
- [x] Supabase Auth integration (supabase_client.py singleton)
- [x] Email/password + Google OAuth (login/page.tsx + auth/callback/route.ts)
- [x] Protected routes — proxy.ts (frontend) + get_current_user dependency (backend)
- [x] User plan storage (users table + daily_usage view in migrations/001)
- [x] JWT verification with python-jose (auth_service.py)
- [x] Plan permission + daily limit enforcement (plan_checker.py)
- [x] Usage logging server-side (log_usage in plan_checker.py)
- [x] POST /api/auth/me — user info + plan + today's usage

### Sprint 2.2 — Usage Limits
- [ ] Daily usage tracking (DB)
- [ ] Server-side limit enforcement
- [ ] Limit exceeded UI + upgrade prompt
- [ ] Usage counter display in UI

### Sprint 2.3 — Payments
- [ ] LemonSqueezy integration
- [ ] 3 plan setup (Niche / Opposition / Full)
- [ ] Webhook handler (plan activation/cancellation)
- [ ] Billing page in UI

### Sprint 2.4 — UI Polish
- [ ] Full responsive design review
- [ ] Landing/marketing page
- [ ] Onboarding flow
- [ ] Plan upgrade flow

### Sprint 2.5 — SaaS Launch Prep
- [ ] KVKK compliance (privacy policy, data processing)
- [ ] Terms of service
- [ ] Error monitoring (Sentry or similar)
- [ ] Rate limiting (API abuse protection)
- [ ] Beta user testing (5-10 users)

**Phase 2 Done Criteria:**
- 10+ paying users
- Payments processing correctly
- No data leaks between users
- KVKK compliant

---

## PHASE 3 — Power Features

**Goal:** Differentiation. Features competitors can't easily copy.

### Sprint 3.1 — Twitter API
- [ ] Twitter API v2 integration
- [ ] Real tweet fetching (not web search)
- [ ] BYOK option (user's own API key)

### Sprint 3.2 — AI Image Generation
- [ ] Flux API integration
- [ ] Image prompt generation from tweet context

### Sprint 3.3 — Analytics + Growth
- [ ] More niche options (expand from 4 to 10+)
- [ ] Reply performance tracker
- [ ] Saved replies library

---

## Decision Log

See `docs/DECISIONS.md` for why each technology was chosen.

---

## Notes

- **Do not start Phase 2 work during Phase 1.** No auth scaffolding in MVP.
- **Prompt quality is the product.** Spend extra sessions on prompts if needed.
- **Turkish language.** Every user-facing string must be in Turkish.
- **Legal filter is mandatory.** Never ship without it, even in MVP.
- **Next.js version is 16.2.6** (latest as of May 2026), not "15" as originally planned.
