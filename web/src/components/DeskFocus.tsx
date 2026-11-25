import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deskWrite, type FocusSession } from "../lib/studyDesks";
import { DeskBrassClock, DeskForestPorthole } from "./DeskCampfireClock";
export default function DeskFocus({
  sessions,
  serverTime,
  registered,
  deskId,
  onChange,
}: {
  sessions: FocusSession[];
  serverTime: string;
  registered: boolean;
  deskId?: string;
  onChange: () => void;
}) {
  const [minutes, setMinutes] = useState(25);
  const [fireOverride, setFireOverride] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(Date.now());
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    setOffset(Date.parse(serverTime) - Date.now());
  }, [serverTime]);
  useEffect(() => {
    const timer = window.setInterval(() => setTick(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const active = sessions.find(
    (s) => s.state === "running" || s.state === "paused",
  );
  const elapsed = active
    ? Math.min(
        active.duration_seconds,
        active.elapsed_seconds +
          (active.resumed_at
            ? Math.max(
                0,
                Math.floor(
                  (tick + offset - Date.parse(active.resumed_at)) / 1000,
                ),
              )
            : 0),
      )
    : 0;
  const remaining = active
    ? Math.max(0, active.duration_seconds - elapsed)
    : minutes * 60;
  async function action(value: string) {
    setBusy(true);
    setError("");
    try {
      if (active)
        await deskWrite("/focus/" + active.id, {
          action: value,
          expected_version: active.version,
        });
      else
        await deskWrite(
          "/focus",
          { minutes, desk_id: deskId || null },
          crypto.randomUUID(),
        );
      onChange();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const totalSeconds = active ? active.duration_seconds : minutes * 60;
  const pct = totalSeconds > 0 ? Math.min(100, Math.round((elapsed / totalSeconds) * 100)) : 0;
  const fireLit = fireOverride !== null ? fireOverride : active ? active.state === "running" : true;

  return (
    <section className="desk-focus-wrap">
      <div className="desk-focus-stage">
        <div className="desk-focus-grid">
          <div className="desk-focus-porthole-col">
            <DeskForestPorthole
              lit={fireLit}
              onToggle={() => setFireOverride((prev) => !(prev !== null ? prev : fireLit))}
              size={188}
            />
            <span className="desk-porthole-hint">Tap the fire to toggle ambiance</span>
          </div>

          <div className="desk-focus-ctrl-col">
            <div className="desk-focus-toprow">
              <div>
                <div className="desk-focus-kicker">
                  Forest cabin timer ·{" "}
                  {active?.desk_id ? "linked to private desk" : "your own time"}
                </div>
                <div
                  role="timer"
                  aria-label="Focus time remaining"
                  className="desk-focus-clock"
                >
                  {Math.floor(remaining / 60)
                    .toString()
                    .padStart(2, "0")}
                  :{(remaining % 60).toString().padStart(2, "0")}
                </div>
              </div>
              <DeskBrassClock size={74} />
            </div>

            {active && (
              <div className="desk-focus-bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                <span style={{ width: `${pct}%` }} />
              </div>
            )}

            {!active && (
              <div className="desk-focus-presets" role="group" aria-label="Session duration">
                {[15, 25, 45, 60, 90].map((n) => (
                  <button
                    key={n}
                    type="button"
                    aria-pressed={minutes === n}
                    onClick={() => setMinutes(n)}
                    className={"desk-preset-pill" + (minutes === n ? " is-on" : "")}
                  >
                    {n}m
                  </button>
                ))}
              </div>
            )}

            <div className="desk-focus-actions">
              {registered ? (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void action(
                        !active
                          ? "start"
                          : remaining === 0
                            ? "finish"
                            : active.state === "running"
                              ? "pause"
                              : "resume",
                      )
                    }
                    className="desk-focus-primary"
                  >
                    {busy
                      ? "Saving…"
                      : !active
                        ? `Start ${minutes}m focus`
                        : remaining === 0
                          ? "Complete session"
                          : active.state === "running"
                            ? "Pause"
                            : "Resume"}
                  </button>
                  {active && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void action("cancel")}
                      className="desk-focus-ghost"
                    >
                      End early
                    </button>
                  )}
                </>
              ) : (
                <Link to="/login" className="desk-focus-primary">
                  Sign in to save focus sessions
                </Link>
              )}
            </div>
            <p className="desk-focus-note">
              Your timer resumes across devices. Early endings retain actual time.
              Focus time earns no points.
            </p>
            {error && (
              <p role="alert" className="mt-3 text-sm text-[#FCA5A5]">
                {error}
              </p>
            )}
          </div>
        </div>
      </div>
      <h3 className="mt-[26px] border-b border-hairline pb-2 font-display text-lg">
        Recent sessions
      </h3>
      {sessions
        .filter((s) => s.state === "completed" || s.state === "cancelled")
        .map((s) => (
          <div
            key={s.id}
            className="flex justify-between gap-3 border-b border-hairline2 py-3 text-sm"
          >
            <span>
              {new Date(s.created_at).toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </span>
            <span className="text-secondary">
              {Math.floor(s.elapsed_seconds / 60)} min ·{" "}
              {s.state === "completed" ? "completed" : "ended early"}
            </span>
          </div>
        ))}
      {!sessions.some(
        (s) => s.state === "completed" || s.state === "cancelled",
      ) && (
        <p className="desk-v3-empty">
          Your completed and early-ended focus sessions will appear here.
        </p>
      )}
    </section>
  );
}
