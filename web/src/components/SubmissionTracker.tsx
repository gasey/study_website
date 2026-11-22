import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {accountContext} from '../lib/accountContext'
import {reviewRequest,kindLabel} from '../lib/review'
import {TierFlair,type ContributorTier} from './ContributorStanding'

interface Submission {pipeline:'bank'|'material'|'collection';id:string;title:string;kind:string;state:string;revision:number;updated_at:string;published_revision:number|null;locked:boolean;queue_position:number|null;feedback:{note:string;revision:number|string;created_at:string}|null}
interface ReviewTime {pipeline:Submission['pipeline'];sample_count:number;median_seconds:number|null}
interface Tracker {items:Submission[];has_more:boolean;offset:number;as_of:string;queue_scope:string;review_times:ReviewTime[];standing:{display_tier:ContributorTier|null;tier:ContributorTier|null;can_create:boolean;privileges_restricted:boolean;mentor_eligible:boolean;post_limit:number;reply_limit:number;posts_remaining:number;replies_remaining:number}}
const B='inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold disabled:opacity-40'
const PIPELINES={bank:'Questions & corrections',material:'Materials',collection:'Learning collections'}
const STATES:Record<string,string>={draft:'Draft',submitted:'Submitted',in_review:'In review',changes_requested:'Returned for changes',published:'Published',accepted:'Approved · awaiting publication',publishing:'Publishing',publication_failed:'Publication failed',rejected:'Rejected',withdrawn:'Withdrawn',reverted:'Reverted',archived:'Archived'}
const EVENTS=['ism-auth-change','ism-community-change','ism-community-standing-change','ism-content-change']
const date=(value:string)=>new Date(value).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})+' IST'

