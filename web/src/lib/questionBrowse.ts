export type StudyStatus='all'|'unseen'|'ever_wrong'|'wrong'|'answered'
export type QuestionOrder='mixed'|'repeated'
export const studyStatusOptions=[['all','All questions'],['unseen','Never attempted'],['ever_wrong','Previously wrong'],['wrong','Last answer wrong'],['answered','Attempted']] as const
export function readStudyStatus(value:string|null):StudyStatus{return studyStatusOptions.some(([key])=>key===value)?value as StudyStatus:'all'}
export function readQuestionOrder(value:string|null):QuestionOrder{return value==='repeated'?'repeated':'mixed'}
export function newQuestionSeed(){return crypto.randomUUID()}
/** Personal queues shrink on checking, so forward navigation subtracts departures. */
export function nextBrowseOffset(offset:number,size:number,status:StudyStatus,results:({correct:boolean}|undefined)[]){
 const departed=results.filter(result=>result&&(status==='unseen'||status==='wrong'&&result.correct)).length
 return Math.max(0,offset+size-departed)
}
