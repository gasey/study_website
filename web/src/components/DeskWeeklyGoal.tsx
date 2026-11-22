import { useEffect, useRef, useState } from "react";
import { deskRead } from "../lib/desk";
import { deskWrite, type DeskWeeklyGoal as Goal } from "../lib/studyDesks";
import { accountGeneration } from "../lib/accountContext";

const dateLabel = (day: string) => new Date(day + "T00:00:00+05:30").toLocaleDateString("en-IN", {
  day: "numeric", month: "short", timeZone: "Asia/Kolkata",
});

export default function DeskWeeklyGoal({ deskId }: { deskId: string }) {
  const [data, setData] = useState<Goal | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<{ week_start: string; expected_version: number } | null>(null);
  const [target, setTarget] = useState("");
  const refreshRef = useRef<() => Promise<void>>(async () => {});
  const generation = useRef(accountGeneration());
  const lifetime = useRef(0);
  const active = useRef(false);
  const valid = () => active.current && generation.current === accountGeneration();
  useEffect(() => {
    active.current = true;
    ++lifetime.current;
    generation.current = accountGeneration();
    let sequence = 0;
    setData(null); setEditing(null); setError(""); setNotice(""); setBusy(false);
    async function refresh() {
      const run = ++sequence;
      try {
        const next = await deskRead<Goal>("/rooms/" + deskId + "/weekly-goal");
        if (!valid() || run !== sequence) return;
        setData(next); setError("");
      } catch (e) {
        if (!valid() || run !== sequence) return;
        setData(null); setError((e as Error).message);
      }
    }
    refreshRef.current = refresh;
    void refresh();
    const visibleRefresh = () => { if (document.visibilityState === "visible") void refresh(); };
    const reset = () => {
      active.current = false; ++sequence; ++lifetime.current;
      setData(null); setEditing(null); setError(""); setNotice(""); setBusy(false);
    };
    const timer = window.setInterval(visibleRefresh, 30000);
    window.addEventListener("focus", visibleRefresh);
    window.addEventListener("ism-progress-change", visibleRefresh);
    window.addEventListener("ism-auth-change", reset);
    window.addEventListener("ism-auth-expired", reset);
    return () => {
      active.current = false; ++sequence; ++lifetime.current;
      window.clearInterval(timer);
      window.removeEventListener("focus", visibleRefresh);
      window.removeEventListener("ism-progress-change", visibleRefresh);
      window.removeEventListener("ism-auth-change", reset);
      window.removeEventListener("ism-auth-expired", reset);
    };
  }, [deskId]);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!valid() || !editing || busy) return;
    const run = lifetime.current;
    const current = () => valid() && run === lifetime.current;
    setBusy(true); setError(""); setNotice("");
    try {
      await deskWrite("/rooms/" + deskId + "/weekly-goal", { ...editing, target: Number(target) });
      if (!current()) return;
      setEditing(null); setNotice("Weekly target saved.");
      await refreshRef.current();
    } catch (e) {
      if (current()) setError((e as Error).message);
    } finally {
      if (current()) setBusy(false);
    }
  }

  return <section aria-label="Shared weekly goal" className="my-4 min-w-0 rounded-panel border border-hairline bg-card p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-base font-bold">Together this week</h2>
      <button type="button" className="desk-v3-button" disabled={busy} onClick={() => { if (valid()) void refreshRef.current(); }}>Refresh goal</button>
    </div>
    {error && <p role="alert" className="mt-2 break-words text-sm text-secondary">{error}</p>}
    {notice && <p role="status" className="mt-2 text-sm">{notice}</p>}
    {!data && !error && <p role="status" className="mt-2 text-sm text-secondary">Loading weekly goal…</p>}
    {data && <>
      <p className="mt-2 text-xs text-secondary">{dateLabel(data.week_start)} – {dateLabel(data.week_end)} · IST</p>
      {data.target === null ? <p className="mt-3 text-sm">No shared goal this week.{!data.can_edit && " The room owner can set one."}</p> : <>
        <p className="mt-3 text-lg font-bold tabular-nums">{data.scored_attempts.toLocaleString("en-IN")} / {data.target.toLocaleString("en-IN")} scored attempts</p>
        <div role="progressbar" aria-label="Shared scored attempts" aria-valuemin={0} aria-valuemax={data.target}
          aria-valuenow={Math.min(data.scored_attempts, data.target)} aria-valuetext={`${data.scored_attempts} of ${data.target} scored attempts`}
          className="mt-2 h-2 overflow-hidden rounded-full bg-opt-bg">
          <div className="h-full rounded-full bg-link" style={{ width: Math.min(100, data.scored_attempts / data.target * 100) + "%" }} />
        </div>
        {data.completed && <p className="mt-2 text-sm font-semibold">Weekly goal reached.</p>}
      </>}
      <p className="mt-3 text-sm text-secondary">Counts scored attempts since joining this room, from current members who share progress with you. Private and blocked activity is excluded. Counts can change after answer corrections or sharing changes.</p>
      <p className="mt-2 text-sm text-secondary">Resets Monday at 00:00 IST. This goal earns no XP or points.</p>
      {data.can_edit && !editing && <button type="button" className="desk-v3-button mt-3" onClick={() => {
        if (!valid()) return;
        setEditing({ week_start: data.week_start, expected_version: data.version });
        setTarget(data.target?.toString() || ""); setNotice("");
      }}>{data.target === null ? "Set weekly target" : "Edit weekly target"}</button>}
    </>}
    {editing && <form onSubmit={save} className="mt-4 border-t border-hairline pt-4">
      <label className="block text-sm font-semibold">Scored attempts together
        <input className="desk-v3-input mt-2" type="number" inputMode="numeric" min={1} max={10000} step={1} required
          value={target} onChange={e => setTarget(e.target.value)} disabled={busy} />
      </label>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="desk-v3-button" disabled={busy || !data}>{busy ? "Saving…" : "Save weekly target"}</button>
        <button type="button" className="desk-v3-button" disabled={busy} onClick={() => setEditing(null)}>Cancel</button>
      </div>
      {data && (editing.week_start !== data.week_start || editing.expected_version !== data.version) &&
        <p role="status" className="mt-2 text-sm text-secondary">The goal or week changed. Cancel and reopen the editor to use the current version.</p>}
    </form>}
  </section>;
}
