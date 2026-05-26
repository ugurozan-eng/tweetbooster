import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-48px)] flex flex-col justify-center px-4 py-16 max-w-6xl mx-auto">
      <div className="stagger-in">

        {/* ── Eyebrow ──────────────────────────────────────────────── */}
        <p className="eyebrow mb-6">
          AI destekli siyasi analiz · Türk Twitter kullanıcıları için
        </p>

        {/* ── Hero headline ────────────────────────────────────────── */}
        <h1
          className="font-display leading-none mb-10"
          style={{ fontSize: "clamp(4rem, 14vw, 10rem)", color: "var(--paper)" }}
        >
          TROLLERE KARŞI SİLAHIN
          <span style={{ color: "var(--accent)" }}>.</span>
        </h1>

        {/* ── Mode cards — newspaper columns ───────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-px" style={{ background: "var(--accent)" }}>

          {/* Muhalif Mod */}
          <Link href="/opposition" className="card-mode p-8">
            <p className="eyebrow mb-4">MOD 01</p>
            <h2
              className="font-display leading-none mb-4"
              style={{ fontSize: "clamp(2.5rem, 6vw, 4.5rem)" }}
            >
              MUHALİF MOD
            </h2>
            <p
              className="font-code mb-6"
              style={{ fontSize: "0.78rem", lineHeight: 1.7, color: "inherit", opacity: 0.7 }}
            >
              Bir politikacının tweetini yapıştırın. Araç geçmiş beyanlarını
              araştırır, çelişkileri tespit eder ve hukuki açıdan güvenli
              yanıtlar üretir.
            </p>
            <p
              className="font-code"
              style={{ fontSize: "0.75rem", letterSpacing: "0.12em" }}
            >
              ARAŞTIRMAYA BAŞLA →
            </p>
          </Link>

          {/* Niş Mod */}
          <Link href="/niche" className="card-mode p-8">
            <p className="eyebrow mb-4">MOD 02</p>
            <h2
              className="font-display leading-none mb-4"
              style={{ fontSize: "clamp(2.5rem, 6vw, 4.5rem)" }}
            >
              NİŞ MOD
            </h2>
            <p
              className="font-code mb-6"
              style={{ fontSize: "0.78rem", lineHeight: 1.7, color: "inherit", opacity: 0.7 }}
            >
              Nişinizi seçin — yemek, futbol, ekonomi veya siyaset. Trend
              tweetleri getirin, etkileşim potansiyelini görün ve organik
              büyüme için yanıtlar üretin.
            </p>
            <p
              className="font-code"
              style={{ fontSize: "0.75rem", letterSpacing: "0.12em" }}
            >
              NİŞ SEÇ →
            </p>
          </Link>

        </div>

        {/* ── Version line ─────────────────────────────────────────── */}
        <p
          className="font-code mt-8 text-right"
          style={{ fontSize: "0.6rem", color: "var(--dim)", letterSpacing: "0.1em" }}
        >
          v0.1 — kişisel kullanım
        </p>

      </div>
    </div>
  );
}
