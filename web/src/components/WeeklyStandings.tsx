import {useEffect,useState} from 'react'
import {reviewRequest} from '../lib/review'

type Row={handle:string;rank:number;xp?:number;score?:number}
type Board={top:Row[];nearby:Row[];items:Row[];total:number;placement:{rank:number;xp?:number;score?:number;public:boolean}|null;league?:{name:string};period_start:string;period_end:string;neighborhood_truncated:boolean}

export default function WeeklyStandings({endpoint,unit='XP',empty='No public scores this week yet.'}:{endpoint:string;unit?:string;empty?:string}){
 const [board,setBoard]=useState<Board|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{const refresh=()=>{setBoard(null);setError('');setRetry(n=>n+1)};window.addEventListener('ism-auth-change',refresh);return()=>window.removeEventListener('ism-auth-change',refresh)},[])
 useEffect(()=>{let live=true;setBoard(null);setError('');reviewRequest<Board>(endpoint).then(x=>{if(live)setBoard(x)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[endpoint,retry])
 const score=(row:{xp?:number;score?:number})=>(row.xp??row.score??0).toLocaleString('en-IN')
 function rows(items:Row[]){return <ol className="divide-y divide-hairline">{items.map((row,i)=><li key={row.handle+'-'+i} className="flex min-h-14 items-center gap-3 py-3"><span className="w-9 shrink-0 font-mono text-sm text-secondary">#{row.rank}</span><span className="min-w-0 flex-1 break-words text-sm font-semibold">{row.handle}</span><span className="shrink-0 font-mono text-xs">{score(row)} {unit}</span></li>)}</ol>}
 return <div aria-live="polite">
  {error?<p role="alert" className="mt-4 text-sm text-wrong">Standings couldn’t load. <button className="min-h-11 font-semibold underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>:!board?<p role="status" className="mt-4 text-sm text-secondary">Loading standings…</p>:<>
   {board.league&&<p className="mt-4 text-sm font-semibold">{board.league.name}</p>}
   <p className="mt-2 text-xs text-secondary">{new Date(board.period_start).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} – {new Date(Date.parse(board.period_end)-1).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} · India time</p>
   {board.placement?<p className="mt-4 rounded-xl bg-canvas p-3 text-sm">{board.placement.public?'Your position:':'Your private placement: you’d be'} <strong>#{board.placement.rank}</strong> · {score(board.placement)} {unit}{!board.placement.public&&<span className="mt-1 block text-secondary">Your handle and score are hidden from everyone else.</span>}</p>:<p className="mt-4 text-sm text-secondary">Your placement appears after you record activity this week.</p>}
   <div className={'mt-5 grid gap-6 '+(board.nearby.some(row=>!board.top.some(top=>top.handle===row.handle))?'lg:grid-cols-2':'')}>
    <section className="order-2 min-w-0 lg:order-1"><h3 className="text-sm font-bold">Top 10</h3>{board.top.length?rows(board.top):<p className="mt-3 text-sm text-secondary">{empty}</p>}</section>
    {board.nearby.some(row=>!board.top.some(top=>top.handle===row.handle))&&<section className="order-1 min-w-0 lg:order-2"><h3 className="text-sm font-bold">Nearby ranks</h3>{rows(board.nearby)}</section>}
   </div>
   {board.neighborhood_truncated&&<p className="mt-2 text-xs text-secondary">Several learners share these ranks. Showing up to 25 nearby learners.</p>}
   <p className="mt-4 text-xs leading-relaxed text-secondary">Equal scores share a rank. Only learners who opted in appear publicly. Blocked accounts are excluded.</p>
  </>}
 </div>
}
