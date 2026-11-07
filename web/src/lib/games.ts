import { deviceId } from "./device";
import { reviewRequest } from "./review";
import type { AvatarLook } from "./avatar";
export type GameMode = "gauntlet" | "speed" | "duel" | "party" | "cup" | "trail";
export interface GameQuestion {
  id: string;
  question: string;
  options: string[];
  direction: string | null;
  passage: string | null;
  question_markup: string | null;
  options_markup: (string | null)[] | null;
  figure_image_url: string | null;
  source_pdf_url: string | null;
  exam_name: string | null;
  year: number | null;
  qnum: string | null;
  page: number | null;
  answer_source: string;
  pillar?: string | null;
  pillar_label?: string | null;
  round_seconds?: number | null;
  courage_eligible?: boolean;
}
export interface Player {
  user_id: string;
  handle: string;
  avatar: AvatarLook | null;
  score?: number;
  correct?: number;
  wrong?: number;
  skipped?: number;
  excluded?: number;
  lives?: number;
  distance?: number;
  pace_bonus?: number;
  streak_bonus?: number;
  courage_bonus?: number;
  best_streak?: number;
  ready?: boolean;
  left_at: string | null;
  elapsed_ms?: number;
}
export interface GameRoom {
  id: string;
  owner_id: string;
  mode: GameMode;
  state: "waiting" | "running" | "finished" | "cancelled";
  selection?:{label:string;source_label:string;excluded_labels:string[];rules:{questions:number;round_seconds:number;total_seconds:number}}|null;
  context_hash?:string|null;
  round_seconds?:number;
  subject_id: string | null;
  capacity: number;
  join_code: string | null;
  cup_id: string | null;
  version: number;
  position: number;
  total: number;
  server_now: string;
  round_ends_at: string | null;
  deadline: string | null;
  viewer_id: string;
  players: Player[];
  question: GameQuestion | null;
  answered: boolean;
  chosen_index: number | null;
  review: (GameQuestion & {
    position: number;
    chosen_index: number | null;
    correct: boolean;
    excluded: boolean;
    answer_index: number;
    explanation: string | null;
  })[];
  review_available_at: string | null;
}
export interface GamesData {
  setup:GameSetupData;
  registered: boolean;
  active_mock: {id:string;collection_id:string;collection_title:string|null;seconds_remaining:number;resume_url:string}|null;
  active: { id: string; mode: GameMode; state: string } | null;
  history: {
    id: string;
    mode: GameMode;
    state: string;
    score: number;
    correct: number;
    wrong: number;
    excluded: number;
    distance: number;
    pace_bonus?: number;
    streak_bonus?: number;
    courage_bonus?: number;
    best_streak?: number;
    finished_at: string;
  }[];
  game_xp_today: number;
  shared_daily_xp_cap: number;
  subjects: { id: string; title: string; questions: number }[];
  cup: {
    id: string;
    opens_at: string;
    closes_at: string;
    entry_room: string | null;
    entries: number;
  };
  server_now: string;
}
export async function gameRead<T>(path: string): Promise<T> {
  const r = await fetch("/api/games" + path, {
    credentials: "include",
    cache: "no-store",
    headers: { "x-device-id": deviceId() },
  });
  if (!r.ok) {
    let message = "Game could not load";
    try {
      message = (await r.json()).detail || message;
    } catch {}
    throw Object.assign(new Error(message), { status: r.status });
  }
  return r.json();
}
export const gameWrite = <T>(path: string, body: unknown) =>
  reviewRequest<T>("/games" + path, body);
export const MODE_NAMES: Record<GameMode, string> = {
  trail: "Topic Trail",
  gauntlet: "Gauntlet Run",
  speed: "Speed round",
  duel: "Duel",
  party: "Multiplayer room",
  cup: "Weekly cup",
};

export interface FoundationPreset {
  id: string;
  title: string;
  badge: string;
  subtitle: string;
  quotas: { gk_gs?: number; english?: number; everyday_math?: number };
  math_round_seconds: number;
  courage_pillar: string | null;
  available: number;
}
export interface GameSelection {
  kind: 'mixed' | 'area' | 'exam' | 'foundation';
  area_id?: string | null;
  collection_id?: string | null;
  section?: string | null;
  preset_id?: string | null;
  excluded_areas: string[];
}
export interface GameSetupData {
  areas: { id: string; title: string; questions: number }[];
  exams: { id: string; title: string; saved: boolean }[];
  suggestions: { area_id: string; title: string; reason: string; evidence_count: number }[];
  foundation_presets?: FoundationPreset[];
  pillar_counts?: Record<string, number>;
  saved_selection: GameSelection | null;
  source_label: string;
  mixed_available: number;
}
export interface GamePreview {
  context_hash: string;
  public: {
    label: string;
    source_label: string;
    included_subjects: { title: string; questions: number }[];
    pillar_breakdown?: { pillar: string; title: string; required: number; available: number }[];
    math_round_seconds?: number;
    courage_pillar?: string | null;
    rules: { questions: number; round_seconds: number; total_seconds: number; scoring: string };
    excluded_labels: string[];
    selector: GameSelection;
  };
  available: number;
  required: number;
  can_start: boolean;
  message: string;
}
export interface JoinPreview {mode:GameMode;players:number;capacity:number;context_hash:string|null;label:string;source_label:string;questions:number;round_seconds:number;excluded_labels:string[]}
export interface CompetitiveLeaderboardItem {
  handle: string;
  avatar: AvatarLook | null;
  stream_cohort: string | null;
  streak: number;
  score: number;
  correct?: number;
  best_streak?: number;
  courage_bonus?: number;
  pace_bonus?: number;
  rank: number;
  is_you: boolean;
  league?: { id: string; name: string };
}
export interface CompetitiveLeaderboardResponse {
  track: string;
  period: string;
  cohort: string;
  items: CompetitiveLeaderboardItem[];
  has_more: boolean;
}

// Read-only preview accepts guests; contribution-session CSRF is only for writes.
export async function gamePreview(mode:GameMode,selection:GameSelection):Promise<GamePreview> {
 const response=await fetch('/api/games/preview',{method:'POST',credentials:'include',cache:'no-store',headers:{'content-type':'application/json','x-device-id':deviceId()},body:JSON.stringify({mode,selection})});
 if(!response.ok){let message='Game preview could not load';try{const e=await response.json();message=typeof e.detail==='string'?e.detail:message}catch{}throw new Error(message)}
 return response.json();
}
