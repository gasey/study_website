import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
import {canOpenAdminTab,type AdminGrant} from '../lib/adminNavigation'
import type {AdminHealth} from './AdminHome'

type Quality={total:number;needs_review:number;missing:number;held:number}
type Tasks={task_counts:Record<string,number>}
const questions=(filters:Record<string,string>)=>'/admin/bank?'+new URLSearchParams({tab:'questions',...filters})

export default function AdminReviewAttention({health,grants,onRefresh}:{health:AdminHealth;grants:AdminGrant[];onRefresh?:()=>void}){
 const [counts,setCounts]=useState<{quality:Quality;tasks:Tasks}|null>(null)
 const [error,setError]=useState(''),[refresh,setRefresh]=useState(0)
 const scope=JSON.stringify(grants.map(g=>[g.role,g.subject_id]))
 useEffect(()=>{let live=true;setCounts(null);setError('')
  // Use the same scoped answer-status view and current task lanes as Questions.
  // Contribution history includes superseded failures, so it is not a task count.
  Promise.all([
   reviewRequest<Quality>('/admin/bank/quality'),
   reviewRequest<Tasks>('/admin/bank/questions?issue=all&review_task=all&limit=1'),
  ]).then(([quality,tasks])=>{if(live)setCounts({quality,tasks})}).catch(e=>{if(live)setError(e.message)});
  return()=>{live=false}
 },[scope,health,refresh])
 useEffect(()=>{const reload=()=>setRefresh(n=>n+1);window.addEventListener('focus',reload);window.addEventListener('ism-content-change',reload);return()=>{window.removeEventListener('focus',reload);window.removeEventListener('ism-content-change',reload)}},[])
 const q=counts?.quality,t=counts?.tasks.task_counts
 const rows=[
  {count:q?.needs_review,label:'Answers needing review',note:'An answer is recorded but not yet confirmed.',to:questions({answer_status:'needs-review'}),action:'Review'},
  {count:q?.missing,label:'MCQ answers missing',note:'No answer is recorded. Inspect the original question and key.',to:questions({issue:'missing'}),action:'Review'},
  {count:t?(t.source||0):undefined,label:'Source / scoring problems',note:'Current source-check lane, after pending and failed publications.',to:questions({review_task:'source'}),action:'Inspect'},
  {count:q?.held,label:'Held from scoring',note:'Resolve the recorded issue before releasing a hold.',to:questions({issue:'held'}),action:'Open'},
  {count:t?(t.publishing||0):undefined,label:'Questions awaiting publication',note:'Current accepted or publishing correction for each question.',to:questions({review_task:'publishing'}),action:'Open'},
  {count:t?(t.failed||0):undefined,label:'Questions with failed publications',note:'Current failed task per question; superseded failures are excluded.',to:questions({review_task:'failed'}),action:'Inspect'},
  {count:health.queue.filter(x=>x.state==='submitted').reduce((sum,x)=>sum+x.count,0),label:'Submitted corrections',note:'Submitted correction records in your review scope.',to:'/admin/bank?tab=review&state=submitted',action:'Review'},
 ].filter(row=>canOpenAdminTab(new URLSearchParams(row.to.split('?')[1]).get('tab')||'',grants))
 return <section className="finna-card finna-attention" aria-label="Current review needs" aria-busy={!counts&&!error}>
  <div className="finna-section-top"><h2>Needs attention</h2><button type="button" className="finna-attention-refresh" onClick={()=>onRefresh?onRefresh():setRefresh(n=>n+1)}>Refresh counts</button></div>
  {error?<p role="alert" className="finna-admin-note">Review counts could not load: {error}. Use Refresh counts to retry.</p>:!counts?<p role="status" className="finna-admin-note">Counting current review needs…</p>:<p className="finna-admin-note">{counts.quality.total.toLocaleString('en-IN')} distinct questions in your permitted scope.</p>}
  {rows.map(row=><div key={row.label} className="finna-attention-row"><strong>{typeof row.count==='number'?row.count.toLocaleString('en-IN'):'—'}</strong><div><h3>{row.label}</h3><p>{row.note}</p></div><Link className="finna-btn finna-btn-ink" to={row.to}>{row.action}</Link></div>)}
  <p className="finna-admin-note">Answer status, holds and task groups overlap; do not add them as a remaining-work total. Counts follow the linked question filters. Tag reviews and explanations do not confirm an answer.</p>
 </section>
}
