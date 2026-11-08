import {learnerExplanation} from '../lib/answerStatus'
import TestShare from './TestShare'
import {lazy,Suspense,useState} from 'react'
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
  const [outcome,setOutcome]=useState('all')
  const [topic,setTopic]=useState('all')
  const topics=Array.from(new Set(result.review.map(r=>r.topic_label||'Unclassified')))
  const visible=result.review.filter(r=>(topic==='all'||(r.topic_label||'Unclassified')===topic)&&(outcome==='all'||(outcome==='correct'?r.correct:outcome==='wrong'?!!r.chosen_text&&!r.correct:!r.chosen_text)))
  const pct = Math.round((result.n_correct / Math.max(1, result.total)) * 100)
  return (
    <div className="exam-result mx-auto max-w-shell px-6 pb-24 pt-8">
      <Link to={backTo} className="text-[13px] text-secondary">
        {backLabel}
      </Link>

      <div className="mt-3 rounded-xl bg-practice-soft p-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">
          Original result · {result.answer_mode === 'derived-practice' ? 'Practice estimate' : 'Official-key mock'}
        </div>
        {result.answer_mode === 'derived-practice' && <p className="mt-2 text-[13px] leading-snug text-[#684919]">This practice estimate may include worked solutions. Your original result stays available; an updated result uses the answers currently approved for scoring.</p>}
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

      {result.learning_test_id&&<TestShare id={result.learning_test_id} title={result.learning_test_title||'Try this mock test'}/>}
      {result.score_breakdown&&<p className="mt-3 text-[13px] text-secondary">Original score for questions with official keys: {result.score_breakdown.official_subset.scorable_total?`${result.score_breakdown.official_subset.score} / ${result.score_breakdown.official_subset.maximum} marks across ${result.score_breakdown.official_subset.scorable_total} questions`:'No questions with official keys'}.</p>}
      {result.legacy_unversioned&&<p className="mt-3 text-[13px] text-secondary">Legacy result: original question text and keys were not saved. Recorded marks remain original; review text may reflect the current catalogue.</p>}
      <Suspense fallback={<p className="mt-5 text-[13px] text-muted">Loading adjusted results…</p>}><AdjustedMockResults mockId={result.id}/></Suspense>
      <h2 className="mt-8 font-display text-[26px] font-medium">Topic performance</h2>
      <p className="mt-2 text-sm text-secondary">Based on this saved attempt and its original grading. Topic labels are captured for new attempts; older attempts may be unclassified.</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">{topics.map(t=>{const rows=result.review.filter(r=>(r.topic_label||'Unclassified')===t);return <button key={t} onClick={()=>setTopic(t)} className="rounded-panel border border-hairline bg-card p-4 text-left"><b>{t}</b><p className="mt-2 text-sm">{rows.filter(r=>r.correct).length} / {rows.length} correct</p></button>})}</div>
      <h2 className="mt-8 font-display text-[26px] font-medium">Review</h2>
      <div className="my-3 flex flex-wrap gap-3"><label>Outcome <select className="min-h-11 rounded-lg border border-hairline p-2" value={outcome} onChange={e=>setOutcome(e.target.value)}>{['all','correct','wrong','skipped'].map(x=><option key={x} value={x}>{x}</option>)}</select></label><label>Topic <select className="min-h-11 rounded-lg border border-hairline p-2" value={topic} onChange={e=>setTopic(e.target.value)}><option value="all">All topics</option>{topics.map(t=><option key={t}>{t}</option>)}</select></label></div>
      {!visible.length&&<p>No answers match these filters.</p>}
      <div className="mt-3 flex flex-col gap-3">
        {visible.map((r) => (
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
              {r.answer_source === 'derived' && <span className="rounded-pill bg-[#FFF4DF] px-2 py-1 text-[10px] text-[#684919]">Worked solution · unofficial</span>}
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
              <p className="mt-2 text-[14px] leading-[1.6] text-secondary"><SourceQuestionText text={learnerExplanation(r.explanation)}/></p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
