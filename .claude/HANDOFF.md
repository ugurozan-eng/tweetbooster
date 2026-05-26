# TwitBoost — Sprint Handoff

> Updated after each sprint. Load this at the start of a new session to resume quickly.

---

## Last Completed Sprint

**Sprint 2.2 — Payments / Billing**
**Date:** 2026-05-26

### ✅ Sprint 2.2 COMPLETE

142/142 backend tests passing. `tsc --noEmit` clean. `next build` 9/9 clean.

### What was done this session

#### Backend changes
| File | Change |
|------|---------|
| `backend/migrations/002_subscriptions.sql` | ADD COLUMN lemonsqueezy_customer_id, lemonsqueezy_subscription_id, plan_expires_at + index |
| `backend/services/lemonsqueezy_client.py` | Singleton httpx.AsyncClient; get_subscription(), create_checkout() |
| `backend/services/subscription_service.py` | activate_plan, cancel_plan, get_active_plan with expiry auto-downgrade |
| `backend/services/auth_service.py` | get_user_plan() now delegates to subscription_service.get_active_plan() (local import to avoid circular deps) |
| `backend/routers/webhooks.py` | HMAC-SHA256 signature verification; routes 4 LemonSqueezy events; always HTTP 200 |
| `backend/routers/billing.py` | GET /api/billing/plans; POST /api/billing/checkout; GET /api/billing/status |
| `backend/main.py` | Registers billing + webhooks routers; startup warnings for all 6 LS env vars |
| `backend/tests/test_subscription_service.py` | 12 tests: activate (known/unknown variant), cancel, get_active_plan (active/expired/null/no-row/malformed/db-error) |
| `backend/tests/test_webhooks.py` | 11 tests: all 4 events, bad sig, missing sig, missing secret, unknown event, internal error → 200, missing user_id → 200 |
| `backend/tests/test_auth_service.py` | Fixed 3 tests: get_user_plan_* now patches services.subscription_service.get_service_client |

#### Frontend changes
| File | Change |
|------|---------|
| `frontend/lib/api.ts` | apiGet helper (GET with auth); BillingPlan/BillingStatus/CheckoutResponse types; getBillingPlans, getBillingStatus, createCheckout |
| `frontend/app/billing/page.tsx` | HESABIM page: current plan banner, 3 plan cards (active = red fill), SATIN AL → checkout redirect |
| `frontend/app/layout.tsx` | Added HESABIM nav link |
| `frontend/proxy.ts` | Added /billing to PROTECTED_PATHS |
| `.env.example` | Added LEMONSQUEEZY_VARIANT_NICHE_ID, LEMONSQUEEZY_VARIANT_OPPOSITION_ID, LEMONSQUEEZY_VARIANT_FULL_ID |

#### Auth bypass (still active)
- `frontend/proxy.ts`: `return NextResponse.next()` at top
- `backend/middleware/auth_middleware.py`: dev user fallback
- **To restore:** remove bypass lines (clearly commented in both files)

### Test count
**142 / 142 passing** (+23 from Sprint 2.2: 12 subscription + 11 webhook tests)

### Security guarantees implemented
- ✅ Webhook signature check (HMAC-SHA256) — non-negotiable
- ✅ Variant IDs from env vars only — never hardcoded
- ✅ plan_expires_at checked on every authenticated request via get_active_plan()
- ✅ Internal webhook errors return HTTP 200 (never trigger LemonSqueezy retries)

---

## Previous Sprint

**Neo-Brutalist Redesign Sprint + twitter_handle input**
**Date:** 2026-05-26

119/119 backend tests passing. `tsc --noEmit` clean. `next build` 8/8 clean.
- IBM Plex Mono replaces JetBrains Mono; neo-brutalist design across all pages
- twitter_handle fast-path: skip Gemini when handle is provided
- Full redesign: page.tsx, opposition/page.tsx, niche/page.tsx, login/page.tsx

---

## Next Sprint

**Sprint 2.3 — Usage Limits UI**

Before coding:
1. Apply migration `002_subscriptions.sql` in Supabase SQL Editor
2. Set all 6 LemonSqueezy env vars in `backend/.env`
3. Set LemonSqueezy webhook URL in LemonSqueezy dashboard: `https://<domain>/api/webhooks/lemonsqueezy`
4. Remove auth bypass (both files) before production deploy

Tasks:
1. `GET /api/usage/me` — daily usage details (current count + limit + reset time)
2. UI: usage counter in header (e.g. "3/20 kullanım")
3. Test: verify 429 fires correctly at the limit boundary
4. Integration test: full auth + limit flow with real Supabase project
5. Remove auth bypass and test full login → billing → analysis flow

---

## Environment Setup Reminder

```bash
# Backend
cd backend
# Create .env from .env.example, fill ALL keys:
#   GEMINI_API_KEY=...               (https://aistudio.google.com/apikey)
#   BRAVE_SEARCH_API_KEY=...
#   SUPABASE_URL=...
#   SUPABASE_ANON_KEY=...
#   SUPABASE_SERVICE_ROLE_KEY=...
#   LEMONSQUEEZY_API_KEY=...         (https://app.lemonsqueezy.com/settings/api)
#   LEMONSQUEEZY_STORE_ID=...
#   LEMONSQUEEZY_WEBHOOK_SECRET=...
#   LEMONSQUEEZY_VARIANT_NICHE_ID=...
#   LEMONSQUEEZY_VARIANT_OPPOSITION_ID=...
#   LEMONSQUEEZY_VARIANT_FULL_ID=...
# Apply migrations/001_initial_auth.sql AND 002_subscriptions.sql in Supabase SQL Editor
uvicorn main:app --reload

# Frontend (frontend/.env.local already exists with Supabase keys)
cd frontend
npm run dev

# Tests
cd backend
& "c:\Claude Projects\tweetboost\backend\.venv\Scripts\pytest.exe" tests/
```

---

## API Reference (quick)

| Method | Path | Auth required | Body |
|--------|------|---------------|------|
| GET | `/health` | No | — |
| POST | `/api/auth/me` | Yes (JWT) | — |
| POST | `/api/research/identify` | No | `{tweet_text}` |
| POST | `/api/research/run` | No | `{name, topic}` |
| POST | `/api/opposition/analyze` | Yes (JWT) | `{tweet_text, tones?, twitter_handle?}` |
| POST | `/api/niche/trending` | Yes (JWT) | `{niche_id, hours?}` |
| POST | `/api/niche/reply` | Yes (JWT) | `{tweet_text, niche_id}` |
| GET | `/api/billing/plans` | No | — |
| POST | `/api/billing/checkout` | Yes (JWT) | `{plan_id}` |
| GET | `/api/billing/status` | Yes (JWT) | — |
| POST | `/api/webhooks/lemonsqueezy` | Signature | LemonSqueezy webhook payload |

Full contracts: `docs/API_CONTRACTS.md`

---

## Plan Limits (from docs/PRD.md §4)

| Plan | Daily limit | Modes | Price |
|------|------------|-------|-------|
| trial | 3 | both | free |
| niche | 20 | niche only | 54.99 TL/mo |
| opposition | 15 | opposition only | 109.99 TL/mo |
| full | 30 | both | 149.99 TL/mo |

Reset: midnight Istanbul time (UTC+3 / `Europe/Istanbul`)
