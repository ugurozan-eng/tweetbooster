# TwitBoost — Sprint Handoff

> Updated after each sprint. Load this at the start of a new session to resume quickly.

---

## Last Completed Sprint

**Sprint 1.5 — Frontend MVP**
**Commit:** `fc683c3`
**Date:** 2026-05-25

### What was built

| File | Purpose |
|------|---------|
| `frontend/lib/api.ts` | Single API client: `identifyPerson`, `runOppositionAnalysis`, `getNicheTrending`, `generateNicheReply`. Full TypeScript types. `ApiError` class with status code. Turkish error messages. |
| `frontend/app/layout.tsx` | Root layout: `lang="tr"`, dark `zinc-950` bg, sticky nav with TwitBoost logo + Muhalif/Niş links. |
| `frontend/app/page.tsx` | Landing page: product name + two mode cards linking to `/opposition` and `/niche`. |
| `frontend/app/opposition/page.tsx` | Full Opposition Mode UI: tweet input, 3 tone checkboxes, loading state, person card, contradictions list, reply cards with copy-to-clipboard, error banner. |
| `frontend/app/niche/page.tsx` | Full Niche Mode UI: 2×2 niche selector, hours dropdown, tweet list with score badges, per-tweet inline reply generation with hook_type badges and copy buttons. |
| `frontend/env.local.example` | `NEXT_PUBLIC_API_URL=http://localhost:8000` (renamed without leading dot to avoid `.gitignore`). |

### Build & Type check
- `tsc --noEmit` → **0 errors**
- `next build` → **6/6 pages OK**, Turbopack, zero errors
- Backend tests: **84 / 84 passing** (unchanged from Sprint 1.4)

---

## Next Sprint

**Sprint 1.6 — Connect & Polish**

The UI and backend are complete independently. Next tasks:

1. **End-to-end manual test** with a real backend running locally:
   - Start backend (`uvicorn main:app --reload`)
   - Start frontend (`npm run dev`)
   - Paste a real Turkish tweet into opposition mode
   - Fetch trending in niche mode and generate a reply
   - Fix any integration issues found

2. **Error handling polish** (if needed after E2E test):
   - Network timeout handling (add `signal: AbortSignal.timeout(30000)` to fetch)
   - Better loading text for long-running opposition analysis (~20–30s expected)

3. **`NEXT_PUBLIC_API_URL` documentation** — update `README.md` with frontend setup instructions

4. **Optional Sprint 1.6 extras:**
   - Persist selected niche in `localStorage` so it survives page refresh
   - Show tweet character count in opposition textarea
   - `next.config.ts`: add `output: 'standalone'` for Railway deploy

---

## Active Blockers / Notes

- **`.env.local.example` renamed to `env.local.example`** (no leading dot) because the frontend `.gitignore` has `.env*` which would block it. Remember to rename to `.env.local` when setting up locally.
- **Copy-to-clipboard uses `navigator.clipboard` + `execCommand` fallback.** Both require user gesture (button click) — this is correctly implemented.
- **Opposition analysis can take 20–30 seconds** (Brave Search + multiple Claude calls). The UI shows "Araştırılıyor…" spinner during loading. No timeout is set yet — add in Sprint 1.6 if needed.
- **Niche page resets all reply states on each new "Tweet'leri Getir"** click — this is intentional to avoid stale data.
- **Brave free tier has no time-range filter.** `hours` param is sent to backend but not forwarded to Brave.
- **CORS is `allow_origins=["*"]`** — acceptable for Phase 1 local dev.
- **No auth in Phase 1** — all endpoints are open.
- **Twitter API not integrated** — all tweet discovery via Brave Search.

---

## Environment Setup Reminder

```bash
# Backend
cd backend
.venv/Scripts/activate        # Windows (venv already created)
uvicorn main:app --reload

# Frontend
cd frontend
cp env.local.example .env.local   # fill in NEXT_PUBLIC_API_URL
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
