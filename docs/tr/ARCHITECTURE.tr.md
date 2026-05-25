# ARCHITECTURE.md — TwitBoost Teknik Mimari (Türkçe Kopya)

**Versiyon:** 1.0
**Tarih:** Mayıs 2026

---

## 1. Genel Mimari

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (Vercel)                      │
│           Next.js 15 + TypeScript + Tailwind            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / REST
┌────────────────────────▼────────────────────────────────┐
│                  BACKEND (Railway)                      │
│                   FastAPI (Python)                      │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Araştırma  │  │   Analiz     │  │    Üretim     │  │
│  │   Ajansı    │  │   Ajansı     │  │    Ajansı     │  │
│  │(Brave API)  │  │(Claude API)  │  │(Claude API)   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────┬──────────────────────┬─────────────────────┘
             │                      │
┌────────────▼──────┐   ┌──────────▼────────────────────┐
│  Supabase         │   │  Harici API'ler               │
│  - PostgreSQL     │   │  - Brave Search API           │
│  - Auth           │   │  - Claude API (Anthropic)     │
│  - Storage        │   │  - LemonSqueezy (Faz 2)       │
└───────────────────┘   │  - Twitter API v2 (Faz 3)    │
                        └──────────────────────────────┘
```

---

## 2. Muhalif Mod Pipeline'ı

```
GİRDİ: Kullanıcının yapıştırdığı tweet metni
         │
         ▼
[Adım 1] KİŞİ TESPİTİ
  - Tweet metninden isim/kullanıcı adı çıkar (Claude)
  - Brave Search: isim + haber siteleri araması
  - Çıktı: kişi profili (isim, görev, parti/kurum)
         │
         ▼
[Adım 2] PARALEL ARAŞTIRMA (Brave Search — 4 eşzamanlı sorgu)
  Sorgu A: "{isim} eski açıklama beyanat"
  Sorgu B: "{isim} twitter geçmiş"
  Sorgu C: "{isim} çelişki tutarsızlık"
  Sorgu D: "{isim} {güncel tweet konusu}"
  - Çıktı: tarihli URL + snippet listesi
         │
         ▼
[Adım 3] İÇERİK ÇIKARMA
  - En alakalı 5 URL'den tam metin çek
  - Filtrele: sadece tarih içeren içerik
  - Çıktı: tarihli + kaynaklı beyanat listesi
         │
         ▼
[Adım 4] TUTARSIZLIK ANALİZİ (Claude Sonnet)
  - Sistem prompt: hukuki güvenlik kuralları, sadece olgusal mod
  - Girdi: güncel tweet + geçmiş beyanatlar
  - Çıktı: güven skoru ile çelişki haritası
         │
         ▼
[Adım 5] YANIT ÜRETİMİ (Claude Sonnet)
  - Girdi: çelişki haritası + ton seçimi
  - Çıktı: 3 yanıt varyantı (Soğuk / Keskin / Thread)
  - Her varyant: tweet metni + kanıt notları + kaynak URL'leri
         │
         ▼
ÇIKTI: Yanıt paketi (metin + kaynaklar + web görselleri)
```

---

## 3. Token Maliyeti (Tahmini)

| Adım | Tahmini Token | Maliyet (USD) |
|------|--------------|---------------|
| Kişi tespiti | ~500 | ~$0,001 |
| Tutarsızlık analizi | ~2000 | ~$0,004 |
| Yanıt üretimi | ~1500 | ~$0,003 |
| **Toplam (1 run)** | **~4000** | **~$0,008** |

Günlük 100 istek: ~$0,80/gün → ~$24/ay

---

## 4. Tahmini Aylık Gider

| Servis | Plan | Ücret |
|--------|------|-------|
| Claude API | ~500K token/ay | ~$8 |
| Brave Search API | ~2K sorgu/ay | $5 |
| Supabase | Free | $0 |
| Vercel | Free | $0 |
| Railway | Starter | $5 |
| **TOPLAM (MVP)** | | **~$18/ay** |
| **Twitter API (Faz 3)** | Basic | +$100/ay |

---

## 5. Ortam Değişkenleri

```bash
# AI
ANTHROPIC_API_KEY=

# Arama
BRAVE_SEARCH_API_KEY=

# Supabase (Faz 2)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Ödeme (Faz 2)
LEMONSQUEEZY_API_KEY=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_WEBHOOK_SECRET=

# Twitter (Faz 3)
TWITTER_BEARER_TOKEN=
```

---

## 6. Deployment

- **Frontend:** Vercel — git push ile otomatik deploy
- **Backend:** Railway — nixpacks builder, `uvicorn main:app`
- **Veritabanı:** Supabase — managed PostgreSQL
