import { deviceId } from "./device";
import { reviewSession } from "./review";
import { scopedApiPath } from "./examScope";
export interface VocabularyOverview {
  eligible: number;
  started: number;
  due: number;
  retaining: number;
  graded: number;
  correct: number;
  next_due: string | null;
  new_daily_target: number;
}
export interface VocabularyCard {
  id: string;
  question_id: string;
  exam_scope: string;
  expires_at: string;
  stage: number;
  seen: number;
  question: {
    question: string;
    question_markup: string | null;
    direction: string | null;
    passage: string | null;
    options: string[];
    options_markup: (string | null)[] | null;
    figure_image_url: string | null;
    source_pdf_url: string | null;
    page: number | null;
    answer_source: string;
  };
}
export interface VocabularyResult {
  correct: boolean | null;
  outcome: "correct" | "wrong" | "reveal" | "defer";
  answer_text: string | null;
  explanation: string | null;
  next_due: string;
  stage: number;
  message: string;
}
export async function vocabularyRequest<T>(
  path: string,
  user: string,
  body?: unknown,
): Promise<T> {
  const session = await reviewSession();
  if (session.user_id !== user)
    throw new Error("Your account changed. Reload before continuing.");
  const r = await fetch("/api" + scopedApiPath("/vocabulary" + path), {
    method: body === undefined ? "GET" : "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      "x-device-id": deviceId(),
      "x-vocabulary-user": user,
      ...(body === undefined ? {} : { "x-review-csrf": session.csrf }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(
      typeof e.detail === "string"
        ? e.detail
        : "The review could not be saved. Please retry.",
    );
  }
  return r.json();
}
