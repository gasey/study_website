import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCollection, isLaterExamCollection, type CollectionDetail } from '../lib/api'

/** One exam's landing page — the prototype's `module` screen, line 1700.
 *  See docs/DESIGN-FIDELITY.md: "module" is the old name, and the
 *  prototype's `exam` screen is the timed paper, not this. */
export default function ExamPage() {
  const { id = '' } = useParams()
  const [c, setC] = useState<CollectionDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setC(null)
    setError(null)
    getCollection(id).then(setC).catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-[14px] border border-mypick bg-mypick-soft p-5 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to="/exams" className="label mt-4 inline-block underline">← Exams</Link>
      </div>
    )
  }
  if (!c) return <div className="mx-auto max-w-shell px-6 py-10 label">Loading…</div>

  if (isLaterExamCollection(c)) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-[14px] border border-hairline bg-card p-6">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted">Planned for later</div>
          <h1 className="mt-2 font-display text-[28px] font-medium">This exam is not open yet</h1>
          <p className="mt-2 text-[14px] text-secondary">We’ll add LDE exam practice as the exam library grows.</p>
        </div>
        <Link to="/exams" className="label mt-4 inline-block underline">← Exams</Link>
      </div>
    )
  }

  const general = c.section_list.filter((s) => s.path.startsWith('general/'))
  const technical = c.section_list.filter((s) => s.path.startsWith('technical/'))
  const papers = c.section_list.reduce((n, s) => n + s.papers, 0)

  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-8">
      <Link to="/exams" className="text-[13px] text-secondary">← Exams</Link>

      {/* Tinted header block, markup line 1702. Exams area colour. */}
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4 rounded-xl bg-exams-soft p-6">
        <div className="min-w-0">
          <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-exams-dark">
            {c.kind} · Exam collection
          </div>
          <h1 className="mt-2 font-display text-[clamp(32px,4.6vw,48px)] font-medium -tracking-[0.02em]">
            {c.title}
          </h1>
          <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5 text-[14px] text-[#2E2A24]">
            <span>{papers} papers</span>
            <span>{c.scorable.toLocaleString('en-IN')} scorable questions</span>
            <span>{c.sections} sections</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/exams/${c.id}/mock`}
            className="whitespace-nowrap rounded-pill bg-ink px-[18px] py-2.5 text-[14px] font-semibold text-paper"
          >
            Start a mock
          </Link>
          <Link
            to="/bank"
            className="whitespace-nowrap rounded-pill border border-ink px-[17px] py-[9px] text-[14px] font-semibold"
          >
            Browse the bank
          </Link>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-start gap-7">
        {/* "Where the marks are" — share of scorable questions per section. The
            prototype charts topics; ours are sections until classification
            gives us topics to chart. */}
        <section className="min-w-0 flex-[2_1_480px]">
          <div className="flex flex-wrap items-baseline justify-between gap-2.5 border-b border-hairline pb-2.5">
            <h2 className="font-display text-[26px] font-medium">Where the marks are</h2>
            <span className="text-[13px] text-secondary">Share of scorable questions</span>
          </div>
          {c.section_list.map((s) => (
            <div
              key={s.path}
              className="grid items-center gap-3.5 border-b border-hairline2 py-2.5 [grid-template-columns:minmax(120px,200px)_minmax(0,1fr)_48px]"
            >
              <span className="text-[14px]">{s.title}</span>
              <div className="h-2 rounded-[4px] bg-[#E8DFCC]">
                <div
                  className="h-2 rounded-[4px] bg-exams"
                  style={{ width: `${c.scorable ? Math.round((s.scorable / c.scorable) * 100) : 0}%` }}
                  role="progressbar"
                  aria-label={`${s.title}: ${s.scorable.toLocaleString('en-IN')} scorable questions`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={c.scorable ? Math.round((s.scorable / c.scorable) * 100) : 0}
                />
              </div>
              <span className="text-right font-mono text-[12px]">{s.scorable}</span>
            </div>
          ))}
        </section>

        <aside className="flex min-w-0 max-w-[380px] flex-[1_1_280px] flex-col gap-3.5">
          <div className="rounded-[14px] bg-practice-soft p-[18px]">
            <div className="text-[14px] font-semibold">Mocks use reliable answer keys</div>
            <p className="mt-1.5 text-[13px] leading-snug text-[#2E2A24]">
              {c.scorable.toLocaleString('en-IN')} questions can be used in scored practice.
              Derived and unverified answers stay out of mocks.
            </p>
          </div>
        </aside>
      </div>

      <Group title="General papers" items={general} examId={c.id} />
      <Group title="By trade" items={technical} examId={c.id} />
    </div>
  )
}

function Group({
  title,
  items,
  examId,
}: {
  title: string
  items: { path: string; title: string; papers: number; scorable: number }[]
  examId: string
}) {
  if (!items.length) return null
  return (
    <section className="mt-9">
      <h2 className="font-display text-[26px] font-medium">{title}</h2>
      <div className="mt-3 grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(260px,1fr))]">
        {items.map((s) => (
          <Link
            key={s.path}
            to={`/exams/${examId}/mock?section=${encodeURIComponent(s.path)}`}
            className="flex flex-col gap-2 rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)] transition-shadow hover:shadow-[0_8px_24px_rgba(29,27,24,.12)]"
          >
            <span className="flex items-center gap-2 text-[12.5px] font-semibold">
              <span className="h-2 w-2 rounded-full bg-exams" />
              {s.papers} paper{s.papers === 1 ? '' : 's'}
            </span>
            <div className="font-display text-[21px] font-medium leading-tight">{s.title}</div>
            <div className="flex-1 text-[14px] leading-[1.55] text-[#2E2A24]">
              {s.scorable.toLocaleString('en-IN')} scorable questions
            </div>
            <span className="text-[12px] font-semibold">Start this section →</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
