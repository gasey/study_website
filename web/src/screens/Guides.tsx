import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import guidesSeed from '../data/guides-seed.json'

interface GuideChapter {
  ord: number
  anchor: string
  heading: string
  body_markdown: string
  practice_query?: string
  question_ids?: string[]
}

interface GuideDoc {
  slug: string
  title: string
  subject_id?: string | null
  subject_label?: string
  summary: string
  reading_minutes: number
  status?: string
  chapters: GuideChapter[]
}

const SEED_GUIDES = guidesSeed as GuideDoc[]

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={idx}>{part.slice(2, -2)}</strong>
    if (part.startsWith('*') && part.endsWith('*')) return <em key={idx}>{part.slice(1, -1)}</em>
    if (part.startsWith('`') && part.endsWith('`'))
      return (
        <code key={idx} className="rounded bg-canvas px-1.5 py-0.5 font-mono text-sm text-ink">
          {part.slice(1, -1)}
        </code>
      )
    return part
  })
}

/** Safe markdown renderer — never emits raw HTML (`dangerouslySetInnerHTML` is banned). */
function GuideMarkdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/)
  return (
    <div className="font-reading mt-3 space-y-4 text-ink">
      {blocks.map((block, bIdx) => {
        const lines = block.split('\n').filter(Boolean)
        if (lines.every((l) => l.startsWith('- '))) {
          return (
            <ul key={bIdx} className="list-disc space-y-2 pl-6">
              {lines.map((l, i) => (
                <li key={i}>{renderInline(l.slice(2))}</li>
              ))}
            </ul>
          )
        }
        if (lines[0]?.startsWith('> ')) {
          return (
            <blockquote key={bIdx} className="border-l-2 border-ink pl-4 italic text-secondary">
              {renderInline(lines.map((l) => l.replace(/^>\s?/, '')).join(' '))}
            </blockquote>
          )
        }
        return <p key={bIdx}>{renderInline(lines.join(' '))}</p>
      })}
    </div>
  )
}

/** `/guides` and `/guides/:slug` reading library (§VII.5, §VII.12.2, Phase V.15).
 *  Reads published Postgres guides from `/api/guides` when available and falls
 *  back cleanly to the structured markdown seed (Using Finna, Polity Codex,
 *  Quick Revision, Tenses & Voice) with zero embedded HTML. */
