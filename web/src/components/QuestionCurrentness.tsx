import {useState} from 'react'
import {questionCurrentness} from '../lib/questionCurrentness'

/** Possible date sensitivity; editorial notes never replace a historical key. */
export default function QuestionCurrentness({question,year,topic,revealed=false}:{question:string;year?:number|null;topic?:string|null;revealed?:boolean}) {
  const [revealedFor,setRevealedFor]=useState<string|null>(null)
  const contextKey=JSON.stringify([question,year])
  const canShow=revealed||revealedFor===contextKey
  const hint=questionCurrentness(question,topic||'',year)
  if(!hint)return null
  const update=hint.update
  return <aside role="note" aria-label="Exam date and revision context" className="my-3 rounded-[9px] border border-[#E9D8B4] bg-[#FBF4E6] px-3 py-2 text-[12px] leading-relaxed text-[#684919]">
    <strong>At the exam date.</strong> {year?`Read time-sensitive wording in the context of the ${year} paper; check the exact sitting date in the source PDF.`:'The exam date is not recorded. Check the original PDF.'} Historical answers and scores stay tied to that paper.
    <details className="mt-1"><summary className="min-h-8 cursor-pointer py-1 font-semibold">Revision context{update?' · dated note available':''}</summary>
      {!canShow?<div className="mt-1"><p>Answer first, or reveal revision context separately. Notes and references may disclose the answer.</p><button type="button" onClick={()=>setRevealedFor(contextKey)} className="mt-1 inline-flex min-h-11 items-center font-semibold underline">Reveal revision context · may disclose answer</button></div>:update?<div className="mt-2 space-y-2">
        {update.historicalContext&&<p><strong>Historical context.</strong> {update.historicalContext}</p>}
        <p><strong>Dated revision note · as of {update.effectiveOn}.</strong> {update.note}</p>
        <p><strong>Revision hint.</strong> {update.revisionHint}</p>
        <p className="text-[11px]">Source checked {update.checkedOn} · {update.stale?'Recheck due; this is an archived note, not a verified statement about today.':`Next review due ${update.reviewBy}.`}</p>
        <a href={update.reference.url} target="_blank" rel="noreferrer" className="inline-flex min-h-9 items-center font-semibold underline">{update.reference.label} ↗</a>
        <p>This note does not verify or replace the stored answer or its explanation.</p>
      </div>:<><p className="mt-1">No question-specific dated update has been checked here yet. Learn the answer for the exam date, then compare a dated primary source. A topic reference alone does not verify an update.</p>{hint.reference&&<a href={hint.reference.url} target="_blank" rel="noreferrer" className="mt-2 inline-flex min-h-9 items-center font-semibold underline">{hint.reference.label} ↗</a>}</>}
      <p className="mt-2">Use Suggest correction to submit the event or effective date, a direct source link and what changed.</p>
    </details>
  </aside>
}
