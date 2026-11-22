import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {getCalendarLayers,type CalendarLayers} from '../lib/api'
import {deskRead} from '../lib/desk'
import {accountGeneration} from '../lib/accountContext'
import {dateLabel,dayNumber,indiaToday,ownedKindLabel,type OwnedOccurrence} from '../lib/calendar'
type Shared = OwnedOccurrence & {author:string;is_you:boolean;days_until:number}
type RoomDates = {occurrences:Shared[];limited:boolean;start:string;end:string}
/** One central calendar store; the room reads only explicitly shared entries. */
export default function DeskCalendar({deskId}:{deskId?:string}){
 const [data,setData]=useState<CalendarLayers|null>(null),[room,setRoom]=useState<RoomDates|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 const start=indiaToday(),end=new Date((dayNumber(start)+(deskId?31:7))*86400000).toISOString().slice(0,10)
 useEffect(()=>{
  let live=true,sequence=0;const generation=accountGeneration();const valid=()=>live&&generation===accountGeneration()
  setData(null);setRoom(null);setError('')
  async function load(){const run=++sequence;try{
   if(deskId){const r=await deskRead<RoomDates>(`/rooms/${encodeURIComponent(deskId)}/calendar?`+new URLSearchParams({start,end}));if(valid()&&run===sequence){setRoom(r);setError('')}}
   else{const r=await getCalendarLayers(start,end);if(valid()&&run===sequence){setData(r);setError('')}}
  }catch(e){if(valid()&&run===sequence){setRoom(null);setData(null);setError((e as Error).message)}}}
  const refresh=()=>{if(document.visibilityState==='visible')void load()},reset=()=>{live=false;++sequence;setData(null);setRoom(null);setError('Your account changed. Refresh this calendar to continue.')}
  void load();const timer=window.setInterval(refresh,30000)
  window.addEventListener('focus',refresh);window.addEventListener('ism-calendar-change',refresh);window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-auth-expired',reset)
  return()=>{reset();window.clearInterval(timer);window.removeEventListener('focus',refresh);window.removeEventListener('ism-calendar-change',refresh);window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-auth-expired',reset)}
 },[deskId,start,end,retry])
 const upcoming=data?[...data.occurrences.map(e=>({id:e.id+e.day,day:e.day,title:e.title,url:'/calendar?view=week&week='+e.day})),...data.community,...data.official.filter(e=>e.starts_on).map(e=>({id:'official:'+e.id,day:e.starts_on!<start?start:e.starts_on!,title:e.title,url:'/calendar?event='+e.id}))].sort((a,b)=>a.day.localeCompare(b.day)||a.id.localeCompare(b.id)):[]
 return <section className="my-4 min-w-0 rounded-panel border border-hairline bg-card p-4" aria-label={deskId?'Room calendar':'Upcoming calendar'}>
  <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-base font-bold">{deskId?'On this room’s calendar':'On your calendar'}</h2><Link className="inline-flex min-h-11 items-center text-sm font-bold text-link" to={'/calendar?view=week&week='+start}>Open calendar →</Link></div>
  {deskId&&<p className="mt-2 text-xs text-secondary">Coming month · India time. Members choose individual calendar entries to share here. Add or edit your entries in the main calendar; choose this room under “Share this entry”. Personal exam targets use the date chosen by their author.</p>}
  {error?<p role="alert" className="mt-3 break-words text-sm">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>:deskId?(!room?<p role="status" className="mt-3 text-sm text-secondary">Loading room dates…</p>:<>
   {room.occurrences.length?<ul className="mt-3 divide-y divide-hairline">{room.occurrences.slice(0,50).map(e=><li key={e.id+e.day} className="min-w-0 py-3"><p className="text-xs text-secondary">{dateLabel(e.day)} · {ownedKindLabel[e.kind]}{e.kind==='exam-target'&&` · ${e.days_until===0?'Today':e.days_until+' days away'}`}</p><h3 className="mt-1 break-words font-bold">{e.title}</h3><p className="text-xs text-secondary">Shared by {e.is_you?'you':e.author}</p>{e.note&&<p className="mt-2 whitespace-pre-wrap break-words text-sm">{e.note}</p>}</li>)}</ul>:<p className="mt-3 text-sm text-secondary">No entries shared with this room in the coming month. Private entries stay in their owners’ calendars.</p>}
   {(room.limited||room.occurrences.length>50)&&<p className="mt-2 text-xs text-secondary">Showing the first 50 upcoming dates from a bounded calendar view.</p>}
  </>):!data?<p role="status" className="text-sm text-secondary">Loading dates…</p>:!data.registered?<p className="text-sm text-secondary">Sign in to see your private plans here.</p>:upcoming.length?<ul>{upcoming.slice(0,4).map(e=><li key={e.id}><Link className="flex min-h-11 flex-wrap items-center gap-x-3 py-2 text-sm" to={e.url}><span className="text-secondary">{dateLabel(e.day)}</span><span className="min-w-0 break-words font-semibold text-link">{e.title}</span></Link></li>)}</ul>:<p className="text-sm text-secondary">No plans in the coming week. Add a goal or progress-test slot in your calendar.</p>}
 </section>
}
