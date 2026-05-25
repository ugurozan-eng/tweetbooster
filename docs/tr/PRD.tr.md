# PRD — TwitBoost Ürün Gereksinimleri Belgesi (Türkçe Kopya)

**Versiyon:** 1.0
**Tarih:** Mayıs 2026
**Durum:** Aktif

---

## 1. Problem Tanımı

Türk Twitter kullanıcıları şunları istiyor:
- Siyasi trollere kanıtlı, etkili yanıtlar vermek
- Kendi nişlerinde viral yanıtlarla takipçi kazanmak

...ama bunu otomatikleştiren, geçmiş beyanatları bulan ve hukuki açıdan güvenli yanıtlar üreten bir araç yok.

---

## 2. Ürün Vizyonu

TwitBoost; hedef kişinin web geçmişini araştıran, eski ve yeni beyanatları arasındaki tutarsızlıkları ortaya çıkaran ve paylaşıma hazır yanıtlar üreten bir AI Twitter asistanıdır.

---

## 3. Modlar

### 3.1 Muhalif Mod

**Kullanıcı akışı:**
1. Kullanıcı tweet metnini app'e yapıştırır
2. App tweet sahibini web aramasıyla tespit eder
3. App kişinin geçmiş beyanatlarını araştırır (haber arşivleri, eski tweet'ler, röportajlar)
4. Claude tutarsızlıkları ve çelişkileri analiz eder
5. App şunları içeren bir yanıt üretir: karşı argüman + kaynak linkleri + web görselleri

**Çıktı formatı:**
- Kopyalamaya hazır tweet metni (tek tweet veya thread)
- Kanıt paketi: kaynaklı, tarihli alıntılar listesi
- Ton seçeneği: Soğuk/Olgusal | Keskin/Nükteli | Thread formatı

**Hukuki güvenlik kuralları (değiştirilemez):**
- Çıktı yalnızca hedef kişinin kendi kamuya açık beyanatlarına dayanır
- Hakaret, iftira veya doğrulanmamış iddia içeremez
- Her iddia için kaynak URL zorunludur
- Çıktıya otomatik not eklenir: "Bunlar [kişinin] kendi beyanatlarıdır"

### 3.2 Niş Mod

**Kullanıcı akışı:**
1. Kullanıcı nişini seçer
2. App o nişte trend tweet'leri getirir (son 1 saat, Brave Search ile)
3. App top 10 tweet'i listeler
4. Kullanıcı bir tweet seçer
5. App takipçi büyümesi için optimize edilmiş yanıt üretir

**Faz 1 Nişleri (4 adet):**

| Niş | Neden |
|-----|-------|
| Yemek & Tarif | Türkiye'nin en büyük Twitter nişi |
| Futbol | Anlık, yüksek hacim |
| Ekonomi & Finans | Görüş ağırlıklı, yüksek etkileşim |
| Siyaset | Muhalif Mod ile örtüşen ana kullanım |

---

## 4. Fiyatlandırma

| Plan | Ücret (TRY/ay) | Günlük Limit | Modlar |
|------|----------------|--------------|--------|
| Niş Only | 54,99 | 20 yanıt | Sadece Niş |
| Muhalif | 109,99 | 15 analiz | Sadece Muhalif |
| Full Access | 149,99 | 30 toplam | Her ikisi |
| Ücretsiz Deneme | 0 | 3 toplam | Her ikisi (sınırlı) |

**Limitler sunucu tarafında uygulanır.** UTC+3 gece yarısı sıfırlanır.

---

## 5. Kullanıcı Personaları

### Persona A — Muhalif Mehmet
- 28-45 yaş, muhalif eğilimli aktif Twitter kullanıcısı
- Trollere yanıt vermek istiyor ama araştırmaya vakti yok
- Kanıtlı, zekice bir yanıtla viral olmak istiyor
- Teknik değil — tek tıkla çalışan basitlik şart

### Persona B — Nişçi Neslihan
- 22-35 yaş, yemek veya lifestyle içerik üreticisi
- 500-5000 takipçi var, büyümek istiyor
- Büyük hesaplara reply atmanın en hızlı büyüme taktiği olduğunu biliyor
- Zaten her gün aktif, sadece daha iyi içerik üretimine ihtiyaç var

---

## 6. Kapsam Dışı (Faz 1)

- ❌ Twitter API entegrasyonu (Faz 3)
- ❌ App üzerinden doğrudan Twitter'a post atma
- ❌ AI görsel üretimi (Faz 3)
- ❌ Çok kullanıcılı hesap
- ❌ Analitik dashboard
- ❌ Tarayıcı uzantısı
- ❌ Mobil uygulama

---

## 7. Başarı Kriterleri

| Metrik | Faz 1 Hedefi | Faz 2 Hedefi |
|--------|-------------|-------------|
| Kişisel kullanım session'ı | 50/ay | — |
| Ödeme yapan kullanıcı | — | 50 |
| Aylık gelir | — | 4.000 TRY |
| Yanıt kalitesi (öz değerlendirme) | 4/5 | 4,2/5 |
| Çıktı süresi | < 30 sn | < 20 sn |

---

## 8. Açık Sorular

- [ ] Ürünün nihai adı (TwitBoost geçici isim)
- [ ] LemonSqueezy TRY desteği — Faz 2 öncesi doğrulanmalı
- [ ] Faz 3'te Twitter API BYOK modeli mi, paylaşımlı havuz mu?
- [ ] KVKK veri işleme sözleşmesi şablonu — SaaS lansmanı öncesi hazır olmalı
