import {useEffect,useId,useState} from 'react'
import type {AnswerSource} from '../lib/api'
import {explanationPresentation,type AnswerContext} from '../lib/answerStatus'
import {SourceQuestionText} from './SourceQuestionText'

/** Only mounted after the existing answer/reveal gate permits access. */
export default function QuestionExplanation({explanation,source,context}:{explanation?:string|null;source:AnswerSource;context?:AnswerContext;questionId?:string;inline?:boolean}) {
 const info=explanationPresentation(explanation,source,context)
 const [expanded,setExpanded]=useState(false)
 const bodyId=useId()
 useEffect(()=>setExpanded(false),[explanation])
 const present=!!explanation?.trim(),long=(explanation?.trim().length??0)>600
 return <section aria-label="Explanation" data-explanation-status={info.status} className={present?'answer-explanation':'answer-explanation-missing'}>
   <h4 className="answer-explanation-title">Explanation{info.status==='needs-review'?' · awaiting review':''}</h4>
   {present?<div id={bodyId} className={'answer-explanation-body'+(long&&!expanded?' is-condensed':'')}><SourceQuestionText text={explanation!}/></div>:<p className="answer-explanation-empty">Explanation not available yet.</p>}
   {long&&<button type="button" aria-expanded={expanded} aria-controls={bodyId} onClick={()=>setExpanded(value=>!value)} className="answer-explanation-more">{expanded?'Show less':'Read more'}</button>}
 </section>
}
