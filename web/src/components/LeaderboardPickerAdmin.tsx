import { useCallback, useEffect, useState } from "react";
import { reviewRequest } from "../lib/review";

type ThemeId = "balanced" | "gk" | "english" | "maths" | "computer";

interface ThemeOption {
  id: ThemeId;
  label: string;
  short: string;
  description: string;
}

interface QuestionPreview {
  position: number;
  id: string;
  question: string;
  options: string[];
  answer_text: string | null;
  pillar: string;
  pillar_label: string;
  exam_name: string | null;
  year: number | null;
}

interface PickedSet {
  kind: "daily" | "cup";
  id: string;
  opens_at: string;
  closes_at: string;
  status: "scheduled" | "live" | "closed";
  entries: number;
  locked: boolean;
  question_count: number;
  pillar_counts: Record<string, number>;
  questions: QuestionPreview[];
}

interface UpcomingResponse {
  as_of: string;
  timezone: string;
  no_repeat_daily_days: number;
  no_repeat_cup_days: number;
  themes: ThemeOption[];
  dailies: PickedSet[];
  cups: PickedSet[];
}

function fmtIst(iso: string): string {
  try {
    return (
      new Date(iso).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        dateStyle: "medium",
        timeStyle: "short",
      }) + " IST"
    );
  } catch {
    return iso;
  }
}

