import {learningSubjectTitle} from '../lib/groupBStudy'
import {useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {getExamStudyTopics,type GroupBStudyArea,type ExamStudySubject,type ExamStudyTopics as StudyTopics} from '../lib/api'

type Selection = {subject_id?:string;topic_id?:string;subtopic_id?:string}
function studyLink(examId:string,view:'browse'|'practice',selection:Selection,area?:GroupBStudyArea,basePath?:string) {
  const params=new URLSearchParams({view});if(examId==='combined-prelims'){const section=new URLSearchParams(window.location.search).get('section');if(section==='gs'||section==='aptitude')params.set('section',section)}
  if(area)params.set('study_area',area)
  if(basePath)params.set('collection',examId)
  if(view==='practice')params.set('pool','practice')
  for(const [key,value] of Object.entries(selection))if(value)params.set(key,value)
  return `${basePath||`/exams/${encodeURIComponent(examId)}`}?${params}#exam-question-browser`
}

export default function ExamStudyTopics({examId,area,basePath,allowPractice=true}:{examId:string;area?:GroupBStudyArea;basePath?:string;allowPractice?:boolean}) {
  const [params]=useSearchParams();const section=examId==='combined-prelims'?(params.get('section')||undefined):undefined
  const [data,setData]=useState<StudyTopics|null>(null)
  const [error,setError]=useState('')
  const [search,setSearch]=useState('')
  const [expanded,setExpanded]=useState<Record<string,boolean>>({})
  useEffect(()=>{
    let live=true
    setData(null);setError('');setExpanded({})
    getExamStudyTopics(examId,area,section).then(value=>{if(live)setData(value)}).catch(e=>{if(live)setError(e instanceof Error?e.message:'Could not load subjects')})
    return()=>{live=false}
  },[examId,area,section])
  const displayTitle=(subject:ExamStudySubject)=>learningSubjectTitle(subject.id,subject.title,examId)
  const query=search.trim().toLocaleLowerCase()
  const subjects=useMemo(()=>data?.subjects.filter(subject=>
    !query || subject.title.toLocaleLowerCase().includes(query) ||
    subject.topics.some(topic=>topic.title.toLocaleLowerCase().includes(query) ||
      topic.subtopics.some(subtopic=>subtopic.title.toLocaleLowerCase().includes(query))))??[],[data,query])

  return <section className="mt-7" aria-labelledby="exam-study-heading">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div><div className="font-mono text-[10px] uppercase tracking-[.12em] text-exams-dark">Your study route</div><h2 id="exam-study-heading" className="mt-1 font-display text-[30px] font-medium">Study by subject and topic</h2><p className="mt-2 max-w-[700px] text-[14px] leading-relaxed text-secondary">Open a subject to explore its topics, or jump straight into questions.</p></div>
      {data&&<span className="rounded-pill border border-hairline bg-card px-3 py-2 font-mono text-[11px] text-secondary">{data.subjects.length} subjects · {data.questions.toLocaleString('en-IN')} distinct questions</span>}
    </div>
    {error&&<p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-[13px] text-mypick">Could not load this exam’s topic map: {error}</p>}
    {!data&&!error&&<p role="status" className="mt-4 rounded-[14px] border border-hairline bg-card p-5 text-[13px] text-secondary">Loading subjects and topics…</p>}
    {data&&<>
      <div className="mt-5 flex flex-wrap items-end gap-3 rounded-[14px] border border-hairline bg-card p-4">
        <label className="min-w-0 basis-56 flex-1 text-[12px] font-semibold">Find a subject or topic<input type="search" value={search} onChange={e=>{setSearch(e.target.value);setExpanded({})}} placeholder="English, arithmetic, computer…" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas px-3 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none"/></label>
        <Link to={studyLink(examId,'browse',{},area,basePath)} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Browse all exam questions →</Link>
      </div>
      {!subjects.length&&<p className="mt-5 rounded-[12px] border border-hairline bg-card p-5 text-[13px] text-secondary">No subject or topic matches that search.</p>}
      {subjects.length>0&&<div className="mt-2 flex items-center justify-between text-xs text-secondary"><span>{subjects.length} subjects shown</span><button type="button" className="min-h-11 px-2 font-semibold text-link" onClick={()=>{const close=subjects.every(subject=>expanded[subject.id]??!!query);setExpanded(Object.fromEntries(subjects.map(subject=>[subject.id,!close])))}}>{subjects.every(subject=>expanded[subject.id]??!!query)?'Collapse all':'Expand all'}</button></div>}
      <div className="mt-2 grid items-start gap-3 md:grid-cols-2">{subjects.map(subject=><SubjectCard key={subject.id} subject={{...subject,title:displayTitle(subject)}} examId={examId} expanded={expanded[subject.id]??!!query} onToggle={()=>setExpanded(previous=>({...previous,[subject.id]:!(previous[subject.id]??!!query)}))} query={query} area={area} basePath={basePath} allowPractice={allowPractice}/>)}</div>
      {data.unclassified>0&&<p className="mt-4 text-[12px] leading-relaxed text-secondary">{data.unclassified.toLocaleString('en-IN')} questions do not yet have an approved subject tag. They remain available through “Browse all exam questions” and their paper pages.</p>}
      <p className="mt-3 text-[12px] leading-relaxed text-secondary">A question can have more than one approved tag, so subject and topic counts can overlap. Browse includes questions without answers; practice uses questions with an available answer and keeps review labels visible.</p>
    </>}
  </section>
}

function SubjectCard({subject,examId,expanded,onToggle,query,area,basePath,allowPractice}:{subject:ExamStudySubject;examId:string;expanded:boolean;onToggle:()=>void;query:string;area?:GroupBStudyArea;basePath?:string;allowPractice:boolean}) {
  const topics=subject.topics.filter(topic=>!query||subject.title.toLocaleLowerCase().includes(query)||topic.title.toLocaleLowerCase().includes(query)||topic.subtopics.some(subtopic=>subtopic.title.toLocaleLowerCase().includes(query)))
  const selection={subject_id:subject.id}
  return <article className="exam-subject min-w-0" data-expanded={expanded}>
    <h3><button type="button" onClick={onToggle} aria-expanded={expanded} aria-controls={'subject-topics-'+subject.id} aria-label={`${expanded?'Hide':'Show'} topics in ${subject.title}`} className="exam-subject-toggle"><span><span className="exam-subject-title">{subject.title}</span><span className="exam-subject-count">{subject.questions.toLocaleString('en-IN')} {subject.questions===1?'question':'questions'} · {subject.topics.length} {subject.topics.length===1?'topic':'topics'}</span></span><span className="exam-chevron" aria-hidden="true">⌄</span></button></h3>
    <div className="exam-subject-body">
    {!area&&['udc','ldc','assistant'].includes(examId)&&subject.id==='gk-gs'&&subject.topics.some(topic=>topic.id==='gk-gs:science')&&<p className="mt-3 text-[12px] leading-relaxed text-secondary">Includes Science. Open topics to choose Physics, Chemistry, Biology or science in the news.</p>}
    {!area&&['udc','ldc','assistant'].includes(examId)&&subject.id==='science'&&<p className="mt-3 text-[12px] leading-relaxed text-secondary">Also included under General Knowledge → Science. Use this subject for deeper science topics.</p>}
    <div className="mt-4 flex flex-wrap gap-2"><Link to={studyLink(examId,'browse',selection,area,basePath)} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[12px] font-semibold text-paper">Browse subject</Link>{allowPractice&&<Link to={studyLink(examId,'practice',selection,area,basePath)} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[12px] font-semibold">Practise answers</Link>}</div>
    <div id={'subject-topics-'+subject.id} hidden={!expanded} className="mt-4 border-t border-hairline pt-3">
      {topics.length?<ul className="space-y-2">{topics.map(topic=><li key={topic.id} className="rounded-[10px] bg-canvas p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><strong className="text-[14px]">{topic.title}</strong><span className="ml-2 font-mono text-[11px] text-muted">{topic.questions.toLocaleString('en-IN')}</span></div><div className="flex flex-wrap gap-2"><Link className="inline-flex min-h-11 items-center px-2 text-[12px] font-semibold text-link underline" to={studyLink(examId,'browse',{...selection,topic_id:topic.id},area,basePath)}>Browse</Link>{allowPractice&&<Link className="inline-flex min-h-11 items-center px-2 text-[12px] font-semibold text-link underline" to={studyLink(examId,'practice',{...selection,topic_id:topic.id},area,basePath)}>Practise</Link>}</div></div>{topic.subtopics.length>0&&<ul className="mt-2 flex flex-wrap gap-2">{topic.subtopics.filter(subtopic=>!query||subject.title.toLocaleLowerCase().includes(query)||topic.title.toLocaleLowerCase().includes(query)||subtopic.title.toLocaleLowerCase().includes(query)).map(subtopic=><li key={subtopic.id}><Link className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-3 text-[11px] font-semibold hover:border-ink" to={studyLink(examId,'browse',{...selection,topic_id:topic.id,subtopic_id:subtopic.id},area,basePath)}>{subtopic.title} · {subtopic.questions}</Link></li>)}</ul>}</li>)}</ul>:<p className="text-[12px] text-secondary">No narrower approved topics yet. Use the subject buttons to study all its questions.</p>}
    </div>
    </div>
  </article>
}
