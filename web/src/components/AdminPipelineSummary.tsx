import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
export const PAPER_STAGES=[['discovered','Discovered'],['acquired','Acquired'],['extracted','Extracted'],['review','In review'],['ready','Ready'],['published','Published']] as const
export default function AdminPipelineSummary(){
 const [counts,setCounts]=useState<{stage:string;count:number}[]|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;setError('');reviewRequest<{counts:{stage:string;count:number}[]}>('/admin/bank/intake?stage=all&offset=0').then(r=>{if(live)setCounts(r.counts)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[retry])
 return <section className="finna-card"><div className="finna-section-top"><h2>Paper pipeline</h2><Link to="/admin/bank?tab=intake">Open board</Link></div>{error?<p role="alert">{error} <button onClick={()=>setRetry(n=>n+1)}>Retry pipeline</button></p>:<div className="finna-pipeline-summary">{PAPER_STAGES.map(([stage,label])=><Link key={stage} to={'/admin/bank?tab=intake&stage='+stage} data-stage={stage}><strong>{counts?(counts.find(c=>c.stage===stage)?.count??0).toLocaleString('en-IN'):'—'}</strong><span>{label}</span></Link>)}</div>}</section>
}
