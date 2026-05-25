# TwitBoost — Sprint Handoff

> Updated after each sprint. Load this at the start of a new session to resume quickly.

---

## Last Completed Sprint

**Sprint 2.1 — Auth**
**Commit:** `8c6786a`
**Date:** 2026-05-26

### ✅ Sprint 2.1 is now COMPLETE

Full auth layer implemented. 115 tests passing. Clean build.

### What was done this sprint

| Area | Change |
|------|--------|
| **Backend deps** | `requirements.txt`: added supabase==2.15.1, python-jose[cryptography]==3.3.0, passlib==1.7.4, tzdata==2026.2 |
| **Env vars** | `.env.example`: added `SUPABASE_JWT_SECRET`; `frontend/env.local.example`: added `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY` |
| **DB schema** | `migrations/001_initial_auth.sql`: `users`, `usage_logs` tables + `daily_usage` view + RLS policies |
| **Supabase client** | `services/supabase_client.py`: `lru_cache` singletons for anon + service role clients |
| **Auth service** | `services/auth_service.py`: `verify_jwt()`, `get_user_plan()`, `create_user_if_not_exists()` |
| **Auth middleware** | `middleware/auth_middleware.py`: `get_current_user` FastAPI dependency, HTTP 401 Turkish |
| **Plan checker** | `services/plan_checker.py`: `check_permission()` (sync), `check_daily_limit()` (async), `log_usage()` |
| **Router updates** | `opposition.py` + `niche.py`: `Depends(get_current_user)` + permission + limit check + usage log |
| **Auth router** | `routers/auth.py`: `POST /api/auth/me` → user_id, email, plan, usage_today |
| **Frontend lib** | `lib/supabase.ts`: singleton client + cookie helpers + `getAccessToken()` |
| **Login page** | `app/login/page.tsx`: email+password form + Google OAuth + Turkish error messages |
| **OAuth callback** | `app/auth/callback/route.ts`: code exchange, sets `twitboost-authed` cookie |
| **Route protection** | `proxy.ts` (Next.js 16): protects `/opposition` and `/niche` routes |
| **API client** | `lib/api.ts`: dynamic import `getAccessToken()`, attaches `Authorization: Bearer` |
| **Auth header** | `components/AuthHeader.tsx`: client component, shows email + logout button |
| **Layout** | `app/layout.tsx`: AuthHeader in nav, updated footer to Faz 2 |
| **Tests** | `test_auth_service.py` (9 tests) + `test_plan_checker.py` (21 tests) |

### Test count
**115 / 115 passing** (was 85 at end of Sprint 1.6)

New tests: 30 total (9 auth_service + 21 plan_checker)

### Architecture decisions made

1. **JWT verification**: HS256 with `SUPABASE_JWT_SECRET` via `python-jose` — standard Supabase JWT flow
2. **Route protection**: `proxy.ts` (renamed from `middleware.ts` in Next.js 16) with presence cookie only (no JWT verification at edge)
3. **Daily limit reset**: midnight `Europe/Istanbul` (UTC+3) via `ZoneInfo` — matches PRD §4
4. **Usage logging**: server-side only (`log_usage` called after success, never trusted from frontend)
5. **Plan defaults**: users not in DB → `trial` plan (3 req/day, both modes)
6. **First-login upsert**: `POST /api/auth/me` calls `create_user_if_not_exists` — frontend calls this after every sign-in

### Blockers / Notes for Sprint 2.2

- **Migration not applied yet**: `migrations/001_initial_auth.sql` needs to be run in Supabase SQL Editor before Sprint 2.2 can be tested
- **Supabase project needed**: create a Supabase project and fill in all 4 env vars (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`)
- **Google OAuth**: requires Supabase project to have Google OAuth provider configured
- **CORS still `allow_origins=["*"]`**: restrict to Vercel domain before public deploy
- **`tzdata==2026.2`**: Windows-only requirement; Linux/Mac can omit (built-in IANA db)
- **Supabase `gotrue` deprecation warning**: `supabase==2.15.1` uses deprecated gotrue package — not a blocker but worth noting
- **Full E2E test**: requires all 4 Supabase env vars + real API keys + migration applied

---

## Next Sprint

**Sprint 2.2 — Usage Limits**

Before coding, confirm migration 001 is applied in Supabase.

Tasks:
1. `GET /api/usage/me` — daily usage details (current count + limit + reset time)
2. UI: usage counter in header (e.g. "3/20 kullanım")
3. Test: verify 429 fires correctly at the limit boundary
4. Test the full auth + limit flow with real Supabase project

---

## Environment Setup Reminder

```bash
# Backend
cd backend
.venv\Scripts\activate        # Windows (venv already exists)
# Fill in .env from .env.example (ALL keys including Supabase)
# Apply migrations/001_initial_auth.sql in Supabase SQL Editor
uvicorn main:app --reload

# Frontend
cd frontend
cp env.local.example .env.local
# Fill in: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
npm run dev

# Tests
cd backend
.venv\Scripts\pytest
```

---

## API Reference (quick)

| Method | Path | Auth required | Body |
|--------|------|---------------|------|
| GET | `/health` | No | — |
| POST | `/api/auth/me` | Yes (JWT) | — |
| POST | `/api/research/identify` | No | `{tweet_text}` |
| POST | `/api/research/run` | No | `{name, topic}` |
| POST | `/api/opposition/analyze` | Yes (JWT) | `{tweet_text, tones?}` |
| POST | `/api/niche/trending` | Yes (JWT) | `{niche_id, hours?}` |
| POST | `/api/niche/reply` | Yes (JWT) | `{tweet_text, niche_id}` |

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
