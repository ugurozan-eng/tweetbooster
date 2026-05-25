"""
TwitBoost — Niche Configuration
=================================
Single source of truth for all Niche Mode configurations.

RULE: Never hardcode niche IDs, labels, or queries outside this file.
      All other modules must import from here and use ``get_niche()``.

Adding a new niche in the future:
  1. Add a ``NicheConfig`` entry to ``_NICHES``.
  2. No other file needs changing — the router and agent discover niches dynamically.
"""

from __future__ import annotations

from typing import TypedDict


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class NicheConfig(TypedDict):
    id: str                         # Machine identifier — used in API requests
    label_tr: str                   # Turkish display label shown to users
    search_queries: list[str]       # Brave Search query strings (Turkish)
    reply_goal: str                 # One sentence: what a good reply achieves here
    tone_instructions: str          # 2-3 sentences of niche-specific voice guidance


# ---------------------------------------------------------------------------
# Niche definitions — the single source of truth
# ---------------------------------------------------------------------------

_NICHES: dict[str, NicheConfig] = {
    "food": NicheConfig(
        id="food",
        label_tr="Yemek & Tarif",
        search_queries=[
            "yemek tarifi",
            "türk mutfağı",
            "ne pişirsem",
        ],
        reply_goal=(
            "Tarifte eksik bir ipucu paylaşmak, küçük bir kişisel dokunuş eklemek "
            "veya ilgili başka bir tarif önermek suretiyle sohbeti sürdürmek ve "
            "paylaşımcı bir topluluk duygusu yaratmak."
        ),
        tone_instructions=(
            "Samimi ve sıcak bir dil kullan; paylaşımcı bir ev aşçısı gibi yaz. "
            "Kısa, pratik bir ipucu veya kişisel bir deneyimle somut değer kat. "
            "Sonunda basit bir soru veya davet ekleyerek okuyucuyu yanıt vermeye teşvik et."
        ),
    ),

    "football": NicheConfig(
        id="football",
        label_tr="Futbol",
        search_queries=[
            "süper lig",
            "milli takım",
            "şampiyonlar ligi",
        ],
        reply_goal=(
            "Güçlü bir görüş bildirmek veya gözden kaçan bir istatistik paylaşmak "
            "suretiyle tartışmayı kışkırtmak, retweet almak ve futbolseverler arasında "
            "aktif bir diyalog başlatmak."
        ),
        tone_instructions=(
            "Tutku dolu ama bilgiye dayalı bir taraftar sesi kullan. "
            "İddiayı destekleyen somut bir veri, skor veya tarihsel karşılaştırma ekle. "
            "Kışkırtıcı ama hakaret içermeyen, tartışma yaratan bir cümleyle bitir."
        ),
    ),

    "economy": NicheConfig(
        id="economy",
        label_tr="Ekonomi & Finans",
        search_queries=[
            "dolar kur",
            "enflasyon",
            "borsa istanbul",
        ],
        reply_goal=(
            "Ekonomik bir veriyi ya da haberi güncel bağlamla yorumlamak ve "
            "okuyucuyu kendi pozisyonunu belirtmeye veya daha fazla soru sormaya "
            "teşvik etmek."
        ),
        tone_instructions=(
            "Analitik ve olgun bir ses kullan; somut rakam, yüzde veya karşılaştırma ekle. "
            "Siyasi taraf tutmaktan kaçın; gerçeklere ve verilere odaklan. "
            "Okuyucuyu düşündürecek açık uçlu bir soru veya gözlemle bitir."
        ),
    ),

    "politics": NicheConfig(
        id="politics",
        label_tr="Siyaset",
        search_queries=[
            "türkiye siyaset",
            "meclis",
            "muhalefet iktidar",
        ],
        reply_goal=(
            "Gündemdeki konuya farklı ya da gözden kaçan bir perspektiften bakış açısı "
            "sunarak tartışmayı derinleştirmek ve okuyucuyu kendi görüşünü paylaşmaya "
            "davet etmek."
        ),
        tone_instructions=(
            "Nötr ama eleştirel bir ses kullan; belgelenmiş bir gerçeği veya tarihsel "
            "benzerliği öne çıkar. "
            "Duygusal ya da partizan dil yerine argümana odaklan. "
            "Okuyucunun katılıp katılmayacağını sormak için bir kanca cümleyle bitir."
        ),
    ),
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

#: Frozen set of all valid niche IDs — use for validation in routers.
VALID_NICHE_IDS: frozenset[str] = frozenset(_NICHES.keys())


def get_niche(niche_id: str) -> NicheConfig:
    """
    Return the :class:`NicheConfig` for ``niche_id``.

    Args:
        niche_id: One of the valid niche identifiers (``food``, ``football``,
                  ``economy``, ``politics``).

    Raises:
        ValueError: ``niche_id`` is not recognised.
    """
    try:
        return _NICHES[niche_id]
    except KeyError:
        valid = ", ".join(sorted(VALID_NICHE_IDS))
        raise ValueError(
            f"Geçersiz niş kimliği: '{niche_id}'. "
            f"Geçerli değerler: {valid}"
        )


def all_niches() -> list[NicheConfig]:
    """Return all niche configs as an ordered list (insertion order)."""
    return list(_NICHES.values())
