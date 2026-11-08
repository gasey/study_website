import {useEffect,useState} from 'react'
import {reviewRequest,reviewSession,type BankSnapshot} from '../lib/review'
import type {AnswerDecisionReceipt} from './AdminAnswerDecision'
import QuestionCorrectionEditor from './QuestionCorrectionEditor'
import QuestionOrganizationContext from './QuestionOrganizationContext'

/** Exact-source correction without leaving the current filtered question inspector. */
export default function InlineQuestionCorrection({question,appearance,onNext,onDecision}:{question:string;appearance:string;onNext?:()=>void;onDecision?:(receipt:AnswerDecisionReceipt)=>void}){
 const [open,setOpen]=useState(false),[snapshot,setSnapshot]=useState<BankSnapshot|null>(null),[user,setUser]=useState(''),[mfa,setMfa]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;setSnapshot(null);if(open)Promise.all([reviewRequest<BankSnapshot>('/review/questions/'+encodeURIComponent(question)+'?appearance_id='+encodeURIComponent(appearance)),reviewSession()]).then(([s,u])=>{if(live){setSnapshot(s);setUser(u.user_id);setMfa(!!u.mfa_required);setError('')}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[question,appearance,open,retry])
 return <details className="mt-4 rounded-xl border border-hairline bg-paper p-3" onToggle={e=>setOpen(e.currentTarget.open)}><summary className="min-h-11 cursor-pointer py-2 text-[14px] font-semibold">Edit tags, text, source or explanation</summary>{error&&<p role="alert" className="mt-2 text-[13px] text-mypick">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Retry editor</button></p>}{open&&!snapshot&&!error&&<p role="status">Opening the exact source…</p>}{open&&snapshot&&<fieldset disabled={mfa}><QuestionCorrectionEditor key={snapshot.record.id+snapshot.baseline_token} snapshot={snapshot} user={user} onNext={onNext} onQueued={receipt=>{if(receipt)onDecision?.(receipt)}}/><QuestionOrganizationContext key={'context-'+snapshot.baseline_token} snapshot={snapshot} canWrite={!!snapshot.can_publish&&!mfa}/></fieldset>}</details>
}
