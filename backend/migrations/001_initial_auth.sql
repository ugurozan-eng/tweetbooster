-- ============================================================
-- TwitBoost — Migration 001: Auth Foundation
-- ============================================================
-- Apply manually via Supabase SQL Editor or CLI:
--   supabase db push  (if using Supabase CLI)
--   or paste into: Dashboard → SQL Editor → New Query
--
-- DO NOT run this file automatically from application code.
-- ============================================================

-- ------------------------------------------------------------
-- Users table
-- Mirrors the Supabase Auth user record so we can store plan.
-- id = Supabase Auth user UUID (same value as auth.users.id)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id          uuid PRIMARY KEY,          -- Supabase Auth UID
    email       text NOT NULL UNIQUE,
    plan        text NOT NULL DEFAULT 'trial'
                     CHECK (plan IN ('trial', 'niche', 'opposition', 'full')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Row-level security: users can only read/update their own row
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users: own row read"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "users: own row update"
    ON public.users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Service role bypasses RLS — backend uses service key for admin writes.

-- ------------------------------------------------------------
-- Usage logs table
-- One row per successful analysis request. Immutable audit log.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mode        text NOT NULL CHECK (mode IN ('opposition', 'niche')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Row-level security: users can only read their own logs
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usage_logs: own rows read"
    ON public.usage_logs FOR SELECT
    USING (auth.uid() = user_id);

-- Inserts only via service role key — no INSERT policy for authenticated users.

-- Indexes for the daily_usage view query
CREATE INDEX IF NOT EXISTS usage_logs_user_created
    ON public.usage_logs (user_id, created_at);

-- ------------------------------------------------------------
-- daily_usage view
-- Counts per-user, per-UTC+3-date to enforce daily limits.
-- Grouped by Istanbul time (UTC+3) so reset is at midnight local.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW public.daily_usage AS
SELECT
    user_id,
    (created_at AT TIME ZONE 'Europe/Istanbul')::date  AS day,
    COUNT(*) FILTER (WHERE mode = 'opposition')        AS opposition_count,
    COUNT(*) FILTER (WHERE mode = 'niche')             AS niche_count,
    COUNT(*)                                           AS total_count
FROM public.usage_logs
GROUP BY user_id, (created_at AT TIME ZONE 'Europe/Istanbul')::date;

-- ============================================================
-- Rollback (run manually if needed)
-- ============================================================
-- DROP VIEW  IF EXISTS public.daily_usage;
-- DROP TABLE IF EXISTS public.usage_logs;
-- DROP TABLE IF EXISTS public.users;
