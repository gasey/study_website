import type {AvatarLook} from './avatar'
import { deviceId } from "./device";
import { reviewRequest } from "./review";
export interface DeskTask {
  id: string;
  text: string;
  done: boolean;
  week: boolean;
}
export interface DeskNote {
  id: string;
  title: string;
  body: string;
  subject: string;
}
export interface DeskData {
  goal: string;
  goalSubject: string;
  tasks: DeskTask[];
  notes: DeskNote[];
  saved: string[];
  recent: string[];
  completedDays: string[];
  weeklyTarget: number;
}
interface Stored {
  data: DeskData;
  version: number;
  dirty: boolean;
}
interface Personal {
  avatar: AvatarLook|null;
  user_id: string;
  handle: string;
  registered: boolean;
  version: number;
  data: DeskData;
  private_desks_enabled: boolean;
}
export interface DeskSync {
  avatar?:AvatarLook|null;
  loading: boolean;
  registered: boolean;
  userId: string;
  handle: string;
  status: "loading" | "local" | "saved" | "saving" | "conflict" | "error";
  error: string;
  privateEnabled: boolean;
}
const EVENT = "ism-study-desk-change";
const empty = (): DeskData => ({
  goal: "",
  goalSubject: "",
  tasks: [],
  notes: [],
  saved: [],
  recent: [],
  completedDays: [],
  weeklyTarget: 100,
});
let state: Stored = { data: empty(), version: 0, dirty: false };
let sync: DeskSync = {
  loading: true,
  registered: false,
  userId: "",
  handle: "",
  status: "loading",
  error: "",
  privateEnabled: false,
};
let epoch = 0;
let timer: number | undefined;
let writing = false;
let initialized = false;
let pendingRecent: string[] = [];
const guestKey = () => `ism.study-desk.v1.${deviceId()}`;
const key = () =>
  sync.registered ? "ism.study-desk.account.v2." + sync.userId : guestKey();
