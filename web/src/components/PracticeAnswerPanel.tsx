import {useRef,useState,useEffect} from 'react'
import {revealAnswer,type AnswerResult,type ViewedAnswer} from '../lib/api'
import type {AnswerContext} from '../lib/answerStatus'
import AnswerProvenance from './AnswerProvenance'
import AnswerComparison from './AnswerComparison'
import QuestionExplanation from './QuestionExplanation'
import QuestionCurrentness from './QuestionCurrentness'
import RewardOutcome from './RewardOutcome'
import {SourceQuestionText} from './SourceQuestionText'

/** One answer-bearing surface. A view is never passed to attempt/progress handlers. */
export default function PracticeAnswerPanel({qid,paperId,question,year,topic,context,result,available=true,disabled=false,onViewed,onBusy}: {
 qid:string;paperId?:string|null;question:string;year?:number|null;topic?:string;
 context:AnswerContext;result?:AnswerResult|null;available?:boolean;disabled?:boolean;
 onViewed:()=>void;onBusy?:(busy:boolean)=>void
}) {
 const [viewed,setViewed]=useState<ViewedAnswer|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('')
 const active=useRef(true),inFlight=useRef(false)
 useEffect(()=>{active.current=true;return()=>{active.current=false}},[])
 async function show(){
  if(inFlight.current||disabled||result||viewed)return
  inFlight.current=true;setBusy(true);setError('');onBusy?.(true)
  try{const answer=await revealAnswer(qid,paperId);if(active.current){setViewed(answer);onViewed()}}
  catch(e){if(active.current)setError((e as Error).message)}
  finally{inFlight.current=false;if(active.current){setBusy(false);onBusy?.(false)}}
 }
 const answer=result||viewed
 if(!available&&!answer)return <AnswerComparison qid={qid} paperId={paperId}/>
 return <div className="mt-3">
  {!answer&&<><button type="button" disabled={busy||disabled} onClick={()=>void show()} className="min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold text-link disabled:opacity-40">{busy?'Opening…':'Show answer'}</button><p className="mt-1 text-[12px] text-muted">Show answer is for reading: no attempt, accuracy credit or rewards. Retry after 30 minutes.</p></>}
  {error&&<p role="alert" className="mt-2 text-[13px] text-mypick">{error}</p>}
  {answer&&<section aria-label="Answer and explanation" aria-live="polite" className="rounded-[10px] border border-hairline bg-paper p-4 text-[14px]">
   <strong>{!result?'Viewed answer':!result.verified&&!context.reviewed?(result.correct?'Matches stored answer':'Differs from stored answer'):result.correct?'Correct':'Not quite'}</strong>
   {!result&&<p className="mt-1 text-[12px] text-muted">No attempt or reward recorded. Return after 30 minutes for a fresh attempt.</p>}
   <div className="mt-2"><SourceQuestionText text={answer.answer_text}/></div>
   <div className="mt-2"><AnswerProvenance source={answer.answer_source} {...context}/></div>
   <QuestionExplanation explanation={answer.explanation} source={answer.answer_source} context={context} questionId={qid}/>
   <QuestionCurrentness revealed question={question} year={year} topic={topic}/>
   {result&&<RewardOutcome reward={result.reward}/>}
   <AnswerComparison qid={qid} paperId={paperId}/>
  </section>}
 </div>
}
