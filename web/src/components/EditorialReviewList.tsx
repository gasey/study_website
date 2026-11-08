import {useEffect,useRef,useState} from 'react'
import {reviewRequest,type BankSnapshot} from '../lib/review'
import {SourceQuestionContext,SourceQuestionText} from './SourceQuestionText'

export type ReviewListItem={id:string;questionId:string;number:string|null;text:string;status:string}
const BUTTON='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-3 py-2 text-[13px] font-semibold disabled:opacity-40'

/** Read-only source inspection. Reveals and local picks never submit reviews or attempts. */
export default function EditorialReviewList({items,busy,onReview}:{items:ReviewListItem[];busy:boolean;onReview:(item:ReviewListItem)=>void}){
 const [snapshots,setSnapshots]=useState<Record<string,BankSnapshot>>({}),[errors,setErrors]=useState<Record<string,string>>({})
 const [expanded,setExpanded]=useState<Record<string,boolean>>({}),[revealed,setRevealed]=useState<Record<string,boolean>>({}),[picks,setPicks]=useState<Record<string,number>>({}),[showAll,setShowAll]=useState(false)
 const alive=useRef(true),requests=useRef(new Map<string,Promise<void>>()),lanes=useRef<Promise<void>[]>([Promise.resolve(),Promise.resolve(),Promise.resolve()]),lane=useRef(0)
 useEffect(()=>{alive.current=true;return()=>{alive.current=false}},[])
 function load(item:ReviewListItem){
  const existing=requests.current.get(item.id);if(existing)return existing
  const index=lane.current++%lanes.current.length
  const task=lanes.current[index].then(async()=>{
   if(!alive.current)return
   try{
    const snapshot=await reviewRequest<BankSnapshot>('/review/questions/'+encodeURIComponent(item.questionId)+'?appearance_id='+encodeURIComponent(item.id))
    if(snapshot.record.id!==item.id)throw Error('Source changed. Reload this list before continuing.')
    if(alive.current){setSnapshots(old=>({...old,[item.id]:snapshot}));setErrors(old=>({...old,[item.id]:''}))}
   }catch(error){requests.current.delete(item.id);if(alive.current)setErrors(old=>({...old,[item.id]:error instanceof Error?error.message:'Source could not load.'}))}
  })
  lanes.current[index]=task;requests.current.set(item.id,task);return task
 }
 function revealPage(){setShowAll(true);for(const item of items)void load(item)}
 function hideAnswers(){setShowAll(false);setRevealed({});setPicks({})}
 return <section aria-label="Question review list" className="min-w-0">
  <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-hairline bg-paper p-4"><div><h3 className="text-[15px] font-semibold">Quick revision & source checking</h3><p className="mt-1 text-[12px] text-secondary">Open options and tap a choice to compare with the recorded answer. No attempt or source check is saved.</p></div><button type="button" disabled={busy||!items.length} className={BUTTON} aria-pressed={showAll} onClick={showAll?hideAnswers:revealPage}>{showAll?'Hide all answers':'Show answers on this page'}</button></div>
  {!items.length&&<p className="rounded-xl border border-hairline bg-card p-4 text-sm">No questions match this view.</p>}
  <ol className="divide-y divide-hairline overflow-hidden rounded-[14px] border border-hairline bg-card">{items.map(item=>{
   const snapshot=snapshots[item.id],record=snapshot?.record,open=!!expanded[item.id],show=showAll||!!revealed[item.id],pick=picks[item.id]
   const answer=record?.answerIndex,hasAnswer=answer!=null&&!!record?.options[answer]
   return <li key={item.id} className="min-w-0 p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-2"><p className="font-mono text-[11px] text-secondary">Q{item.number||'—'} · {item.status}</p><button disabled={busy} className={BUTTON+' text-link'} onClick={()=>onReview(item)}>Review / edit source →</button></div>
    <div className="mt-2 break-words font-display text-[21px] leading-snug"><SourceQuestionText text={record?.questionMarkup||record?.question||item.text}/></div>
    {snapshot&&<p className="mt-2 break-words text-[12px] text-secondary">{snapshot.tag_label||'Tags unavailable'} · PDF page {record?.page||'unknown'} {snapshot.paper.source_pdf_url&&<a className="text-link underline" href={snapshot.paper.source_pdf_url+'#page='+(record?.page||1)} target="_blank" rel="noreferrer">Original PDF ↗</a>}</p>}
    <div className="mt-3 flex flex-wrap gap-2"><button disabled={busy} className={BUTTON} aria-expanded={open} onClick={()=>{setExpanded(old=>({...old,[item.id]:!open}));if(!open)void load(item)}}>{open?'Hide options & context':'Options / self-check'}</button>{!show&&<button disabled={busy} className={BUTTON} onClick={()=>{setRevealed(old=>({...old,[item.id]:true}));void load(item)}}>Show answer</button>}{show&&!showAll&&<button disabled={busy} className={BUTTON} onClick={()=>{setRevealed(old=>({...old,[item.id]:false}));setPicks(old=>{const next={...old};delete next[item.id];return next})}}>Hide answer / try again</button>}</div>
    {(open||show)&&!record&&!errors[item.id]&&<p role="status" className="mt-3 text-sm text-secondary">Loading this source…</p>}
    {errors[item.id]&&<p role="alert" className="mt-3 text-sm text-mypick">{errors[item.id]} <button disabled={busy} className={BUTTON} onClick={()=>void load(item)}>Retry source</button></p>}
    {open&&record&&<div className="mt-3"><SourceQuestionContext direction={record.direction||null} passage={record.passage||null}/>{record.hasDiagram&&<p className="mt-2 text-sm text-secondary">Compare the printed figure using Original PDF.</p>}<div className="mt-3 grid gap-2 sm:grid-cols-2">{record.options.map((option,i)=>{
     const keyed=show&&hasAnswer&&answer===i,chosen=pick===i
     return <button key={i} type="button" disabled={busy||show||!hasAnswer||option==null} aria-pressed={chosen} onClick={()=>{setPicks(old=>({...old,[item.id]:i}));setRevealed(old=>({...old,[item.id]:true}))}} className={'flex min-h-11 min-w-0 gap-3 rounded-[6px] border p-3 text-left text-[14px] '+(keyed?'border-correct bg-correct-soft':chosen?'border-wrong bg-wrong-soft':'border-hairline bg-[#FBF8F1]')}><span className="font-mono">{String.fromCharCode(65+i)}.</span><span className="min-w-0 break-words"><SourceQuestionText text={record.optionsMarkup?.[i]||option||'Option unavailable'}/>{keyed&&<span className="mt-1 block text-[12px] font-semibold">Recorded answer</span>}{chosen&&<span className="mt-1 block text-[12px] font-semibold">Your pick</span>}</span></button>
    })}</div>{!record.options.length&&<p className="text-sm text-secondary">Written question</p>}</div>}
    {show&&record&&<div className="mt-3 rounded-lg border border-hairline bg-paper p-3" aria-label={'Recorded answer for question '+(item.number||'—')}><p className="break-words text-sm"><strong>Recorded answer: </strong>{hasAnswer?String.fromCharCode(65+answer!)+'. '+record.options[answer!]:record.type==='mcq'?'No answer recorded — compare the source or flag an issue.':'Written response — see marking guidance if available.'}</p>{pick!==undefined&&hasAnswer&&<p className="mt-2 text-[12px]">{pick===answer?'Your pick matches the recorded answer.':'Your pick differs from the recorded answer.'}</p>}<p className="mt-2 break-words text-[12px] text-secondary">Source: {record.answerSource||'No provenance recorded'}{record.answerKeyRef?' · '+record.answerKeyRef:''}</p><details className="mt-2"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Explanation / marking guidance</summary><p className="whitespace-pre-wrap break-words text-sm">{record.explanation||'No explanation recorded.'}</p></details></div>}
   </li>
  })}</ol>
 </section>
}
