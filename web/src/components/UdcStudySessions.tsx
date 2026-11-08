import {answerFeedbackLabel} from '../lib/answerStatus'
import QuestionStudyControls from './QuestionStudyControls'
import {newQuestionSeed} from '../lib/questionBrowse'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import StudyQuestionCard from './StudyQuestionCard'
import { AnswerLayoutControl } from './AnswerLayout'
import { scrollToResults } from '../lib/pagination'
import { nextStudySetLink, studySetFilters, studySetLink } from '../lib/studySetLinks'
import {
  getExamStudyTopics, getStudySet, listStudySets, startStudySet, moveStudySet,
  checkStudySet, viewStudySet, finishStudySet,
  type CollectionPaper, type ExamStudyTopics, type StudySet, type StudySetPreview, type StudySetState,
} from '../lib/api'

const primary='inline-flex min-h-11 items-center justify-center rounded-pill bg-ink px-4 py-2 text-[13px] font-semibold text-paper disabled:opacity-40'
const secondary='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 py-2 text-[13px] font-semibold disabled:opacity-40'

function StoredFeedbackNotice({fields,qid,paper}:{fields?:string[];qid:string;paper?:string}) {
  if(!fields?.length)return null
  const query=new URLSearchParams({exam:'udc'});if(paper)query.set('paper',paper)
  return <aside className="mt-3 rounded-lg border border-hairline bg-canvas p-3 text-[13px] text-secondary">
    <p>This question was updated after your check ({fields.join(', ')}). This set keeps your original feedback and totals. Source details may reflect the updated paper.</p>
    <Link to={'/bank/'+encodeURIComponent(qid)+'?'+query} className="inline-flex min-h-11 items-center font-semibold text-link underline">Review current question →</Link>
  </aside>
}

