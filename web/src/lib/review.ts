import {ReadRequestCache} from './requestCache'
import {adminReadCanCoalesce} from './adminReviewFlow'
import {accountContext,accountGeneration,checkSessionRejected} from './accountContext'
import { deviceId } from './device'

export type ReviewKind = 'answer'|'transcription'|'explanation'|'taxonomy'|'source_reference'|'new_question'|'defect'|'duplicate'|'source_request'
export interface ReviewSession { mfa_required?:boolean;user_id:string; csrf:string; grants:{role:string;subject_id:string|null}[] }
export interface TaxonomyNode { id:string;label:string;parent_id:string|null;level:'subject'|'topic'|'subtopic';version:string }
export interface Evidence {module_item_id?:string|null;module_run_sha256?:string|null;kind:'paper'|'official-key'|'reference'|'reasoning';document_id?:string|null;sha256?:string|null;page?:number|null;url?:string|null;note:string;printed_question?:string|null;series?:string|null;answer_text?:string|null}
export interface BankRecord { relatedClassifications?:{subject_id:string;topic_id?:string|null;subtopic_id?:string|null}[]; id:string;paperId:string;type:string;question:string;options:(string|null)[];answerIndex:number|null;answerSource:string|null;answerKeyRef?:string|null;explanation:string|null;direction?:string|null;questionMarkup?:string|null;optionsMarkup?:(string|null)[]|null;passage?:string|null;difficulty?:string|null;page:number|null;qnum:string|null;hasDiagram?:boolean;figureImage?:string|null;classification:{subject_id:string;topic_id?:string|null;subtopic_id?:string|null} }
export interface BankSnapshot { solo_owner?:boolean;inspection_version?:string;tag_label?:string;canonical_id?:string;edit_hash?:string;can_publish?:boolean;reports?:{id:number;kind:string;note:string|null}[];baseline_token?:string;record:BankRecord;paper:{id:string;title:string|null;year:number|null;series:string|null;source_pdf_url:string|null};documents?:RegisteredDocument[] }
export interface RegisteredDocument {id:string;title:string;sha256:string;kind:string;key_status:string|null}
export interface Proposal {reverts_publication?:string|null;kind:ReviewKind;canonical_id:string|null;appearance_id:string|null;subject_id:string;title:string;patch:Record<string,unknown>;rationale:string;evidence:Evidence[]}
export interface Contribution { id:string;title:string;kind:ReviewKind;state:string;revision:number;lock_version:number;subject_id:string;canonical_id?:string|null;appearance_id?:string|null;created_at:string;updated_at:string;author?:string }
export interface ContributionDetail extends Contribution {admin_decision?:{batch_id?:string;mode:string;reason:string;created_at:string}|null;viewer_id:string;required_reviews:number;author_id:string;is_author:boolean;permissions:string[];current:{payload:Proposal;baseline:BankSnapshot|Record<string,never>;baseline_hash:string};decisions:{id:number;reviewer_id:string;decision:string;rationale:string;revision:number;created_at:string}[];events:{id:number;action:string;actor_id:string;detail:Record<string,unknown>;created_at:string}[];appeals:{id:number;state:string;reason:string}[];publications:{id:string;state:string;error:string|null}[]}
export interface ReviewPage {items:Contribution[];next_cursor:string|null}
const pendingReads=new ReadRequestCache(32)
let current:Promise<ReviewSession>|null=null
export function reviewSession(force=false):Promise<ReviewSession> { if(force)current=null;return current??(current=reviewRequest<ReviewSession>('/review/session')) }
window.addEventListener('ism-auth-change',()=>{current=null;pendingReads.clear()})
window.addEventListener('ism-content-change',()=>pendingReads.clear())
export async function reviewRequest<T>(path:string,body?:unknown,key?:string,sourceVersion?:string):Promise<T> {
 const epoch=accountGeneration()
 if(body!==undefined)pendingReads.clear()
 const load=async()=>{
 const identity=await accountContext()
 const headers:Record<string,string>={'content-type':'application/json','x-device-id':deviceId()}
 if(sourceVersion)headers['x-review-source-version']=sourceVersion
 if(body!==undefined) { headers['x-review-csrf']=(await reviewSession()).csrf;if(key)headers['idempotency-key']=key }
 const controller=body===undefined?new AbortController():null
 const timer=controller?setTimeout(()=>controller.abort(),15000):undefined
 let response:Response
 try{response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'include',headers,...(controller?{signal:controller.signal}:{}),...(body===undefined?{}:{body:JSON.stringify(body)})})}finally{if(timer!==undefined)clearTimeout(timer)}
 if(!response.ok) {
  let message=response.statusText
  try {const err=await response.json();message=Array.isArray(err.detail)?err.detail.map((e:{msg:string})=>e.msg).join('; '):err.detail||err.message||message}catch{/* fallback */}
  if(response.status===401){current=null;await checkSessionRejected(identity)}
  throw new Error(message)
 }
 const data=await response.json() as T
 if(epoch!==accountGeneration())throw new Error('Your account changed. Please reload.')
 return data
 }
 return body===undefined&&adminReadCanCoalesce(path)?pendingReads.read(epoch+':'+path,load):load()
}
export const kindLabel=(kind:string)=>({answer:'Answer correction',transcription:'Text, options & figures',explanation:'Explanation',taxonomy:'Subject & topic tags',source_reference:'Source locator',new_question:'New MCQ',defect:'Question defect',duplicate:'Duplicate report',source_request:'Request a paper'}[kind]||kind)
export const stateLabel=(state:string)=>state.replace(/_/g,' ')
