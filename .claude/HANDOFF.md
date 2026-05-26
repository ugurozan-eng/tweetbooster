# TwitBoost — Sprint Handoff

> Updated after each sprint. Load this at the start of a new session to resume quickly.

---

## Last Completed Sprint

**Neo-Brutalist Redesign Sprint + twitter_handle input**
**Date:** 2026-05-26

### ✅ Neo-brutalist redesign + twitter_handle input COMPLETE

119/119 backend tests passing. `tsc --noEmit` clean. `next build` 8/8 clean.

### What was done this session

#### Backend changes
| File | Change |
|------|---------|
| `backend/routers/opposition.py` | `AnalyzeRequest` gets `twitter_handle: str \| None = None`; passed to `identify_person()` |
| `backend/services/person_identifier.py` | `identify_person(tweet_text, twitter_handle=None)` — fast-path: if handle supplied, Gemini skipped, handle used directly as `name` + `handle` |
| `backend/tests/test_person_identifier.py` | +3 tests: handle skips Gemini; `@` prefix stripped; whitespace-only handle falls through |

#### Design system changes
| File | Change |
|------|--------|
| `frontend/app/globals.css` | IBM Plex Mono replaces JetBrains Mono; `--warn: #f5c518`; `.card-mode` hover (red fill + black text); `.tone-pill` toggle; `.warn-box` / `.error-box`; `prefers-reduced-motion` support |
| `frontend/app/layout.tsx` | IBM Plex Mono; 48px explicit nav height; 1px red bottom border |

#### Pages redesigned (neo-brutalist / "Bloomberg Terminal meets redacted government document")
| Page | Design highlights |
|------|-------------------|
| `app/page.tsx` | Giant Bebas Neue headline with red period; two cards with 1px red border → hover fills red + text inverts black; `v0.1 — kişisel kullanım` footer line |
| `app/opposition/page.tsx` | 40%/60% two-column; twitter handle text input below tweet textarea; tone pills (`.tone-pill` → red fill when active); `ANALİZ ET →` 48px red button; "// analiz bekleniyor" 30% opacity idle state; BASIN KİMLİĞİ press badge; contradiction cards with large red `≠`; reply cards with SOĞUK/KESKİN/THREAD Bebas headers; 800ms copy flash |
| `app/niche/page.tsx` | 4 niche selector buttons (red gap grid, selected = red fill + black text); 3 hour pills (1S/3S/6S); tweet table (score in accent red left, text center, YANITLA → right); row expands to 3-column reply grid |
| `app/login/page.tsx` | 4.5rem TWITBOOST Bebas top; rule-red; transparent 1px border inputs; red 48px submit; inline mono error (no box) |

#### Auth bypass (still active from previous sprint)
- `frontend/proxy.ts`: `return NextResponse.next()` at top
- `backend/middleware/auth_middleware.py`: dev user fallback
- **To restore:** remove bypass lines (clearly commented in both files)

### Test count
**119 / 119 passing** (+3 from twitter_handle fast-path tests)

### Blockers / Notes for Sprint 2.2

- **Auth bypass is active**: remove before production deploy
- **GEMINI_API_KEY**: set in `backend/.env` (done — do not commit)
- **Migration 001 must be applied** in Supabase SQL Editor
- **Supabase env vars needed**: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`; `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `frontend/.env.local`
- **CORS still `allow_origins=["*"]`**: restrict to Vercel domain before public deploy

---

## Previous Sprint

**Sprint 2.1 + Post-2.1 Cleanup (Issues #1 & #2)**
Full auth layer + tweet validation fix + Gemini migration. 116 tests passing.
- JWT verification via JWKS (ECC P-256); plan-based access control; daily limits
- `PersonNotFoundError` raised from service → HTTP 422 yellow warning in UI
- `google-genai==2.6.0` replaces `anthropic==0.52.0`; all test mocks updated

---

## Next Sprint

**Sprint 2.2 — Usage Limits UI**

Before coding:
1. Confirm migration `001_initial_auth.sql` is applied in Supabase
2. Confirm all env vars are set in backend `.env`
3. Confirm `GEMINI_API_KEY` is set

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
# Create .env from .env.example, fill ALL keys:
#   GEMINI_API_KEY=...          (https://aistudio.google.com/apikey)
#   BRAVE_SEARCH_API_KEY=...
#   SUPABASE_URL=...
#   SUPABASE_ANON_KEY=...
#   SUPABASE_SERVICE_ROLE_KEY=...
# Apply migrations/001_initial_auth.sql in Supabase SQL Editor
uvicorn main:app --reload

# Frontend (frontend/.env.local already exists with Supabase keys)
cd frontend
npm run dev

# Tests
cd backend
../.venv/Scripts/python.exe -m pytest tests/  # from project root
# OR from backend/: ../.venv/Scripts/pytest
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
