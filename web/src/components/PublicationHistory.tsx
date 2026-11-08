import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {kindLabel,reviewRequest} from '../lib/review'

type Entry={id:string;contribution_id:string;state:string;error:string|null;created_at:string;finished_at:string|null;revision:number;title:string;kind:string;canonical_id:string|null;author:string|null;publisher:string|null;paper_title:string|null;qnum:string|null;fields:string[]}
type Page={items:Entry[];next_offset:number|null}
type Change={field:string;label:string;before:unknown;after:unknown;recorded_after:boolean;before_available:boolean}
type Detail={reason:string;changes:Change[];has_receipt:boolean}
const INPUT='min-h-11 min-w-0 rounded-[8px] border border-hairline bg-card px-3 py-2 text-[13px]'
const STATUS:Record<string,{label:string;note:string;style:string}>={
 applied:{label:'Published',note:'Applied to the question bank.',style:'border-[#BBD1B1] bg-[#E3ECDD] text-[#355E3B]'},
 exported:{label:'Publishing',note:'Queued for the publication worker. Not live yet.',style:'border-[#C3D7E8] bg-[#EDF4FA] text-[#254E70]'},
 failed:{label:'Needs attention',note:'Publication failed. Open the correction to review the reason.',style:'border-[#E6BBAA] bg-[#F5E1D8] text-[#913E2B]'},
 reverted:{label:'Reverted',note:'This publication was reversed. Its history is retained.',style:'border-hairline bg-paper text-secondary'},
}
function date(value:string|null){return value?new Date(value).toLocaleString('en-IN',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}):'Not recorded'}
function valueText(value:unknown,field:string):string{
 if(value===null||value===undefined||value==='')return 'Empty / not set'
 if(field==='answerIndex'&&typeof value==='number')return `Option ${String.fromCharCode(65+value)}`
 if(typeof value==='boolean')return value?'Yes':'No'
 if(Array.isArray(value))return value.map((v,i)=>field==='options'?`${String.fromCharCode(65+i)}. ${v??'Unavailable'}`:valueText(v,'')).join('\n')||'None'
 if(typeof value==='object')return Object.entries(value as Record<string,unknown>).map(([key,v])=>`${key.replace(/_/g,' ')}: ${valueText(v,'')}`).join('\n')
 return String(value)
}
function HistoryEntry({entry}:{entry:Entry}){
 const [open,setOpen]=useState(false),[detail,setDetail]=useState<Detail|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 useEffect(()=>{if(!open)return;let live=true;setBusy(true);setError('');reviewRequest<Detail>('/admin/bank/publication-history/'+encodeURIComponent(entry.id)).then(d=>{if(live)setDetail(d)}).catch(e=>{if(live)setError(e.message)}).finally(()=>{if(live)setBusy(false)});return()=>{live=false}},[open,entry.id,retry])
 const status=STATUS[entry.state]||{label:entry.state,note:'',style:'border-hairline bg-paper text-secondary'}
 return <article className="overflow-hidden rounded-[12px] border border-hairline bg-card shadow-sm">
  <div className="p-4 sm:p-5"><div className="flex flex-wrap items-center justify-between gap-3"><span className={'rounded-pill border px-3 py-1 text-[12px] font-semibold '+status.style}>{status.label}</span><time dateTime={entry.created_at} className="text-[12px] text-muted">Requested {date(entry.created_at)}</time></div>
   <p className="mt-3 text-[12px] font-semibold text-secondary">{kindLabel(entry.kind)}{entry.qnum?' · Q'+entry.qnum:''}</p>
   <h2 className="mt-1 break-words font-display text-[23px] leading-snug">{entry.title}</h2>
   {entry.paper_title&&<p className="mt-1 break-words text-[13px] text-secondary">{entry.paper_title}</p>}
   <p className="mt-2 text-[13px] text-secondary">{entry.fields.length?'Changed: '+entry.fields.join(', '):'Correction details available below.'}</p>
   <p className="mt-2 text-[12px] text-secondary">By {entry.author||'Account unavailable'}{entry.publisher&&entry.publisher!==entry.author?' · Sent to publication by '+entry.publisher:''}{entry.finished_at?' · '+(entry.state==='applied'?'Published ': 'Finished ')+date(entry.finished_at):''}</p>
   {entry.error&&<div role="note" className="mt-3 rounded-[8px] border border-[#E6BBAA] bg-[#FFF6F0] p-3 text-[13px]"><p className="font-semibold text-[#913E2B]">This correction needs attention</p><p className="mt-1 break-words text-secondary">{entry.error}</p></div>}
   <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px]"><button type="button" aria-expanded={open} onClick={()=>setOpen(!open)} className="min-h-11 font-semibold text-link">{open?'Hide changes ↑':'See what changed ↓'}</button><Link className="inline-flex min-h-11 items-center text-link underline" to={'/contributions/'+entry.contribution_id}>Open correction →</Link>{entry.canonical_id&&<Link className="inline-flex min-h-11 items-center text-link underline" to={'/admin/bank?'+new URLSearchParams({tab:'questions',question:entry.canonical_id,issue:'all'})}>Current question →</Link>}</div>
  </div>
  {open&&<section aria-label="Correction details" className="border-t border-hairline bg-[#FBF8F1] p-4 sm:p-5">
   {busy&&<p role="status" className="text-[13px] text-muted">Loading saved changes…</p>}
   {error&&<p role="alert" className="text-[13px] text-mypick">{error} <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 underline">Retry</button></p>}
   {!busy&&!error&&detail&&<><p className="text-[12px] text-secondary">{status.note} These are the values saved for this publication; later corrections may have changed the current question.</p>{detail.reason&&<div className="my-4 text-[13px]"><strong>Correction note</strong><p className="mt-1 whitespace-pre-wrap break-words text-secondary">{detail.reason}</p></div>}
    <div className="space-y-4">{detail.changes.map(change=><div key={change.field}><h3 className="mb-2 text-[13px] font-semibold">{change.label}</h3><div className="grid gap-2 sm:grid-cols-2"><div className="rounded-[8px] border border-hairline bg-card p-3"><p className="mb-2 font-mono text-[10px] uppercase tracking-wide text-muted">Before</p><p className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-[13px] leading-relaxed">{change.before_available?valueText(change.before,change.field):'Not recorded in this historical snapshot'}</p></div><div className="rounded-[8px] border border-[#C3D7E8] bg-[#EDF4FA] p-3"><p className="mb-2 font-mono text-[10px] uppercase tracking-wide text-[#254E70]">{change.recorded_after?'Recorded after publication':'Saved correction (requested)'}</p><p className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-[13px] leading-relaxed">{valueText(change.after,change.field)}</p></div></div></div>)}</div>
    {detail.changes.length===0&&<p className="mt-3 text-[13px] text-secondary">No field comparison is recorded for this publication. Open the correction for its original evidence.</p>}
    <p className="mt-4 break-all font-mono text-[10px] text-muted">Publication {entry.id} · revision {entry.revision}</p>
   </>}
  </section>}
 </article>
}
export default function PublicationHistory(){
 const [mine,setMine]=useState(true),[state,setState]=useState(''),[kind,setKind]=useState(''),[query,setQuery]=useState(''),[search,setSearch]=useState(''),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0)
 const [page,setPage]=useState<Page|null>(null),[busy,setBusy]=useState(true),[error,setError]=useState('')
 useEffect(()=>{const timer=setTimeout(()=>{setSearch(query.trim());setOffset(0)},300);return()=>clearTimeout(timer)},[query])
 useEffect(()=>{let live=true;setBusy(true);setError('');setPage(null);reviewRequest<Page>('/admin/bank/publication-history?'+new URLSearchParams({mine:String(mine),state,kind,q:search,offset:String(offset),limit:'20'})).then(d=>{if(live)setPage(d)}).catch(e=>{if(live)setError(e.message)}).finally(()=>{if(live)setBusy(false)});return()=>{live=false}},[mine,state,kind,search,offset,refresh])
 return <section className="mt-5 max-w-6xl" aria-label="Publication history">
  <div className="rounded-[12px] border border-hairline bg-card p-4"><div className="flex flex-wrap items-end gap-3"><label className="min-w-[180px] flex-1 text-[12px] font-semibold">Search corrections<input type="search" maxLength={200} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Question, paper or publication ID" className={INPUT+' mt-1 w-full'}/></label><label className="text-[12px] font-semibold">Whose corrections<select value={String(mine)} onChange={e=>{setMine(e.target.value==='true');setOffset(0)}} className={INPUT+' mt-1 block w-full'}><option value="true">My corrections</option><option value="false">All permitted corrections</option></select></label><label className="text-[12px] font-semibold">Status<select value={state} onChange={e=>{setState(e.target.value);setOffset(0)}} className={INPUT+' mt-1 block w-full'}><option value="">All statuses</option>{Object.entries(STATUS).map(([key,v])=><option key={key} value={key}>{v.label}</option>)}</select></label><label className="text-[12px] font-semibold">Correction type<select value={kind} onChange={e=>{setKind(e.target.value);setOffset(0)}} className={INPUT+' mt-1 block w-full'}><option value="">All types</option>{['answer','explanation','taxonomy','transcription','source_reference','defect','new_question'].map(value=><option key={value} value={value}>{kindLabel(value)}</option>)}</select></label><button disabled={busy} type="button" onClick={()=>setRefresh(n=>n+1)} className={INPUT+' font-semibold disabled:opacity-40'}>Refresh</button></div>
   <p className="mt-3 text-[12px] leading-relaxed text-secondary">Newest publication requests first. “My corrections” includes changes you authored or sent for publication. Corrections still awaiting approval appear in the <Link to="/admin/bank?tab=review" className="text-link underline">review queue</Link>.</p>
  </div>
  {busy&&<p role="status" className="mt-5 text-[13px] text-muted">Loading correction history…</p>}
  {error&&<p role="alert" className="mt-5 rounded-[8px] border border-mypick bg-card p-4 text-[13px] text-mypick">{error} <button type="button" onClick={()=>setRefresh(n=>n+1)} className="min-h-11 underline">Retry history</button></p>}
  {!busy&&!error&&page&&<><p role="status" className="my-4 text-[12px] text-muted">{page.items.length?`${offset+1}–${offset+page.items.length} · newest first`:'No matching publications'}</p><div className="space-y-3">{page.items.map(entry=><HistoryEntry key={entry.id} entry={entry}/>)}</div>{page.items.length===0&&<div className="rounded-[12px] border border-hairline bg-card p-6"><h2 className="font-display text-[23px]">No corrections match these filters</h2><p className="mt-2 text-[13px] text-secondary">Try all statuses or all permitted corrections. Publication requests will appear here once they have been exported for publishing.</p></div>}<nav aria-label="Publication history pages" className="mt-5 flex items-center justify-between"><button type="button" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-20))} className={INPUT+' disabled:opacity-40'}>← Newer</button><button type="button" disabled={page.next_offset===null} onClick={()=>{if(page.next_offset!==null)setOffset(page.next_offset)}} className={INPUT+' disabled:opacity-40'}>Older corrections →</button></nav></>}
 </section>
}
