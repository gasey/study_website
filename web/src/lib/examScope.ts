import { useSyncExternalStore } from "react";
export type ExamScope = "mizoram-recruitment" | "all";
const KEY = "ism-exam-scope";
function readExamScope(): ExamScope {
  const explicit = new URLSearchParams(window.location.search).get(
    "exam_scope",
  );
  if (explicit === "all" || explicit === "mizoram-recruitment") return explicit;
  try {
    return localStorage.getItem(KEY) === "all" ? "all" : "mizoram-recruitment";
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
