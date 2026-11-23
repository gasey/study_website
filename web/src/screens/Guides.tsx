import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import guidesSeed from "../data/guides-seed.json";
import { bookMonogram, bookToneFor } from "../components/ConceptBook";

interface GuideChapter {
  ord: number;
  anchor: string;
  heading: string;
  body_markdown: string;
  practice_query?: string;
  question_ids?: string[];
}

interface GuideDoc {
  slug: string;
  title: string;
  subject_id?: string | null;
  subject_label?: string;
  summary: string;
  reading_minutes: number;
  status?: string;
  chapters: GuideChapter[];
}

const SEED_GUIDES = guidesSeed as GuideDoc[];

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**"))
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("*") && part.endsWith("*"))
      return <em key={idx}>{part.slice(1, -1)}</em>;
    if (part.startsWith("`") && part.endsWith("`"))
      return (
        <code
          key={idx}
          className="rounded bg-canvas px-1.5 py-0.5 font-mono text-sm text-ink"
        >
          {part.slice(1, -1)}
        </code>
      );
    return part;
  });
}

/** Safe markdown renderer — never emits raw HTML (`dangerouslySetInnerHTML` is banned). */
function GuideMarkdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="font-reading mt-3 space-y-4 text-ink">
      {blocks.map((block, bIdx) => {
        const lines = block.split("\n").filter(Boolean);
        if (lines.every((l) => l.startsWith("- "))) {
          return (
            <ul key={bIdx} className="list-disc space-y-2 pl-6">
              {lines.map((l, i) => (
                <li key={i}>{renderInline(l.slice(2))}</li>
              ))}
            </ul>
          );
        }
        if (lines[0]?.startsWith("> ")) {
          return (
            <blockquote
              key={bIdx}
              className="gd-quote border-l-2 border-ink pl-4 italic text-secondary"
            >
              {renderInline(
                lines.map((l) => l.replace(/^>\s?/, "")).join(" "),
              )}
            </blockquote>
          );
        }
        return <p key={bIdx}>{renderInline(lines.join(" "))}</p>;
      })}
    </div>
  );
}

/** `/guides` and `/guides/:slug` reading library (§VII.5, §VII.12.2, Phase V.15).
 *  Reads published Postgres guides from `/api/guides` when available and falls
 *  back cleanly to the structured markdown seed (Using Finna, Polity Codex,
 *  Quick Revision, Tenses & Voice) with zero embedded HTML. */
