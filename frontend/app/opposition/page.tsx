"use client";

import { useState } from "react";
import {
  runOppositionAnalysis,
  AnalysisResult,
  Contradiction,
  ReplyContent,
  ApiError,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TONE_LABELS: Record<string, string> = {
  cold: "Soğuk",
  sharp: "Keskin",
  thread: "Thread",
};

const TONE_DESCRIPTIONS: Record<string, string> = {
  cold: "Nötr, gazetecilik tonu",
  sharp: "İğneleyici, dokunaklı",
  thread: "Çok tweetlik dizi",
};

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-900/40 text-green-400 border-green-700",
  medium: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
  low: "bg-red-900/40 text-red-400 border-red-700",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  high: "Yüksek",
  medium: "Orta",
  low: "Düşük",
};

function confidenceStyle(c: string): string {
  return (
    CONFIDENCE_STYLES[c.toLowerCase()] ??
    "bg-zinc-800 text-zinc-400 border-zinc-700"
  );
}

function confidenceLabel(c: string): string {
  return CONFIDENCE_LABELS[c.toLowerCase()] ?? c;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-blue-400"
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

function ContradictionCard({ c, index }: { c: Contradiction; index: number }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          Çelişki #{index + 1}
        </span>
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full border ${confidenceStyle(c.confidence)}`}
        >
          {confidenceLabel(c.confidence)} güven
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-zinc-300 mb-3">{c.summary}</p>

      {/* Statements */}
      <div className="grid sm:grid-cols-2 gap-3">
        <div className="rounded-md border border-zinc-700 bg-zinc-800/60 p-3">
          <p className="text-xs text-zinc-500 mb-1">{c.date_a}</p>
          <p className="text-sm text-zinc-200">&ldquo;{c.statement_a}&rdquo;</p>
        </div>
        <div className="rounded-md border border-zinc-700 bg-zinc-800/60 p-3">
          <p className="text-xs text-zinc-500 mb-1">{c.date_b}</p>
          <p className="text-sm text-zinc-200">&ldquo;{c.statement_b}&rdquo;</p>
        </div>
      </div>

      {/* Source */}
      {c.source_url && (
        <a
          href={c.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2"
        >
          Kaynak →
        </a>
      )}
    </div>
  );
}

function ReplyCard({
  tone,
  reply,
}: {
  tone: string;
  reply: ReplyContent;
}) {
  const [copied, setCopied] = useState(false);

  const textToCopy =
    tone === "thread" && reply.thread.length > 0
      ? reply.thread.join("\n\n")
      : reply.tweet_text;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
    } catch {
      // Fallback for older browsers
      const el = document.createElement("textarea");
      el.value = textToCopy;
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

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
          {TONE_LABELS[tone] ?? tone}
        </span>
        <button
          onClick={copyToClipboard}
          className="text-xs px-3 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white transition-colors border border-zinc-700"
        >
          {copied ? "Kopyalandı ✓" : "Kopyala"}
        </button>
      </div>

      {/* Content */}
      {tone === "thread" && reply.thread.length > 0 ? (
        <ol className="flex flex-col gap-2">
          {reply.thread.map((tweet, i) => (
            <li
              key={i}
              className="text-sm text-zinc-200 border-l-2 border-zinc-700 pl-3"
            >
              {tweet}
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-sm text-zinc-200 leading-relaxed">
          {reply.tweet_text}
        </p>
      )}

      {/* Disclaimer */}
      {reply.disclaimer && (
        <p className="text-xs text-zinc-500 border-t border-zinc-800 pt-2">
          {reply.disclaimer}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tones = { cold: boolean; sharp: boolean; thread: boolean };

export default function OppositionPage() {
  const [tweetText, setTweetText] = useState("");
  const [tones, setTones] = useState<Tones>({
    cold: true,
    sharp: true,
    thread: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const selectedToneList = (
    Object.entries(tones) as [keyof Tones, boolean][]
  )
    .filter(([, v]) => v)
    .map(([k]) => k);

  const canSubmit =
    tweetText.trim().length > 0 && selectedToneList.length > 0 && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await runOppositionAnalysis(tweetText, selectedToneList);
      setResult(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.");
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleTone = (key: keyof Tones) => {
    setTones((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Page heading */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Muhalif Mod</h1>
        <p className="text-zinc-400 text-sm">
          Bir tweet yapıştırın; araç kişiyi araştırır, tutarsızlıkları bulur ve
          yanıt üretir.
        </p>
      </div>

      {/* ── Form ──────────────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {/* Tweet textarea */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="tweet-input"
            className="text-sm font-medium text-zinc-300"
          >
            Tweet metni
          </label>
          <textarea
            id="tweet-input"
            rows={4}
            value={tweetText}
            onChange={(e) => setTweetText(e.target.value)}
            placeholder="Tweet metnini yapıştırın…"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500 resize-none transition-colors"
          />
        </div>

        {/* Tone checkboxes */}
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-zinc-300">
            Yanıt tonu
          </span>
          <div className="flex flex-col sm:flex-row gap-3">
            {(Object.keys(TONE_LABELS) as (keyof Tones)[]).map((key) => (
              <label
                key={key}
                className={`flex items-start gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors ${
                  tones[key]
                    ? "border-blue-600 bg-blue-950/30"
                    : "border-zinc-700 bg-zinc-900 hover:border-zinc-600"
                }`}
              >
                <input
                  type="checkbox"
                  checked={tones[key]}
                  onChange={() => toggleTone(key)}
                  className="mt-0.5 accent-blue-500"
                />
                <span className="flex flex-col">
                  <span className="text-sm font-medium text-zinc-100">
                    {TONE_LABELS[key]}
                  </span>
                  <span className="text-xs text-zinc-500">
                    {TONE_DESCRIPTIONS[key]}
                  </span>
                </span>
              </label>
            ))}
          </div>
          {selectedToneList.length === 0 && (
            <p className="text-xs text-yellow-500">
              En az bir ton seçmelisiniz.
            </p>
          )}
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 transition-colors text-sm"
        >
          {loading ? (
            <>
              <Spinner />
              Araştırılıyor…
            </>
          ) : (
            "Analiz Et"
          )}
        </button>
      </form>

      {/* ── Error banner ─────────────────────────────────────────────── */}
      {error && (
        <div className="mt-6 rounded-lg border border-red-700 bg-red-950/40 px-4 py-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────────────── */}
      {result && (
        <div className="mt-8 flex flex-col gap-6">
          {/* Person info card */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <h2 className="text-lg font-bold text-white">
                {result.person_name || "Kişi tespit edilemedi"}
              </h2>
              {result.contradictions.length > 0 && (
                <p className="text-sm text-zinc-400 mt-0.5">
                  {result.contradictions.length} çelişki bulundu
                </p>
              )}
            </div>
            <span
              className={`self-start sm:self-auto text-xs font-medium px-3 py-1 rounded-full border ${confidenceStyle(
                result.contradictions[0]?.confidence ?? "low"
              )}`}
            >
              {confidenceLabel(
                result.contradictions[0]?.confidence ?? "low"
              )}{" "}
              güven
            </span>
          </div>

          {/* No contradictions */}
          {result.status === "no_contradictions_found" && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-5 py-6 text-center">
              <p className="text-zinc-400 text-sm">
                Bu tweet için tutarsızlık bulunamadı.
              </p>
            </div>
          )}

          {/* Contradictions list */}
          {result.contradictions.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                Tespit Edilen Çelişkiler
              </h3>
              <div className="flex flex-col gap-3">
                {result.contradictions.map((c, i) => (
                  <ContradictionCard key={i} c={c} index={i} />
                ))}
              </div>
            </section>
          )}

          {/* Reply cards */}
          {(["cold", "sharp", "thread"] as const).some(
            (t) => result.replies[t] !== null
          ) && (
            <section>
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                Üretilen Yanıtlar
              </h3>
              <div className="flex flex-col gap-3">
                {(["cold", "sharp", "thread"] as const).map((tone) => {
                  const reply = result.replies[tone];
                  if (!reply) return null;
                  return <ReplyCard key={tone} tone={tone} reply={reply} />;
                })}
              </div>
              {(["cold", "sharp", "thread"] as const).every(
                (t) => result.replies[t] === null
              ) && (
                <p className="text-sm text-zinc-500 text-center py-4">
                  Tüm yanıtlar hukuki güvenlik filtresi tarafından engellendi.
                </p>
              )}
            </section>
          )}

          {/* Sources */}
          {result.sources.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                Kaynaklar
              </h3>
              <ul className="flex flex-col gap-1">
                {result.sources.map((url, i) => (
                  <li key={i}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2 break-all"
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
