import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getHome, type HomeData } from "../lib/api";
import CalendarLearningLayers,{type LearningLayersState} from '../components/CalendarLearningLayers'
import {
  calendarRead,
  calendarPersonal,
  calendarChange,
  EVENT_KINDS,
  indiaToday,
  dateLabel,
  dayNumber,
  exportCalendar,
  googleCalendar,
  type CalendarEvent,
  type CalendarPersonal,
  type EventKind,
  ownedKindLabel,
} from "../lib/calendar";
const KIND_DOT: Record<EventKind, string> = {
  notification: "#7C3AED",
  deadline: "#E11D48",
  admit_card: "#2563EB",
  exam: "#D97706",
  answer_key: "#059669",
  result: "#0A7D8C",
};
const COLORS: Record<EventKind, string> = {
  notification: "bg-[#EEE6F7] text-[#5E2F98]",
  deadline: "bg-[#F8DEDA] text-[#9E2A1F]",
  admit_card: "bg-[#E3E9F8] text-[#1F44A6]",
  exam: "bg-[#F6E7C6] text-[#7E4A00]",
  answer_key: "bg-[#DCEFE1] text-[#1F6234]",
  result: "bg-[#D3EAEA] text-[#1F7F86]",
};
export default function ExamCalendar({
  notices = false,
}: {
  notices?: boolean;
}) {
  const [params, setParams] = useSearchParams();
  const [learning,setLearning]=useState<LearningLayersState|null>(null)
  const today = indiaToday();
  const rawMonth = params.get("month");
  const month =
    rawMonth &&
    /^\d{4}-(0[1-9]|1[0-2])$/.test(rawMonth) &&
    rawMonth >= "2000-01" &&
    rawMonth <= "2100-12"
      ? rawMonth
      : today.slice(0, 7);
  const view = params.get("view") === "list" ? "list" : params.get("view") === "week" ? "week" : "month";
  const kind = params.get("kind") || "";
  const exam = params.get("exam") || "";
  const onlyFollowing = params.get("following") === "1";
  const focus = params.get("event");
  const [rows, setRows] = useState<CalendarEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const accountEpoch = useRef(0);
  const [personal, setPersonal] = useState<CalendarPersonal | null>(null);
  const [exams, setExams] = useState<HomeData["collections"]>([]);
  const [selected, setSelected] = useState(today);
  const [focused, setFocused] = useState<CalendarEvent | null>(null);
  const year = Number(month.slice(0, 4)),
    mi = Number(month.slice(5)) - 1;
  const days = new Date(Date.UTC(year, mi + 1, 0)).getUTCDate();
  const addDays=(day:string,n:number)=>new Date(dayNumber(day)*86400000+n*86400000).toISOString().slice(0,10);
  const rawWeek=params.get('week')||'';
  const weekAnchor=/^\d{4}-\d{2}-\d{2}$/.test(rawWeek)&&rawWeek>='2000-01-01'&&rawWeek<='2100-12-31'&&Number.isFinite(Date.parse(rawWeek))&&new Date(rawWeek).toISOString().slice(0,10)===rawWeek?rawWeek:month===today.slice(0,7)?today:month+'-01';
  const weekStart=addDays(weekAnchor,-((new Date(weekAnchor).getUTCDay()+6)%7));
  const start=view==='week'?weekStart:month+'-01',
    end=view==='week'?addDays(weekStart,6):month+'-'+String(days).padStart(2,'0');
  const gridDays=Array.from({length:view==='week'?7:days},(_,i)=>addDays(start,i));
  const change = (patch: Record<string, string>) => {
    const next = new URLSearchParams(params);
    next.delete("event");
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    setParams(next);
    setOffset(0);
  };
  useEffect(() => {
    let live = true;
    getHome()
      .then((h) => {
        if (live) setExams(h.collections);
      })
      .catch(() => {});
    const load = () => {
      const epoch = ++accountEpoch.current;
      setPersonal(null);
      setLearning(null);
      return calendarPersonal()
        .then((p) => {
          if (live && epoch === accountEpoch.current) setPersonal(p);
        })
        .catch(() => {
          if (live && epoch === accountEpoch.current) setPersonal(null);
        });
    };
    void load();
    window.addEventListener("ism-auth-change", load);
    return () => {
      live = false;
      window.removeEventListener("ism-auth-change", load);
    };
  }, []);
  useEffect(() => {
    let live = true;
    setLoading(true);
    setError("");
    setRows([]);
    const query = new URLSearchParams({
      start,
      end,
      limit: "100",
      offset: String(offset),
      ...(kind && kind in EVENT_KINDS ? { kind } : {}),
      ...(exam ? { collection_id: exam } : {}),
    });
    calendarRead<{
      items: CalendarEvent[];
      total?: number;
      has_more?: boolean;
    }>(
      notices
        ? "/calendar/notices?" +
            new URLSearchParams({
              limit: "20",
              offset: String(offset),
              ...(kind && kind in EVENT_KINDS ? { kind } : {}),
              ...(exam ? { collection_id: exam } : {}),
            })
        : "/calendar/events?" + query,
    )
      .then((r) => {
        if (live) {
          setRows(r.items);
          setTotal(r.total || 0);
          setMore(!!r.has_more);
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [start, end, kind, exam, notices, offset, reload]);
  useEffect(() => {
    let live = true;
    setFocused(null);
    if (focus)
      calendarRead<CalendarEvent>(
        "/calendar/events/" + encodeURIComponent(focus),
      )
        .then((r) => {
          if (live) setFocused(r);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    return () => {
      live = false;
    };
  }, [focus, reload]);
  useEffect(() => {
    setSelected(view==='week'?weekAnchor:today>=start&&today<=end?today:start);
  }, [start, end, today, view, weekAnchor]);
  async function mutate(
    action: "reminders" | "follow" | "save",
    body: unknown,
  ) {
    const epoch = accountEpoch.current;
    setBusy(true);
    setError("");
    try {
      await calendarChange(action, body);
      const latest = await calendarPersonal();
      if (epoch !== accountEpoch.current) return;
      setPersonal(latest);
      window.dispatchEvent(new Event("ism-calendar-change"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const visible = rows.filter(
    (e) =>
      (!notices ||
        ((!kind || e.kind === kind) && (!exam || e.collection_id === exam))) &&
      (!onlyFollowing ||
        personal?.saved.includes(e.id) ||
        (!!e.collection_id && personal?.following.includes(e.collection_id))),
  );
  const ownedVisible=(learning?.data?.occurrences||[]).filter(e=>e.kind==='personal'?learning?.personal:e.kind==='progress-test'?learning?.progress:learning?.targets)
  const communityVisible=learning?.community?learning.data?.community||[]:[]
  const officialVisible=learning?.official===false?[]:visible
  const upcoming = personal?.upcoming;
  const remaining = upcoming?.starts_on
    ? Math.max(0, dayNumber(upcoming.starts_on) - dayNumber(today))
    : null;
  const move = (delta: number) => {
    if(view==='week'){
      const next=addDays(weekAnchor,delta*7);
      change({week:next,month:next.slice(0,7)});
    }else{
      const d = new Date(Date.UTC(year, mi + delta, 1));
      change({ month: d.toISOString().slice(0, 7),week:'' });
    }
  };
  function row(e: CalendarEvent) {
    const saved = personal?.saved.includes(e.id);
    return (
      <article
        id={"event-" + e.id}
        key={e.id}
        className="cal-event-card"
        style={{ borderLeftColor: KIND_DOT[e.kind] }}
      >
        <div className="flex flex-wrap items-start gap-2.5">
          <span
            className={
              "cal-kind-tag " + COLORS[e.kind]
            }
          >
            {EVENT_KINDS[e.kind]}
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold leading-snug">
              {e.title}
              {e.state === "archived" && (
                <span className="ml-2 text-mypick">Withdrawn</span>
              )}
            </h3>
            <p className="mt-1 text-xs text-secondary">
              {e.starts_on
                ? dateLabel(e.starts_on) +
                  (e.ends_on && e.ends_on !== e.starts_on
                    ? " – " + dateLabel(e.ends_on)
                    : "")
                : "Publication notice · no event date announced"}
              {e.exam_title ? " · " + e.exam_title : ""}
              {e.starts_on && (e.ends_on || e.starts_on) < today
                ? " · Date passed"
                : ""}
            </p>
          </div>
          {(e.state === "published" || saved) &&
            (personal?.registered ? (
              <button
                disabled={busy}
                className="finna-st-btn"
                aria-pressed={saved || false}
                onClick={() =>
                  void mutate("save", { event_id: e.id, enabled: !saved })
                }
              >
                {saved ? "Saved ✓" : "Save notice"}
              </button>
            ) : (
              <Link className="finna-st-btn" to="/login">
                Sign in to save
              </Link>
            ))}
        </div>
        <p className="mt-2.5 whitespace-pre-wrap text-sm leading-relaxed text-secondary">
          {e.summary}
        </p>
        <p className="mt-2 text-xs text-muted">
          {e.source_reference} · Verified {dateLabel(e.verified_on)} ·{" "}
          {e.verification_note}
        </p>
        <div className="mt-2 flex flex-wrap gap-3 text-xs font-semibold">
          <a
            className="inline-flex min-h-9 items-center text-link underline"
            href={e.source_url}
            target="_blank"
            rel="noreferrer"
          >
            Official source ↗
          </a>
          {e.collection_id && (
            <Link
              className="inline-flex min-h-9 items-center text-link"
              to={"/exams/" + e.collection_id}
            >
              Exam practice →
            </Link>
          )}
          {e.starts_on && e.state === "published" && (
            <>
              <a
                className="inline-flex min-h-9 items-center text-link"
                href={googleCalendar(e)}
                target="_blank"
                rel="noreferrer"
              >
                Google Calendar ↗
              </a>
              {personal?.registered && e.kind === "exam" && !notices && (
                <button
                  className="min-h-9 text-link"
                  onClick={() =>
                    window.dispatchEvent(
                      new CustomEvent("ism-calendar-target", {
                        detail: {
                          date: e.starts_on,
                          title: e.title,
                          collection_id: e.collection_id,
                        },
                      }),
                    )
                  }
                >
                  Use as my target
                </button>
              )}
              <button
                className="min-h-9 text-link"
                onClick={() => exportCalendar([e])}
              >
                Download .ics
              </button>
            </>
          )}
        </div>
      </article>
    );
  }

  const jumpToday = () => {
    setSelected(today);
    change({ month: today.slice(0, 7), week: view === "week" ? today : "" });
  };

  const agendaOfficial =
    notices || view === "list"
      ? notices
        ? visible
        : officialVisible
      : officialVisible.filter(
          (e) =>
            !!e.starts_on &&
            e.starts_on <= selected &&
            (e.ends_on || e.starts_on) >= selected,
        );
  const agendaCommunity = !notices
    ? communityVisible.filter((e) => view === "list" || e.day === selected)
    : [];
  const agendaOwned = !notices
    ? ownedVisible.filter((e) => view === "list" || e.day === selected)
    : [];
  const agendaTotal =
    agendaOfficial.length + agendaCommunity.length + agendaOwned.length;
  const selectedForecast = !notices && learning?.forecast
    ? learning.data?.forecast.find((r) => r.day === selected)
    : null;

  const agendaPanel = loading ? (
    <p role="status" className="py-6 text-sm text-secondary">
      Loading official entries…
    </p>
  ) : (
    <section className="cal-agenda-card" aria-label="Schedule details">
      <div className="cal-agenda-head">
        <div>
          <span className="cal-agenda-eyebrow">
            {notices
              ? "Verified feed"
              : view === "list"
                ? "Month schedule"
                : selected === today
                  ? "Today’s schedule"
                  : "Selected day"}
          </span>
          <h2>
            {notices
              ? "Latest verified notices"
              : view === "list"
                ? "Dates this month"
                : dateLabel(selected)}
          </h2>
        </div>
        <span className="cal-agenda-badge">
          {agendaTotal} {agendaTotal === 1 ? "item" : "items"}
        </span>
      </div>

      {selectedForecast && (
        <Link
          to={"/revise?" + new URLSearchParams({ through: selected, exam_scope: "all" })}
          className="cal-forecast-cta"
        >
          <span>↻ {selectedForecast.count} projected reviews due</span>
          <strong>Review this day →</strong>
        </Link>
      )}

      <div className="cal-agenda-list">
        {agendaCommunity.map((e) => (
          <article key={e.id} className="cal-event-card cal-event-card--play">
            <span className="cal-kind-tag cal-kind-tag--play">
              Community &amp; play · {dateLabel(e.day)}
            </span>
            <h3 className="mt-2 font-semibold">{e.title}</h3>
            <p className="mt-1 text-xs text-secondary">
              Optional scheduled event. Participation starts in Games.
            </p>
            <Link
              className="mt-2 inline-flex min-h-9 items-center text-xs font-bold text-link"
              to={e.url}
            >
              Open games →
            </Link>
          </article>
        ))}

        {agendaOwned.map((e) => (
          <article
            key={e.id + e.day}
            className="cal-event-card cal-event-card--own"
          >
            <span className="cal-kind-tag cal-kind-tag--own">
              {ownedKindLabel[e.kind]} · Private · {dateLabel(e.day)}
            </span>
            <h3 className="mt-2 break-words font-semibold">{e.title}</h3>
            {e.kind === "exam-target" && e.day >= today && (
              <p className="mt-1 text-xs font-bold text-secondary">
                {dayNumber(e.day) - dayNumber(today)} days to your target
              </p>
            )}
            {e.note && (
              <p className="mt-1.5 whitespace-pre-wrap break-words text-sm text-secondary">
                {e.note}
              </p>
            )}
            {e.kind === "progress-test" && e.collection_id && (
              <Link
                className="mt-2 inline-flex min-h-9 items-center text-xs font-bold text-link"
                to={"/exams/" + encodeURIComponent(e.collection_id) + "/mock"}
              >
                Start normal mock →
              </Link>
            )}
          </article>
        ))}

        {agendaOfficial.map(row)}

        {(notices || learning?.official !== false) && !agendaTotal && (
          <div className="cal-agenda-empty">
            <strong>No events scheduled</strong>
            <p>
              {onlyFollowing
                ? "No entries match your follows and filters."
                : notices
                  ? "No verified notices published yet. Check the official MPSC website."
                  : "Pick another highlighted date on the calendar or add a private study target above."}
            </p>
          </div>
        )}
      </div>
    </section>
  );

  const [filtersOpen, setFiltersOpen] = useState(false);

  return (
    <main className="finna-page cal-page">
      {/* Slim 1-row Calendar Top Bar — puts the interactive Calendar immediately above the fold */}
      <header className="cal-topbar">
        <div className="cal-topbar-left">
          <h1>{notices ? "Official MPSC Notices" : "Exam & Study Calendar"}</h1>
          {upcoming && remaining !== null ? (
            <Link
              to={"/calendar?event=" + upcoming.id}
              className="cal-next-chip"
              title={upcoming.title}
            >
              <span className="cal-next-days">
                {remaining === 0 ? "Today" : `${remaining}d`}
              </span>
              <span className="cal-next-title">{upcoming.title}</span>
            </Link>
          ) : null}
        </div>

        <div className="cal-topbar-right">
          <select
            aria-label="Calendar exam"
            className="cal-topbar-select"
            value={exam}
            onChange={(e) => change({ exam: e.target.value })}
          >
            <option value="">All exams</option>
            {exams.map((e) => (
              <option key={e.id} value={e.id}>
                {e.title}
              </option>
            ))}
          </select>

          <button
            type="button"
            className={`finna-st-btn${filtersOpen || kind || onlyFollowing ? " finna-st-btn--primary" : ""}`}
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((o) => !o)}
          >
            Filters{kind || onlyFollowing ? " •" : ""} {filtersOpen ? "⌃" : "⌄"}
          </button>

          <Link
            className="finna-st-btn"
            to={notices ? "/calendar" : "/calendar?view=notices"}
          >
            {notices ? "Calendar" : "Notices"}
          </Link>

          {!notices && (
            <button
              type="button"
              className="finna-st-btn"
              disabled={!visible.some((e) => e.starts_on)}
              onClick={() => exportCalendar(visible)}
            >
              .ics
            </button>
          )}
        </div>
      </header>

      {filtersOpen && (
        <section className="cal-filters" aria-label="Filter calendar">
          <div className="cal-filters-top">
            <div className="cal-filter-actions">
              {personal?.registered ? (
                <>
                  {exam && (
                    <button
                      type="button"
                      disabled={busy}
                      className="finna-st-btn"
                      onClick={() =>
                        void mutate("follow", {
                          collection_id: exam,
                          enabled: !personal.following.includes(exam),
                        })
                      }
                    >
                      {personal.following.includes(exam)
                        ? "Unfollow exam"
                        : "Follow exam"}
                    </button>
                  )}
                  <button
                    type="button"
                    className={
                      "finna-st-btn" +
                      (onlyFollowing ? " finna-st-btn--primary" : "")
                    }
                    aria-pressed={onlyFollowing}
                    onClick={() =>
                      change({ following: onlyFollowing ? "" : "1" })
                    }
                  >
                    Following &amp; saved
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    className={
                      "finna-st-btn" +
                      (personal.reminders ? " finna-st-btn--primary" : "")
                    }
                    aria-pressed={personal.reminders}
                    onClick={() =>
                      void mutate("reminders", { enabled: !personal.reminders })
                    }
                  >
                    {personal.reminders ? "Inbox alerts on ✓" : "Inbox alerts"}
                  </button>
                </>
              ) : (
                <Link className="finna-st-btn" to="/login">
                  Sign in for follows &amp; alerts
                </Link>
              )}
              <a
                className="finna-st-btn"
                target="_blank"
                rel="noreferrer"
                href="https://mpsc.mizoram.gov.in/"
              >
                MPSC website ↗
              </a>
            </div>
          </div>

          <div className="cal-kind-strip" role="group" aria-label="Event types">
            <button
              type="button"
              className={"cal-kind-pill" + (!kind ? " is-active" : "")}
              aria-pressed={!kind}
              onClick={() => change({ kind: "" })}
            >
              All types
            </button>
            {(Object.entries(EVENT_KINDS) as [EventKind, string][]).map(
              ([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={
                    "cal-kind-pill" + (kind === value ? " is-active" : "")
                  }
                  aria-pressed={kind === value}
                  onClick={() => change({ kind: value })}
                >
                  <i
                    aria-hidden="true"
                    style={{
                      background: kind === value ? "#FFFFFF" : KIND_DOT[value],
                    }}
                  />
                  {label}
                </button>
              ),
            )}
          </div>
        </section>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-[14px] border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark"
        >
          {error}
          <button
            type="button"
            className="ml-3 font-bold underline"
            onClick={() => setReload((n) => n + 1)}
          >
            Retry
          </button>
        </div>
      )}

      {focused && (
        <section
          className="cal-focused-card"
          aria-label="Selected official notice"
        >
          <div className="cal-agenda-eyebrow">Highlighted official notice</div>
          {row(focused)}
        </section>
      )}

      {!notices ? (
        <div className={view === "list" ? "cal-single" : "cal-split"}>
          <div className="cal-card">
            <header className="cal-card-head">
              <div className="cal-head-nav">
                <button
                  type="button"
                  className="cal-head-arrow"
                  aria-label={view === "week" ? "Previous week" : "Previous month"}
                  disabled={
                    view === "week"
                      ? addDays(weekAnchor, -7) < "2000-01-01"
                      : month === "2000-01"
                  }
                  onClick={() => move(-1)}
                >
                  ‹
                </button>
                <div className="cal-head-center">
                  <h2>
                    {view === "week"
                      ? dateLabel(start) + " – " + dateLabel(end)
                      : new Date(Date.UTC(year, mi, 1)).toLocaleDateString(
                          "en-IN",
                          {
                            month: "long",
                            year: "numeric",
                            timeZone: "UTC",
                          },
                        )}
                  </h2>
                </div>
                <button
                  type="button"
                  className="cal-head-arrow"
                  aria-label={view === "week" ? "Next week" : "Next month"}
                  disabled={
                    view === "week"
                      ? addDays(weekAnchor, 7) > "2100-12-31"
                      : month === "2100-12"
                  }
                  onClick={() => move(1)}
                >
                  ›
                </button>
              </div>

              <div className="cal-head-tools">
                <button
                  type="button"
                  onClick={jumpToday}
                  className="cal-head-today"
                >
                  Today
                </button>
                <div
                  className="cal-head-views"
                  role="group"
                  aria-label="Calendar view"
                >
                  {(["month", "week", "list"] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      className={
                        "cal-head-view" + (view === v ? " is-active" : "")
                      }
                      aria-pressed={view === v}
                      onClick={() =>
                        change({
                          view: v,
                          week: v === "week" ? selected : "",
                          month: (view === "week" ? weekAnchor : selected).slice(
                            0,
                            7,
                          ),
                        })
                      }
                    >
                      {v === "month" ? "Month" : v === "week" ? "Week" : "List"}
                    </button>
                  ))}
                </div>
              </div>
            </header>

            {view !== "list" && (
              <>
                <div className="cal-dow-row">
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                    (d, idx) => (
                      <div
                        key={d}
                        className={
                          "cal-dow" + (idx >= 5 ? " is-weekend" : "")
                        }
                      >
                        {d}
                      </div>
                    ),
                  )}
                </div>
                <div className="cal-grid">
                  {Array.from(
                    {
                      length:
                        view === "week"
                          ? 0
                          : (new Date(Date.UTC(year, mi, 1)).getUTCDay() + 6) %
                            7,
                    },
                    (_, i) => (
                      <div key={"blank" + i} className="cal-cell-blank" />
                    ),
                  )}
                  {gridDays.map((d) => {
                    const own = ownedVisible.filter((e) => e.day === d);
                    const play = communityVisible.filter((e) => e.day === d);
                    const evs = officialVisible.filter(
                      (e) =>
                        !!e.starts_on &&
                        e.starts_on <= d &&
                        (e.ends_on || e.starts_on) >= d,
                    );
                    const forecastRow = learning?.forecast
                      ? learning.data?.forecast.find((r) => r.day === d)
                      : null;
                    const hasHabit =
                      !!learning?.habit &&
                      !!learning.data?.habit.some((r) => r.day === d);
                    const totalItems = evs.length + own.length + play.length;
                    return (
                      <button
                        key={d}
                        type="button"
                        aria-label={
                          dateLabel(d) +
                          ", " +
                          totalItems +
                          " events, " +
                          (forecastRow?.count || 0) +
                          " projected reviews"
                        }
                        aria-pressed={selected === d}
                        onClick={() => setSelected(d)}
                        className={
                          "cal-cell" +
                          (selected === d ? " is-selected" : "") +
                          (d === today ? " is-today" : "") +
                          (hasHabit ? " has-habit" : "") +
                          (totalItems > 0 ? " has-events" : "")
                        }
                      >
                        <div className="cal-cell-top">
                          <span className="cal-day-num">
                            {Number(d.slice(-2))}
                          </span>
                          <span className="cal-cell-marks">
                            {hasHabit && (
                              <i
                                aria-label="Verified activity"
                                className="cal-habit-dot"
                              />
                            )}
                            {forecastRow && (
                              <span className="cal-forecast-chip">
                                ↻{forecastRow.count}
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="cal-cell-pills">
                          {evs.slice(0, 2).map((e) => (
                            <span
                              key={e.id}
                              className="cal-mini-pill"
                              style={{ borderLeftColor: KIND_DOT[e.kind] }}
                            >
                              {e.title}
                            </span>
                          ))}
                          {own.slice(0, 2).map((e) => (
                            <span
                              key={e.id}
                              className="cal-mini-pill cal-mini-pill--own"
                            >
                              {e.title}
                            </span>
                          ))}
                          {play.slice(0, 1).map((e) => (
                            <span
                              key={e.id}
                              className="cal-mini-pill cal-mini-pill--play"
                            >
                              Cup · 7 pm
                            </span>
                          ))}
                          {(evs.length > 2 || own.length > 2) && (
                            <span className="cal-more-tag">
                              +
                              {Math.max(0, evs.length - 2) +
                                Math.max(0, own.length - 2)}{" "}
                              more
                            </span>
                          )}
                        </div>
                        {totalItems > 0 && (
                          <div className="cal-mobile-dots" aria-hidden="true">
                            {evs.slice(0, 3).map((e) => (
                              <i
                                key={e.id}
                                style={{ background: KIND_DOT[e.kind] }}
                              />
                            ))}
                            {own.length > 0 && (
                              <i style={{ background: "#0A7D8C" }} />
                            )}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
                <div className="cal-card-foot">
                  <span>
                    <i className="cal-dot-habit" /> Practised day
                  </span>
                  <span>
                    <i className="cal-dot-own" /> Personal target/plan
                  </span>
                  <span>
                    <i className="cal-dot-exam" /> Official exam date
                  </span>
                  <span>↻ Projected reviews</span>
                </div>
              </>
            )}
          </div>

          <aside className="cal-agenda-col">{agendaPanel}</aside>
        </div>
      ) : (
        <div className="cal-single">{agendaPanel}</div>
      )}

      {(notices ? offset > 0 || more : total > 100) && (
        <nav aria-label="Calendar pages" className="mt-4 flex justify-between">
          <button
            className="finna-st-btn"
            disabled={offset === 0}
            onClick={() =>
              setOffset((n) => Math.max(0, n - (notices ? 20 : 100)))
            }
          >
            ← Previous
          </button>
          <span className="self-center text-xs text-secondary">
            Page {Math.floor(offset / (notices ? 20 : 100)) + 1}
          </span>
          <button
            className="finna-st-btn"
            disabled={notices ? !more : offset + 100 >= total}
            onClick={() => setOffset((n) => n + (notices ? 20 : 100))}
          >
            Next →
          </button>
        </nav>
      )}
      {!notices && (
        <section className="cal-below-layers" aria-label="Study layers and personal targets">
          <CalendarLearningLayers
            start={start}
            end={end}
            exams={exams}
            onLayers={setLearning}
          />
        </section>
      )}

      <p className="mt-5 text-xs leading-relaxed text-muted">
        Official dates are transcribed from official sources with staff
        verification notes. All dates use India time; official-date exports are
        all-day entries. Confirm exact times, eligibility and any revisions in
        the official notice.
      </p>
    </main>
  );
}
