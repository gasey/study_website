import { useSyncExternalStore } from "react";
// Mirrors api/app/exam_scope.py KNOWN_SCOPES (§VIII.3.1, phase V.19). A new exam
// body adds its id in both places; api/tests/test_exam_scope_drift.py fails if the
// two lists disagree. The type is open so no new code assumes exactly two scopes.
export const KNOWN_EXAM_SCOPES = [
  "all",
  "mizoram-recruitment",
  "outside-mizoram",
] as const;
export type ExamScope = (typeof KNOWN_EXAM_SCOPES)[number];
function isExamScope(value: string | null): value is ExamScope {
  return !!value && (KNOWN_EXAM_SCOPES as readonly string[]).includes(value);
}
const KEY = "ism-exam-scope";
function readExamScope(): ExamScope {
  const explicit = new URLSearchParams(window.location?.search || "").get(
    "exam_scope",
  );
  if (isExamScope(explicit)) return explicit;
  try {
    const stored = localStorage.getItem(KEY);
    return isExamScope(stored) ? stored : "mizoram-recruitment";
  } catch {
    return "mizoram-recruitment";
  }
}
// Other tabs do not silently change the active pool. Explicit navigation and
// focus changes update the store; keyed learner routes discard stale requests.
let documentScope = readExamScope();
const listeners = new Set<() => void>();
const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};
export function useExamScope() {
  return useSyncExternalStore(subscribe, currentExamScope, currentExamScope);
}
export function syncExamScope(search: string) {
  const requested = new URLSearchParams(search).get("exam_scope");
  if (
    (requested === "all" || requested === "mizoram-recruitment") &&
    requested !== documentScope
  ) {
    documentScope = requested;
    listeners.forEach((fn) => fn());
  }
}
export function currentExamScope(): ExamScope {
  return documentScope;
}
export function changeExamScope(scope: ExamScope) {
  try {
    localStorage.setItem(KEY, scope);
  } catch {
    /* URL still retains the choice */
  }
  const url = new URL(window.location.href);
  url.searchParams.set("exam_scope", scope);
  for (const key of [
    "collection_id",
    "paper_id",
    "offset",
    "section_path",
    "review",
  ])
    url.searchParams.delete(key);
  documentScope = scope;
  listeners.forEach((fn) => fn());
  return url.pathname + url.search + url.hash;
}
export function scopedApiPath(path: string): string {
  if (
    !/^\/(questions|collections|library|home|search|scoring-facts|mocks|vocabulary)([/?]|$)/.test(
      path,
    ) &&
    !path.startsWith("/community/feed")
  )
    return path;
  const [base, query = ""] = path.split("?");
  const params = new URLSearchParams(query);
  if (!params.has("exam_scope")) params.set("exam_scope", currentExamScope());
  return base + "?" + params;
}
export function scopeLink(path: string): string {
  if (currentExamScope() !== "all") return path;
  const [base, hash] = path.split("#");
  return (
    base +
    (base.includes("?") ? "&" : "?") +
    "exam_scope=all" +
    (hash ? "#" + hash : "")
  );
}
