import {dateMonths,dateEvidenceLabel,formatBankDate,dateYearGroup,type DateEvent} from '../lib/bankDates'

export function DateList({items,chronology=false,onSources}:{items:DateEvent[];chronology?:boolean;onSources:(id:string)=>void}){
 let previous=''
 return <ol aria-label={chronology?'Chronological events':'Dates and events'} className="border-t border-hairline">
  {items.map(entry=>{
   const group=dateYearGroup(entry),showGroup=chronology&&group!==previous;previous=group
   return <li key={entry.id}>
    {showGroup&&<h3 className="border-b border-hairline bg-canvas px-3 py-3 font-display text-xl">{group}</h3>}
    <div className="grid gap-x-6 gap-y-2 border-b border-hairline py-5 sm:grid-cols-[155px_minmax(0,1fr)_auto] sm:items-start">
     <p className="font-mono text-sm font-semibold leading-7 text-ink">{entry.dates.length?entry.dates.map(formatBankDate).join(' · '):'Date to check'}</p>
     <div className="min-w-0"><p className="font-display text-lg leading-snug [overflow-wrap:anywhere]">{entry.title}</p><p className="mt-2 text-xs leading-relaxed text-muted">{entry.category==='observance'?'Observance':entry.category==='history'?'History':'Event'} · {entry.evidence.map(dateEvidenceLabel).join(' · ')}</p></div>
     <button type="button" aria-label={`Sources for ${entry.title}`} onClick={()=>onSources(entry.id)} className="inline-flex min-h-11 items-center justify-self-start text-xs text-link underline-offset-4 hover:underline sm:justify-self-end">{entry.question_count} {entry.question_count===1?'source':'sources'} ↗</button>
    </div>
   </li>
  })}
 </ol>
}

const SHORT_MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function heatTier(count:number):number{
 if(!count)return 0
 if(count<=2)return 1
 if(count<=7)return 2
 return 3
}

/** Month/day index across all years; no implied weekday or annual recurrence. */
export function EventCalendar({month,day,counts,monthOnlyCount,onMonth,onDay}:{month:number;day:string;counts:{day:number;events:number}[];monthOnlyCount:number;onMonth:(month:number)=>void;onDay:(day:string)=>void}){
 const days=new Date(Date.UTC(2000,month,0)).getUTCDate()
 const byDay=new Map(counts.map(item=>[item.day,item.events]))
 const monthTotal=counts.reduce((sum,item)=>sum+item.events,0)
 return <section aria-label="Event calendar" className="cal-card cal-chrono-card">
  <header className="cal-card-head cal-card-head--chrono">
   <button type="button" aria-label="Previous month" onClick={()=>onMonth(month===1?12:month-1)} className="cal-head-arrow">←</button>
   <div className="cal-head-center">
    <h2>{dateMonths[month-1]}</h2>
    <p>Month &amp; day · across all years · {monthTotal.toLocaleString('en-IN')} dated {monthTotal===1?'entry':'entries'}</p>
   </div>
   <button type="button" aria-label="Next month" onClick={()=>onMonth(month===12?1:month+1)} className="cal-head-arrow">→</button>
  </header>

  <div className="cal-month-strip" role="group" aria-label="Jump to month">
   {SHORT_MONTHS.map((label,idx)=><button key={label} type="button" aria-pressed={month===idx+1} onClick={()=>onMonth(idx+1)} className={'cal-month-chip'+(month===idx+1?' is-active':'')}>{label}</button>)}
  </div>

  <div className="cal-chrono-body">
   <p className="cal-chrono-note">Choose any highlighted day to filter its bank events. Colour intensity reflects how many events fall on that day across all years.</p>
   <div className="cal-chrono-grid" role="group" aria-label={`${dateMonths[month-1]} dates`}>{Array.from({length:days},(_,i)=>i+1).map(number=>{
    const count=byDay.get(number)||0,selected=day===String(number),tier=heatTier(count)
    return <button type="button" key={number} disabled={!count} aria-label={`${number} ${dateMonths[month-1]}: ${count} ${count===1?'event':'events'}`} aria-pressed={selected} onClick={()=>onDay(selected?'':String(number))} data-tier={tier} className={'cal-chrono-day'+(selected?' is-selected':'')}>
     <span className="cal-chrono-num">{number}</span>
     {count>0?<span className="cal-chrono-cnt">{count}<span className="cal-chrono-unit"> {count===1?'event':'events'}</span></span>:<span className="cal-chrono-empty" aria-hidden="true">·</span>}
    </button>
   })}</div>

   <div className="cal-chrono-foot">
    <div className="cal-heat-legend" aria-hidden="true">
     <span>Density</span>
     <i data-tier="0"/>
     <i data-tier="1"/>
     <i data-tier="2"/>
     <i data-tier="3"/>
     <span>More</span>
    </div>
    <div className="cal-chrono-actions">
     <button type="button" aria-pressed={!day} onClick={()=>onDay('')} className={'cal-foot-pill'+(!day?' is-active':'')}>All dates in {dateMonths[month-1]}</button>
     <a href="#date-events" className="cal-foot-link">Jump to events ↓</a>
    </div>
   </div>
   {monthOnlyCount>0&&<p className="cal-chrono-sub">{monthOnlyCount} month-only {monthOnlyCount===1?'entry':'entries'} included in the full month list below.</p>}
   <p className="cal-chrono-sub">Year-only events appear in List and Chronology. No weekday or annual recurrence is assumed.</p>
  </div>
 </section>
}
