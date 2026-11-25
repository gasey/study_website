import type { ReactNode } from 'react'
import ConceptBook, { type BookTone, bookToneFor } from './ConceptBook'
import { moduleHref, type Collection, type ExamProgressSummary } from '../lib/api'

interface SubjectBookMeta {
  title: string
  subtitle: string
  peek: string
  tone: BookTone
  vol: string
  /** Taxonomy subject_id prefixes that match this book for Focus highlighting. */
  matchTokens: string[]
}

const SUBJECT_BOOK_META: Record<string, SubjectBookMeta> = {
  'subject-gk-gs': {
    title: 'General Knowledge & Studies',
    subtitle: 'Polity, history, economy, geography & Mizoram GK from all MPSC exams.',
    peek: 'All MPSC GK & GS past questions combined into one volume.',
    tone: 'cobalt',
    vol: 'Vol. I',
    matchTokens: ['gk', 'general', 'polity', 'history', 'geography', 'economy', 'science'],
  },
  'subject-english': {
    title: 'English',
    subtitle: 'Grammar, comprehension, idioms, vocabulary & usage from real papers.',
    peek: 'Practise grammar and past English sets from UDC, LDC & MCS together.',
    tone: 'teal',
    vol: 'Vol. II',
    matchTokens: ['english', 'grammar', 'vocab'],
  },
  'subject-mathematics': {
    title: 'Mathematics & Arithmetic',
    subtitle: 'Quantitative aptitude, percentages, ratios, algebra & geometry.',
    peek: 'Worked quantitative questions combined from past recruitment papers.',
    tone: 'plum',
    vol: 'Vol. III',
    matchTokens: ['math', 'arith', 'quant'],
  },
  'subject-reasoning': {
    title: 'Reasoning & Aptitude',
    subtitle: 'Logical sequences, syllogisms, coding & analytical puzzles.',
    peek: 'Build speed on recurring MPSC reasoning & aptitude patterns.',
    tone: 'amber',
    vol: 'Vol. IV',
    matchTokens: ['reason', 'aptitude', 'logic', 'csat'],
  },
  'subject-mizo': {
    title: 'Mizo',
    subtitle: 'Language, literature, proverbs, grammar & Mizoram heritage.',
    peek: 'Authentic Mizo paper questions combined across recruitment grades.',
    tone: 'terracotta',
    vol: 'Vol. V',
    matchTokens: ['mizo'],
  },
}

const ORDER = [
  'subject-gk-gs',
  'subject-english',
  'subject-mathematics',
  'subject-reasoning',
  'subject-mizo',
]

function isBookFocused(collectionId: string, focusedIds: string[]): boolean {
  if (!focusedIds.length) return false
  const meta = SUBJECT_BOOK_META[collectionId]
  const lowered = focusedIds.map((id) => id.toLowerCase())
  const slug = collectionId.replace(/^subject-/, '').toLowerCase()
  if (lowered.some((id) => id === slug || id.includes(slug))) return true
  if (!meta) return false
  return lowered.some((id) => meta.matchTokens.some((tok) => id.includes(tok)))
}

export default function SubjectBookshelf({
  subjects,
  progress,
  focusedSubjectIds = [],
  variant = 'featured',
  eyebrow = 'All-exam subject books',
  heading = 'Study a subject once for every exam',
  subtitle,
  action,
  footer,
}: {
  subjects: Collection[]
  progress?: Record<string, ExamProgressSummary>
  focusedSubjectIds?: string[]
  variant?: 'featured' | 'compact'
  eyebrow?: string
  heading?: string
  subtitle?: string
  action?: ReactNode
  footer?: ReactNode
}) {
  if (!subjects.length) return null

  const resolvedSubtitle =
    subtitle === undefined
      ? `Questions from UDC, LDC, MCS, Group B and other MPSC exams combined into ${subjects.length} subject ${subjects.length === 1 ? 'book' : 'books'} — pull any volume open to practise.`
      : subtitle

  const ordered = [...subjects].sort((a, b) => {
    const ia = ORDER.indexOf(a.id)
    const ib = ORDER.indexOf(b.id)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return b.questions - a.questions
  })

  const totalQs = ordered.reduce((sum, s) => sum + (s.questions || 0), 0)
  const isCompact = variant === 'compact'

  return (
    <section
      aria-label="All-exam subject bookshelf"
      className={`bk-shelf-wrap sb-shelf${isCompact ? ' is-compact' : ''}`}
    >
      <div className="bk-shelf-head">
        <div className="min-w-0">
          <span className="cr-eyebrow">{eyebrow}</span>
          <h2>{heading}</h2>
          {resolvedSubtitle && <p className="sb-shelf-sub">{resolvedSubtitle}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {!isCompact && (
            <span className="finna-st-pill finna-st-pill--teal">
              {ordered.length} books · {totalQs.toLocaleString('en-IN')} Qs
            </span>
          )}
          {action}
        </div>
      </div>

      <div className={`bk-shelf-grid sb-shelf-grid${isCompact ? ' is-compact' : ''}`}>
        {ordered.map((s, idx) => {
          const meta = SUBJECT_BOOK_META[s.id]
          const prog = progress?.[s.id]
          const pct =
            prog && s.questions > 0
              ? Math.min(100, Math.round((prog.unique_questions / s.questions) * 100))
              : null
          const highlighted = isBookFocused(s.id, focusedSubjectIds)
          return (
            <ConceptBook
              key={s.id}
              to={moduleHref(s)}
              title={meta?.title || s.title}
              subtitle={meta?.subtitle}
              eyebrow={highlighted ? '★ Focus' : meta?.vol || `Vol. ${idx + 1}`}
              meta={`${s.questions.toLocaleString('en-IN')} Qs`}
              peekTitle="All-exam volume"
              peekNote={meta?.peek || 'Practise questions from every MPSC exam in one volume.'}
              tone={meta?.tone || bookToneFor(s.id || s.title, idx)}
              compact={isCompact}
              progressPct={pct}
              highlighted={highlighted}
            />
          )
        })}
      </div>

      <div className="bk-shelf-ledge" aria-hidden="true" />

      {footer && <div className="sb-shelf-footer">{footer}</div>}
    </section>
  )
}
