import {questionCurrentness} from '../lib/questionCurrentness'

/** Possible date sensitivity; editorial notes never replace a historical key. */
export default function QuestionCurrentness({question,year,topic,revealed=false,variant='full'}:{question:string;year?:number|null;topic?:string|null;revealed?:boolean;variant?:'full'|'summary'|'details'}) {
  const canShow=revealed
  const hint=questionCurrentness(question,topic||'',year)
  if(!hint)return null
  const update=hint.update
  if(variant==='summary')return <p role="note" aria-label="Historical answer context" className="mt-1 text-[11px] text-muted">{year?`For the ${year} exam`:'Answer for the exam date'}{update?' · dated revision note available':''}</p>
  const revision=<>
      {!canShow?<p className="mt-1">Check or show the answer to read revision notes and references.</p>:update?<div className="mt-2 space-y-2">
        {update.historicalContext&&<p><strong>Historical context.</strong> {update.historicalContext}</p>}
        <p><strong>Dated revision note · as of {update.effectiveOn}.</strong> {update.note}</p>
        <p><strong>Revision hint.</strong> {update.revisionHint}</p>
        <p className="text-[11px]">Source checked {update.checkedOn} · {update.stale?'Recheck due; this is an archived note, not a verified statement about today.':`Next review due ${update.reviewBy}.`}</p>
        <a href={update.reference.url} target="_blank" rel="noreferrer" className="inline-flex min-h-9 items-center font-semibold underline">{update.reference.label} ↗</a>
        <p>This note does not verify or replace the exam answer or its explanation.</p>
      </div>:<><p className="mt-1">No question-specific dated update has been checked here yet. Learn the answer for the exam date, then compare a dated primary source. A topic reference alone does not verify an update.</p>{hint.reference&&<a href={hint.reference.url} target="_blank" rel="noreferrer" className="mt-2 inline-flex min-h-9 items-center font-semibold underline">{hint.reference.label} ↗</a>}</>}
  </>
  if(variant==='details')return <aside role="note" aria-label="Exam date and revision context" className="text-[12px] leading-relaxed">
    <p className="font-semibold">{year?`Answer for the ${year} exam`:'Answer for the exam date'}</p>{revision}
  </aside>
  return <aside role="note" aria-label="Exam date and revision context" className="my-3 rounded-[9px] border border-[#E9D8B4] bg-[#FBF4E6] px-3 py-2 text-[12px] leading-relaxed text-[#684919]">
    <strong>At the exam date.</strong> {year?`Answer for the ${year} paper.`:'Check the exam date in the source PDF.'}
    <details className="mt-1"><summary className="min-h-11 cursor-pointer py-2 font-semibold">Revision context{update?' · dated note available':''}</summary>{revision}</details>
  </aside>
}
