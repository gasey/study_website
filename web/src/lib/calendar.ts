import { deviceId } from "./device";
import { reviewRequest } from "./review";
export const EVENT_KINDS = {
  notification: "Notification",
  deadline: "Last date",
  admit_card: "Admit card",
  exam: "Exam",
  answer_key: "Answer key",
  result: "Result",
} as const;
export type EventKind = keyof typeof EVENT_KINDS;
export interface CalendarEvent {
  id: string;
  collection_id: string | null;
  exam_title: string | null;
  title: string;
  kind: EventKind;
  starts_on: string | null;
  ends_on: string | null;
  summary: string;
  source_url: string;
  source_reference: string;
  verification_note: string;
  verified_on: string;
  version: number;
  published_at: string | null;
  updated_at: string;
  state: "draft" | "published" | "archived";
}
export interface CalendarPersonal {
  registered: boolean;
  following: string[];
  saved: string[];
  reminders: boolean;
  upcoming: CalendarEvent | null;
}
export async function calendarRead<T>(path: string): Promise<T> {
  const r = await fetch("/api" + path, {
    credentials: "include",
    headers: { "x-device-id": deviceId() },
  });
  if (!r.ok) {
    let m = "Calendar could not load";
    try {
      m = (await r.json()).detail || m;
    } catch {}
    throw new Error(m);
  }
  return r.json();
}
export const calendarPersonal = () =>
  calendarRead<CalendarPersonal>("/me/calendar");
export const calendarChange = (
  kind: "reminders" | "follow" | "save",
  body: unknown,
) => reviewRequest("/me/calendar/" + kind, body);
export const indiaToday = () => {
  const p = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const get = (type: string) => p.find((x) => x.type === type)!.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
};
export const dayNumber = (s: string) => Date.parse(s + "T00:00:00Z") / 86400000;
export const dateLabel = (s: string) =>
  new Date(s + "T12:00:00Z").toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
const addDay = (s: string) =>
  new Date((dayNumber(s) + 1) * 86400000).toISOString().slice(0, 10);
const icsText = (s: string) =>
  s
    .replace(/\\/g, "\\\\")
    .replace(/\r?\n/g, "\\n")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,");
/** RFC5545 all-day intervals use an exclusive end; lines fold at UTF-8 octets. */
export function exportCalendar(events: CalendarEvent[]) {
  const dated = events.filter((e) => e.starts_on && e.state === "published");
  if (!dated.length) return;
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//India Study Map//Exam Calendar//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    ...dated.flatMap((e) => [
      "BEGIN:VEVENT",
      `UID:${e.id}@study.hawayu.in`,
      `SEQUENCE:${e.version}`,
      `DTSTAMP:${new Date()
        .toISOString()
        .replace(/[-:]/g, "")
        .replace(/\.\d{3}/, "")}`,
      `DTSTART;VALUE=DATE:${e.starts_on!.replace(/-/g, "")}`,
      `DTEND;VALUE=DATE:${addDay(e.ends_on || e.starts_on!).replace(/-/g, "")}`,
      `SUMMARY:${icsText(e.title)}`,
      `DESCRIPTION:${icsText(e.summary + "\nOfficial source: " + e.source_url + "\n" + e.source_reference + "\nDate only; confirm exact reporting/closing time in the notice.")}`,
      `URL:${e.source_url}`,
      "END:VEVENT",
    ]),
    "END:VCALENDAR",
  ];
  const enc = new TextEncoder();
  const folded =
    lines
      .map((line) => {
        let part = "",
          bytes = 0,
          out = "";
        for (const c of line) {
          const n = enc.encode(c).length;
          if (bytes + n > 75) {
            out += part + "\r\n";
            part = " ";
            bytes = 1;
          }
          part += c;
          bytes += n;
        }
        return out + part;
      })
      .join("\r\n") + "\r\n";
  const url = URL.createObjectURL(
    new Blob([folded], { type: "text/calendar;charset=utf-8" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "india-study-map-exams.ics";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function googleCalendar(e: CalendarEvent) {
  if (!e.starts_on) return "";
  return (
    "https://calendar.google.com/calendar/render?" +
    new URLSearchParams({
      action: "TEMPLATE",
      text: e.title,
      dates:
        e.starts_on.replace(/-/g, "") +
        "/" +
        addDay(e.ends_on || e.starts_on).replace(/-/g, ""),
      details:
        e.summary +
        "\nOfficial source: " +
        e.source_url +
        "\nConfirm exact times in the official notice.",
      ctz: "Asia/Kolkata",
    })
  );
}
