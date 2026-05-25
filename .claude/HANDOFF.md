# TwitBoost — Sprint Handoff

> Updated after each sprint. Load this at the start of a new session to resume quickly.

---

## Last Completed Sprint

**Sprint 1.4 — Niche Mode**
**Commit:** `5045d34`
**Date:** 2026-05-25

### What was built

| File | Purpose |
|------|---------|
| `backend/config/__init__.py` | Makes config/ a package |
| `backend/config/niches.py` | Single source of truth for 4 niches (food, football, economy, politics). `NicheConfig` TypedDict, `get_niche()`, `all_niches()`, `VALID_NICHE_IDS`. |
| `backend/prompts/niche_tweet_scorer.txt` | Claude prompt: scores tweet candidates 0–10 on 5 criteria, returns `{scored_tweets: [...]}` sorted desc |
| `backend/prompts/niche_reply_generator.txt` | Claude prompt: generates 3 replies ≤240 chars with hook_type (question/opinion/fact) |
| `backend/services/niche_agent.py` | `get_trending(niche_id, hours)` → scored list; `generate_reply(tweet_text, niche_id)` → filtered replies; `NicheReplyBlockedError` if all blocked |
| `backend/routers/niche.py` | `POST /api/niche/trending` + `POST /api/niche/reply`; Turkish 422 for invalid niche |
| `backend/main.py` | Niche router registered |
| `backend/tests/test_niche_agent.py` | 19 new tests |

### Test count
**84 / 84 passing** (was 65 at end of Sprint 1.3)

---

## Next Sprint

**Sprint 1.5 — Frontend MVP**

Build the Next.js UI that connects to the FastAPI backend already running on Railway (or locally). Phase 1 — no auth, no payments. Two pages:

1. **Opposition Mode page** (`/opposition`)
   - Text area: paste a tweet
   - Tone selector: cold / sharp / thread (checkboxes)
   - "Analiz Et" button → POST `/api/opposition/analyze`
   - Display: person name + contradiction list + 1–3 replies side-by-side
   - Source URLs shown as links

2. **Niche Mode page** (`/niche`)
   - Dropdown: select niche (populated from API or hardcoded from niches config)
   - "Trendleri Getir" button → POST `/api/niche/trending`
   - Tweet list with score badges
   - Click a tweet → text pre-fills reply box
   - "Yanıt Üret" button → POST `/api/niche/reply`
   - Show 3 replies with hook_type label

### Design constraints (from PRD)
- Tailwind CSS only — no external UI library
- Mobile-first, responsive
- Turkish language throughout
- No TypeScript `any` types
- API base URL from `NEXT_PUBLIC_API_URL` env var

### Skills to load
- `frontend-backend` — during API connection
- `frontend-design` — during component work

---

## Active Blockers / Notes

- **Brave free tier has no time-range filter.** `hours` param in `get_trending` is stored but not forwarded to Brave. When upgrading to a paid Brave plan, add `freshness=ph` query param.
- **Next.js version is 16.2.6** (latest as of May 2026), not "15" as written in PRD. PRD should be updated.
- **CORS is `allow_origins=["*"]`** — acceptable for Phase 1 local dev, must be restricted to Vercel domain in Phase 2.
- **No auth in Phase 1** — all endpoints are open. Do not add middleware or JWT tokens yet.
- **Legal filter word list** lives in `services/legal_safety_filter.py`. It will need expansion before public launch.
- **Twitter API not integrated** — all tweet discovery via Brave Search. Phase 3 task.

---

## Environment Setup Reminder

```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp ../.env.example ../.env    # fill in keys
.venv/Scripts/uvicorn main:app --reload

# Frontend
cd frontend
npm install
cp .env.local.example .env.local   # fill in NEXT_PUBLIC_API_URL
npm run dev

# Tests
cd backend
.venv/Scripts/pytest
```

---

## API Reference (quick)

| Method | Path | Body |
|--------|------|------|
| GET | `/health` | — |
| POST | `/api/research/identify` | `{tweet_text}` |
| POST | `/api/research/run` | `{name, topic}` |
| POST | `/api/opposition/analyze` | `{tweet_text, tones?}` |
| POST | `/api/niche/trending` | `{niche_id, hours?}` |
| POST | `/api/niche/reply` | `{tweet_text, niche_id}` |

Full contracts: `docs/API_CONTRACTS.md`
