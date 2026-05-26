"use client";

import { useState } from "react";
import {
  runOppositionAnalysis,
  AnalysisResult,
  Contradiction,
  ReplyContent,
  ApiError,
} from "@/lib/api";

// ── Constants ──────────────────────────────────────────────────────────────

const TONE_KEYS = ["cold", "sharp", "thread"] as const;
type ToneKey = (typeof TONE_KEYS)[number];

const TONE_LABELS: Record<ToneKey, string> = {
  cold:   "SOĞUK",
  sharp:  "KESKİN",
  thread: "THREAD",
};

const TONE_DESC: Record<ToneKey, string> = {
  cold:   "Nötr, gazetecilik",
  sharp:  "İğneleyici, dokunaklı",
  thread: "Çok tweetlik dizi",
};

const CONFIDENCE_LABEL: Record<string, string> = {
  high:   "YÜKSEK",
  medium: "ORTA",
  low:    "DÜŞÜK",
};

// ── Sub-components ──────────────────────────────────────────────────────────

/** Horizontal scan-line loading state */
function LoadingBar() {
  return (
    <div className="scanning h-px w-full my-6" style={{ background: "var(--border)" }} />
  );
}

/** Press ID badge for the identified person */
function PersonBadge({ result }: { result: AnalysisResult }) {
  const conf = result.contradictions[0]?.confidence ?? "low";
  const badgeClass =
    conf === "high" ? "badge-high" : conf === "medium" ? "badge-medium" : "badge-low";

  return (
    <div
      className="evidence-card flagged stamp-in p-5 mb-6"
    >
      <p className="eyebrow mb-3">BASIN KİMLİĞİ</p>

      <div className="flex items-end justify-between gap-4">
        <div>
          <h2
            className="font-display leading-none mb-1"
            style={{ fontSize: "clamp(2rem, 5vw, 3.25rem)", color: "var(--paper)" }}
          >
            {result.person_name}
          </h2>
          {result.contradictions.length > 0 && (
            <p
              className="font-code"
              style={{ color: "var(--muted)", fontSize: "0.7rem", letterSpacing: "0.06em" }}
            >
              {result.contradictions.length} ÇELİŞKİ TESPİT EDİLDİ
            </p>
          )}
        </div>
        <span className={`badge ${badgeClass} shrink-0`}>
          {CONFIDENCE_LABEL[conf] ?? conf} GÜVEN
        </span>
      </div>
    </div>
  );
}

/** Single contradiction clipping card */
function ContradictionCard({ c, index }: { c: Contradiction; index: number }) {
  const conf = c.confidence;
  const badgeClass =
    conf === "high" ? "badge-high" : conf === "medium" ? "badge-medium" : "badge-low";

  return (
    <div
      className="evidence-card stamp-in mb-4"
      style={{ animationDelay: `${index * 0.06}s` }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <p className="eyebrow">ÇELİŞKİ #{index + 1}</p>
        <span className={`badge ${badgeClass}`}>
          {CONFIDENCE_LABEL[conf] ?? conf}
        </span>
      </div>

      {/* Summary */}
      <p
        className="font-code px-4 py-3"
        style={{ color: "var(--paper)", fontSize: "0.78rem", lineHeight: 1.7, borderBottom: "1px solid var(--border)" }}
      >
        {c.summary}
      </p>

      {/* Two-column statements */}
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr]">
        {/* Old statement */}
        <div className="p-4" style={{ borderRight: "1px solid var(--border)" }}>
          <p className="datestamp mb-2">ESKİ BEYAN{c.date_a ? ` · ${c.date_a}` : ""}</p>
          <p
            className="font-code"
            style={{ color: "var(--paper)", fontSize: "0.78rem", lineHeight: 1.7 }}
          >
            &ldquo;{c.statement_a}&rdquo;
          </p>
        </div>

        {/* Divider symbol */}
        <div
          className="flex items-center justify-center px-3 py-4 sm:py-0"
          style={{ borderBottom: "1px solid var(--border)", fontSize: "1.5rem", color: "var(--accent)", fontWeight: 700 }}
        >
          ≠
        </div>

        {/* New statement */}
        <div className="p-4">
          <p className="datestamp mb-2">YENİ BEYAN{c.date_b ? ` · ${c.date_b}` : ""}</p>
          <p
            className="font-code"
            style={{ color: "var(--paper)", fontSize: "0.78rem", lineHeight: 1.7 }}
          >
            &ldquo;{c.statement_b}&rdquo;
          </p>
        </div>
      </div>

      {/* Source footnote */}
      {c.source_url && (
        <div
          className="px-4 py-2"
          style={{ borderTop: "1px solid var(--border)", background: "var(--surface-2)" }}
        >
          <span className="eyebrow" style={{ marginRight: "0.5rem" }}>KAYNAK:</span>
          <a
            href={c.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="footnote-link"
          >
            {c.source_url}
          </a>
        </div>
      )}
    </div>
  );
}

/** Single reply card */
function ReplyCard({ tone, reply }: { tone: ToneKey; reply: ReplyContent }) {
  const [copied, setCopied] = useState(false);

  const textToCopy =
    tone === "thread" && reply.thread.length > 0
      ? reply.thread.join("\n\n")
      : reply.tweet_text;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
    } catch {
      const el = document.createElement("textarea");
      el.value = textToCopy;
      Object.assign(el.style, { position: "absolute", left: "-9999px" });
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="evidence-card stamp-in flex flex-col">
      {/* Tone header */}
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <p
          className="font-display"
          style={{ fontSize: "1.25rem", color: "var(--accent)", lineHeight: 1 }}
        >
          {TONE_LABELS[tone]}
        </p>
        <p className="eyebrow">{TONE_DESC[tone]}</p>
      </div>

      {/* Reply content */}
      <div className="flex-1 p-4">
        {tone === "thread" && reply.thread.length > 0 ? (
          <ol className="flex flex-col gap-3">
            {reply.thread.map((tweet, i) => (
              <li
                key={i}
                className="font-code"
                style={{
                  borderLeft: "2px solid var(--accent)",
                  paddingLeft: "0.75rem",
                  fontSize: "0.82rem",
                  lineHeight: 1.7,
                  color: "var(--paper)",
                }}
              >
                {tweet}
              </li>
            ))}
          </ol>
        ) : (
          <p
            className="font-code"
            style={{ fontSize: "0.9rem", lineHeight: 1.8, color: "var(--paper)" }}
          >
            {reply.tweet_text}
          </p>
        )}
      </div>

      {/* Disclaimer + copy */}
      <div
        className="flex items-end justify-between gap-3 px-4 py-3"
        style={{ borderTop: "1px solid var(--border)", background: "var(--surface-2)" }}
      >
        {reply.disclaimer && (
          <p className="datestamp flex-1">{reply.disclaimer}</p>
        )}
        <button onClick={copy} className={`btn-ghost shrink-0 ${copied ? "copied-flash" : ""}`}>
          {copied ? "Kopyalandı ✓" : "Kopyala"}
        </button>
      </div>
    </div>
  );
}

