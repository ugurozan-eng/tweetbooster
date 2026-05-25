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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NICHES = [
  { id: "food", label: "Yemek & Tarif", emoji: "🍳" },
  { id: "football", label: "Futbol", emoji: "⚽" },
  { id: "economy", label: "Ekonomi & Finans", emoji: "📈" },
  { id: "politics", label: "Siyaset", emoji: "🏛" },
] as const;

type NicheId = (typeof NICHES)[number]["id"];

const HOURS_OPTIONS = [
  { value: 1, label: "Son 1 saat" },
  { value: 3, label: "Son 3 saat" },
  { value: 6, label: "Son 6 saat" },
];

const HOOK_TYPE_STYLES: Record<string, string> = {
  question: "bg-blue-900/40 text-blue-400 border-blue-700",
  opinion: "bg-violet-900/40 text-violet-400 border-violet-700",
  fact: "bg-emerald-900/40 text-emerald-400 border-emerald-700",
};

const HOOK_TYPE_LABELS: Record<string, string> = {
  question: "Soru",
  opinion: "Görüş",
  fact: "Bilgi",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function scoreBadgeStyle(score: number): string {
  if (score >= 7) return "bg-green-900/40 text-green-400 border-green-700";
  if (score >= 4) return "bg-yellow-900/40 text-yellow-400 border-yellow-700";
  return "bg-red-900/40 text-red-400 border-red-700";
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Spinner({ size = "md" }: { size?: "sm" | "md" }) {
  const cls = size === "sm" ? "h-4 w-4" : "h-5 w-5";
  return (
    <svg
      className={`animate-spin ${cls} text-blue-400`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8z"
      />
    </svg>
  );
}

function NicheReplyCard({ reply }: { reply: NicheReply }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
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

  const hookStyle =
    HOOK_TYPE_STYLES[reply.hook_type] ??
    "bg-zinc-800 text-zinc-400 border-zinc-700";
  const hookLabel = HOOK_TYPE_LABELS[reply.hook_type] ?? reply.hook_type;

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800/60 px-4 py-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full border ${hookStyle}`}
        >
          {hookLabel}
        </span>
        <button
          onClick={copyToClipboard}
          className="text-xs px-2.5 py-1 rounded bg-zinc-700 hover:bg-zinc-600 text-zinc-300 hover:text-white transition-colors"
        >
          {copied ? "Kopyalandı ✓" : "Kopyala"}
        </button>
      </div>
      <p className="text-sm text-zinc-200 leading-relaxed">{reply.text}</p>
      <p className="text-xs text-zinc-600 text-right">
        {reply.text.length} karakter
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tweet row — handles its own reply state
// ---------------------------------------------------------------------------

type TweetReplyState = {
  loading: boolean;
  error: string | null;
  replies: NicheReply[] | null;
};

function TweetRow({
  tweet,
  nicheId,
}: {
  tweet: ScoredTweet;
  nicheId: NicheId;
}) {
  const [state, setState] = useState<TweetReplyState>({
    loading: false,
    error: null,
    replies: null,
  });

  const handleGenerateReply = async () => {
    setState({ loading: true, error: null, replies: null });
    try {
      const data = await generateNicheReply(tweet.text, nicheId);
      setState({ loading: false, error: null, replies: data.replies });
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Yanıt üretilirken bir hata oluştu.";
      setState({ loading: false, error: message, replies: null });
    }
  };

  return (
    <li className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 flex flex-col gap-3">
      {/* Tweet header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-zinc-200 leading-relaxed line-clamp-3">
            {tweet.text}
          </p>
          <p className="text-xs text-zinc-500 mt-1.5 italic">{tweet.reason}</p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {/* Score badge */}
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full border ${scoreBadgeStyle(tweet.score)}`}
          >
            {tweet.score}/10
          </span>

          {/* Tweet link */}
          {tweet.url && (
            <a
              href={tweet.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2"
            >
              Tweet →
            </a>
          )}
        </div>
      </div>

      {/* Yanıt Üret button */}
      <button
        onClick={handleGenerateReply}
        disabled={state.loading}
        className="self-start flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-300 hover:text-white transition-colors border border-zinc-700"
      >
        {state.loading ? (
          <>
            <Spinner size="sm" />
            Üretiliyor…
          </>
        ) : state.replies ? (
          "Yeniden Üret"
        ) : (
          "Yanıt Üret"
        )}
      </button>

      {/* Inline error */}
      {state.error && (
        <p className="text-xs text-red-400 border border-red-800 bg-red-950/30 rounded px-3 py-2">
          {state.error}
        </p>
      )}

      {/* Generated replies */}
      {state.replies && state.replies.length > 0 && (
        <div className="flex flex-col gap-2 pt-1">
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Yanıt Seçenekleri
          </p>
          {state.replies.map((reply, i) => (
            <NicheReplyCard key={i} reply={reply} />
          ))}
        </div>
      )}
    </li>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function NichePage() {
  const [nicheId, setNicheId] = useState<NicheId>("food");
  const [hours, setHours] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trendingResult, setTrendingResult] = useState<TrendingResult | null>(
    null
  );

  const handleFetchTrending = async () => {
    setLoading(true);
    setError(null);
    setTrendingResult(null);

    try {
      const data = await getNicheTrending(nicheId, hours);
      setTrendingResult(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Tweetler getirilirken bir hata oluştu. Lütfen tekrar deneyin.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Page heading */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Niş Mod</h1>
        <p className="text-zinc-400 text-sm">
          Nişinizi seçin, trend tweetleri getirin ve etkileşim yanıtları üretin.
        </p>
      </div>

      {/* ── Controls ─────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-5">
        {/* Niche selector */}
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-zinc-300">Niş seçin</span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {NICHES.map((n) => (
              <button
                key={n.id}
                onClick={() => setNicheId(n.id)}
                className={`rounded-lg border px-3 py-3 text-sm font-medium transition-colors flex flex-col items-center gap-1 ${
                  nicheId === n.id
                    ? "border-emerald-600 bg-emerald-950/30 text-emerald-300"
                    : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-600 hover:text-white"
                }`}
              >
                <span className="text-xl" role="img" aria-label={n.label}>
                  {n.emoji}
                </span>
                <span className="text-xs leading-tight text-center">
                  {n.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Hours selector */}
        <div className="flex flex-col gap-2">
          <label
            htmlFor="hours-select"
            className="text-sm font-medium text-zinc-300"
          >
            Zaman aralığı
          </label>
          <select
            id="hours-select"
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="w-full sm:w-48 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-emerald-500 transition-colors"
          >
            {HOURS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Fetch button */}
        <button
          onClick={handleFetchTrending}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 transition-colors text-sm self-start"
        >
          {loading ? (
            <>
              <Spinner />
              Yükleniyor…
            </>
          ) : (
            "Tweet'leri Getir"
          )}
        </button>
      </div>

      {/* ── Error banner ─────────────────────────────────────────────── */}
      {error && (
        <div className="mt-6 rounded-lg border border-red-700 bg-red-950/40 px-4 py-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────────────── */}
      {trendingResult && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              Trend Tweetler
            </h2>
            <span className="text-xs text-zinc-600">
              {trendingResult.tweets.length} sonuç
            </span>
          </div>

          {trendingResult.tweets.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-5 py-8 text-center">
              <p className="text-zinc-400 text-sm">
                Bu niş için şu anda sonuç bulunamadı.
              </p>
            </div>
          ) : (
            <ul className="flex flex-col gap-3">
              {trendingResult.tweets.map((tweet) => (
                <TweetRow key={tweet.url} tweet={tweet} nicheId={nicheId} />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