export default function Guides() {
  const { slug } = useParams();
  const [query, setQuery] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [activeAnchor, setActiveAnchor] = useState("");
  const [apiGuides, setApiGuides] = useState<GuideDoc[] | null>(null);
  const [apiDoc, setApiDoc] = useState<GuideDoc | null>(null);

  useEffect(() => {
    let live = true;
    if (slug) {
      setApiDoc(null);
      fetch("/api/guides/" + encodeURIComponent(slug))
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (live && data && data.slug) setApiDoc(data);
        })
        .catch(() => {});
    } else {
      fetch("/api/guides")
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (live && Array.isArray(data?.items) && data.items.length)
            setApiGuides(data.items);
        })
        .catch(() => {});
    }
    return () => {
      live = false;
    };
  }, [slug]);

  const catalog = apiGuides && apiGuides.length ? apiGuides : SEED_GUIDES;

  const subjectTags = useMemo(() => {
    const labels = new Set<string>();
    for (const g of catalog) {
      labels.add(g.subject_label || g.subject_id || "Guide");
    }
    return ["all", ...labels];
  }, [catalog]);

  const filteredCatalog = useMemo(() => {
    const q = query.trim().toLowerCase();
    return catalog.filter((g) => {
      const label = g.subject_label || g.subject_id || "Guide";
      if (subjectFilter !== "all" && label !== subjectFilter) return false;
      if (!q) return true;
      return `${g.title} ${g.summary} ${label}`.toLowerCase().includes(q);
    });
  }, [catalog, query, subjectFilter]);

  if (slug) {
    const doc = apiDoc || SEED_GUIDES.find((g) => g.slug === slug);
    if (!doc) {
      return (
        <div className="at-sub-page at-sub-page--narrow" data-screen="guides">
          <section className="at-card">
            <Link to="/guides" className="at-link">
              ← All guides
            </Link>
            <h1 className="font-display text-2xl font-bold">Guide not found</h1>
            <p className="text-sm text-secondary">
              Only published first-party guides appear here.
            </p>
          </section>
        </div>
      );
    }

    const tone = bookToneFor(doc.subject_id || doc.slug);
    const mono = bookMonogram(doc.title);

    return (
      <div className="gd-reader-shell" data-screen="guides">
        <div className="gd-reader-grid">
          {/* Left Sticky Bookmark & Volume Rail */}
          <aside className="gd-bookmark-rail">
            <Link to="/guides" className="gd-back-link">
              ← Back to reading shelf
            </Link>

            <div className={`gd-mini-cover bk-tone-${tone}`}>
              <span className="gd-mini-cover-spine" aria-hidden="true" />
              <div className="gd-mini-cover-body">
                <span className="gd-mini-cover-mono">{mono}</span>
                <strong>{doc.title}</strong>
                <span>
                  {doc.subject_label || doc.subject_id || "Guide"} ·{" "}
                  {doc.reading_minutes} min
                </span>
              </div>
            </div>

            <nav aria-label="Guide chapters" className="gd-toc hidden lg:block">
              <p className="gd-toc-label">
                Chapters · {doc.chapters.length}
              </p>
              <ul className="gd-toc-list">
                {doc.chapters.map((ch, idx) => (
                  <li key={ch.anchor}>
                    <a
                      href={"#" + ch.anchor}
                      onClick={() => setActiveAnchor(ch.anchor)}
                      className={`gd-toc-link${activeAnchor === ch.anchor ? " is-active" : ""}`}
                    >
                      <span className="gd-toc-num">
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <span>{ch.heading}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </nav>

            <details className="gd-toc-mobile lg:hidden">
              <summary>Contents ({doc.chapters.length} chapters)</summary>
              <ul>
                {doc.chapters.map((ch, idx) => (
                  <li key={ch.anchor}>
                    <a href={"#" + ch.anchor}>
                      <span>{String(idx + 1).padStart(2, "0")}</span>{" "}
                      {ch.heading}
                    </a>
                  </li>
                ))}
              </ul>
            </details>
          </aside>

          {/* Right Open-Book Paper Spread */}
          <article className={`gd-paper-spread bk-tone-${tone}`}>
            <span className="gd-spine-fold" aria-hidden="true" />
            <header className="gd-paper-head">
              <div className="gd-paper-meta">
                <span className="finna-st-pill finna-st-pill--teal">
                  {doc.subject_label || doc.subject_id || "Guide"}
                </span>
                <span>{doc.reading_minutes} min read</span>
                <span>·</span>
                <span>{doc.chapters.length} chapters</span>
              </div>
              <h1>{doc.title}</h1>
              <p>{doc.summary}</p>
            </header>

            <div className="gd-chapters">
              {doc.chapters.map((ch, idx) => {
                const practiceHref =
                  ch.question_ids && ch.question_ids.length
                    ? "/practice/build?" +
                      new URLSearchParams(
                        ch.question_ids.map((id) => ["ids", id]),
                      ).toString()
                    : ch.practice_query || "/practice";
                const nextCh = doc.chapters[idx + 1];
                return (
                  <section
                    key={ch.anchor}
                    id={ch.anchor}
                    className="gd-chapter scroll-mt-24"
                  >
                    <div className="gd-chapter-kicker">
                      Chapter {String(idx + 1).padStart(2, "0")} of{" "}
                      {String(doc.chapters.length).padStart(2, "0")}
                    </div>
                    <h2>{ch.heading}</h2>
                    <GuideMarkdown text={ch.body_markdown} />
                    <div className="gd-chapter-actions">
                      <Link to={practiceHref} className="cr-primary-btn">
                        Practice this chapter →
                      </Link>
                      {nextCh && (
                        <a
                          href={"#" + nextCh.anchor}
                          onClick={() => setActiveAnchor(nextCh.anchor)}
                          className="finna-st-btn"
                        >
                          Next: {nextCh.heading} ↓
                        </a>
                      )}
                    </div>
                  </section>
                );
              })}
            </div>
          </article>
        </div>
      </div>
    );
  }

  return (
    <div className="bk-shell gd-catalog-page" data-screen="guides">
      <header className="av-hero bk-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">First-party reading room</span>
          <h1>Study Guides</h1>
          <p>
            Edited concept books linked directly to verified bank questions.
            Hover or tap any volume to peek inside — always free to read.
          </p>
        </div>
        <div className="av-hero-actions">
          <Link to="/library" className="cr-glass-btn">
            ← Subject library
          </Link>
          <Link to="/materials" className="cr-glass-btn cr-glass-btn--accent">
            Community notes
          </Link>
        </div>
      </header>

      {/* Search & Subject Shelf Filter Bar */}
      <div className="gd-toolbar">
        <label className="at-field gd-search-field">
          <span className="sr-only">Search guides</span>
          <input
            type="search"
            aria-label="Search guides"
            placeholder="Search guides by title, subject or topic…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <div className="av-cat-strip" role="group" aria-label="Filter guides by subject">
          {subjectTags.map((tag) => (
            <button
              key={tag}
              type="button"
              aria-pressed={subjectFilter === tag}
              className={`av-cat-pill${subjectFilter === tag ? " is-active" : ""}`}
              onClick={() => setSubjectFilter(tag)}
            >
              {tag === "all" ? `All (${catalog.length})` : tag}
            </button>
          ))}
        </div>
      </div>

      {/* Interactive 3D Page-Flip Guide Shelf (jkantner/xrRPRL + vYaeadj + oNxEBXj) */}
      <section aria-label="Published study guides" className="gd-shelf-wrap">
        <div className="gd-book-grid">
          {filteredCatalog.map((g, idx) => {
            const tone = bookToneFor(g.subject_id || g.slug, idx);
            const mono = bookMonogram(g.title);
            const previewChapters = (g.chapters || []).slice(0, 3);
            return (
              <Link
                key={g.slug}
                to={"/guides/" + g.slug}
                className={`gd-book-card bk-tone-${tone}`}
              >
                {/* 3D Interactive Page-Flip Book Preview */}
                <span className="gd-3d-book" aria-hidden="true">
                  <span className="gd-3d-back" />
                  <span className="gd-3d-leaf gd-3d-leaf-3" />
                  <span className="gd-3d-leaf gd-3d-leaf-2" />
                  <span className="gd-3d-leaf gd-3d-leaf-1">
                    <span className="gd-leaf-label">Contents</span>
                    {previewChapters.map((c) => (
                      <span key={c.anchor} className="gd-leaf-line">
                        {c.heading}
                      </span>
                    ))}
                  </span>
                  <span className="gd-3d-front">
                    <span className="bk-spine" />
                    <span className="bk-ribbon" />
                    <span className="gd-front-inner">
                      <span className="gd-front-mono">{mono}</span>
                      <span className="gd-front-title">{g.title}</span>
                      <span className="gd-front-meta">
                        {g.reading_minutes} min
                      </span>
                    </span>
                  </span>
                </span>

                {/* Jacket Metadata */}
                <span className="gd-card-info">
                  <span className="gd-card-top">
                    <span className="finna-st-pill finna-st-pill--teal">
                      {g.subject_label || g.subject_id || "Guide"}
                    </span>
                    <span className="gd-card-mins">
                      {g.reading_minutes} min · {(g.chapters || []).length}{" "}
                      chapters
                    </span>
                  </span>
                  <h2>{g.title}</h2>
                  <p>{g.summary}</p>
                  {previewChapters.length > 0 && (
                    <span className="gd-card-chips">
                      {previewChapters.map((c) => (
                        <span key={c.anchor}>{c.heading}</span>
                      ))}
                    </span>
                  )}
                  <span className="gd-card-cta">Open guide →</span>
                </span>
              </Link>
            );
          })}
        </div>

        {!filteredCatalog.length && (
          <div className="at-card">
            <p className="text-sm text-secondary">
              No published guides match that search.
            </p>
          </div>
        )}
        <div className="bk-shelf-ledge" aria-hidden="true" />
      </section>

      <section className="at-card">
        <div className="at-card-head">
          <div>
            <h2>From the community</h2>
            <p>
              Looking for notes and summaries written by other learners? Those
              live separately in community materials.
            </p>
          </div>
        </div>
        <div className="at-btn-row">
          <Link to="/materials" className="finna-st-btn finna-st-btn--primary">
            Browse community materials →
          </Link>
          <Link to="/create" className="finna-st-btn">
            Share a study note
          </Link>
        </div>
      </section>
    </div>
  );
}
