import {useEffect,useRef,useState} from 'react'
import {accountGeneration} from '../lib/accountContext'
import {SUBMISSION_BODY_LIMIT,submissionBytes} from '../lib/submissionChecklist'

const LABELS=['I have named any sources or quotations and identified my own explanation.','I wrote this work or have permission to share it, with the required attribution.','I have reviewed the format, linked content and submission size.']
const B='inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold'
export function useSubmissionChecklist(binding:string,body:unknown,issues:string[]=[],disabled=false){
 binding=JSON.stringify([binding,body])
 const [version,setVersion]=useState(0),proof=useRef<{binding:string;epoch:number;checks:boolean[]}|null>(null),identity=useRef(accountGeneration()),valid=useRef(true),latest=useRef(binding)
 if(latest.current!==binding){proof.current=null;latest.current=binding}
 const bytes=submissionBytes(body),problems=[...issues,...bytes>SUBMISSION_BODY_LIMIT?['Reduce the draft to fit the 64 KiB submission limit.']:[]]
 useEffect(()=>{valid.current=identity.current===accountGeneration();const changed=()=>{valid.current=false;proof.current=null;setVersion(n=>n+1)};window.addEventListener('ism-auth-change',changed);window.addEventListener('ism-auth-expired',changed);return()=>{valid.current=false;proof.current=null;window.removeEventListener('ism-auth-change',changed);window.removeEventListener('ism-auth-expired',changed)}},[])
 function identityCurrent(){return valid.current&&identity.current===accountGeneration()}
 const confirmed=proof.current?.binding===binding&&proof.current.epoch===accountGeneration()?proof.current.checks:[false,false,false]
 function isReady(){return identityCurrent()&&!disabled&&!problems.length&&proof.current?.binding===binding&&proof.current.epoch===accountGeneration()&&proof.current.checks.every(Boolean)}
 function check(index:number,enabled:boolean){if(!identityCurrent()||disabled)return;const checks=[...confirmed];checks[index]=enabled;proof.current={binding,epoch:accountGeneration(),checks};setVersion(n=>n+1)}
 const notice=<section role="alert" className="mx-auto mt-8 max-w-xl rounded-panel border border-hairline bg-card p-5"><h1 className="font-display text-xl">Your account changed</h1><p className="mt-3 text-sm text-secondary">Reload this workspace before continuing with a draft or review action.</p><button className={B+' mt-3'} onClick={()=>window.location.reload()}>Reload workspace</button></section>
 return {ready:!!isReady(),isReady,identityCurrent,accountChanged:!identityCurrent(),notice,panel:<section aria-label="Before you submit" className="mt-5 min-w-0 rounded-panel border border-hairline bg-card p-5" data-checklist-version={version}>
  <h2 className="font-display text-xl">Before you submit</h2>
  <p className="mt-2 text-sm leading-relaxed text-secondary">Check the saved revision and its sources before review starts. Editing the draft or changing accounts clears these confirmations.</p>
  <p className="mt-2 text-xs text-secondary">Prepared draft: {(bytes/1024).toFixed(1)} KiB of 64 KiB. The server checks source eligibility and format again when you submit.</p>
  {disabled&&<p role="status" className="mt-3 text-sm text-secondary">Save the current draft and finish any pending save before completing this checklist.</p>}
  {problems.length>0&&<ul role="status" className="mt-3 list-disc space-y-1 pl-5 text-sm text-mypick">{problems.map((problem,i)=><li key={i}>{problem}</li>)}</ul>}
  <fieldset disabled={disabled||!identityCurrent()} className="mt-3 space-y-2 disabled:opacity-60">{LABELS.map((label,index)=><label key={label} className="flex min-h-11 items-start gap-3 py-2 text-sm leading-relaxed"><input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={confirmed[index]} onChange={e=>check(index,e.target.checked)}/><span>{label}</span></label>)}</fieldset>
 </section>}
}
