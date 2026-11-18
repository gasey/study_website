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
export interface VocabularyDecks {
  curated_items?:CuratedDeck[];curated_known_total?:number;curated_practice_enabled?:boolean;
  items: {id:string;label:string;source:'bank';eligible:number;started:number;attempted:number;correct_latest:number;due:number;state:string;rusty:boolean;last_activity:string|null}[];
  basis:string;
  curated_available:boolean;
  curated_message:string;
}
export interface VocabularyCard {
  id: string;
  question_id: string;
  exam_scope: string;
  expires_at: string;
  started?: boolean;
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
  next_due: string | null;
  graduated?: boolean;
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

export type CuratedMode='recognition'|'cloze'|'mizo-to-english'|'english-to-mizo'
export interface CuratedDeck{id:string;label:string;source:'curated';eligible_cards:number;eligible_words:number;started:number;due:number;attempted:number;correct_latest:number;known:number;state:string;rusty:boolean;last_activity:string|null;modes:CuratedMode[];url:string}
export interface CuratedCard{id:string;card_id:string;deck_id:string;deck_title:string;mode:CuratedMode;prompt:string;options:string[];expires_at:string;stage:number;seen:number;source:'reviewed-editorial'}
export interface CuratedResult{answer_index?:number|null;correct:boolean|null;outcome:string;answer_text:string|null;card:import('./materials').CuratedWordCard|null;next_due:string|null;graduated:boolean;stage:number;source:'reviewed-editorial';xp:0;points:0}
