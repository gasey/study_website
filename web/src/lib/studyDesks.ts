import type {AvatarLook} from './avatar'
import { deskRead } from "./desk";
export interface RoomSummary {
  id: string;
  name: string;
  goal: string;
  owner_id: string;
  members: number;
  version: number;
}
export interface DeskInvite {
  sender_id?: string;
  id: string;
  desk_id: string;
  name: string;
  sender: string;
  expires_at: string;
  recipient_id?: string;
  handle?: string;
}
export interface Member {
  avatar?:AvatarLook|null;
  user_id: string;
  handle: string;
  is_you: boolean;
  blocked: boolean;
  focusing: boolean;
  progress: { answered: number; correct: number } | null;
}
export interface RoomDetail {
  id: string;
  name: string;
  goal: string;
  owner_id: string;
  version: number;
  members: Member[];
  sharing: {
    progress: boolean;
    mistakes: boolean;
    times: boolean;
    muted: boolean;
  };
  invitations: DeskInvite[];
  joined_at: string;
}
export interface SharedItem {
  id: string;
  author_id: string;
  author: string;
  kind: "question" | "note" | "bookmark" | "mistake" | "update";
  title: string;
  body: string;
  question_id: string | null;
  question: string | null;
  answer_source: string | null;
  version: number;
  created_at: string;
}
export interface ChatMessage {
  id: number;
  author_id: string;
  author: string;
  body: string;
  version: number;
  created_at: string;
}
export interface FocusSession {
  id: string;
  state: "running" | "paused" | "completed" | "cancelled";
  duration_seconds: number;
  elapsed_seconds: number;
  elapsed?: number;
  resumed_at: string | null;
  version: number;
  created_at: string;
  desk_id: string | null;
}
export interface DeskOverview {
  stats: {
    answered: number;
    correct: number;
    unique_questions: number;
    week_answers: number;
  };
  questions: {
    id: string;
    question: string;
    type: string;
    answer_source: string;
    subject: string | null;
  }[];
  subjects: { subject: string; answered: number; correct: number }[];
  mistakes: { id: string; question: string; times_wrong: number }[];
  sessions: FocusSession[];
  server_time: string;
}
export type RoomList = {
  items: RoomSummary[];
  invitations: DeskInvite[];
  can_create: boolean;
  enabled: boolean;
};
export const getOverview = () => deskRead<DeskOverview>("/overview");
export const getRooms = () => deskRead<RoomList>("/rooms");
export const getRoom = (id: string) => deskRead<RoomDetail>("/rooms/" + id);
import { deviceId } from "./device";
import { getDeskSync } from "./desk";
import { reviewSession } from "./review";
export async function deskWrite<T = Record<string, unknown>>(
  path: string,
  body: unknown = {},
  key?: string,
): Promise<T> {
  const owner = getDeskSync().userId;
  const session = await reviewSession();
  if (session.user_id !== owner)
    throw new Error("Your signed-in account changed. Reload before saving.");
  const r = await fetch("/api/desk" + path, {
    method: "POST",
    credentials: "include",
    headers: {
      "content-type": "application/json",
      "x-device-id": deviceId(),
      "x-review-csrf": session.csrf,
      "x-desk-user": owner,
      ...(key ? { "idempotency-key": key } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const e = await r.json();
    throw new Error(
      typeof e.detail === "string"
        ? e.detail
        : Array.isArray(e.detail)
          ? e.detail.map((x: { msg: string }) => x.msg).join("; ")
          : "This desk change could not be saved",
    );
  }
  return r.json();
}
