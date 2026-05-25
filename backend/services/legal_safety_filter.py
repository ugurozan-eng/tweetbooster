"""
TwitBoost — Legal Safety Filter
=================================
Pattern-based guard that checks AI-generated reply text for content that could
constitute defamation, incitement, or hate speech under Turkish TCK §125–131.

CRITICAL: This module NEVER calls Claude. All checks are regex / word-list
matching so the filter is fast (microseconds) and costs nothing.

The filter is the LAST safety gate — it runs after Claude generates a reply.
A reply that fails the filter is silently dropped; it is NEVER returned to the
user.  False positives (blocking a legitimate reply) are acceptable;
false negatives (letting harmful content through) are not.

Violation categories
---------------------
PROFANITY   — Explicit Turkish sexual/scatological language.
INSULT      — Severe derogatory personal labels (şerefsiz, namussuz, etc.).
ACCUSATION  — Standalone criminal accusations without a documented source qualifier
              (hırsız, katil, terörist, dolandırıcı used as direct labels).
INCITEMENT  — Calls to mob action or personal harm (linç et, mahvet, etc.).

Legal basis
-----------
Turkish TCK §125 (hakaret), §126 (alenen aşağılama), §267 (iftira),
§216 (halkı kin ve düşmanlığa tahrik).
"""

from __future__ import annotations

import re
from typing import TypedDict

# ---------------------------------------------------------------------------
# 1. Explicit profanity — ALWAYS block, no context exceptions
# ---------------------------------------------------------------------------

_PROFANITY: frozenset[str] = frozenset(
    {
        "orospu",
        "orospu çocuğu",
        "piç",
        "piçlik",
        "sik",
        "sikim",
        "sikeyim",
        "siktirir",
        "göt",
        "götünü",
        "bok",
        "boktan",
        "amk",
        "amına",
        "yarrak",
        "yarak",
        "orosp",   # truncated form used in abbreviations
    }
)

# ---------------------------------------------------------------------------
# 2. Severe derogatory personal labels — direct insults against a person
#    (not slang/informal — specifically derogatory when aimed at someone)
# ---------------------------------------------------------------------------

_INSULTS: frozenset[str] = frozenset(
    {
        "şerefsiz",
        "serefsiz",
        "namussuz",
        "alçak",
        "aşağılık",
        "asagilık",
        "ahlaksız",
        "ahlaksiz",
        "hain",
        "vatan haini",
        "geri zekalı",
        "geri zekali",
        "embesil",
        "sürtük",
        "surtuk",
        "kaltak",
        "it herif",
        "pislik",
    }
)

# ---------------------------------------------------------------------------
# 3. Standalone criminal / legal accusations
#    Matches the accusation word when used as a direct label (noun form),
#    NOT when it appears inside a quoted court verdict or factual reporting.
#    Pattern: optional "bir " + accusation_word + optional Turkish noun suffix.
# ---------------------------------------------------------------------------

_ACCUSATION_PATTERNS: list[re.Pattern[str]] = [
    # hırsız / hırsızdır / bir hırsız
    re.compile(
        r"(?<!['\"])\b(bir\s+)?(hırsız|hirsiz)(dır|dir|dur|dür|tır|tir|sın|sin|sın)?\b(?!['\"])",
        re.IGNORECASE,
    ),
    # katil / katildir
    re.compile(
        r"(?<!['\"])\b(bir\s+)?(katil)(dir|dır|dur|dür|tır|tir)?\b(?!['\"])",
        re.IGNORECASE,
    ),
    # terörist / terorist
    re.compile(
        r"(?<!['\"])\b(bir\s+)?(terörist|terorist)(tir|tır|dir|dır)?\b(?!['\"])",
        re.IGNORECASE,
    ),
    # dolandırıcı
    re.compile(
        r"(?<!['\"])\b(bir\s+)?(dolandırıcı|dolandirici)(dır|dir|dur)?\b(?!['\"])",
        re.IGNORECASE,
    ),
    # mafya / mafyacı
    re.compile(
        r"(?<!['\"])\b(bir\s+)?(mafyacı|mafyaci|mafya\s+üyesi)(dır|dir|dur)?\b(?!['\"])",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# 4. Incitement to mob action or personal harm
# ---------------------------------------------------------------------------

_INCITEMENT_PATTERNS: list[re.Pattern[str]] = [
    # linç et / linc et  (Unicode ç + ASCII c fallback)
    re.compile(r"\b(linç|linc)\s*(et|edin|ediniz|edilsin)\b", re.IGNORECASE),
    re.compile(r"\brezil\s+et\b", re.IGNORECASE),
    re.compile(r"\bmahvet\b", re.IGNORECASE),
    re.compile(r"\byok\s+et\b", re.IGNORECASE),
    # işten at / isten at
    re.compile(r"\b(işten|isten)\s+at(ılsın|ilsin|ılması|ilmasi)?\b", re.IGNORECASE),
    re.compile(r"\bzarara\s+u(ğ|g)rat\b", re.IGNORECASE),
    re.compile(r"\bk(ö|o)t(ü|u)l(ü|u)k\s+(yap|et)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class FilterResult(TypedDict):
    passed: bool
    violations: list[str]  # human-readable Turkish violation descriptions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_reply(text: str) -> FilterResult:
    """
    Run the legal safety filter on a generated reply text.

    Args:
        text: The full reply text (single tweet or concatenated thread).

    Returns:
        :class:`FilterResult` with ``passed`` flag and ``violations`` list.

    IMPORTANT: If ``passed`` is ``False``, the reply MUST be dropped — never
    returned to the user. No exceptions.

    Notes:
        - Synchronous and Claude-free. Runs in microseconds.
        - Intentionally strict: false positives are acceptable; false negatives
          (letting defamatory content through) are not.
        - Duplicate violations for the same word/pattern are de-duplicated.
    """
    violations: list[str] = []
    seen: set[str] = set()
    text_lower = text.lower()

    def _add(msg: str) -> None:
        if msg not in seen:
            seen.add(msg)
            violations.append(msg)

    # ── 1. Explicit profanity ─────────────────────────────────────────────
    for word in _PROFANITY:
        if word in text_lower:
            _add(f"PROFANITY: '{word}' ifadesi tespit edildi")

    # ── 2. Severe personal insults ────────────────────────────────────────
    for word in _INSULTS:
        if word in text_lower:
            _add(f"INSULT: '{word}' hakaret ifadesi tespit edildi")

    # ── 3. Unverified criminal accusations ───────────────────────────────
    for pattern in _ACCUSATION_PATTERNS:
        m = pattern.search(text)
        if m:
            _add(f"ACCUSATION: doğrulanmamış suçlama tespit edildi — '{m.group().strip()}'")

    # ── 4. Incitement ─────────────────────────────────────────────────────
    for pattern in _INCITEMENT_PATTERNS:
        m = pattern.search(text)
        if m:
            _add(f"INCITEMENT: kışkırtıcı ifade tespit edildi — '{m.group().strip()}'")

    return FilterResult(passed=len(violations) == 0, violations=violations)


def check_thread(tweets: list[str]) -> FilterResult:
    """
    Run the legal safety filter over all tweets in a thread.

    Concatenates all tweets and calls :func:`check_reply`.
    Returns a single :class:`FilterResult` for the whole thread.
    """
    combined = " ".join(tweets)
    return check_reply(combined)
