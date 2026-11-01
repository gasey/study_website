import PracticeAnswerPanel from '../components/PracticeAnswerPanel'
import {questionQueryString} from '../lib/requestCache'
import {questionTopicLabel} from '../lib/questionLabels'
import {savePracticePosition} from '../lib/learning'
import Pagination from '../components/Pagination'
import {scrollToResults} from '../lib/pagination'
import AnswerProvenance from '../components/AnswerProvenance'
import {QuestionActions} from '../components/QuestionDiscussion'
import {AnswerOptions,AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams,Link } from 'react-router-dom'
import { SourceQuestionContext,SourceQuestionText } from '../components/SourceQuestionText'
import {reviewRequest} from '../lib/review'
import { getAccountSession,getExamStudyTopics,getMistakes, getProgress, listQuestions, prefetchQuestionPage, submitAnswer, type GroupBStudyArea, type AnswerResult, type CollectionPaper, type CollectionSection, type ExamStudyTopics, type Mistake, type Progress, type Question } from '../lib/api'

const LETTERS = ['A','B','C','D','E','F','G','H','I','J']

export function ModuleQuestionBrowser({ collectionId, papers, sections, initialSectionPath = '', initialPool = 'all', studyArea, sourceCollections, metadataLoading=false, collectionTitle }: { metadataLoading?:boolean;collectionTitle?:string;studyArea?: GroupBStudyArea; sourceCollections?:Record<string,string>; collectionId: string; papers: CollectionPaper[]; sections: CollectionSection[]; initialSectionPath?: string; initialPool?: 'all'|'scorable'|'practice' }) {
  const [urlParams,setURLParams]=useSearchParams()
  const combined = collectionId === 'combined-prelims'
  const practice=urlParams.get('view')==='practice',PAGE_SIZE=practice?1:25
  const [reload,setReload]=useState(0),[loading,setLoading]=useState(true)
  const [primaryFiltersOpen,setPrimaryFiltersOpen]=useState(false)
  const search=urlParams.get('q')||'',paperId=urlParams.get('paper')||'',sectionPath=urlParams.get('section')||initialSectionPath
  const subjectId=urlParams.get('subject_id')||'',topicId=urlParams.get('topic_id')||'',subtopicId=urlParams.get('subtopic_id')||''
  const pool:'all'|'scorable'|'practice'=['all','scorable','practice'].includes(urlParams.get('pool')||'')?urlParams.get('pool') as 'all'|'scorable'|'practice':initialPool
  const studyStatus:'all'|'unseen'|'answered'|'wrong'=['all','unseen','answered','wrong'].includes(urlParams.get('status')||'')?urlParams.get('status') as 'all'|'unseen'|'answered'|'wrong':'all'
  const answerStatus=(['official','verified','needs-review','unsolved','written'].includes(urlParams.get('answer_status')||'')?urlParams.get('answer_status'):undefined) as 'official'|'verified'|'needs-review'|'unsolved'|'written'|undefined
  const offset=Math.floor(Math.max(0,Math.min(100000,Number(urlParams.get('offset'))||0))/PAGE_SIZE)*PAGE_SIZE
  function filter(key:string,value:string){setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);if(key!=='offset')next.delete('offset');return next},{replace:key!=='offset'})}
  const setSearch=(v:string)=>filter('q',v),setPaperId=(v:string)=>filter('paper',v),setSectionPath=(v:string)=>filter('section',v),setPool=(v:typeof pool)=>filter('pool',v),setStudyStatus=(v:typeof studyStatus)=>filter('status',v),setOffset=(v:number)=>filter('offset',String(v))
  const [taxonomy,setTaxonomy]=useState<ExamStudyTopics|null>(null)
  useEffect(()=>{let live=true;getExamStudyTopics(collectionId,studyArea).then(value=>{if(live)setTaxonomy(value)}).catch(()=>{});return()=>{live=false}},[collectionId,studyArea])
  const selectedSubject=taxonomy?.subjects.find(subject=>subject.id===subjectId)
  const selectedTopic=selectedSubject?.topics.find(topic=>topic.id===topicId)
  function taxonomyFilter(key:'subject_id'|'topic_id'|'subtopic_id',value:string){
    setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);if(key==='subject_id'){next.delete('topic_id');next.delete('subtopic_id')}if(key==='topic_id')next.delete('subtopic_id');next.delete('offset');return next},{replace:true})
    setResults({});setPicks({})
  }
  const requestKey=questionQueryString({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q:search.trim()||undefined,answer_status:answerStatus,pool,study_status:studyStatus,limit:PAGE_SIZE,offset})
  const [resolvedKey,setResolvedKey]=useState('')
  const pending=loading||resolvedKey!==requestKey
  function resetFilters(){
    setURLParams(previous=>{const next=new URLSearchParams(previous);for(const key of ['subject_id','topic_id','subtopic_id','section','paper','pool','status','answer_status','q','offset'])next.delete(key);return next},{replace:true})
    setResults({});setPicks({})
  }
  const [page, setPage] = useState<{items: Question[];total: number}|null>(null)
  const [picks, setPicks] = useState<Record<string,number>>({})
  const [viewed,setViewed]=useState<Record<string,boolean>>({})
  const [answerBusy,setAnswerBusy]=useState<Record<string,boolean>>({})
  const checking=useRef(new Set<string>())
  const [results, setResults] = useState<Record<string,AnswerResult>>({})
  const [error, setError] = useState<string|null>(null)
  const [account,setAccount]=useState(false);const [checkpointError,setCheckpointError]=useState('');const saveQueue=useRef(Promise.resolve())
  useEffect(()=>{let live=true;getAccountSession().then(s=>{if(live)setAccount(s.authenticated)}).catch(()=>{});return()=>{live=false}},[])
  useEffect(()=>{if(!account||!page||pending)return;const timer=window.setTimeout(()=>{saveQueue.current=saveQueue.current.then(async()=>{try{if(studyArea){if(page.items[0])await savePracticePosition(page.items[0].id)}else await reviewRequest('/me/exam-checkpoint/'+collectionId,{section:sectionPath,paper:paperId,q:search,pool,status:studyStatus,subject_id:subjectId,topic_id:topicId,subtopic_id:subtopicId,offset});setCheckpointError('');window.dispatchEvent(new Event('ism-study-checkpoint'))}catch(e){setCheckpointError((e as Error).message)}})},700);return()=>window.clearTimeout(timer)},[account,page,pending,studyArea,collectionId,sectionPath,paperId,search,pool,studyStatus,subjectId,topicId,subtopicId,offset])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    let prefetchTimer:number|undefined
    const timer = window.setTimeout(() => {
      if(search.trim().length===1){setPage({items:[],total:0});setResolvedKey(requestKey);setError('Enter at least two characters to search.');setLoading(false);return}
      setError(null)
      listQuestions({study_area:studyArea,collection_id: collectionId,section_path: sectionPath || undefined,paper_id: paperId || undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q: search.trim() || undefined,answer_status:answerStatus,pool,study_status: studyStatus,limit: PAGE_SIZE,offset})
        .then((value) => { if (!cancelled) {
          const last=Math.max(0,(Math.ceil(value.total/PAGE_SIZE)-1)*PAGE_SIZE)
          if(offset>last){setURLParams(previous=>{const next=new URLSearchParams(previous);if(last)next.set('offset',String(last));else next.delete('offset');return next},{replace:true});return}
          setPage(value);setResolvedKey(requestKey);setError(null)
          if(offset+PAGE_SIZE<value.total)prefetchTimer=window.setTimeout(()=>prefetchQuestionPage({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q:search.trim()||undefined,answer_status:answerStatus,pool,study_status:studyStatus,limit:PAGE_SIZE,offset:offset+PAGE_SIZE}),250)
        } })
        .catch((e) => { if (!cancelled) setError(e.message) })
        .finally(()=>{if(!cancelled)setLoading(false)})
    }, search.trim() ? 250 : 0)
    return () => { cancelled = true; window.clearTimeout(timer);if(prefetchTimer!==undefined)window.clearTimeout(prefetchTimer) }
  }, [studyArea,collectionId,sectionPath,paperId,subjectId,topicId,subtopicId,search,pool,studyStatus,answerStatus,offset,PAGE_SIZE,reload])

  const currentPage=Math.floor(offset/PAGE_SIZE)+1,pages=Math.max(1,Math.ceil((page?.total||0)/PAGE_SIZE))
  function goPage(value:number){
    // Answering changes membership of personal queues. Refresh this position so
    // advancing cannot skip the next unseen question after the current one leaves.
    const current=page?.items[0],result=current&&results[current.id]
    if(practice&&value===currentPage+1&&result&&(studyStatus==='unseen'||(studyStatus==='wrong'&&result.correct))){setReload(n=>n+1)}
    else setOffset((value-1)*PAGE_SIZE)
    requestAnimationFrame(()=>scrollToResults('exam-question-browser'))
  }
  function update<T>(setter: (value:T)=>void, value:T) { setter(value); setResults({}); setPicks({}) }
  // Selection is provisional until Check answer.
  async function answer(q: Question, index: number) {
    if (pending || q.held || results[q.id] || viewed[q.id] || answerBusy[q.id] || checking.current.has(q.id) || q.answer_source === 'none' || q.key_disputed || ['duplicate-options','unresolved-source'].includes(q.source_defect||'')) return
    checking.current.add(q.id);setAnswerBusy(old=>({...old,[q.id]:true}))
    try {
      const actualPaper=paperId||((studyArea||['udc','ldc','assistant'].includes(collectionId))?q.source_appearance?.paper_id:undefined)
      const actualCollection=sourceCollections?.[actualPaper||'']||collectionId
      const result = await submitAnswer(q.id,index,'practice',actualCollection==='group-b'?undefined:actualCollection,actualPaper,sectionPath || undefined)
      setResults((old) => ({...old,[q.id]:result}))
    } catch (e) {
      setPicks((old) => { const next={...old}; delete next[q.id]; return next })
      setError((e as Error).message)
    } finally {checking.current.delete(q.id);setAnswerBusy(old=>({...old,[q.id]:false}))}
  }

  return <section id="exam-question-browser" tabIndex={-1} aria-busy={pending} className="mt-6 scroll-mt-28 focus:outline-none">
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-display text-[22px]">{practice?'Study practice':'Browse questions'}</h2><p className="text-[12px] text-secondary">{collectionTitle||'This exam'}{selectedSubject?' · '+selectedSubject.title:''}{selectedTopic?' · '+selectedTopic.title:''}</p></div><button type="button" onClick={resetFilters} className="min-h-11 rounded-pill border border-hairline px-4 text-[12px] font-semibold">Reset filters</button></div>
    <button type="button" aria-expanded={primaryFiltersOpen} aria-controls="exam-primary-filters" onClick={()=>setPrimaryFiltersOpen(open=>!open)} className="mb-2 min-h-11 rounded-pill border border-hairline bg-card px-4 text-[12px] font-semibold sm:hidden">{primaryFiltersOpen?'Hide subject filters':'Subject, topic & search'}</button>
    <div id="exam-primary-filters" className={`${primaryFiltersOpen?'grid':'hidden sm:grid'} mb-3 gap-3 rounded-[14px] border border-hairline bg-card p-4 sm:grid-cols-3`}>
      <label className="text-[12px] font-semibold">Subject<select value={subjectId} onChange={e=>taxonomyFilter('subject_id',e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All subjects</option>{subjectId&&!selectedSubject&&<option value={subjectId}>Selected subject</option>}{taxonomy?.subjects.map(subject=><option key={subject.id} value={subject.id}>{subject.title} · {subject.questions}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Topic<select value={topicId} onChange={e=>taxonomyFilter('topic_id',e.target.value)} disabled={!subjectId} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px] disabled:opacity-60"><option value="">All topics</option>{selectedSubject?.topics.map(topic=><option key={topic.id} value={topic.id}>{topic.title} · {topic.questions}</option>)}</select></label>

      <label className="text-[12px] font-semibold">Search<input maxLength={120} value={search} onChange={(e)=>update(setSearch,e.target.value)} placeholder="Question or option text" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]" /></label>
    </div>
    {subjectId==='gk-gs'&&topicId==='gk-gs:science'&&selectedTopic&&<nav aria-label="Science branches" className="mb-3 flex flex-wrap items-center gap-2">
      <span className="mr-1 text-[12px] font-semibold text-secondary">Science:</span>
      {[{id:'',title:'All Science'},...selectedTopic.subtopics].map(branch=><button key={branch.id} type="button" aria-pressed={subtopicId===branch.id} onClick={()=>taxonomyFilter('subtopic_id',branch.id)} className={`min-h-11 rounded-pill border px-4 text-[12px] font-semibold ${subtopicId===branch.id?'border-ink bg-ink text-paper':'border-hairline bg-card'}`}>{branch.title}</button>)}
    </nav>}
    <details className="rounded-[12px] border border-hairline bg-card px-3 py-1">
      <summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">More filters &amp; answer layout{[paperId&&'paper',sectionPath&&'section',subtopicId&&'subtopic',answerStatus&&answerStatus,studyStatus!=='all'&&studyStatus,pool!==initialPool&&pool].filter(Boolean).length?` · ${[paperId&&'paper selected',sectionPath&&'section selected',subtopicId&&'subtopic selected',answerStatus,studyStatus!=='all'&&studyStatus,pool!==initialPool&&pool].filter(Boolean).join(' · ')}`:''}</summary>
    <nav aria-label="Answer verification lists" className="mb-4 flex flex-wrap gap-2">{[['','All questions'],['needs-review','Needs review'],['verified','Verified solutions'],['official','Official keys'],['unsolved','No answer yet']].map(([value,label])=><button type="button" key={value} aria-pressed={(answerStatus||'')===value} onClick={()=>setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set('answer_status',value);else next.delete('answer_status');next.set('pool','all');next.delete('offset');return next},{replace:true})} className={'min-h-11 rounded-pill border px-4 text-[13px] '+((answerStatus||'')===value?'border-ink bg-ink text-paper':'border-hairline bg-card')}>{label}</button>)}</nav>
    <AnswerLayoutControl/>
    <div className={`${combined?'cp-filters':'grid gap-3 rounded-[14px] border border-hairline bg-card p-4 sm:grid-cols-2 lg:grid-cols-5'}`}>
      <label className="text-[12px] font-semibold">Subtopic<select value={subtopicId} onChange={e=>taxonomyFilter('subtopic_id',e.target.value)} disabled={!topicId} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px] disabled:opacity-60"><option value="">All subtopics</option>{selectedTopic?.subtopics.map(subtopic=><option key={subtopic.id} value={subtopic.id}>{subtopic.title} · {subtopic.questions}</option>)}</select></label>
      <label hidden={!!studyArea} className="text-[12px] font-semibold">Section<select disabled={metadataLoading} value={sectionPath} onChange={(e)=>update(setSectionPath,e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All sections</option>{sections.map((s)=><option key={s.path} value={s.path}>{s.title}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Paper<select disabled={metadataLoading} value={paperId} onChange={(e)=>update(setPaperId,e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All papers</option>{paperId&&!papers.some(p=>p.id===paperId)&&<option value={paperId}>Selected paper · loading details</option>}{papers.map((p)=><option key={p.id} value={p.id}>{p.year?`${p.year} · `:''}{p.id.split('/').pop()?.replace(/\.pdf$/i,'')||p.title}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Answer pool<select value={pool} onChange={(e)=>update(setPool,e.target.value as typeof pool)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="all">All questions</option><option value="scorable">Verified keys only</option><option value="practice">Questions with an answer</option></select></label>
      <label className="text-[12px] font-semibold">My status<select value={studyStatus} onChange={(e)=>update(setStudyStatus,e.target.value as typeof studyStatus)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="all">All</option><option value="unseen">Not practised</option><option value="answered">Practised</option><option value="wrong">Last answer wrong</option></select></label>

    </div>
    </details>
    <div className="mt-4 flex justify-between text-[13px] text-secondary"><span>{!pending&&page ? `${page.total.toLocaleString('en-IN')} questions` : page?'Updating questions…':'Loading questions…'}</span>{!pending&&page && <span>{page.total ? offset+1 : 0}–{Math.min(offset+page.items.length,page.total)} of {page.total}</span>}</div>
    {error && <p role="alert" className="mt-3 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error} <button type="button" onClick={()=>setReload(n=>n+1)} className="underline">Retry</button></p>}
    {metadataLoading&&<p role="status" className="mt-2 text-[12px] text-muted">Paper details are loading. You can start with the available questions.</p>}
    {checkpointError&&<p role="status" className="mt-2 text-[12px] text-mypick">Could not save your place: {checkpointError}</p>}
    {practice&&<p className="mt-3 text-[12px] text-secondary">Choose an option, then Check answer. Show answer opens reading mode.</p>}
    {page&&<Pagination page={currentPage} pages={pages} disabled={pending} onPageChange={goPage} label={practice?'Practice question navigator':'Exam question pages'}/>}
    {pending&&!page&&!error&&<p role="status" className="min-h-[320px] py-10 text-center text-secondary">Loading questions…</p>}
    <div className={`exam-reading-area mt-2 divide-y divide-hairline ${pending&&page?'opacity-50':''}`} data-results-current={!pending}>
      {page?.items.map((q)=>{
        const result=results[q.id]
        const blocked=q.held||q.key_disputed||['duplicate-options','unresolved-source'].includes(q.source_defect||'')
        return <article key={q.id} className={`${combined?'cp-question':'udc-question-card'} py-5`}>
          <div className="flex flex-wrap gap-x-3 text-[11px] text-muted"><span>{q.source_appearance?.year ?? q.first_year ?? q.last_year ?? 'Year unknown'}</span><span>{q.type==='mcq'?'MCQ':'Written question'}</span><span>{questionTopicLabel(q,collectionId)}</span><AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.id}/></div>
          <SourceQuestionContext direction={q.direction} passage={q.passage}/><h3 className="mt-2 font-display text-[20px] leading-snug"><SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup||q.question}/></h3>
          {blocked&&<p className="mt-3 rounded-[8px] bg-mypick-soft p-3 text-[13px] text-mypick">Source issue · excluded from scoring. {q.dispute_note||'Check the source PDF or suggest a correction.'}</p>}
          {q.figure_image_url&&<img src={q.figure_image_url} loading="lazy" alt="Printed question figure" className="mt-3 max-h-[360px] max-w-full rounded-[8px] border border-hairline object-contain"/>}
          {q.source_appearance&&<p className="mt-2 text-[12px] text-secondary">{q.source_appearance.exam||'Source paper'}{q.source_appearance.paper_label ? ' · '+q.source_appearance.paper_label : ''}{q.source_appearance.section_label ? ' · Section: '+q.source_appearance.section_label : ''} · Q{q.source_appearance.qnum||'?'}{q.source_appearance.page?' · p. '+q.source_appearance.page:''} {q.source_appearance.source_pdf_url&&<a href={q.source_appearance.source_pdf_url+(q.source_appearance.page?'#page='+q.source_appearance.page:'')} target="_blank" rel="noreferrer" className="text-link underline">Source PDF ↗</a>}</p>}
          {!!q.options.length && <AnswerOptions className="mt-3">{q.options.map((option,i)=>{
            const correct=result?.answer_index===i
            const wrong=!!result && picks[q.id]===i && !result.correct
            return <button key={i} type="button" disabled={pending || !!result || viewed[q.id] || answerBusy[q.id] || option==null || blocked || q.answer_source==='none'} onClick={()=>setPicks(old=>({...old,[q.id]:i}))} aria-pressed={picks[q.id]===i} data-answer-state={correct?'correct':wrong?'wrong':picks[q.id]===i?'selected':'neutral'} className={`answer-option ${combined?'cp-option':'udc-option-label'} flex min-h-11 gap-2 rounded-[8px] border p-3 text-left text-[13px] disabled:cursor-default ${correct?'is-right border-correct bg-correct-soft':wrong?'is-wrong border-wrong bg-wrong-soft':picks[q.id]===i?'is-chosen border-ink bg-paper':'border-hairline bg-card'}`}><span className={`${combined?'cp-option-letter':'font-mono'}`}>{LETTERS[i]}.</span><span><SourceQuestionText text={q.options_markup?.[i]||option||'Option unavailable'}/></span></button>
          })}</AnswerOptions>}
          {q.answer_source==='none'&&<p className="mt-3 text-[12px] text-muted">This question is available to read, but no answer key is available to check yet.</p>}
          {!result&&!viewed[q.id]&&!blocked&&q.answer_source!=='none'&&q.type==='mcq'&&<button type="button" disabled={pending||picks[q.id]===undefined||answerBusy[q.id]} onClick={()=>void answer(q,picks[q.id])} className="mt-3 min-h-11 rounded-pill bg-ink px-4 py-2 text-[13px] text-paper disabled:opacity-40">{answerBusy[q.id]?'Checking…':'Check answer'}</button>}
          {q.type==='mcq'&&<PracticeAnswerPanel qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={paperId||q.source_appearance?.paper_id} year={q.source_appearance?.year ?? q.first_year ?? q.last_year} available={!blocked&&q.answer_source!=='none'} disabled={pending||answerBusy[q.id]} onBusy={v=>setAnswerBusy(old=>({...old,[q.id]:v}))} onViewed={()=>setViewed(old=>({...old,[q.id]:true}))}/>}
          <QuestionActions questionType={q.type} qid={q.id} context={{paper_id:q.source_appearance?.paper_id,collection_id:q.source_appearance?.paper_id?(sourceCollections?.[q.source_appearance.paper_id]||(collectionId==='group-b'?null:collectionId)):null}} answeredSignal={result}/>
        </article>
      })}
      {!pending&&page && !page.items.length && <div className="py-10 text-center text-[14px] text-secondary">No questions match these filters. <button type="button" onClick={resetFilters} className="min-h-11 underline">Reset filters</button></div>}
    </div>
    {page&&<Pagination page={currentPage} pages={pages} disabled={pending} onPageChange={goPage} label={practice?'Practice question navigator':'Exam question pages'}/>}
  </section>
}

export function ModuleProgressPanel({ collectionId, collectionTitle, totalScorable, totalQuestions = totalScorable }: { collectionId: string; collectionTitle: string; totalScorable: number; totalQuestions?: number }) {
  const [progress, setProgress] = useState<Progress | null>(null)
  const [mistakes, setMistakes] = useState<Mistake[]>([])
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    Promise.all([getProgress(collectionId), getMistakes(collectionId)])
      .then(([p, m]) => { if (!cancelled) { setProgress(p); setMistakes(m) } })
      .catch((e) => { if (!cancelled) setError(e.message) })
    return () => { cancelled = true }
  }, [collectionId])

  if (error) return <p role="alert" className="mt-5 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-mypick">Couldn’t load this progress yet. {error}</p>
  if (!progress) return <div className="learning-dashboard" aria-live="polite"><p className="label">Loading your {collectionTitle} progress…</p></div>

  const started = progress.answered > 0
  const coverage = totalQuestions > 0 ? Math.min(100, Math.round(progress.unique_questions / totalQuestions * 100)) : 0
  const activity = Array.from({ length: 28 }, (_, i) => {
    const day = new Date()
    day.setHours(12, 0, 0, 0)
    day.setDate(day.getDate() - (27 - i))
    const key = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`
    return { day: key, count: progress.daily_activity.find((item) => item.day === key)?.answered ?? 0 }
  })

  return <section className="learning-dashboard">
    <header className="learning-header">
      <div><p className="learning-eyebrow">Your study map · {collectionTitle}</p><h2>Your progress</h2><p className="learning-intro">A clear record of what you’ve practised in this exam, what’s going well, and where to focus next.</p></div>
      <div className="learning-storage"><span className="learning-storage-dot"/><div><strong>Progress saved automatically</strong><small>{progress.last_active_at ? `Last practice ${new Date(progress.last_active_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}` : 'This exam is ready when you are.'}</small></div></div>
    </header>

    {!started ? <section className="learning-start-panel"><div className="learning-start-icon" aria-hidden="true">↗</div><div className="learning-start-copy"><p className="learning-eyebrow">A fresh start</p><h3>Your {collectionTitle} progress starts with one question.</h3><p>Try a short practice set. Your answers, accuracy, section coverage and review list will build here automatically.</p></div><div className="learning-start-actions"><Link to={`/exams/${collectionId}?view=practice`} className="learning-primary-button">Start practice →</Link><Link to={`/exams/${collectionId}?view=papers`} className="learning-secondary-button">Choose a paper</Link></div></section> : <section className="learning-overall"><div className="learning-overall-copy"><span>Question coverage</span><strong>{progress.unique_questions.toLocaleString('en-IN')} <small>of {totalQuestions.toLocaleString('en-IN')}</small></strong></div><div className="learning-overall-meter" role="progressbar" aria-label={`${collectionTitle} question coverage`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={coverage}><span style={{ width: `${coverage}%` }} /></div><div className="learning-overall-foot"><span>{coverage}% of the question set explored</span><Link to={`/exams/${collectionId}?view=practice`}>Keep practising →</Link></div></section>}

    <div className="learning-summary-grid">{[
      ['Answer attempts', progress.answered.toLocaleString('en-IN'), `${progress.unique_questions.toLocaleString('en-IN')} distinct questions`, true],
      ['Accuracy', started ? `${progress.accuracy}%` : '—', started ? `${progress.correct.toLocaleString('en-IN')} correct answers` : 'Appears after your first answer', false],
      ['Current streak', started ? `${progress.current_streak} days` : '—', started ? 'Consecutive days with practice' : 'Build a streak with regular practice', false],
      ['Active days', `${progress.active_days_30} / 30`, 'Days with practice in the last month', false],
    ].map(([label, value, foot, primary]) => <article key={String(label)} className={`learning-summary-card ${primary ? 'learning-summary-primary' : ''}`}><span>{label}</span><strong>{value}</strong><div className="learning-summary-foot">{foot}</div></article>)}</div>

    <div className="learning-dashboard-columns">
      <section className="learning-panel">
        <div className="learning-panel-heading"><div><p className="learning-eyebrow">Progress by section</p><h3>{started ? 'Your exam sections' : 'Sections are ready to explore'}</h3><p>Practice is grouped by the sections in this exam.</p></div></div>
        {progress.sections.length ? <div className="learning-area-list">{progress.sections.map((s) => {
          const accuracy = s.accuracy
          const status = accuracy < 50 ? 'Needs review' : accuracy < 75 ? 'Building' : 'Strong'
          const sectionUrl = `/exams/${collectionId}?view=browse${s.scope_id === 'unsectioned' ? '' : `&section=${encodeURIComponent(s.scope_id)}`}`
          return <article className="learning-area-row" key={s.scope_id}><div className="learning-area-main"><div className="learning-area-title"><strong>{s.label}</strong><span className={`learning-status ${accuracy < 50 ? 'is-weak' : accuracy < 75 ? 'is-developing' : 'is-strong'}`}>{status}</span></div><div className="learning-area-meta"><span>{s.unique_questions} distinct</span><span>{s.answered} attempts</span><span>{accuracy}% accuracy</span></div><div className="learning-meter"><span style={{ width: `${accuracy}%` }} /></div></div><div className="learning-area-numbers"><span><b>{s.correct}</b><small>correct</small></span></div><Link className="learning-link-button" to={sectionUrl}>Review →</Link></article>
        })}</div> : <div className="learning-empty-state"><span aria-hidden="true">◎</span><p>{started ? 'Section details will appear as you practise questions from this exam.' : 'Answer a few questions and this view will show your activity in each section.'}</p><Link to={`/exams/${collectionId}?view=practice`}>Choose a practice set →</Link></div>}
      </section>

      <div className="learning-side-column">
        <section className="learning-panel"><div className="learning-panel-heading"><div><p className="learning-eyebrow">Last 28 days</p><h3>Practice activity</h3></div><span className="learning-status is-developing">{progress.active_days_30} active</span></div><div className="learning-activity-grid" aria-label="Daily answers over the last 28 days">{activity.map((item) => <div key={item.day} title={`${item.day}: ${item.count} answers`} aria-label={`${item.day}, ${item.count} answers`} className={`learning-activity-day ${item.count ? 'has-activity' : ''}`}><span>{item.count || ''}</span></div>)}</div><div className="learning-activity-legend"><span>Less</span>{[0, 1, 3, 6].map((level) => <i key={level} className={level ? 'has-activity' : ''} style={level ? { opacity: .25 + level * .1 } : undefined} />)}<span>More</span></div><p className="learning-panel-note">{started ? `${progress.answered.toLocaleString('en-IN')} answers recorded in this exam.` : 'Your daily activity will appear here after your first practice.'}</p></section>

        <section className="learning-panel"><div className="learning-panel-heading compact"><div><p className="learning-eyebrow">Review queue</p><h3>Questions to revisit</h3></div><span className={`learning-status ${mistakes.length ? 'is-weak' : 'is-developing'}`}>{mistakes.length} due</span></div>
          {mistakes.length ? <div className="learning-queue-list">{mistakes.slice(0, 8).map((m) => <Link className="learning-queue-row" key={m.id} to={`/bank/${m.id}`}><span><strong>{m.question}</strong><small>Missed {m.times_wrong} times · answer: {m.answer_text ?? 'not available'}</small></span><b>{m.times_wrong}</b><span className="learning-queue-arrow">›</span></Link>)}</div> : <div className="learning-queue-empty"><span aria-hidden="true">✓</span><p>{started ? 'Nothing is waiting for review right now.' : 'Missed questions will be collected here so you can revisit them later.'}</p>{!started && <Link to={`/exams/${collectionId}?view=practice`}>Start a practice set →</Link>}</div>}
        </section>
      </div>
    </div>
  </section>
}
