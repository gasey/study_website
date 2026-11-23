import {lazy,Suspense,useCallback,useEffect,useMemo,useRef,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {bankDates,formatBankDate,dateEvidenceLabel,dateYearGroup,type DateIndex,type DateEvent} from '../lib/bankDates'
import {DateList} from '../components/ImportantDateViews'
import ChronicleNav from '../components/ChronicleNav'
import Pagination from '../components/Pagination'
import {pageNumber} from '../lib/pagination'
import {useDebouncedValue} from '../lib/useDebouncedValue'
const SIZE=24
/** The prototype's timeline uses real bank dates; no invented eras or classifications. */
const DateViews=lazy(()=>import('./ImportantDates'))
export default function Chronicle(){
 const [params]=useSearchParams()
 const dateView=['list','calendar','chronology','collections'].includes(params.get('view')||'')||params.has('event')||params.has('entry')
 return dateView?<Suspense fallback={<p role="status" className="finna-page">Loading dates…</p>}><DateViews/></Suspense>:<Timeline/>
}
function Timeline(){
 const [params,setParams]=useSearchParams(),[data,setData]=useState<DateIndex|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 const [selected,setSelected]=useState<DateEvent|null>(null)
 const nodeRefs=useRef<Record<string,HTMLButtonElement|null>>({})
 const railRef=useRef<HTMLDivElement|null>(null)
 const mode=params.get('display')==='reading'?'reading':'canvas',query=params.get('q')||'',page=pageNumber(params.get('page'))
 const category=['all','history','observance','event'].includes(params.get('category')||'')?params.get('category')!:'history'
 const search=useDebouncedValue(query,250)
 function change(name:string,value:string){setParams(old=>{const next=new URLSearchParams(old);value?next.set(name,value):next.delete(name);if(name!=='page')next.delete('page');return next},{replace:name!=='page'})}
 useEffect(()=>{let live=true;setData(null);setError('');setSelected(null);bankDates(new URLSearchParams({order:'year',origin:'all',evidence:'dated',limit:String(SIZE),offset:String((page-1)*SIZE),...(search?{q:search}:{}),...(category!=='all'?{category}:{})}).toString()).then(result=>{if(live&&'items'in result){setData(result);setSelected(result.items[0]||null)}}).catch(e=>{if(live)setError(e instanceof Error?e.message:'The timeline could not load.')});return()=>{live=false}},[search,category,page,retry])
 useEffect(()=>{const reset=()=>{setData(null);setSelected(null);setRetry(n=>n+1)};window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-content-change',reset);return()=>{window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-content-change',reset)}},[])
 useEffect(()=>{if(data&&page>Math.max(1,Math.ceil(data.total/SIZE)))change('page','')},[data,page])

 const items=data?.items||[]
 const activeIndex=useMemo(()=>selected?items.findIndex(e=>e.id===selected.id):-1,[items,selected])
 const activeGroup=selected?dateYearGroup(selected):''

 const milestones=useMemo(()=>{
  const groups:{label:string;firstId:string;count:number}[]=[]
  const byLabel=new Map<string,{label:string;firstId:string;count:number}>()
  for(const entry of items){
   const label=dateYearGroup(entry)
   const shortLabel=label==='Dates without a recorded year'?'No year':label==='Dates to check'?'Check date':label
   const existing=byLabel.get(label)
   if(existing){existing.count+=1}
   else{const item={label:shortLabel,firstId:entry.id,count:1};byLabel.set(label,item);groups.push(item)}
  }
  return groups
 },[items])

 const focusEvent=useCallback((entry:DateEvent,scroll=true)=>{
  setSelected(entry)
  if(scroll&&mode==='canvas'){
   const el=nodeRefs.current[entry.id]
   if(el&&typeof el.scrollIntoView==='function')el.scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'})
  }
 },[mode])

 const step=useCallback((delta:number)=>{
  if(!items.length)return
  const current=activeIndex>=0?activeIndex:0
  const nextIndex=Math.max(0,Math.min(items.length-1,current+delta))
  focusEvent(items[nextIndex],true)
 },[items,activeIndex,focusEvent])

 useEffect(()=>{
  if(!items.length)return
  const onKey=(e:KeyboardEvent)=>{
   const tag=(e.target as HTMLElement|null)?.tagName
   if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||(e.target as HTMLElement|null)?.isContentEditable)return
   if(e.metaKey||e.ctrlKey||e.altKey)return
   if(e.key==='ArrowLeft'){e.preventDefault();step(-1)}
   else if(e.key==='ArrowRight'){e.preventDefault();step(1)}
  }
  window.addEventListener('keydown',onKey)
  return()=>window.removeEventListener('keydown',onKey)
 },[items.length,step])

 const source=(entry:DateEvent)=>'/chronicle?'+new URLSearchParams({view:'chronology',event:entry.id})
 const mark=(entry:DateEvent)=>entry.dates.length?entry.dates.map(formatBankDate).join(' · '):'Date to check'
 const progressPct=items.length&&activeIndex>=0?Math.round(((activeIndex+1)/items.length)*100):0

 return <div className="finna-page finna-chronicle" data-screen="chronicle">
  <header className="finna-page-heading">
   <div>
    <Link to="/library" className="text-sm font-bold text-[#C2410C] dark:text-[#FB923C]">← Library</Link>
    <h1>Chronicle</h1>
   </div>
   <div className="finna-segments" role="group" aria-label="Timeline display">
    {['canvas','reading'].map(value=><button type="button" key={value} aria-pressed={mode===value} onClick={()=>change('display',value)}>{value==='canvas'?'Canvas':'Reading'}</button>)}
   </div>
  </header>

  <ChronicleNav active="timeline"/>

  <div className="mb-5 flex flex-wrap items-center gap-3">
   <nav className="finna-segments" aria-label="Timeline events">
    {[['all','All events'],['history','History'],['observance','Observances'],['event','Other events']].map(([value,label])=><button type="button" key={value} aria-pressed={category===value} onClick={()=>change('category',value)}>{label}</button>)}
   </nav>
   <label className="ml-auto min-w-0 flex-1 basis-64 sm:max-w-sm">
    <span className="sr-only">Search the timeline</span>
    <input type="search" aria-label="Search the timeline" value={query} onChange={e=>change('q',e.target.value)} placeholder="Search a date, event or topic" className="min-h-11 w-full rounded-xl border border-hairline bg-card px-4 text-sm"/>
   </label>
  </div>

  {error&&<section className="finna-card" role="alert"><h2>The timeline couldn’t load</h2><p className="mt-2 text-sm text-secondary">{error}</p><button className="finna-btn mt-4" onClick={()=>setRetry(n=>n+1)}>Try again</button></section>}
  {!data&&!error&&<section className="finna-card" role="status">Finding dates and events in the bank…</section>}

  {data&&<div className="finna-chronicle-layout">
   <section className="finna-card finna-chronicle-stage">
    <div className="finna-section-top">
     <div>
      <h2 className="text-xl">{category==='history'?'History':category==='observance'?'Observances':'Dates through time'}</h2>
      <p className="mt-1 text-xs text-secondary">Dates as recorded in the question bank. Timeline spacing shows order, not elapsed time.</p>
     </div>
     <span className="finna-chrono-count">{data.total.toLocaleString('en-IN')} events</span>
    </div>

    {items.length>0&&<div className="finna-chrono-dock" role="region" aria-label="Chronology scrubber navigation">
     <div className="finna-chrono-dock-controls">
      <button type="button" className="finna-chrono-step" aria-label="Previous event" disabled={activeIndex<=0} onClick={()=>step(-1)}>‹</button>
      <span className="finna-chrono-pos" aria-live="polite">{activeIndex>=0?activeIndex+1:1} / {items.length}</span>
      <button type="button" className="finna-chrono-step" aria-label="Next event" disabled={activeIndex>=items.length-1} onClick={()=>step(1)}>›</button>
     </div>
     <div className="finna-chrono-scrubber" aria-label="Jump to year or date group">
      {milestones.map(m=>{
       const matchEntry=items.find(e=>e.id===m.firstId)
       const isCurrent=!!matchEntry&&dateYearGroup(matchEntry)===activeGroup
       return <button key={m.firstId} type="button" aria-pressed={isCurrent} className={'finna-chrono-pill'+(isCurrent?' is-active':'')} onClick={()=>matchEntry&&focusEvent(matchEntry,true)}>
        <span>{m.label}</span>
        {m.count>1&&<em className="finna-chrono-pill-badge">{m.count}</em>}
       </button>
      })}
     </div>
     <span className="finna-chrono-keys" aria-hidden="true"><kbd>←</kbd><kbd>→</kbd></span>
     <div className="finna-chrono-progress" aria-hidden="true"><span style={{width:`${progressPct}%`}}/></div>
    </div>}

    {!items.length?<p className="py-6 text-sm text-secondary">No events match this search. Try a broader topic or another event category.</p>:mode==='reading'?<DateList items={items} chronology onSources={id=>{const found=items.find(e=>e.id===id);if(found)setSelected(found)}}/>:<div ref={railRef} className="finna-chronicle-scroll" role="region" aria-label="Chronological timeline" tabIndex={0}>
     <div className="finna-chronicle-tracks" style={{minWidth:Math.max(900,items.length*196)+'px',gridTemplateColumns:`repeat(${items.length},196px)`}}>
      <span className="finna-track-label">History</span>
      {items.map((entry,i)=>{
       const isTop=entry.category==='history'
       return <button key={entry.id} ref={node=>{nodeRefs.current[entry.id]=node}} type="button" data-track={isTop?'top':'bottom'} aria-pressed={selected?.id===entry.id} className="finna-event-node" title={entry.title} style={{gridColumn:i+1,gridRow:isTop?2:4}} onClick={()=>focusEvent(entry,true)}>
        <strong>{mark(entry)}</strong>
        <span>{entry.title}</span>
        <small>{entry.question_count} {entry.question_count===1?'question':'questions'}</small>
       </button>
      })}
      <div className="finna-timeline-axis" style={{gridColumn:'1 / -1',gridRow:3}}/>
      <span className="finna-track-label finna-track-label-bottom">Events & observances</span>
     </div>
    </div>}

    <Pagination page={page} pages={Math.max(1,Math.ceil(data.total/SIZE))} onPageChange={n=>change('page',String(n))} label="Timeline pages"/>
   </section>

   <aside className="finna-chronicle-aside space-y-4">
    {selected?<section className="finna-card finna-event-detail">
     <div className="finna-section-top">
      <span className="finna-chrono-cat-badge">{selected.category}</span>
      <div className="flex items-center gap-1">
       <button type="button" className="finna-chrono-mini-step" aria-label="Previous event" disabled={activeIndex<=0} onClick={()=>step(-1)}>‹</button>
       <button type="button" className="finna-chrono-mini-step" aria-label="Next event" disabled={activeIndex>=items.length-1} onClick={()=>step(1)}>›</button>
       <button type="button" className="ml-1 min-h-9 text-xs font-bold text-link" onClick={()=>setSelected(null)}>Close</button>
      </div>
     </div>
     <p className="finna-event-date">{mark(selected)}</p>
     <h2 className="mt-3 text-xl">{selected.title}</h2>
     <p className="mt-3 text-sm leading-relaxed text-secondary">{selected.preview}</p>
     <div className="mt-3 flex flex-wrap gap-1.5">
      {selected.evidence.map(ev=><span key={ev} className="finna-chrono-evidence-tag">{dateEvidenceLabel(ev)}</span>)}
     </div>
     <Link className="finna-btn mt-4 w-full" to={source(selected)}>Sources & questions →</Link>
    </section>:<section className="finna-card">
     <h2>Explore an event</h2>
     <p className="mt-2 text-sm leading-relaxed text-secondary">Choose a timeline node or jump by year in the scrubber bar to inspect its recorded date, context and linked bank questions.</p>
    </section>}
    <section className="finna-card">
     <h2>Keep the source in view</h2>
     <p className="mt-2 text-sm leading-relaxed text-secondary">Dates are extracted from bank questions and recorded answers. Open the linked source to check its context; source labels remain attached.</p>
     <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
      <Link className="inline-flex min-h-11 items-center text-sm font-bold text-link" to="/chronicle?view=list">Date list →</Link>
      <Link className="inline-flex min-h-11 items-center text-sm font-bold text-link" to="/chronicle?view=calendar">Month calendar →</Link>
     </div>
    </section>
   </aside>
  </div>}
 </div>
}
