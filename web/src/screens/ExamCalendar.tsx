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
const BTN =
  "inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-3 py-2 text-sm font-semibold disabled:opacity-40";
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
        className="border-b border-[#DCD3C2] py-4"
      >
        <div className="flex flex-wrap items-start gap-3">
          <span
            className={
              "rounded-pill px-2.5 py-1 font-mono text-xs uppercase tracking-wide " +
              COLORS[e.kind]
            }
          >
            {EVENT_KINDS[e.kind]}
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold">
              {e.title}
              {e.state === "archived" && (
                <span className="ml-2 text-mypick">Withdrawn</span>
              )}
            </h3>
            <p className="mt-1 text-sm text-secondary">
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
                className={BTN}
                aria-pressed={saved || false}
                onClick={() =>
                  void mutate("save", { event_id: e.id, enabled: !saved })
                }
              >
                {saved ? "Saved" : "Save notice"}
              </button>
            ) : (
              <Link className={BTN} to="/login">
                Sign in to save
              </Link>
            ))}
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-secondary">
          {e.summary}
        </p>
        <p className="mt-2 text-xs text-muted">
          {e.source_reference} · Verified {dateLabel(e.verified_on)} ·{" "}
          {e.verification_note}
        </p>
        <div className="mt-2 flex flex-wrap gap-3 text-xs font-semibold">
          <a
            className="inline-flex min-h-11 items-center text-link underline"
            href={e.source_url}
            target="_blank"
            rel="noreferrer"
          >
            Official source ↗
          </a>
          {e.collection_id && (
            <Link
              className="inline-flex min-h-11 items-center text-link"
              to={"/exams/" + e.collection_id}
            >
              Exam practice →
            </Link>
          )}
          {e.starts_on && e.state === "published" && (
            <>
              <a
                className="inline-flex min-h-11 items-center text-link"
                href={googleCalendar(e)}
                target="_blank"
                rel="noreferrer"
              >
                Add to Google Calendar ↗
              </a>
              {personal?.registered&&e.kind==='exam'&&!notices&&<button className="min-h-11 text-link" onClick={()=>window.dispatchEvent(new CustomEvent('ism-calendar-target',{detail:{date:e.starts_on,title:e.title,collection_id:e.collection_id}}))}>Use as my target</button>}
              <button
                className="min-h-11 text-link"
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
  return (
    <main className="mx-auto max-w-shell px-4 pb-24 pt-9 sm:px-6">
      <div className="font-mono text-xs uppercase tracking-[.1em] text-[#7E4A00]">
        {notices ? "Official notices" : "Plan your study"}
      </div>
      <h1 className="mt-2 font-display text-[clamp(34px,5vw,50px)] font-medium leading-tight">
        {notices ? "From the Commission" : "Your helper calendar"}
      </h1>
      <p className="mt-3 max-w-[720px] text-md leading-relaxed text-secondary">
        {notices?'MPSC notifications, last dates, admit cards, exams, answer keys and results.':'Official exam dates, your targets and private study plans in one place. Choose the layers you want to see.'}
      </p>
      <div className="mt-3 flex flex-wrap gap-4 text-sm font-semibold">
        <Link
          className="min-h-11 py-3 text-link underline"
          to={notices ? "/calendar" : "/news"}
        >
          {notices ? "Open exam calendar →" : "Read official notices →"}
        </Link>
        <a
          className="min-h-11 py-3 text-link underline"
          target="_blank"
          rel="noreferrer"
          href="https://mpsc.mizoram.gov.in/"
        >
          MPSC website ↗
        </a>
      </div>
      {!notices&&<CalendarLearningLayers start={start} end={end} exams={exams} onLayers={setLearning}/>}
      <div className="mt-4 flex flex-wrap items-stretch gap-5">
        <section className="flex-[1_1_300px] rounded-[10px] bg-ink p-[22px] text-paper">
          <div className="font-mono text-xs uppercase tracking-wider text-[#D8A33A]">
            Following
          </div>
          <h2 className="mt-2 font-display text-xl">
            {upcoming?.title || "Your next exam date"}
          </h2>
          {upcoming && remaining !== null ? (
            <>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-display text-3xl leading-none">
                  {remaining}
                </span>
                <span>
                  {remaining === 0 ? "today / in progress" : "days"} ·{" "}
                  {dateLabel(upcoming.starts_on!)}
                </span>
              </div>
              <Link
                className="mt-3 inline-flex min-h-11 items-center text-sm underline"
                to={"/calendar?event=" + upcoming.id}
              >
                Read notice →
              </Link>
            </>
          ) : (
            <p className="mt-3 text-sm text-[#D9D0BF]">
              {personal?.following.length || personal?.saved.length
                ? "No upcoming verified date for your followed exams or saved notices."
                : "Follow an exam or save a dated notice to see your countdown here."}
            </p>
          )}
        </section>
        <section className="flex-[2_1_420px]">
          <label className="block text-sm font-semibold">
            Exam
            <select
              aria-label="Calendar exam"
              value={exam}
              onChange={(e) => change({ exam: e.target.value })}
              className="mt-2 min-h-11 w-full rounded-[6px] border border-hairline bg-card px-3"
            >
              <option value="">All exams</option>
              {exams.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.title}
                </option>
              ))}
            </select>
          </label>
          <div
            className="mt-3 flex flex-wrap gap-2"
            role="group"
            aria-label="Event types"
          >
            <button
              className={BTN + (!kind ? " bg-ink text-paper" : "")}
              aria-pressed={!kind}
              onClick={() => change({ kind: "" })}
            >
              All types
            </button>
            {Object.entries(EVENT_KINDS).map(([value, label]) => (
              <button
                key={value}
                className={BTN + (kind === value ? " bg-ink text-paper" : "")}
                aria-pressed={kind === value}
                onClick={() => change({ kind: value })}
              >
                {label}
              </button>
            ))}
          </div>
          {personal?.registered ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {exam && (
                <button
                  disabled={busy}
                  className={BTN}
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
                className={BTN}
                aria-pressed={onlyFollowing}
                onClick={() => change({ following: onlyFollowing ? "" : "1" })}
              >
                Following & saved
              </button>
              <button
                disabled={busy}
                className={BTN}
                aria-pressed={personal.reminders}
                onClick={() =>
                  void mutate("reminders", { enabled: !personal.reminders })
                }
              >
                {personal.reminders
                  ? "Inbox reminders on"
                  : "Enable inbox reminders"}
              </button>
            </div>
          ) : (
            <Link className={BTN + " mt-3"} to="/login">
              Sign in for follows & reminders
            </Link>
          )}
          <p className="mt-2 text-xs text-muted">
            Optional inbox alerts for updates and 7 days, 1 day and the day of a
            date. No email or push delivery. Existing exam bookmarks are your
            follows.
          </p>
        </section>
      </div>
      {error && (
        <div
          role="alert"
          className="mt-4 rounded-panel border border-mypick p-3 text-sm text-mypick"
        >
          {error}
          <button
            className="ml-3 underline"
            onClick={() => setReload((n) => n + 1)}
          >
            Retry
          </button>
        </div>
      )}
      {focused && (
        <section
          className="mt-6 rounded-[10px] border border-ink bg-card p-5"
          aria-label="Selected official notice"
        >
          <h2 className="font-display text-xl">Official notice</h2>
          {row(focused)}
        </section>
      )}
      {!notices && (
        <>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-1" role="group" aria-label="Calendar view">
              {(["month", "week", "list"] as const).map((v) => (
                <button
                  key={v}
                  className={BTN + (view === v ? " bg-ink text-paper" : "")}
                  aria-pressed={view === v}
                  onClick={() => change({ view: v,week:v==='week'?selected:'',month:(view==='week'?weekAnchor:selected).slice(0,7) })}
                >
                  {v === "month" ? "Month" : v === "week" ? "Week" : "List"}
                </button>
              ))}
            </div>
            <button
              className={BTN}
              disabled={!visible.some((e) => e.starts_on)}
              onClick={() => exportCalendar(visible)}
            >
              Export official dates (.ics)
            </button>
          </div>
          <div className="mt-4 overflow-hidden rounded-[10px] border border-ink bg-[#FBF8F1]">
            <div className="flex items-center justify-between gap-2 border-b border-ink px-4 py-3">
              <button
                className={BTN}
                aria-label={view==='week'?'Previous week':'Previous month'}
                disabled={view==='week'?addDays(weekAnchor,-7)<'2000-01-01':month==='2000-01'}
                onClick={() => move(-1)}
              >
                ‹
              </button>
              <h2 className="font-display text-xl">
                {view==='week'?dateLabel(start)+' – '+dateLabel(end):new Date(Date.UTC(year, mi, 1)).toLocaleDateString("en-IN", {
                  month: "long",
                  year: "numeric",
                  timeZone: "UTC",
                })}
              </h2>
              <button
                className={BTN}
                aria-label={view==='week'?'Next week':'Next month'}
                disabled={view==='week'?addDays(weekAnchor,7)>'2100-12-31':month==='2100-12'}
                onClick={() => move(1)}
              >
                ›
              </button>
            </div>
            {view !== "list" && (
              <>
                <div className="grid grid-cols-7 border-b border-hairline">
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                    (d) => (
                      <div
                        key={d}
                        className="py-2 text-center font-mono text-xs uppercase text-muted"
                      >
                        {d}
                      </div>
                    ),
                  )}
                </div>
                <div className="grid grid-cols-7">
                  {Array.from(
                    {
                      length:
                        view==='week'?0:(new Date(Date.UTC(year, mi, 1)).getUTCDay() + 6) % 7,
                    },
                    (_, i) => (
                      <div
                        key={"blank" + i}
                        className="border-b border-r border-hairline bg-paper/50"
                      />
                    ),
                  )}
                  {gridDays.map(d => {
                    const own=ownedVisible.filter(e=>e.day===d);
                    const play=communityVisible.filter(e=>e.day===d);
                    const evs = officialVisible.filter(
                      (e) =>
                        !!e.starts_on &&
                        e.starts_on <= d &&
                        (e.ends_on || e.starts_on) >= d,
                    );
                    return (
                      <button
                        key={d}
                        type="button"
                        aria-label={
                          dateLabel(d) + ", " + (evs.length+own.length+play.length) + " events, "+(learning?.forecast?learning.data?.forecast.find(r=>r.day===d)?.count||0:0)+" projected reviews"
                        }
                        aria-pressed={selected === d}
                        onClick={() => setSelected(d)}
                        className={
                          "flex min-h-[72px] min-w-0 flex-col items-start overflow-hidden border-b border-r border-hairline p-1.5 text-left sm:min-h-[106px] " +
                          (selected === d ? "bg-[#E3E9F8]" : "")
                        }
                      >
                        {learning?.forecast&&learning.data?.forecast.some(r=>r.day===d)&&<span className="text-xs font-bold text-link">↻ {learning.data.forecast.find(r=>r.day===d)?.count}</span>}
                        {learning?.habit&&learning.data?.habit.some(r=>r.day===d)&&<span aria-label="Verified activity" className="text-xs text-learn-dark">●</span>}
                        <span
                          className={
                            "grid h-6 w-6 place-items-center rounded-full text-xs " +
                            (d === today ? "bg-ink text-paper" : "")
                          }
                        >
                          {Number(d.slice(-2))}
                        </span>
                        {evs.slice(0, 2).map((e) => (
                          <span
                            key={e.id}
                            className={
                              "mt-1 block w-full truncate rounded-[4px] px-1 py-0.5 text-xs font-semibold " +
                              COLORS[e.kind]
                            }
                          >
                            {e.title}
                          </span>
                        ))}
                        {own.slice(0,2).map(e=><span key={e.id} className="mt-1 block w-full truncate rounded bg-learn-soft px-1 py-0.5 text-xs font-semibold text-learn-dark">{e.title}</span>)}
                        {play.slice(0,1).map(e=><span key={e.id} className="mt-1 block w-full truncate rounded bg-play-soft px-1 py-0.5 text-xs font-semibold text-ink">Cup · 7 pm</span>)}
                        {(evs.length>2||own.length>2) && (
                          <span className="text-xs">
                            +{Math.max(0,evs.length-2)+Math.max(0,own.length-2)} more
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </>
      )}
      {loading ? (
        <p role="status" className="mt-5 text-sm text-muted">
          Loading official entries…
        </p>
      ) : (
        <section className="mt-5 border-t border-ink pt-3">
          <h2 className="font-display text-xl">
            {notices
              ? "Latest verified notices"
              : view === "list"
                ? "Dates this month"
                : dateLabel(selected)}
          </h2>
          {!notices&&learning?.forecast&&learning.data?.forecast.some(r=>r.day===selected)&&<Link to={'/revise?'+new URLSearchParams({through:selected,exam_scope:'all'})} className="my-3 inline-flex min-h-11 items-center rounded-xl bg-learn-soft px-4 text-sm font-bold text-link">{learning.data.forecast.find(r=>r.day===selected)?.count} projected reviews · Review this day →</Link>}
          {!notices&&communityVisible.filter(e=>view==='list'||e.day===selected).map(e=><article key={e.id} className="border-b border-hairline py-4"><p className="text-xs font-semibold text-secondary">Community & play · {dateLabel(e.day)}</p><h3 className="mt-1 font-semibold">{e.title}</h3><Link className="mt-1 inline-flex min-h-11 items-center text-sm font-bold text-link" to={e.url}>Open games →</Link><p className="text-xs text-secondary">An optional scheduled event. Participation starts in Games.</p></article>)}
          {!notices&&ownedVisible.filter(e=>view==='list'||e.day===selected).map(e=><article key={e.id+e.day} className="min-w-0 border-b border-hairline py-4"><p className="text-xs font-semibold text-learn-dark">{ownedKindLabel[e.kind]} · Private · {dateLabel(e.day)}</p><h3 className="mt-1 break-words font-semibold">{e.title}</h3>{e.kind==='exam-target'&&e.day>=today&&<p className="mt-1 text-sm text-secondary">{dayNumber(e.day)-dayNumber(today)} days to your target</p>}{e.note&&<p className="mt-2 whitespace-pre-wrap break-words text-sm text-secondary">{e.note}</p>}{e.kind==='progress-test'&&e.collection_id&&<Link className="mt-2 inline-flex min-h-11 items-center text-sm font-bold text-link" to={'/exams/'+encodeURIComponent(e.collection_id)+'/mock'}>Start normal mock →</Link>}</article>)}
          {(notices || view === "list"
            ? (notices?visible:officialVisible)
            : officialVisible.filter(
                (e) =>
                  !!e.starts_on &&
                  e.starts_on <= selected &&
                  (e.ends_on || e.starts_on) >= selected,
              )
          ).map(row)}
          {(notices||learning?.official!==false)&&!(
            notices || view === "list"
              ? (notices?visible:officialVisible)
              : officialVisible.filter(
                  (e) =>
                    !!e.starts_on &&
                    e.starts_on <= selected &&
                    (e.ends_on || e.starts_on) >= selected,
                )
          ).length && (
            <p className="py-5 text-sm text-secondary">
              {onlyFollowing
                ? "No entries match your follows and filters."
                : notices
                  ? "No verified notices published yet. Check the official MPSC website."
                  : "No verified events for this selection. Dates will appear after staff check the official notice."}
            </p>
          )}
        </section>
      )}
      {(notices ? offset > 0 || more : total > 100) && (
        <nav aria-label="Calendar pages" className="mt-4 flex justify-between">
          <button
            className={BTN}
            disabled={offset === 0}
            onClick={() =>
              setOffset((n) => Math.max(0, n - (notices ? 20 : 100)))
            }
          >
            Previous
          </button>
          <span className="self-center text-xs">
            Page {Math.floor(offset / (notices ? 20 : 100)) + 1}
          </span>
          <button
            className={BTN}
            disabled={notices ? !more : offset + 100 >= total}
            onClick={() => setOffset((n) => n + (notices ? 20 : 100))}
          >
            Next
          </button>
        </nav>
      )}
      <p className="mt-5 text-xs leading-relaxed text-muted">
        Official dates are transcribed from official sources with staff verification
        notes. All dates use India time; official-date exports are all-day entries.
        Confirm exact times, eligibility and any revisions in the official
        notice. Saved external calendar copies do not update automatically.
      </p>
    </main>
  );
}
