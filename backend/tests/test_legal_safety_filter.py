"""
Tests for services/legal_safety_filter.py

Coverage
--------
- Clean reply passes (no violations)
- Explicit profanity is blocked (PROFANITY category)
- Severe personal insult is blocked (INSULT category)
- Standalone criminal accusation is blocked (ACCUSATION category)
- Incitement to mob action is blocked (INCITEMENT category)
- Multiple violations are all reported
- check_thread: clean thread passes
- check_thread: dirty tweet inside thread blocks the whole thread
- De-duplication: same word appearing twice yields one violation message
- Edge cases: empty string, whitespace-only, disclaimer phrase passes
"""

from __future__ import annotations

import pytest

from services.legal_safety_filter import FilterResult, check_reply, check_thread


# ---------------------------------------------------------------------------
# Passing cases
# ---------------------------------------------------------------------------


def test_clean_reply_passes() -> None:
    """A factual, clean reply passes the filter."""
    result = check_reply(
        "2019'da X dedi, 2024'te Y dedi. Kaynaklar aşağıdadır."
    )
    assert result["passed"] is True
    assert result["violations"] == []


def test_disclaimer_phrase_passes() -> None:
    """The required disclaimer phrase does not trigger any filter."""
    result = check_reply("Bu kişinin kendi beyanatlarıdır.")
    assert result["passed"] is True


def test_empty_string_passes() -> None:
    """Empty string passes the filter (nothing to block)."""
    result = check_reply("")
    assert result["passed"] is True


def test_whitespace_only_passes() -> None:
    """Whitespace-only input passes."""
    result = check_reply("   \n\t  ")
    assert result["passed"] is True


def test_clean_thread_passes() -> None:
    """A thread with clean tweets passes."""
    result = check_thread(["1/ Konu başlığı.", "2/ Eski beyan.", "3/ Yeni beyan."])
    assert result["passed"] is True


# ---------------------------------------------------------------------------
# PROFANITY
# ---------------------------------------------------------------------------


def test_explicit_profanity_blocked() -> None:
    """Explicit Turkish profanity is blocked with PROFANITY violation."""
    result = check_reply("Bu adam tam bir orospu çocuğudur.")
    assert result["passed"] is False
    assert any("PROFANITY" in v for v in result["violations"])


def test_profanity_case_insensitive() -> None:
    """Profanity check is case-insensitive."""
    result = check_reply("OROSPU sözcüğü içeriyor.")
    assert result["passed"] is False
    assert any("PROFANITY" in v for v in result["violations"])


# ---------------------------------------------------------------------------
# INSULT
# ---------------------------------------------------------------------------


def test_severe_insult_blocked() -> None:
    """A severe personal insult is blocked with INSULT violation."""
    result = check_reply("Bu kişi şerefsizin teki.")
    assert result["passed"] is False
    assert any("INSULT" in v for v in result["violations"])


def test_insult_vatan_haini_blocked() -> None:
    """'vatan haini' (traitor) is blocked."""
    result = check_reply("Bu siyasetçi bir vatan hainidir.")
    assert result["passed"] is False
    assert any("INSULT" in v for v in result["violations"])


def test_insult_namussuz_blocked() -> None:
    """'namussuz' is blocked."""
    result = check_reply("Namussuz biri olarak tanınıyor.")
    assert result["passed"] is False
    assert any("INSULT" in v for v in result["violations"])


# ---------------------------------------------------------------------------
# ACCUSATION
# ---------------------------------------------------------------------------


def test_accusation_hirsiz_blocked() -> None:
    """Standalone 'hırsız' accusation is blocked."""
    result = check_reply("Bu adam bir hırsızdır.")
    assert result["passed"] is False
    assert any("ACCUSATION" in v for v in result["violations"])


def test_accusation_hirsiz_ascii_blocked() -> None:
    """ASCII variant 'hirsiz' is also blocked."""
    result = check_reply("Bu adam bir hirsizdir.")
    assert result["passed"] is False
    assert any("ACCUSATION" in v for v in result["violations"])


def test_accusation_katil_blocked() -> None:
    """Standalone 'katil' accusation is blocked."""
    result = check_reply("Bu kişi bir katildir.")
    assert result["passed"] is False
    assert any("ACCUSATION" in v for v in result["violations"])


def test_accusation_terorist_blocked() -> None:
    """Standalone 'terörist' accusation is blocked."""
    result = check_reply("Teröristtir bu adam.")
    assert result["passed"] is False
    assert any("ACCUSATION" in v for v in result["violations"])


def test_accusation_dolandirici_blocked() -> None:
    """'dolandırıcı' label is blocked."""
    result = check_reply("Bir dolandırıcıdır.")
    assert result["passed"] is False
    assert any("ACCUSATION" in v for v in result["violations"])


# ---------------------------------------------------------------------------
# INCITEMENT
# ---------------------------------------------------------------------------


def test_incitement_linc_unicode_blocked() -> None:
    """'linç edin' (Unicode ç) is blocked."""
    result = check_reply("Herkese duyuruyorum: bunu linç edin!")
    assert result["passed"] is False
    assert any("INCITEMENT" in v for v in result["violations"])


def test_incitement_linc_ascii_blocked() -> None:
    """'linc edin' (ASCII c fallback) is also blocked."""
    result = check_reply("Bunu linc et!")
    assert result["passed"] is False
    assert any("INCITEMENT" in v for v in result["violations"])


def test_incitement_mahvet_blocked() -> None:
    """'mahvet' is blocked."""
    result = check_reply("Onu mahvet.")
    assert result["passed"] is False
    assert any("INCITEMENT" in v for v in result["violations"])


# ---------------------------------------------------------------------------
# Multiple violations
# ---------------------------------------------------------------------------


def test_multiple_violations_all_reported() -> None:
    """When multiple categories trigger, all violations are listed."""
    result = check_reply("Bu orospu çocuğunu linç edin, hırsız herif!")
    assert result["passed"] is False
    categories = {v.split(":")[0] for v in result["violations"]}
    assert "PROFANITY" in categories
    assert "INCITEMENT" in categories
    assert "ACCUSATION" in categories


def test_violations_deduplication() -> None:
    """The same word appearing twice produces only one violation entry."""
    result = check_reply("şerefsiz mi şerefsiz, tam bir şerefsiz.")
    assert result["passed"] is False
    insult_violations = [v for v in result["violations"] if "INSULT" in v and "şerefsiz" in v]
    assert len(insult_violations) == 1


# ---------------------------------------------------------------------------
# check_thread
# ---------------------------------------------------------------------------


def test_thread_with_one_dirty_tweet_blocked() -> None:
    """A thread containing one dirty tweet blocks the entire thread."""
    result = check_thread(
        [
            "1/ Konu başlığı temiz.",
            "2/ Eski beyan temiz.",
            "3/ Bu orospu çocuğunu linç edin!",  # dirty
        ]
    )
    assert result["passed"] is False
    assert any("PROFANITY" in v for v in result["violations"])


def test_thread_all_clean_passes() -> None:
    """A fully clean thread passes."""
    result = check_thread(
        [
            "1/ Önemli bir çelişki tespit edildi.",
            "2/ 2019'da şunu söyledi.",
            "3/ 2024'te ise bunu söyledi.",
            "4/ Bu kişinin kendi beyanatlarıdır.",
        ]
    )
    assert result["passed"] is True
