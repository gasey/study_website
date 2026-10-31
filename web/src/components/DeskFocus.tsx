import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deskWrite, type FocusSession } from "../lib/studyDesks";
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
  return (
    <section>
      <div className="rounded-[8px] border border-[#B23A9A] bg-[#EEDDEC] p-7 text-center">
        <div className="desk-v3-label !text-[#86226F]">
          Focus session ·{" "}
          {active?.desk_id ? "linked to a private desk" : "your own time"}
        </div>
        <div
          role="timer"
          aria-label="Focus time remaining"
          className="my-4 font-display text-[clamp(64px,10vw,104px)] leading-none -tracking-[.02em]"
        >
          {Math.floor(remaining / 60)
            .toString()
            .padStart(2, "0")}
          :{(remaining % 60).toString().padStart(2, "0")}
        </div>
        {!active && (
          <label className="mx-auto mb-4 block max-w-[180px] text-[13px]">
            Duration
            <select
              className="desk-v3-input mt-1"
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            >
              {[5, 15, 25, 45, 50, 60, 90, 120].map((n) => (
                <option key={n} value={n}>
                  {n} minutes
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="flex flex-wrap justify-center gap-2">
          {registered ? (
            <>
              <button
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
                className="desk-v3-button border-[#B23A9A] bg-[#B23A9A] text-white"
              >
                {busy
                  ? "Saving…"
                  : !active
                    ? "Start focus"
                    : remaining === 0
                      ? "Complete session"
                      : active.state === "running"
                        ? "Pause"
                        : "Resume"}
              </button>
              {active && (
                <button
                  disabled={busy}
                  onClick={() => void action("cancel")}
                  className="desk-v3-button border-[#B23A9A] text-[#6A3767]"
                >
                  End early
                </button>
              )}
            </>
          ) : (
            <Link
              to="/login"
              className="desk-v3-button border-[#B23A9A] bg-[#B23A9A] text-white"
            >
              Sign in to save focus sessions
            </Link>
          )}
        </div>
        <p className="mt-4 text-[13px] leading-relaxed text-[#4E3A4D]">
          Your timer resumes across devices. Early endings retain actual time.
          Focus time earns no points.
        </p>
        {error && (
          <p role="alert" className="mt-3 text-[13px] text-mypick">
            {error}
          </p>
        )}
      </div>
      <h3 className="mt-[26px] border-b border-hairline pb-2 font-display text-[22px]">
        Recent sessions
      </h3>
      {sessions
        .filter((s) => s.state === "completed" || s.state === "cancelled")
        .map((s) => (
          <div
            key={s.id}
            className="flex justify-between gap-3 border-b border-hairline2 py-3 text-[13px]"
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
