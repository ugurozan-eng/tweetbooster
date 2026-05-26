"use client";

import { useState, useCallback } from "react";
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
  { id: "food",     label: "YEMEK"   },
  { id: "football", label: "FUTBOL"  },
  { id: "economy",  label: "EKONOMİ" },
  { id: "politics", label: "SİYASET" },
] as const;

type NicheId = (typeof NICHES)[number]["id"];

const HOURS_OPTIONS = [
  { value: 1, label: "1S"  },
  { value: 3, label: "3S"  },
  { value: 6, label: "6S"  },
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

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const el = document.createElement("textarea");
      el.value = text;
      el.style.cssText = "position:absolute;left:-9999px";
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 800);
  }, [text]);

  return (
    <button
      onClick={copy}
      className={`btn-ghost ${copied ? "copied-flash" : ""}`}
      style={{ fontSize: "0.6rem", padding: "0.25rem 0.625rem" }}
      aria-label="Yanıtı kopyala"
    >
      {copied ? "✓ KOPYALANDI" : "KOPYALA"}
    </button>
  );
}

// ── Reply card (inside expanded row) ─────────────────────────────────────────

function NicheReplyCard({
  reply,
  index,
}: {
  reply: NicheReply;
  index: number;
}) {
  const hookClass = HOOK_BADGE[reply.hook_type] ?? "badge badge-medium";
  const hookLabel = HOOK_LABELS[reply.hook_type] ?? reply.hook_type.toUpperCase();

  return (
    <div
      className="evidence-card stamp-in flex flex-col gap-3 p-4"
      style={{ minHeight: "140px" }}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <p className="eyebrow">YANIT {index + 1}</p>
          <span className={hookClass}>{hookLabel}</span>
        </div>
        <CopyButton text={reply.text} />
      </div>
      <p
        className="font-code flex-1"
        style={{ fontSize: "0.8rem", color: "var(--paper)", lineHeight: 1.75 }}
      >
        {reply.text}
      </p>
      <p className="datestamp text-right">{reply.text.length} kar.</p>
    </div>
  );
}

// ── Tweet row ─────────────────────────────────────────────────────────────────

type ReplyState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "done"; replies: NicheReply[] };

