/** These reads never select learner state. Question lists deliberately retain
 * credentials: booklet representatives can depend on the viewer's attempts. */
export function publicBrowseRead(path:string,init?:RequestInit){
  if((init?.method||'GET').toUpperCase()!=='GET')return false
  const headers=new Headers(init?.headers)
  if(['authorization','cookie','x-device-id'].some(name=>headers.has(name)))return false
  const [base,query='']=path.split('?')
  const params=new URLSearchParams(query)
  if(params.has('learning_entry')||params.getAll('study_status').some(value=>value!=='all'))return false
  return /^\/questions\/(?:taxonomy|papers)$/.test(base)
    || /^\/questions\/[^/]+(?:\/next)?$/.test(base)
    || /^\/collections(?:\/[^/]+(?:\/(?:header|study-topics|paper-questions))?)?$/.test(base)
}

/** Mirrors the server's filter categories; admission and counts are server-owned. */
export function powerFilterQuery(query:Record<string,unknown>){
  const present=(key:string)=>Array.isArray(query[key])?(query[key] as unknown[]).length>0:query[key]!==undefined&&query[key]!==null&&query[key]!==''
  const topic=present('topic_id')||present('subtopic_id'),year=present('year_from')||present('year_to')
  const answer=present('answer_status')||present('source')||(present('pool')&&query.pool!=='all')
  const crossExam=query.exam_scope==='all'&&['subject_id','topic_id','subtopic_id','shelf_id'].some(present)
  return crossExam||[topic,year,answer].filter(Boolean).length>=2
}