/** Source list — footnote style */
function SourcesList({ sources }: { sources: string[] }) {
  if (!sources.length) return null;
  return (
    <div className="evidence-card stamp-in">
      <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
        <p className="eyebrow">KAYNAKLAR</p>
      </div>
      <ol className="px-4 py-3 flex flex-col gap-1.5">
        {sources.map((url, i) => (
          <li key={i} className="flex items-baseline gap-2">
            <span className="datestamp shrink-0">[{i + 1}]</span>
            <a href={url} target="_blank" rel="noopener noreferrer" className="footnote-link break-all">
              {url}
            </a>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

type Tones = Record<ToneKey, boolean>;

export default function OppositionPage() {
  const [tweetText, setTweetText] = useState("");
  const [tones, setTones] = useState<Tones>({ cold: true, sharp: true, thread: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isWarning, setIsWarning] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const selectedTones = TONE_KEYS.filter((k) => tones[k]);
  const canSubmit = tweetText.trim().length > 0 && selectedTones.length > 0 && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setIsWarning(false);
    setResult(null);

    try {
      const data = await runOppositionAnalysis(tweetText, selectedTones);
      setResult(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setIsWarning(err.status === 422);
      } else {
        setError("Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.");
        setIsWarning(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleTone = (key: ToneKey) =>
    setTones((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">

      {/* ── Page header ────────────────────────────────────────────── */}
      <div className="mb-8 stagger-in">
        <p className="eyebrow mb-2">ARAŞTIRMA &amp; YANITLAMA</p>
        <h1
          className="font-display leading-none"
          style={{ fontSize: "clamp(2.5rem, 7vw, 5rem)", color: "var(--paper)" }}
        >
          MUHALİF MOD
        </h1>
        <div className="rule-red mt-3" />
      </div>

      {/* ── Two-column layout ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-0">

        {/* ── LEFT: Input panel ──────────────────────────────────── */}
        <div
          className="lg:border-r py-0 lg:pr-6"
          style={{ borderColor: "var(--border)" }}
        >
          <form onSubmit={handleSubmit} className="flex flex-col gap-5 stagger-in">

            {/* Tweet textarea */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="tweet-input"
                className="eyebrow"
              >
                Tweet metni
              </label>
              <textarea
                id="tweet-input"
                rows={5}
                value={tweetText}
                onChange={(e) => setTweetText(e.target.value)}
                placeholder="Tweet metnini buraya yapıştırın…"
                className="field"
                style={{ minHeight: "120px" }}
              />
            </div>

            {/* Tone selector */}
            <div className="flex flex-col gap-2">
              <p className="eyebrow">Yanıt tonu</p>
              <div className="flex flex-col gap-1">
                {TONE_KEYS.map((key) => (
                  <label
                    key={key}
                    className="flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors"
                    style={{
                      border: "1px solid",
                      borderColor: tones[key] ? "var(--accent)" : "var(--border)",
                      background: tones[key] ? "rgba(232,25,44,0.06)" : "var(--surface)",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={tones[key]}
                      onChange={() => toggleTone(key)}
                      className="shrink-0"
                    />
                    <span className="flex-1">
                      <span
                        className="font-display block"
                        style={{
                          fontSize: "1.1rem",
                          lineHeight: 1,
                          color: tones[key] ? "var(--accent)" : "var(--paper)",
                        }}
                      >
                        {TONE_LABELS[key]}
                      </span>
                      <span className="datestamp">{TONE_DESC[key]}</span>
                    </span>
                  </label>
                ))}
              </div>
              {selectedTones.length === 0 && (
                <p className="datestamp" style={{ color: "var(--accent)" }}>
                  En az bir ton seçmelisiniz.
                </p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="btn-primary w-full"
            >
              {loading ? (
                <span className="cursor-blink">Araştırılıyor</span>
              ) : (
                "ANALİZ ET →"
              )}
            </button>

          </form>
        </div>

        {/* ── RIGHT: Results panel ───────────────────────────────── */}
        <div className="lg:pl-6 pt-8 lg:pt-0">

          {/* Loading scan */}
          {loading && (
            <div>
              <p
                className="eyebrow mb-3 cursor-blink"
                style={{ color: "var(--accent)" }}
              >
                Araştırılıyor
              </p>
              <LoadingBar />
              <LoadingBar />
              <LoadingBar />
            </div>
          )}

          {/* Error / Warning banner */}
          {error && !loading && (
            <div
              className="stamp-in mb-6 px-4 py-3 flex items-start gap-3"
              style={{
                border: `1px solid ${isWarning ? "rgba(245,158,11,0.4)" : "rgba(239,68,68,0.4)"}`,
                background: isWarning ? "rgba(245,158,11,0.06)" : "rgba(239,68,68,0.06)",
              }}
            >
              <span style={{ color: isWarning ? "#fbbf24" : "#fca5a5", marginTop: "1px" }}>
                {isWarning ? "⚠" : "✕"}
              </span>
              <p
                className="font-code"
                style={{
                  color: isWarning ? "#fbbf24" : "#fca5a5",
                  fontSize: "0.78rem",
                  lineHeight: 1.6,
                }}
              >
                {error}
              </p>
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && !result && (
            <div
              className="flex items-center justify-center"
              style={{ minHeight: "200px" }}
            >
              <p
                className="font-code cursor-blink"
                style={{ color: "var(--muted)", fontSize: "0.78rem", letterSpacing: "0.06em" }}
              >
                ANALİZ BEKLENİYOR
              </p>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <div className="flex flex-col gap-8">

              {/* Person badge */}
              <PersonBadge result={result} />

              {/* No contradictions */}
              {result.status === "no_contradictions_found" && (
                <div
                  className="evidence-card stamp-in px-5 py-6 text-center"
                >
                  <p className="font-display" style={{ fontSize: "1.5rem", color: "var(--muted)" }}>
                    ÇELİŞKİ BULUNAMADI
                  </p>
                  <p className="font-code mt-2" style={{ color: "var(--muted)", fontSize: "0.73rem" }}>
                    Bu tweet için geçmişte tutarsız bir beyan tespit edilemedi.
                  </p>
                </div>
              )}

              {/* Contradictions */}
              {result.contradictions.length > 0 && (
                <section>
                  <p className="eyebrow mb-4">
                    TESPİT EDİLEN ÇELİŞKİLER — {result.contradictions.length} KAYIT
                  </p>
                  {result.contradictions.map((c, i) => (
                    <ContradictionCard key={i} c={c} index={i} />
                  ))}
                </section>
              )}

              {/* Replies */}
              {TONE_KEYS.some((t) => result.replies[t] !== null) && (
                <section>
                  <p className="eyebrow mb-4">ÜRETİLEN YANITLAR</p>
                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-0">
                    {TONE_KEYS.map((tone, i) => {
                      const reply = result.replies[tone];
                      if (!reply) return null;
                      return (
                        <div
                          key={tone}
                          style={{
                            borderRight: i < TONE_KEYS.length - 1 ? "1px solid var(--border)" : undefined,
                          }}
                        >
                          <ReplyCard tone={tone} reply={reply} />
                        </div>
                      );
                    })}
                  </div>
                  {TONE_KEYS.every((t) => result.replies[t] === null) && (
                    <p
                      className="font-code text-center py-6"
                      style={{ color: "var(--muted)", fontSize: "0.73rem" }}
                    >
                      Tüm yanıtlar hukuki güvenlik filtresi tarafından engellendi.
                    </p>
                  )}
                </section>
              )}

              {/* Sources */}
              <SourcesList sources={result.sources} />

            </div>
          )}

        </div>
      </div>
    </div>
  );
}
