/**
 * TwitBoost — Supabase Client
 * ============================
 * Singleton browser client. Import `supabase` everywhere you need Supabase Auth.
 *
 * After a successful sign-in, the session is stored in localStorage by default.
 * A presence cookie (`twitboost-authed=1`) is also set so that the server-side
 * proxy.ts can redirect unauthenticated users without reading localStorage.
 *
 * Never import the service role key here — only the public anon key.
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

// ---------------------------------------------------------------------------
// Env vars
// IMPORTANT: Must use dot notation (process.env.NEXT_PUBLIC_XXX), not bracket
// notation. Turbopack/Webpack inlines NEXT_PUBLIC_* values at compile time via
// static analysis — bracket notation (process.env[name]) is not replaced and
// results in undefined at runtime in the browser.
// ---------------------------------------------------------------------------

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

if (!SUPABASE_URL && typeof window !== "undefined") {
  console.warn("[supabase] NEXT_PUBLIC_SUPABASE_URL is not set. Auth will not work.");
}
if (!SUPABASE_ANON_KEY && typeof window !== "undefined") {
  console.warn("[supabase] NEXT_PUBLIC_SUPABASE_ANON_KEY is not set. Auth will not work.");
}

// ---------------------------------------------------------------------------
// Singleton — module-level, one instance per JS context
// ---------------------------------------------------------------------------

let _client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!_client) {
    _client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return _client;
}

/** Convenience shorthand — equivalent to `getSupabaseClient()`. */
export const supabase = (() => {
  // Lazy-initialised on first access; safe to import at module top-level
  // even when NEXT_PUBLIC_SUPABASE_* vars are not yet available (SSR).
  return new Proxy({} as SupabaseClient, {
    get(_target, prop) {
      return getSupabaseClient()[prop as keyof SupabaseClient];
    },
  });
})();

// ---------------------------------------------------------------------------
// Auth cookie helpers
// Used by login/logout to keep proxy.ts in sync with the localStorage session.
// The cookie is NOT HttpOnly — it is set client-side and holds no sensitive data.
// ---------------------------------------------------------------------------

const AUTH_COOKIE = "twitboost-authed";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7; // 7 days (matches Supabase default)

/** Set the presence cookie after a successful sign-in. */
export function setAuthCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=1; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

/** Clear the presence cookie on sign-out. */
export function clearAuthCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

// ---------------------------------------------------------------------------
// Token helper for API calls
// ---------------------------------------------------------------------------

/**
 * Get the current user's Bearer token, or null if not signed in.
 * Used by api.ts to attach Authorization header to every backend request.
 */
export async function getAccessToken(): Promise<string | null> {
  const {
    data: { session },
  } = await getSupabaseClient().auth.getSession();
  return session?.access_token ?? null;
}
