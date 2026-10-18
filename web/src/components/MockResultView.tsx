import { Link } from 'react-router-dom'
import type { MockResult } from '../lib/api'

export const mmss = (s: number) =>
  `${String(Math.floor(Math.max(0, s) / 60)).padStart(2, '0')}:${String(Math.max(0, s) % 60).padStart(2, '0')}`

/** Shared by the mock runner (straight after submit) and the standalone
 *  results screen (revisiting a past paper), so the two cannot drift. */
export default function MockResultView({
  result,
  backTo,
  backLabel = '← Exam',
}: {
  result: MockResult
  backTo: string
  backLabel?: string
}) {
  const pct = Math.round((result.n_correct / Math.max(1, result.total)) * 100)
  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-8">
      <Link to={backTo} className="text-[13px] text-secondary">
        {backLabel}
      </Link>

      <div className="mt-3 rounded-xl bg-practice-soft p-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">
          Result
        </div>
        <h1 className="mt-2 font-display text-[clamp(32px,4.6vw,48px)] font-medium -tracking-[0.02em]">
          {result.score} {result.score === 1 ? 'mark' : 'marks'} · {pct}%
        </h1>
        <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5 text-[14px] text-[#2E2A24]">
          <span>{result.n_correct} correct</span>
          <span>{result.n_wrong} wrong</span>
          <span>{result.n_skipped} skipped</span>
          <span>{mmss(result.elapsed_seconds)} taken</span>
        </div>
        {result.late && (
          <p className="mt-2 text-[13px] text-attention-dark">
            ! Submitted after the time limit. The attempt is recorded and marked late.
          </p>
        )}
      </div>

      <h2 className="mt-8 font-display text-[26px] font-medium">Review</h2>
      <div className="mt-3 flex flex-col gap-3">
        {result.review.map((r) => (
          <div
            key={r.question_id}
            className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]"
          >
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.06em]">
              <span className="text-muted">Q{r.position + 1}</span>
              <span
                className={
                  r.correct ? 'text-keyed' : r.chosen_text ? 'text-mypick' : 'text-muted'
                }
              >
                {r.correct ? 'Correct' : r.chosen_text ? 'Wrong' : 'Skipped'}
              </span>
              <span className="grow" />
              <Link to={`/bank/${r.question_id}`} className="text-link">
                Open ↗
              </Link>
            </div>
            <p className="mt-2 font-display text-[19px] leading-snug">{r.question}</p>
            <div className="mt-2 grid gap-1 text-[14px]">
              {r.chosen_text && (
                <span className={r.correct ? 'text-keyed' : 'text-mypick'}>
                  You chose: {r.chosen_text}
                </span>
              )}
              {!r.correct && <span className="text-keyed">Answer: {r.answer_text}</span>}
            </div>
            {r.explanation && (
              <p className="mt-2 text-[14px] leading-[1.6] text-secondary">{r.explanation}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
