import { deviceId } from "./device";
import { reviewSession } from "./review";
export const categories = [
  "discussions",
  "desks",
  "calendar",
  "contributions",
  "materials",
  "scores",
  "system",
] as const;
export type Category = (typeof categories)[number];
export const categoryLabels: Record<Category, string> = {
  discussions: "Discussions",
  desks: "Study desks",
  calendar: "Exam notices",
  contributions: "Contributions",
  materials: "Content reviews",
  scores: "Score updates",
  system: "Account & system",
};
export interface Notice {
  id: number;
  message: string;
  category: Category;
  silent: boolean;
  read_at: string | null;
  created_at: string;
  calendar_event_id: string | null;
  study_desk_id: string | null;
  study_invite_id: string | null;
  discussion_post_id: number | null;
  discussion_question_id: string | null;
  contribution_id: string | null;
  material_id: string | null;
  mock_id: string | null;
  corrected_question_id?:string|null;
  question_change_id?:number|null;
}
export interface NoticePage {
  items: Notice[];
  next_cursor: number | null;
  snapshot_id: number;
  unread: number;
  unread_by_category: Partial<Record<Category, number>>;
}
export interface InboxThread {
  id: string;
  name: string;
  goal: string;
  last_message: string | null;
  author: string | null;
  last_at: string | null;
  unread: number;
}
export async function inboxRequest<T>(
  path: string,
  user: string,
  body?: unknown,
): Promise<T> {
  const session = await reviewSession();
  if (session.user_id !== user)
    throw new Error(
      "Your signed-in account changed. Reload before continuing.",
    );
  const response = await fetch("/api/inbox" + path, {
    method: body === undefined ? "GET" : "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      "x-device-id": deviceId(),
      "x-inbox-user": user,
      ...(body === undefined ? {} : { "x-review-csrf": session.csrf }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The Inbox request could not be completed. Please retry.",
    );
  }
  return response.json();
}
export function noticeLink(n: Notice): { url: string; label: string } | null {
  if(n.corrected_question_id)return {url:'/bank/'+encodeURIComponent(n.corrected_question_id)+'?exam_scope=all'+(n.question_change_id?'&update='+n.question_change_id:''),label:'Review question update'};
  if (n.study_desk_id)
    return {
      url: n.study_invite_id
        ? "/desk"
        : "/inbox?desk=" + encodeURIComponent(n.study_desk_id),
      label: n.study_invite_id ? "View invitation" : "Open desk messages",
    };
  if (n.calendar_event_id)
    return {
      url: "/calendar?event=" + encodeURIComponent(n.calendar_event_id),
      label: "Open notice",
    };
  if (n.discussion_question_id)
    return {
      url:
        "/bank/" +
        encodeURIComponent(n.discussion_question_id) +
        "?exam_scope=all" +
        (n.discussion_post_id ? "&post=" + n.discussion_post_id : "") +
        "#discussion",
      label: "Open discussion",
    };
  if (n.contribution_id)
    return {
      url: "/contributions/" + encodeURIComponent(n.contribution_id),
      label: "Open contribution",
    };
  if (n.material_id)
    return {
      url: "/studio/" + encodeURIComponent(n.material_id) + "#review-feedback",
      label: "Open review",
    };
  if (n.mock_id)
    return {
      url: "/results/" + encodeURIComponent(n.mock_id),
      label: "Open result",
    };
  return null;
}
