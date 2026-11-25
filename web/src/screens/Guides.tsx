import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import guidesSeed from "../data/guides-seed.json";
import { bookMonogram, bookToneFor } from "../components/ConceptBook";

interface GuideChapter {
  ord: number;
  anchor: string;
  heading: string;
  body_markdown: string;
  practice_query?: string;
  practice_label?: string;
  companion_href?: string;
  companion_label?: string;
  question_ids?: string[];
}

interface GuideDoc {
  slug: string;
  title: string;
  subject_id?: string | null;
  subject_label?: string;
  topic_id?: string | null;
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

function parseGrammarExample(raw: string): { label: string; text: string; tone: "pos" | "neg" | "ask" } | null {
  const trimmed = raw.trim();
  if (!trimmed.startsWith("{") || !trimmed.endsWith("}")) return null;
  try {
    const obj = JSON.parse(trimmed) as { l?: string; t?: string };
    if (typeof obj?.l !== "string" || typeof obj?.t !== "string") return null;
    const tone = obj.l === "+" ? "pos" : obj.l === "?" ? "ask" : "neg";
    return { label: obj.l, text: obj.t, tone };
  } catch {
    return null;
  }
}

function parseVoiceRow(raw: string): { tense: string; active: string; passive: string } | null {
  const m = raw.match(/^\*\*([^*]+)\*\*:\s*Active:\s*`([^`]+)`\s*→\s*Passive:\s*`([^`]+)`$/);
  if (!m) return null;
  return { tense: m[1].trim(), active: m[2].trim(), passive: m[3].trim() };
}

function renderFactItem(raw: string): ReactNode {
  // Auto-highlight short lead-in terms like "Regulating Act 1773: ..." or "Harappa — ..."
  if (!raw.startsWith("**")) {
    const colon = raw.match(/^([^:]{2,52}):\s+(.+)$/);
    if (colon) {
      return (
        <>
          <strong className="gd-fact-term">{colon[1]}:</strong>{" "}
          {renderInline(colon[2])}
        </>
      );
    }
    const dash = raw.match(/^([^—]{2,48})\s+—\s+(.+)$/);
    if (dash) {
      return (
        <>
          <strong className="gd-fact-term">{dash[1]}</strong> —{" "}
          {renderInline(dash[2])}
        </>
      );
    }
  }
  return renderInline(raw);
}

type CalloutSpec = {
  kind: "lead" | "concept" | "example" | "trap" | "hook";
  eyebrow: string;
  body: string;
};

function parseCallout(text: string): CalloutSpec | null {
  const specs: [RegExp, CalloutSpec["kind"], string][] = [
    [/^\*\*Overview:\*\*\s*(.+)$/s, "lead", "Overview"],
    [/^\*\*Core Mental Model:\*\*\s*(.+)$/s, "concept", "Mental Model"],
    [/^\*\*Intuition:\*\*\s*(.+)$/s, "concept", "Intuition"],
    [/^\*\*Worked Example:\*\*\s*(.+)$/s, "example", "Worked Example"],
    [/^\*\*Exam Trap:\*\*\s*(.+)$/s, "trap", "Exam Trap"],
    [/^\*\*Memory Hook:\*\*\s*(.+)$/s, "hook", "Memory Hook"],
  ];
  for (const [re, kind, eyebrow] of specs) {
    const m = text.match(re);
    if (m) return { kind, eyebrow, body: m[1].trim() };
  }
  return null;
}

/** Safe editorial textbook renderer — never emits raw HTML (`dangerouslySetInnerHTML` is banned). */
function GuideMarkdown({ text, quickMode = false }: { text: string; quickMode?: boolean }) {
  const blocks = text.split(/\n{2,}/);
  const grouped: { kind: "examples" | "voice" | "block"; items: string[] }[] = [];

  for (const block of blocks) {
    const lines = block.split("\n").filter(Boolean);
    if (lines.length === 1 && lines[0].startsWith("- ")) {
      const content = lines[0].slice(2).trim();
      if (parseGrammarExample(content)) {
        const last = grouped[grouped.length - 1];
        if (last?.kind === "examples") {
          last.items.push(content);
          continue;
        }
        grouped.push({ kind: "examples", items: [content] });
        continue;
      }
      if (parseVoiceRow(content)) {
        const last = grouped[grouped.length - 1];
        if (last?.kind === "voice") {
          last.items.push(content);
          continue;
        }
        grouped.push({ kind: "voice", items: [content] });
        continue;
      }
    }
    grouped.push({ kind: "block", items: lines });
  }

  // If Quick Revision mode is active and this chapter has structured scan blocks
  // (callouts, formulas, tables, examples, voice), hide dense plain prose & long fact dumps.
  const hasHighYieldBlocks = grouped.some((g) => {
    if (g.kind === "examples" || g.kind === "voice") return true;
    const joined = g.items.join(" ").trim();
    if (parseCallout(joined)) return true;
    if (g.items.length >= 2 && g.items.every((l) => l.trim().startsWith("|") && l.trim().endsWith("|"))) return true;
    if (g.items.every((l) => /^-\s+`[^`]+`$/.test(l.trim()))) return true;
    return false;
  });

  return (
    <div className="gd-prose font-reading mt-4 space-y-4 text-ink">
      {grouped.map((g, bIdx) => {
        if (g.kind === "examples") {
          const parsed = g.items
            .map(parseGrammarExample)
            .filter((x): x is NonNullable<typeof x> => Boolean(x));
          return (
            <div key={bIdx} className="gd-ex-list" role="list" aria-label="Grammar examples">
              {parsed.map((ex, i) => (
                <div key={i} className={`gd-ex-row is-${ex.tone}`} role="listitem">
                  <span
                    className="gd-ex-badge"
                    title={
                      ex.tone === "pos"
                        ? "Affirmative"
                        : ex.tone === "ask"
                          ? "Question"
                          : "Negative"
                    }
                  >
                    {ex.label}
                  </span>
                  <span className="gd-ex-text">{ex.text}</span>
                </div>
              ))}
            </div>
          );
        }

        if (g.kind === "voice") {
          const rows = g.items
            .map(parseVoiceRow)
            .filter((x): x is NonNullable<typeof x> => Boolean(x));
          return (
            <div key={bIdx} className="gd-table-wrap">
              <table className="gd-ref-table">
                <thead>
                  <tr>
                    <th>Form / Tense</th>
                    <th>Active Voice</th>
                    <th>Passive Voice</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <th>{r.tense}</th>
                      <td>{r.active}</td>
                      <td>{r.passive}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        const lines = g.items;
        const joined = lines.join(" ").trim();

        // Formula section kicker label (handled cleanly by the formula grid right below it)
        if (joined === "**Key Formulas & Shortcuts**") {
          return (
            <p key={bIdx} className="gd-formula-kicker">
              Key Formulas &amp; Shortcuts
            </p>
          );
        }

        // Semantic Callout Cards (Overview, Mental Model / Intuition, Worked Example, Exam Trap, Memory Hook)
        const callout = parseCallout(joined);
        if (callout) {
          if (callout.kind === "lead") {
            return (
              <p key={bIdx} className="gd-lead">
                {renderInline(callout.body)}
              </p>
            );
          }
          return (
            <aside key={bIdx} className={`gd-callout is-${callout.kind}`}>
              <span className="gd-callout-label">{callout.eyebrow}</span>
              <p>{renderInline(callout.body)}</p>
            </aside>
          );
        }

        // Subheadings
        if (lines.length === 1 && lines[0].startsWith("### ")) {
          const subTitle = lines[0].slice(4).trim();
          if (
            quickMode &&
            hasHighYieldBlocks &&
            (subTitle === "High-Yield Exam Facts" || subTitle === "Key Constitutional Notes")
          ) {
            return null;
          }
          return (
            <h3 key={bIdx} className="gd-subhead">
              {renderInline(subTitle)}
            </h3>
          );
        }

        // Editorial Reference / Comparison / Timeline Tables
        if (
          lines.length >= 2 &&
          lines.every((l) => l.trim().startsWith("|") && l.trim().endsWith("|"))
        ) {
          const rows = lines
            .filter((l) => !/^\|[\s:|-]+\|$/.test(l.trim()))
            .map((l) =>
              l
                .trim()
                .slice(1, -1)
                .split("|")
                .map((c) => c.trim()),
            );
          const [head, ...body] = rows;
          if (head?.length) {
            return (
              <div key={bIdx} className="gd-table-wrap">
                <table className="gd-ref-table">
                  <thead>
                    <tr>
                      {head.map((c, ci) => (
                        <th key={ci}>{renderInline(c)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {body.map((r, ri) => (
                      <tr key={ri}>
                        {r.map((c, ci) => (
                          <td key={ci}>{renderInline(c)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }
        }

        // Formula Cheat-Sheet Grid (all bullet lines are backticked formulas)
        if (lines.every((l) => /^-\s+`[^`]+`$/.test(l.trim()))) {
          return (
            <div key={bIdx} className="gd-formula-grid" role="list" aria-label="Formulas and shortcuts">
              {lines.map((l, i) => {
                const formula = l.trim().replace(/^-\s+`/, "").replace(/`$/, "");
                return (
                  <div key={i} className="gd-formula-card" role="listitem">
                    <code>{formula}</code>
                  </div>
                );
              })}
            </div>
          );
        }

        // Structured Editorial Fact Cards
        if (lines.every((l) => l.startsWith("- "))) {
          if (quickMode && hasHighYieldBlocks) return null;
          return (
            <ul key={bIdx} className="gd-fact-list">
              {lines.map((l, i) => (
                <li key={i} className="gd-fact-item">
                  <span className="gd-fact-dot" aria-hidden="true" />
                  <span className="gd-fact-body">{renderFactItem(l.slice(2).trim())}</span>
                </li>
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

        if (quickMode && hasHighYieldBlocks) return null;
        return <p key={bIdx} className="gd-para">{renderInline(joined)}</p>;
      })}
    </div>
  );
}

/** `/guides` and `/guides/:slug` reading library (§VII.5, §VII.12.2, Phase V.15).
 *  Merges published Postgres guides from `/api/guides` with the bundled first-party
 *  seed library so live Admin edits always take precedence while newly crafted
 *  concept guides appear immediately. */
export default function Guides() {
  const { slug } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const fromQuestion = Boolean((location.state as { fromQuestion?: boolean } | null)?.fromQuestion);
  const [query, setQuery] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [activeAnchor, setActiveAnchor] = useState("");
  const [targetedAnchor, setTargetedAnchor] = useState("");
  const [quickMode, setQuickMode] = useState(false);
  const [apiGuides, setApiGuides] = useState<GuideDoc[] | null>(null);
  const [apiDoc, setApiDoc] = useState<GuideDoc | null>(null);

  useEffect(() => {
    setQuickMode(false);
    setActiveAnchor("");
    setTargetedAnchor("");
  }, [slug]);

  // Guaranteed smooth auto-scroll & highlight when deep-linked from a question (/guides/:slug#anchor)
  useEffect(() => {
    if (!slug) return;
    const rawHash = (location.hash || "").replace(/^#/, "").trim();
    if (!rawHash) return;
    const decoded = decodeURIComponent(rawHash);
    setActiveAnchor(decoded);
    setTargetedAnchor(decoded);
    let cancelled = false;
    const scrollNow = () => {
      if (cancelled) return;
      const el = document.getElementById(decoded);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };
    const raf = window.requestAnimationFrame(scrollNow);
    const retry = window.setTimeout(scrollNow, 220);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(raf);
      window.clearTimeout(retry);
    };
  }, [slug, location.hash, apiDoc]);

  useEffect(() => {
    if (!slug || typeof IntersectionObserver === "undefined") return;
    const sections = Array.from(document.querySelectorAll<HTMLElement>(".gd-chapter[id]"));
    if (!sections.length) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]?.target.id) {
          setActiveAnchor(visible[0].target.id);
        }
      },
      { rootMargin: "-90px 0px -65% 0px", threshold: 0 },
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, [slug, apiDoc]);

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

  const catalog = useMemo(() => {
    if (!apiGuides || !apiGuides.length) return SEED_GUIDES;
    const bySlug = new Map<string, GuideDoc>();
    for (const g of SEED_GUIDES) bySlug.set(g.slug, g);
    for (const g of apiGuides) {
      const seed = bySlug.get(g.slug);
      bySlug.set(g.slug, {
        ...seed,
        ...g,
        subject_label: g.subject_label || seed?.subject_label,
      });
    }
    return [...bySlug.values()];
  }, [apiGuides]);

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

    const tone = bookToneFor(doc.slug + " " + (doc.subject_label || doc.subject_id || ""));
    const mono = bookMonogram(doc.title);
    const seedDoc = SEED_GUIDES.find((g) => g.slug === doc.slug);
    const subjectTopicsLink = (() => {
      const raw = (doc.subject_id || "").trim().toLowerCase();
      if (doc.slug === "tenses-and-voice" || raw === "english") {
        return { to: "/subjects/english?view=topics", label: "English Topics →" };
      }
      if (
        doc.slug === "polity-codex" ||
        doc.slug === "quick-revision" ||
        ["gk-gs", "gk", "gs", "polity", "general-studies", "general-knowledge", "science", "history", "geography", "economy"].includes(raw)
      ) {
        return { to: "/subjects/gk-gs?view=topics", label: "GK & GS Topics →" };
      }
      if (["mathematics", "math", "maths", "arithmetic", "quantitative"].includes(raw)) {
        return { to: "/subjects/mathematics?view=topics", label: "Mathematics Topics →" };
      }
      if (raw === "reasoning" || raw === "reasoning-and-aptitude") {
        return { to: "/subjects/reasoning?view=topics", label: "Reasoning Topics →" };
      }
      if (raw === "computer-science" || doc.slug === "computer-fundamentals") {
        return { to: "/subjects/computer-science?view=topics", label: "Computer & IT Topics →" };
      }
      if (raw === "science" || doc.slug === "general-science") {
        return { to: "/subjects/science?view=topics", label: "General Science Topics →" };
      }
      if (raw === "mizo") {
        return { to: "/subjects/mizo?view=topics", label: "Mizo Topics →" };
      }
      if (raw && /^[a-z0-9-]+$/.test(raw)) {
        const label = doc.subject_label || raw.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        return { to: `/subjects/${encodeURIComponent(raw)}?view=topics`, label: `${label} Topics →` };
      }
      return null;
    })();

    return (
      <div className="gd-reader-shell" data-screen="guides">
        <div className="gd-reader-grid">
          {/* Left Sticky Bookmark & Volume Rail */}
          <aside className="gd-bookmark-rail">
            {fromQuestion && (
              <button
                type="button"
                className="gd-back-question-btn"
                onClick={() => navigate(-1)}
              >
                ← Back to question
              </button>
            )}
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

            {subjectTopicsLink && (
              <Link to={subjectTopicsLink.to} className="gd-subject-jump">
                {subjectTopicsLink.label}
              </Link>
            )}

            <nav aria-label="Guide chapters" className="gd-toc hidden lg:block">
              <p className="gd-toc-label">
                Chapters · {doc.chapters.length}
              </p>
              <ul className="gd-toc-list">
                {doc.chapters.map((ch, idx) => {
                  const seedCh = seedDoc?.chapters.find((s) => s.anchor === ch.anchor);
                  const displayHeading =
                    seedCh && /^\d+\.\s*[a-z]{2,8}$/.test(ch.heading.trim())
                      ? seedCh.heading
                      : ch.heading;
                  return (
                    <li key={ch.anchor}>
                      <a
                        href={"#" + ch.anchor}
                        onClick={() => setActiveAnchor(ch.anchor)}
                        className={`gd-toc-link${activeAnchor === ch.anchor ? " is-active" : ""}`}
                      >
                        <span className="gd-toc-num">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <span>{displayHeading}</span>
                      </a>
                    </li>
                  );
                })}
              </ul>
            </nav>

            <details className="gd-toc-mobile lg:hidden">
              <summary>Contents ({doc.chapters.length} chapters)</summary>
              <ul>
                {doc.chapters.map((ch, idx) => {
                  const seedCh = seedDoc?.chapters.find((s) => s.anchor === ch.anchor);
                  const displayHeading =
                    seedCh && /^\d+\.\s*[a-z]{2,8}$/.test(ch.heading.trim())
                      ? seedCh.heading
                      : ch.heading;
                  return (
                    <li key={ch.anchor}>
                      <a href={"#" + ch.anchor}>
                        <span>{String(idx + 1).padStart(2, "0")}</span>{" "}
                        {displayHeading}
                      </a>
                    </li>
                  );
                })}
              </ul>
            </details>
          </aside>

          {/* Right Open-Book Paper Spread */}
          <article className={`gd-paper-spread bk-tone-${tone}`}>
            <span className="gd-spine-fold" aria-hidden="true" />
            {doc.chapters.length > 1 && (() => {
              const idx = Math.max(
                0,
                doc.chapters.findIndex((c) => c.anchor === activeAnchor),
              );
              const pct = Math.round(((idx + 1) / doc.chapters.length) * 100);
              return (
                <div className="gd-progress-track" aria-hidden="true">
                  <span style={{ width: `${pct}%` }} />
                </div>
              );
            })()}
            <header className="gd-paper-head">
              <div className="gd-paper-head-row">
                <div className="gd-paper-meta">
                  <span className="finna-st-pill finna-st-pill--teal">
                    {doc.subject_label || doc.subject_id || "Guide"}
                  </span>
                  <span>{doc.reading_minutes} min read</span>
                  <span>·</span>
                  <span>{doc.chapters.length} chapters</span>
                </div>
                <div className="gd-mode-seg" role="group" aria-label="Reading depth">
                  <button
                    type="button"
                    aria-pressed={!quickMode}
                    className={!quickMode ? "is-on" : ""}
                    onClick={() => setQuickMode(false)}
                  >
                    Full guide
                  </button>
                  <button
                    type="button"
                    aria-pressed={quickMode}
                    className={quickMode ? "is-on" : ""}
                    onClick={() => setQuickMode(true)}
                    title="Spotlight mental models, formulas, comparison tables, worked examples & exam traps"
                  >
                    ⚡ Quick revision
                  </button>
                </div>
              </div>
              <h1>{doc.title}</h1>
              <p>{doc.summary}</p>
            </header>

            <div className="gd-chapters">
              {doc.chapters.map((ch, idx) => {
                const seedChapter = seedDoc?.chapters.find((s) => s.anchor === ch.anchor);
                const displayHeading =
                  seedChapter && /^\d+\.\s*[a-z]{2,8}$/.test(ch.heading.trim())
                    ? seedChapter.heading
                    : ch.heading;
                // If live Postgres still holds the un-enriched Polity Codex bullet dump,
                // seamlessly present the upgraded seed (which preserves every original bullet
                // plus comparison tables, mental models, and exam traps).
                const displayBody =
                  doc.slug === "polity-codex" &&
                  seedChapter &&
                  seedChapter.body_markdown.includes("### Key Constitutional Notes") &&
                  !ch.body_markdown.includes("### Key Constitutional Notes")
                    ? seedChapter.body_markdown
                    : ch.body_markdown;
                const englishTopicHref =
                  doc.slug === "tenses-and-voice"
                    ? ch.anchor.includes("voice")
                      ? "/subjects/english?view=browse&subject_id=english&topic_id=english%2Fgrammar&subtopic_id=english%2Fgrammar%2Fvoice#exam-question-browser"
                      : "/subjects/english?view=browse&subject_id=english&topic_id=english%2Fgrammar&subtopic_id=english%2Fgrammar%2Ftenses#exam-question-browser"
                    : null;
                const practiceHref =
                  ch.question_ids && ch.question_ids.length
                    ? "/practice/build?" +
                      new URLSearchParams(
                        ch.question_ids.map((id) => ["ids", id]),
                      ).toString()
                    : englishTopicHref || ch.practice_query || seedChapter?.practice_query || "/practice";
                const practiceLabel =
                  ch.practice_label ||
                  seedChapter?.practice_label ||
                  (doc.slug === "tenses-and-voice"
                    ? ch.anchor.includes("voice")
                      ? "Practise Voice MCQs →"
                      : "Practise Tenses MCQs →"
                    : "Practice this chapter →");
                const companionHref = ch.companion_href || seedChapter?.companion_href;
                const companionLabel = ch.companion_label || seedChapter?.companion_label;
                const nextCh = doc.chapters[idx + 1];
                const nextSeed = nextCh ? seedDoc?.chapters.find((s) => s.anchor === nextCh.anchor) : null;
                const nextHeading =
                  nextCh && nextSeed && /^\d+\.\s*[a-z]{2,8}$/.test(nextCh.heading.trim())
                    ? nextSeed.heading
                    : nextCh?.heading;
                const isTargeted = targetedAnchor === ch.anchor;
                return (
                  <section
                    key={ch.anchor}
                    id={ch.anchor}
                    className={`gd-chapter scroll-mt-24${isTargeted ? " gd-chapter--targeted" : ""}`}
                  >
                    <div className="gd-chapter-kicker">
                      Chapter {String(idx + 1).padStart(2, "0")} of{" "}
                      {String(doc.chapters.length).padStart(2, "0")}
                      {isTargeted && (
                        <span className="gd-targeted-badge">Matched chapter</span>
                      )}
                    </div>
                    <h2>{displayHeading}</h2>
                    <GuideMarkdown text={displayBody} quickMode={quickMode} />
                    <div className="gd-chapter-actions">
                      <Link to={practiceHref} className="cr-primary-btn">
                        {practiceLabel}
                      </Link>
                      {companionHref && companionLabel && (
                        <Link to={companionHref} className="finna-st-btn">
                          {companionLabel}
                        </Link>
                      )}
                      {nextCh && (
                        <a
                          href={"#" + nextCh.anchor}
                          onClick={() => setActiveAnchor(nextCh.anchor)}
                          className="finna-st-btn"
                        >
                          Next: {nextHeading} ↓
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
            const tone = bookToneFor(g.slug + " " + (g.subject_label || g.subject_id || ""), idx);
            const mono = bookMonogram(g.title);
            const previewChapters = (g.chapters || []).slice(0, 3);
            const chCount = (g.chapters || []).length;
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
                      {g.reading_minutes} min · {chCount}{" "}
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
