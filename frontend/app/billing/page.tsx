"use client";

/**
 * TwitBoost — Hesabım / Billing Page
 * ====================================
 * Shows current plan + available plan cards with checkout flow.
 * Neo-brutalist design: sharp edges, Bebas Neue headings, IBM Plex Mono body.
 */

import { useState, useEffect, useCallback } from "react";
import {
  getBillingPlans,
  getBillingStatus,
  createCheckout,
  BillingPlan,
  BillingStatus,
  ApiError,
} from "@/lib/api";

// ── Plan badge label map ───────────────────────────────────────────────────

const PLAN_DISPLAY: Record<string, string> = {
  trial:      "ÜCRETSİZ DENEME",
  niche:      "NİŞ MOD",
  opposition: "MUHALEFET MODU",
  full:       "TAM ERİŞİM",
};

// ── Checkout button state ─────────────────────────────────────────────────

type CheckoutState =
  | { phase: "idle" }
  | { phase: "loading"; planId: string }
  | { phase: "error"; message: string };

// ── Plan card ─────────────────────────────────────────────────────────────

function PlanCard({
  plan,
  isActive,
  onBuy,
  isLoading,
}: {
  plan: BillingPlan;
  isActive: boolean;
  onBuy: (planId: string) => void;
  isLoading: boolean;
}) {
  return (
    <div
      style={{
        border: isActive ? "2px solid var(--accent)" : "1px solid var(--border)",
        background: isActive ? "var(--accent)" : "var(--surface)",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        position: "relative",
      }}
    >
      {/* Active badge */}
      {isActive && (
        <div
          className="eyebrow"
          style={{
            position: "absolute",
            top: "0.75rem",
            right: "0.75rem",
            background: "#000",
            color: "var(--accent)",
            padding: "0.125rem 0.5rem",
            fontSize: "0.55rem",
          }}
        >
          AKTİF PLAN
        </div>
      )}

      {/* Plan name */}
      <h2
        className="font-display leading-none"
        style={{
          fontSize: "clamp(1.5rem, 4vw, 2.5rem)",
          color: isActive ? "#000" : "var(--paper)",
        }}
      >
        {plan.name.toUpperCase()}
      </h2>

      {/* Price */}
      <div>
        <span
          className="font-display leading-none"
          style={{
            fontSize: "clamp(2rem, 6vw, 3.5rem)",
            color: isActive ? "#000" : "var(--accent)",
          }}
        >
          {plan.price_try.toFixed(2)}
        </span>
        <span
          className="font-code"
          style={{
            fontSize: "0.75rem",
            color: isActive ? "#000" : "var(--muted)",
            marginLeft: "0.375rem",
          }}
        >
          TL / AY
        </span>
      </div>

      {/* Divider */}
      <div
        style={{
          borderTop: `1px solid ${isActive ? "#000" : "var(--border)"}`,
        }}
      />

      {/* Details */}
      <div className="flex flex-col gap-1.5">
        <p
          className="font-code"
          style={{ fontSize: "0.75rem", color: isActive ? "#000" : "var(--muted)" }}
        >
          Günlük {plan.daily_limit} kullanım
        </p>
        <p
          className="font-code"
          style={{ fontSize: "0.75rem", color: isActive ? "#000" : "var(--muted)" }}
        >
          {plan.modes.map((m) => (m === "niche" ? "Niş Mod" : "Muhalefet Modu")).join(" + ")}
        </p>
      </div>

      {/* CTA */}
      {!isActive && (
        <button
          onClick={() => onBuy(plan.id)}
          disabled={isLoading}
          className="btn-primary"
          style={{ marginTop: "auto" }}
        >
          {isLoading ? (
            <span className="cursor-blink">YÖNLENDİRİLİYOR</span>
          ) : (
            "SATIN AL →"
          )}
        </button>
      )}

      {isActive && (
        <div
          className="eyebrow"
          style={{
            background: "#000",
            color: "var(--accent)",
            padding: "0.75rem 1rem",
            textAlign: "center",
            marginTop: "auto",
            fontSize: "0.7rem",
          }}
        >
          MEVCUT PLANIN
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

export default function BillingPage() {
  const [plans,  setPlans]  = useState<BillingPlan[]>([]);
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [checkout, setCheckout]   = useState<CheckoutState>({ phase: "idle" });

  // ── Load plans + status in parallel ─────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [plansData, statusData] = await Promise.all([
          getBillingPlans(),
          getBillingStatus(),
        ]);
        if (!cancelled) {
          setPlans(plansData);
          setStatus(statusData);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError
              ? err.message
              : "Hesap bilgileri yüklenemedi."
          );
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Checkout handler ─────────────────────────────────────────────────────
  const handleBuy = useCallback(async (planId: string) => {
    setCheckout({ phase: "loading", planId });
    try {
      const { checkout_url } = await createCheckout(planId);
      window.location.href = checkout_url;
    } catch (err) {
      setCheckout({
        phase: "error",
        message:
          err instanceof ApiError
            ? err.message
            : "Ödeme sayfası açılamadı. Lütfen tekrar deneyin.",
      });
    }
  }, []);

  const isCheckoutLoading = checkout.phase === "loading";

  return (
    <div className="min-h-[calc(100vh-48px)] px-4 py-10 max-w-6xl mx-auto">
      <div className="stagger-in">

        {/* ── Heading ──────────────────────────────────────────── */}
        <p className="eyebrow mb-3">HESABIM · Abonelik</p>
        <h1
          className="font-display leading-none mb-1"
          style={{ fontSize: "clamp(3rem, 9vw, 6rem)", color: "var(--paper)" }}
        >
          HESABIM
        </h1>
        <div className="rule-red mb-8" />

        {/* ── Load error ────────────────────────────────────────── */}
        {loadError && (
          <div className="error-box mb-8">{loadError}</div>
        )}

        {/* ── Current plan banner ──────────────────────────────── */}
        {status && (
          <div
            className="mb-8 px-5 py-4 flex items-center gap-4"
            style={{ border: "1px solid var(--border)", background: "var(--surface)" }}
          >
            <div>
              <p className="eyebrow" style={{ fontSize: "0.55rem" }}>AKTİF PLAN</p>
              <p
                className="font-display leading-none mt-1"
                style={{ fontSize: "1.75rem", color: "var(--accent)" }}
              >
                {PLAN_DISPLAY[status.plan] ?? status.plan.toUpperCase()}
              </p>
            </div>
            {status.plan === "trial" && (
              <p
                className="font-code ml-auto"
                style={{ fontSize: "0.7rem", color: "var(--muted)" }}
              >
                Günlük 3 kullanım · Her iki mod
              </p>
            )}
          </div>
        )}

        {/* ── Plan grid ────────────────────────────────────────── */}
        {plans.length > 0 && (
          <>
            <p className="eyebrow mb-4">PLANI SEÇ</p>

            {/* Checkout error */}
            {checkout.phase === "error" && (
              <div className="error-box mb-5">{checkout.message}</div>
            )}

            <div
              className="grid gap-px"
              style={{
                gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
                background: "var(--border)",
              }}
            >
              {plans.map((plan) => (
                <PlanCard
                  key={plan.id}
                  plan={plan}
                  isActive={status?.plan === plan.id}
                  onBuy={handleBuy}
                  isLoading={
                    isCheckoutLoading &&
                    checkout.phase === "loading" &&
                    checkout.planId === plan.id
                  }
                />
              ))}
            </div>

            {/* Fine print */}
            <p
              className="font-code mt-6"
              style={{ fontSize: "0.65rem", color: "var(--dim)", lineHeight: 1.7 }}
            >
              // Ödeme LemonSqueezy üzerinden güvenli şekilde işlenir. Abonelik iptal
              edilirse bir sonraki fatura döneminde deneme planına geçilir. Fiyatlar KDV hariçtir.
            </p>
          </>
        )}

        {/* ── Loading skeleton ─────────────────────────────────── */}
        {!loadError && plans.length === 0 && (
          <div
            className="px-6 py-16 text-center font-code"
            style={{
              border: "1px dashed var(--dim)",
              color: "var(--dim)",
              fontSize: "0.75rem",
              letterSpacing: "0.1em",
            }}
          >
            // HESAP BİLGİLERİ YÜKLENİYOR
          </div>
        )}

      </div>
    </div>
  );
}
