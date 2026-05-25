# DECISIONS.md — Architecture Decision Log

Every significant technical or product decision is recorded here.
Format: Decision | Alternatives Considered | Reason

---

## D-001: Brave Search API over Tavily

**Decision:** Use Brave Search API as primary web search provider
**Alternatives:** Tavily, Exa, Perplexity Sonar, Firecrawl
**Date:** May 2026

**Reason:**
- Brave runs its own independent index (30B+ pages) — not dependent on Google or Bing
- Bing Search API retired August 2025, making independent indexes more valuable
- Brave is in top benchmark tier alongside Firecrawl and Exa (AIMultiple 2026)
- Tavily was acquired by Nebius (Feb 2026) — pricing uncertainty risk
- $5/1k queries is competitive pricing
- No legal/ToS risk vs. Google-scraping alternatives (SerpAPI lawsuit Dec 2025)

---

## D-002: Claude Sonnet as sole AI model

**Decision:** Use claude-sonnet-4-20250514 for all AI tasks
**Alternatives:** GPT-4o, Gemini 3.5 Flash, mixture
**Date:** May 2026

**Reason:**
- Best-in-class for long context analysis (inconsistency detection requires reading many sources)
- Turkish language quality superior to competitors
- Already in Claude ecosystem — no additional API accounts
- Sonnet is better value than Opus for this use case; Haiku not good enough for nuanced political analysis
- Gemini 3.5 Flash is strong but keeping stack simple is a priority

---

## D-003: Twitter API deferred to Phase 3

**Decision:** Phase 1 and 2 use Brave Search for tweet discovery, not Twitter API
**Alternatives:** Start with Twitter API v2 immediately
**Date:** May 2026

**Reason:**
- Twitter API Basic tier: $100/month, only 10K tweet reads/month
- For a single user (Phase 1) this is wasteful
- For SaaS (Phase 2) this limit blows up quickly without BYOK
- Brave Search can find recent tweets via web indexing — sufficient for MVP
- Phase 3 will implement BYOK model where users provide their own API key

---

## D-004: FastAPI over Node.js/Express for backend

**Decision:** Use FastAPI (Python) for backend
**Alternatives:** Node.js + Express, Next.js API routes
**Date:** May 2026

**Reason:**
- Developer preference and existing expertise
- Python ecosystem is better for AI/LLM integrations (Anthropic SDK, async HTTP)
- FastAPI async support is excellent for parallel Brave Search queries
- Next.js API routes would couple frontend and backend — bad for future scaling

---

## D-005: No direct Twitter posting in app

**Decision:** App generates copy-paste text only; user posts manually
**Alternatives:** Direct Twitter OAuth + post from app
**Date:** May 2026

**Reason:**
- Legal risk reduction: if user reviews and manually posts, app is a tool not a publisher
- Twitter automation rules are strict — auto-posting reply bots can get accounts banned
- Simpler MVP scope
- Users actually want to review before posting

---

## D-006: LemonSqueezy for payments

**Decision:** Use LemonSqueezy for subscription management
**Alternatives:** Stripe, iyzico, Paddle
**Date:** May 2026

**Reason:**
- Developer preference (already used in other projects)
- TRY (Turkish Lira) currency support
- Merchant of Record model — LemonSqueezy handles VAT/tax
- Simpler integration than Stripe for SaaS subscriptions
- Needs verification: confirm TRY support before Phase 2 starts

---

## D-007: Supabase for database + auth

**Decision:** Use Supabase for all data storage and authentication
**Alternatives:** PlanetScale, Railway PostgreSQL, Firebase
**Date:** May 2026

**Reason:**
- Developer preference and existing expertise
- Auth + PostgreSQL + Storage in one service
- Free tier sufficient for Phase 1-2 early stage
- Row Level Security for multi-tenant data isolation
- Already used in other projects — no new tooling to learn

---

## OPEN DECISIONS

- [ ] **D-008:** Final product name (TwitBoost is placeholder)
- [ ] **D-009:** Image generation provider in Phase 3 (Flux vs DALL-E 3)
- [ ] **D-010:** BYOK vs shared Twitter API pool in Phase 3
- [ ] **D-011:** LemonSqueezy TRY support — verify before Phase 2