/** Owner workbench for previewing, theming, and swapping pre-picked Daily Five & Weekly Cup leaderboard sets. */
export default function LeaderboardPickerAdmin() {
  const [data, setData] = useState<UpcomingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [theme, setTheme] = useState<ThemeId>("balanced");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await reviewRequest<UpcomingResponse>(
        "/admin/leaderboard-picker/upcoming?days_ahead=3",
      );
      setData(res);
    } catch (e) {
      setError((e as Error).message || "Could not load scheduled leaderboard sets.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runEnsure() {
    setBusyKey("ensure");
    setError("");
    setNotice("");
    try {
      const res = await reviewRequest<{
        run: { dailies: { created: boolean }[]; cups: { created: boolean }[] };
        upcoming: UpcomingResponse;
      }>("/admin/leaderboard-picker/ensure", {
        days_ahead: 3,
        daily_theme: theme,
        cup_theme: theme,
      });
      setData(res.upcoming);
      const newD = res.run.dailies.filter((d) => d.created).length;
      const newC = res.run.cups.filter((c) => c.created).length;
      setNotice(
        `Pre-picker finished (${theme}): created ${newD} Daily set(s) and ${newC} Weekly Cup set(s).`,
      );
    } catch (e) {
      setError((e as Error).message || "Could not pre-pick upcoming sets.");
    } finally {
      setBusyKey(null);
    }
  }

  async function regenerate(kind: "daily" | "cup", setId: string) {
    const key = `regen:${kind}:${setId}`;
    setBusyKey(key);
    setError("");
    setNotice("");
    try {
      const res = await reviewRequest<{ upcoming: UpcomingResponse }>(
        "/admin/leaderboard-picker/regenerate",
        { kind, set_id: setId, theme },
      );
      setData(res.upcoming);
      setNotice(`Re-rolled ${kind === "daily" ? "Daily Five" : "Weekly Cup"} ${setId} using "${theme}".`);
    } catch (e) {
      setError((e as Error).message || "Could not regenerate this set.");
    } finally {
      setBusyKey(null);
    }
  }

  async function swapSlot(kind: "daily" | "cup", setId: string, position: number) {
    const key = `swap:${kind}:${setId}:${position}`;
    setBusyKey(key);
    setError("");
    setNotice("");
    try {
      const res = await reviewRequest<{ upcoming: UpcomingResponse }>(
        "/admin/leaderboard-picker/swap",
        { kind, set_id: setId, position, theme },
      );
      setData(res.upcoming);
      setNotice(`Swapped Q${position + 1} in ${setId} with a fresh non-repeating question.`);
    } catch (e) {
      setError((e as Error).message || "Could not swap question.");
    } finally {
      setBusyKey(null);
    }
  }

  function renderSetCard(item: PickedSet) {
    const cardKey = `${item.kind}:${item.id}`;
    const isOpen = expanded[cardKey] ?? item.kind === "daily";
    const regenKey = `regen:${item.kind}:${item.id}`;
    return (
      <article
        key={cardKey}
        className="rounded-2xl border border-hairline bg-card p-5 shadow-sm"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-paper px-2.5 py-0.5 font-mono text-xs font-bold uppercase text-ink">
                {item.kind === "daily" ? "📅 Daily Five" : "🏆 Weekly 25-Q Cup"}
              </span>
              <strong className="font-mono text-base text-ink">{item.id}</strong>
              <span
                className={
                  "rounded-full px-2.5 py-0.5 font-mono text-xs font-bold " +
                  (item.status === "live"
                    ? "bg-correct-soft text-correct-dark"
                    : item.status === "scheduled"
                      ? "bg-practice-soft text-practice-dark"
                      : "bg-canvas text-muted")
                }
              >
                {item.status.toUpperCase()}
              </span>
              <span
                className={
                  "rounded-full px-2.5 py-0.5 font-mono text-xs font-semibold " +
                  (item.locked
                    ? "bg-attention-soft text-ink"
                    : "bg-canvas text-secondary")
                }
              >
                {item.locked
                  ? `🔒 Locked (${item.entries} player${item.entries === 1 ? "" : "s"})`
                  : "✎ Editable (0 entries)"}
              </span>
            </div>
            <p className="mt-1.5 text-xs text-secondary">
              Window: {fmtIst(item.opens_at)} → {fmtIst(item.closes_at)} ·{" "}
              {item.question_count} questions
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {Object.entries(item.pillar_counts).map(([label, count]) => (
                <span
                  key={label}
                  className="rounded-full border border-hairline bg-paper px-2.5 py-0.5 text-xs font-semibold text-secondary"
                >
                  {label}: {count}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() =>
                setExpanded((prev) => ({ ...prev, [cardKey]: !isOpen }))
              }
              className="min-h-10 rounded-pill border border-hairline bg-paper px-3.5 text-xs font-bold text-ink hover:border-ink"
            >
              {isOpen ? "Hide questions" : `Preview ${item.question_count} Qs`}
            </button>
            <button
              type="button"
              disabled={item.locked || !!busyKey}
              onClick={() => void regenerate(item.kind, item.id)}
              title={
                item.locked
                  ? "Locked once players have started"
                  : `Re-roll entire set with theme "${theme}"`
              }
              className="min-h-10 rounded-pill bg-ink px-4 text-xs font-bold text-paper disabled:opacity-40"
            >
              {busyKey === regenKey ? "Re-rolling…" : `🎲 Re-roll (${theme})`}
            </button>
          </div>
        </div>

        {isOpen && (
          <ol className="mt-4 space-y-2.5 border-t border-hairline pt-4">
            {item.questions.map((q) => {
              const swapKey = `swap:${item.kind}:${item.id}:${q.position}`;
              return (
                <li
                  key={`${cardKey}-${q.position}-${q.id}`}
                  className="rounded-xl border border-hairline bg-paper p-3.5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-muted">
                        <span className="font-bold text-ink">Q{q.position + 1}</span>
                        <span>·</span>
                        <span>{q.pillar_label}</span>
                        {q.exam_name && (
                          <>
                            <span>·</span>
                            <span>
                              {q.exam_name}
                              {q.year ? ` ${q.year}` : ""}
                            </span>
                          </>
                        )}
                      </div>
                      <p className="mt-1 text-sm font-medium text-ink">
                        {q.question}
                      </p>
                      {q.answer_text && (
                        <p className="mt-1 text-xs font-semibold text-correct-dark">
                          ✓ Official key: {q.answer_text}
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      disabled={item.locked || !!busyKey}
                      onClick={() => void swapSlot(item.kind, item.id, q.position)}
                      className="min-h-9 shrink-0 rounded-pill border border-hairline bg-card px-3 text-xs font-bold text-ink hover:border-ink disabled:opacity-40"
                    >
                      {busyKey === swapKey ? "Swapping…" : "🔄 Swap"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </article>
    );
  }

  return (
    <section className="mt-4 space-y-5">
      <div className="rounded-2xl border border-hairline bg-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-muted">
              Scheduled Microservice · Daily &amp; Weekly Leaderboards
            </span>
            <h2 className="mt-1 font-display text-2xl font-bold text-ink">
              Leaderboard Question Picker
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-secondary">
              Automatically pre-picks official-key non-technical sets 24h+ ahead via{" "}
              <code className="rounded bg-canvas px-1.5 py-0.5 font-mono text-xs">
                finna-leaderboard-picker.timer
              </code>{" "}
              (30-day Daily / 8-week Cup no-repeat window). Pick a subject theme below to
              preview, re-roll, or swap questions before players enter.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!!busyKey}
              onClick={() => void runEnsure()}
              className="finna-btn min-h-11 px-4 text-sm"
            >
              {busyKey === "ensure" ? "Picking…" : "⚡ Pick Upcoming Sets Now"}
            </button>
            <button
              type="button"
              disabled={loading || !!busyKey}
              onClick={() => void load()}
              className="min-h-11 rounded-pill border border-hairline bg-paper px-4 text-sm font-semibold text-ink hover:border-ink"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Theme Picker Pills */}
        <div className="mt-4 border-t border-hairline pt-4">
          <div className="font-mono text-xs font-bold uppercase tracking-wider text-muted">
            Active Theme for Pick / Re-roll / Swap
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(
              data?.themes || [
                { id: "balanced", short: "Balanced Core", label: "Balanced Core", description: "" },
                { id: "gk", short: "Only GK", label: "Only GK", description: "" },
                { id: "english", short: "Only English", label: "Only English", description: "" },
                { id: "maths", short: "Only Maths", label: "Only Maths", description: "" },
                { id: "computer", short: "Only Computer", label: "Only Computer", description: "" },
              ]
            ).map((opt) => (
              <button
                key={opt.id}
                type="button"
                aria-pressed={theme === opt.id}
                onClick={() => setTheme(opt.id as ThemeId)}
                className={
                  "min-h-10 rounded-pill border px-3.5 text-xs font-bold transition " +
                  (theme === opt.id
                    ? "border-ink bg-ink text-paper"
                    : "border-hairline bg-paper text-ink hover:border-ink")
                }
              >
                {opt.short}
              </button>
            ))}
          </div>
        </div>

        {notice && (
          <p
            role="status"
            className="mt-3 rounded-xl border border-correct/30 bg-correct-soft px-3.5 py-2.5 text-sm font-semibold text-correct-dark"
          >
            ✓ {notice}
          </p>
        )}
        {error && (
          <p
            role="alert"
            className="mt-3 rounded-xl border border-wrong bg-wrong-soft px-3.5 py-2.5 text-sm font-semibold text-wrong-dark"
          >
            {error}
          </p>
        )}
      </div>

      {loading && !data && (
        <p className="text-sm text-secondary">Loading upcoming Daily &amp; Weekly sets…</p>
      )}

      {data && (
        <>
          <div className="space-y-3">
            <h3 className="font-display text-lg font-bold text-ink">
              Daily Five Sets ({data.dailies.length})
            </h3>
            {data.dailies.length === 0 ? (
              <div className="rounded-2xl border border-hairline bg-card p-5 text-sm text-secondary">
                No Daily Five sets pre-picked yet. Click{" "}
                <strong>⚡ Pick Upcoming Sets Now</strong> above.
              </div>
            ) : (
              data.dailies.map(renderSetCard)
            )}
          </div>

          <div className="space-y-3">
            <h3 className="font-display text-lg font-bold text-ink">
              Weekly 25-Q Cup Sets ({data.cups.length})
            </h3>
            {data.cups.length === 0 ? (
              <div className="rounded-2xl border border-hairline bg-card p-5 text-sm text-secondary">
                No Weekly Cup pre-picked yet. Click{" "}
                <strong>⚡ Pick Upcoming Sets Now</strong> above.
              </div>
            ) : (
              data.cups.map(renderSetCard)
            )}
          </div>
        </>
      )}
    </section>
  );
}
