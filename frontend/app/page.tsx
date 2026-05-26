import Link from "next/link";

export default function Home() {
  return (
    <div
      className="min-h-[calc(100vh-5rem)] flex flex-col justify-center px-4 py-16 max-w-6xl mx-auto"
    >
      <div className="stagger-in">

        {/* ── Eyebrow ──────────────────────────────────────────────── */}
        <p className="eyebrow mb-4">
          AI destekli siyasi analiz aracı · Türk Twitter kullanıcıları için
        </p>

        {/* ── Hero headline ────────────────────────────────────────── */}
        <h1
          className="font-display leading-none mb-1"
          style={{ fontSize: "clamp(4rem, 12vw, 9rem)", color: "var(--paper)" }}
        >
          TROLLERE KARŞI
        </h1>
        <h1
          className="font-display leading-none mb-8"
          style={{ fontSize: "clamp(4rem, 12vw, 9rem)", color: "var(--accent)" }}
        >
          SİLAHIN.
        </h1>

        {/* ── Red rule ─────────────────────────────────────────────── */}
        <div className="rule-red mb-10" />

        {/* ── Mode cards — newspaper column style ──────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-px" style={{ borderColor: "var(--border)" }}>

          {/* Muhalif Mod */}
          <Link
            href="/opposition"
            className="group block p-6 transition-colors"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <p className="eyebrow mb-3">MOD 01</p>
            <h2
              className="font-display leading-none mb-3"
              style={{ fontSize: "clamp(2.5rem, 6vw, 4rem)", color: "var(--paper)" }}
            >
              MUHALİF MOD
            </h2>
            <div className="rule-red mb-4" style={{ borderColor: "var(--border)" }} />
            <p className="font-code" style={{ color: "var(--muted)", fontSize: "0.78rem", lineHeight: 1.7 }}>
              Bir politikacının ya da kamuoyunun önündeki ismin tweetini yapıştırın.
              Araç geçmiş beyanlarını araştırır, çelişkileri tespit eder ve
              hukuki açıdan güvenli yanıtlar üretir.
            </p>
            <p
              className="font-display mt-5 transition-colors"
              style={{ color: "var(--border)", fontSize: "1.1rem", letterSpacing: "0.06em" }}
            >
              ARAŞTIRMAYA BAŞLA →
            </p>
          </Link>

          {/* Niş Mod */}
          <Link
            href="/niche"
            className="group block p-6 transition-colors"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <p className="eyebrow mb-3">MOD 02</p>
            <h2
              className="font-display leading-none mb-3"
              style={{ fontSize: "clamp(2.5rem, 6vw, 4rem)", color: "var(--paper)" }}
            >
              NİŞ MOD
            </h2>
            <div className="rule-red mb-4" style={{ borderColor: "var(--border)" }} />
            <p className="font-code" style={{ color: "var(--muted)", fontSize: "0.78rem", lineHeight: 1.7 }}>
              İlgilendiğiniz nişi seçin — yemek, futbol, ekonomi veya siyaset.
              Trend tweetleri getirin, etkileşim potansiyelini görün ve
              organik büyüme için yanıtlar üretin.
            </p>
            <p
              className="font-display mt-5 transition-colors"
              style={{ color: "var(--border)", fontSize: "1.1rem", letterSpacing: "0.06em" }}
            >
              NİŞ SEÇ →
            </p>
          </Link>

        </div>

        {/* ── Bottom rule + tagline ─────────────────────────────────── */}
        <div className="rule-red mt-10 mb-4" />
        <p className="eyebrow text-right">
          Hukuki güvenlik filtresi dahil · Sonuçlar Türkçe üretilir
        </p>

      </div>
    </div>
  );
}
