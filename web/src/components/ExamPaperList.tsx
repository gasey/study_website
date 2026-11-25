import { paperBrowseLink } from '../lib/browsePosition'
import { groupSourceBooklets, representativeBooklet, withoutBooklet } from '../lib/sourceBooklets'
import { bookletLabel, type BookletGroup } from '../lib/mcsBooklets'
import { Link } from 'react-router-dom'
import type { CollectionPaper } from '../lib/api'
import { paperIdentity } from '../lib/paperIdentity'

export default function ExamPaperList({
  papers,
  examId,
  groups = groupSourceBooklets(papers),
  layout = 'list',
}: {
  papers: CollectionPaper[]
  examId: string
  groups?: BookletGroup[]
  layout?: 'cards' | 'list'
}) {
  if (layout === 'cards') {
    return (
      <div className="pp-cards-grid" aria-label="Original exam papers">
        {groups.map((group) => {
          const p = representativeBooklet(group)
          const identity = paperIdentity(p)
          const heading =
            group.papers.length > 1
              ? withoutBooklet(identity.exam || p.title)
              : identity.exam || p.title
          const paperLabel = group.papers.length > 1 ? group.title : identity.title
          return (
            <article key={p.id} className="pp-sheet-card">
              <div className="pp-sheet-top">
                <span className="pp-year-stamp">{p.year ?? 'Archive'}</span>
                <span className="pp-q-badge">
                  {p.questions.toLocaleString('en-IN')} Qs
                  {p.descriptive ? ` · ${p.descriptive} written` : ''}
                </span>
              </div>

              <h3 className="pp-sheet-title">
                {p.questions > 0 ? (
                  <Link to={paperBrowseLink(examId, p.id)}>{heading}</Link>
                ) : (
                  heading
                )}
              </h3>
              {paperLabel && paperLabel !== heading && (
                <p className="pp-sheet-sub">{paperLabel}</p>
              )}

              {group.papers.length > 1 && (
                <details className="pp-booklets-drawer">
                  <summary>{group.papers.length} booklet originals (Series A/B/C/D)</summary>
                  <ul>
                    {group.papers.map((source) => (
                      <li key={source.id}>
                        <Link
                          to={`/exams/${examId}/paper?paper=${encodeURIComponent(source.id)}`}
                        >
                          {bookletLabel(source)} →
                        </Link>
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              <div className="pp-sheet-actions">
                {p.questions > 0 && (
                  <Link className="pp-act-primary" to={paperBrowseLink(examId, p.id)}>
                    Browse questions →
                  </Link>
                )}
                {p.allow_practice && p.answerable_count > 0 && (
                  <Link
                    className="pp-act-quiet"
                    to={`/exams/${examId}?view=practice&paper=${encodeURIComponent(p.id)}#exam-question-browser`}
                  >
                    Practice
                  </Link>
                )}
                {p.source_pdf_url && (
                  <a
                    className="pp-act-quiet"
                    href={p.source_pdf_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PDF ↗
                  </a>
                )}
              </div>
            </article>
          )
        })}
      </div>
    )
  }

  return (
    <div
      className="mt-3 overflow-hidden rounded-[18px] border border-hairline bg-card shadow-[var(--ism-card-shadow)]"
      aria-label="Exam and year list"
    >
      <div
        aria-hidden="true"
        className="hidden gap-4 border-b border-hairline bg-canvas px-5 py-3.5 text-xs font-bold uppercase tracking-wider text-secondary md:grid md:grid-cols-[84px_minmax(0,2fr)_minmax(0,1.2fr)_200px]"
      >
        <span>Year</span>
        <span>Examination</span>
        <span>Paper</span>
        <span>Open</span>
      </div>
      <ul className="divide-y divide-hairline">
        {groups.map((group) => {
          const p = representativeBooklet(group)
          const identity = paperIdentity(p)
          return (
            <li
              key={p.id}
              className="grid min-w-0 items-center gap-2 px-5 py-4 transition-colors hover:bg-canvas/50 md:grid-cols-[84px_minmax(0,2fr)_minmax(0,1.2fr)_200px] md:gap-4"
            >
              <span className="inline-flex w-fit rounded-lg bg-exams-soft px-2.5 py-1 font-mono text-xs font-bold text-exams-dark">
                {p.year ?? 'Archive'}
              </span>
              <div className="min-w-0">
                <h3 className="break-words font-reading text-[17px] font-semibold leading-snug text-ink">
                  {group.papers.length > 1
                    ? withoutBooklet(identity.exam || p.title)
                    : identity.exam || p.title}
                </h3>
                <p className="mt-1 text-xs font-medium text-secondary">
                  {p.questions.toLocaleString('en-IN')} questions
                  {p.descriptive ? ` · ${p.descriptive} written` : ''}
                </p>
              </div>
              <div className="min-w-0">
                <p className="break-words text-sm font-medium text-secondary">
                  {group.papers.length > 1 ? group.title : identity.title}
                </p>
                {group.papers.length > 1 && (
                  <details className="mt-1">
                    <summary className="min-h-10 cursor-pointer py-2 text-xs font-bold text-link">
                      {group.papers.length} booklet originals
                    </summary>
                    <ul className="space-y-1 text-xs">
                      {group.papers.map((source) => (
                        <li key={source.id}>
                          <Link
                            className="inline-flex min-h-9 items-center text-link underline"
                            to={`/exams/${examId}/paper?paper=${encodeURIComponent(source.id)}`}
                          >
                            {bookletLabel(source)} →
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm font-bold text-link">
                {p.questions > 0 && (
                  <Link
                    className="inline-flex min-h-10 items-center hover:underline"
                    to={paperBrowseLink(examId, p.id)}
                  >
                    Browse →
                  </Link>
                )}
                {p.source_pdf_url && (
                  <a
                    className="inline-flex min-h-10 items-center text-secondary hover:text-ink hover:underline"
                    href={p.source_pdf_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PDF ↗
                  </a>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
