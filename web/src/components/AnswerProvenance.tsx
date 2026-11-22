import type { AnswerSource } from '../lib/api'
import {answerStatus,answerStatusAppearance,type AnswerContext} from '../lib/answerStatus'
export function answerProvenance(source:AnswerSource,reviewed=false){return answerStatus(source,{reviewed})}
export function evidenceLink(questionId:string) {
  return '/create/new?'+new URLSearchParams({question:questionId,kind:'answer',intent:'verify'})
}
/** Part VII (§VII.6, §VII.6.2):
 *  - Learner mode (default): trusted answers render no badge at all;
 *    unverified/provisional answers render an always-visible amber "Not verified" line;
 *    disputed answers render an always-visible "Answer disputed" line;
 *    descriptive prompts render a plain "Written question" line.
 *  - Staff mode (`staff={true}`): keeps the full five-state expandable badge. */
export default function AnswerProvenance({source,reviewed=false,disputed=false,defect=null,questionType='mcq',statusOverride,keyStatus=null,hasConflict=false,outlined=false,staff=false}:{source:AnswerSource;reviewed?:boolean;questionId?:string;outlined?:boolean;staff?:boolean}&AnswerContext) {
  const info=answerStatus(source,{reviewed,disputed,defect,questionType,statusOverride,keyStatus,hasConflict})
  if(!staff){
    if(!info.learnerLabel)return null
    if(info.status==='written'){
      return <span data-answer-status="written" className="text-xs font-medium text-secondary">Written question</span>
    }
    const isDisputed=info.learnerLabel==='Answer disputed'
    return <span
      data-answer-status={isDisputed?'disputed':info.status}
      title={info.description+' '+info.scoring}
      className={'inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold '+(isDisputed?'border-wrong bg-wrong-soft text-wrong-dark':'border-exams bg-exams-soft text-exams-dark')}
    >
      {info.learnerLabel}
    </span>
  }
  const label=info.label
  const appearance=answerStatusAppearance(info.learnerLabel==='Answer disputed'?'disputed':info.status)
  return <details data-answer-status={info.status} className="max-w-full text-left open:w-full open:basis-full">
    <summary title={info.description+' '+info.scoring} aria-label={label+' — answer source'} className={'inline-flex min-h-[44px] cursor-pointer list-none items-center gap-1 rounded-pill px-2 py-1 font-mono text-xs uppercase tracking-[.04em] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 '+'border '+appearance.badge+(outlined?' ring-1 ring-inset ring-black/5':'' )}><span aria-hidden="true" className="mr-1 text-sm font-bold">{appearance.symbol}</span>{label} <span aria-hidden="true">ⓘ</span></summary>
    <div role="note" className="mt-2 w-full max-w-[680px] rounded-[10px] border border-hairline bg-card p-4 font-sans text-sm font-normal normal-case leading-relaxed tracking-normal text-secondary">
      <p className="font-semibold text-ink">{info.label}</p>
      <p className="mt-2">{info.description}</p><p className="mt-2">{info.scoring}</p>
    </div>
  </details>
}
