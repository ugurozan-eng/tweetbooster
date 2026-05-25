"use client";

/**
 * Auth-aware header section.
 * Shows email + logout button when signed in, or a login link when signed out.
 * Must be a client component to read Supabase session from localStorage.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSupabaseClient, clearAuthCookie } from "@/lib/supabase";

export default function AuthHeader() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Read initial session
    getSupabaseClient()
      .auth.getSession()
      .then(({ data: { session } }) => {
        setEmail(session?.user?.email ?? null);
        setLoading(false);
      });

    // Subscribe to auth state changes (login / logout in other tabs)
    const {
      data: { subscription },
    } = getSupabaseClient().auth.onAuthStateChange((_event, session) => {
      setEmail(session?.user?.email ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  async function handleLogout() {
    await getSupabaseClient().auth.signOut();
    clearAuthCookie();
    router.push("/login");
  }

  if (loading) {
    return <span className="text-sm text-zinc-500">…</span>;
  }

  if (!email) {
    return (
      <Link
        href="/login"
        className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors"
      >
        Giriş Yap
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span
        className="text-sm text-zinc-400 max-w-[180px] truncate hidden sm:block"
        title={email}
      >
        {email}
      </span>
      <button
        onClick={handleLogout}
        className="
          text-sm rounded-md border border-zinc-700 px-3 py-1
          text-zinc-300 hover:text-zinc-100 hover:border-zinc-500
          transition-colors
        "
      >
        Çıkış
      </button>
    </div>
  );
}
