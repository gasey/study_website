import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewSession} from '../lib/review'
import {useExamScope} from '../lib/examScope'
import {learningRequest,type ResumePage,type RevisionOverview} from '../lib/learning'
export default function LearningOverview(){
 const epoch=useRef(0)
 const scope=useExamScope(),[data,setData]=useState<ResumePage|null>(null),[revision,setRevision]=useState<RevisionOverview|null>(null),[error,setError]=useState(''),[guest,setGuest]=useState(false),[refresh,setRefresh]=useState(0)
 useEffect(()=>{let live=true;const run=++epoch.current;setData(null);setRevision(null);setError('');setGuest(false)
  reviewSession().then(async s=>{const [resume,daily]=await Promise.all([learningRequest<ResumePage>('/resume?exam_scope='+scope,s.user_id),learningRequest<RevisionOverview>('/revision?exam_scope='+scope,s.user_id)]);if(live&&run===epoch.current){setData(resume);setRevision(daily)}}).catch(e=>{if(live&&run===epoch.current){if(/sign in|session|expired/i.test(e.message))setGuest(true);else setError(e.message)}})
  const auth=()=>{++epoch.current;setData(null);setRevision(null);setRefresh(n=>n+1)};window.addEventListener('ism-auth-change',auth)
  return()=>{live=false;window.removeEventListener('ism-auth-change',auth)}
 },[scope,refresh])
 if(guest)return <section className="mt-6 rounded-panel border border-hairline bg-card p-5 text-[14px]"><Link to="/login" className="font-semibold text-link underline">Sign in</Link> to continue studying across devices and build a daily revision session.</section>
 return <section aria-label="Continue studying and daily revision" className="mt-6 rounded-panel border border-hairline bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-display text-[26px]">Pick up where you left off</h2><button onClick={()=>setRefresh(n=>n+1)} className="min-h-11 text-[12px] text-link underline">Refresh</button></div>
 {error?<p role="alert" className="text-mypick">{error}</p>:!data?<p role="status" className="mt-3 text-[14px] text-muted">Loading your saved activities…</p>:<>
 <div className="mt-3 grid gap-3 sm:grid-cols-2">{data.items.map(item=><Link key={item.kind} to={item.url} className="rounded-[9px] border border-hairline bg-paper p-4"><div className="font-mono text-[10px] uppercase text-muted">{item.kind}</div><h3 className="mt-1 text-[14px] font-semibold text-link">{item.title} →</h3><p className="mt-2 line-clamp-2 text-[13px] text-secondary">{item.detail}</p></Link>)}</div>
 {!data.items.length&&<p className="mt-3 text-[14px] text-secondary">Your unfinished mock, practice position, vocabulary card and desk tasks will appear here.</p>}
 {revision&&<div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4"><p className="text-[13px] text-secondary"><strong>{revision.available}</strong> available for revision · {revision.mistakes} mistakes · {revision.saved} saved · {revision.vocabulary} vocabulary due. Overlapping questions count once.</p><Link to={'/revision?exam_scope='+scope} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-5 text-[13px] font-semibold text-paper">Daily revision →</Link></div>}
 </>}
 </section>
}
