import {useRef,useState,useEffect} from 'react'
import {Link,useNavigate,useSearchParams} from 'react-router-dom'
import {revealAnswer,getNextQuestion,type AnswerResult,type ViewedAnswer} from '../lib/api'
import {getPracticeState} from '../lib/practiceState'
import {getDesk,getDeskSync,saveDesk,flushDesk,subscribeDesk} from '../lib/desk'
import {scopeLink} from '../lib/examScope'
import type {AnswerContext} from '../lib/answerStatus'
import AnswerProvenance from './AnswerProvenance'
import AnswerComparison from './AnswerComparison'
import QuestionExplanation from './QuestionExplanation'
import QuestionCurrentness from './QuestionCurrentness'
import RewardOutcome from './RewardOutcome'
import {SourceQuestionText} from './SourceQuestionText'

/** Views are restored privately; only checked results reach attempt/progress handlers. */
export default function PracticeAnswerPanel({qid,paperId,question,year,topic,context,result,available=true,disabled=false,onViewed,onBusy,onRetry,onNext}: {
 qid:string;paperId?:string|null;question:string;year?:number|null;topic?:string;
 context:AnswerContext;result?:AnswerResult|null;available?:boolean;disabled?:boolean;
 onViewed:(viewed:boolean)=>void;onBusy?:(busy:boolean)=>void;onRetry?:()=>void;onNext?:()=>void|Promise<void>
}) {
 const nav=useNavigate(),[params]=useSearchParams()
 const [viewed,setViewed]=useState<ViewedAnswer|null>(null),[busy,setBusy]=useState(false),[restoring,setRestoring]=useState(true),[error,setError]=useState('')
 const [deadline,setDeadline]=useState(0),[now,setNow]=useState(Date.now),[restricted,setRestricted]=useState(''),[revisionMessage,setRevisionMessage]=useState('')
 const [deskVersion,setDeskVersion]=useState(0),[actionBusy,setActionBusy]=useState(false)
 const callbacks=useRef({onViewed,onBusy,onRetry,onNext});callbacks.current={onViewed,onBusy,onRetry,onNext}
 const active=useRef(true),generation=useRef(0),inFlight=useRef(false)
 useEffect(()=>{active.current=true;return()=>{active.current=false;generation.current++}},[])
 useEffect(()=>subscribeDesk(()=>setDeskVersion(n=>n+1)),[])
 void deskVersion
 useEffect(()=>{
  let live=true
  async function restore(){
   const run=++generation.current
   setRestoring(true);setViewed(null);setRestricted('');setError('');callbacks.current.onViewed(false);callbacks.current.onBusy?.(true)
   try{
    const state=await getPracticeState(qid,paperId)
    if(!live||run!==generation.current)return
    if(state.restricted){setRestricted(state.message||'Finish your active test before reading this answer.');callbacks.current.onViewed(true)}
    else if(state.viewed){setViewed(state.answer);setDeadline(Date.now()+state.retry_after_seconds*1000);setNow(Date.now());callbacks.current.onViewed(true)}
   }catch(e){if(live&&run===generation.current)setError((e as Error).message)}
   finally{if(live&&run===generation.current){setRestoring(false);callbacks.current.onBusy?.(false)}}
  }
  if(!result)void restore();else setRestoring(false)
  const refresh=()=>{if(live)void restore()}
  const authRefresh=()=>{callbacks.current.onRetry?.();refresh()}
  const answerRefresh=(event:Event)=>{if((event as CustomEvent).detail?.qid===qid)refresh()}
  window.addEventListener('ism-auth-change',authRefresh);window.addEventListener('ism-answer-viewed',answerRefresh)
  return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',authRefresh);window.removeEventListener('ism-answer-viewed',answerRefresh)}
 },[qid,paperId,result])
 useEffect(()=>{if(!viewed)return;const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(timer)},[viewed])
 async function show(){
  if(inFlight.current||disabled||result||viewed||restoring)return
  const run=++generation.current;inFlight.current=true;setBusy(true);setError('');onBusy?.(true)
  try{
   const answer=await revealAnswer(qid,paperId)
   if(active.current&&run===generation.current){setViewed(answer);setDeadline(Date.now()+answer.retry_after_seconds*1000);setNow(Date.now());onViewed(true);window.dispatchEvent(new CustomEvent('ism-answer-viewed',{detail:{qid}}))}
  }catch(e){if(active.current&&run===generation.current)setError((e as Error).message)}
  finally{inFlight.current=false;if(active.current){setBusy(false);onBusy?.(false)}}
 }
 async function next(){
  if(callbacks.current.onNext){await callbacks.current.onNext();return}
  const next=await getNextQuestion(qid,paperId)
  if(!active.current)return
  if(!next.question_id){setRevisionMessage('You reached the end of this paper. Choose another paper or revisit saved questions.');return}
  const query=new URLSearchParams({paper:next.paper_id});if(params.get('exam'))query.set('exam',params.get('exam')!)
  nav(scopeLink('/bank/'+next.question_id+'?'+query));window.scrollTo({top:0,behavior:'auto'})
 }
 async function save(forLater=false){
  if(getDeskSync().loading)throw new Error('Your study desk is still loading. Please retry in a moment.')
  const desk=getDesk(),saved=desk.saved.includes(qid)
  if(!saved&&desk.saved.length>=500)throw new Error('Your 500 saved-question places are full. Remove a saved question first.')
  saveDesk({...desk,saved:forLater||!saved?[qid,...desk.saved.filter(id=>id!==qid)]:desk.saved.filter(id=>id!==qid)})
  await flushDesk()
  const sync=getDeskSync()
  if(sync.status==='error'||sync.status==='conflict')throw new Error(sync.error||'Saved in this browser; account sync needs attention in Study desk.')
  setRevisionMessage(forLater?'Saved for later revision.':saved?'Removed from saved revision.':'Saved for revision.')
  if(forLater)await next()
 }
 async function action(task:()=>Promise<void>){if(actionBusy)return;setActionBusy(true);setError('');try{await task()}catch(e){if(active.current)setError((e as Error).message)}finally{if(active.current)setActionBusy(false)}}
 function retry(){setViewed(null);setError('');setDeadline(0);onViewed(false);onRetry?.()}
 const answer=result||viewed,remaining=Math.max(0,Math.ceil((deadline-now)/60000)),saved=getDesk().saved.includes(qid)
 const control='min-h-11 rounded-pill border border-hairline bg-card px-4 py-2 text-[13px] font-semibold disabled:opacity-40'
 if(restoring&&!result)return <p role="status" className="mt-3 text-[12px] text-muted">Restoring your practice state…</p>
 if(restricted)return <p role="status" className="mt-3 rounded-[10px] border border-hairline bg-paper p-3 text-[13px] text-secondary">{restricted}</p>
 return <div className="mt-3">
  {!available&&!answer?<AnswerComparison qid={qid} paperId={paperId}/>:!answer&&<><button type="button" disabled={busy||disabled} onClick={()=>void show()} className={control+' text-link'}>{busy?'Opening…':'Show answer'}</button><p className="mt-1 text-[12px] text-muted">Show answer is for reading: no attempt, accuracy credit or rewards. Retry after 30 minutes.</p></>}
  {error&&<p role="alert" className="mt-2 text-[13px] text-mypick">{error}</p>}
  {answer&&<section aria-label="Answer and explanation" className="rounded-[10px] border border-hairline bg-paper p-4 text-[14px]">
   <strong>{!result?'Viewed answer':!result.verified&&!context.reviewed?(result.correct?'Matches stored answer':'Differs from stored answer'):result.correct?'Correct':'Not quite'}</strong>
   {!result&&<p className="mt-1 text-[12px] text-muted">No attempt or reward recorded. {remaining>0?`Retry available in ${remaining} ${remaining===1?'minute':'minutes'}.`:'Ready for a fresh attempt.'}</p>}
   {!result&&remaining===0&&onRetry&&<button type="button" onClick={retry} className={control+' mt-2 text-link'}>Retry now</button>}
   <div className="mt-2"><SourceQuestionText text={answer.answer_text}/></div>
   <div className="mt-2"><AnswerProvenance source={answer.answer_source} {...context}/></div>
   <QuestionExplanation explanation={answer.explanation} source={answer.answer_source} context={context} questionId={qid}/>
   <QuestionCurrentness revealed question={question} year={year} topic={topic}/>
   {result&&<RewardOutcome reward={result.reward}/>}
   <nav aria-label="Continue studying" className="mt-4 flex flex-wrap gap-2">
    <button type="button" disabled={actionBusy||getDeskSync().loading} aria-pressed={saved} onClick={()=>void action(()=>save())} className={control}>{saved?'Saved for revision':'Save for revision'}</button>
    <button type="button" disabled={actionBusy||getDeskSync().loading} onClick={()=>void action(()=>save(true))} className={control}>Retry later</button>
    <button type="button" disabled={actionBusy} onClick={()=>void action(next)} className={control+' text-link'}>Next question →</button>
   </nav>
   {revisionMessage&&<p role="status" className="mt-2 text-[12px] text-secondary">{revisionMessage} <Link to={scopeLink('/desk?tab=bookmarks')} className="text-link underline">Saved questions</Link></p>}
   <AnswerComparison qid={qid} paperId={paperId}/>
  </section>}
 </div>
}