export default function UdcStudySessions({papers}:{papers:CollectionPaper[]}) {
  const [params,setParams]=useSearchParams(),nav=useNavigate()
  const sid=params.get('session')||''
  const filters=studySetFilters(params)
  useEffect(()=>{if(!sid&&filters.order==='mixed'&&!filters.seed)setParams(previous=>{const next=new URLSearchParams(previous);next.set('seed',newQuestionSeed());return next},{replace:true})},[sid,filters.order,filters.seed,setParams])
  const [size,setSize]=useState<10|20>(10)
  const [taxonomy,setTaxonomy]=useState<ExamStudyTopics|null>(null)
  const [recent,setRecent]=useState<StudySetPreview[]>([])
  const [session,setSession]=useState<StudySet|null>(null)
  const [loading,setLoading]=useState(!!sid),[busy,setBusy]=useState(false),[panelBusy,setPanelBusy]=useState(false)
  const [error,setError]=useState(''),[retry,setRetry]=useState(0)
  const [picks,setPicks]=useState<Record<string,number>>({}),[viewed,setViewed]=useState<Record<string,boolean>>({})
  const inFlight=useRef(false),active=useRef(true),generation=useRef(0)
  const startRequest=useRef<{signature:string;key:string}|null>(null)
  useEffect(()=>{active.current=true;return()=>{active.current=false;generation.current++}},[])
  useEffect(()=>{
    let live=true
    getExamStudyTopics('udc').then(value=>{if(live)setTaxonomy(value)}).catch(()=>{})
    if(!sid)listStudySets().then(value=>{if(live)setRecent(value.items)}).catch(e=>{if(live)setError(e.message)})
    return()=>{live=false}
  },[sid,retry])
  useEffect(()=>{
    let live=true
    setSession(null);setPicks({});setViewed({});setPanelBusy(false);setError('');setLoading(!!sid)
    const run=++generation.current
    if(sid)getStudySet(sid).then(value=>{if(live&&run===generation.current)setSession(value)})
      .catch(e=>{if(live&&run===generation.current)setError(e.message)})
      .finally(()=>{if(live&&run===generation.current)setLoading(false)})
    const auth=()=>{setSession(null);setRecent([]);setPicks({});setViewed({});setRetry(n=>n+1)}
    window.addEventListener('ism-auth-change',auth)
    return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',auth)}
  },[sid,retry])
  useEffect(()=>{
    if(!session||loading)return
    const frame=requestAnimationFrame(()=>scrollToResults('exam-question-browser'))
    return()=>cancelAnimationFrame(frame)
  },[session?.id,session?.position,session?.finished_at,loading])
  const subject=taxonomy?.subjects.find(s=>s.id===filters.subject_id)
  const topic=subject?.topics.find(t=>t.id===filters.topic_id)
  const sessionSubject=taxonomy?.subjects.find(s=>s.id===session?.filters.subject_id)?.title
  const qid=session?.question_ids[session.position]
  const question=session?.items.find(q=>q.id===qid)
  const checked=qid?session?.results[qid]:undefined
  const pick=qid?(checked?.chosen_index??picks[qid]):undefined
  const locked=busy||panelBusy

  function filter(key:string,value:string) {
    setParams(old=>{const next=new URLSearchParams(old);if(value)next.set(key,value);else next.delete(key);next.delete('session');next.delete('offset');
      if(key==='subject_id'){next.delete('topic_id');next.delete('subtopic_id')}
      if(key==='topic_id')next.delete('subtopic_id')
      return next},{replace:true})
    startRequest.current=null;setError('')
  }
  async function start(reviewId?:string) {
    if(inFlight.current||filters.order==='mixed'&&!filters.seed)return
    const clean={...filters};delete clean.review_session_id
    const requestedSize=reviewId&&session?session.requested_size:size
    const signature=JSON.stringify({size:requestedSize,filters:clean,reviewId})
    if(startRequest.current?.signature!==signature)startRequest.current={signature,key:crypto.randomUUID()}
    inFlight.current=true;setBusy(true);setError('')
    const run=generation.current
    try {
      const value=await startStudySet(startRequest.current.key,requestedSize,clean,reviewId)
      if(active.current&&run===generation.current){nav(studySetLink(value.id));window.dispatchEvent(new Event('ism-study-checkpoint'))}
    } catch(e) {if(active.current&&run===generation.current)setError((e as Error).message)}
    finally {inFlight.current=false;if(active.current)setBusy(false)}
  }
  async function change(task:()=>Promise<StudySetState>) {
    if(inFlight.current)return
    inFlight.current=true;setBusy(true);setError('')
    const run=generation.current
    try {
      const value=await task()
      if(active.current&&run===generation.current){setSession(old=>old?{...old,...value}:old);window.dispatchEvent(new Event('ism-study-checkpoint'))}
    } catch(e) {if(active.current&&run===generation.current)setError((e as Error).message)}
    finally {inFlight.current=false;if(active.current)setBusy(false)}
  }
  async function next() {
    if(!session||locked)return
    if(session.position===session.total-1)await change(()=>finishStudySet(session.id,session.version))
    else await change(()=>moveStudySet(session.id,session.version,session.position+1))
  }
  function onViewed(value:boolean) {
    if(!qid||!session)return
    setViewed(old=>old[qid]===value?old:{...old,[qid]:value})
    if(value&&!session.finished_at&&!session.viewed_ids.includes(qid)&&!checked)
      void change(()=>viewStudySet(session.id,qid))
  }
  const feedback=<p className="mt-3 text-[12px] leading-relaxed text-secondary">Practice feedback uses each question’s labelled answer source and review status.</p>
  const errorPanel=error&&<div role="alert" className="mt-4 rounded-xl border border-mypick bg-mypick-soft p-4 text-[13px] text-mypick"><p>{error}</p>{sid?<button type="button" className="mt-2 min-h-11 underline" disabled={busy} onClick={()=>setRetry(n=>n+1)}>Reload saved set</button>:<button type="button" className="mt-2 min-h-11 underline" disabled={busy} onClick={()=>filter('offset','')}>Start from the beginning</button>}</div>

  if(!sid)return <section id="exam-question-browser" tabIndex={-1} className="exam-reading-area mt-6 focus:outline-none">
    <h2 className="font-display text-[28px]">A short UDC practice set</h2>
    <p className="mt-2 text-[14px] text-secondary">Choose 10 or 20 questions. Your order, checked answers and place are saved automatically.</p>
    <div className="mt-4 rounded-[14px] border border-hairline bg-card p-4 sm:p-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="min-w-0 text-[13px] font-semibold">Subject<select disabled={busy} value={filters.subject_id||''} onChange={e=>filter('subject_id',e.target.value)} className="mt-2 block min-h-11 min-w-0 w-full max-w-full rounded-lg border border-hairline bg-canvas p-2"><option value="">All UDC subjects</option>{filters.subject_id&&!subject&&<option value={filters.subject_id}>Selected subject</option>}{taxonomy?.subjects.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
        <fieldset><legend className="text-[13px] font-semibold">Set size</legend><div className="mt-2 flex gap-2">{([10,20] as const).map(n=><button type="button" key={n} disabled={busy} aria-pressed={size===n} onClick={()=>{setSize(n);startRequest.current=null}} className={size===n?primary:secondary}>{n} questions</button>)}</div></fieldset>
      </div>
      <QuestionStudyControls status={filters.study_status||'all'} order={filters.order||'mixed'} disabled={busy} onStatus={value=>filter('status',value)} onOrder={value=>filter('order',value)} onShuffle={()=>{filter('seed',newQuestionSeed());startRequest.current=null}}/>
      <details className="mt-4 border-t border-hairline pt-1"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Topic, paper &amp; study filters{[filters.topic_id,filters.paper_id,filters.section_path,filters.answer_status,filters.q,filters.offset].filter(Boolean).length?' · filters applied':''}</summary>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="min-w-0 text-[12px] font-semibold">Topic<select value={filters.topic_id||''} disabled={busy||!subject} onChange={e=>filter('topic_id',e.target.value)} className="mt-1 block min-h-11 min-w-0 w-full max-w-full rounded-lg border border-hairline bg-canvas p-2"><option value="">All topics</option>{filters.topic_id&&!topic&&<option value={filters.topic_id}>Selected topic</option>}{subject?.topics.map(t=><option key={t.id} value={t.id}>{t.title}</option>)}</select></label>
          <label className="min-w-0 text-[12px] font-semibold">Paper<select disabled={busy} value={filters.paper_id||''} onChange={e=>filter('paper',e.target.value)} className="mt-1 block min-h-11 min-w-0 w-full max-w-full rounded-lg border border-hairline bg-canvas p-2"><option value="">All UDC papers</option>{filters.paper_id&&!papers.some(p=>p.id===filters.paper_id)&&<option value={filters.paper_id}>Selected paper</option>}{papers.map(p=><option key={p.id} value={p.id}>{p.id.split('/').pop()?.replace(/\.pdf$/i,'')}</option>)}</select></label>
          <label className="min-w-0 text-[12px] font-semibold">Answer sources<select disabled={busy} value={filters.answer_status||''} onChange={e=>filter('answer_status',e.target.value)} className="mt-1 block min-h-11 min-w-0 w-full max-w-full rounded-lg border border-hairline bg-canvas p-2"><option value="">All available answers</option><option value="official">Official keys</option><option value="verified">Verified answers</option><option value="needs-review">Needs review</option></select></label>
        </div>
        <button type="button" className="mt-2 min-h-11 text-[12px] font-semibold underline" disabled={busy} onClick={()=>{setParams({view:'practice'},{replace:true});startRequest.current=null}}>Clear all filters</button>
      </details>
      <p className="mt-3 text-[12px] text-secondary">If fewer questions are available, the set will use that smaller number. Identical text copies from booklet series are grouped; figures and source differences stay separate.</p>
      {feedback}
      <button type="button" disabled={busy} onClick={()=>void start()} className={primary+' mt-4'}>{busy?'Preparing your set…':`Start ${size}-question set →`}</button>
    </div>
    {errorPanel}
    {recent.length>0&&<section aria-label="Saved UDC practice sets" className="mt-6"><h3 className="font-display text-[23px]">Your saved sets</h3><div className="mt-3 space-y-2">{recent.map(s=><Link key={s.id} to={studySetLink(s.id)} className="flex min-h-11 flex-wrap items-center justify-between gap-2 rounded-xl border border-hairline bg-card p-4 text-[13px]"><span>{taxonomy?.subjects.find(t=>t.id===s.filters.subject_id)?.title||'UDC practice'} · {s.total} {s.total===1?'question':'questions'} <span className="text-muted">· {new Date(s.created_at).toLocaleDateString('en-IN')}</span></span><strong className="text-link">{s.finished_at?'View summary':`Resume · ${s.position+1} of ${s.total}`} →</strong></Link>)}</div></section>}
    <Link to="/exams/udc?view=browse#exam-question-browser" className="mt-5 inline-flex min-h-11 items-center text-[13px] font-semibold text-link">Browse the full UDC question bank →</Link>
  </section>

  if(loading||!session)return <section id="exam-question-browser" tabIndex={-1} className="exam-reading-area mt-6 focus:outline-none">{loading?<p role="status">Restoring your saved UDC set…</p>:errorPanel}<Link to="/exams/udc?view=practice#exam-question-browser" className="mt-4 inline-flex min-h-11 items-center text-[13px] font-semibold text-link">Choose a UDC set →</Link></section>

  if(session.finished_at)return <section id="exam-question-browser" tabIndex={-1} className="exam-reading-area mt-6 focus:outline-none">
    <div className="rounded-[14px] border border-hairline bg-card p-5">
      <p className="font-mono text-[11px] uppercase tracking-widest text-exams-dark">Saved UDC practice</p>
      <h2 className="mt-2 font-display text-[30px]">Your set is finished</h2>
      <p className="mt-2 text-[14px] text-secondary">{sessionSubject||'UDC'} · {session.total} questions · {new Date(session.finished_at).toLocaleString('en-IN')}</p>
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">{[['Correct',session.summary.correct],['Wrong',session.summary.wrong],['Viewed',session.summary.viewed],['Skipped',session.summary.skipped]].map(([label,value])=><div key={label} className="rounded-xl bg-canvas p-4"><strong className="block font-display text-[30px]">{value}</strong><span className="text-[12px] text-secondary">{label}</span></div>)}</div>
      {feedback}
      {Object.values(session.results).some(answer=>answer.updated_fields?.length)&&<p className="mt-3 text-[13px] text-secondary">Some questions have changed since this set. Open the checked-question review below to see which ones.</p>}
      {session.summary.unofficial>0&&<p className="mt-2 text-[12px] text-secondary">{session.summary.unofficial} checked {session.summary.unofficial===1?'answer used an unofficial solution':'answers used unofficial solutions'}. See each question’s review label.</p>}
      <div className="mt-5 flex flex-wrap gap-2">
        {session.summary.wrong>0&&<button type="button" disabled={busy} onClick={()=>void start(session.id)} className={primary}>{busy?'Preparing review…':'Practise mistakes →'}</button>}
        <Link to={nextStudySetLink(session.filters,session.total)} className={secondary}>Choose another set →</Link>
        <Link to="/exams/udc?view=progress" className={secondary}>UDC progress</Link>
      </div>
    </div>
    {errorPanel}
    <details className="mt-5 rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer py-2 text-[14px] font-semibold">Review checked questions</summary>
      <div className="divide-y divide-hairline">{session.question_ids.filter(id=>session.results[id]).map(id=>{const q=session.items.find(item=>item.id===id),answer=session.results[id];return q?<div key={id} className="py-4"><h3 className="text-[14px] font-semibold">{q.question}</h3><p className="mt-2 text-[13px] text-secondary">{answerFeedbackLabel(answer.result,{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status})} · Your answer: {q.options[answer.chosen_index??-1]||'Unavailable'} · Answer: {answer.result.answer_text}</p><StoredFeedbackNotice fields={answer.updated_fields} qid={id} paper={q.source_appearance?.paper_id}/></div>:null})}</div>
      {Object.keys(session.results).length===0&&<p className="text-[13px] text-secondary">No answers were checked in this set.</p>}
    </details>
  </section>

  return <section id="exam-question-browser" tabIndex={-1} className="exam-reading-area mt-6 focus:outline-none" aria-busy={busy}>
    <div className="rounded-xl border border-hairline bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-display text-[24px]">UDC practice{sessionSubject?' · '+sessionSubject:''}</h2><p role="status" className="mt-1 text-[13px] text-secondary">Question {session.position+1} of {session.total} · Saved automatically</p></div><button type="button" disabled={locked} onClick={()=>void change(()=>finishStudySet(session.id,session.version))} className={secondary}>Finish set</button></div>
      {session.total<session.requested_size&&<p className="mt-2 text-[12px] text-secondary">{session.total} {session.total===1?'question was':'questions were'} available for your {session.requested_size}-question choice.</p>}
    </div>
    {errorPanel}
    <details className="mt-3 rounded-xl border border-hairline bg-card px-4"><summary className="min-h-11 cursor-pointer py-3 text-[12px] font-semibold">Answer layout &amp; set details</summary><AnswerLayoutControl/>{feedback}<p className="my-3 text-[12px] text-secondary">Viewed answers are reading only. They earn no attempt credit or rewards; the existing retry window applies.</p></details>
    {qid&&<StoredFeedbackNotice fields={checked?.updated_fields} qid={qid} paper={question?.source_appearance?.paper_id}/>}
    {question&&qid?<StudyQuestionCard key={qid} q={question} collectionId="udc" result={checked?.result} pick={pick} viewed={viewed[qid]} disabled={locked}
      onPick={i=>{if(inFlight.current||locked)return;setPicks(old=>({...old,[qid]:i}));void change(()=>checkStudySet(session.id,session.version,qid,i,question.presentation_hash))}}
      showPanelNext={false} onViewed={onViewed} onBusy={setPanelBusy} onRetry={()=>setViewed(old=>({...old,[qid]:false}))} onNext={next} nextLabel={session.position===session.total-1?'Finish set →':'Next question →'}/>:<p className="my-6 rounded-xl border border-hairline bg-card p-4 text-[14px]">This saved question is no longer available. Skip it to continue the set.</p>}
    <nav aria-label="Study set navigation" className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4">
      <button type="button" disabled={locked||session.position===0} onClick={()=>void change(()=>moveStudySet(session.id,session.version,session.position-1))} className={secondary}>← Previous</button>
      <span className="text-[12px] text-secondary">{session.summary.correct+session.summary.wrong} checked · {session.summary.viewed} viewed</span>
      <button type="button" disabled={locked} onClick={()=>void next()} className={primary}>{session.position===session.total-1?'Finish set →':checked||viewed[qid||'']?'Next question →':'Skip question →'}</button>
    </nav>
  </section>
}
