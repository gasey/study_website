import {Link} from 'react-router-dom'
import type {AnswerSource} from '../lib/api'
import {explanationPresentation,type AnswerContext} from '../lib/answerStatus'
import {SourceQuestionText} from './SourceQuestionText'

/** Render only after an answer/reveal, alongside the answer's own provenance. */
export default function QuestionExplanation({explanation,source,context,questionId}:{explanation?:string|null;source:AnswerSource;context?:AnswerContext;questionId?:string}) {
 const info=explanationPresentation(explanation,source,context)
 return <section aria-label="Explanation" data-explanation-status={info.status} className="mt-3 border-t border-hairline pt-3 text-[13px] leading-relaxed text-secondary">
   <h4 className="font-semibold text-ink">{info.label}</h4>
   <p className="mt-1 text-[12px]">{info.detail}</p>
   {explanation?.trim()&&<div className="mt-2 whitespace-pre-line text-[14px]"><SourceQuestionText text={explanation}/></div>}
   {questionId&&<Link to={'/contribute/new?'+new URLSearchParams({question:questionId,kind:'explanation'})} className="mt-2 inline-flex min-h-11 items-center font-semibold text-link underline">{info.status==='missing'?'Add a supported explanation':'Improve this explanation'} →</Link>}
 </section>
}
