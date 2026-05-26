import type { Metadata } from "next";
import { Bebas_Neue, JetBrains_Mono, Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

// ── Fonts ─────────────────────────────────────────────────────────────────

const bebas = Bebas_Neue({
  weight: "400",
  variable: "--font-bebas",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

// Keep Geist as fallback (used by --font-geist-sans legacy token)
const geist = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

// ── Metadata ───────────────────────────────────────────────────────────────

export const metadata: Metadata = {
  title: "TwitBoost — Siyasi Analiz Aracı",
  description: "Trollere karşı silahın. AI destekli Twitter yanıt ve araştırma aracı.",
};

// ── Layout ─────────────────────────────────────────────────────────────────

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="tr"
      className={`${bebas.variable} ${jetbrains.variable} ${geist.variable} h-full`}
    >
      <body
        className="min-h-full flex flex-col"
        style={{ background: "var(--bg)", color: "var(--paper)" }}
      >
        {/* ── Nav ─────────────────────────────────────────────────────── */}
        <header
          className="sticky top-0 z-20"
          style={{
            background: "var(--bg)",
            borderBottom: "1px solid var(--border)",
            borderBottomColor: "var(--accent)",
            borderBottomWidth: "1px",
          }}
        >
          {/* thin red line at very top */}
          <div style={{ height: "2px", background: "var(--accent)" }} />

          <div className="mx-auto max-w-6xl flex items-center justify-between px-4 py-2">
            {/* Wordmark */}
            <Link
              href="/"
              className="font-display text-2xl tracking-wide"
              style={{ color: "var(--paper)", lineHeight: 1 }}
            >
              TWITBOOST
            </Link>

            {/* Nav links */}
            <nav className="flex items-center gap-0">
              <Link
                href="/opposition"
                className="font-code text-xs tracking-widest uppercase px-4 py-3 transition-colors text-muted hover:text-paper"
              >
                Muhalif
              </Link>
              <Link
                href="/niche"
                className="font-code text-xs tracking-widest uppercase px-4 py-3 transition-colors text-muted hover:text-paper"
              >
                Niş
              </Link>
            </nav>
          </div>
        </header>

        {/* ── Page content ────────────────────────────────────────────── */}
        <main className="flex-1">{children}</main>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <footer
          className="py-3 px-4 text-center"
          style={{
            borderTop: "1px solid var(--border)",
            color: "var(--muted)",
            fontSize: "0.6rem",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            fontFamily: "var(--font-jetbrains), monospace",
          }}
        >
          TwitBoost — Türk Twitter Kullanıcıları için AI Araştırma Aracı
        </footer>
      </body>
    </html>
  );
}
