# ROADMAP.md — TwitBoost Geliştirme Yol Haritası (Türkçe Kopya)

**Versiyon:** 1.0
**Tarih:** Mayıs 2026
**Tahmini toplam session:** 30+

---

## Faz Özeti

| Faz | Ad | Hedef | Tahmini Session |
|-----|----|-------|-----------------|
| 1 | MVP | Çalışan pipeline, kişisel kullanım | 8-10 |
| 2 | SaaS | Auth + ödeme + çok kullanıcı | 10-12 |
| 3 | Güçlü Özellikler | Twitter API + görsel üretimi | 8-10 |

---

## FAZ 1 — MVP (Mevcut)

**Hedef:** Tek kişi (sen) kullanabilsin. Auth yok. Ödeme yok. Sadece AI pipeline.

### Sprint 1.1 — Proje Kurulumu (Session 1-2)
- [ ] Next.js 15 projesi başlat (frontend)
- [ ] FastAPI projesi başlat (backend)
- [ ] Supabase projesi kur (şimdilik kullanılmasa da)
- [ ] Railway + Vercel deployment ayarla
- [ ] `.env` ve `.env.example` kur
- [ ] `.claudeignore` ve GSD kur
- [ ] Temel health check endpoint'leri

### Sprint 1.2 — Araştırma Ajansı (Session 3-4)
- [ ] Brave Search API entegrasyonu (Python servisi)
- [ ] Tweet metninden kişi tespiti (Claude)
- [ ] Paralel arama sorguları (4 eşzamanlı)
- [ ] URL'lerden içerik çıkarma
- [ ] Tarihli + kaynaklı beyanat listesi çıktısı

### Sprint 1.3 — Analiz + Üretim (Session 5-6)
- [ ] Tutarsızlık analizi prompt'u (Claude Sonnet)
- [ ] 3 ton seçeneğiyle yanıt üretimi
- [ ] Hukuki güvenlik filtresi (hakaret yok, kaynak zorunlu)
- [ ] Kaynak URL + tarih formatlama

### Sprint 1.4 — Niş Mod (Session 7)
- [ ] Trend tweet keşfi (Brave Search)
- [ ] 4 niş konfigürasyonu (yemek, futbol, ekonomi, siyaset)
- [ ] Niş yanıt üretimi prompt'u

### Sprint 1.5 — Frontend (Session 8-9)
- [ ] Tweet giriş arayüzü
- [ ] Mod seçici (Muhalif / Niş)
- [ ] Sonuç ekranı (yanıt varyantları + kaynaklar)
- [ ] Her varyant için kopyalama butonu
- [ ] Yükleme durumları

### Sprint 1.6 — Test + Düzeltme (Session 10)
- [ ] Her iki mod uçtan uca test
- [ ] Prompt kalite incelemesi (20 gerçek tweet testi)
- [ ] Hata yönetimi (Brave API çökmesi, Claude rate limit)
- [ ] Performans: pipeline 30 saniyenin altında

**Faz 1 Tamamlanma Kriterleri:**
- Her iki mod çalışıyor
- 20 test case'de çıktı kalitesi 4/5
- Pipeline < 30 saniyede tamamlanıyor
- Hatalı girişte çökmüyor

---

## FAZ 2 — SaaS

**Hedef:** Gerçek kullanıcılar, gerçek ödemeler, gerçek veriler.

### Sprint 2.1 — Auth (Session 11-12)
- [ ] Supabase Auth entegrasyonu
- [ ] E-posta/şifre + Google OAuth
- [ ] Korumalı rotalar (frontend + backend)
- [ ] Kullanıcı plan kaydı

### Sprint 2.2 — Kullanım Limitleri (Session 13-14)
- [ ] Günlük kullanım takibi (DB)
- [ ] Sunucu taraflı limit uygulaması
- [ ] Limit aşımı UI + yükseltme yönlendirmesi
- [ ] UI'da kullanım sayacı

### Sprint 2.3 — Ödeme (Session 15-16)
- [ ] LemonSqueezy entegrasyonu
- [ ] 3 plan kurulumu (Niş / Muhalif / Full)
- [ ] Webhook handler (plan aktivasyon/iptal)
- [ ] UI'da fatura sayfası

### Sprint 2.4 — UI Düzeltmeleri (Session 17-18)
- [ ] Tam responsive tasarım
- [ ] Türkçe dil desteği (tüm arayüz)
- [ ] Landing page
- [ ] Onboarding akışı
- [ ] Plan yükseltme akışı

### Sprint 2.5 — SaaS Lansman Hazırlığı (Session 19-20)
- [ ] KVKK uyumu (gizlilik politikası, veri işleme)
- [ ] Kullanım şartları
- [ ] Hata izleme (Sentry veya benzeri)
- [ ] Rate limiting (API kötüye kullanım koruması)
- [ ] Beta kullanıcı testi (5-10 kişi)

---

## FAZ 3 — Güçlü Özellikler

### Sprint 3.1 — Twitter API (Session 21-23)
- [ ] Twitter API v2 entegrasyonu
- [ ] Gerçek tweet çekme (web araması yerine)
- [ ] BYOK seçeneği (kullanıcı kendi API key'ini getirir)
- [ ] Kullanıcı başına Twitter kota takibi

### Sprint 3.2 — AI Görsel Üretimi (Session 24-26)
- [ ] Flux API entegrasyonu
- [ ] Tweet bağlamından görsel prompt üretimi
- [ ] Web görseli toplama (Faz 1 yükseltmesi)
- [ ] Çıktıda görsel gösterimi

### Sprint 3.3 — Analitik + Büyüme (Session 27-29)
- [ ] Kullanıcı analitik dashboard'u
- [ ] Yanıt performans takibi (manuel giriş)
- [ ] Ek niş seçenekleri (4'ten 10+'a)
- [ ] Kaydedilen yanıtlar kütüphanesi

---

## Önemli Kurallar

- **Faz 1'deyken Faz 2 işi yapma.** MVP'de auth iskelet kodu yok.
- **Prompt kalitesi üründür.** Gerekirse ekstra session harca.
- **Tüm arayüz Türkçe.** İstisna yok.
- **Hukuki filtre zorunludur.** MVP'de bile çıkarmadan ship etme.
