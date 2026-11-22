import type {AnswerSource} from './api'
export interface AnswerContext {
  reviewed?:boolean
  disputed?:boolean
  defect?:string|null
  questionType?:string
  statusOverride?:string
  keyStatus?:string|null
  hasConflict?:boolean
}
export type LearnerAnswerLabel = null | 'Not verified' | 'Answer disputed' | 'Written question'

/** Display policy only. Never grants publication approval or scoring eligibility.
 *  Part VII (§VII.6, §VII.6.2):
 *  - Staff retain the full five-state `status` taxonomy.
 *  - Learners see no badge on trusted answers, an always-visible amber line
 *    ("Not verified") on unverified/unsolved/provisional keys, an always-visible
 *    dispute line ("Answer disputed") when official key and reviewed working
 *    disagree or `key_disputed` is set, and a plain "Written question" line for
 *    descriptive prompts. */
export function answerStatus(source:AnswerSource,{reviewed=false,disputed=false,defect=null,questionType='mcq',statusOverride,keyStatus=null,hasConflict=false}:AnswerContext={}){
 const sourceDetail=source==='official'?'Official answer key':source==='key'?'Official answer key':source==='derived'?'Worked solution':source==='inferred'?'Answer awaiting review':'No recorded answer'
 if(questionType==='descriptive')return {status:'written',label:'Written question',learnerLabel:'Written question' as LearnerAnswerLabel,sourceDetail,description:'Write your response using the instructions in the original paper.',scoring:'Written answers are self-checked against your own draft.',trusted:false}
 if(disputed||hasConflict)return {status:'needs-review',label:'Answer disputed',learnerLabel:'Answer disputed' as LearnerAnswerLabel,sourceDetail,description:'The official key and reviewed working disagree, or the key is disputed. Check both sources below.',scoring:'Check both sources below while this question is under review.',trusted:false}
 if(keyStatus==='provisional'&&(source==='official'||source==='key'))return {status:'needs-review',label:'Not verified',learnerLabel:'Not verified' as LearnerAnswerLabel,sourceDetail:'Provisional official key',description:'A provisional key may change when the final key is published.',scoring:'Provisional key — final key awaited.',trusted:false}
 if(statusOverride==='needs-review'||['duplicate-options','unresolved-source'].includes(defect||''))return {status:'needs-review',label:'Needs review',learnerLabel:'Not verified' as LearnerAnswerLabel,sourceDetail,description:'This question or its answer needs checking.',scoring:'This question is being checked against the original paper.',trusted:false}
 if(statusOverride==='unsolved')source='none'
 if(source==='official'||source==='key')return {status:'official',label:'Official key',learnerLabel:null as LearnerAnswerLabel,sourceDetail,description:source==='key'?'This answer was copied from the examination authority’s key.':'This answer comes from the examination authority’s key.',scoring:'Answer from the examination authority’s key.',trusted:true}
 if(source==='derived'&&reviewed)return {status:'verified',label:'Verified answer',learnerLabel:null as LearnerAnswerLabel,sourceDetail,description:'This answer has been reviewed against the original paper.',scoring:'Reviewed worked solution.',trusted:true}
 if(source==='derived'||source==='inferred')return {status:'needs-review',label:'Needs review',learnerLabel:'Not verified' as LearnerAnswerLabel,sourceDetail,description:source==='derived'?'A worked answer is available but has not yet been verified.':'A suggested answer is available and is awaiting review.',scoring:'Awaiting verification.',trusted:false}
 return {status:'unsolved',label:'No answer yet',learnerLabel:'Not verified' as LearnerAnswerLabel,sourceDetail,description:'An answer is not available here yet.',scoring:'Read the original paper or suggest a solution with a reliable source.',trusted:false}
}

/** Theme-token provenance styles (replaces hardcoded hex palette so night mode works cleanly). */
export function answerStatusAppearance(status:string){
 if(status==='official')return {badge:'border-correct bg-correct-soft text-correct-dark',accent:'border-correct',symbol:'▣',shortLabel:'Official key',meaning:'Answer from the exam authority'}
 if(status==='verified')return {badge:'border-practice bg-practice-soft text-practice-dark',accent:'border-practice',symbol:'✓',shortLabel:'Verified answer',meaning:'Reviewed answer with a worked solution'}
 if(status==='disputed')return {badge:'border-wrong bg-wrong-soft text-wrong-dark',accent:'border-wrong',symbol:'!',shortLabel:'Answer disputed',meaning:'Official key and reviewed working disagree'}
 if(status==='needs-review')return {badge:'border-exams bg-exams-soft text-exams-dark',accent:'border-exams',symbol:'?',shortLabel:'Not verified',meaning:'Awaiting verification'}
 return {badge:'border-hairline2 bg-canvas text-secondary',accent:'border-hairline2',symbol:'—',shortLabel:status==='written'?'Written question':'Not verified',meaning:status==='written'?'Requires a written response':'No recorded answer'}
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
