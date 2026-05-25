/**
 * TwitBoost — Proxy (Next.js 16 route protection)
 * =================================================
 * Runs on every request matching the `config.matcher` below.
 * Redirects unauthenticated users away from protected routes.
 *
 * Auth check: presence cookie `twitboost-authed=1` (optimistic, no JWT
 * verification — the real JWT check happens in the FastAPI backend).
 * The cookie is set client-side after Supabase sign-in and cleared on logout.
 *
 * NOTE: In Next.js 16, this file is named proxy.ts (renamed from middleware.ts).
 * See: node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md
 */

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const PROTECTED_PATHS = ["/opposition", "/niche"];
const AUTH_COOKIE = "twitboost-authed";

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const isProtected = PROTECTED_PATHS.some((p) => pathname.startsWith(p));
  if (!isProtected) {
    return NextResponse.next();
  }

  const isAuthed = Boolean(req.cookies.get(AUTH_COOKIE)?.value);
  if (!isAuthed) {
    const loginUrl = new URL("/login", req.nextUrl);
    loginUrl.searchParams.set("next", pathname); // preserve intended destination
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Run on all routes except Next.js internals and static assets.
  // API routes handled by FastAPI — no proxy needed there.
  matcher: ["/((?!_next/static|_next/image|favicon\\.ico).*)"],
};
