-- ============================================================
-- TwitBoost — Migration 002: LemonSqueezy Subscription Fields
-- ============================================================
-- Apply manually via Supabase SQL Editor:
--   Dashboard → SQL Editor → New Query → paste → Run
--
-- DO NOT run this file automatically from application code.
-- Prerequisites: Migration 001 must already be applied.
-- ============================================================

-- Add LemonSqueezy subscription tracking columns to public.users.
-- All columns nullable — only populated after a successful purchase.
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS lemonsqueezy_customer_id      text,
    ADD COLUMN IF NOT EXISTS lemonsqueezy_subscription_id  text,
    ADD COLUMN IF NOT EXISTS plan_expires_at               timestamptz;

-- Optional index: fast look-up of expiring subscriptions for future cron jobs.
CREATE INDEX IF NOT EXISTS users_plan_expires_at
    ON public.users (plan_expires_at)
    WHERE plan_expires_at IS NOT NULL;

-- ============================================================
-- Rollback (run manually if needed)
-- ============================================================
-- ALTER TABLE public.users
--     DROP COLUMN IF EXISTS lemonsqueezy_customer_id,
--     DROP COLUMN IF EXISTS lemonsqueezy_subscription_id,
--     DROP COLUMN IF EXISTS plan_expires_at;
-- DROP INDEX IF EXISTS users_plan_expires_at;
