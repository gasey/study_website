import {dateMonths,dateEvidenceLabel,formatBankDate,dateYearGroup,type DateEvent} from '../lib/bankDates'

export function DateList({items,chronology=false,onSources}:{items:DateEvent[];chronology?:boolean;onSources:(id:string)=>void}){
 let previous=''
 return <ol aria-label={chronology?'Chronological events':'Dates and events'} className="border-t border-hairline">
  {items.map(entry=>{
   const group=dateYearGroup(entry),showGroup=chronology&&group!==previous;previous=group
   return <li key={entry.id}>
    {showGroup&&<h3 className="border-b border-hairline bg-canvas px-3 py-3 font-display text-[25px]">{group}</h3>}
    <div className="grid gap-x-6 gap-y-2 border-b border-hairline py-5 sm:grid-cols-[155px_minmax(0,1fr)_auto] sm:items-start">
     <p className="font-mono text-[14px] font-semibold leading-7 text-ink">{entry.dates.length?entry.dates.map(formatBankDate).join(' · '):'Date to check'}</p>
     <div className="min-w-0"><p className="font-display text-[22px] leading-snug [overflow-wrap:anywhere]">{entry.title}</p><p className="mt-2 text-[11px] leading-relaxed text-muted">{entry.category==='observance'?'Observance':entry.category==='history'?'History':'Event'} · {entry.evidence.map(dateEvidenceLabel).join(' · ')}</p></div>
     <button type="button" aria-label={`Sources for ${entry.title}`} onClick={()=>onSources(entry.id)} className="inline-flex min-h-11 items-center justify-self-start text-xs text-link underline-offset-4 hover:underline sm:justify-self-end">{entry.question_count} {entry.question_count===1?'source':'sources'} ↗</button>
    </div>
   </li>
  })}
 </ol>
}

/** Month/day index across all years; no implied weekday or annual recurrence. */
export function EventCalendar({month,day,counts,monthOnlyCount,onMonth,onDay}:{month:number;day:string;counts:{day:number;events:number}[];monthOnlyCount:number;onMonth:(month:number)=>void;onDay:(day:string)=>void}){
 const days=new Date(Date.UTC(2000,month,0)).getUTCDate()
 const byDay=new Map(counts.map(item=>[item.day,item.events]))
 return <section aria-label="Event calendar" className="mb-7 border-y border-hairline py-5">
  <div className="flex items-center justify-between gap-3"><button type="button" aria-label="Previous month" onClick={()=>onMonth(month===1?12:month-1)} className="min-h-11 min-w-11 rounded-pill border border-hairline px-3">←</button><div className="text-center"><h2 className="font-display text-[28px]">{dateMonths[month-1]}</h2><p className="text-xs text-muted">Month & day · across all years</p></div><button type="button" aria-label="Next month" onClick={()=>onMonth(month===12?1:month+1)} className="min-h-11 min-w-11 rounded-pill border border-hairline px-3">→</button></div>
  <p className="my-4 text-sm leading-relaxed text-secondary">Choose a date to see its events. These are dates from different years, grouped by day of the month.</p>
  <div className="grid grid-cols-7 gap-1 sm:gap-2" role="group" aria-label={`${dateMonths[month-1]} dates`}>{Array.from({length:days},(_,i)=>i+1).map(number=>{
   const count=byDay.get(number)||0,selected=day===String(number)
   return <button type="button" key={number} disabled={!count} aria-label={`${number} ${dateMonths[month-1]}: ${count} ${count===1?'event':'events'}`} aria-pressed={selected} onClick={()=>onDay(selected?'':String(number))} className={'flex min-h-[64px] min-w-0 flex-col items-center justify-center border p-1 text-sm transition-colors sm:min-h-[76px] '+(selected?'border-learn bg-learn-soft font-semibold text-learn-dark':count?'border-hairline bg-card hover:border-learn':'border-transparent text-muted disabled:opacity-50')}><span>{number}</span>{count>0&&<span className="mt-1 text-[10px] sm:text-xs">{count}<span className="hidden sm:inline"> {count===1?'event':'events'}</span></span>}</button>
  })}</div>
  <div className="mt-3 flex flex-wrap items-center justify-between gap-2"><button type="button" aria-pressed={!day} onClick={()=>onDay('')} className="min-h-11 text-sm text-link underline underline-offset-4">All dates in {dateMonths[month-1]}</button>{monthOnlyCount>0&&<p className="text-xs text-muted">{monthOnlyCount} month-only {monthOnlyCount===1?'entry':'entries'} in the full month list</p>}</div>
  <a href="#date-events" className="inline-flex min-h-11 items-center text-sm text-link">Jump to events ↓</a>
  <p className="mt-1 text-xs leading-relaxed text-muted">Year-only events appear in List and Chronology. No weekday or annual recurrence is assumed.</p>
 </section>
}
