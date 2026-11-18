import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'

export type AuditEvent={id:string|number;action:unknown;actor_id:unknown;created_at:unknown;detail:unknown}
const FILTERS=['All','Answers','Tags','Papers','Access','Other']
function category(action:string){if(/answer|explanation|scoring|hold/.test(action))return 'Answers';if(/tag|taxonomy|classif/.test(action))return 'Tags';if(/paper|source|publish|intake|document/.test(action))return 'Papers';if(/grant|revoke|permission|mfa|account/.test(action))return 'Access';return 'Other'}
const date=(value:unknown)=>new Date(String(value)).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})
export function AuditEvents({rows,compact=false}:{rows:AuditEvent[];compact?:boolean}){
 return <div className={'finna-audit-events'+(compact?' is-compact':'')}>{rows.map(row=>{const action=String(row.action),kind=category(action),detail=row.detail&&typeof row.detail==='object'?row.detail as Record<string,unknown>:null;return <article key={row.id} className="finna-audit-event" data-kind={kind}>
  <time dateTime={String(row.created_at)}>{date(row.created_at)}</time><span className="finna-audit-dot" aria-hidden="true"/>
  <div><div className="finna-audit-person"><strong>{String(row.actor_id||'Actor not recorded')}</strong><span>{kind}</span></div><p>{action.replace(/[_.-]+/g,' ')}</p>{typeof detail?.reason==='string'&&<p className="finna-audit-reason">{detail.reason}</p>}
   {!compact&&<details><summary>Event details</summary><pre>{JSON.stringify(row.detail,null,2)}</pre></details>}
  </div></article>})}{!rows.length&&<p className="finna-empty">No recorded events match this view.</p>}</div>
}
export default function AdminAuditTimeline({rows,onMore}:{rows:AuditEvent[];onMore?:()=>void}){
 const [filter,setFilter]=useState('All'),[query,setQuery]=useState('')
 const visible=rows.filter(row=>(filter==='All'||category(String(row.action))===filter)&&JSON.stringify(row).toLowerCase().includes(query.toLowerCase()))
 return <section className="finna-audit" aria-label="Admin audit history"><div className="finna-audit-toolbar"><nav className="finna-segments" aria-label="Audit event types">{FILTERS.map(label=><button key={label} aria-pressed={filter===label} onClick={()=>setFilter(label)}>{label}</button>)}</nav><input aria-label="Search loaded audit events" type="search" placeholder="Find an action, actor or reason" value={query} onChange={e=>setQuery(e.target.value)}/></div><p className="finna-audit-scope">Filters search the loaded events. Load older events to extend this view.</p><div className="finna-card"><AuditEvents rows={visible}/></div>{onMore&&<button className="finna-btn finna-btn-quiet" onClick={onMore}>Load older events</button>}</section>
}
export function AdminRecentActivity({owner}:{owner:boolean}){
 const [rows,setRows]=useState<AuditEvent[]|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;setRows(null);setError('');const request=owner?reviewRequest<AuditEvent[]>('/admin/bank/audit').then(r=>r.slice(0,6)):reviewRequest<{items:{id:string;state:string;publisher:string|null;author:string|null;created_at:string;title:string}[]}>('/admin/bank/publication-history?mine=true&limit=6').then(r=>r.items.map(e=>({id:e.id,action:e.state+' · '+e.title,actor_id:e.publisher||e.author,created_at:e.created_at,detail:null})));request.then(r=>{if(live)setRows(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[owner,retry])
 return <section className="finna-card finna-admin-recent"><div className="finna-section-top"><h2>Recent activity</h2><Link to={'/admin/bank?tab='+(owner?'audit':'publications')}>{owner?'Audit history':'Publication history'}</Link></div>{error?<p role="alert">{error} <button onClick={()=>setRetry(n=>n+1)}>Retry activity</button></p>:rows?<AuditEvents rows={rows} compact/>:<p role="status" className="finna-empty">Loading recorded activity…</p>}</section>
}
