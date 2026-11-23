import "../styles/exam-experience.css";
import { choosePreferredExam } from "../lib/preferredExam";
import { MES_GUIDE } from "../lib/examGuideCatalog";
import { examPresentation, examCatalogLayout } from "../lib/examPresentation";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Pagination from "../components/Pagination";
import { pageNumber, scrollToResults } from "../lib/pagination";
import {
  getExamBookmarks,
  getExamProgress,
  isLaterExamCollection,
  listCollections,
  removeExamBookmark,
  saveExamBookmark,
  type Collection,
  type ExamProgressSummary,
} from "../lib/api";

type Filter = "all" | "saved";
type CatalogEntry =
  | { type: "collection"; collection: Collection }
  | { type: "guide"; id: "mes" };
const PAGE_SIZE = 8;
const ALIASES: Record<string, string[]> = {
  ldc: ["ldc", "lower division clerk"],
  udc: ["udc", "upper division clerk"],
  prelims: ["prelims", "preliminary", "combined prelims"],
  mpsc: ["mpsc", "mizoram public service commission"],
  gazetted: ["gazetted", "gazette", "group b"],
  gazette: ["gazetted", "gazette", "group b"],
  nongazetted: ["non gazetted", "non-gazetted", "ldc", "udc"],
  assistant: ["assistant", "assistant grade", "assistant audit"],
};
const PHRASES: Record<string, string[]> = {
  "non gazetted": ["non gazetted", "ldc", "udc"],
  "group b": ["group b", "gazetted"],
  "combined prelims": ["combined prelims", "preliminary"],
  "lower division clerk": ["lower division clerk", "ldc"],
  "upper division clerk": ["upper division clerk", "udc"],
};
const examShort = (id: string, fallback: string) =>
  ({
    udc: "UDC",
    ldc: "LDC",
    assistant: "Assistant",
    "combined-prelims": "Combined Prelims",
    "group-b-gazetted": "Group B Gazetted",
    "group-b-non-gazetted": "Group B Non-Gazetted",
    "iti-instructor-2026": "ITI Instructor",
  })[id] || fallback;
const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
function matches(text: string, query: string) {
  const terms = norm(query).split(" ").filter(Boolean);
  const target = norm(text);
  const groups: string[][] = [];
  for (let i = 0; i < terms.length; ) {
    const phrase = Object.keys(PHRASES)
      .sort((a, b) => b.length - a.length)
      .find(
        (p) => terms.slice(i, i + p.split(" ").length).join(" ") === p,
      );
    if (phrase) {
      groups.push(PHRASES[phrase]);
      i += phrase.split(" ").length;
    } else {
      groups.push(ALIASES[terms[i]] ?? [terms[i]]);
      i++;
    }
  }
  return groups.every((g) => g.some((alias) => target.includes(norm(alias))));
}

