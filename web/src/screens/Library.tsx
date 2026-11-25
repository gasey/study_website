import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  getExamProgress,
  isSubjectModule,
  listCollections,
  listLibraryShelves,
  type Collection,
  type ExamProgressSummary,
  type LibraryShelf,
  listTaxonomy,
  type TaxonomyFacet,
} from "../lib/api";
import { SITE_MAP, destinationPath } from "../lib/siteMap";
import MaterialDiscovery from "../components/MaterialDiscovery";
import ConceptBook, { bookToneFor } from "../components/ConceptBook";
import SubjectBookshelf from "../components/SubjectBookshelf";

const Materials = lazy(() => import("./Materials"));

const VIEWS = [
  ["subjects", "Subjects"],
  ["reading", "From the community"],
  ["saved", "Saved"],
] as const;

const FEATURED_STUDY_TOOLS = [
  {
    title: "Concept Guides (11)",
    href: "/guides",
    tag: "Reading room",
    label: "Edited Polity, Computer, Science, Economy, Maths, Reasoning & English guides linked to bank questions.",
    cta: "Open Guides →",
    image: "/images/discover/guides.jpg",
  },
  {
    title: "Interactive Atlas",
    href: "/atlas",
    tag: "Geography maps",
    label: "Explore Mizoram districts, Indian rivers, sanctuaries, passes and historical map layers.",
    cta: "Open Atlas →",
    image: "/images/discover/atlas.jpg",
  },
  {
    title: "History Chronicle",
    href: "/chronicle",
    tag: "Timeline & dates",
    label: "Step through constitutional milestones, freedom-struggle eras and linked past-paper years.",
    cta: "Open Chronicle →",
    image: "/images/discover/chronicle.jpg",
  },
  {
    title: "India & Global Stats",
    href: "/stats",
    tag: "Verified data",
    label: "Official Economic Survey indicators, Mizoram tables and global rankings for quick GK recall.",
    cta: "Open Stats →",
    image: "/images/discover/stats.jpg",
  },
] as const;

const SUBJECT_TOOLS = SITE_MAP.filter((d) =>
  ["practice", "revise", "exams", "desk"].includes(d.id),
);

