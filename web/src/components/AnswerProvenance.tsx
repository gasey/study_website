import { Link } from 'react-router-dom'
import type { AnswerSource } from '../lib/api'
export function answerProvenance(source:AnswerSource,reviewed=false){return answerStatus(source,{reviewed})}
import {answerStatus,answerStatusAppearance,type AnswerContext} from '../lib/answerStatus'
export function evidenceLink(questionId:string) {
  return '/contribute/new?'+new URLSearchParams({question:questionId,kind:'answer',intent:'verify'})
}
/** Native hover text plus keyboard/touch expandable help. In-flow content avoids
 * clipped tooltips at narrow viewport edges and does not disclose an answer. */
export default function AnswerProvenance({source,reviewed=false,disputed=false,defect=null,questionType='mcq',statusOverride,questionId,outlined=false}:{source:AnswerSource;reviewed?:boolean;questionId?:string;outlined?:boolean}&AnswerContext) {
  const info=answerStatus(source,{reviewed,disputed,defect,questionType,statusOverride})
  const appearance=answerStatusAppearance(info.status)
  return <details data-answer-status={info.status} className="max-w-full text-left open:w-full open:basis-full">
    <summary title={info.description+' '+info.scoring} aria-label={info.label+' — meaning and how to contribute'} className={'inline-flex min-h-[44px] cursor-pointer list-none items-center gap-1 rounded-pill px-2 py-1 font-mono text-[10px] uppercase tracking-[.04em] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 '+'border '+appearance.badge+(outlined?' ring-1 ring-inset ring-black/5':'' )}><span aria-hidden="true" className="mr-1 text-[13px] font-bold">{appearance.symbol}</span>{info.label} <span aria-hidden="true">ⓘ</span></summary>
    <div role="note" className="mt-2 w-full max-w-[680px] rounded-[10px] border border-hairline bg-[#FBF8F1] p-4 font-sans text-[13px] font-normal normal-case leading-relaxed tracking-normal text-secondary shadow-sm">
      <p className="font-semibold text-ink">{info.label}</p><p className="mt-1 text-[12px]">Question format: {questionType==='mcq'?'MCQ (multiple choice)':'Written response'}. Answer source: {info.sourceDetail}.</p><p className="mt-2">“Derived” describes how an answer was established, not the question format. An MCQ can have an official-key answer or a derived solution. Explanation availability and review are shown separately after answering.</p><p className="mt-2">{info.description}</p><p className="mt-2">{info.scoring}</p>
      {questionType==='mcq'&&<><p className="mt-3">Help strengthen the answer: explain each step, cite a reliable source and identify the exact question. Community answer proposals require independent review. An authorized administrator can also publish a recorded correction directly; Official key still requires a mapped authority key. Upvotes help discussion; they do not approve a key.</p>
      {questionId&&<Link to={evidenceLink(questionId)} className="mt-3 inline-flex min-h-[44px] items-center font-semibold text-link underline">Submit evidence or a worked solution →</Link>}
      <p className="mt-2 text-[12px]">An eligible answer improvement earns 10 contribution points after publication. Submissions, repeated claims and votes alone earn no publication credit. Contribution points are separate from study XP and spendable rewards.</p></>}
    </div>
  </details>
}