export default function Exams() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [progress, setProgress] = useState<Record<string, ExamProgressSummary>>(
    {},
  );
  const [bookmarks, setBookmarks] = useState<string[]>([]);
  const [busyBookmark, setBusyBookmark] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();
  const filter: Filter =
    params.get("exam_filter") === "saved" ? "saved" : "all";
  const query = params.get("q") || "";
  const page = pageNumber(params.get("page")) - 1;
  function filterURL(key: string, value: string) {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        if (value) next.set(key, value);
        else next.delete(key);
        next.delete("page");
        return next;
      },
      { replace: true },
    );
  }
  const setFilter = (value: Filter) =>
    filterURL("exam_filter", value === "all" ? "" : value);
  const setQuery = (value: string) => filterURL("q", value);
  const goPage = (value: number) => {
    setParams((previous) => {
      const next = new URLSearchParams(previous);
      if (value > 1) next.set("page", String(value));
      else next.delete("page");
      return next;
    });
    requestAnimationFrame(() => scrollToResults("exam-library-heading"));
  };
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let live = true;
    setLoading(true);
    setCatalogError(false);
    setError(null);
    listCollections()
      .then((all) => {
        if (!live) return;
        const order = [
          "udc",
          "ldc",
          "combined-prelims",
          "group-b-gazetted",
          "group-b-non-gazetted",
          "assistant",
        ];
        const rank = (id: string) => {
          const i = order.indexOf(id);
          return i < 0 ? 99 : i;
        };
        const available = all
          .filter((c) => c.kind === "exam" && !isLaterExamCollection(c))
          .sort((a, b) => rank(a.id) - rank(b.id));
        setCollections(available);
        setLoading(false);
      })
      .catch((e) => {
        if (live) {
          setError(e.message);
          setCatalogError(true);
          setLoading(false);
        }
      });
    Promise.all([getExamBookmarks(), getExamProgress()])
      .then(([saved, rows]) => {
        if (!live) return;
        setBookmarks(saved.collection_ids);
        setProgress(
          Object.fromEntries(rows.map((row) => [row.collection_id, row])),
        );
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [retry]);

  const mesVisible =
    filter === "all" &&
    !collections.some((c) => c.id === "mes") &&
    matches(MES_GUIDE.title + " " + MES_GUIDE.search, query);
  const shown = useMemo<CatalogEntry[]>(() => {
    const entries: CatalogEntry[] = collections
      .filter((c) => {
        const isSaved = bookmarks.includes(c.id);
        const typeMatch = filter === "all" || isSaved;
        return typeMatch && matches(`${c.title} ${c.id} ${c.kind}`, query);
      })
      .map((collection) => ({ type: "collection", collection }));
    return mesVisible ? [{ type: "guide", id: "mes" }, ...entries] : entries;
  }, [collections, bookmarks, filter, query, mesVisible]);
  const pages = Math.ceil(shown.length / PAGE_SIZE);
  const visible = shown.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  useEffect(() => {
    if (!loading && page >= Math.max(1, pages))
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          if (pages > 1) next.set("page", String(pages));
          else next.delete("page");
          return next;
        },
        { replace: true },
      );
  }, [loading, page, pages, setParams]);

  async function toggleBookmark(c: Collection) {
    const wasSaved = bookmarks.includes(c.id);
    setBusyBookmark(c.id);
    setBookmarks((old) =>
      wasSaved ? old.filter((id) => id !== c.id) : [c.id, ...old],
    );
    try {
      if (wasSaved) await removeExamBookmark(c.id);
      else await saveExamBookmark(c.id);
    } catch (e) {
      setBookmarks((old) =>
        wasSaved ? [...old, c.id] : old.filter((id) => id !== c.id),
      );
      setError(
        e instanceof Error
          ? `Could not update saved exams: ${e.message}`
          : "Could not update saved exams.",
      );
    } finally {
      setBusyBookmark(null);
    }
  }

  const layout = examCatalogLayout(params.get("exam_layout"));
  const expanded = params.get("exam_open") || "";
  function expand(id: string) {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        if (next.get("exam_open") === id) next.delete("exam_open");
        else next.set("exam_open", id);
        return next;
      },
      { replace: true },
    );
  }
  const compared = (params.get("compare") || "")
    .split(",")
    .filter((id) => collections.some((c) => c.id === id))
    .slice(0, 3);
  const comparison = collections.filter((c) => compared.includes(c.id));
  function toggleCompare(id: string) {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        const ids = compared.includes(id)
          ? compared.filter((x) => x !== id)
          : [...compared, id].slice(0, 3);
        if (ids.length) next.set("compare", ids.join(","));
        else next.delete("compare");
        return next;
      },
      { replace: true },
    );
  }
  const savedCount = bookmarks.filter((id) =>
    collections.some((c) => c.id === id),
  ).length;

  return (
    <div className="ex-shell" data-screen="exams">
      <header className="av-hero ex-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">Question booklets · Verified bank</span>
          <h1>Choose your exam</h1>
          <p>
            Archival past papers, official keys, subjects and timed practice —
            packaged as exam booklets with live coverage tracking.
          </p>
        </div>
        <div className="av-hero-actions">
          <Link to="/library" className="cr-glass-btn">
            Subject library
          </Link>
          <Link to="/desk" className="cr-glass-btn cr-glass-btn--accent">
            My study desk ↗
          </Link>
        </div>
      </header>

      <section aria-labelledby="exam-library-heading" className="ex-section">
            <div className="ex-toolbar">
              <label className="at-field ex-search">
                <span className="sr-only">Search exam collections</span>
                <input
                  id="exam-search"
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Find MES, UDC, LDC, Assistant, Prelims…"
                />
              </label>
              <div className="ex-toolbar-pills">
                <div className="av-tabs" role="group" aria-label="Filter exams">
                  {(
                    [
                      ["all", "All exams"],
                      ["saved", "Saved"],
                    ] as const
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      className={`av-tab${filter === key ? " is-active" : ""}`}
                      onClick={() => setFilter(key)}
                      aria-pressed={filter === key}
                    >
                      {label}
                      {key === "saved" ? (
                        <span className="av-tab-count">{savedCount}</span>
                      ) : null}
                    </button>
                  ))}
                </div>
                <div
                  className="av-tabs"
                  role="group"
                  aria-label="Exam display"
                >
                  {(["cards", "list"] as const).map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={`av-tab${layout === value ? " is-active" : ""}`}
                      aria-pressed={layout === value}
                      onClick={() => filterURL("exam_layout", value)}
                    >
                      {value === "cards" ? "Booklets" : "List"}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="ex-results-head">
              <h2
                id="exam-library-heading"
                tabIndex={-1}
                className="scroll-mt-28"
              >
                {filter === "saved" ? "Your saved exams" : "Exam booklets"}
              </h2>
              <span role="status" className="finna-st-pill finna-st-pill--gray">
                {loading ? "Loading…" : `${shown.length} available`}
              </span>
            </div>

            {error && (
              <div role="status" className="at-inline-err">
                {error}
                {catalogError ? (
                  <button
                    type="button"
                    onClick={() => setRetry((n) => n + 1)}
                    className="ml-2 font-bold underline"
                  >
                    Retry exams
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setError(null)}
                    className="ml-2 font-bold underline"
                  >
                    Dismiss
                  </button>
                )}
              </div>
            )}

            {loading && (
              <div className="ex-grid" aria-label="Loading exams">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-72 animate-pulse rounded-[16px] border border-hairline bg-card"
                  />
                ))}
              </div>
            )}

            {!loading && visible.length > 0 && (
              <div className="ex-grid" data-layout={layout}>
                {visible.map((entry) => {
                  if (entry.type === "guide")
                    return (
                      <MesExamCard
                        key={entry.id}
                        open={expanded === entry.id}
                        onExpand={() => expand(entry.id)}
                      />
                    );
                  const c = entry.collection;
                  const p = progress[c.id];
                  const saved = bookmarks.includes(c.id);
                  const identity = examPresentation(c.id);
                  const open = expanded === c.id;
                  const completion =
                    p && c.questions
                      ? Math.min(
                          100,
                          Math.round((100 * p.unique_questions) / c.questions),
                        )
                      : 0;
                  const isCompared = compared.includes(c.id);

                  return (
                    <article
                      key={c.id}
                      className={`ex-paper-card ex-tone-${identity.tone}`}
                      data-exam-tone={identity.tone}
                    >
                      {/* Paper Masthead Header (double-ruled exam booklet cover) */}
                      <div className="ex-paper-masthead">
                        <div className="ex-paper-series">
                          <span className="ex-series-stamp">
                            {identity.short}
                          </span>
                          <div className="ex-series-meta">
                            <span className="ex-series-code">
                              BOOKLET · {identity.short}
                            </span>
                            <span className="ex-series-cat">
                              {identity.category}
                            </span>
                          </div>
                        </div>
                        <button
                          type="button"
                          className={`ex-paper-save${saved ? " is-saved" : ""}`}
                          disabled={busyBookmark !== null}
                          onClick={() => void toggleBookmark(c)}
                          aria-pressed={saved}
                          aria-label={`${saved ? "Remove" : "Save"} ${c.title} ${saved ? "from" : "to"} saved exams`}
                        >
                          {saved ? "★ Saved" : "☆ Save"}
                        </button>
                      </div>

                      {/* Paper Sheet Body with subtle left ruled margin */}
                      <div className="ex-paper-body">
                        <Link
                          className="ex-title-link"
                          onClick={() => choosePreferredExam(c.id)}
                          to={`/exams/${c.id}`}
                        >
                          <h3>{examShort(c.id, c.title)}</h3>
                          <p>{c.title}</p>
                        </Link>

                        <div className="ex-meter-block">
                          <div className="ex-meter-head">
                            <span>
                              {p
                                ? `${p.unique_questions.toLocaleString("en-IN")} answered`
                                : "Ready to practise"}
                            </span>
                            <strong>{completion}% covered</strong>
                          </div>
                          <div
                            className="ex-meter-track"
                            role="progressbar"
                            aria-label={`${c.title} coverage`}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-valuenow={completion}
                          >
                            <span style={{ width: `${completion}%` }} />
                          </div>
                        </div>

                        <div className="ex-actions">
                          <Link
                            className="ex-open-btn"
                            onClick={() => choosePreferredExam(c.id)}
                            to={`/exams/${c.id}`}
                          >
                            Open booklet →
                          </Link>
                          <button
                            type="button"
                            className={`finna-st-btn${isCompared ? " finna-st-btn--primary" : ""}`}
                            aria-pressed={isCompared}
                            disabled={compared.length >= 3 && !isCompared}
                            onClick={() => toggleCompare(c.id)}
                            aria-label={`Compare ${c.title}`}
                          >
                            {isCompared ? "Added" : "Compare"}
                          </button>
                          <button
                            type="button"
                            className="ex-options-toggle"
                            aria-expanded={open}
                            aria-controls={"exam-options-" + c.id}
                            aria-label={`${open ? "Hide" : "Show"} study options for ${c.title}`}
                            onClick={() => expand(c.id)}
                          >
                            Options {open ? "⌃" : "⌄"}
                          </button>
                        </div>

                        <div
                          id={"exam-options-" + c.id}
                          hidden={!open}
                          className="ex-options-drawer"
                        >
                          <nav aria-label={`${c.title} study options`}>
                            <Link
                              to={`/exams/${c.id}?view=browse#exam-question-browser`}
                            >
                              Questions
                            </Link>
                            <Link
                              to={`/exams/${c.id}?view=topics#exam-study-heading`}
                            >
                              Subjects &amp; topics
                            </Link>
                            <Link
                              to={`/exams/${c.id}?view=papers#past-paper-results`}
                            >
                              Original papers
                            </Link>
                            <Link
                              to={`/exams/${c.id}?view=practice#exam-question-browser`}
                            >
                              Open practice →
                            </Link>
                          </nav>
                        </div>
                      </div>

                      {/* Framed Exam Rubric Footer Box (3-col inventory strip) */}
                      <div className="ex-rubric-bar">
                        <div className="ex-rubric-cell">
                          <strong>{c.questions.toLocaleString("en-IN")}</strong>
                          <span>Questions</span>
                        </div>
                        <div className="ex-rubric-cell">
                          <strong>{c.scorable.toLocaleString("en-IN")}</strong>
                          <span>Official Key</span>
                        </div>
                        <div className="ex-rubric-cell">
                          <strong>{c.sections}</strong>
                          <span>
                            {c.sections === 1 ? "Section" : "Sections"}
                          </span>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}

            {!loading && !catalogError && !visible.length && (
              <div className="at-card text-center">
                <div className="font-display text-lg font-bold">
                  {filter === "saved"
                    ? "No saved exams match"
                    : "No matching exams"}
                </div>
                <p className="text-sm text-secondary">
                  {filter === "saved"
                    ? "Save an exam with the Save button, or clear your search to see all saved exams."
                    : "Try a shorter search or clear the selected filter."}
                </p>
                {(filter === "saved" || query) && (
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={() => {
                        setParams((previous) => {
                          const next = new URLSearchParams(previous);
                          next.delete("q");
                          next.delete("exam_filter");
                          next.delete("page");
                          return next;
                        });
                      }}
                      className="cr-primary-btn"
                    >
                      Clear filters
                    </button>
                  </div>
                )}
              </div>
            )}

            <Pagination
              page={page + 1}
              pages={pages}
              disabled={loading}
              onPageChange={goPage}
              label="Exam collection pages"
            />
          </section>

          {comparison.length > 0 && (
            <section
              className="at-card mt-5 overflow-x-auto"
              aria-labelledby="compare-exams"
            >
              <div className="at-card-head">
                <div>
                  <h2 id="compare-exams">Compare exams</h2>
                  <p>
                    {comparison.length} of 3 selected · live bank inventory
                  </p>
                </div>
              </div>
              <table className="w-full min-w-[500px] text-left text-sm">
                <thead>
                  <tr>
                    <th className="py-3 pr-4">In the bank</th>
                    {comparison.map((c) => (
                      <th key={c.id} className="px-4 py-3 text-exams-dark">
                        {examShort(c.id, c.title)}
                        <button
                          type="button"
                          onClick={() => toggleCompare(c.id)}
                          aria-label={"Remove " + c.title + " from comparison"}
                          className="ml-2 inline-grid min-h-9 min-w-9 place-items-center text-secondary"
                        >
                          ×
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Sections", (c: Collection) => c.sections],
                    ["Questions", (c: Collection) => c.questions],
                    ["Official-key questions", (c: Collection) => c.scorable],
                    [
                      "Questions attempted",
                      (c: Collection) =>
                        progress[c.id]?.unique_questions ?? "—",
                    ],
                  ].map(([label, value]) => (
                    <tr key={String(label)} className="border-t border-hairline">
                      <th className="py-3 pr-4 font-semibold text-secondary">
                        {String(label)}
                      </th>
                      {comparison.map((c) => (
                        <td key={c.id} className="px-4 py-3">
                          {typeof value === "function"
                            ? value(c).toLocaleString("en-IN")
                            : ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          <section
            aria-label="Group B common subjects"
            className="at-trial-banner mt-5"
          >
            <div>
              <strong>Study across Group B exams</strong>
              <p>Common subjects or technical papers across Gazetted tracks.</p>
            </div>
            <div className="at-btn-row">
              <Link className="finna-st-btn" to="/exams/group-b-gazetted">
                English &amp; GK/GS →
              </Link>
              <Link
                className="finna-st-btn"
                to="/exams/group-b-gazetted?study_area=technical"
              >
                Technical papers →
              </Link>
            </div>
          </section>
    </div>
  );
}

function MesExamCard({
  open,
  onExpand,
}: {
  open: boolean;
  onExpand: () => void;
}) {
  return (
    <article
      className="ex-paper-card ex-tone-amber"
      data-exam-tone="amber"
      aria-label={MES_GUIDE.title}
    >
      <div className="ex-paper-masthead">
        <div className="ex-paper-series">
          <span className="ex-series-stamp">MES</span>
          <div className="ex-series-meta">
            <span className="ex-series-code">GUIDE · 2013 REG</span>
            <span className="ex-series-cat">Engineering Service</span>
          </div>
        </div>
        <span className="ex-paper-save is-saved">★ Guide</span>
      </div>

      <div className="ex-paper-body">
        <Link className="ex-title-link" to="/exams/mes">
          <h3>MES</h3>
          <p>{MES_GUIDE.title}</p>
        </Link>

        <p className="ex-mes-blurb">
          Choose your engineering branch and regulations to explore syllabus
          checklists and source-linked past papers.
        </p>

        <div className="ex-actions">
          <Link className="ex-open-btn" to="/exams/mes">
            Open MES →
          </Link>
          <button
            type="button"
            className="ex-options-toggle"
            aria-expanded={open}
            aria-controls="exam-options-mes"
            aria-label={`${open ? "Hide" : "Show"} study options for Mizoram Engineering Service (MES)`}
            onClick={onExpand}
          >
            Options {open ? "⌃" : "⌄"}
          </button>
        </div>

        <div id="exam-options-mes" hidden={!open} className="ex-options-drawer">
          <nav aria-label="MES study options">
            <Link to="/exams/mes?view=browse">Questions</Link>
            <Link to="/exams/mes?view=topics">Subjects &amp; syllabus</Link>
            <Link to="/exams/mes?view=papers">Original papers</Link>
            <Link to="/exams/mes?view=practice">Open practice →</Link>
          </nav>
        </div>
      </div>

      <div className="ex-rubric-bar">
        <div className="ex-rubric-cell">
          <strong>{MES_GUIDE.branchCount}</strong>
          <span>Branches</span>
        </div>
        <div className="ex-rubric-cell">
          <strong>{MES_GUIDE.paperCount}</strong>
          <span>Papers</span>
        </div>
        <div className="ex-rubric-cell">
          <strong>2</strong>
          <span>Schemes</span>
        </div>
      </div>
    </article>
  );
}
