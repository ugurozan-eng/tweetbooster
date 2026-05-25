/**
 * Supabase OAuth callback handler.
 *
 * After Google sign-in, Supabase redirects here with a code.
 * We exchange the code for a session, set the auth presence cookie,
 * then redirect to the home page.
 *
 * Route: GET /auth/callback
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const AUTH_COOKIE = "twitboost-authed";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7; // 7 days

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");

  if (code) {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ""
    );
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      const response = NextResponse.redirect(origin);
      response.cookies.set(AUTH_COOKIE, "1", {
        path: "/",
        maxAge: COOKIE_MAX_AGE,
        sameSite: "lax",
        httpOnly: false, // needs to be readable client-side for logout cleanup
      });
      return response;
    }
  }

  // Something went wrong — redirect to login with error param
  return NextResponse.redirect(`${origin}/login?error=oauth_failed`);
}
