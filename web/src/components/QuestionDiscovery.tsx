import {useEffect,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {getDiscovery,type Discovery,type DiscoveryExam,type DiscoveryQuestion} from '../lib/discovery'
import {accountGeneration} from '../lib/accountContext'

export default function QuestionDiscovery({exam,limit=3,compact=false}:{exam?:DiscoveryExam;limit?:number;compact?:boolean}) {
 const [view,setView]=useState<'recommended'|'popular'|'hot'>('recommended')
 const [params,setParams]=useSearchParams()
 const selected=exam||(params.get('discover_exam')==='udc'?'udc':params.get('discover_exam')==='combined-prelims'?'combined-prelims':null)
 const [data,setData]=useState<Discovery|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{
  let live=true;const epoch=accountGeneration();setData(null);setError('')
  if(selected)getDiscovery(selected,limit).then(d=>{if(live&&epoch===accountGeneration())setData(d)}).catch(()=>{if(live)setError('Discovery could not load.')})
  return()=>{live=false}
 },[selected,limit,retry])
 useEffect(()=>{const changed=()=>{setData(null);setRetry(n=>n+1)};window.addEventListener('ism-auth-change',changed);return()=>window.removeEventListener('ism-auth-change',changed)},[])
 return <section className="mt-7 min-w-0" aria-label="Practice discovery">
  {!exam&&<div className="flex flex-wrap items-center gap-3"><h2 className="font-display text-[28px]">Find your next practice</h2><label className="text-[13px]">Exam<select className="ml-2 min-h-11 rounded-lg border border-hairline bg-card px-3" value={selected||''} onChange={e=>setParams(p=>{const n=new URLSearchParams(p);n.set('discover_exam',e.target.value);return n},{replace:true})}><option value="">Choose an exam</option><option value="udc">UDC</option><option value="combined-prelims">Prelims</option></select></label></div>}
  {!selected&&<p className="mt-2 text-[13px] text-secondary">Choose UDC or Prelims to explore relevant questions and timely topics.</p>}
  {selected&&!data&&!error&&<p role="status" className="mt-3 text-[13px] text-secondary">Loading practice discovery…</p>}
  {error&&<p role="status" className="mt-3 text-[13px] text-secondary">{error} <button className="min-h-11 px-3 text-link underline" onClick={()=>setRetry(n=>n+1)}>Retry</button></p>}
  {data?.withheld?<p className="mt-3 text-[13px] text-secondary">{data.message}</p>:data&&<>
   {compact&&<div className="mt-4 flex flex-wrap gap-2" aria-label="Discovery views">{(['recommended','popular','hot'] as const).map(v=><button key={v} aria-pressed={view===v} onClick={()=>setView(v)} className={'min-h-11 rounded-pill px-4 text-[12px] font-semibold '+(view===v?'bg-ink text-paper':'border border-hairline bg-card')}>{v==='recommended'?'Recommended':v==='popular'?'Popular this week':'Timely topics'}</button>)}</div>}
   {(!compact||view==='popular')&&<QuestionSection title="Popular questions" note="Recent activity from registered learners · last 7 days" items={data.popular} empty="There is not enough recent learner activity to establish popularity yet."/>}
   {(compact?view==='recommended':!!data.recommended.length)&&<QuestionSection title="Recommended practice" note="Editorial selections from an inspected source list" items={data.recommended} empty="Reviewed recommendations will appear here as they become available."/>}
   {(!compact||view==='hot')&&<div className="mt-5"><h3 className="font-display text-[25px]">Hot topics</h3><p className="mt-1 text-[12px] text-secondary">Dated, reviewed picks with a reason to study them now.</p>{data.hot.length?<div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{data.hot.map(p=><article key={p.id} className="min-w-0 rounded-xl border border-hairline bg-card p-4"><Link to={p.url} className="inline-flex min-h-11 items-center font-display text-[22px] text-link">{p.title} →</Link><p className="mt-2 break-words text-[13px] leading-relaxed">{p.why_now}</p><p className="mt-2 text-[11px] text-secondary">Review until {new Date(p.expires_at).toLocaleDateString()}</p><ul className="mt-2">{p.sources.map(s=><li key={s.url}><a href={s.url} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center break-words text-[12px] text-link underline">{s.title} · {s.published_on}</a></li>)}</ul></article>)}</div>:<p className="mt-2 text-[13px] text-secondary">No timely picks are published for this exam yet.</p>}</div>}
   <p className="mt-3 text-[11px] text-secondary">These sections guide practice; they do not predict the next exam.{data.generated_at&&` Activity checked ${new Date(data.generated_at).toLocaleString()}.`}</p>
  </>}
 </section>
}
function QuestionSection({title,note,items,empty}:{title:string;note:string;items:DiscoveryQuestion[];empty?:string}) {
 return <div className="mt-5"><h3 className="font-display text-[25px]">{title}</h3><p className="mt-1 text-[12px] text-secondary">{note}</p>{items.length?<div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{items.map(q=><Link key={q.id} to={q.url} className="block min-w-0 rounded-xl border border-hairline bg-card p-4 hover:border-ink"><span className="text-[11px] text-secondary">{q.exam_name} · {q.year||'Year unknown'} · Q{q.qnum||'—'}</span><p className="mt-2 line-clamp-3 break-words text-[14px] leading-relaxed">{q.question}</p><span className="mt-3 inline-flex min-h-11 items-center text-[13px] font-semibold text-link">Open question →</span></Link>)}</div>:empty&&<p className="mt-2 text-[13px] text-secondary">{empty}</p>}</div>
}
