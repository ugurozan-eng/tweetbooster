/**
 * TwitBoost — API Client
 * ======================
 * Single source of truth for all backend communication.
 * Never import fetch or call NEXT_PUBLIC_API_URL directly from components.
 *
 * Base URL: process.env.NEXT_PUBLIC_API_URL (falls back to localhost:8000)
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PersonResult {
  name: string;
  handle: string;
  topic: string;
  confidence: string;
}

export interface Contradiction {
  statement_a: string;
  statement_b: string;
  date_a: string;
  date_b: string;
  source_url: string;
  confidence: string;
  summary: string;
}

export interface ReplyContent {
  tweet_text: string;
  thread: string[];
  evidence_note: string;
  disclaimer: string;
}

export interface Replies {
  cold: ReplyContent | null;
  sharp: ReplyContent | null;
  thread: ReplyContent | null;
}

export interface AnalysisResult {
  status: string;
  person_name: string;
  contradictions: Contradiction[];
  replies: Replies;
  sources: string[];
}

export interface ScoredTweet {
  url: string;
  text: string;
  score: number;
  reason: string;
}

export interface TrendingResult {
  niche_id: string;
  tweets: ScoredTweet[];
}

export interface NicheReply {
  text: string;
  hook_type: string;
}

export interface ReplyResult {
  niche_id: string;
  replies: NicheReply[];
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// ---------------------------------------------------------------------------
// Internal fetch helper
// ---------------------------------------------------------------------------

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `İstek başarısız oldu (HTTP ${res.status})`;
    try {
      const json: unknown = await res.json();
      if (
        typeof json === "object" &&
        json !== null &&
        "detail" in json &&
        typeof (json as { detail: unknown }).detail === "string"
      ) {
        detail = (json as { detail: string }).detail;
      }
    } catch {
      // Use default message
    }
    throw new ApiError(detail, res.status);
  }

  const data: unknown = await res.json();
  return data as T;
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/**
 * Identify the person mentioned in a tweet.
 * (Sprint 1.2 — used in research flow)
 */
export async function identifyPerson(
  tweetText: string
): Promise<PersonResult> {
  return apiFetch<PersonResult>("/api/research/identify", {
    tweet_text: tweetText,
  });
}

/**
 * Run full opposition analysis: identify → research → analyse → generate replies.
 * @param tones  Subset of ["cold", "sharp", "thread"]. Defaults to all three.
 */
export async function runOppositionAnalysis(
  tweetText: string,
  tones: string[]
): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>("/api/opposition/analyze", {
    tweet_text: tweetText,
    tones,
  });
}

/**
 * Fetch and score trending tweet candidates for a niche.
 * @param nicheId  One of: food, football, economy, politics
 * @param hours    Recency window hint (1–24)
 */
export async function getNicheTrending(
  nicheId: string,
  hours: number
): Promise<TrendingResult> {
  return apiFetch<TrendingResult>("/api/niche/trending", {
    niche_id: nicheId,
    hours,
  });
}

/**
 * Generate engagement replies for a tweet in a given niche.
 * @param tweetText  The tweet to reply to
 * @param nicheId    One of: food, football, economy, politics
 */
export async function generateNicheReply(
  tweetText: string,
  nicheId: string
): Promise<ReplyResult> {
  return apiFetch<ReplyResult>("/api/niche/reply", {
    tweet_text: tweetText,
    niche_id: nicheId,
  });
}
