import type {PaperQuestion} from './api'

export function sourcePageUrl(url:string,page:number|null){
 return url.split('#')[0]+(page&&Number.isInteger(page)&&page>0?'#page='+page:'')
}
export function printedQuestionLabel(q:Pick<PaperQuestion,'qnum'>,index:number){
 return q.qnum?'Q'+q.qnum:'Item '+(index+1)
}
export function matchesPaperSearch(q:PaperQuestion,search:string){
 const needle=search.trim().toLocaleLowerCase()
 if(!needle)return true
 const number=/^(?:q(?:uestion)?\s*|#)(\d+[a-z]?(?:\([a-z0-9]+\))?)$/i.exec(needle)
 if(number)return q.qnum?.trim().toLocaleLowerCase()===number[1].toLocaleLowerCase()
 return [q.qnum,q.question,q.direction,q.passage,...q.options].some(text=>text?.toLocaleLowerCase().includes(needle))
}
/** Fetch this paper only, in bounded batches; publish progress without waiting for every page. */
export async function loadPaperWorkspace<T>(read:(offset:number)=>Promise<{items:T[];total:number;practice_count:number}>,publish:(items:T[],total:number,practice:number)=>void,active:()=>boolean,batchSize=100){
 const all:T[]=[]
 while(active()){
  const page=await read(all.length)
  if(!active())return
  all.push(...page.items)
  const complete=page.items.length<batchSize
  publish([...all],complete?all.length:Math.max(page.total,all.length),page.practice_count)
  if(complete)return
 }
}

/** Exam presentation only: retain the canonical classification and printed identity. */
export function paperLearningSubjects(q:Pick<PaperQuestion,'taxonomy_subject_id'|'taxonomy_subject'|'taxonomy_topic'>,exam:string){
 const id=q.taxonomy_subject_id
 if(!id)return []
 const clerical=['udc','ldc','assistant'].includes(exam)
 const general=['general-knowledge','general-studies'].includes(id)
 const science=id==='science'||(general&&q.taxonomy_topic?.toLowerCase()==='science in the news')
 const choices:{id:string;label:string}[]=[]
 if(general||((clerical||exam==='combined-prelims')&&science))choices.push({id:'gk-gs',label:clerical?'General Knowledge':exam==='combined-prelims'?'General Studies':'GK/GS'})
 if(science)choices.push({id:'science',label:'Science'})
 if(!general&&!science)choices.push({id,label:q.taxonomy_subject||id})
 return choices
}
