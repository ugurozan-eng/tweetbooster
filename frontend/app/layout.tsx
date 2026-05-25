import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TwitBoost — AI Destekli Twitter Yanıt Aracı",
  description:
    "Muhalif mod ve niş mod ile Twitter'da etkili yanıtlar üretin.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-950 text-zinc-100">
        {/* ── Nav ───────────────────────────────────────────────────────── */}
        <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
          <div className="mx-auto max-w-5xl flex items-center justify-between px-4 py-3">
            {/* Logo */}
            <Link
              href="/"
              className="text-lg font-bold text-white tracking-tight hover:text-blue-400 transition-colors"
            >
              TwitBoost
            </Link>

            {/* Nav links */}
            <nav className="flex items-center gap-1">
              <Link
                href="/opposition"
                className="px-3 py-1.5 rounded-md text-sm font-medium text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
              >
                Muhalif Mod
              </Link>
              <Link
                href="/niche"
                className="px-3 py-1.5 rounded-md text-sm font-medium text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
              >
                Niş Mod
              </Link>
            </nav>
          </div>
        </header>

        {/* ── Page content ──────────────────────────────────────────────── */}
        <main className="flex-1">{children}</main>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <footer className="border-t border-zinc-800 py-4 text-center text-xs text-zinc-600">
          TwitBoost — Faz 1 MVP
        </footer>
      </body>
    </html>
  );
}
