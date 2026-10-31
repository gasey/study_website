import {useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import {getExamStudyTopics,type GroupBStudyArea,type ExamStudySubject,type ExamStudyTopics as StudyTopics} from '../lib/api'

type Selection = {subject_id?:string;topic_id?:string;subtopic_id?:string}
function studyLink(examId:string,view:'browse'|'practice',selection:Selection,area?:GroupBStudyArea,basePath?:string) {
  const params=new URLSearchParams({view})
  if(area)params.set('study_area',area)
  if(examId!=='group-b'&&basePath)params.set('collection',examId)
  if(view==='practice')params.set('pool','practice')
  for(const [key,value] of Object.entries(selection))if(value)params.set(key,value)
  return `${basePath||`/exams/${encodeURIComponent(examId)}`}?${params}#exam-question-browser`
}

export default function ExamStudyTopics({examId,area,basePath}:{examId:string;area?:GroupBStudyArea;basePath?:string}) {
  const [data,setData]=useState<StudyTopics|null>(null)
  const [error,setError]=useState('')
  const [search,setSearch]=useState('')
  const [expanded,setExpanded]=useState<string|null>(null)
  useEffect(()=>{
    let live=true
    setData(null);setError('');setExpanded(null)
    getExamStudyTopics(examId,area).then(value=>{if(live)setData(value)}).catch(e=>{if(live)setError(e instanceof Error?e.message:'Could not load subjects')})
    return()=>{live=false}
  },[examId,area])
  const query=search.trim().toLocaleLowerCase()
  const subjects=useMemo(()=>data?.subjects.filter(subject=>
    !query || subject.title.toLocaleLowerCase().includes(query) ||
    subject.topics.some(topic=>topic.title.toLocaleLowerCase().includes(query) ||
      topic.subtopics.some(subtopic=>subtopic.title.toLocaleLowerCase().includes(query))))??[],[data,query])

  return <section className="mt-7" aria-labelledby="exam-study-heading">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div><div className="font-mono text-[10px] uppercase tracking-[.12em] text-exams-dark">Your study route</div><h2 id="exam-study-heading" className="mt-1 font-display text-[30px] font-medium">Study by subject and topic</h2><p className="mt-2 max-w-[700px] text-[14px] leading-relaxed text-secondary">Choose a subject, then a topic or subtopic. Every count comes from this exam’s listed papers and approved question tags.</p></div>
      {data&&<span className="rounded-pill border border-hairline bg-card px-3 py-2 font-mono text-[11px] text-secondary">{data.subjects.length} subjects · {data.questions.toLocaleString('en-IN')} distinct questions</span>}
    </div>
    {error&&<p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-[13px] text-mypick">Could not load this exam’s topic map: {error}</p>}
    {!data&&!error&&<p role="status" className="mt-4 rounded-[14px] border border-hairline bg-card p-5 text-[13px] text-secondary">Loading subjects and topics…</p>}
    {data&&<>
      <div className="mt-5 flex flex-wrap items-end gap-3 rounded-[14px] border border-hairline bg-card p-4">
        <label className="min-w-[220px] flex-1 text-[12px] font-semibold">Find a subject or topic<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="English, arithmetic, computer…" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas px-3 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none"/></label>
        <Link to={studyLink(examId,'browse',{},area,basePath)} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Browse all exam questions →</Link>
      </div>
      {!subjects.length&&<p className="mt-5 rounded-[12px] border border-hairline bg-card p-5 text-[13px] text-secondary">No subject or topic matches that search.</p>}
      <div className="mt-4 grid items-start gap-3 md:grid-cols-2">{subjects.map(subject=><SubjectCard key={subject.id} subject={subject} examId={examId} expanded={expanded===subject.id||!!query} onToggle={()=>setExpanded(expanded===subject.id?null:subject.id)} query={query} area={area} basePath={basePath}/>)}</div>
      {data.unclassified>0&&<p className="mt-4 text-[12px] leading-relaxed text-secondary">{data.unclassified.toLocaleString('en-IN')} questions do not yet have an approved subject tag. They remain available through “Browse all exam questions” and their paper pages.</p>}
      <p className="mt-3 text-[12px] leading-relaxed text-secondary">A question can have more than one approved tag, so subject and topic counts can overlap. Browse includes questions without answers; practice uses questions with an available answer and keeps review labels visible.</p>
    </>}
  </section>
}

function SubjectCard({subject,examId,expanded,onToggle,query,area,basePath}:{subject:ExamStudySubject;examId:string;expanded:boolean;onToggle:()=>void;query:string;area?:GroupBStudyArea;basePath?:string}) {
  const topics=subject.topics.filter(topic=>!query||subject.title.toLocaleLowerCase().includes(query)||topic.title.toLocaleLowerCase().includes(query)||topic.subtopics.some(subtopic=>subtopic.title.toLocaleLowerCase().includes(query)))
  const selection={subject_id:subject.id}
  return <article className="min-w-0 rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.04)]">
    <div className="flex items-start justify-between gap-3"><div><h3 className="font-display text-[24px] leading-tight">{subject.title}</h3><p className="mt-1 font-mono text-[11px] text-muted">{subject.questions.toLocaleString('en-IN')} questions · {subject.topics.length} topics</p></div><button type="button" onClick={onToggle} aria-expanded={expanded} aria-label={`${expanded?'Hide':'Show'} topics in ${subject.title}`} className="grid min-h-11 min-w-11 place-items-center rounded-full border border-hairline text-[20px]">{expanded?'−':'+'}</button></div>
    {!area&&['udc','ldc','assistant'].includes(examId)&&subject.id==='gk-gs'&&subject.topics.some(topic=>topic.id==='gk-gs:science')&&<p className="mt-3 text-[12px] leading-relaxed text-secondary">Includes Science. Open topics to choose Physics, Chemistry, Biology or science in the news.</p>}
    {!area&&['udc','ldc','assistant'].includes(examId)&&subject.id==='science'&&<p className="mt-3 text-[12px] leading-relaxed text-secondary">Also included under General Knowledge → Science. Use this subject for deeper science topics.</p>}
    <div className="mt-4 flex flex-wrap gap-2"><Link to={studyLink(examId,'browse',selection,area,basePath)} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[12px] font-semibold text-paper">Browse subject</Link><Link to={studyLink(examId,'practice',selection,area,basePath)} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[12px] font-semibold">Practise answers</Link></div>
    {expanded&&<div className="mt-5 border-t border-hairline pt-3">
      {topics.length?<ul className="space-y-2">{topics.map(topic=><li key={topic.id} className="rounded-[10px] bg-canvas p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><strong className="text-[14px]">{topic.title}</strong><span className="ml-2 font-mono text-[11px] text-muted">{topic.questions.toLocaleString('en-IN')}</span></div><div className="flex flex-wrap gap-2"><Link className="text-[12px] font-semibold text-link underline" to={studyLink(examId,'browse',{...selection,topic_id:topic.id},area,basePath)}>Browse</Link><Link className="text-[12px] font-semibold text-link underline" to={studyLink(examId,'practice',{...selection,topic_id:topic.id},area,basePath)}>Practise</Link></div></div>{topic.subtopics.length>0&&<ul className="mt-2 flex flex-wrap gap-2">{topic.subtopics.filter(subtopic=>!query||subject.title.toLocaleLowerCase().includes(query)||topic.title.toLocaleLowerCase().includes(query)||subtopic.title.toLocaleLowerCase().includes(query)).map(subtopic=><li key={subtopic.id}><Link className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-3 text-[11px] font-semibold hover:border-ink" to={studyLink(examId,'browse',{...selection,topic_id:topic.id,subtopic_id:subtopic.id},area,basePath)}>{subtopic.title} · {subtopic.questions}</Link></li>)}</ul>}</li>)}</ul>:<p className="text-[12px] text-secondary">No narrower approved topics yet. Use the subject buttons to study all its questions.</p>}
    </div>}
  </article>
}
