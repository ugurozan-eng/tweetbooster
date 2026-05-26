"use client";

import { useState } from "react";
import {
  getNicheTrending,
  generateNicheReply,
  ScoredTweet,
  NicheReply,
  TrendingResult,
  ApiError,
} from "@/lib/api";

// ── Constants ─────────────────────────────────────────────────────────────────

const NICHES = [
  { id: "food",     label: "YEMEK"    },
  { id: "football", label: "FUTBOL"   },
  { id: "economy",  label: "EKONOMİ"  },
  { id: "politics", label: "SİYASET"  },
] as const;

type NicheId = (typeof NICHES)[number]["id"];

const HOURS_OPTIONS = [
  { value: 1, label: "Son 1 saat" },
  { value: 3, label: "Son 3 saat" },
  { value: 6, label: "Son 6 saat" },
];

const HOOK_LABELS: Record<string, string> = {
  question: "SORU",
  opinion:  "GÖRÜŞ",
  fact:     "BİLGİ",
};

const HOOK_BADGE: Record<string, string> = {
  question: "badge badge-medium",
  opinion:  "badge badge-accent",
  fact:     "badge badge-high",
};

// ── Reply card ────────────────────────────────────────────────────────────────

function ReplyCard({ reply, index }: { reply: NicheReply; index: number }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(reply.text);
    } catch {
      const el = document.createElement("textarea");
      el.value = reply.text;
      el.style.position = "absolute";
      el.style.left = "-9999px";
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hookClass = HOOK_BADGE[reply.hook_type] ?? "badge badge-medium";
  const hookLabel = HOOK_LABELS[reply.hook_type] ?? reply.hook_type.toUpperCase();

  return (
    <div
      className="evidence-card stamp-in flex flex-col gap-3 p-4"
      style={{ minHeight: "160px" }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <p className="eyebrow">YANIT {index + 1}</p>
          <span className={hookClass}>{hookLabel}</span>
        </div>
        <button
          onClick={copy}
          className="btn-ghost"
          style={{
            fontSize: "0.65rem",
            padding: "0.25rem 0.625rem",
            color: copied ? "#6ee7b7" : undefined,
            borderColor: copied ? "#6ee7b7" : undefined,
          }}
        >
          {copied ? "KOPYALANDI ✓" : "KOPYALA"}
        </button>
      </div>

      {/* Reply text */}
      <p
        className="font-code flex-1"
        style={{ color: "var(--paper)", fontSize: "0.8rem", lineHeight: 1.75 }}
      >
        {reply.text}
      </p>

      {/* Char count */}
      <p className="datestamp text-right">{reply.text.length} karakter</p>
    </div>
  );
}

// ── Tweet row ─────────────────────────────────────────────────────────────────

type ReplyState = {
  loading: boolean;
  error: string | null;
  replies: NicheReply[] | null;
};

function TweetRow({ tweet, nicheId }: { tweet: ScoredTweet; nicheId: NicheId }) {
  const [state, setState] = useState<ReplyState>({
    loading: false,
    error: null,
    replies: null,
  });

  const generate = async () => {
    setState({ loading: true, error: null, replies: null });
    try {
      const data = await generateNicheReply(tweet.text, nicheId);
      setState({ loading: false, error: null, replies: data.replies });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Yanıt üretilirken hata oluştu.";
      setState({ loading: false, error: message, replies: null });
    }
  };

  return (
    <div className="evidence-card" style={{ background: "var(--surface)" }}>
      {/* ── Main row ────────────────────────────────────────────────── */}
      <div
        className="grid items-start gap-4 p-4"
        style={{ gridTemplateColumns: "3.5rem 1fr auto" }}
      >
        {/* Score column */}
        <div className="flex flex-col items-center pt-0.5 shrink-0">
          <span
            className="font-display leading-none"
            style={{ fontSize: "2.5rem", color: "var(--accent)" }}
          >
            {tweet.score}
          </span>
          <span className="eyebrow" style={{ fontSize: "0.5rem" }}>/10</span>
        </div>

        {/* Tweet text column */}
        <div className="flex flex-col gap-1.5 min-w-0">
          <p
            className="font-code"
            style={{ color: "var(--paper)", fontSize: "0.8125rem", lineHeight: 1.7 }}
          >
            {tweet.text}
          </p>
          {tweet.reason && (
            <p className="eyebrow" style={{ letterSpacing: "0.06em" }}>
              {tweet.reason}
            </p>
          )}
          {tweet.url && (
            <a
              href={tweet.url}
              target="_blank"
              rel="noopener noreferrer"
              className="footnote-link"
              style={{ width: "fit-content" }}
            >
              TWEET → KAYNAK
            </a>
          )}
        </div>

        {/* Action column */}
        <div className="shrink-0 pt-0.5">
          <button
            onClick={generate}
            disabled={state.loading}
            className="btn-ghost"
            style={{ whiteSpace: "nowrap" }}
          >
            {state.loading ? (
              <span className="cursor-blink" style={{ fontSize: "0.65rem" }}>
                ÜRET
              </span>
            ) : state.replies ? (
              "YENİDEN →"
            ) : (
              "YANIT ÜRET →"
            )}
          </button>
        </div>
      </div>

      {/* ── Inline error ───────────────────────────────────────────── */}
      {state.error && (
        <div
          className="mx-4 mb-4 px-3 py-2 font-code"
          style={{
            border: "1px solid var(--accent)",
            background: "rgba(232,25,44,0.07)",
            color: "var(--accent)",
            fontSize: "0.75rem",
          }}
        >
          {state.error}
        </div>
      )}

      {/* ── Replies panel ──────────────────────────────────────────── */}
      {state.replies && state.replies.length > 0 && (
        <div style={{ borderTop: "1px solid var(--border)", background: "var(--surface-2)" }}>
          <div className="p-4">
            <div className="rule-red mb-4" />
            <p className="eyebrow mb-3">YANIT SEÇENEKLERİ</p>
            <div
              className="grid gap-3"
              style={{ gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}
            >
              {state.replies.map((r, i) => (
                <ReplyCard key={i} reply={r} index={i} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NichePage() {
  const [nicheId, setNicheId]       = useState<NicheId>("food");
  const [hours, setHours]           = useState<number>(1);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [result, setResult]         = useState<TrendingResult | null>(null);

  const fetchTrending = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await getNicheTrending(nicheId, hours);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Tweetler getirilirken hata oluştu. Lütfen tekrar deneyin."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] px-4 py-12 max-w-6xl mx-auto">
      <div className="stagger-in">

        {/* ── Eyebrow ──────────────────────────────────────────────── */}
        <p className="eyebrow mb-4">MOD 02 · Niş Trend Analizi</p>

        {/* ── Headline ─────────────────────────────────────────────── */}
        <h1
          className="font-display leading-none mb-1"
          style={{ fontSize: "clamp(3rem, 9vw, 7rem)", color: "var(--paper)" }}
        >
          NİŞ MOD
        </h1>

        <div className="rule-red mb-8" />

        {/* ── Controls ─────────────────────────────────────────────── */}
        <div className="flex flex-col gap-6 mb-8">

          {/* Niche selector */}
          <div>
            <p className="eyebrow mb-3">NİŞ SEÇİN</p>
            {/* Gap-px grid creates 1px separator lines via the parent background */}
            <div
              className="grid grid-cols-2 sm:grid-cols-4"
              style={{ gap: "1px", background: "var(--border)" }}
            >
              {NICHES.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setNicheId(n.id)}
                  style={{
                    background: nicheId === n.id ? "var(--accent)" : "var(--surface)",
                    color:      nicheId === n.id ? "#fff" : "var(--muted)",
                    border:     "none",
                    padding:    "1.25rem 1rem",
                    cursor:     "pointer",
                    transition: "background 0.12s, color 0.12s",
                    textAlign:  "center",
                  }}
                >
                  <span
                    className="font-display block leading-none"
                    style={{
                      fontSize: "clamp(1.25rem, 3vw, 2rem)",
                      color: nicheId === n.id ? "#fff" : "var(--paper)",
                      transition: "color 0.12s",
                    }}
                  >
                    {n.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Hours + fetch row */}
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label
                htmlFor="hours-select"
                className="eyebrow mb-2 block"
              >
                ZAMAN ARALIĞI
              </label>
              <select
                id="hours-select"
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                className="field"
                style={{ width: "14rem" }}
              >
                {HOURS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={fetchTrending}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? (
                <span className="cursor-blink">YÜKLENIYOR</span>
              ) : (
                "TREND TWEETLER →"
              )}
            </button>
          </div>
        </div>

        {/* ── Error ────────────────────────────────────────────────── */}
        {error && (
          <div
            className="mb-6 px-4 py-3 font-code"
            style={{
              border: "1px solid var(--accent)",
              background: "rgba(232,25,44,0.07)",
              color: "var(--accent)",
              fontSize: "0.78rem",
            }}
          >
            {error}
          </div>
        )}

        {/* ── Empty state ───────────────────────────────────────────── */}
        {!result && !loading && !error && (
          <div
            className="px-6 py-16 text-center font-code"
            style={{
              border: "1px dashed var(--dim)",
              color: "var(--dim)",
              fontSize: "0.75rem",
              letterSpacing: "0.1em",
            }}
          >
            NİŞ SEÇİN · TREND TWEETLER GETİR
          </div>
        )}

        {/* ── Results ──────────────────────────────────────────────── */}
        {result && (
          <div>
            <div className="flex items-center gap-4 mb-4">
              <p className="eyebrow" style={{ whiteSpace: "nowrap" }}>
                TREND TWEETLER · {result.tweets.length} SONUÇ
              </p>
              <div className="rule-red flex-1" />
            </div>

            {result.tweets.length === 0 ? (
              <div
                className="px-6 py-10 text-center font-code"
                style={{
                  border: "1px solid var(--border)",
                  color: "var(--muted)",
                  fontSize: "0.8rem",
                }}
              >
                Bu niş için şu anda sonuç bulunamadı.
              </div>
            ) : (
              /* 1px gaps via parent background color */
              <div
                className="flex flex-col"
                style={{ gap: "1px", background: "var(--border)" }}
              >
                {result.tweets.map((tweet) => (
                  <TweetRow
                    key={tweet.url ?? tweet.text.slice(0, 40)}
                    tweet={tweet}
                    nicheId={nicheId}
                  />
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
