import {useEffect,useState} from 'react'
import {reviewRequest,reviewSession,type BankSnapshot} from '../lib/review'
import type {AnswerDecisionReceipt} from './AdminAnswerDecision'
import QuestionCorrectionEditor from './QuestionCorrectionEditor'
import QuestionOrganizationContext from './QuestionOrganizationContext'

/** Exact-source correction without leaving the current filtered question inspector.
 *  Opens expanded, and reuses the inspector's snapshot when it carries the
 *  stale-source token, so the common case costs no extra round-trip (§VIII.5.2 #3).
 *  The server re-checks the token and the baseline digest on every save regardless. */
export default function InlineQuestionCorrection({question,appearance,preloaded,onNext,onDecision}:{question:string;appearance?:string;preloaded?:BankSnapshot;onNext?:()=>void;onDecision?:(receipt:AnswerDecisionReceipt)=>void}){
 const reusable=preloaded?.baseline_token?preloaded:null
 const [open,setOpen]=useState(true),[snapshot,setSnapshot]=useState<BankSnapshot|null>(reusable),[user,setUser]=useState(''),[mfa,setMfa]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;if(!open)return;const fresh=retry===0&&reusable
  // Without an explicit appearance the snapshot resolves the primary one, which is the
  // right target for a correction raised from the question's own page (§VIII.5.2 #11).
  // QuestionCorrectionEditor posts `record.id` either way, so the patch always binds to
  // whichever appearance the server actually returned.
  const load=fresh?reviewSession().then(u=>[reusable,u] as const)
   :Promise.all([reviewRequest<BankSnapshot>('/review/questions/'+encodeURIComponent(question)+(appearance?'?appearance_id='+encodeURIComponent(appearance):'')),reviewSession()])
  if(!fresh)setSnapshot(null)
  load.then(([s,u])=>{if(live){setSnapshot(s);setUser(u.user_id);setMfa(!!u.mfa_required);setError('')}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[question,appearance,open,retry])
 return <details open={open} className="mt-4 rounded-xl border border-hairline bg-paper p-3" onToggle={e=>setOpen(e.currentTarget.open)}><summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold">Edit tags, text, source or explanation</summary>{error&&<p role="alert" className="mt-2 text-sm text-mypick">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Retry editor</button></p>}{open&&!snapshot&&!error&&<p role="status">Opening the exact source…</p>}{open&&snapshot&&<fieldset disabled={mfa}><QuestionCorrectionEditor key={snapshot.record.id+snapshot.baseline_token} snapshot={snapshot} user={user} onNext={onNext} onQueued={receipt=>{if(receipt)onDecision?.(receipt)}}/><QuestionOrganizationContext key={'context-'+snapshot.baseline_token} snapshot={snapshot} canWrite={!!snapshot.can_publish&&!mfa}/></fieldset>}</details>
}
