import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest,type ContributionDetail} from '../lib/review'
import type {AnswerDecisionReceipt} from './AdminAnswerDecision'
export default function AdminReviewProgress({receipt}:{receipt:AnswerDecisionReceipt}){
 const [state,setState]=useState(receipt.state),[error,setError]=useState(''),[retry,setRetry]=useState(0),[stopped,setStopped]=useState(false)
 useEffect(()=>{if(!receipt.contribution_id)return;let live=true,timer:number|undefined;const end=Date.now()+15*60*1000;setStopped(false)
  async function check(){if(!live)return;if(Date.now()>end){setStopped(true);return}if(document.visibilityState==='hidden'){timer=window.setTimeout(check,12000);return}
   try{const d=await reviewRequest<ContributionDetail>('/contributions/'+receipt.contribution_id);if(!live)return;const p=receipt.publication_id?d.publications.find(p=>p.id===receipt.publication_id):d.publications[d.publications.length-1];setState(p?.state||d.state);setError('');if(p&&['applied','failed','reverted'].includes(p.state))return;if(['publication_failed','reverted','withdrawn','rejected'].includes(d.state))return}
   catch(e){if(!live)return;setError((e as Error).message);setStopped(true);return}timer=window.setTimeout(check,12000)
  }void check();return()=>{live=false;window.clearTimeout(timer)}
 },[receipt.contribution_id,receipt.publication_id,retry])
 const applied=state==='applied',held=state==='held',failed=['failed','publication_failed'].includes(state)
 return <div className="rounded-[6px] border border-hairline bg-card p-3 text-[13px]" role="status"><strong>{receipt.label}</strong><p className="mt-1">{held?'Review hold is active; scored tests exclude this question.':applied?'Published · website and local bank updated.':failed?'Publication needs attention; this decision is not confirmed as live.':state==='reverted'?'Publication reverted.':'Saved · waiting for bank publication. You can review the next question.'}</p><div className="mt-1 flex flex-wrap items-center gap-3 text-[12px]"><span className="break-all font-mono text-[10px] text-muted">{receipt.questionId}</span>{receipt.contribution_id&&<Link to={'/contributions/'+receipt.contribution_id} className="inline-flex min-h-11 items-center text-link underline">Decision & publication details →</Link>}{(stopped||error||failed)&&<button onClick={()=>setRetry(n=>n+1)} className="min-h-11 text-link underline">Check status again</button>}</div>{error&&<p className="text-mypick">Status check: {error}</p>}{stopped&&!error&&<p className="text-secondary">Automatic checks paused. Check again for the latest publication status.</p>}</div>
}
