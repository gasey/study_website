import {lazy,Suspense} from 'react'
const AdjustedMockResults=lazy(()=>import('./AdjustedMockResults'))
import { Link } from 'react-router-dom'
import {SourceQuestionContext,SourceQuestionText} from './SourceQuestionText'
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
          Original result · {result.answer_mode === 'derived-practice' ? 'Practice estimate' : 'Official-key mock'}
        </div>
        {result.answer_mode === 'derived-practice' && <p className="mt-2 text-[13px] leading-snug text-[#684919]">This saved estimate may include derived answers. Its original grading is retained. New estimates admit only published reviewed derived answers; adjusted results use current scoring eligibility.</p>}
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

      {result.score_breakdown&&<p className="mt-3 text-[13px] text-secondary">Original official-key subset: {result.score_breakdown.official_subset.scorable_total?`${result.score_breakdown.official_subset.score} / ${result.score_breakdown.official_subset.maximum} marks across ${result.score_breakdown.official_subset.scorable_total} questions`:'No official-key subset'}.</p>}
      {result.legacy_unversioned&&<p className="mt-3 text-[13px] text-secondary">Legacy result: original question text and keys were not saved. Recorded marks remain original; review text may reflect the current catalogue.</p>}
      <Suspense fallback={<p className="mt-5 text-[13px] text-muted">Loading adjusted results…</p>}><AdjustedMockResults mockId={result.id}/></Suspense>
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
              {r.answer_source === 'derived' && <span className="rounded-pill bg-[#FFF4DF] px-2 py-1 text-[10px] text-[#684919]">Derived · not an official key</span>}
              <span className="grow" />
              <Link to={`/bank/${r.question_id}`} className="text-link">
                Open ↗
              </Link>
            </div>
            <div className="mt-3"><SourceQuestionContext direction={r.direction} passage={r.passage}/></div>
            <p className="mt-2 font-display text-[19px] leading-snug"><SourceQuestionText text={r.question_markup ?? r.question}/></p>
            {r.figure_image_url && <a href={r.figure_image_url} target="_blank" rel="noreferrer" className="mt-3 block max-w-2xl rounded-[8px] border border-hairline bg-paper p-2" aria-label="Open original question figure"><img src={r.figure_image_url} loading="lazy" decoding="async" alt="Original figure shown in this test" className="max-h-[360px] w-full object-contain"/></a>}
            <div className="mt-2 grid gap-1 text-[14px]">
              {r.chosen_text && (
                <span className={r.correct ? 'text-keyed' : 'text-mypick'}>
                  You chose: <SourceQuestionText text={r.chosen_text}/>
                </span>
              )}
              {!r.correct && <span className="text-keyed">{r.answer_text?`Answer: ${r.answer_text}`:'Original key unavailable'}</span>}
            </div>
            {r.explanation && (
              <p className="mt-2 text-[14px] leading-[1.6] text-secondary"><SourceQuestionText text={r.explanation}/></p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
