import { Link } from 'react-router-dom'
import type { Question } from '../lib/api'
import ProvenanceTag, { RepeatBadge } from './ProvenanceTag'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

/** White card on the warm paper background, 10px radius, 1px hairline —
 *  one area colour per card, and for the bank that area is Practice. */
export default function QuestionCard({ q }: { q: Question }) {
  const years =
    q.first_year && q.last_year && q.first_year !== q.last_year
      ? `${q.first_year}–${q.last_year}`
      : (q.last_year ?? q.first_year ?? '—')

  return (
    <Link
      to={`/bank/${q.id}`}
      className="block rounded-card border border-hairline bg-card p-5 transition-shadow hover:shadow-[0_6px_20px_rgba(29,27,24,0.07)]"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="label text-practice-dark">{years}</span>
        <span className="text-hairline2">·</span>
        <span className="label">{q.type === 'mcq' ? 'MCQ' : 'Descriptive'}</span>
        <span className="grow" />
        <RepeatBadge times={q.times_asked} />
        <ProvenanceTag source={q.answer_source} />
      </div>

      <p className="font-display text-[19px] font-medium leading-snug text-ink">{q.question}</p>

      {q.options.length > 0 && (
        <ol className="mt-3 grid gap-1 sm:grid-cols-2">
          {q.options.map((o, i) => (
            <li key={i} className="flex gap-2 text-[14px] text-secondary">
              <span className="label mt-[3px] shrink-0">{LETTERS[i]}</span>
              <span>{o}</span>
            </li>
          ))}
        </ol>
      )}
    </Link>
  )
}
