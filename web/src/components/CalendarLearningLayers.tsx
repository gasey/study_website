import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {getCalendarLayers,type CalendarLayers,type HomeData} from '../lib/api'
import OwnedCalendar from './OwnedCalendar'
export type LearningLayersState={data:CalendarLayers|null;forecast:boolean;habit:boolean;personal:boolean;progress:boolean;targets:boolean;official:boolean;community:boolean}
export default function CalendarLearningLayers({start,end,exams,onLayers}:{start:string;end:string;exams:HomeData['collections'];onLayers?:(state:LearningLayersState)=>void}){
 const [data,setData]=useState<CalendarLayers|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0),[forecast,setForecast]=useState(true),[habit,setHabit]=useState(false),[personal,setPersonal]=useState(true),[progress,setProgress]=useState(true),[targets,setTargets]=useState(true),[official,setOfficial]=useState(true),[community,setCommunity]=useState(true)
 useEffect(()=>{let live=true;setData(null);setError('');getCalendarLayers(start,end).then(d=>{if(live)setData(d)}).catch(e=>{if(live)setError(e.message)});const refresh=()=>{live=false;setData(null);setRetry(n=>n+1)};window.addEventListener('ism-auth-change',refresh);window.addEventListener('ism-calendar-change',refresh);return()=>{live=false;window.removeEventListener('ism-auth-change',refresh);window.removeEventListener('ism-calendar-change',refresh)}},[start,end,retry])
 useEffect(()=>{onLayers?.({data,forecast,habit,personal,progress,targets,official,community})},[data,forecast,habit,personal,progress,targets,official,community,onLayers])
 return <section className="my-5 min-w-0 rounded-panel border border-hairline bg-card p-4 sm:p-5"><h2 className="font-display text-[24px]">Your calendar layers</h2><p className="mt-2 text-[12px] leading-relaxed text-secondary">Official dates and your private plans share the grid below. Review forecasts shift as you answer.</p>
  <fieldset className="mt-3 flex flex-wrap gap-x-4"><legend className="sr-only">Calendar layers</legend><label className="flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" checked={official} onChange={e=>setOfficial(e.target.checked)}/>Official dates</label>{data?.registered&&<>{([[forecast,setForecast,'Review forecast'],[habit,setHabit,'Verified activity'],[personal,setPersonal,'Personal'],[progress,setProgress,'Progress tests'],[targets,setTargets,'My exams'],[community,setCommunity,'Community & play']] as const).map(([checked,change,label])=><label key={label} className="flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" checked={checked} onChange={e=>change(e.target.checked)}/>{label}</label>)}</>}</fieldset>
  {error?<p role="alert" className="text-sm">{error} <button className="min-h-11 font-bold text-link underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>:!data?<p role="status" className="text-sm text-secondary">Loading learning layers…</p>:data.registered?<>
   {forecast&&<p className="mt-2 text-sm text-secondary">{data.forecast.length?'Review counts appear on the calendar. Select a day to review early.':'No question reviews are scheduled in this date range.'}</p>}
   {habit&&<p className="mt-2 text-sm text-secondary">{data.habit.length?'Activity dots mark days with verified checks.':'No verified activity in this date range.'}</p>}
   <Link to="/revise" className="mt-2 inline-flex min-h-11 items-center text-sm font-bold text-link">Your full review queue →</Link>
   {community&&<p className="mt-2 text-xs text-secondary">Weekly Cup times use the game schedule. Desk events will appear when Desk scheduling is available.</p>}
   <OwnedCalendar entries={data.entries} exams={exams}/>
  </>:<p className="mt-2 text-sm text-secondary"><Link to="/login" className="inline-flex min-h-11 items-center font-bold text-link">Sign in</Link> for private entries, exam targets, progress tests and review forecasts.</p>}
 </section>
}
