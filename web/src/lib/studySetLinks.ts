import type { StudySetFilters } from './api'

export function studySetLink(id:string) {
  return '/exams/udc?'+new URLSearchParams({view:'practice',session:id})+'#exam-question-browser'
}
export function studySetFilters(params:URLSearchParams):StudySetFilters {
  const f:StudySetFilters={pool:params.get('pool')==='scorable'?'scorable':'practice'}
  for(const [url,key] of [['subject_id','subject_id'],['topic_id','topic_id'],['subtopic_id','subtopic_id'],['paper','paper_id'],['section','section_path'],['q','q']] as const) {
    const value=params.get(url)?.trim();if(value)f[key]=value
  }
  const status=params.get('status')
  if(status==='wrong'||status==='unseen'||status==='answered'||status==='ever_wrong')f.study_status=status
  const answer=params.get('answer_status')
  if(answer==='official'||answer==='verified'||answer==='needs-review')f.answer_status=answer
  f.order=params.get('order')==='repeated'?'repeated':'mixed'
  f.seed=params.get('seed')||''
  f.offset=Math.floor(Math.max(0,Math.min(100000,Number(params.get('offset'))||0)))
  return f
}
export function nextStudySetLink(filters:StudySetFilters,total:number) {
  const params=new URLSearchParams({view:'practice',order:filters.order||'repeated'})
  for(const [key,url] of [['subject_id','subject_id'],['topic_id','topic_id'],['subtopic_id','subtopic_id'],['paper_id','paper'],['section_path','section'],['q','q'],['study_status','status'],['pool','pool'],['answer_status','answer_status'],['order','order'],['seed','seed']] as const) {
    const value=filters[key];if(value)params.set(url,value)
  }
  // Personal queues shrink as answers leave them. A second set must read from
  // the same offset, rather than skipping the next unseen/corrected question.
  const offset=filters.review_session_id?0:(filters.offset||0)+(['wrong','unseen'].includes(filters.study_status||'')?0:total)
  if(offset)params.set('offset',String(offset))
  return '/exams/udc?'+params+'#exam-question-browser'
}
