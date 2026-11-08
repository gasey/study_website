import type {AnswerSource} from './api'
export interface AnswerContext {reviewed?:boolean;disputed?:boolean;defect?:string|null;questionType?:string;statusOverride?:string}
/** Display policy only. Never grants publication approval or scoring eligibility. */
export function answerStatus(source:AnswerSource,{reviewed=false,disputed=false,defect=null,questionType='mcq',statusOverride}:AnswerContext={}){
 const sourceDetail=source==='official'?'Official answer key':source==='key'?'Official answer key':source==='derived'?'Worked solution':source==='inferred'?'Answer awaiting review':'No recorded answer'
 if(questionType==='descriptive')return {status:'written',label:'Written question',sourceDetail,description:'Write your response using the instructions in the original paper.',scoring:'Written answers are not automatically scored.',trusted:false}
 if(statusOverride==='needs-review'||disputed||['duplicate-options','unresolved-source'].includes(defect||''))return {status:'needs-review',label:'Needs review',sourceDetail,description:disputed?'The answer is disputed. Check the original key and available explanation.':'This question or its answer needs checking.',scoring:'Questions with unresolved issues are excluded from scored tests.',trusted:false}
 if(statusOverride==='unsolved')source='none'
 if(source==='official'||source==='key')return {status:'official',label:'Official key',sourceDetail,description:source==='key'?'This answer was copied from the examination authority’s key.':'This answer comes from the examination authority’s key.',scoring:'Used for official-key tests when eligible. A provisional key may change when the final key is published.',trusted:true}
 if(source==='derived'&&reviewed)return {status:'verified',label:'Verified answer',sourceDetail,description:'This answer has been reviewed. Official test scores continue to use the examination authority’s answer key.',scoring:'May be used for practice estimates, but not official-key test scores.',trusted:true}
 if(source==='derived'||source==='inferred')return {status:'needs-review',label:'Needs review',sourceDetail,description:source==='derived'?'A worked answer is available but has not yet been verified.':'A suggested answer is available and is awaiting review.',scoring:'Not used in scored tests until verified.',trusted:false}
 return {status:'unsolved',label:'No answer yet',sourceDetail,description:'An answer is not available here yet.',scoring:'Read the original paper or suggest a solution with a reliable source.',trusted:false}
}

/** Provenance colours are independent of correct/wrong answer colours. */
export function answerStatusAppearance(status:string){
 if(status==='official')return {badge:'border-[#8CB89A] bg-[#E7F3EA] text-[#214E34]',accent:'border-[#8CB89A]',symbol:'▣',shortLabel:'Official key',meaning:'Answer from the exam authority'}
 if(status==='verified')return {badge:'border-[#8DAED7] bg-[#EAF1FC] text-[#204F86]',accent:'border-[#8DAED7]',symbol:'✓',shortLabel:'Verified answer',meaning:'Reviewed answer with a worked solution'}
 if(status==='needs-review')return {badge:'border-[#D9B76B] bg-[#FFF4D9] text-[#705015]',accent:'border-[#D9B76B]',symbol:'?',shortLabel:'Needs review',meaning:'Not yet verified for scored mocks'}
 return {badge:'border-[#C9C4BA] bg-[#F1EFEA] text-[#514C43]',accent:'border-[#C9C4BA]',symbol:'—',shortLabel:status==='written'?'Written question':'No answer yet',meaning:status==='written'?'Requires a written response':'No recorded answer'}
}

/** Explanation availability is independent of key provenance. No review is
 * inferred merely from a nonempty explanation or an official answer badge. */
export function explanationPresentation(explanation:string|null|undefined,source:AnswerSource,context:AnswerContext={}) {
 const available=!!explanation?.trim()
 if(!available)return {status:'missing',label:'Explanation not yet available',detail:'You can check the original paper or suggest an explanation.'}
 const answer=answerStatus(source,context)
 if(answer.status==='verified')return {status:'reviewed-solution',label:'Explanation',detail:'Reasoning for the reviewed answer.'}
 if(answer.status==='official')return {status:'available',label:'Explanation available',detail:'The answer comes from an official key. This explanation has not been separately verified.'}
 return {status:'needs-review',label:'Explanation awaiting review',detail:'This explanation has not yet been verified. Check its reasoning against a reliable source.'}
}

/** Learner wording follows actual source/review status, never storage terminology. */
export function answerFeedbackLabel(answer:{correct:boolean;answer_source:AnswerSource},context:AnswerContext={}) {
 const state=answerStatus(answer.answer_source,context)
 return state.trusted?(answer.correct?'Correct':'Incorrect'):['official','key'].includes(answer.answer_source)?'Answer under review':'Suggested answer'
}

/** Omit only the legacy trailing process certificate from learner reasoning.
 * Never rewrites stored content or strips substantive warnings/model subject matter. */
export function learnerExplanation(text:string|null|undefined):string {
 return (text||'').replace(/\s*Original printed source and ordered choices independently reviewed\.\s+Verified worked solution, unofficial; no matching examiner key is asserted\.\s*$/, '')
}
