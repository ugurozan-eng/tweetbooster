"use client";

import { useState, useCallback } from "react";
import {
  runOppositionAnalysis,
  AnalysisResult,
  Contradiction,
  ReplyContent,
  ApiError,
} from "@/lib/api";

// ── Constants ─────────────────────────────────────────────────────────────────

const TONES = [
  { id: "cold",   label: "SOĞUK"  },
  { id: "sharp",  label: "KESKİN" },
  { id: "thread", label: "THREAD" },
] as const;

type ToneId = (typeof TONES)[number]["id"];

const TONE_HEADER: Record<ToneId, string> = {
  cold:   "SOĞUK",
  sharp:  "KESKİN",
  thread: "THREAD",
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

// ── Person press-badge ────────────────────────────────────────────────────────

function PersonBadge({ result }: { result: AnalysisResult }) {
  const noContradictions = result.status === "no_contradictions_found";
  return (
    <div className="evidence-card flagged stamp-in p-5">
      <p className="eyebrow mb-3">BASIN KİMLİĞİ</p>
      <h2
        className="font-display leading-none mb-1"
        style={{ fontSize: "clamp(2rem, 5vw, 3rem)", color: "var(--paper)" }}
      >
        {result.person_name || "—"}
      </h2>
      <div className="flex items-center gap-2 mt-3">
        <span className="badge badge-high">TANIMLI</span>
        {noContradictions && (
          <span className="badge badge-medium">ÇELİŞKİ BULUNAMADI</span>
        )}
      </div>
    </div>
  );
}

// ── Contradiction card ────────────────────────────────────────────────────────

function ContradictionCard({
  c,
  index,
}: {
  c: Contradiction;
  index: number;
}) {
  const displayUrl = (() => {
    try {
      return new URL(c.source_url).hostname.replace("www.", "");
    } catch {
      return c.source_url.slice(0, 40);
    }
  })();

  return (
    <div className="evidence-card flagged stamp-in">
      {/* Summary */}
      <div
        className="px-4 pt-4 pb-3"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <p className="eyebrow mb-1">ÇELİŞKİ {index + 1}</p>
        <p
          className="font-code"
          style={{ fontSize: "0.78rem", color: "var(--paper)", lineHeight: 1.6 }}
        >
          {c.summary}
        </p>
      </div>

      {/* Side-by-side statements with ≠ divider */}
      <div
        className="grid items-start p-4 gap-3"
        style={{ gridTemplateColumns: "1fr auto 1fr" }}
      >
        {/* Old statement */}
        <div>
          <p className="datestamp mb-2">{c.date_a || "tarih belirsiz"}</p>
          <p
            className="font-code"
            style={{ fontSize: "0.75rem", color: "var(--muted)", lineHeight: 1.65 }}
          >
            &ldquo;{c.statement_a}&rdquo;
          </p>
        </div>

        {/* Divider */}
        <div className="flex items-center justify-center px-2 pt-5">
          <span
            className="font-display"
            style={{ fontSize: "2.25rem", color: "var(--accent)", lineHeight: 1 }}
          >
            ≠
          </span>
        </div>

        {/* New statement */}
        <div>
          <p className="datestamp mb-2">{c.date_b || "tarih belirsiz"}</p>
          <p
            className="font-code"
            style={{ fontSize: "0.75rem", color: "var(--paper)", lineHeight: 1.65 }}
          >
            &ldquo;{c.statement_b}&rdquo;
          </p>
        </div>
      </div>

      {/* Source footnote */}
      {c.source_url && (
        <div
          className="px-4 pb-3"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <p className="datestamp mt-2 mb-1">KAYNAK</p>
          <a
            href={c.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="footnote-link"
            title={c.source_url}
          >
            {displayUrl}
          </a>
        </div>
      )}
    </div>
  );
}

// ── Reply card ────────────────────────────────────────────────────────────────

function ReplyCard({ tone, reply }: { tone: ToneId; reply: ReplyContent }) {
  const textToCopy =
    reply.thread.length > 0 ? reply.thread.join("\n\n") : reply.tweet_text;

  return (
    <div className="evidence-card stamp-in flex flex-col">
      {/* Tone header */}
      <div
        className="px-4 py-3 flex items-center justify-between gap-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <h3
          className="font-display leading-none"
          style={{ fontSize: "1.5rem", color: "var(--accent)" }}
        >
          {TONE_HEADER[tone]}
        </h3>
        <CopyButton text={textToCopy} />
      </div>

      {/* Reply text */}
      <div className="px-4 py-4 flex-1">
        <p
          className="font-code"
          style={{ fontSize: "0.8125rem", color: "var(--paper)", lineHeight: 1.75 }}
        >
          {reply.tweet_text}
        </p>

        {/* Thread parts */}
        {reply.thread.length > 0 && (
          <div className="mt-3 flex flex-col gap-2">
            {reply.thread.map((t, i) => (
              <p
                key={i}
                className="font-code"
                style={{
                  fontSize: "0.78rem",
                  color: "var(--muted)",
                  lineHeight: 1.7,
                  paddingLeft: "0.75rem",
                  borderLeft: "1px solid var(--border)",
                }}
              >
                {t}
              </p>
            ))}
          </div>
        )}

        {/* Legal disclaimer */}
        {reply.disclaimer && (
          <p className="datestamp mt-3">{reply.disclaimer}</p>
        )}
      </div>
    </div>
  );
}

// ── Sources list ──────────────────────────────────────────────────────────────

function SourcesList({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="evidence-card stamp-in p-4">
      <p className="eyebrow mb-3">KAYNAKLAR</p>
      <ol className="flex flex-col gap-1.5">
        {sources.map((url, i) => {
          const host = (() => {
            try {
              return new URL(url).hostname.replace("www.", "");
            } catch {
              return url.slice(0, 50);
            }
          })();
          return (
            <li key={i} className="flex items-baseline gap-2">
              <span className="datestamp shrink-0">[{i + 1}]</span>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="footnote-link"
                title={url}
              >
                {host}
              </a>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

// ── Loading state ─────────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="flex flex-col gap-5 pt-8">
      <div className="scanning" />
      <p
        className="font-code cursor-blink"
        style={{ fontSize: "0.75rem", color: "var(--muted)", letterSpacing: "0.12em" }}
      >
        ARAŞTIRILIYOR
      </p>
      <div className="scanning" style={{ opacity: 0.5 }} />
      <div className="scanning" style={{ opacity: 0.3 }} />
    </div>
  );
}

// ── Page state type ───────────────────────────────────────────────────────────

type PageState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; message: string; isWarning: boolean }
  | { phase: "result"; data: AnalysisResult };

// ── Main page ─────────────────────────────────────────────────────────────────

export default function OppositionPage() {
  const [tweetText, setTweetText]           = useState("");
  const [twitterHandle, setTwitterHandle]   = useState("");
  const [selectedTones, setSelectedTones]   = useState<ToneId[]>(["cold", "sharp", "thread"]);
  const [pageState, setPageState]           = useState<PageState>({ phase: "idle" });

  const toggleTone = (id: ToneId) => {
    setSelectedTones((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    if (!tweetText.trim() || selectedTones.length === 0) return;
    setPageState({ phase: "loading" });
    try {
      const data = await runOppositionAnalysis(
        tweetText,
        selectedTones,
        twitterHandle || undefined
      );
      setPageState({ phase: "result", data });
    } catch (err) {
      if (err instanceof ApiError) {
        setPageState({
          phase: "error",
          message: err.message,
          isWarning: err.status === 422,
        });
      } else {
        setPageState({
          phase: "error",
          message: "Sunucuya bağlanılamadı. Backend servisinin çalıştığından emin olun.",
          isWarning: false,
        });
      }
    }
  };

  const isLoading = pageState.phase === "loading";

  return (
    <div className="min-h-[calc(100vh-48px)] max-w-6xl mx-auto">
      {/* ── Two-column grid with 1px separator ──────────────────── */}
      <div
        className="grid grid-cols-1 lg:grid-cols-[40%_1fr]"
        style={{ gap: "1px", background: "var(--border)", minHeight: "calc(100vh - 48px)" }}
      >

        {/* ══════ LEFT — Input ══════ */}
        <div
          className="flex flex-col gap-6 p-6"
          style={{ background: "var(--bg)" }}
        >
          {/* Heading */}
          <div>
            <p className="eyebrow mb-2">MOD 01 · Muhalif Analiz</p>
            <h1
              className="font-display leading-none"
              style={{ fontSize: "clamp(2.5rem, 6vw, 4rem)", color: "var(--paper)" }}
            >
              MUHALİF MOD
            </h1>
            <div className="rule-red mt-3" />
          </div>

          {/* Tweet textarea */}
          <div>
            <label htmlFor="tweet-input" className="eyebrow mb-2 block">
              TWEET METNİ
            </label>
            <textarea
              id="tweet-input"
              className="field"
              rows={6}
              value={tweetText}
              onChange={(e) => setTweetText(e.target.value)}
              placeholder="Tweet metnini buraya yapıştırın..."
              disabled={isLoading}
            />
          </div>

          {/* Twitter handle */}
          <div>
            <label htmlFor="handle-input" className="eyebrow mb-2 block">
              TWITTER KULLANICI ADI{" "}
              <span style={{ color: "var(--dim)" }}>(isteğe bağlı)</span>
            </label>
            <input
              id="handle-input"
              type="text"
              className="field"
              value={twitterHandle}
              onChange={(e) => setTwitterHandle(e.target.value)}
              placeholder="@kullaniciadi"
              disabled={isLoading}
            />
          </div>

          {/* Tone pills */}
          <div>
            <p className="eyebrow mb-2">YANIT TONU</p>
            <div className="flex flex-wrap gap-2">
              {TONES.map((t) => {
                const isActive = selectedTones.includes(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => toggleTone(t.id)}
                    disabled={isLoading}
                    aria-pressed={isActive}
                    style={{
                      display:        "inline-flex",
                      alignItems:     "center",
                      justifyContent: "center",
                      padding:        "0.35rem 0.875rem",
                      border:         `1px solid ${isActive ? "var(--accent)" : "var(--border)"}`,
                      background:     isActive ? "var(--accent)" : "transparent",
                      color:          isActive ? "#000" : "var(--muted)",
                      fontFamily:     "var(--font-ibm-mono), monospace",
                      fontSize:       "0.65rem",
                      letterSpacing:  "0.12em",
                      textTransform:  "uppercase",
                      cursor:         isLoading ? "not-allowed" : "pointer",
                      opacity:        isLoading ? 0.4 : 1,
                      transition:     "background 0.1s, color 0.1s, border-color 0.1s",
                      userSelect:     "none",
                    }}
                  >
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submit */}
          <button
            type="button"
            className="btn-primary w-full"
            onClick={handleSubmit}
            disabled={isLoading || !tweetText.trim() || selectedTones.length === 0}
          >
            {isLoading ? (
              <span className="cursor-blink">ANALİZ EDİLİYOR</span>
            ) : (
              "ANALİZ ET →"
            )}
          </button>
        </div>

        {/* ══════ RIGHT — Results ══════ */}
        <div
          className="p-6 flex flex-col gap-5"
          style={{ background: "var(--bg)" }}
        >
          {/* Idle */}
          {pageState.phase === "idle" && (
            <div className="flex items-center justify-center h-full min-h-[300px]">
              <p
                className="font-code"
                style={{ color: "var(--paper)", opacity: 0.3, fontSize: "0.8rem", letterSpacing: "0.12em" }}
              >
                // analiz bekleniyor
              </p>
            </div>
          )}

          {/* Loading */}
          {pageState.phase === "loading" && <LoadingState />}

          {/* Error / warning */}
          {pageState.phase === "error" && (
            <div className={pageState.isWarning ? "warn-box" : "error-box"}>
              {pageState.message}
            </div>
          )}

          {/* Results */}
          {pageState.phase === "result" && (
            <>
              <PersonBadge result={pageState.data} />

              {pageState.data.contradictions.length > 0 && (
                <div className="flex flex-col gap-3">
                  <p className="eyebrow">
                    ÇELİŞKİLER — {pageState.data.contradictions.length} BULGU
                  </p>
                  {pageState.data.contradictions.map((c, i) => (
                    <ContradictionCard key={i} c={c} index={i} />
                  ))}
                </div>
              )}

              {(["cold", "sharp", "thread"] as ToneId[]).some(
                (t) => pageState.data.replies[t] != null
              ) && (
                <div className="flex flex-col gap-3">
                  <p className="eyebrow">YANITLAR</p>
                  {(["cold", "sharp", "thread"] as ToneId[]).map((tone) => {
                    const reply = pageState.data.replies[tone];
                    return reply ? (
                      <ReplyCard key={tone} tone={tone} reply={reply} />
                    ) : null;
                  })}
                </div>
              )}

              {pageState.data.sources.length > 0 && (
                <SourcesList sources={pageState.data.sources} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
