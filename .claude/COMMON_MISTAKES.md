# COMMON_MISTAKES.md — Known Pitfalls for This Project

This file is updated as bugs and mistakes are discovered.
Claude Code: read this before implementing any feature.

---

## Legal / Safety

- NEVER generate output that insults or mocks the target person
- NEVER generate output that contains unverified accusations
- ALWAYS require a source URL for every claim in Opposition Mode output
- The legal safety filter must run AFTER generation, not before — catch it at output stage

## API Usage

- Brave Search rate limit is 1 req/sec on lower tiers — always add 1-second delay between parallel queries or use async with rate limiter
- Claude API: do NOT exceed 1500 output tokens per request — responses get cut off
- Always handle Brave Search returning 0 results gracefully (person not found in web)

## Turkish Language

- All user-facing strings must be in Turkish
- Do not use Google Translate — write natural Turkish or flag for human review
- Date formatting: Turkish format is DD.MM.YYYY not MM/DD/YYYY

## Architecture

- Usage limits are ALWAYS enforced in the FastAPI backend, never only in Next.js
- Never store raw tweet text or user input in logs — KVKK risk
- Research cache keys must be sanitized (Turkish characters in names can break cache keys)

## Frontend

- Do not use `<form>` tags — use onClick handlers
- All API calls go through `/api/` proxy in Next.js — never call Railway URL directly from browser
