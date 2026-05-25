# ROADMAP.md — TwitBoost Development Roadmap

**Version:** 1.0
**Date:** May 2026
**Estimated total sessions:** 30+

---

## Phase Overview

| Phase | Name | Goal | Sessions Est. |
|-------|------|------|--------------|
| 1 | MVP | Working pipeline, personal use | 8-10 |
| 2 | SaaS | Auth + payments + multi-user | 10-12 |
| 3 | Power Features | Twitter API + image gen | 8-10 |

---

## PHASE 1 — MVP (Current)

**Goal:** A working web app usable by one person (you).
No auth. No payments. Core AI pipeline only.

### Sprint 1.1 — Project Setup (Sessions 1-2)
- [ ] Initialize Next.js 15 project (frontend)
- [ ] Initialize FastAPI project (backend)
- [ ] Set up Supabase project (even if not used yet — for later)
- [ ] Configure Railway + Vercel deployments
- [ ] Set up `.env` and `.env.example`
- [ ] Set up `.claudeignore` and GSD
- [ ] Basic health check endpoints

### Sprint 1.2 — Research Agent (Sessions 3-4)
- [ ] Brave Search API integration (Python service)
- [ ] Person identification from tweet text (Claude)
- [ ] Parallel search queries (4 concurrent)
- [ ] Content extraction from URLs
- [ ] Structured output: statements list with dates + sources

### Sprint 1.3 — Analysis + Generation (Sessions 5-6)
- [ ] Inconsistency analysis prompt (Claude Sonnet)
- [ ] Reply generation with 3 tone variants
- [ ] Legal safety filter (no insults, source required)
- [ ] Source URL + date formatting in output

### Sprint 1.4 — Niche Mode (Session 7)
- [ ] Trending tweet discovery (Brave Search)
- [ ] 4 niche configurations (food, football, economy, politics)
- [ ] Niche reply generation prompt

### Sprint 1.5 — Frontend (Sessions 8-9)
- [ ] Tweet input UI
- [ ] Mode selector (Opposition / Niche)
- [ ] Results display (reply variants + sources)
- [ ] Copy-to-clipboard for each variant
- [ ] Basic loading states

### Sprint 1.6 — Polish + Testing (Session 10)
- [ ] End-to-end testing of both modes
- [ ] Prompt quality review (test 20 real tweets)
- [ ] Error handling (Brave API down, Claude rate limit)
- [ ] Performance: pipeline under 30 seconds

**Phase 1 Done Criteria:**
- Both modes working
- Output quality rated 4/5 on 20 test cases
- Pipeline completes in < 30 seconds
- No crashes on bad input

---

## PHASE 2 — SaaS

**Goal:** Real users, real payments, real data.

### Sprint 2.1 — Auth (Sessions 11-12)
- [ ] Supabase Auth integration
- [ ] Email/password + Google OAuth
- [ ] Protected routes (frontend + backend)
- [ ] User plan storage

### Sprint 2.2 — Usage Limits (Sessions 13-14)
- [ ] Daily usage tracking (DB)
- [ ] Server-side limit enforcement
- [ ] Limit exceeded UI + upgrade prompt
- [ ] Usage counter display in UI

### Sprint 2.3 — Payments (Sessions 15-16)
- [ ] LemonSqueezy integration
- [ ] 3 plan setup (Niche / Opposition / Full)
- [ ] Webhook handler (plan activation/cancellation)
- [ ] Billing page in UI

### Sprint 2.4 — UI Polish (Sessions 17-18)
- [ ] Full responsive design
- [ ] Turkish language throughout
- [ ] Landing page
- [ ] Onboarding flow
- [ ] Plan upgrade flow

### Sprint 2.5 — SaaS Launch Prep (Sessions 19-20)
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

### Sprint 3.1 — Twitter API (Sessions 21-23)
- [ ] Twitter API v2 integration
- [ ] Real tweet fetching (not web search)
- [ ] BYOK option (user's own API key)
- [ ] Per-user Twitter quota tracking

### Sprint 3.2 — AI Image Generation (Sessions 24-26)
- [ ] Flux API integration
- [ ] Image prompt generation from tweet context
- [ ] Web image collection (Phase 1 upgrade)
- [ ] Image display in output

### Sprint 3.3 — Analytics + Growth (Sessions 27-29)
- [ ] User analytics dashboard (usage trends)
- [ ] Reply performance tracker (manual input)
- [ ] More niche options (expand from 4 to 10+)
- [ ] Saved replies library

### Sprint 3.4 — Scale (Session 30+)
- [ ] Performance optimization
- [ ] Caching layer (research cache)
- [ ] CDN for images
- [ ] Affiliate/referral system

---

## Decision Log

See `docs/DECISIONS.md` for why each technology was chosen.

---

## Notes

- **Do not start Phase 2 work during Phase 1.** No auth scaffolding in MVP.
- **Prompt quality is the product.** Spend extra sessions on prompts if needed.
- **Turkish language.** Every user-facing string must be in Turkish.
- **Legal filter is mandatory.** Never ship without it, even in MVP.
