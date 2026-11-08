import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'

type Item={id:string;canonical_id:string;title:string;decision:string;finding:string;repair:string;suggested_answer:string|null;paper_title:string;year:number;source_url:string|null;stale:boolean;source_version?:string;question_version_hash?:string;expected:{question:string;options:string[];page:number;qnum:string|number};references:{title:string;url:string}[]}
type Report={reviewed_on:string;can_save:boolean;items:Item[]}
const button='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-4 text-[13px] font-semibold disabled:opacity-40'

export default function McqSolverReview(){
 const [report,setReport]=useState<Report|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(''),[saved,setSaved]=useState<Record<string,string>>({})
 async function load(){setError('');try{setReport(await reviewRequest<Report>('/admin/mcq-solver/review'))}catch(e){setError((e as Error).message)}}
 useEffect(()=>{void load()},[])
 async function stage(item:Item){
  if(busy||item.stale||!report?.can_save)return
  setBusy(item.id);setError('')
  try{const receipt=await reviewRequest<{contribution_id:string}>('/admin/mcq-solver/drafts/'+item.id,{source_version:item.source_version,question_version_hash:item.question_version_hash});setSaved(s=>({...s,[item.id]:receipt.contribution_id}))}catch(e){setError((e as Error).message)}finally{setBusy('')}
 }
 return <main className="mx-auto max-w-5xl px-4 pb-24 pt-8">
  <Link to="/admin/bank" className="inline-flex min-h-11 items-center text-[13px] text-link underline">← Administration</Link>
  <h1 className="mt-2 font-display text-[36px]">Solver source review</h1>
  <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-secondary">Five pilot records compared with the original papers. Four need question-format repairs; one circuit has a source-supported answer. These are AI-assisted findings awaiting review. Saving creates a contribution draft.</p>
  {error&&<p role="alert" className="mt-4 rounded-lg border border-hairline bg-card p-4 text-[14px]">{error} <button onClick={()=>void load()} className="min-h-11 px-3 text-link underline">Reload</button></p>}
  {!report&&!error&&<p role="status" className="mt-6">Loading private review…</p>}
  {report&&<>
   <div className="mt-5 flex flex-wrap items-center gap-3 border-y border-hairline py-3 text-[13px]"><span>{report.items.length} source checks · {report.reviewed_on}</span><span>Published answers are separate</span></div>
   {!report.can_save&&<p className="mt-4 rounded-lg bg-paper p-4 text-[14px]">To save a draft, verify your authenticator and use a recent sign-in. <Link to="/account/security" className="inline-flex min-h-11 items-center text-link underline">Account security →</Link></p>}
   <div className="mt-5 space-y-4">{report.items.map(item=><article key={item.id} className="rounded-[14px] border border-hairline bg-card p-5 shadow-sm">
    <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-mono text-[11px] uppercase tracking-wide text-secondary">{item.decision==='hold_format'?'Format repair needed':'Derived answer draft'}</span>{item.source_url&&<a href={item.source_url+'#page='+item.expected.page} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center text-[13px] text-link underline">Original PDF · page {item.expected.page} ↗</a>}</div>
    <h2 className="mt-1 font-display text-[25px]">{item.title}</h2><p className="mt-1 text-[12px] text-secondary">{item.paper_title} · {item.year} · Q{item.expected.qnum}</p>
    <p className="mt-4 whitespace-pre-line font-display text-[21px] leading-snug">{item.expected.question}</p>
    <p className="mt-4 text-[14px] leading-relaxed">{item.finding}</p>
    {item.suggested_answer&&<p className="mt-3 rounded-lg bg-paper p-3 text-[14px]"><strong>Study answer: </strong>{item.suggested_answer}</p>}
    <p className="mt-3 text-[14px] leading-relaxed"><strong>Next correction: </strong>{item.repair}</p>
    {item.references.length>0&&<ul className="mt-3 text-[13px]">{item.references.map(ref=><li key={ref.url}><a href={ref.url} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center text-link underline">{ref.title} ↗</a></li>)}</ul>}
    {item.stale&&<p role="status" className="mt-4 text-[14px] font-semibold">The live source no longer matches this check. Reinspection is required.</p>}
    <div className="mt-4 flex flex-wrap gap-3">{saved[item.id]?<Link className={button+' text-link'} to={'/contributions/'+saved[item.id]}>Open saved draft →</Link>:<button className={button+' bg-ink text-paper'} disabled={!!busy||item.stale||!report.can_save} onClick={()=>void stage(item)}>{busy===item.id?'Saving draft…':item.decision==='hold_format'?'Save defect draft':'Save answer draft'}</button>}<Link className={button+' text-link'} to={'/admin/bank?tab=questions&q='+encodeURIComponent(item.canonical_id)}>Inspect bank record →</Link></div>
   </article>)}</div>
  </>}
 </main>
}
