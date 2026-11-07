import type {PaperReadiness} from '../lib/bankOrganization'
import {GROUP_B_COLLECTIONS,groupBLink} from '../lib/groupBStudy'
import {paperIdentity} from '../lib/paperIdentity'
import PracticeAnswerPanel from '../components/PracticeAnswerPanel'
import AnswerProvenance from '../components/AnswerProvenance'
import {QuestionActions} from '../components/QuestionDiscussion'
import {AnswerOptions,AnswerLayoutControl} from '../components/AnswerLayout'
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import {loadPaperWorkspace,matchesPaperSearch,paperLearningSubjects,printedQuestionLabel,sourcePageUrl} from '../lib/paperWorkspace'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getCollection, getPaperReadiness, listPaperQuestions, submitAnswer, type AnswerResult, type CollectionDetail, type PaperQuestion } from '../lib/api'
import { SourceQuestionContext, SourceQuestionText } from '../components/SourceQuestionText'
import {paperDuplicateGroups,paperPresentationItems} from '../lib/paperDuplicates'

const PaperPdf=lazy(()=>import('../components/PaperPdf'))
const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
const PAGE_SIZE = 30

export default function PaperViewer() {
  const { id = '' } = useParams()
  const [search,setSearch] = useSearchParams()
  const paperId = search.get('paper') || ''
  const [readiness,setReadiness]=useState<PaperReadiness|null>(null),[readinessError,setReadinessError]=useState('')
  const [collection,setCollection]=useState<CollectionDetail|null>(null)
  const [items,setItems]=useState<PaperQuestion[]>([])
  const [total,setTotal]=useState(0),[practiceCount,setPracticeCount]=useState(0)
  const [questionsLoading,setQuestionsLoading]=useState(true),[pageRetry,setPageRetry]=useState(0)
  const [offset,setOffset]=useState(0)
  const [viewed,setViewed]=useState<Record<string,boolean>>({})
  const [answers,setAnswers]=useState<Record<string,AnswerResult>>({})
  const [picked,setPicked]=useState<Record<string,number>>({})
  const [flags,setFlags]=useState<Set<string>>(new Set())
  const [notes,setNotes]=useState<Record<string,string>>({})
  const [showAllTranscriptions,setShowAllTranscriptions]=useState(false)
  const [error,setError]=useState<string|null>(null),[questionError,setQuestionError]=useState('')
  const [answerErrors,setAnswerErrors]=useState<Record<string,string>>({})
  const [busy,setBusy]=useState<Set<string>>(new Set()),pending=useRef(new Set<string>())
  const contentHeading=useRef<HTMLHeadingElement>(null),identity=useRef(id+':'+paperId)
  const view=['focus','source'].includes(search.get('view')||'')?search.get('view')!:'paper'
  const query=search.get('q')||'',kind=search.get('kind')||'',status=search.get('status')||'',subject=search.get('subject')||''
  const selected=search.get('appearance')||''
  function update(values:Record<string,string>){setSearch(previous=>{const next=new URLSearchParams(previous);for(const [key,value]of Object.entries(values)){if(value)next.set(key,value);else next.delete(key)}return next},{replace:true})}
  useEffect(()=>{setItems([]);setTotal(0);setPracticeCount(0);setOffset(0);setAnswers({});setViewed({});setPicked({});setFlags(new Set());setNotes({});setAnswerErrors({});setShowAllTranscriptions(false);pending.current.clear();setBusy(new Set())},[id,paperId])
  useEffect(()=>{
    let live=true;identity.current=id+':'+paperId
    setCollection(null);setError(null)
    if(!paperId){setError('Choose a paper from the exam page.');return}
    getCollection(id).then(c=>{if(live)setCollection(c)}).catch(e=>{if(live)setError(e.message)})
    return()=>{live=false;identity.current=''}
  },[id,paperId,pageRetry])
  useEffect(()=>{
    if(!paperId)return
    let live=true;const controller=new AbortController();setQuestionsLoading(true);setQuestionError('');setItems([])
    loadPaperWorkspace(offset=>listPaperQuestions(id,paperId,offset,100,controller.signal),(rows,count,practice)=>{setItems(rows);setTotal(count);setPracticeCount(practice)},()=>live)
      .catch(e=>{if(live)setQuestionError(e.message)}).finally(()=>{if(live)setQuestionsLoading(false)})
    return()=>{live=false;controller.abort()}
  },[id,paperId,pageRetry])
  useEffect(()=>{const clear=()=>{setAnswers({});setViewed({});setPicked({});setNotes({});setFlags(new Set());setAnswerErrors({})};window.addEventListener('ism-auth-change',clear);return()=>window.removeEventListener('ism-auth-change',clear)},[])
  useEffect(()=>setOffset(0),[query,kind,status,subject])
  useEffect(()=>{let live=true;setReadiness(null);setReadinessError('');if(paperId)getPaperReadiness(id,paperId).then(r=>{if(live)setReadiness(r)}).catch(e=>{if(live)setReadinessError(e.message)});return()=>{live=false}},[id,paperId,pageRetry])
  const orderedItems=useMemo(()=>{if(!readiness?.appearance_order.length)return items;const order=new Map(readiness.appearance_order.map((id,i)=>[id,i]));return [...items].sort((a,b)=>(order.get(a.appearance_id)??Number.MAX_SAFE_INTEGER)-(order.get(b.appearance_id)??Number.MAX_SAFE_INTEGER))},[items,readiness])
  const sectionLabels=useMemo(()=>new Map(Object.entries(readiness?.section_appearances||{}).flatMap(([key,ids])=>ids.map(aid=>[aid,readiness?.scheme?.paper.sections.find(s=>s.key===key)?.title||key] as const))),[readiness])
  const paper=collection?.paper_list.find(p=>p.id===paperId)
  const duplicateGroups=useMemo(()=>paperDuplicateGroups(paperId,items),[paperId,items])
  const indexed=useMemo(()=>paperPresentationItems(orderedItems,duplicateGroups,showAllTranscriptions||status==='flagged',selected).map((q,index)=>({q,index})),[orderedItems,duplicateGroups,showAllTranscriptions,selected,status])
  const filtered=indexed.filter(({q})=>matchesPaperSearch(q,query)&&(!kind||q.type===kind)&&(!subject||paperLearningSubjects(q,id).some(s=>s.id===subject))&&(!status||(status==='flagged'?flags.has(q.appearance_id):status==='unchecked'?!answers[q.appearance_id]:status==='checked'?!!answers[q.appearance_id]:q.answer_status===status)))
  const active=filtered.find(({q})=>q.appearance_id===selected)||filtered[0]
  const activeIndex=active?filtered.indexOf(active):-1
  const safeOffset=Math.min(offset,Math.max(0,Math.floor((filtered.length-1)/PAGE_SIZE)*PAGE_SIZE))
  const shown=view==='paper'?filtered.slice(safeOffset,safeOffset+PAGE_SIZE):active?[active]:[]
  const subjects=Array.from(new Map(items.flatMap(q=>paperLearningSubjects(q,id).map(s=>[s.id,s.label] as const))).entries()).sort((a,b)=>a[1].localeCompare(b[1]))
  function focusQuestion(appearance:string,mode=view==='paper'?'focus':view){update({appearance,view:mode});requestAnimationFrame(()=>contentHeading.current?.scrollIntoView({block:'start',behavior:'auto'}))}
  function toggleFlag(appearance:string){setFlags(previous=>{const next=new Set(previous);if(next.has(appearance))next.delete(appearance);else next.add(appearance);return next})}
  async function check(q:PaperQuestion,shownIndex:number){
    const key=q.appearance_id,scope=id+':'+paperId
    if(q.held||q.key_disputed||q.answer_source==='none'||['duplicate-options','unresolved-source'].includes(q.source_defect||'')||shownIndex===undefined||answers[key]||viewed[key]||busy.has(key)||!q.option_order||pending.current.has(key))return
    setPicked(p=>({...p,[key]:shownIndex}))
    const canonicalIndex=q.option_order[shownIndex]
    if(!Number.isInteger(canonicalIndex)||canonicalIndex<0)return
    pending.current.add(key);setBusy(new Set(pending.current));setAnswerErrors(e=>({...e,[key]:''}))
    try{const result=await submitAnswer(q.id,canonicalIndex,'practice',id,paperId);if(identity.current===scope)setAnswers(a=>({...a,[key]:result}))}
    catch(e){if(identity.current===scope)setAnswerErrors(a=>({...a,[key]:(e as Error).message}))}
    finally{pending.current.delete(key);if(identity.current===scope)setBusy(new Set(pending.current))}
  }
  const control='min-h-11 min-w-0 rounded-[8px] border border-hairline bg-card px-3 py-2 text-[13px] disabled:opacity-40'
  if (error && !collection) return <div className="mx-auto max-w-3xl px-6 py-10"><p className="rounded-[12px] border border-mypick bg-mypick-soft p-4 text-mypick">{error}</p><button type="button" onClick={()=>setPageRetry(n=>n+1)} className="mt-3 min-h-11 px-3 underline">Retry paper</button><Link className="label mt-4 inline-block underline" to={`/exams/${id}`}>← Back to exam</Link></div>
  if (!collection) return <div className="mx-auto max-w-shell px-6 py-10 label">Loading paper…</div>
  if(!paper)return <div className="mx-auto max-w-3xl px-6 py-10"><p role="alert" className="rounded-[12px] border border-mypick bg-mypick-soft p-4 text-mypick">This paper is not available in this exam. Choose an available paper from the list.</p><Link to={GROUP_B_COLLECTIONS.some(group=>group===id)?groupBLink(id,'papers'):`/exams/${id}?view=papers`} className="mt-4 inline-flex min-h-11 items-center text-link underline">← Choose a paper</Link></div>

  const printedIdentity=paperIdentity(paper)
  return <main className="exam-booklet mx-auto w-full px-3 pb-24 pt-5 sm:px-4">
    <Link to={GROUP_B_COLLECTIONS.some(group=>group===id)?groupBLink(id,'papers'):`/exams/${id}?view=papers`} className="inline-flex min-h-11 items-center text-[13px] text-link">← {collection.title} · Papers</Link>
    <header className="booklet-masthead rounded-[14px] border border-hairline bg-exams-soft p-4 sm:p-6">
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-exams-dark">Original examination paper · {paper.year??'Year not listed'}</div>
      <h1 className="mt-2 max-w-5xl break-words font-display text-[clamp(26px,3vw,38px)] font-medium leading-tight">{printedIdentity.title}</h1>
      {printedIdentity.exam&&<p className="mt-3 max-w-5xl break-words text-[14px] leading-relaxed text-secondary">{printedIdentity.exam}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px] text-secondary"><span>{!questionsLoading&&!questionError&&duplicateGroups.hidden?`${duplicateGroups.printedCount} printed questions · ${items.length} stored transcriptions`:`${paper.questions.toLocaleString('en-IN')} questions${paper.descriptive>0?` · ${paper.descriptive} written`:''}`}</span>{paper.source_pdf_url&&<a href={sourcePageUrl(paper.source_pdf_url,null)} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center font-semibold text-link underline">Open original PDF ↗</a>}</div>
      {duplicateGroups.hidden>0&&<div className="mt-2 text-[12px] text-secondary"><p>{duplicateGroups.hidden} duplicate extractions of the same printed questions are grouped. Every stored record remains available.</p><button type="button" aria-pressed={showAllTranscriptions} onClick={()=>{setShowAllTranscriptions(value=>!value);setOffset(0)}} className="min-h-11 font-semibold text-link underline">{showAllTranscriptions?'Group duplicate transcriptions':'Show all stored transcriptions'}</button></div>}
      {readiness&&<details className="mt-3 rounded-lg border border-hairline bg-card p-3"><summary className="min-h-11 cursor-pointer py-2 text-[13px] font-semibold">{readiness.full_simulation_ready?'Full original-paper simulation ready':readiness.practice_eligible?'Original paper · practice subset available':'Original paper · scoring readiness'}{readiness.scheme?' · '+readiness.scheme.edition:' · scheme not confirmed'}</summary><p className="mt-2 text-[13px] text-secondary">{readiness.appearances} stored positions{readiness.expected_questions!==null?' / '+readiness.expected_questions+' expected':''} · {readiness.official_eligible} eligible official-key MCQs.</p>{readiness.scheme&&<p className="mt-2 text-[13px]">{readiness.scheme.title} · {readiness.scheme.paper.title} · {readiness.scheme.state}</p>}{readiness.instructions&&<p className="mt-2 whitespace-pre-line text-[13px]">{readiness.instructions}</p>}{readiness.blockers.map(b=><p key={b} className="mt-1 text-[12px] text-secondary">• {b}</p>)}{readiness.full_simulation_ready&&paper.allow_timed_test&&<Link to={`/exams/${id}/mock?paper=${encodeURIComponent(paper.id)}&simulation=full`} className={control+' mt-3 inline-flex items-center'}>Start full original-paper simulation →</Link>}</details>}{readinessError&&<p className="mt-2 text-[12px] text-secondary">Paper readiness could not load. <button className="min-h-11 underline" onClick={()=>setPageRetry(n=>n+1)}>Retry readiness</button></p>}
      <details className="mt-2 border-t border-hairline pt-1"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Instructions, answer coverage &amp; timed practice</summary>
        <p className="mb-3 text-[14px] font-semibold">{paper.paper_label||paper.title}</p>
        {paper.instructions?<section aria-label="Paper instructions" className="mt-2 rounded-[10px] border border-hairline bg-card p-4"><h2 className="font-semibold text-[13px]">Paper instructions</h2><p className="mt-2 whitespace-pre-line text-[13px] leading-relaxed text-secondary">{paper.instructions}</p></section>:<p className="text-[13px] text-secondary">Read the original PDF for printed instructions; a complete instruction transcript is not available here.</p>}
        <p className="mt-3 break-words text-[12px] text-secondary">{paper.title} · {paper.id.split('/').pop()}</p>
        <p className="mt-3 text-[13px] text-secondary">{paper.scorable} eligible official-key MCQs · {paper.verified_solutions} verified unofficial solutions · {paper.needs_review} need review · {paper.missing_explanations} without explanations.</p>
        <div className="mt-3 flex flex-wrap gap-2">{paper.allow_timed_test&&paper.scorable>=20&&<Link to={`/exams/${id}/mock?paper=${encodeURIComponent(paper.id)}`} className={control+' border-ink bg-ink text-paper'}>Timed key practice · {paper.scorable}</Link>}{paper.allow_practice&&practiceCount>0&&<Link to={`/exams/${id}/mock?paper=${encodeURIComponent(paper.id)}&mode=derived`} className={control}>Reviewed estimate · {practiceCount}</Link>}</div>
        <p className="mt-3 text-[12px] text-secondary">Timed sets use eligible MCQs, not every printed question. Reviewed estimates can include verified unofficial solutions; they are not official exam scores. Written questions remain available to read.</p>
        {paper.rule_source==='platform-default'&&<p className="mt-2 text-[12px] text-secondary">Original timing and marks are not confirmed; timed sets use practice rules.</p>}
      </details>
    </header>
    <section aria-label="Explore this paper" className="booklet-tools mt-4 rounded-[14px] border border-hairline bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><div role="group" aria-label="Paper view" className="flex flex-wrap gap-2">{[['paper','Paper'],['focus','Focus'],['source','Question + PDF']].map(([value,label])=><button key={value} type="button" aria-pressed={view===value} disabled={value==='source'&&!paper.source_pdf_url} onClick={()=>update({view:value})} className={control+(view===value?' border-ink bg-ink text-paper':'')}>{label}</button>)}</div><p className="text-[12px] text-secondary">This visit: {Object.keys(answers).length} checked · {flags.size} flagged</p></div>
      <details className="booklet-filters" open={!!(query||kind||status)}><summary>Search &amp; filter questions{(query||kind||status)?' · filters active':''}</summary><div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-[minmax(240px,1fr)_180px_210px]"><label className="col-span-2 min-w-0 text-[12px] font-semibold md:col-span-1">Search this paper<input aria-label="Search this paper" type="search" value={query} maxLength={200} onChange={e=>update({q:e.target.value})} placeholder="Words, a phrase or Q73" className={control+' mt-1 w-full'}/></label><label className="min-w-0 text-[12px] font-semibold">Question type<select aria-label="Question type" value={kind} onChange={e=>update({kind:e.target.value})} className={control+' mt-1 w-full'}><option value="">All types</option><option value="mcq">Multiple choice</option><option value="descriptive">Written questions</option></select></label><label className="min-w-0 text-[12px] font-semibold">Show<select aria-label="Paper question filter" value={status} onChange={e=>update({status:e.target.value})} className={control+' mt-1 w-full'}>{[['','All questions'],['flagged','Flagged this visit'],['unchecked','Not checked this visit'],['checked','Checked this visit'],['official','Official keys'],['verified','Verified solutions'],['needs-review','Needs review'],['unsolved','No answer recorded']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label></div></details>
      <div className="mt-3 flex flex-wrap items-center gap-3"><details className="min-w-0 flex-1"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Question map{subject?' · subject filtered':''}</summary><label className="block max-w-sm text-[12px] font-semibold">Learning subject<select aria-label="Paper learning subject" value={subject} onChange={e=>update({subject:e.target.value})} className={control+' my-2 w-full'}><option value="">All subjects</option>{subject&&!subjects.some(([id])=>id===subject)&&<option value={subject}>{subject}</option>}{subjects.map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label><p className="mb-2 text-[12px] text-secondary">Jump to a printed question. ✓ Checked · ⚑ Flagged. Search and filters also narrow this map.</p><nav aria-label="Printed question map" className="flex max-h-64 flex-wrap gap-2 overflow-y-auto py-1">{filtered.map(({q,index})=><button type="button" key={q.appearance_id} aria-label={'Go to '+printedQuestionLabel(q,index)+(q.page?' · PDF page '+q.page:'')} aria-current={active?.q.appearance_id===q.appearance_id?'true':undefined} onClick={()=>focusQuestion(q.appearance_id)} className={control+' min-w-12 '+(selected===q.appearance_id?'border-ink bg-paper':'')}>{printedQuestionLabel(q,index)}{answers[q.appearance_id]?' ✓':''}{flags.has(q.appearance_id)?' ⚑':''}</button>)}</nav></details>{(query||kind||status||subject)&&<button type="button" onClick={()=>update({q:'',kind:'',status:'',subject:''})} className="min-h-11 text-[13px] font-semibold text-link underline">Clear filters</button>}<button type="button" disabled={!filtered.some(({q})=>q.type==='mcq'&&!answers[q.appearance_id])} onClick={()=>{const ordered=[...filtered.slice(activeIndex+1),...filtered.slice(0,activeIndex+1)];const next=ordered.find(({q})=>q.type==='mcq'&&!answers[q.appearance_id]);if(next)focusQuestion(next.q.appearance_id)}} className={control}>Next unchecked →</button></div>
    </section>
    {questionError&&<p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">The complete paper could not load: {questionError}. Search currently covers {items.length} loaded questions. <button type="button" onClick={()=>setPageRetry(n=>n+1)} className="min-h-11 font-semibold underline">Retry paper</button></p>}
    <div className="booklet-section-heading mb-3 mt-5 flex flex-wrap items-center justify-between gap-3"><h2 ref={contentHeading} tabIndex={-1} className="scroll-mt-40 font-display text-[23px] outline-none">{query||kind||status||subject?'Matching questions':showAllTranscriptions?'Stored transcriptions':'Printed questions'}</h2><p role="status" className="text-[12px] text-secondary">{questionsLoading?`Loading paper · ${items.length} questions ready…`:duplicateGroups.hidden?`${filtered.length} shown · ${duplicateGroups.printedCount} printed · ${total} stored`:`${filtered.length} of ${total} questions`}</p></div>
    {view!=='paper'&&active&&<nav aria-label="Focus question navigation" className="mb-3 flex flex-wrap items-center justify-between gap-2"><button type="button" disabled={activeIndex<=0} onClick={()=>focusQuestion(filtered[activeIndex-1].q.appearance_id)} className={control}>← Previous question</button><span className="text-[12px] text-secondary">{activeIndex+1} / {filtered.length} · {printedQuestionLabel(active.q,active.index)}</span><button type="button" disabled={activeIndex+1>=filtered.length} onClick={()=>focusQuestion(filtered[activeIndex+1].q.appearance_id)} className={control}>Next question →</button></nav>}
    <div className={view==='source'?'grid items-start gap-4 lg:grid-cols-2':'mx-auto max-w-4xl'}>
    <section aria-label="Paper questions" className="min-w-0 space-y-4">
      <AnswerLayoutControl/>
      {!questionsLoading&&filtered.length===0&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-secondary">{items.length?'No questions match. Try another phrase or clear the filters.':'No transcribed questions are available. Use the original PDF above.'}</p>}
      {shown.map(({q,index}) => {

        const blocked = q.held || q.key_disputed || ['duplicate-options','unresolved-source'].includes(q.source_defect || '')
        const result = answers[q.appearance_id]
        const correctShown = result && q.option_order ? q.option_order.indexOf(result.answer_index) : -1
        return <article key={q.appearance_id} className="exam-sheet min-w-0 rounded-[14px] border border-hairline bg-card p-4 sm:p-5">
          <div className="sheet-metadata flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] text-muted">{sectionLabels.has(q.appearance_id)&&<span className="font-semibold">{sectionLabels.get(q.appearance_id)}</span>}<span>{q.type==='mcq'?'MCQ':'Written question'}</span><span>{printedQuestionLabel(q,index)} · {q.page?'PDF page '+q.page:'PDF page not mapped'}{q.marks!==null?' · '+q.marks+' marks':''}</span><AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.id}/>{paper.source_pdf_url && <a href={sourcePageUrl(paper.source_pdf_url,q.page)} target="_blank" rel="noreferrer" className="font-semibold text-exams-dark underline underline-offset-2">Source PDF ↗</a>}</div>
          <div className="sheet-actions mt-2 flex flex-wrap gap-3"><button type="button" aria-pressed={flags.has(q.appearance_id)} onClick={()=>toggleFlag(q.appearance_id)} className="min-h-11 text-[12px] font-semibold text-link">{flags.has(q.appearance_id)?'⚑ Flagged · remove':'⚑ Flag to revisit'}</button>{paper.source_pdf_url&&view!=='source'&&<button type="button" onClick={()=>focusQuestion(q.appearance_id,'source')} className="min-h-11 text-[12px] font-semibold text-link underline">View beside PDF</button>}</div>
          {blocked && <p role="note" className="mt-3 rounded-[8px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">Source issue — excluded from scoring. {q.dispute_note || 'The printed question needs clarification before a reliable answer can be scored.'}</p>}
          <div className="mt-3"><SourceQuestionContext direction={q.direction} passage={q.passage} /></div>
          <h2 className="sheet-question mt-2 font-display text-[21px] leading-snug"><SourceQuestionText instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup ?? q.question} /></h2>
          {q.figure_image_url && <a href={q.figure_image_url} target="_blank" rel="noreferrer" className="mt-3 block max-w-2xl overflow-hidden rounded-[9px] border border-hairline bg-paper" aria-label="Open original question figure"><img src={q.figure_image_url} loading="lazy" decoding="async" alt={`Original source figure for question ${q.qnum ?? ''}`} className="max-h-[360px] w-full object-contain" /><span className="block border-t border-hairline px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-muted">Original source figure · open full image ↗</span></a>}
          {!!q.options.length && <AnswerOptions as="ol" className="mt-4">
            {q.options.map((option, i) => {
              const correct = result && i === correctShown
              const wrong = result && picked[q.appearance_id] === i && !result.correct
              return <li key={i}><button type="button" disabled={blocked || !q.option_order || q.answer_source==='none' || !!result || viewed[q.appearance_id] || busy.has(q.appearance_id) || option == null} onClick={() => void check(q,i)} aria-pressed={picked[q.appearance_id]===i} data-answer-state={correct?'correct':wrong?'wrong':picked[q.appearance_id]===i?'selected':'neutral'} className={`answer-option flex w-full items-start gap-3 rounded-[8px] border p-3 text-left text-[14px] ${correct ? 'border-correct bg-correct-soft' : wrong ? 'border-wrong bg-wrong-soft' : picked[q.appearance_id] === i ? 'border-ink bg-paper' : 'border-hairline bg-card'}`}><span className="font-mono">{LETTERS[i]}</span><span>{option == null ? 'Option unavailable in source' : <SourceQuestionText text={q.options_markup?.[i] ?? option} />}{correct&&<small className="option-outcome">{picked[q.appearance_id]===i?'Correct':'Answer'}</small>}{wrong&&<small className="option-outcome">Your pick</small>}</span></button></li>
            })}
          </AnswerOptions>}
          {answerErrors[q.appearance_id]&&<p role="alert" className="mt-3 text-[13px] text-mypick">{answerErrors[q.appearance_id]}</p>}
          {q.type==='mcq'&&!q.option_order&&<p className="mt-3 text-[12px] text-secondary">Printed options are available to read; reliable answer mapping is not available for this appearance.</p>}
          {q.type==='descriptive'&&<p className="mt-3 text-[12px] text-secondary">Written response · use the original instructions. This question is not automatically scored.</p>}
          {duplicateGroups.representative.has(q.appearance_id)&&<p className="mt-3 text-[12px] text-secondary">Duplicate extraction of this printed question. <button type="button" onClick={()=>focusQuestion(duplicateGroups.representative.get(q.appearance_id)!)} className="min-h-11 font-semibold text-link underline">Open grouped transcription</button></p>}
          {q.type==='mcq'&&<PracticeAnswerPanel options={q.options} showNext={view!=='paper'} key={paperId+':'+q.appearance_id} qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={paperId} year={q.year ?? paper.year} available={!blocked&&q.answer_source!=='none'} disabled={busy.has(q.appearance_id)} onBusy={value=>setBusy(old=>{const next=new Set(old);if(value)next.add(q.appearance_id);else next.delete(q.appearance_id);return next})} onViewed={value=>setViewed(old=>({...old,[q.appearance_id]:value}))} onRetry={()=>{setPicked(old=>{const next={...old};delete next[q.appearance_id];return next});setAnswers(old=>{const next={...old};delete next[q.appearance_id];return next})}} onNext={()=>{const position=filtered.findIndex(item=>item.q.appearance_id===q.appearance_id),next=filtered[position+1];if(next)focusQuestion(next.q.appearance_id,'focus');else setAnswerErrors(old=>({...old,[q.appearance_id]:'You reached the end of these paper results.'}))}}/>}
          <details className="mt-4 border-t border-hairline pt-1"><summary className="min-h-11 cursor-pointer py-3 text-[12px] font-semibold">Scratchpad · this visit only</summary><label className="text-[12px] text-secondary">Working for {printedQuestionLabel(q,index)}<textarea aria-label={'Scratchpad for '+printedQuestionLabel(q,index)} maxLength={20000} rows={5} value={notes[q.appearance_id]||''} onChange={e=>setNotes(n=>({...n,[q.appearance_id]:e.target.value}))} placeholder="Work through calculations or outline a written answer…" className="mt-2 w-full rounded-[8px] border border-hairline bg-paper p-3 text-[14px] text-ink"/></label><p className="mt-1 text-[12px] text-secondary">Kept while this paper is open. Copy your work before leaving or reloading.</p></details>
          <QuestionActions questionType={q.type} qid={q.id} context={{paper_id:paperId,collection_id:id}} answeredSignal={result}/>
        </article>
      })}
    </section>
    {view==='source'&&paper.source_pdf_url&&<aside aria-label="Original PDF alongside question" className="order-first min-w-0 rounded-[14px] border border-hairline bg-card p-3 lg:sticky lg:top-40 lg:order-last"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-semibold text-[13px]">Original PDF{active?.q.page?' · page '+active.q.page:''}</h2><a href={sourcePageUrl(paper.source_pdf_url,active?.q.page??null)} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center text-[12px] font-semibold text-link underline">Open full PDF ↗</a></div><p className="mb-3 text-[12px] text-secondary">{active?.q.page?'Follows the selected question’s recorded PDF page. PDF page numbers can differ from printed page labels.':'This question has no mapped PDF page. Locate it in the original document.'}</p><Suspense fallback={<p className="p-4 text-[13px]">Loading PDF reader…</p>}><PaperPdf url={paper.source_pdf_url} questionPage={active?.q.page??null} questionId={active?.q.appearance_id||''}/></Suspense><p className="mt-2 text-[12px] text-secondary">Read the original page, zoom in or turn pages here. Open the full PDF for download or printing.</p></aside>}
    </div>
    {view==='paper'&&filtered.length>0&&<nav aria-label="Paper question pages" className="mx-auto mt-5 flex max-w-4xl items-center justify-between gap-3"><button type="button" disabled={safeOffset===0} onClick={()=>{setOffset(Math.max(0,safeOffset-PAGE_SIZE));contentHeading.current?.scrollIntoView({block:'start'})}} className={control}>← Previous</button><span className="text-[12px] text-secondary">{safeOffset+1}–{Math.min(safeOffset+PAGE_SIZE,filtered.length)} / {filtered.length}</span><button type="button" disabled={safeOffset+PAGE_SIZE>=filtered.length} onClick={()=>{setOffset(safeOffset+PAGE_SIZE);contentHeading.current?.scrollIntoView({block:'start'})}} className={control}>Next →</button></nav>}
    <p className="mx-auto mt-5 max-w-4xl text-[12px] leading-relaxed text-secondary">The PDF is the original paper. This workspace is a transcription for study; use Report an issue for any differences. Flags and scratchpad notes last for this visit; checked answers use the existing practice history.</p>
  </main>
}
