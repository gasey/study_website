import BankOverview,{type Overview} from './BankOverview'
import {Link} from 'react-router-dom'
import {canOpenAdminTab,adminTabHref,type AdminGrant} from '../lib/adminNavigation'
import {AdminRecentActivity} from './AdminAuditTimeline'
import AdminPipelineSummary from './AdminPipelineSummary'
import AdminReviewAttention from './AdminReviewAttention'
export interface AdminHealth{overview?:Overview|null;assessments?:{pending:number;failed:number};assessment_worker?:{seen_at:string;status:string;available:boolean}|null;worker?:{seen_at:string;status:string;available:boolean}|null;questions:number;missing_answers:number;keyed:number;defects:number;held:number;queue:{state:string;count:number}[];sync:{bank_checksum:string;finished_at:string}|null}
const n=(value:number)=>value.toLocaleString('en-IN')
export default function AdminHome({health,grants,busy,onRetry,onRefresh}:{health:AdminHealth;grants:AdminGrant[];busy:boolean;onRetry:()=>void;onRefresh?:()=>void}){
 const owner=grants.some(g=>g.role==='owner'),inventory=canOpenAdminTab('intake',grants)
 return <div className="finna-admin-overview">
  <div className="finna-admin-overview-main"><AdminReviewAttention health={health} grants={grants} onRefresh={onRefresh}/>
   {inventory&&<AdminPipelineSummary/>}
   <section className="finna-admin-totals" aria-label="Bank totals">{[[health.questions,'Questions'],[health.overview?.papers??null,'Source papers'],[health.keyed,'Official / transcribed keys'],[health.overview?.published_corrections??null,'Published corrections']].map(([value,label])=><div key={String(label)}><strong>{typeof value==='number'?n(value):'—'}</strong><span>{label}</span></div>)}</section>
   <section className="finna-card"><div className="finna-section-top"><h2>Continue reviewing</h2><Link to="/editorial">Review workspace →</Link></div><nav aria-label="Admin tasks" className="finna-admin-tools">{[['questions','Review answers'],['retag','Fix learning tags'],['exams','Manage papers & exams'],['organization','Modules & schemes'],[owner?'workflow':'review','Review submitted work'],['publications','Publication history']].filter(([tab])=>canOpenAdminTab(tab,grants)).map(([tab,label])=><Link key={tab} to={adminTabHref(tab)}>{label}<span>→</span></Link>)}</nav></section>
   {owner&&!!health.assessments?.failed&&<section className="finna-card finna-admin-warning" role="status"><p>{n(health.assessments.failed)} score reassessment jobs need investigation.</p><button disabled={busy} onClick={onRetry}>Review and retry stalled jobs</button></section>}
  </div>
  <AdminRecentActivity owner={owner}/>
  <details className="finna-admin-coverage"><summary>Detailed coverage, exam table & system status</summary>{health.overview?<BankOverview data={health.overview} health={health} grants={grants} busy={busy} onRetry={onRetry}/>:<div className="finna-card"><p>Publication worker: {health.worker?.available?health.worker.status:'not seen recently'}</p>{health.sync&&<p>Last completed bank sync: {new Date(health.sync.finished_at).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})}</p>}<Link to="/editorial">Open paper review →</Link></div>}</details>
 </div>
}
