"use client";

/**
 * TwitBoost — Giriş Sayfası
 * Neo-brutalist login. Supabase email/password + Google OAuth.
 */

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSupabaseClient, setAuthCookie } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const supabase = getSupabaseClient();
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        if (
          authError.message.includes("Invalid login credentials") ||
          authError.message.includes("invalid_credentials")
        ) {
          setError("E-posta adresi veya şifre hatalı.");
        } else if (authError.message.includes("Email not confirmed")) {
          setError(
            "E-posta adresinizi doğrulamanız gerekiyor. Lütfen gelen kutunuzu kontrol edin."
          );
        } else {
          setError(`Giriş yapılamadı: ${authError.message}`);
        }
        return;
      }

      setAuthCookie();
      router.push("/");
    } catch {
      setError("Giriş sırasında beklenmedik bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setError(null);
    setLoading(true);
    try {
      const supabase = getSupabaseClient();
      const { error: authError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/auth/callback` },
      });
      if (authError) {
        setError(`Google ile giriş yapılamadı: ${authError.message}`);
      }
    } catch {
      setError("Google ile giriş sırasında beklenmedik bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-48px)] flex items-center justify-center px-4">
      <div className="w-full max-w-xs">

        {/* ── Brand ──────────────────────────────────────────────── */}
        <div className="text-center mb-8">
          <Link href="/">
            <span
              className="font-display leading-none block"
              style={{ fontSize: "4.5rem", color: "var(--paper)" }}
            >
              TWITBOOST
            </span>
          </Link>
          <div className="rule-red my-4" />
          <p className="eyebrow">Hesabınıza giriş yapın</p>
        </div>

        {/* ── Error (inline mono, no box) ─────────────────────────── */}
        {error && (
          <p
            className="font-code mb-5"
            style={{ color: "var(--accent)", fontSize: "0.75rem", lineHeight: 1.5 }}
          >
            {error}
          </p>
        )}

        {/* ── Form ───────────────────────────────────────────────── */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label htmlFor="email" className="eyebrow mb-2 block">
              E-POSTA
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ornek@mail.com"
              className="field"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="eyebrow mb-2 block">
              ŞİFRE
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="field"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? (
              <span className="cursor-blink">GİRİŞ YAPILIYOR</span>
            ) : (
              "GİRİŞ YAP →"
            )}
          </button>
        </form>

        {/* ── Divider ────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 my-6">
          <div className="flex-1" style={{ borderTop: "1px solid var(--border)" }} />
          <span className="eyebrow">VEYA</span>
          <div className="flex-1" style={{ borderTop: "1px solid var(--border)" }} />
        </div>

        {/* ── Google OAuth ───────────────────────────────────────── */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="btn-ghost w-full"
          style={{ justifyContent: "center", gap: "0.625rem", height: "44px" }}
        >
          <span
            className="font-display leading-none"
            style={{ fontSize: "1rem", color: "var(--paper)" }}
          >
            G
          </span>
          GOOGLE İLE GİRİŞ YAP
        </button>

      </div>
    </div>
  );
}
