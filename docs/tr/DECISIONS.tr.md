# DECISIONS.md — Mimari Karar Günlüğü (Türkçe Kopya)

Her önemli teknik ve ürün kararı burada kayıt altına alınır.

---

## D-001: Tavily yerine Brave Search API

**Karar:** Brave Search API birincil web arama sağlayıcısı
**Alternatifler:** Tavily, Exa, Perplexity Sonar, Firecrawl
**Tarih:** Mayıs 2026

**Gerekçe:**
- Brave kendi bağımsız indeksini işletiyor (30B+ sayfa) — Google/Bing'e bağımlı değil
- Bing Search API Ağustos 2025'te kapandı — bağımsız indeks artık kritik
- Bağımsız benchmark'ta top tier (Firecrawl ve Exa ile aynı seviye)
- Tavily Şubat 2026'da Nebius tarafından satın alındı — fiyat riski
- 1K sorgu = $5, rekabetçi fiyat
- Google scraping davası riski yok (SerpAPI davası Aralık 2025'te açıldı)

---

## D-002: Tek AI modeli olarak Claude Sonnet

**Karar:** Tüm AI görevleri için claude-sonnet-4-20250514
**Alternatifler:** GPT-4o, Gemini 3.5 Flash, karışık model kullanımı
**Tarih:** Mayıs 2026

**Gerekçe:**
- Uzun context analizinde rakiplerden üstün (tutarsızlık tespiti çok kaynak gerektiriyor)
- Türkçe dil kalitesi rakiplerden yüksek
- Zaten Claude ekosistemine hakimiz
- Sonnet, bu kullanım için Opus'tan daha iyi fiyat/performans oranı sunuyor
- Stack'i basit tutmak öncelik

---

## D-003: Twitter API'nin Faz 3'e ertelenmesi

**Karar:** Faz 1 ve 2'de tweet keşfi için Brave Search kullanılır
**Alternatifler:** Twitter API v2 ile hemen başlamak
**Tarih:** Mayıs 2026

**Gerekçe:**
- Twitter API Basic: $100/ay, sadece 10K tweet okuma/ay
- Tek kullanıcı (Faz 1) için israf
- SaaS (Faz 2) için BYOK olmadan bu limit patlar
- Brave Search web indeksi üzerinden son tweet'leri bulabiliyor — MVP için yeterli
- Faz 3'te BYOK modeli: kullanıcılar kendi API key'lerini getirir

---

## D-004: Backend için FastAPI

**Karar:** Backend olarak FastAPI (Python)
**Alternatifler:** Node.js + Express, Next.js API routes
**Tarih:** Mayıs 2026

**Gerekçe:**
- Geliştirici tercihi ve mevcut uzmanlık
- Python ekosistemi AI/LLM entegrasyonları için daha iyi (Anthropic SDK, async HTTP)
- Paralel Brave Search sorguları için async desteği mükemmel
- Next.js API routes frontend ve backend'i bağlar — ilerisi için kötü

---

## D-005: Doğrudan Twitter post atma yok

**Karar:** App sadece kopyala-yapıştır metin üretir; kullanıcı manuel post atar
**Alternatifler:** Twitter OAuth + app üzerinden post
**Tarih:** Mayıs 2026

**Gerekçe:**
- Hukuki risk azaltma: kullanıcı inceleyip manuel atarsa app araç konumunda kalır
- Twitter otomasyon kuralları katı — otomatik reply bot'lar hesap askıya alınmasına yol açabilir
- Daha basit MVP kapsamı
- Kullanıcılar zaten post atmadan önce incelemek istiyor

---

## D-006: Ödeme için LemonSqueezy

**Karar:** Abonelik yönetimi için LemonSqueezy
**Alternatifler:** Stripe, iyzico, Paddle
**Tarih:** Mayıs 2026

**Gerekçe:**
- Geliştirici tercihi (diğer projelerde zaten kullanılıyor)
- TRY (Türk Lirası) desteği
- Merchant of Record modeli — KDV/vergi LemonSqueezy üstleniyor
- SaaS abonelikleri için Stripe'tan daha basit entegrasyon
- **DİKKAT:** Faz 2 başlamadan TRY desteği doğrulanmalı

---

## D-007: Supabase (veritabanı + auth)

**Karar:** Tüm veri depolama ve kimlik doğrulama için Supabase
**Alternatifler:** PlanetScale, Railway PostgreSQL, Firebase
**Tarih:** Mayıs 2026

**Gerekçe:**
- Geliştirici tercihi ve mevcut uzmanlık
- Auth + PostgreSQL + Storage tek serviste
- Erken aşama için ücretsiz tier yeterli
- Row Level Security ile multi-tenant veri izolasyonu
- Diğer projelerde zaten kullanılıyor

---

## AÇIK KARARLAR

- [ ] **D-008:** Ürün adı (TwitBoost geçici)
- [ ] **D-009:** Faz 3 görsel üretim sağlayıcısı (Flux mu, DALL-E 3 mü?)
- [ ] **D-010:** Faz 3'te BYOK mu, paylaşımlı Twitter API havuzu mu?
- [ ] **D-011:** LemonSqueezy TRY desteği — Faz 2 öncesi doğrula
