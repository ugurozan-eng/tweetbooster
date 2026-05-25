"use client";

/**
 * TwitBoost — Giriş Sayfası
 * Email/password sign-in via Supabase Auth.
 * Successful login → set auth cookie → redirect to /
 */

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSupabaseClient, setAuthCookie } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        // Map common Supabase error messages to Turkish
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

      // Session stored in localStorage by Supabase; set presence cookie for proxy.ts
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
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (authError) {
        setError(`Google ile giriş yapılamadı: ${authError.message}`);
      }
      // On success Supabase redirects the browser — no manual navigation needed.
    } catch {
      setError("Google ile giriş sırasında beklenmedik bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <Link href="/" className="text-2xl font-bold text-zinc-100 hover:text-white">
            TwitBoost
          </Link>
          <p className="mt-2 text-zinc-400 text-sm">Hesabınıza giriş yapın</p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-4 rounded-lg bg-red-900/40 border border-red-700/50 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Email/password form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-1">
              E-posta
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ornek@mail.com"
              className="
                w-full rounded-lg border border-zinc-700 bg-zinc-900
                px-3 py-2 text-zinc-100 placeholder-zinc-600
                focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500
              "
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-1">
              Şifre
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="
                w-full rounded-lg border border-zinc-700 bg-zinc-900
                px-3 py-2 text-zinc-100 placeholder-zinc-600
                focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500
              "
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="
              w-full rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50
              px-4 py-2.5 text-sm font-semibold text-white
              transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500
            "
          >
            {loading ? "Giriş yapılıyor…" : "Giriş Yap"}
          </button>
        </form>

        {/* Divider */}
        <div className="my-5 flex items-center gap-3">
          <div className="flex-1 border-t border-zinc-700" />
          <span className="text-xs text-zinc-500">veya</span>
          <div className="flex-1 border-t border-zinc-700" />
        </div>

        {/* Google OAuth */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="
            w-full flex items-center justify-center gap-2
            rounded-lg border border-zinc-700 bg-zinc-900 hover:bg-zinc-800
            px-4 py-2.5 text-sm font-medium text-zinc-200
            transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-500
            disabled:opacity-50
          "
        >
          {/* Simple Google "G" icon */}
          <span className="font-bold text-base leading-none">G</span>
          Google ile Giriş Yap
        </button>
      </div>
    </main>
  );
}
