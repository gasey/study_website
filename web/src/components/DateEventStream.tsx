import {useCallback,useEffect,useRef,useState} from 'react'
import {bankDates,type DateIndex} from '../lib/bankDates'
import {DateList} from './ImportantDateViews'

/** Append bounded API pages while keeping the existing rows and scroll position. */
export default function DateEventStream({initial,request,chronology,onSources,onStart}:{initial:DateIndex;request:string;chronology:boolean;onSources:(id:string)=>void;onStart:()=>void}){
 const [result,setResult]=useState({items:initial.items,next:initial.offset+initial.limit,total:initial.total,done:initial.items.length<initial.limit||initial.offset+initial.limit>=initial.total})
 const [loading,setLoading]=useState(false),[error,setError]=useState('')
 const active=useRef(true),pending=useRef(false),sentinel=useRef<HTMLDivElement>(null)
 useEffect(()=>{active.current=true;return()=>{active.current=false}},[])
 const more=useCallback(async()=>{
  if(!active.current||pending.current||result.done)return
  pending.current=true;setLoading(true);setError('')
  const query=new URLSearchParams(request);query.set('offset',String(result.next))
  try{
   const page=await bankDates(query.toString())
   if(!('items'in page))throw new Error('Could not load more events. Please try again.')
   if(active.current)setResult(previous=>{
    const seen=new Set(previous.items.map(item=>item.id))
    const added=page.items.filter(item=>{if(seen.has(item.id))return false;seen.add(item.id);return true})
    return {items:[...previous.items,...added],next:page.offset+page.limit,total:page.total,done:page.items.length<page.limit||page.offset+page.limit>=page.total}
   })
  }catch(cause){if(active.current)setError(cause instanceof Error?cause.message:'Could not load more events. Please try again.')}
  finally{pending.current=false;if(active.current)setLoading(false)}
 },[request,result.next,result.done])
 useEffect(()=>{
  if(result.done||loading||error||!sentinel.current||typeof IntersectionObserver==='undefined')return
  const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting))void more()},{rootMargin:'320px 0px'})
  observer.observe(sentinel.current)
  return()=>observer.disconnect()
 },[more,result.done,loading,error])
 return <>
  <DateList items={result.items} chronology={chronology} onSources={onSources}/>
  <div ref={sentinel} className="flex min-h-32 flex-col items-center justify-center gap-2 border-b border-hairline py-5 text-center [overflow-anchor:none]" aria-label="More events">
   <p className="text-xs text-muted" aria-live="polite">{result.items.length.toLocaleString('en-IN')} loaded · {result.total.toLocaleString('en-IN')} matching events{initial.offset>0?` · starting at event ${(initial.offset+1).toLocaleString('en-IN')}`:''}</p>
   {error&&<p role="alert" className="max-w-xl text-sm text-secondary">{error}</p>}
   {loading?<p role="status" className="min-h-11 py-3 text-sm text-secondary">Loading more events…</p>:result.done?<p className="min-h-11 py-3 text-sm text-muted">End of results</p>:<button type="button" onClick={()=>void more()} className="min-h-11 rounded-pill border border-hairline bg-card px-5 text-sm font-semibold text-link hover:border-ink">{error?'Retry loading more':'Load more events'}</button>}
   {initial.offset>0&&<button type="button" onClick={onStart} className="min-h-11 text-sm text-link underline underline-offset-4">Start from first event</button>}
  </div>
 </>
}
