# PRD — TwitBoost Product Requirements Document

**Version:** 1.0
**Date:** May 2026
**Status:** Active

---

## 1. Problem Statement

Turkish Twitter users who want to:
- Respond to politically biased accounts (trolls) effectively, with evidence
- Grow their follower count through high-engagement replies in their niche

...currently have no tool that automates research, finds source inconsistencies, and generates legally safe, viral-quality replies.

---

## 2. Product Vision

TwitBoost is an AI-powered Twitter reply assistant that:
- Researches a target account's history across the web
- Exposes inconsistencies between their past and present statements
- Generates ready-to-post replies optimized for engagement
- Helps niche content creators grow by replying strategically to trending tweets

---

## 3. Modes

### 3.1 Opposition Mode (Muhalif Mod)

**User flow:**
1. User pastes a tweet (text) into the app
2. App identifies the author via web search
3. App researches the author's past statements (news archives, old tweets via web, interviews)
4. Claude analyzes inconsistencies and contradictions
5. App generates a reply with: counter-argument text + source links + web images (if found)

**Output format:**
- Ready-to-copy tweet text (max 280 chars for single, up to thread for longer)
- Evidence package: list of source URLs with dates and quotes
- Tone options: Cold/Factual | Sharp/Witty | Thread format

**Legal safety rules (non-negotiable):**
- Output must only reference the subject's own publicly available statements
- No insults, accusations, or unverified claims
- Every claim must have a source URL
- Output includes automatic disclaimer: "These are [person]'s own statements"

### 3.2 Niche Mode

**User flow:**
1. User selects their niche
2. App fetches trending/recent tweets in that niche (via Brave Search, last 1 hour)
3. App presents top 10 tweets with engagement metrics
4. User selects a tweet
5. App generates the optimal reply for follower growth

**Phase 1 Niches (4 total):**

| Niche | Turkish Label | Why |
|-------|--------------|-----|
| Food & Recipes | Yemek & Tarif | Largest Turkish Twitter niche |
| Football | Futbol | Real-time, high volume |
| Economy & Finance | Ekonomi & Finans | Opinion-heavy, high engagement |
| Politics | Siyaset | Core use case overlap with Opposition Mode |

**Reply optimization criteria:**
- Add value (information, humor, or a strong opinion)
- Invite engagement (question at end, agree/disagree hook)
- Under 240 characters (leave room for RT context)
- Avoid sounding like AI

---

## 4. Pricing

| Plan | Price (TRY/month) | Daily Limit | Modes |
|------|--------------------|-------------|-------|
| Niche Only | 54.99 | 20 replies | Niche only |
| Opposition | 109.99 | 15 analyses | Opposition only |
| Full Access | 149.99 | 30 total | Both |
| Free Trial | 0 | 3 total | Both (limited) |

**Limits are enforced server-side.** Reset at midnight UTC+3.

---

## 5. User Personas

### Persona A — Muhalif Mehmet
- Age: 28-45
- Active opposition-leaning Twitter user
- Frustrated by trolls but lacks time to research
- Wants to go viral with a clever, evidence-based reply
- Not tech-savvy — needs one-click simplicity

### Persona B — Nişçi Neslihan
- Age: 22-35
- Food or lifestyle content creator
- Has 500-5000 followers, wants to grow
- Understands that replying to big accounts is the fastest growth hack
- Already active daily, just needs better content

---

## 6. Non-Features (Phase 1)

The following are explicitly NOT in scope for Phase 1:

- ❌ Twitter API integration (Phase 3)
- ❌ Direct posting to Twitter from the app
- ❌ AI-generated images (Phase 3)
- ❌ Multi-user accounts
- ❌ Analytics dashboard
- ❌ Browser extension
- ❌ Mobile app

---

## 7. Success Metrics

| Metric | Phase 1 Goal | Phase 2 Goal |
|--------|-------------|-------------|
| Personal usage sessions | 50/month | — |
| Paying users | — | 50 |
| Monthly revenue | — | 4,000 TRY |
| Reply quality rating (self-eval) | 4/5 | 4.2/5 |
| Avg. time to output | < 30 sec | < 20 sec |

---

## 8. Out of Scope — Legal Disclaimer

TwitBoost does not:
- Scrape data in violation of platform ToS (Phase 1 uses public web search only)
- Generate content that could constitute defamation under Turkish TCK 125-131
- Store personal data beyond what's needed for the session (KVKK compliance required in Phase 2)

---

## 9. Open Questions

- [ ] Final product name (TwitBoost is working name only)
- [ ] Twitter API BYOK (Bring Your Own Key) model for Phase 3?
- [ ] LemonSqueezy TRY support — needs verification before Phase 2
- [ ] KVKK data processing agreement template needed before SaaS launch
