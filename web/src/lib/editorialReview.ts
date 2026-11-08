export type CheckOutcome='checked'|'needs_correction'|'cannot_verify'
export type ReviewFilter='all'|'unreviewed'|'flagged'|'recheck'
export type EditorialQuestion={appearance_id:string;canonical_id:string;qnum:string|null;page:number|null;question:string;answer_status:string;type:string;previous_check:{outcome:string;created_at:string;stale?:boolean}|null}
export const CHECKS=[
 ['source_checked','Question & context','Compare wording, passage and numbering with the original paper.'],
 ['options_checked','Options & figures','Check every option, diagram or written subquestion.'],
 ['answer_checked','Answer & evidence','Check against the key or a reliable supporting reference.'],
 ['explanation_checked','Explanation','Check the reasoning or written marking guidance.'],
] as const
export const EMPTY_FLAGS={source_checked:false,options_checked:false,answer_checked:false,explanation_checked:false}
export type CheckDraft={reason?:string;flags:typeof EMPTY_FLAGS;note:string;outcome:CheckOutcome;edited:boolean}
export function blankDraft():CheckDraft{return {flags:{...EMPTY_FLAGS},note:'',outcome:'checked',edited:false}}
export function outcomeLabel(outcome:string){return outcome==='checked'?'Checked':outcome==='needs_correction'?'Needs correction':outcome==='cannot_verify'?'Cannot verify':'No recorded check'}
export function matchesReview(q:EditorialQuestion,filter:ReviewFilter){return filter==='all'||filter==='unreviewed'&&!q.previous_check||filter==='recheck'&&!!q.previous_check?.stale||filter==='flagged'&&!!q.previous_check&&!q.previous_check.stale&&q.previous_check.outcome!=='checked'}
export function canSaveCheck(draft:CheckDraft){return draft.note.trim().length>=10&&draft.note.length<=4000&&(draft.outcome!=='checked'||Object.values(draft.flags).every(Boolean))}
export function draftKey(user:string,assignment:string,appearance:string,version:string){return 'ism.editorial-draft:'+JSON.stringify([user,assignment,appearance,version])}
export function parseDraft(raw:string|null,now=Date.now()):CheckDraft|null{
 try{if(!raw)return null;const d=JSON.parse(raw);if(!Number.isFinite(d.updatedAt)||now-d.updatedAt>86400000||d.updatedAt>now+60000||!['checked','needs_correction','cannot_verify'].includes(d.outcome)||typeof d.note!=='string'||d.note.length>4000||!d.flags||CHECKS.some(([key])=>typeof d.flags[key]!=='boolean'))return null;
 return {reason:typeof d.reason==='string'?d.reason:undefined,flags:Object.fromEntries(CHECKS.map(([key])=>[key,d.flags[key]])) as typeof EMPTY_FLAGS,note:d.note,outcome:d.outcome,edited:true}
 }catch{return null}
}
export function adjacentQuestion(index:number,delta:-1|1,offset:number,length:number,total:number,pageSize=25):{index:number;offset:number}|null{
 if(index<0)return null;const absolute=offset+index+delta;if(absolute<0||absolute>=total)return null;
 if(index+delta>=0&&index+delta<length)return {index:index+delta,offset};
 const nextOffset=delta===1?offset+pageSize:Math.max(0,offset-pageSize);return {offset:nextOffset,index:delta===1?0:Math.min(pageSize-1,total-nextOffset-1)}
}