const emit = () => window.dispatchEvent(new Event(EVENT));
function normal(value: Partial<DeskData> | null): DeskData {
  const v = value || {};
  return {
    ...empty(),
    ...v,
    tasks: Array.isArray(v.tasks)
      ? v.tasks
          .filter(
            (x) =>
              x &&
              typeof x.id === "string" &&
              typeof x.text === "string" &&
              typeof x.done === "boolean",
          )
          .map((x) => ({ ...x, week: !!x.week }))
          .slice(-200)
      : [],
    notes: Array.isArray(v.notes) ? v.notes.slice(0, 100) : [],
    saved: Array.isArray(v.saved)
      ? v.saved.filter((x) => typeof x === "string").slice(0, 500)
      : [],
    recent: Array.isArray(v.recent)
      ? v.recent.filter((x) => typeof x === "string").slice(0, 8)
      : [],
    completedDays: Array.isArray(v.completedDays)
      ? v.completedDays.filter((x) => /^\d{4}-\d{2}-\d{2}$/.test(x)).slice(-730)
      : [],
    weeklyTarget: Number(v.weeklyTarget) || 100,
  };
}
function persist() {
  try {
    localStorage.setItem(
      key(),
      JSON.stringify(sync.registered ? state : state.data),
    );
  } catch {
    sync = {
      ...sync,
      status: "error",
      error:
        "Browser storage is unavailable. Keep this page open until your account save finishes.",
    };
  }
}
export function getDesk(): DeskData {
  return sync.loading ? empty() : state.data;
}
export function getDeskSync(): DeskSync {
  return sync;
}
export async function deskRead<T>(path: string): Promise<T> {
  const run = epoch;
  const owner = sync.userId;
  const r = await fetch("/api/desk" + path, {
    credentials: "include",
    headers: { "x-device-id": deviceId() },
  });
  if (!r.ok) {
    const e = await r.json();
    throw new Error(e.detail || "Your desk could not load");
  }
  const data = await r.json();
  if (run !== epoch || owner !== sync.userId)
    throw new Error(
      "Your signed-in account changed. Reload before continuing.",
    );
  return data;
}
export async function hydrateDesk(force = false): Promise<void> {
  if (initialized && !force) return;
  initialized = true;
  const run = ++epoch;
  clearTimeout(timer);
  state = { data: empty(), version: 0, dirty: false };
  sync = {
    ...sync,
    avatar: null,
    userId: "",
    handle: "",
    registered: false,
    privateEnabled: false,
    loading: true,
    status: "loading",
    error: "",
  };
  emit();
  try {
    const remote = await deskRead<Personal>("/personal");
    if (run !== epoch) return;
    sync = {
      loading: false,
      registered: remote.registered,
      userId: remote.user_id,
      handle: remote.handle,
      avatar: remote.avatar,
      status: remote.registered ? "saved" : "local",
      error: "",
      privateEnabled: remote.private_desks_enabled,
    };
    let cached: Stored | null = null;
    try {
      const raw = JSON.parse(localStorage.getItem(key()) || "null");
      cached = remote.registered
        ? raw
        : raw
          ? { data: raw, version: 0, dirty: false }
          : null;
    } catch {
      /* use account version */
    }
    state =
      remote.registered && cached?.dirty
        ? { ...cached, data: normal(cached.data) }
        : {
            data: remote.registered
              ? normal(remote.data)
              : normal(cached?.data || null),
            version: remote.version,
            dirty: false,
          };
    persist();
    emit();
    for (const qid of pendingRecent) trackRecentQuestion(qid);
    pendingRecent = [];
    if (state.dirty) void flushDesk();
  } catch (e) {
    if (run !== epoch) return;
    sync = {
      ...sync,
      loading: false,
      status: "error",
      error: (e as Error).message,
    };
    emit();
  }
}
export function saveDesk(next: DeskData): void {
  if (sync.loading || !sync.userId) return;
  state = { ...state, data: normal(next), dirty: sync.registered };
  sync = { ...sync, status: sync.registered ? "saving" : "local", error: "" };
  persist();
  emit();
  clearTimeout(timer);
  if (sync.registered) timer = window.setTimeout(() => void flushDesk(), 650);
}
export async function flushDesk(): Promise<void> {
  if (writing || !state.dirty || !sync.registered || sync.loading) return;
  const run = epoch;
  const owner = sync.userId;
  const submitted = state.data;
  const version = state.version;
  writing = true;
  sync = { ...sync, status: "saving" };
  emit();
  try {
    const r = await reviewRequest<{ data: DeskData; version: number }>(
      "/desk/personal",
      { user_id: owner, expected_version: version, data: submitted },
    );
    if (run !== epoch || owner !== sync.userId) return;
    state = {
      data: state.data,
      version: r.version,
      dirty: JSON.stringify(state.data) !== JSON.stringify(submitted),
    };
    sync = { ...sync, status: state.dirty ? "saving" : "saved", error: "" };
    persist();
    emit();
  } catch (e) {
    if (run !== epoch) return;
    const message = (e as Error).message;
    sync = {
      ...sync,
      status: message.includes("another device") ? "conflict" : "error",
      error: message,
    };
    persist();
    emit();
  } finally {
    writing = false;
    if (
      state.dirty &&
      sync.registered &&
      !sync.loading &&
      sync.status === "saving"
    )
      timer = window.setTimeout(() => void flushDesk(), 650);
  }
}
export async function reloadAccountDesk(keepLocal = false) {
  const r = await deskRead<Personal>("/personal");
  if (r.user_id !== sync.userId)
    throw new Error("Account changed. Reload this page.");
  state = {
    data: keepLocal ? state.data : normal(r.data),
    version: r.version,
    dirty: keepLocal,
  };
  sync = { ...sync, status: keepLocal ? "saving" : "saved", error: "" };
  persist();
  emit();
  if (keepLocal) await flushDesk();
}
export function importGuestDesk() {
  let legacy: DeskData;
  try {
    legacy = normal(JSON.parse(localStorage.getItem(guestKey()) || "null"));
  } catch {
    return;
  }
  const d = getDesk();
  saveDesk({
    ...d,
    goal: d.goal || legacy.goal,
    goalSubject: d.goalSubject || legacy.goalSubject,
    tasks: [
      ...new Map([...legacy.tasks, ...d.tasks].map((x) => [x.id, x])).values(),
    ].slice(-200),
    notes: [
      ...new Map([...legacy.notes, ...d.notes].map((x) => [x.id, x])).values(),
    ].slice(0, 100),
    saved: [...new Set([...d.saved, ...legacy.saved])].slice(0, 500),
    recent: [...new Set([...d.recent, ...legacy.recent])].slice(0, 8),
    completedDays: [
      ...new Set([...d.completedDays, ...legacy.completedDays]),
    ].slice(-730),
  });
}
export function subscribeDesk(listener: () => void): () => void {
  window.addEventListener(EVENT, listener);
  const storage = (e: StorageEvent) => {
    if (e.key === key()) void hydrateDesk(true);
  };
  window.addEventListener("storage", storage);
  return () => {
    window.removeEventListener(EVENT, listener);
    window.removeEventListener("storage", storage);
  };
}
export function trackRecentQuestion(id: string): void {
  if (sync.loading) {
    pendingRecent = [id, ...pendingRecent.filter((x) => x !== id)].slice(0, 8);
    return;
  }
  const d = getDesk();
  if (d.recent[0] !== id)
    saveDesk({
      ...d,
      recent: [id, ...d.recent.filter((x) => x !== id)].slice(0, 8),
    });
}
function resetAccountDesk() {
  pendingRecent = [];
  state = { data: empty(), version: 0, dirty: false };
  void hydrateDesk(true);
}
window.addEventListener("ism-auth-change", () => {
  try {
    localStorage.setItem("ism.desk.account-change", crypto.randomUUID());
  } catch {
    /* local event still works */
  }
  resetAccountDesk();
});
window.addEventListener("storage", (e) => {
  if (e.key === "ism.desk.account-change") resetAccountDesk();
});
window.addEventListener("online", () => {
  if (state.dirty) void flushDesk();
});
export function weekDates(now = new Date()): string[] {
  const d = new Date(now);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return Array.from({ length: 7 }, (_, i) => {
    const x = new Date(d);
    x.setDate(d.getDate() + i);
    return localDate(x);
  });
}
export function localDate(d = new Date()): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
