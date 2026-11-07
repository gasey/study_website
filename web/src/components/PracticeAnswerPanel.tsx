import {useRef,useState,useEffect,type ReactNode} from 'react'
import {Link,useNavigate,useSearchParams} from 'react-router-dom'
import {revealAnswer,getNextQuestion,type AnswerResult,type ViewedAnswer} from '../lib/api'
import {getPracticeState} from '../lib/practiceState'
import {getDesk,getDeskSync,saveDesk,flushDesk,subscribeDesk} from '../lib/desk'
import {scopeLink} from '../lib/examScope'
import {answerFeedbackLabel,answerStatus,type AnswerContext} from '../lib/answerStatus'
import AnswerComparison from './AnswerComparison'
import QuestionExplanation from './QuestionExplanation'
import QuestionCurrentness from './QuestionCurrentness'
import CurrentAffairsConnections from './CurrentAffairsConnections'
import RewardOutcome from './RewardOutcome'
import {SourceQuestionText} from './SourceQuestionText'

/** Views are restored privately; only checked results reach attempt/progress handlers. */
export default function PracticeAnswerPanel({qid,paperId,options,question,year,topic,context,result,available=true,disabled=false,onViewed,onBusy,onRetry,onNext,nextLabel='Next question →',showNext=true,secondaryActions}: {
 qid:string;paperId?:string|null;options?:readonly (string|null)[];question:string;year?:number|null;topic?:string;
 context:AnswerContext;result?:AnswerResult|null;available?:boolean;disabled?:boolean;
 onViewed:(viewed:boolean)=>void;onBusy?:(busy:boolean)=>void;onRetry?:()=>void;onNext?:()=>void|Promise<void>;nextLabel?:string;showNext?:boolean;secondaryActions?:ReactNode
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
  if(sync.status==='error'||sync.status==='conflict')throw new Error(sync.error||'Saved on this device. Open Study desk to finish saving to your account.')
  setRevisionMessage(forLater?'Saved for later revision.':saved?'Removed from saved revision.':'Saved for revision.')
  if(forLater)await next()
 }
 async function action(task:()=>Promise<void>){if(actionBusy)return;setActionBusy(true);setError('');try{await task()}catch(e){if(active.current)setError((e as Error).message)}finally{if(active.current)setActionBusy(false)}}
 function retry(){setViewed(null);setError('');setDeadline(0);onViewed(false);onRetry?.()}
 const answer=result||viewed,remaining=Math.max(0,Math.ceil((deadline-now)/60000)),saved=getDesk().saved.includes(qid)
 const answerMatches=answer&&options?options.flatMap((text,index)=>text===answer.answer_text?[index]:[]):[]
 const answerLetter=answerMatches.length===1?String.fromCharCode(65+answerMatches[0]):null
 const control='min-h-11 rounded-pill border border-hairline bg-card px-3 py-2 text-[13px] font-semibold disabled:opacity-40'
 if(restoring&&!result)return <div><p role="status" className="mt-3 text-[12px] text-muted">Loading your previous answer…</p>{secondaryActions}</div>
 if(restricted)return <div><p role="status" className="mt-3 rounded-[10px] border border-hairline bg-paper p-3 text-[13px] text-secondary">{restricted}</p>{secondaryActions}</div>
 return <div className="mt-3">
  {!answer&&<div className="flex flex-wrap items-center gap-x-4">{!available?<AnswerComparison options={options} qid={qid} paperId={paperId}/>:<><button type="button" disabled={busy||disabled} onClick={()=>void show()} className={control+' text-link'}>{busy?'Opening…':'Show answer'}</button><p className="mt-1 text-[12px] text-muted">No attempt recorded · retry after 30 minutes.</p></>}{secondaryActions}</div>}
  {error&&<p role="alert" className="mt-2 text-[13px] text-mypick">{error}</p>}
  {answer&&<section aria-label="Answer and explanation" className="border-t border-hairline pt-2 text-[14px]">
   <div className="practice-answer-outcome flex flex-wrap items-baseline gap-x-2"><strong>{result?answerFeedbackLabel(result,context):'Answer'}</strong><span>{answerLetter?` · ${answerLetter}. `:' · '}<SourceQuestionText text={answer.answer_text}/></span></div>
   {!result&&<div className="flex flex-wrap items-center gap-x-2 text-[12px] text-muted"><p>No attempt recorded{remaining>0?` · retry in ${remaining} ${remaining===1?'minute':'minutes'}`:''}.</p>{remaining===0&&onRetry&&<button type="button" onClick={retry} className="min-h-11 px-1 font-semibold text-link">Retry now</button>}</div>}
   <QuestionCurrentness variant="summary" revealed question={question} year={year} topic={topic}/>
   <AnswerComparison options={options} qid={qid} paperId={paperId} revealed answer={answer} answerReviewed={answerStatus(answer.answer_source,context).status==='verified'} explanation={answer.explanation} actions={
   <nav aria-label="Continue studying" className="flex flex-wrap gap-2 has-[details[open]]:basis-full">
    <button type="button" disabled={actionBusy||getDeskSync().loading} aria-pressed={saved} aria-label={saved?'Remove from saved revision':'Save for revision'} onClick={()=>void action(()=>save())} className="min-h-11 py-2 text-[13px] font-semibold text-secondary disabled:opacity-40">{saved?'Saved':'Save'}</button>
    {showNext&&<button type="button" disabled={actionBusy} onClick={()=>void action(next)} className={control+' text-link'}>{nextLabel}</button>}
    {secondaryActions}
   </nav>
   } tools={<div className="space-y-3">
     <QuestionCurrentness variant="details" revealed question={question} year={year} topic={topic}/>
     <CurrentAffairsConnections qid={qid} paperId={paperId} onExposure={()=>{setDeadline(Date.now()+30*60*1000);setNow(Date.now())}}/>
     {showNext&&<button type="button" disabled={actionBusy||getDeskSync().loading} onClick={()=>void action(()=>save(true))} className={control}>Save and continue</button>}
     {result&&<RewardOutcome reward={result.reward}/>}
    </div>}>
    <QuestionExplanation inline explanation={answer.explanation} source={answer.answer_source} context={context}/>
   </AnswerComparison>
   {revisionMessage&&<p role="status" className="mt-2 text-[12px] text-secondary">{revisionMessage} <Link to={scopeLink('/desk?tab=bookmarks')} className="text-link underline">Saved questions</Link></p>}
  </section>}
 </div>
}
