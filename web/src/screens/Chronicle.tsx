import {lazy,Suspense,useCallback,useEffect,useMemo,useRef,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {
 bankDates,
 CHRONICLE_ERAS,
 dateEvidenceLabel,
 dateMonths,
 dateYearGroup,
 formatBankDate,
 timelineTrack,
 type ChronicleEra,
 type DateDetail,
 type DateEvent,
 type DateIndex,
} from '../lib/bankDates'
import {getQuestion,submitAnswer,type QuestionDetail} from '../lib/api'
import {learnerExplanation} from '../lib/answerStatus'
import {DateList} from '../components/ImportantDateViews'
import ChronicleNav from '../components/ChronicleNav'
import {ChronicleAtlasLinks} from '../components/AtlasProvenance'
import {CatLoader,CatXpBar} from '../components/CatLoader'
import {SourceQuestionContext,SourceQuestionText} from '../components/SourceQuestionText'
import Pagination from '../components/Pagination'
import {pageNumber} from '../lib/pagination'
import {useDebouncedValue} from '../lib/useDebouncedValue'

const SIZE=36
const LETTERS=['A','B','C','D']
const DateViews=lazy(()=>import('./ImportantDates'))

export default function Chronicle(){
 const [params]=useSearchParams()
 const dateView=['list','calendar','chronology','collections'].includes(params.get('view')||'')||params.has('event')||params.has('entry')
 return dateView?(
  <Suspense fallback={<div className="finna-page flex justify-center py-12"><CatLoader size="md" label="Loading Chronicle dates…"/></div>}>
   <DateViews/>
  </Suspense>
 ):<TimelineStudio/>
}

function formatTodayLabel(iso?:string){
 if(!iso)return 'Today'
 const parts=iso.split('-').map(Number)
 if(parts.length!==3||!parts[1]||!parts[2])return iso
 return `${parts[2]} ${dateMonths[parts[1]-1]}`
}

interface EraQuizModalProps{
 eraLabel:string
 items:DateEvent[]
 onClose:()=>void
}

function EraQuizModal({eraLabel,items,onClose}:EraQuizModalProps){
 const candidateIds=useMemo(()=>{
  const answerFirst=items
   .filter(e=>e.evidence.includes('answer')&&e.first_question_id)
   .map(e=>e.first_question_id)
  const fallback=items.map(e=>e.first_question_id).filter(Boolean)
  const unique=[...new Set(answerFirst.length>=3?answerFirst:[...answerFirst,...fallback])]
  if(unique.length<=10)return unique
  return Array.from({length:10},(_,i)=>unique[Math.round(i*(unique.length-1)/9)])
 },[items])

 const [questions,setQuestions]=useState<QuestionDetail[]>([])
 const [loading,setLoading]=useState(true)
 const [loadError,setLoadError]=useState('')
 const [index,setIndex]=useState(0)
 const [chosen,setChosen]=useState<number|null>(null)
 const [submitting,setSubmitting]=useState(false)
 const [result,setResult]=useState<{correct:boolean;answerIndex:number;explanation:string}|null>(null)
 const [score,setScore]=useState(0)
 const [streak,setStreak]=useState(0)
 const [bestStreak,setBestStreak]=useState(0)
 const [finished,setFinished]=useState(false)

 useEffect(()=>{
  let live=true
  setLoading(true);setLoadError('')
  Promise.all(
   candidateIds.map(id=>getQuestion(id).catch(()=>null))
  ).then(rows=>{
   if(!live)return
   const playable=rows.filter((q):q is QuestionDetail=>!!q&&q.type==='mcq'&&Array.isArray(q.options)&&q.options.length>=2&&q.answer_status!=='written'&&q.answer_status!=='unsolved')
   setQuestions(playable)
   if(!playable.length)setLoadError('No scorable MCQ questions are available in this view yet. Try another era or clear filters.')
  }).catch(()=>{
   if(live)setLoadError('Could not load era quiz questions.')
  }).finally(()=>{if(live)setLoading(false)})
  return()=>{live=false}
 },[candidateIds])

 const current=questions[index]||null

 async function handlePick(optionIdx:number){
  if(!current||chosen!==null||submitting)return
  setSubmitting(true)
  try{
   const res=await submitAnswer(current.id,optionIdx,'practice')
   const ok=!!res.correct
   const ansIdx=typeof res.answer_index==='number'?res.answer_index:current.options.findIndex(o=>o&&res.answer_text&&o===res.answer_text)
   setChosen(optionIdx)
   setResult({correct:ok,answerIndex:ansIdx,explanation:learnerExplanation(res.explanation||'')||''})
   if(ok){
    setScore(s=>s+1)
    setStreak(st=>{const next=st+1;setBestStreak(b=>Math.max(b,next));return next})
   }else{
    setStreak(0)
   }
  }catch{
   setChosen(optionIdx)
   setResult({correct:false,answerIndex:-1,explanation:'Could not submit right now. Open this question in the bank to check.'})
  }finally{
   setSubmitting(false)
  }
 }

 function nextQuestion(){
  if(index+1>=questions.length){setFinished(true);return}
  setIndex(i=>i+1);setChosen(null);setResult(null)
 }

 function restart(){
  setIndex(0);setChosen(null);setResult(null);setScore(0);setStreak(0);setBestStreak(0);setFinished(false)
 }

 const pct=questions.length?Math.round(((finished?questions.length:index+(result?1:0))/questions.length)*100):0

 return (
  <div className="chr-modal-backdrop" role="presentation" onClick={e=>{if(e.target===e.currentTarget)onClose()}}>
   <section role="dialog" aria-modal="true" aria-labelledby="chr-quiz-title" className="chr-modal">
    <div className="chr-modal-head">
     <div>
      <span className="chr-modal-kicker">🎯 Chronicle Era Drill · Real MPSC Bank MCQs</span>
      <h2 id="chr-quiz-title" className="chr-modal-title">{eraLabel}</h2>
     </div>
     <button type="button" className="chr-modal-close" onClick={onClose} aria-label="Close era quiz">×</button>
    </div>

    {loading?(
     <div className="flex flex-col items-center justify-center py-10">
      <CatLoader size="md" label="Building your era quiz from verified bank questions…"/>
     </div>
    ):loadError?(
     <div className="py-6 text-center">
      <p className="text-sm text-secondary">{loadError}</p>
      <button type="button" className="finna-btn mt-4" onClick={onClose}>Back to Chronicle</button>
     </div>
    ):finished?(
     <div className="chr-quiz-done">
      <div className="chr-quiz-score-ring">
       <strong>{score} / {questions.length}</strong>
       <span>{Math.round((score/Math.max(1,questions.length))*100)}% accuracy</span>
      </div>
      <h3>Era Drill Complete!</h3>
      <p className="text-sm text-secondary">
       Best streak: <strong>{bestStreak}</strong> · Every answered question is saved to your Finna study accuracy &amp; Smart Review queue.
      </p>
      <div className="mt-5 flex flex-wrap justify-center gap-2.5">
       <button type="button" className="finna-btn" onClick={restart}>↻ Drill Again</button>
       <button type="button" className="finna-btn finna-btn-quiet" onClick={onClose}>Return to Timeline</button>
      </div>
     </div>
    ):current&&(
     <div className="chr-quiz-body">
      <div className="flex items-center justify-between gap-3 text-xs font-bold text-secondary">
       <span>Question {index+1} of {questions.length}</span>
       <span>Score {score} · Streak 🔥 {streak}</span>
      </div>
      <CatXpBar value={pct} max={100} tone={streak>=3?'teal':'gold'} label="Era drill progress"/>

      <div className="chr-quiz-q">
       {current.source_appearance?.exam&&(
        <span className="chr-quiz-src">{current.source_appearance.exam}{current.source_appearance.year?` · ${current.source_appearance.year}`:''}</span>
       )}
       <SourceQuestionContext direction={current.direction} passage={current.passage}/>
       <div className="mt-1.5 text-base font-bold leading-relaxed text-ink">
        <SourceQuestionText text={current.question_markup||current.question}/>
       </div>
      </div>

      <div className="chr-quiz-opts">
       {current.options.map((opt,i)=>{
        const locked=chosen!==null
        const isCorrectOpt=locked&&result&&result.answerIndex===i
        const isWrongPick=locked&&chosen===i&&result&&!result.correct
        return (
         <button
          key={i}
          type="button"
          disabled={locked||submitting}
          onClick={()=>void handlePick(i)}
          className={`chr-quiz-opt${isCorrectOpt?' is-correct':''}${isWrongPick?' is-wrong':''}`}
         >
          <span className="chr-quiz-letter">{LETTERS[i]||i+1}</span>
          <span className="min-w-0 flex-1 text-left">
           <SourceQuestionText text={current.options_markup?.[i]||opt||''}/>
          </span>
         </button>
        )
       })}
      </div>

      {result&&(
       <div className={`chr-quiz-fb ${result.correct?'is-ok':'is-bad'}`}>
        <strong>{result.correct?'✓ Spot on! Date locked in.':'✕ Missed this date — review below.'}</strong>
        {result.explanation&&<p className="mt-1 text-xs leading-relaxed">{result.explanation}</p>}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
         <Link to={'/bank/'+encodeURIComponent(current.id)} className="text-xs font-bold text-link hover:underline" onClick={onClose}>
          Open full question &amp; discussion ↗
         </Link>
         <button type="button" className="finna-btn" onClick={nextQuestion}>
          {index+1>=questions.length?'See Final Score →':'Next Question →'}
         </button>
        </div>
       </div>
      )}
     </div>
    )}
   </section>
  </div>
 )
}

function TimelineStudio(){
 const [params,setParams]=useSearchParams()
 const [data,setData]=useState<DateIndex|null>(null)
 const [error,setError]=useState('')
 const [retry,setRetry]=useState(0)
 const [selected,setSelected]=useState<DateEvent|null>(null)
 const [detail,setDetail]=useState<DateDetail|null>(null)
 const [detailLoading,setDetailLoading]=useState(false)
 const [recallMode,setRecallMode]=useState(false)
 const [revealedIds,setRevealedIds]=useState<Set<string>>(()=>new Set())
 const [quizOpen,setQuizOpen]=useState(false)

 const nodeRefs=useRef<Record<string,HTMLButtonElement|null>>({})
 const railRef=useRef<HTMLDivElement|null>(null)
 const dragRef=useRef<{active:boolean;startX:number;scrollLeft:number}>({active:false,startX:0,scrollLeft:0})

 const mode=params.get('display')==='reading'?'reading':'canvas'
 const query=params.get('q')||''
 const page=pageNumber(params.get('page'))
 const era=(CHRONICLE_ERAS.some(e=>e.id===params.get('era'))?params.get('era'):'all') as ChronicleEra
 const category=['all','history','observance','event'].includes(params.get('category')||'')?params.get('category')!:'all'
 const subject=params.get('subject')||''
 const search=useDebouncedValue(query,220)

 function change(name:string,value:string){
  setParams(old=>{
   const next=new URLSearchParams(old)
   if(value&&(value!=='all'||name==='display'))next.set(name,value)
   else next.delete(name)
   if(name!=='page')next.delete('page')
   return next
  },{replace:name!=='page'})
 }

 useEffect(()=>{
  let live=true
  setData(null);setError('');setSelected(null);setDetail(null)
  const qs=new URLSearchParams({
   order:'year',
   origin:'all',
   evidence:'dated',
   limit:String(SIZE),
   offset:String((page-1)*SIZE),
   ...(era!=='all'?{era}:{}),
   ...(search?{q:search}:{}),
   ...(category!=='all'?{category}:{}),
   ...(subject?{subject_id:subject}:{}),
  }).toString()
  bankDates(qs).then(result=>{
   if(live&&'items'in result){
    setData(result)
    setSelected(result.items[0]||null)
   }
  }).catch(e=>{
   if(live)setError(e instanceof Error?e.message:'The timeline could not load.')
  })
  return()=>{live=false}
 },[era,search,category,subject,page,retry])

 // Load full linked bank questions inline when an event is selected
 useEffect(()=>{
  if(!selected){setDetail(null);return}
  let live=true
  setDetailLoading(true)
  bankDates(new URLSearchParams({event_id:selected.id,limit:'8'}).toString())
   .then(res=>{if(live&&'entry'in res)setDetail(res)})
   .catch(()=>{if(live)setDetail(null)})
   .finally(()=>{if(live)setDetailLoading(false)})
  return()=>{live=false}
 },[selected])

 useEffect(()=>{
  const reset=()=>{setData(null);setSelected(null);setDetail(null);setRetry(n=>n+1)}
  window.addEventListener('ism-auth-change',reset)
  window.addEventListener('ism-content-change',reset)
  return()=>{
   window.removeEventListener('ism-auth-change',reset)
   window.removeEventListener('ism-content-change',reset)
  }
 },[])

 useEffect(()=>{
  if(data&&page>Math.max(1,Math.ceil(data.total/SIZE)))change('page','')
  // eslint-disable-next-line react-hooks/exhaustive-deps
 },[data,page])

 const items=data?.items||[]
 const activeIndex=useMemo(()=>selected?items.findIndex(e=>e.id===selected.id):-1,[items,selected])
 const activeGroup=selected?dateYearGroup(selected):''
 const activeEraSpec=CHRONICLE_ERAS.find(e=>e.id===era)||CHRONICLE_ERAS[0]

 const milestones=useMemo(()=>{
  const groups:{label:string;firstId:string;count:number}[]=[]
  const byLabel=new Map<string,{label:string;firstId:string;count:number}>()
  for(const entry of items){
   const label=dateYearGroup(entry)
   const shortLabel=label==='Dates without a recorded year'?'Annual':label==='Dates to check'?'Check date':label
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
  if(!items.length||quizOpen)return
  const onKey=(e:KeyboardEvent)=>{
   const tag=(e.target as HTMLElement|null)?.tagName
   if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||(e.target as HTMLElement|null)?.isContentEditable)return
   if(e.metaKey||e.ctrlKey||e.altKey)return
   if(e.key==='ArrowLeft'){e.preventDefault();step(-1)}
   else if(e.key==='ArrowRight'){e.preventDefault();step(1)}
   else if(e.key.toLowerCase()==='h'){setRecallMode(r=>!r)}
  }
  window.addEventListener('keydown',onKey)
  return()=>window.removeEventListener('keydown',onKey)
 },[items.length,step,quizOpen])

 const toggleReveal=(id:string)=>{
  setRevealedIds(prev=>{
   const next=new Set(prev)
   if(next.has(id))next.delete(id)
   else next.add(id)
   return next
  })
 }

 const source=(entry:DateEvent)=>'/chronicle?'+new URLSearchParams({view:'chronology',event:entry.id})
 const mark=(entry:DateEvent)=>entry.dates.length?entry.dates.map(formatBankDate).join(' · '):'Date to check'
 const isMasked=(entry:DateEvent)=>recallMode&&!revealedIds.has(entry.id)
 const progressPct=items.length&&activeIndex>=0?Math.round(((activeIndex+1)/items.length)*100):0

 const hasFilters=!!(query||era!=='all'||category!=='all'||subject)

 return (
  <div className="finna-page finna-chronicle" data-screen="chronicle">
   {/* Editorial Archival Hero Banner */}
   <header className="chr-hero">
    <div className="chr-hero-main">
     <div className="chr-hero-eyebrow-row">
      <Link to="/library" className="chr-back-link">← Library</Link>
      <span className="chr-hero-kicker">Interactive Historical &amp; Polity Timeline</span>
     </div>
     <h1 className="chr-hero-title">Finna Chronicle</h1>
     <p className="chr-hero-sub">
      Explore verified dates from <strong>82,383+ MPSC &amp; India bank questions</strong> across every era — inspect linked questions inline, drill dates with Recall Mode, or launch an Era Quiz.
     </p>
     <div className="chr-hero-stats">
      <div className="chr-stat">
       <strong>{data?data.total.toLocaleString('en-IN'):'—'}</strong>
       <span>events in view</span>
      </div>
      <div className="chr-stat">
       <strong>{data?data.question_count.toLocaleString('en-IN'):'—'}</strong>
       <span>linked bank MCQs</span>
      </div>
      <div className="chr-stat">
       <strong>{formatTodayLabel(data?.today)}</strong>
       <span>today (IST)</span>
      </div>
     </div>
    </div>

    <div className="chr-hero-actions">
     <button
      type="button"
      className="chr-action-btn is-primary"
      disabled={!items.length}
      onClick={()=>setQuizOpen(true)}
     >
      🎯 Quiz This Era
     </button>
     <button
      type="button"
      aria-pressed={recallMode}
      className={`chr-action-btn${recallMode?' is-recall-on':''}`}
      onClick={()=>{setRecallMode(r=>!r);setRevealedIds(new Set())}}
      title="Hide dates on cards to test your memory (shortcut: H)"
     >
      {recallMode?'👁 Reveal All Dates':'🃏 Hide Dates (Drill)'}
     </button>
     <div className="chr-mode-toggle" role="group" aria-label="Timeline display">
      <button type="button" aria-pressed={mode==='canvas'} onClick={()=>change('display','canvas')}>Timeline</button>
      <button type="button" aria-pressed={mode==='reading'} onClick={()=>change('display','reading')}>Spine</button>
     </div>
    </div>
   </header>

   <ChronicleNav active="timeline"/>

   {/* On This Day in the Bank Spotlight */}
   {!!data?.on_this_day?.length&&!search&&(
    <section className="chr-otd" aria-label="On this day in the question bank">
     <div className="chr-otd-head">
      <span className="chr-otd-badge">📅 On This Day · {formatTodayLabel(data.today)}</span>
      <Link to="/chronicle?view=calendar" className="chr-otd-link">Full Month Calendar →</Link>
     </div>
     <div className="chr-otd-rail">
      {data.on_this_day.map(ev=>(
       <button
        key={ev.id}
        type="button"
        className={`chr-otd-chip${selected?.id===ev.id?' is-active':''}`}
        onClick={()=>setSelected(ev)}
       >
        <strong>{mark(ev)}</strong>
        <span>{ev.title}</span>
       </button>
      ))}
     </div>
    </section>
   )}

   {/* Interactive Era Ribbon */}
   <nav className="chr-era-ribbon" aria-label="Historical eras">
    {CHRONICLE_ERAS.map(e=>{
     const cnt=data?.era_counts?.[e.id]
     const active=era===e.id
     return (
      <button
       key={e.id}
       type="button"
       aria-pressed={active}
       className={`chr-era-card${active?' is-active':''}`}
       onClick={()=>change('era',e.id)}
      >
       <div className="chr-era-top">
        <span className="chr-era-icon" aria-hidden="true">{e.icon}</span>
        {cnt!=null&&<span className="chr-era-cnt">{cnt.toLocaleString('en-IN')}</span>}
       </div>
       <strong className="chr-era-name">{e.label}</strong>
       <small className="chr-era-range">{e.range}</small>
      </button>
     )
    })}
   </nav>

   {/* Search + Category + Subject Filter Bar */}
   <div className="chr-filter-bar">
    <label className="chr-search-wrap">
     <span className="sr-only">Search the timeline</span>
     <input
      type="search"
      aria-label="Search the timeline"
      value={query}
      onChange={e=>change('q',e.target.value)}
      placeholder="Search a year, treaty, Mizoram, Constitution, Battle…"
      className="chr-search-input"
     />
    </label>

    <div className="finna-segments" role="group" aria-label="Event category">
     {[['all','All'],['history','History'],['observance','Observances'],['event','Polity & Events']].map(([value,label])=>(
      <button type="button" key={value} aria-pressed={category===value} onClick={()=>change('category',value)}>{label}</button>
     ))}
    </div>

    {!!data?.subjects?.length&&(
     <select
      aria-label="Filter by subject"
      value={subject}
      onChange={e=>change('subject',e.target.value)}
      className="chr-subject-select"
     >
      <option value="">All subjects</option>
      {data.subjects.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}
     </select>
    )}

    {hasFilters&&(
     <button
      type="button"
      className="chr-reset-btn"
      onClick={()=>setParams(mode==='reading'?{display:'reading'}:{})}
     >
      Reset
     </button>
    )}
   </div>

   {error&&(
    <section className="finna-card" role="alert">
     <h2>The timeline couldn’t load</h2>
     <p className="mt-2 text-sm text-secondary">{error}</p>
     <button className="finna-btn mt-4" onClick={()=>setRetry(n=>n+1)}>Try again</button>
    </section>
   )}

   {!data&&!error&&(
    <section className="finna-card flex justify-center py-10" role="status">
     <CatLoader size="md" label="Loading dates and events from the bank…"/>
    </section>
   )}

   {data&&(
    <div className="finna-chronicle-layout">
     <section className="finna-card finna-chronicle-stage">
      <div className="finna-section-top">
       <div>
        <h2 className="text-xl">{activeEraSpec.icon} {activeEraSpec.label} <span className="text-sm font-normal text-secondary">({activeEraSpec.range})</span></h2>
        <p className="mt-1 text-xs text-secondary">
         {recallMode
          ?'🃏 Recall Mode active — dates are hidden! Click any event card to inspect & reveal its exact year.'
          :'Top track: History & Movements · Bottom track: Polity, Acts, Science & Observances. Drag or use ← → keys.'}
        </p>
       </div>
       <span className="finna-chrono-count">{data.total.toLocaleString('en-IN')} events</span>
      </div>

      {items.length>0&&(
       <div className="finna-chrono-dock" role="region" aria-label="Chronology scrubber navigation">
        <div className="finna-chrono-dock-controls">
         <button type="button" className="finna-chrono-step" aria-label="Previous event" disabled={activeIndex<=0} onClick={()=>step(-1)}>‹</button>
         <span className="finna-chrono-pos" aria-live="polite">{activeIndex>=0?activeIndex+1:1} / {items.length}</span>
         <button type="button" className="finna-chrono-step" aria-label="Next event" disabled={activeIndex>=items.length-1} onClick={()=>step(1)}>›</button>
        </div>
        <div className="finna-chrono-scrubber" aria-label="Jump to year or date group">
         {milestones.map(m=>{
          const matchEntry=items.find(e=>e.id===m.firstId)
          const isCurrent=!!matchEntry&&dateYearGroup(matchEntry)===activeGroup
          return (
           <button
            key={m.firstId}
            type="button"
            aria-pressed={isCurrent}
            className={'finna-chrono-pill'+(isCurrent?' is-active':'')}
            onClick={()=>matchEntry&&focusEvent(matchEntry,true)}
           >
            <span>{recallMode?'???':m.label}</span>
            {m.count>1&&<em className="finna-chrono-pill-badge">{m.count}</em>}
           </button>
          )
         })}
        </div>
        <span className="finna-chrono-keys" aria-hidden="true"><kbd>←</kbd><kbd>→</kbd><kbd>H</kbd></span>
        <div className="finna-chrono-progress" aria-hidden="true"><span style={{width:`${progressPct}%`}}/></div>
       </div>
      )}

      {!items.length?(
       <div className="py-10 text-center">
        <p className="text-base font-bold text-ink">No events match this filter</p>
        <p className="mt-1 text-sm text-secondary">Try switching to All Eras or broadening your search keyword.</p>
        {hasFilters&&<button type="button" className="finna-btn mt-4" onClick={()=>setParams({})}>Show All Eras</button>}
       </div>
      ):mode==='reading'?(
       <DateList
        items={items}
        chronology
        onSources={id=>{const found=items.find(e=>e.id===id);if(found)setSelected(found)}}
       />
      ):(
       <div
        ref={railRef}
        className="finna-chronicle-scroll chr-drag-rail"
        role="region"
        aria-label="Chronological timeline"
        tabIndex={0}
        onMouseDown={e=>{
         if((e.target as HTMLElement).closest('button'))return
         const el=railRef.current;if(!el)return
         dragRef.current={active:true,startX:e.pageX-el.offsetLeft,scrollLeft:el.scrollLeft}
        }}
        onMouseMove={e=>{
         if(!dragRef.current.active||!railRef.current)return
         e.preventDefault()
         const x=e.pageX-railRef.current.offsetLeft
         railRef.current.scrollLeft=dragRef.current.scrollLeft-(x-dragRef.current.startX)*1.25
        }}
        onMouseUp={()=>{dragRef.current.active=false}}
        onMouseLeave={()=>{dragRef.current.active=false}}
       >
        <div
         className="finna-chronicle-tracks"
         style={{minWidth:Math.max(920,items.length*206)+'px',gridTemplateColumns:`repeat(${items.length},206px)`}}
        >
         <span className="finna-track-label">🏛 History, Battles &amp; Freedom Movements</span>
         {items.map((entry,i)=>{
          const track=timelineTrack(entry)
          const masked=isMasked(entry)
          return (
           <button
            key={entry.id}
            ref={node=>{nodeRefs.current[entry.id]=node}}
            type="button"
            data-track={track}
            data-cat={entry.category}
            aria-pressed={selected?.id===entry.id}
            className="finna-event-node"
            title={entry.title}
            style={{gridColumn:i+1,gridRow:track==='top'?2:4}}
            onClick={()=>focusEvent(entry,true)}
           >
            <div className="chr-node-top">
             <strong>{masked?'🃏 Tap to recall':mark(entry)}</strong>
             <span className={`chr-dot chr-dot--${entry.category}`} aria-hidden="true"/>
            </div>
            <span>{entry.title}</span>
            <small>{entry.question_count} {entry.question_count===1?'MCQ':'MCQs'}{entry.subjects[0]?` · ${entry.subjects[0]}`:''}</small>
           </button>
          )
         })}
         <div className="finna-timeline-axis" style={{gridColumn:'1 / -1',gridRow:3}}/>
         <span className="finna-track-label finna-track-label-bottom">⚖️ Polity, Acts, Institutions &amp; Observances</span>
        </div>
       </div>
      )}

      <Pagination page={page} pages={Math.max(1,Math.ceil(data.total/SIZE))} onPageChange={n=>change('page',String(n))} label="Timeline pages"/>
     </section>

     {/* Live Inline Event Inspector Rail */}
     <aside className="finna-chronicle-aside space-y-4">
      {selected?(
       <section className="finna-card finna-event-detail">
        <div className="finna-section-top">
         <div className="flex flex-wrap items-center gap-1.5">
          <span className="finna-chrono-cat-badge">{selected.category}</span>
          {selected.era&&selected.era!=='other'&&(
           <span className="finna-chrono-evidence-tag">{CHRONICLE_ERAS.find(e=>e.id===selected.era)?.label||selected.era}</span>
          )}
         </div>
         <div className="flex items-center gap-1">
          <button type="button" className="finna-chrono-mini-step" aria-label="Previous event" disabled={activeIndex<=0} onClick={()=>step(-1)}>‹</button>
          <button type="button" className="finna-chrono-mini-step" aria-label="Next event" disabled={activeIndex>=items.length-1} onClick={()=>step(1)}>›</button>
          <button type="button" className="ml-1 min-h-9 text-xs font-bold text-link" onClick={()=>setSelected(null)}>Close</button>
         </div>
        </div>

        {isMasked(selected)?(
         <button type="button" className="chr-reveal-date-btn mt-3" onClick={()=>toggleReveal(selected.id)}>
          🃏 Reveal Recorded Date →
         </button>
        ):(
         <p className="finna-event-date mt-2">{mark(selected)}</p>
        )}

        <h2 className="mt-2.5 text-xl leading-snug">{selected.title}</h2>
        <ChronicleAtlasLinks entryId={selected.id}/>

        <div className="mt-3 flex flex-wrap gap-1.5">
         {selected.evidence.map(ev=><span key={ev} className="finna-chrono-evidence-tag">{dateEvidenceLabel(ev)}</span>)}
         {selected.subjects.slice(0,2).map(sub=><span key={sub} className="finna-chrono-evidence-tag">{sub}</span>)}
        </div>

        {/* Inline Linked Bank Questions */}
        <div className="chr-inline-qs mt-4">
         <div className="chr-inline-qs-head">
          <span>Linked Bank Questions ({detail?.total??selected.question_count})</span>
         </div>
         {detailLoading?(
          <p className="py-3 text-xs text-secondary">Loading linked questions…</p>
         ):detail?.questions?.length?(
          <ul className="chr-inline-q-list">
           {detail.questions.slice(0,4).map(q=>(
            <li key={q.id} className="chr-inline-q-item">
             <p className="chr-inline-q-text">{q.question}</p>
             <div className="chr-inline-q-foot">
              <span>{q.origin==='community'?'Website':'Past paper'}{q.subject?` · ${q.subject}`:''}</span>
              <Link to={'/bank/'+encodeURIComponent(q.id)} className="font-bold text-link hover:underline">
               Practice →
              </Link>
             </div>
            </li>
           ))}
          </ul>
         ):(
          <p className="py-2 text-xs text-secondary">{selected.preview}</p>
         )}
        </div>

        <div className="mt-4 flex flex-col gap-2">
         {selected.first_question_id&&(
          <Link className="finna-btn w-full" to={'/bank/'+encodeURIComponent(selected.first_question_id)}>
           Practice primary question →
          </Link>
         )}
         <Link className="finna-btn finna-btn-quiet w-full" to={source(selected)}>
          All sources &amp; full list ↗
         </Link>
        </div>
       </section>
      ):(
       <section className="finna-card">
        <h2>Explore an event</h2>
        <p className="mt-2 text-sm leading-relaxed text-secondary">
         Click any timeline node, jump by Era above, or press <kbd>←</kbd> <kbd>→</kbd> to inspect verified dates and practice linked bank questions inline.
        </p>
       </section>
      )}

      <section className="finna-card">
       <h2 className="text-base">Quick Views &amp; Study Modes</h2>
       <p className="mt-1.5 text-xs leading-relaxed text-secondary">
        Switch to the Month Calendar heatmap for Important Days, or launch a 10-question Era Drill using official bank answers.
       </p>
       <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" className="finna-btn finna-btn-quiet" disabled={!items.length} onClick={()=>setQuizOpen(true)}>
         🎯 Quiz this era
        </button>
        <Link className="finna-btn finna-btn-quiet" to="/chronicle?view=calendar">
         📅 Month calendar
        </Link>
        <Link className="finna-btn finna-btn-quiet" to="/chronicle?view=list">
         📋 Full date list
        </Link>
       </div>
      </section>
     </aside>
    </div>
   )}

   {quizOpen&&(
    <EraQuizModal
     eraLabel={`${activeEraSpec.icon} ${activeEraSpec.label} (${activeEraSpec.range})`}
     items={items}
     onClose={()=>setQuizOpen(false)}
    />
   )}
  </div>
 )
}