export default function Guides() {
  const { slug } = useParams()
  const [query, setQuery] = useState('')
  const [apiGuides, setApiGuides] = useState<GuideDoc[] | null>(null)
  const [apiDoc, setApiDoc] = useState<GuideDoc | null>(null)

  useEffect(() => {
    let live = true
    if (slug) {
      setApiDoc(null)
      fetch('/api/guides/' + encodeURIComponent(slug))
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (live && data && data.slug) setApiDoc(data)
        })
        .catch(() => {})
    } else {
      fetch('/api/guides')
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (live && Array.isArray(data?.items) && data.items.length) setApiGuides(data.items)
        })
        .catch(() => {})
    }
    return () => {
      live = false
    }
  }, [slug])

  const catalog = apiGuides && apiGuides.length ? apiGuides : SEED_GUIDES
  const filteredCatalog = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return catalog
    return catalog.filter((g) =>
      `${g.title} ${g.summary} ${g.subject_label || ''}`.toLowerCase().includes(q),
    )
  }, [catalog, query])

  if (slug) {
    const doc = apiDoc || SEED_GUIDES.find((g) => g.slug === slug)
    if (!doc) {
      return (
        <div className="mx-auto max-w-[850px] px-4 py-12 sm:px-6" data-screen="guides">
          <Link to="/guides" className="text-sm font-semibold text-link hover:underline">
            ← All guides
          </Link>
          <h1 className="mt-4 text-2xl font-bold text-ink">Guide not found</h1>
          <p className="mt-2 text-base text-secondary">
            Only published first-party guides appear here.
          </p>
        </div>
      )
    }

    return (
      <div className="mx-auto max-w-[1160px] px-4 pb-20 pt-8 sm:px-6" data-screen="guides">
        <div className="grid items-start gap-8 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto">
            <Link to="/guides" className="text-sm font-semibold text-link hover:underline">
              ← All guides
            </Link>
            <nav aria-label="Guide chapters" className="mt-4 hidden lg:block">
              <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">
                Chapters ({doc.chapters.length})
              </p>
              <ul className="mt-2 space-y-2 border-l border-hairline pl-3 text-sm">
                {doc.chapters.map((ch) => (
                  <li key={ch.anchor}>
                    <a href={'#' + ch.anchor} className="text-secondary hover:text-link hover:underline">
                      {ch.heading}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
            <details className="mt-4 rounded-lg border border-hairline bg-card p-3 lg:hidden">
              <summary className="cursor-pointer text-sm font-semibold text-ink">
                Contents ({doc.chapters.length} chapters)
              </summary>
              <ul className="mt-2 space-y-2 text-sm">
                {doc.chapters.map((ch) => (
                  <li key={ch.anchor}>
                    <a href={'#' + ch.anchor} className="text-link hover:underline">
                      {ch.heading}
                    </a>
                  </li>
                ))}
              </ul>
            </details>
          </aside>

          <article className="min-w-0 max-w-[850px]">
            <header className="border-b border-hairline pb-5">
              <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">
                {doc.subject_label || doc.subject_id || 'Guide'} · {doc.reading_minutes} min read ·{' '}
                {doc.chapters.length} chapters
              </p>
              <h1 className="mt-1 text-2xl font-bold text-ink">{doc.title}</h1>
              <p className="mt-2 text-base text-secondary">{doc.summary}</p>
            </header>

            <div className="mt-8 space-y-10">
              {doc.chapters.map((ch) => {
                const practiceHref =
                  ch.question_ids && ch.question_ids.length
                    ? '/practice/build?' +
                      new URLSearchParams(ch.question_ids.map((id) => ['ids', id])).toString()
                    : ch.practice_query || '/practice'
                return (
                  <section key={ch.anchor} id={ch.anchor} className="scroll-mt-24 border-b border-hairline pb-8 last:border-0">
                    <h2 className="text-lg font-bold text-ink">{ch.heading}</h2>
                    <GuideMarkdown text={ch.body_markdown} />
                    <div className="mt-4">
                      <Link
                        to={practiceHref}
                        className="inline-flex min-h-11 items-center rounded-lg border border-ink px-4 py-2 text-sm font-semibold text-ink hover:bg-canvas"
                      >
                        Practice this chapter →
                      </Link>
                    </div>
                  </section>
                )
              })}
            </div>
          </article>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[850px] px-4 pb-20 pt-8 sm:px-6" data-screen="guides">
      <header className="border-b border-hairline pb-5">
        <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">First-party reading</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Guides</h1>
        <p className="mt-2 text-base text-secondary">
          Edited study guides linked directly to bank questions. Free to read.
        </p>
        <div className="mt-4">
          <input
            type="search"
            aria-label="Search guides"
            placeholder="Search guides by title or subject…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-h-11 w-full rounded-lg border border-hairline2 bg-card px-3 text-sm text-ink"
          />
        </div>
      </header>

      <ul className="mt-6 divide-y divide-hairline">
        {filteredCatalog.map((g) => (
          <li key={g.slug} className="py-5">
            <Link to={'/guides/' + g.slug} className="group block">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-lg font-bold text-link group-hover:underline">{g.title}</h2>
                <span className="font-mono text-xs text-muted">
                  {g.subject_label || g.subject_id || 'Guide'} · {g.reading_minutes} min read
                </span>
              </div>
              <p className="mt-1 text-base text-secondary">{g.summary}</p>
            </Link>
          </li>
        ))}
        {!filteredCatalog.length && (
          <li className="py-8 text-sm text-secondary">No published guides match that search.</li>
        )}
      </ul>

      <section className="mt-10 border-t border-hairline pt-6">
        <h2 className="text-base font-bold text-ink">From the community</h2>
        <p className="mt-1 text-sm text-secondary">
          Looking for notes and summaries written by other learners? Those live separately in community materials.
        </p>
        <div className="mt-3 flex flex-wrap gap-4 text-sm font-semibold">
          <Link to="/materials" className="text-link hover:underline">
            Browse community materials →
          </Link>
          <Link to="/library" className="text-link hover:underline">
            Browse by subject →
          </Link>
        </div>
      </section>
    </div>
  )
}
