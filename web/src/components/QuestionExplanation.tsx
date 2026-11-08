import {useEffect,useId,useState} from 'react'
import type {AnswerSource} from '../lib/api'
import {explanationPresentation,learnerExplanation,type AnswerContext} from '../lib/answerStatus'
import {SourceQuestionText} from './SourceQuestionText'

/** Only mounted after the existing answer/reveal gate permits access. */
export default function QuestionExplanation({explanation,source,context}:{explanation?:string|null;source:AnswerSource;context?:AnswerContext;questionId?:string;inline?:boolean}) {
 const body=learnerExplanation(explanation)
 const info=explanationPresentation(body,source,context)
 const [expanded,setExpanded]=useState(false)
 const bodyId=useId()
 useEffect(()=>setExpanded(false),[explanation])
 const present=!!body.trim(),long=body.trim().length>600
 if(!present)return null
 return <section aria-label="Explanation" data-explanation-status={info.status} className="answer-explanation">
   <h4 className="answer-explanation-title">Explanation{info.status==='needs-review'?' · awaiting review':''}</h4>
   <div id={bodyId} className={'answer-explanation-body'+(long&&!expanded?' is-condensed':'')}><SourceQuestionText text={body}/></div>
   {long&&<button type="button" aria-expanded={expanded} aria-controls={bodyId} onClick={()=>setExpanded(value=>!value)} className="answer-explanation-more">{expanded?'Show less':'Read more'}</button>}
 </section>
}