export default function SubmissionTracker(){
 const generation=useRef(0),expired=useRef(false)
 const [data,setData]=useState<Tracker|null>(null),[error,setError]=useState(''),[guest,setGuest]=useState(false),[offset,setOffset]=useState(0),[version,setVersion]=useState(0)
 function refresh(){++generation.current;setData(null);setError('');setOffset(0);setVersion(n=>n+1)}
 useEffect(()=>{const update=()=>{expired.current=false;refresh()},expire=()=>{expired.current=true;++generation.current;setData(null);setError('');setGuest(true)};for(const name of EVENTS)window.addEventListener(name,update);window.addEventListener('ism-auth-expired',expire);return()=>{++generation.current;for(const name of EVENTS)window.removeEventListener(name,update);window.removeEventListener('ism-auth-expired',expire)}},[])
 useEffect(()=>{const run=++generation.current;setData(null);setError('');if(expired.current)return
  accountContext().then(async account=>{if(run!==generation.current)return;if(!account.authenticated){setGuest(true);return}setGuest(false);const result=await reviewRequest<Tracker>('/community/submissions?offset='+offset);if(run===generation.current)setData(result)}).catch(e=>{if(run===generation.current)setError(e.message)})
  return()=>{++generation.current}
 },[offset,version])
 function page(next:number){++generation.current;setData(null);setOffset(next)}
 return <section aria-label="My submissions" id="my-submissions" className="mt-7 min-w-0 scroll-mt-24 space-y-5 lg:scroll-mt-48">
  <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-display text-2xl">My submissions</h2><button className={B} onClick={refresh}>Refresh submissions</button></div>
  <p className="text-sm leading-relaxed text-secondary">Your questions, materials and learning collections, read from their existing review history. Open the same draft to revise and resubmit.</p>
  {guest?<div className="rounded-panel border border-hairline bg-card p-5"><p className="text-sm text-secondary">Sign in to see your submission history and current posting access.</p><Link className={B+' mt-3'} to="/login?next=%2Fcreate">Sign in to create</Link></div>:error?<p role="alert" className="rounded-panel border border-mypick bg-card p-5 text-sm">Could not load submissions: {error} <button onClick={refresh} className={B}>Retry submissions</button></p>:!data?<p role="status" className="text-sm text-secondary">Loading your submissions and posting access…</p>:<>
   <section aria-label="What you can submit today" className="rounded-panel border border-hairline bg-card p-5">
    <div className="flex flex-wrap items-center gap-3"><h3 className="font-display text-xl">What you can submit today</h3><TierFlair tier={data.standing.display_tier}/></div>
    <p className="mt-3 text-sm text-secondary">{data.standing.can_create?'Study notes and material shares are available.':'Study notes and material shares require account age, study activity or eligible Helper standing.'} {data.standing.posts_remaining} of {data.standing.post_limit} posts and {data.standing.replies_remaining} of {data.standing.reply_limit} replies remain today. Moderation and conversation access still apply.</p>
    {data.standing.privileges_restricted&&<p className="mt-2 text-sm text-attention-dark">Ladder privileges are paused while your account or posts need moderation.</p>}
    <p className="mt-3 text-sm text-secondary">Save a question proposal or structured material draft, add attributable sources and submit it for review. Every publication still needs the existing review process.</p>
    <p className="mt-2 text-sm">{data.standing.mentor_eligible?'Your current Mentor standing makes you eligible for a reviewer or editorial invitation.':'Mentor standing opens eligibility for reviewer or editorial invitations.'} Access is granted by invitation; a tier does not assign a role or approve a submission.</p>
    <Link to="/profile" className="mt-2 inline-flex min-h-11 items-center text-sm text-link">View your standing →</Link>
   </section>
   <section aria-label="Recent review times" className="rounded-panel border border-hairline bg-card p-5"><h3 className="font-display text-xl">Recent review times</h3><p className="mt-1 text-xs text-secondary">Observed independent decisions in the last 30 days. These medians are context, not a promised review date.</p><dl className="mt-3 grid gap-4 sm:grid-cols-3">{data.review_times.map(metric=><div key={metric.pipeline}><dt className="text-sm font-semibold">{PIPELINES[metric.pipeline]}</dt><dd className="mt-1 text-sm text-secondary">{metric.median_seconds===null?'No recent paired submission and review history.':`Median ${metric.median_seconds<86400?'less than a day':(metric.median_seconds/86400).toFixed(1)+' days'} · ${metric.sample_count} ${metric.sample_count===1?'decision':'decisions'}`}</dd></div>)}</dl></section>
   {!data.items.length?<p className="rounded-panel border border-hairline bg-card p-5 text-sm text-secondary">No submissions on this page. Your saved drafts and submissions will appear here.</p>:<div className="space-y-3">{data.items.map(item=><article key={item.pipeline+':'+item.id} className="min-w-0 rounded-panel border border-hairline bg-card p-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0"><p className="text-xs uppercase tracking-wide text-secondary">{PIPELINES[item.pipeline]} · {item.pipeline==='bank'?kindLabel(item.kind):item.kind==='test'?'Mock test':item.kind} · revision {item.revision}</p><h3 className="mt-2 break-words font-display text-xl">{item.title||'Untitled draft'}</h3></div><span className="rounded-pill bg-paper px-3 py-2 text-xs font-semibold">{STATES[item.state]||item.state.replace(/_/g,' ')}</span></div>
    <p className="mt-2 text-xs text-secondary">Updated {date(item.updated_at)}{item.published_revision&&['draft','submitted','in_review','changes_requested'].includes(item.state)?' · An approved version remains available while this revision is reviewed.':''}</p>
    {item.queue_position!==null&&<p className="mt-2 text-sm">Queue position {item.queue_position} · oldest submission first</p>}
    {item.feedback&&<div className="mt-3 rounded-[10px] border border-hairline bg-paper p-4"><p className="text-xs font-semibold">Latest return note · revision {item.feedback.revision}</p><p className="mt-2 whitespace-pre-wrap break-words text-sm">{item.feedback.note||'The reviewer recorded a return without a note.'}</p><p className="mt-2 text-xs text-secondary">{date(item.feedback.created_at)}</p></div>}
    {item.locked?<p className="mt-3 text-sm text-secondary">Check the linked question’s answer and finish active assessments before opening these details. Cup details stay locked until the Cup closes.</p>:<Link className="mt-3 inline-flex min-h-11 items-center text-sm font-semibold text-link" to={item.pipeline==='bank'?'/contributions/'+encodeURIComponent(item.id):item.pipeline==='material'?'/studio/'+encodeURIComponent(item.id):'/admin/bank?tab=learning&entry='+encodeURIComponent(item.id)}>Open {item.pipeline==='collection'?'learning workspace':'submission'} →</Link>}
   </article>)}</div>}
   <p className="text-xs text-secondary">Snapshot {date(data.as_of)}. {data.queue_scope}</p>
   <div className="flex flex-wrap gap-3"><button className={B} disabled={offset===0} onClick={()=>page(Math.max(0,offset-20))}>Previous submissions</button><button className={B} disabled={!data.has_more} onClick={()=>page(offset+20)}>Next submissions</button></div>
  </>}
 </section>
}
