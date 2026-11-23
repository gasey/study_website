import {useEffect,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {bankDates,dateMonths,formatBankDate,dateEvidenceLabel,type DateIndex,type DateDetail,type DateEvent} from '../lib/bankDates'
import Pagination from '../components/Pagination'
import LearningCatalog from './LearningCatalog'
import {EventCalendar} from '../components/ImportantDateViews'
import DateEventStream from '../components/DateEventStream'
import {ChronicleAtlasLinks} from '../components/AtlasProvenance'
import ChronicleNav from '../components/ChronicleNav'

const control='min-h-11 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-learn'
const categories=[['','All events'],['observance','Observances'],['history','History'],['event','Other events']]
function choice(value:string|null,allowed:string[],fallback=''){return value&&allowed.includes(value)?value:fallback}
function positive(value:string|null){return Math.min(4000,Math.max(1,Number(value)||1))|0}
function EventDate({entry}:{entry:DateEvent}){
 return <><p className="font-display text-xl leading-tight text-ink">{entry.dates.length?entry.dates.map(formatBankDate).join(' · '):'Date to check'}</p><p className="mt-1 text-xs text-muted">{entry.dates.length?entry.evidence.map(dateEvidenceLabel).join(' · '):'Open the question to investigate the date'}</p></>
}
export default function ImportantDates(){
 const [params]=useSearchParams()
 if(params.get('view')==='collections'||params.get('entry')?.startsWith('learn_'))return <><div className="mx-auto max-w-6xl px-4 pt-5"><Link className="inline-flex min-h-11 items-center text-sm text-link" to="/chronicle">← All dates & events from the bank</Link></div><LearningCatalog kind="day"/></>
 return <BankDateBrowser/>
}
function BankDateBrowser(){
 const [params,setParams]=useSearchParams()
 const mode=choice(params.get('view'),['list','chronology','calendar'],'list')
 const currentMonth=new Intl.DateTimeFormat('en',{month:'numeric',timeZone:'Asia/Kolkata'}).format(new Date())
 const search=(params.get('q')||'').slice(0,120),month=choice(params.get('month'),Array.from({length:12},(_,i)=>String(i+1)))
 const category=choice(params.get('category'),['observance','history','event']),origin=choice(params.get('origin'),['paper','community'],'all')
 const evidence=choice(params.get('evidence'),['all','dated','unresolved'],'dated')
 const order=mode==='chronology'?'year':mode==='calendar'?'calendar':choice(params.get('order'),['title','year'],'calendar')
 const activeMonth=mode==='calendar'?month||currentMonth:month
 const day=mode==='calendar'?choice(params.get('day'),Array.from({length:31},(_,i)=>String(i+1))):''
 const subject=params.get('subject')||'',event=choice(params.get('event'),[params.get('event')?.match(/^date_[0-9a-f]{20}$/)?.[0]||''])
 const page=positive(params.get(event?'question_page':'page'))
 const request=new URLSearchParams({origin,evidence,order,limit:'24',offset:String((page-1)*24),...(search?{q:search}:{}),...(activeMonth?{month:activeMonth}:{}),...(day?{day}:{}),...(category?{category}:{}),...(subject?{subject_id:subject}:{}),...(event?{event_id:event}:{})}).toString()
 const [revision,setRevision]=useState(0),[loaded,setLoaded]=useState<{key:string;data:DateIndex|DateDetail}|null>(null),[failure,setFailure]=useState<{key:string;message:string}|null>(null)
 const [subjects,setSubjects]=useState<{id:string;title:string}[]>([])
 const key=request+':'+revision,data=loaded?.key===key?loaded.data:null,error=failure?.key===key?failure.message:''
 useEffect(()=>{const refresh=()=>{setLoaded(null);setFailure(null);setSubjects([]);setRevision(v=>v+1)};window.addEventListener('ism-auth-change',refresh);window.addEventListener('ism-content-change',refresh);return()=>{window.removeEventListener('ism-auth-change',refresh);window.removeEventListener('ism-content-change',refresh)}},[])
 useEffect(()=>{let live=true;const timer=setTimeout(()=>{bankDates(request).then(data=>{if(live){if('items'in data&&data.total>0&&data.offset>=data.total&&data.offset>0){setParams(p=>{const next=new URLSearchParams(p);next.delete('page');return next});return}setLoaded({key,data});setFailure(null);setSubjects(data.subjects)}}).catch(e=>{if(live)setFailure({key,message:e.message||'Could not load dates. Please try again.'})})},200);return()=>{live=false;clearTimeout(timer)}},[request,key])
 function change(name:string,value:string){setParams(p=>{const next=new URLSearchParams(p);next.delete('event');next.delete('question_page');next.delete('page');next.delete('day');if(value)next.set(name,value);else next.delete(name);return next})}
 function setMode(value:string){setParams(p=>{const next=new URLSearchParams(p);for(const key of ['event','question_page','page','day','order'])next.delete(key);next.set('view',value);if(value==='calendar'&&!month)next.set('month',currentMonth);return next})}
 function reset(){setParams(mode==='calendar'?{view:mode,month:currentMonth}:mode==='chronology'?{view:mode}:{})}
 function open(id:string){setParams(p=>{const next=new URLSearchParams(p);next.set('event',id);next.delete('question_page');return next})}
 function back(){setParams(p=>{const next=new URLSearchParams(p);next.delete('event');next.delete('question_page');return next})}
 const index=data&&'items'in data?data:null,detail=data&&'entry'in data?data:null
 const hasFilters=!!(search||mode!=='calendar'&&month||day||category||subject||origin!=='all'||evidence!=='dated')
 return <div className="mx-auto max-w-6xl px-4 pb-24 pt-7 sm:px-6">
  <nav aria-label="Study navigation" className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-link"><Link className="inline-flex min-h-11 items-center" to="/library">← Library</Link><Link className="inline-flex min-h-11 items-center" to="/bank">Question bank</Link></nav>
  <header className="mb-7 mt-5"><p className="font-mono text-xs uppercase tracking-widest text-learn">From the question bank</p><h1 className="mt-3 font-display text-3xl leading-tight sm:text-3xl">Chronicle</h1><p className="mt-3 max-w-2xl text-base leading-relaxed text-secondary">Read dates and events from the bank in one place. Browse the list, follow historical chronology or explore a month.</p></header>
  <ChronicleNav active={mode as 'list'|'chronology'|'calendar'} onSelectMode={setMode}/>
  <section aria-label="Filter dates and events" className="mb-5 border-y border-hairline py-5">
   <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_200px]"><label className="grid gap-2 text-xs font-semibold">Search events<input aria-label="Search events" type="search" className={control} placeholder="Try Environment Day or Plassey" value={search} maxLength={120} onChange={e=>change('q',e.target.value)}/></label><label className="grid gap-2 text-xs font-semibold">Month<select aria-label="Month" className={control} value={activeMonth} onChange={e=>change('month',e.target.value)}>{mode!=='calendar'&&<option value="">All months</option>}{dateMonths.map((m,i)=><option key={m} value={i+1}>{m}</option>)}</select></label></div>
   <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Event category">{categories.map(([value,label])=><button key={value} type="button" aria-pressed={category===value} className={'min-h-11 rounded-pill border px-4 text-sm transition-colors '+(category===value?'border-learn bg-learn-soft font-semibold text-learn-dark':'border-hairline bg-card text-secondary hover:border-ink')} onClick={()=>change('category',value)}>{label}</button>)}</div>
   <details className="mt-3"><summary className="min-h-11 cursor-pointer py-3 text-sm text-secondary">More filters · source, subject & dates{[origin!=='all',!!subject,evidence!=='dated',mode==='list'&&order!=='calendar'].filter(Boolean).length>0?' · applied':''}</summary><div className="mt-2 grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 lg:grid-cols-4"><label className="grid gap-2 text-xs font-semibold">Question source<select aria-label="Question source" className={control} value={origin} onChange={e=>change('origin',e.target.value)}><option value="all">Both banks</option><option value="paper">MPSC past papers</option><option value="community">Website practice</option></select></label><label className="grid gap-2 text-xs font-semibold">Subject<select aria-label="Subject" className={control} value={subject} onChange={e=>change('subject',e.target.value)}><option value="">All subjects</option>{subject&&!subjects.some(s=>s.id===subject)&&<option value={subject}>{subject}</option>}{subjects.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label><label className="grid gap-2 text-xs font-semibold">Date availability<select aria-label="Date availability" className={control} value={evidence} onChange={e=>change('evidence',e.target.value)}><option value="all">Include dates to check</option><option value="dated">Date available</option><option value="unresolved">Only dates to check</option></select></label>{mode==='list'&&<label className="grid gap-2 text-xs font-semibold">Sort by<select aria-label="Sort by" className={control} value={order} onChange={e=>change('order',e.target.value)}><option value="calendar">Month & day</option><option value="title">Event name</option><option value="year">Historical year</option></select></label>}</div></details>
   {hasFilters&&<button type="button" className="mt-2 min-h-11 text-sm text-link underline underline-offset-4" onClick={reset}>Clear filters</button>}
  </section>
  <p className="mb-6 max-w-3xl text-xs leading-relaxed text-muted">Dates come from bank answers or mentions in question text. A question mention may need checking. Missing dates are never invented; sources are optional references.</p>
  {error&&<div role="alert" className="rounded-[14px] border border-hairline bg-card p-6"><p>{error}</p><button type="button" className="mt-3 min-h-11 text-link underline" onClick={()=>setRevision(v=>v+1)}>Try again</button>{event&&<button type="button" className="ml-5 min-h-11 text-link" onClick={back}>Back to events</button>}</div>}
  {!data&&!error&&<div role="status" className="rounded-[14px] border border-hairline bg-card p-8 text-secondary">Finding dates & events in the bank…</div>}
  {index&&<>
   {mode==='calendar'&&<EventCalendar month={Number(activeMonth)} day={day} counts={index.calendar_days} monthOnlyCount={index.month_only_count} onMonth={number=>change('month',String(number))} onDay={value=>change('day',value)}/>}
   <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2" aria-live="polite"><h2 id="date-events" className="scroll-mt-24 font-display text-2xl">{index.total.toLocaleString('en-IN')} {index.total===1?'event':'events'}{mode==='calendar'&&day?` · ${day} ${dateMonths[Number(activeMonth)-1]}`:''}</h2><p className="text-xs text-muted">{mode==='chronology'?'Earliest recorded year first · dates without a year follow':mode==='calendar'?'Events for the selected month or day':'Dates shown directly · sources available for reference'}</p></div>
   {!index.items.length?<div className="border-y border-hairline py-8"><h3 className="font-display text-2xl">{index.total?'This page is no longer available':'No events match these filters'}</h3><p className="mt-2 text-sm text-secondary">Try a broader search or another month. Year-only events appear in List and Chronology.</p><button className="mt-3 min-h-11 text-link underline" onClick={reset}>Show dates & events</button></div>:<DateEventStream key={key} initial={index} request={request} chronology={mode==='chronology'} onSources={open} onStart={()=>setParams(p=>{const next=new URLSearchParams(p);next.delete('page');return next})}/>}
  </>}
  {detail&&<><button type="button" className="mb-4 min-h-11 text-sm text-link" onClick={back}>← Back to events</button><section className="border-y border-hairline py-6"><EventDate entry={detail.entry}/><ChronicleAtlasLinks entryId={detail.entry.id}/><h2 className="mt-5 font-display text-3xl leading-tight">{detail.entry.title}</h2><p className="mt-3 text-sm text-secondary">{detail.total} linked {detail.total===1?'question':'questions'}. These optional references show where the event appears in the bank.</p></section><h3 className="mb-4 mt-7 font-display text-2xl">Source references</h3><ol className="border-t border-hairline">{detail.questions.map(question=><li key={question.id} className="border-b border-hairline py-5"><p className="text-xs text-muted">{question.origin==='community'?'Website practice':'MPSC past paper'}{question.subject?' · '+question.subject:''} · {dateEvidenceLabel(question.evidence)}</p><p className="mt-3 font-display text-lg leading-relaxed">{question.question}</p><Link className="mt-3 inline-flex min-h-11 items-center text-sm font-semibold text-link" to={'/bank/'+encodeURIComponent(question.id)}>Original question & source ↗</Link></li>)}</ol><Pagination label="Source question pages" page={page} pages={Math.ceil(detail.total/24)} onPageChange={n=>setParams(p=>{const next=new URLSearchParams(p);next.set('question_page',String(n));return next})}/></>}
 </div>
}