export default function Library() {
  const [params, setParams] = useSearchParams();
  const [shelves, setShelves] = useState<LibraryShelf[]>([]);
  const [subjectModules, setSubjectModules] = useState<Collection[]>([]);
  const [examProgress, setExamProgress] = useState<Record<string, ExamProgressSummary>>({});
  const [facets, setFacets] = useState<TaxonomyFacet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [retry, setRetry] = useState(0);

  const tab = VIEWS.some(([id]) => id === params.get("library_view"))
    ? params.get("library_view")!
    : "subjects";

  function setTab(value: string) {
    setParams((p) => {
      const next = new URLSearchParams(p);
      next.set("library_view", value);
      for (const key of [
        "offset",
        "q",
        "access",
        "sort",
        "saved",
        "collection_id",
        "subject_id",
      ]) {
        next.delete(key);
      }
      return next;
    });
  }

  useEffect(() => {
    if (tab !== "subjects") return;
    let live = true;
    setLoading(true);
    setError("");
    Promise.allSettled([
      listLibraryShelves().then((rows) => {
        if (live) setShelves(rows);
      }),
      listCollections().then((rows) => {
        if (live) setSubjectModules(rows.filter((c) => isSubjectModule(c)));
      }),
      getExamProgress()
        .then((rows) => {
          if (live) setExamProgress(Object.fromEntries(rows.map((r) => [r.collection_id, r])));
        })
        .catch(() => {}),
      listTaxonomy("all", true).then((rows) => {
        if (live) setFacets(rows);
      }),
    ]).then((results) => {
      if (live) {
        setLoading(false);
        if (results.some((r) => r.status === "rejected")) {
          setError("Some subjects could not load. Please try again.");
        }
      }
    });
    return () => {
      live = false;
    };
  }, [tab, retry]);

  const subjects = useMemo(() => {
    const grouped = new Map<
      string,
      { id: string; title: string; questions: number }
    >();
    for (const f of facets) {
      const old = grouped.get(f.subject_id);
      if (old) old.questions = f.subject_questions ?? old.questions + f.questions;
      else
        grouped.set(f.subject_id, {
          id: f.subject_id,
          title: f.subject,
          questions: f.subject_questions ?? f.questions,
        });
    }
    return [...grouped.values()]
      .sort((a, b) => a.title.localeCompare(b.title))
      .filter((f) => f.title.toLowerCase().includes(query.toLowerCase()));
  }, [facets, query]);

  const totalShelfQuestions = useMemo(
    () => shelves.reduce((sum, s) => sum + (s.questions || 0), 0),
    [shelves],
  );

  return (
    <div className="finna-page bk-shell" data-screen="library">
      <header className="av-hero bk-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">Study library · Concept books</span>
          <h1>
            {tab === "subjects"
              ? "Study by subject"
              : tab === "reading"
                ? "From the community"
                : "Your saved library"}
          </h1>
          <p>
            {tab === "subjects"
              ? "Pick a concept volume off the shelf to practice verified past questions, read linked notes, and build subject depth."
              : tab === "reading"
                ? "Notes, summaries and study sheets contributed by learners across Finna."
                : "Your bookmarked questions and saved reading materials in one quiet shelf."}
          </p>
        </div>
        <div className="av-hero-actions">
          <Link to="/guides" className="cr-glass-btn cr-glass-btn--accent">
            Open Guides →
          </Link>
          <nav aria-label="Library views" className="av-tabs">
            {VIEWS.map(([id, label]) => (
              <button
                key={id}
                type="button"
                aria-pressed={tab === id}
                className={`av-tab${tab === id ? " is-active" : ""}`}
                onClick={() => setTab(id)}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {tab === "subjects" && (
        <>
          {loading && (
            <p role="status" className="text-sm text-secondary">
              Loading subjects…
            </p>
          )}
          {error && (
            <p role="alert" className="at-inline-err">
              {error}{" "}
              <button
                type="button"
                onClick={() => setRetry((n) => n + 1)}
                className="ml-2 font-bold underline"
              >
                Try again
              </button>
            </p>
          )}

          {/* Subject-Wise Exam Bookshelf (Cross-Exam Volumes) */}
          {subjectModules.length > 0 && (
            <SubjectBookshelf
              subjects={subjectModules}
              progress={examProgress}
              eyebrow="All-exam subject books"
              heading="Subject-wise exam bookshelf"
              subtitle="Five combined books pulling past questions from UDC, LDC, MCS, Group B and every MPSC exam into one subject volume."
              action={
                <Link to="/exams?exam_filter=subjects" className="finna-inline-pill-btn">
                  Open in Exams →
                </Link>
              }
            />
          )}

          {/* Main Concept Bookshelf (vYaeadj + xrRPRL + oNxEBXj) */}
          {shelves.length > 0 && (
            <section aria-label="Subject library" className="bk-shelf-wrap">
              <div className="bk-shelf-head">
                <div>
                  <span className="cr-eyebrow">Core concept shelves</span>
                  <h2>Pull a volume to open</h2>
                </div>
                <span className="finna-st-pill finna-st-pill--teal">
                  {shelves.length} volumes ·{" "}
                  {totalShelfQuestions.toLocaleString("en-IN")} Qs
                </span>
              </div>

              <div className="bk-shelf-grid">
                {shelves.map((s, idx) => (
                  <ConceptBook
                    key={s.id}
                    to={`/library/topics/${s.id}`}
                    title={s.title}
                    subtitle={s.description}
                    eyebrow={`Vol. ${String(idx + 1).padStart(2, "0")}`}
                    meta={`${s.questions.toLocaleString("en-IN")} questions`}
                    peekTitle="Inside this volume"
                    peekNote={s.description}
                    tone={bookToneFor(s.id || s.title, idx)}
                  />
                ))}
              </div>
              <div className="bk-shelf-ledge" aria-hidden="true" />
            </section>
          )}

          {!loading && !error && !shelves.length && (
            <section className="at-card">
              <h2>Your subject library is getting ready</h2>
              <p className="text-sm text-secondary">
                Browse all subject categories below or open the index.
              </p>
            </section>
          )}

          {/* Tall Hover-Reveal Photographic Study Tools Gallery (XWbWKwL inspiration) */}
          <section className="bk-pocket-section" aria-labelledby="study-tools-gallery">
            <div className="bk-shelf-head">
              <div>
                <span className="cr-eyebrow">Interactive reference rooms</span>
                <h2 id="study-tools-gallery">Guides, maps, timelines &amp; data</h2>
              </div>
            </div>
            <div className="xwb-grid">
              {FEATURED_STUDY_TOOLS.map((tool) => (
                <Link key={tool.href} to={tool.href} className="xwb-card">
                  <img
                    src={tool.image}
                    alt=""
                    aria-hidden="true"
                    loading="lazy"
                    decoding="async"
                    className="xwb-bg"
                  />
                  <span className="xwb-scrim" aria-hidden="true" />
                  <span className="xwb-content">
                    <span className="xwb-tag">{tool.tag}</span>
                    <strong className="xwb-title">{tool.title}</strong>
                    <span className="xwb-copy">{tool.label}</span>
                    <span className="xwb-cta">{tool.cta}</span>
                  </span>
                </Link>
              ))}
            </div>
          </section>

          {/* Related surfaces */}
          <section className="bk-pocket-section" aria-labelledby="guided-tools">
            <div className="bk-shelf-head">
              <div>
                <span className="cr-eyebrow">Study surfaces</span>
                <h2 id="guided-tools">Related surfaces</h2>
              </div>
            </div>
            <div className="at-sec-grid">
              {SUBJECT_TOOLS.map((t) => (
                <Link key={t.id} to={t.path} className="at-sec-tile">
                  <strong>{t.label}</strong>
                  <span>{t.blurb}</span>
                </Link>
              ))}
            </div>
          </section>

          {/* Community & Saved split */}
          <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
            <MaterialDiscovery title="From the community" compact />
            <section className="at-card mt-5 lg:mt-6">
              <div className="at-card-head">
                <div>
                  <h2>Saved &amp; revision</h2>
                  <p>Jump straight to your bookmarked items.</p>
                </div>
                <Link to={destinationPath("desk")} className="at-link">
                  Desk →
                </Link>
              </div>
              <div className="at-btn-row">
                <Link to={destinationPath("revise")} className="finna-st-btn">
                  Revise questions &amp; mistakes →
                </Link>
                <Link to={destinationPath("exams")} className="finna-st-btn">
                  My exams →
                </Link>
              </div>
            </section>
          </div>

          {/* All Subject Categories Index Drawer */}
          <details className="at-card">
            <summary className="cursor-pointer text-base font-bold">
              Browse all subject categories ({subjects.length || facets.length})
            </summary>
            <div className="mt-3 space-y-4">
              <label className="at-field">
                <span className="sr-only">Find a library subject</span>
                <input
                  type="search"
                  aria-label="Find a library subject"
                  placeholder="Find a subject…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </label>
              <div className="bk-mini-grid">
                {subjects.map((s, idx) => (
                  <Link
                    key={s.id}
                    to={`/library/subjects/${encodeURIComponent(s.id)}`}
                    className={`bk-mini-book bk-tone-${bookToneFor(s.id, idx)}`}
                  >
                    <span className="bk-mini-spine" aria-hidden="true" />
                    <span className="bk-mini-body">
                      <strong>{s.title}</strong>
                      <span>
                        {s.questions.toLocaleString("en-IN")} questions
                      </span>
                    </span>
                    <span className="bk-mini-edge" aria-hidden="true" />
                  </Link>
                ))}
              </div>
              {!loading && !subjects.length && (
                <p className="py-2 text-sm text-secondary">
                  No subjects match this search.
                </p>
              )}
            </div>
          </details>
        </>
      )}

      {tab === "reading" && (
        <Suspense fallback={<p role="status">Loading community materials…</p>}>
          <Materials embedded />
        </Suspense>
      )}

      {tab === "saved" && (
        <>
          <section className="at-card">
            <div className="at-card-head">
              <div>
                <h2>Your saved questions</h2>
                <p>Bookmarks are kept in your personal Desk.</p>
              </div>
              <Link className="cr-primary-btn" to={destinationPath("desk")}>
                Open saved questions →
              </Link>
            </div>
          </section>
          <Suspense fallback={<p role="status">Loading saved materials…</p>}>
            <Materials key="saved" embedded savedOnly />
          </Suspense>
        </>
      )}
    </div>
  );
}
