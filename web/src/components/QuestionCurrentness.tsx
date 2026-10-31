import {questionCurrentness} from '../lib/questionCurrentness'

/** A possible time-dependent fact, not an automated claim that an answer is wrong. */
export default function QuestionCurrentness({question,year,topic}:{question:string;year?:number|null;topic?:string|null}) {
  const hint=questionCurrentness(question,topic||'')
  if(!hint)return null
  return <aside role="note" className="my-3 rounded-[9px] border border-[#E9D8B4] bg-[#FBF4E6] px-3 py-2 text-[12px] leading-relaxed text-[#684919]">
    <strong>Check the date.</strong> {year?`Read “current”, “present” or “recent” in the context of the ${year} paper.`:'The source date is not recorded; check the original PDF before relying on a time-dependent answer.'} This fact may have changed. A past-paper answer is not a statement about today.
    <details className="mt-1"><summary className="min-h-8 cursor-pointer py-1 font-semibold">Revision hint &amp; current reference</summary><p className="mt-1">Check the exact exam date in the source PDF, especially when an officeholder changed during that year. Learn the answer at the time of the exam first. Then compare it with a dated official update and note what changed. The historical key and your score remain tied to the original question. This hint does not verify either answer.</p>{hint.update&&<p className="mt-2"><strong>Revision note · checked {hint.update.checkedOn}.</strong> {hint.update.note}</p>}{hint.reference&&<a href={hint.reference.url} target="_blank" rel="noreferrer" className="mt-2 inline-flex min-h-9 items-center font-semibold underline">{hint.reference.label} ↗</a>}<p className="mt-1">Found an outdated explanation? Use Suggest a correction below and include the effective date and source.</p></details>
  </aside>
}
