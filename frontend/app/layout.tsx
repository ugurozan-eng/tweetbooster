import type { Metadata } from "next";
import { Bebas_Neue, IBM_Plex_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

// ── Fonts ─────────────────────────────────────────────────────────────────

const bebas = Bebas_Neue({
  weight: "400",
  variable: "--font-bebas",
  subsets: ["latin"],
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
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
      className={`${bebas.variable} ${ibmPlexMono.variable} h-full`}
    >
      <body
        className="min-h-full flex flex-col"
        style={{ background: "var(--bg)", color: "var(--paper)" }}
      >
        {/* ── Nav ─────────────────────────────────────────────────────── */}
        <header
          style={{
            height: "48px",
            background: "var(--bg)",
            borderBottom: "1px solid var(--accent)",
            position: "sticky",
            top: 0,
            zIndex: 20,
            display: "flex",
            alignItems: "stretch",
          }}
        >
          {/* 2px red top line */}
          <div
            style={{
              position: "absolute",
              top: 0, left: 0, right: 0,
              height: "2px",
              background: "var(--accent)",
            }}
          />

          <div
            className="mx-auto max-w-6xl w-full px-4 flex items-center justify-between"
          >
            {/* Wordmark */}
            <Link
              href="/"
              className="font-display tracking-wide"
              style={{ color: "var(--paper)", fontSize: "1.5rem", lineHeight: 1 }}
            >
              TWITBOOST
            </Link>

            {/* Nav links */}
            <nav className="flex items-center">
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
              <Link
                href="/billing"
                className="font-code text-xs tracking-widest uppercase px-4 py-3 transition-colors text-muted hover:text-paper"
              >
                Hesabım
              </Link>
            </nav>
          </div>
        </header>

        {/* ── Page content ────────────────────────────────────────────── */}
        <main className="flex-1">{children}</main>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <footer
          style={{
            padding: "0.625rem 1rem",
            textAlign: "center",
            borderTop: "1px solid var(--border)",
            color: "var(--muted)",
            fontSize: "0.55rem",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            fontFamily: "var(--font-ibm-mono), monospace",
          }}
        >
          TwitBoost — Türk Twitter Kullanıcıları için AI Araştırma Aracı
        </footer>
      </body>
    </html>
  );
}