function TweetRow({
  tweet,
  nicheId,
}: {
  tweet: ScoredTweet;
  nicheId: NicheId;
}) {
  const [state, setState] = useState<ReplyState>({ phase: "idle" });

  const generate = async () => {
    setState({ phase: "loading" });
    try {
      const data = await generateNicheReply(tweet.text, nicheId);
      setState({ phase: "done", replies: data.replies });
    } catch (err) {
      setState({
        phase: "error",
        message:
          err instanceof ApiError ? err.message : "Yanıt üretilirken hata oluştu.",
      });
    }
  };

  const isLoading = state.phase === "loading";

  return (
    <div style={{ background: "var(--surface)" }}>
      {/* ── Main row ─────────────────────────────────────────── */}
      <div
        className="grid items-start gap-4 px-4 py-3"
        style={{ gridTemplateColumns: "2.75rem 1fr auto" }}
      >
        {/* Score */}
        <div className="flex flex-col items-center shrink-0 pt-0.5">
          <span
            className="font-display leading-none"
            style={{ fontSize: "2.25rem", color: "var(--accent)" }}
          >
            {tweet.score}
          </span>
          <span className="eyebrow" style={{ fontSize: "0.45rem" }}>/10</span>
        </div>

        {/* Tweet text */}
        <div className="flex flex-col gap-1 min-w-0 py-1">
          <p
            className="font-code"
            style={{
              fontSize: "0.8125rem",
              color: "var(--paper)",
              lineHeight: 1.6,
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {tweet.text}
          </p>
          {tweet.url && (
            <a
              href={tweet.url}
              target="_blank"
              rel="noopener noreferrer"
              className="footnote-link"
              style={{ width: "fit-content" }}
            >
              KAYNAK →
            </a>
          )}
        </div>

        {/* Action */}
        <div className="shrink-0 pt-1">
          <button
            onClick={generate}
            disabled={isLoading}
            className="btn-ghost"
            style={{ whiteSpace: "nowrap" }}
          >
            {isLoading ? (
              <span className="cursor-blink" style={{ fontSize: "0.6rem" }}>
                ÜRET
              </span>
            ) : state.phase === "done" ? (
              "YENİDEN →"
            ) : (
              "YANITLA →"
            )}
          </button>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────── */}
      {state.phase === "error" && (
        <div className="error-box mx-4 mb-3" style={{ fontSize: "0.73rem" }}>
          {state.message}
        </div>
      )}

      {/* ── Reply expansion ──────────────────────────────────── */}
      {state.phase === "done" && state.replies.length > 0 && (
        <div
          className="p-4"
          style={{ borderTop: "1px solid var(--border)", background: "var(--surface-2)" }}
        >
          <div className="rule-red mb-4" />
          <p className="eyebrow mb-3">YANIT SEÇENEKLERİ</p>
          <div
            className="grid gap-3"
            style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}
          >
            {state.replies.map((r, i) => (
              <NicheReplyCard key={i} reply={r} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NichePage() {
  const [nicheId, setNicheId] = useState<NicheId>("food");
  const [hours, setHours]     = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [result, setResult]   = useState<TrendingResult | null>(null);

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
    <div className="min-h-[calc(100vh-48px)] px-4 py-10 max-w-6xl mx-auto">
      <div className="stagger-in">

        {/* ── Eyebrow + heading ────────────────────────────────── */}
        <p className="eyebrow mb-3">MOD 02 · Niş Trend Analizi</p>
        <h1
          className="font-display leading-none mb-1"
          style={{ fontSize: "clamp(3rem, 9vw, 6rem)", color: "var(--paper)" }}
        >
          NİŞ MOD
        </h1>
        <div className="rule-red mb-8" />

        {/* ── Controls ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-6 mb-8">

          {/* Niche selector — 4 bordered buttons, selected = red fill */}
          <div>
            <p className="eyebrow mb-3">NİŞ SEÇİN</p>
            <div
              className="grid grid-cols-2 sm:grid-cols-4"
              style={{ gap: "1px", background: "var(--accent)" }}
            >
              {NICHES.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setNicheId(n.id)}
                  style={{
                    background: nicheId === n.id ? "var(--accent)" : "var(--bg)",
                    color:      nicheId === n.id ? "#000"          : "var(--muted)",
                    border:     "none",
                    padding:    "1.25rem 1rem",
                    cursor:     "pointer",
                    transition: "background 0.1s, color 0.1s",
                    textAlign:  "center",
                  }}
                >
                  <span
                    className="font-display block leading-none"
                    style={{
                      fontSize: "clamp(1.25rem, 3vw, 2rem)",
                      color: nicheId === n.id ? "#000" : "var(--paper)",
                      transition: "color 0.1s",
                    }}
                  >
                    {n.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Hours pills + fetch button */}
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <p className="eyebrow mb-3">ZAMAN ARALIĞI</p>
              <div className="flex gap-px" style={{ background: "var(--border)" }}>
                {HOURS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setHours(opt.value)}
                    style={{
                      background: hours === opt.value ? "var(--accent)" : "var(--surface)",
                      color:      hours === opt.value ? "#000"          : "var(--muted)",
                      border:     "none",
                      padding:    "0.5rem 1rem",
                      cursor:     "pointer",
                      transition: "background 0.1s, color 0.1s",
                    }}
                  >
                    <span
                      className="font-display"
                      style={{
                        fontSize: "1.25rem",
                        letterSpacing: "0.04em",
                        color: hours === opt.value ? "#000" : "var(--paper)",
                        transition: "color 0.1s",
                      }}
                    >
                      {opt.label}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={fetchTrending}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? (
                <span className="cursor-blink">YÜKLENIYOR</span>
              ) : (
                "TWEET&apos;LERİ GETİR →"
              )}
            </button>
          </div>
        </div>

        {/* ── Error ────────────────────────────────────────────── */}
        {error && <div className="error-box mb-6">{error}</div>}

        {/* ── Empty state ───────────────────────────────────────── */}
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
            // NİŞ SEÇİN · TREND TWEETLER GETİR
          </div>
        )}

        {/* ── Results table ────────────────────────────────────── */}
        {result && (
          <div>
            <div className="flex items-center gap-4 mb-3">
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
              /* 1px separators via parent bg color */
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
