import {currentExamScope} from '../lib/examScope'
import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { AnswerLayoutControl } from "../components/AnswerLayout";
import QuestionCard from "../components/QuestionCard";
import { MaterialCard } from "../components/MaterialDiscovery";
import { contentRequest, type MaterialItem } from "../lib/materials";
import {
  getLibraryShelf,
  getCommunityFeed,
  listQuestions,
  type ShelfDetail,
  type QuestionPage,
  type CommunityFeedResponse,
  type ListParams,
} from "../lib/api";

const INPUT =
  "min-h-11 min-w-0 rounded-[8px] border border-hairline bg-card px-3 text-[13px]";
const TABS = ["practice", "browse", "notes", "discussions"] as const;
export default function LibraryShelf() {
  const { shelfId = "" } = useParams(),
    [params, setParams] = useSearchParams();
  const raw = params.get("view") || "practice",
    view = TABS.find((v) => v === raw) || "practice";
  const offset = Math.min(
    100000,
    Math.max(0, Math.floor(Number(params.get("offset")) || 0)),
  );
  const [shelf, setShelf] = useState<ShelfDetail | null>(null),
    [page, setPage] = useState<QuestionPage | null>(null),
    [materials, setMaterials] = useState<{
      items: MaterialItem[];
      total: number;
    } | null>(null),
    [feed, setFeed] = useState<CommunityFeedResponse | null>(null);
  const [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [query, setQuery] = useState(params.get("q") || ""),
    [retry, setRetry] = useState(0);
  const filter = (key: string, value: string) =>
    setParams((p) => {
      const n = new URLSearchParams(p);
      value ? n.set(key, value) : n.delete(key);
      if (key !== "offset") n.delete("offset");
      return n;
    });
  const generation = useRef(0);
  const [authEpoch, setAuthEpoch] = useState(0);
  useEffect(() => {
    const changed = () => {
      generation.current++;
      setPage(null);
      setMaterials(null);
      setFeed(null);
      setAuthEpoch((n) => n + 1);
    };
    window.addEventListener("ism-auth-change", changed);
    return () => window.removeEventListener("ism-auth-change", changed);
  }, []);
  const key = params.toString();
  useEffect(() => {
    let live = true;
    setShelf(null);
    getLibraryShelf(shelfId)
      .then((r) => {
        if (live) setShelf(r);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [shelfId, retry]);
  useEffect(() => {
    let live = true;
    const current = ++generation.current;
    setLoading(true);
    setError("");
    setPage(null);
    setMaterials(null);
    setFeed(null);
    const timer = window.setTimeout(async () => {
      try {
        if (view === "notes") {
          const r = await contentRequest<{
            items: MaterialItem[];
            total: number;
          }>(
            "/materials?" +
              new URLSearchParams({
                shelf_id: shelfId,
                offset: String(offset),
                limit: "10",
              }),
          );
          if (live && current === generation.current) setMaterials(r);
        } else if (view === "discussions") {
          const r = await getCommunityFeed("questions", offset, "all", shelfId);
          if (live && current === generation.current) setFeed(r);
        } else {
          const filters: ListParams = {
            shelf_id: shelfId,
            pool:
              view === "browse"
                ? "all"
                : params.get("pool") === "scorable"
                  ? "scorable"
                  : "practice",
            limit: 10,
            offset,
            origin: (params.get("origin") || "paper") as ListParams["origin"],
          };
          for (const k of [
            "topic_id",
            "subtopic_id",
            "collection_id",
            "study_status",
          ] as const)
            if (params.get(k))
              (filters as Record<string, unknown>)[k] = params.get(k);
          if (params.get("q") && params.get("q")!.length >= 2)
            filters.q = params.get("q")!;
          if (params.get("year"))
            filters.year_from = filters.year_to = Number(params.get("year"));
          if (params.get("source"))
            filters.source = [params.get("source") as "official"];
          const r = await listQuestions(filters);
          if (live && current === generation.current) setPage(r);
        }
      } catch (e) {
        if (live && current === generation.current) setError((e as Error).message);
      } finally {
        if (live && current === generation.current) setLoading(false);
      }
    }, 150);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [shelfId, key, retry, authEpoch]);
  const topics =
    shelf?.topics
      .filter((t) => t.topic_id)
      .filter(
        (t, i, a) => a.findIndex((v) => v.topic_id === t.topic_id) === i,
      ) || [];
  const subtopics =
    shelf?.topics.filter(
      (t) =>
        t.subtopic_id &&
        (!params.get("topic_id") || t.topic_id === params.get("topic_id")),
    ) || [];
  const total = page?.total ?? materials?.total ?? 0,
    more = feed ? feed.has_more : offset + 10 < total;
  return (
    <main className="mx-auto max-w-shell px-4 pb-24 pt-8 sm:px-6">
      <Link
        to="/library"
        className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link"
      >
        ← Study library
      </Link>
      <div className="mt-3 border-b border-hairline pb-6">
        <div className="font-mono text-[10px] uppercase tracking-widest text-practice-dark">
          Choose a subject · keep your progress
        </div>
        {['geography','history','polity','mizoram-gk'].includes(shelfId)&&<Link to="/atlas" className="mt-3 inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 text-[13px] font-semibold text-link">Explore the Interactive Atlas →</Link>}
        <h1 className="mt-2 font-display text-[clamp(36px,6vw,54px)]">
          {shelf?.title || shelfId.replace(/-/g, " ")}
        </h1>
        <p className="mt-2 max-w-[720px] text-[15px] leading-relaxed text-secondary">
          {shelf?.description} Practise here, browse original questions or join
          their discussions. Your answers save to your account.
        </p>
      </div>
      <nav aria-label="Subject views" className="mt-5 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => filter("view", t)}
            aria-pressed={view === t}
            className={
              "min-h-11 rounded-pill px-5 text-[13px] font-semibold " +
              (view === t
                ? "bg-ink text-paper"
                : "border border-hairline bg-card")
            }
          >
            {t === "practice" ? "Practise" : t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>
      {shelfId === "current-affairs" && (
        <p className="mt-4 rounded-[10px] bg-[#F6EACB] p-4 text-[13px]">
          These are historical exam questions. Answer in the context of the
          original paper year; they do not establish today’s officeholders or
          latest facts.
        </p>
      )}
      {(view === "practice" || view === "browse") && (
        <>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              filter("q", query.trim());
            }}
            className="mt-5 flex gap-2"
          >
            <input
              type="search"
              aria-label="Search this subject"
              placeholder={"Search " + (shelf?.title || "questions")}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className={INPUT + " flex-1"}
            />
            <button className={INPUT + " font-semibold"}>Search</button>
          </form>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select
              aria-label="Choose a topic"
              className={INPUT + " max-w-full"}
              value={params.get("topic_id") || ""}
              onChange={(e) =>
                setParams((p) => {
                  const n = new URLSearchParams(p);
                  e.target.value
                    ? n.set("topic_id", e.target.value)
                    : n.delete("topic_id");
                  n.delete("subtopic_id");
                  n.delete("offset");
                  return n;
                })
              }
            >
              <option value="">All topics</option>
              {topics.map((t) => (
                <option key={t.topic_id} value={t.topic_id!}>
                  {t.topic}
                </option>
              ))}
            </select>
  <select
                  aria-label="Exam filter"
                  className={INPUT}
                  value={params.get("collection_id") || ""}
                  onChange={(e) => filter("collection_id", e.target.value)}
                >
                  <option value="">{currentExamScope()==='all'?'All exams':'All MPSC & Mizoram exams'}</option>
                  {shelf?.exams.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.title}
                    </option>
                  ))}
                </select>
          <details className="max-w-full">
              <summary className="cursor-pointer rounded-pill border border-hairline bg-card px-4 py-3 text-[13px] font-semibold">
                More filters
              </summary>
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">

                <input
                  type="number"
                  aria-label="Paper year"
                  placeholder="Paper year"
                  min={1900}
                  max={2100}
                  className={INPUT}
                  value={params.get("year") || ""}
                  onChange={(e) => filter("year", e.target.value)}
                />
                <select
                  aria-label="Question source"
                  className={INPUT}
                  value={params.get("origin") || "paper"}
                  onChange={(e) => filter("origin", e.target.value)}
                >
                  <option value="paper">Past papers</option>
                  <option value="community">
                    Reviewed community questions
                  </option>
                  <option value="all">Papers & community</option>
                </select>
                <select
                  aria-label="Answer provenance"
                  className={INPUT}
                  value={params.get("source") || ""}
                  onChange={(e) => filter("source", e.target.value)}
                >
                  <option value="">Any answer status</option>
                  <option value="official">Official answer</option>
                  <option value="key">Transcribed key</option>
                  <option value="derived">Reviewed / derived</option>
                  <option value="inferred">Unverified inferred answer</option>
                  <option value="none">No answer recorded</option>
                </select>
                <select
                  aria-label="My progress filter"
                  className={INPUT}
                  value={params.get("study_status") || "all"}
                  onChange={(e) => filter("study_status", e.target.value)}
                >
                  <option value="all">All progress</option>
                  <option value="unseen">Not attempted</option>
                  <option value="answered">Answered</option>
                  <option value="wrong">Last answer wrong</option>
                </select>
                {view === "practice" && (
                  <select
                    aria-label="Scoring pool"
                    className={INPUT}
                    value={params.get("pool") || "practice"}
                    onChange={(e) => filter("pool", e.target.value)}
                  >
                    <option value="practice">All answerable practice</option>
                    <option value="scorable">
                      Strict verified-key questions
                    </option>
                  </select>
                )}
                {subtopics.length > 0 && (
                  <select
                    aria-label="Subtopic filter"
                    className={INPUT}
                    value={params.get("subtopic_id") || ""}
                    onChange={(e) => filter("subtopic_id", e.target.value)}
                  >
                    <option value="">All subtopics</option>
                    {subtopics.map((t) => (
                      <option key={t.subtopic_id} value={t.subtopic_id!}>
                        {t.subtopic}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </details>
            <button
              className="min-h-11 px-3 text-[12px] text-link underline"
              onClick={() => {
                setParams({ view });
                setQuery("");
              }}
            >
              Clear filters
            </button>
            <span className="ml-auto text-[12px] text-muted">
              {loading
                ? "Loading…"
                : total.toLocaleString("en-IN") + " questions"}
            </span>
          </div>
          <p className="mt-3 text-[12px] text-muted">
            {view === "browse"
              ? "Includes descriptive and unkeyed questions, with original sources."
              : "Answer labels show whether a key is official or a solution is derived."}{" "}
            Topics may overlap; each question appears once.
          </p>
          <AnswerLayoutControl />
        </>
      )}
      {loading && (
        <p role="status" className="mt-6 text-[14px] text-secondary">
          Loading {view}…
        </p>
      )}
      {error && (
        <p
          role="alert"
          className="mt-5 rounded-[10px] border border-mypick p-4 text-[13px]"
        >
          {error}{" "}
          <button
            onClick={() => setRetry((n) => n + 1)}
            className="min-h-11 text-link underline"
          >
            Try again
          </button>
        </p>
      )}
      {!loading && !error && (
        <section className="mt-6">
          {page?.items.map((q) => (
            <QuestionCard key={q.id} q={q} />
          ))}
          {materials && (
            <>
              <p className="mb-4 text-[13px] text-secondary">
                Published notes linked to {shelf?.title}.{" "}
                <Link
                  to={"/studio/new?" + new URLSearchParams({ tag: shelfId })}
                  className="text-link underline"
                >
                  Create a note
                </Link>{" "}
                and add the {shelf?.title} tag.
              </p>
              <div className="grid gap-3 md:grid-cols-2">
                {materials.items.map((m) => (
                  <MaterialCard key={m.id} item={m} />
                ))}
              </div>
            </>
          )}
          {feed && (
            <>
              <p className="mb-4 text-[13px] text-secondary">
                Discussions unlock after you answer a question. Open any
                question above to ask a doubt or suggest an improvement.
              </p>
              {feed.items.map((t) => (
                <Link
                  key={t.id}
                  to={"/bank/" + t.question_id + "?discussion=" + t.id}
                  className="mb-3 block rounded-[12px] border border-hairline bg-card p-5"
                >
                  <h2 className="font-display text-[22px]">{t.question}</h2>
                  <p className="mt-2 line-clamp-3 text-[14px] text-secondary">
                    {t.body}
                  </p>
                  <span className="mt-3 block text-[12px] text-link">
                    Open discussion →
                  </span>
                </Link>
              ))}
            </>
          )}
          {(page?.items.length === 0 ||
            materials?.items.length === 0 ||
            feed?.items.length === 0) && (
            <div className="rounded-[12px] border border-hairline bg-card p-5 text-[14px] text-secondary">
              {feed
                ? "No unlocked discussions here yet. Practise a question and open its discussion."
                : materials
                  ? "No notes have been published for this subject yet."
                  : "No questions match. Clear a filter or switch to Browse to include unkeyed questions."}
            </div>
          )}
        </section>
      )}
      {!loading && !error && (offset > 0 || more) && (
        <nav
          aria-label="Subject result pages"
          className="mt-5 flex items-center justify-between gap-3"
        >
          <button
            disabled={!offset}
            className={INPUT + " disabled:opacity-40"}
            onClick={() => filter("offset", String(Math.max(0, offset - 10)))}
          >
            ← Previous
          </button>
          <span className="text-[12px] text-muted">
            Page {Math.floor(offset / 10) + 1}
          </span>
          <button
            disabled={!more}
            className={INPUT + " disabled:opacity-40"}
            onClick={() => filter("offset", String(offset + 10))}
          >
            Next →
          </button>
        </nav>
      )}
    </main>
  );
}
