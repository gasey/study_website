import QuestionStudyControls from '../components/QuestionStudyControls'
import {readStudyStatus,readQuestionOrder,newQuestionSeed,nextBrowseOffset} from '../lib/questionBrowse'
import {learningSubjectTitle} from '../lib/groupBStudy'
import StudyQuestionCard from '../components/StudyQuestionCard'
import {questionQueryString} from '../lib/requestCache'
import {savePracticePosition} from '../lib/learning'
import Pagination from '../components/Pagination'
import {scrollToResults} from '../lib/pagination'
import {AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams,Link } from 'react-router-dom'
import {reviewRequest} from '../lib/review'
import { getAccountSession,getExamStudyTopics,getMistakes, getProgress, listQuestions, prefetchQuestionPage, submitAnswer, type GroupBStudyArea, type AnswerResult, type CollectionPaper, type CollectionSection, type ExamStudyTopics, type Mistake, type Progress, type Question } from '../lib/api'


export function ModuleQuestionBrowser({ collectionId, papers, sections, initialSectionPath = '', initialPool = 'all', studyArea, sourceCollections, metadataLoading=false, collectionTitle }: { metadataLoading?:boolean;collectionTitle?:string;studyArea?: GroupBStudyArea; sourceCollections?:Record<string,string>; collectionId: string; papers: CollectionPaper[]; sections: CollectionSection[]; initialSectionPath?: string; initialPool?: 'all'|'scorable'|'practice' }) {
  const [urlParams,setURLParams]=useSearchParams()
  const combined = collectionId === 'combined-prelims'
  const practice=urlParams.get('view')==='practice',PAGE_SIZE=practice?1:25
  const [reload,setReload]=useState(0),[loading,setLoading]=useState(true)
  const [primaryFiltersOpen,setPrimaryFiltersOpen]=useState(false)
  const search=urlParams.get('q')||'',paperId=urlParams.get('paper')||'',sectionPath=urlParams.get('section')||initialSectionPath
  const subjectId=urlParams.get('subject_id')||'',topicId=urlParams.get('topic_id')||'',subtopicId=urlParams.get('subtopic_id')||''
  const pool:'all'|'scorable'|'practice'=['all','scorable','practice'].includes(urlParams.get('pool')||'')?urlParams.get('pool') as 'all'|'scorable'|'practice':initialPool
  const studyStatus=readStudyStatus(urlParams.get('status')),order=readQuestionOrder(urlParams.get('order')),seed=urlParams.get('seed')||''
  useEffect(()=>{if(order==='mixed'&&!seed)setURLParams(previous=>{const next=new URLSearchParams(previous);next.set('seed',newQuestionSeed());return next},{replace:true})},[order,seed,setURLParams])
  function shuffle(){setURLParams(previous=>{const next=new URLSearchParams(previous);next.set('order','mixed');next.set('seed',newQuestionSeed());next.delete('offset');return next},{replace:true});setResults({});setPicks({})}
  const answerStatus=(['official','verified','needs-review','unsolved','written'].includes(urlParams.get('answer_status')||'')?urlParams.get('answer_status'):undefined) as 'official'|'verified'|'needs-review'|'unsolved'|'written'|undefined
  const offset=Math.floor(Math.max(0,Math.min(100000,Number(urlParams.get('offset'))||0)))
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
  const requestKey=questionQueryString({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q:search.trim()||undefined,answer_status:answerStatus,pool,order,seed,study_status:studyStatus,limit:PAGE_SIZE,offset})
  const [resolvedKey,setResolvedKey]=useState('')
  const pending=loading||resolvedKey!==requestKey||(order==='mixed'&&!seed)
  function resetFilters(){
    setURLParams(previous=>{const next=new URLSearchParams(previous);for(const key of ['subject_id','topic_id','subtopic_id','section','paper','pool','status','answer_status','q','offset','order','seed'])next.delete(key);return next},{replace:true})
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
  useEffect(()=>{let live=true;const refresh=()=>{getAccountSession().then(s=>{if(live)setAccount(s.authenticated)}).catch(()=>{});setPage(null);setResults({});setPicks({});setViewed({});setReload(n=>n+1)};refresh();window.addEventListener('ism-auth-change',refresh);return()=>{live=false;window.removeEventListener('ism-auth-change',refresh)}},[])
  useEffect(()=>{if(!account||!page||pending)return;const timer=window.setTimeout(()=>{saveQueue.current=saveQueue.current.then(async()=>{try{if(studyArea){if(page.items[0])await savePracticePosition(page.items[0].id)}else await reviewRequest('/me/exam-checkpoint/'+collectionId,{section:sectionPath,paper:paperId,q:search,pool,order,seed,status:studyStatus,subject_id:subjectId,topic_id:topicId,subtopic_id:subtopicId,offset});setCheckpointError('');window.dispatchEvent(new Event('ism-study-checkpoint'))}catch(e){setCheckpointError((e as Error).message)}})},700);return()=>window.clearTimeout(timer)},[account,page,pending,studyArea,collectionId,sectionPath,paperId,search,pool,order,seed,studyStatus,subjectId,topicId,subtopicId,offset])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    if(order==='mixed'&&!seed)return
    let prefetchTimer:number|undefined
    const timer = window.setTimeout(() => {
      if(search.trim().length===1){setPage({items:[],total:0});setResolvedKey(requestKey);setError('Enter at least two characters to search.');setLoading(false);return}
      setError(null)
      listQuestions({study_area:studyArea,collection_id: collectionId,section_path: sectionPath || undefined,paper_id: paperId || undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q: search.trim() || undefined,answer_status:answerStatus,pool,order,seed,study_status: studyStatus,limit: PAGE_SIZE,offset})
        .then((value) => { if (!cancelled) {
          const last=Math.max(0,value.total-1)
          if(offset>last){setURLParams(previous=>{const next=new URLSearchParams(previous);if(last)next.set('offset',String(Math.floor(last/PAGE_SIZE)*PAGE_SIZE));else next.delete('offset');return next},{replace:true});return}
          setPage(value);setResolvedKey(requestKey);setError(null)
          if(offset+PAGE_SIZE<value.total)prefetchTimer=window.setTimeout(()=>prefetchQuestionPage({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,q:search.trim()||undefined,answer_status:answerStatus,pool,order,seed,study_status:studyStatus,limit:PAGE_SIZE,offset:offset+PAGE_SIZE}),250)
        } })
        .catch((e) => { if (!cancelled) setError(e.message) })
        .finally(()=>{if(!cancelled)setLoading(false)})
    }, search.trim() ? 250 : 0)
    return () => { cancelled = true; window.clearTimeout(timer);if(prefetchTimer!==undefined)window.clearTimeout(prefetchTimer) }
  }, [studyArea,collectionId,sectionPath,paperId,subjectId,topicId,subtopicId,search,pool,order,seed,studyStatus,answerStatus,offset,PAGE_SIZE,reload])

  const currentPage=Math.floor(offset/PAGE_SIZE)+1,pages=Math.max(currentPage,currentPage+Math.ceil(Math.max(0,(page?.total||0)-offset-PAGE_SIZE)/PAGE_SIZE))
  function goPage(value:number){
    // Answering changes membership of personal queues. Refresh this position so
    // advancing cannot skip the next unseen question after the current one leaves.
    if(value===currentPage+1){
      const next=nextBrowseOffset(offset,PAGE_SIZE,studyStatus,page?.items.map(q=>results[q.id])||[])
      if(next===offset)setReload(n=>n+1);else setOffset(next)
    } else setOffset(Math.max(0,offset+(value-currentPage)*PAGE_SIZE))
    requestAnimationFrame(()=>scrollToResults('exam-question-browser'))
  }
  function update<T>(setter: (value:T)=>void, value:T) { setter(value); setResults({}); setPicks({}) }
  // One option tap submits through the guarded attempt path.
  async function answer(q: Question, index: number) {
    if (pending || q.held || results[q.id] || viewed[q.id] || answerBusy[q.id] || checking.current.has(q.id) || q.answer_source === 'none' || q.key_disputed || ['duplicate-options','unresolved-source'].includes(q.source_defect||'')) return
    setPicks(old=>({...old,[q.id]:index}));checking.current.add(q.id);setAnswerBusy(old=>({...old,[q.id]:true}))
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
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-display text-[22px]">{practice?'Study practice':'Browse questions'}</h2><p className="text-[12px] text-secondary">{collectionTitle||'This exam'}{selectedSubject?' · '+learningSubjectTitle(selectedSubject.id,selectedSubject.title,collectionId):''}{selectedTopic?' · '+selectedTopic.title:''}</p></div><button type="button" onClick={resetFilters} className="min-h-11 rounded-pill border border-hairline px-4 text-[12px] font-semibold">Reset filters</button></div>
    <QuestionStudyControls status={studyStatus} order={order} onStatus={value=>update(setStudyStatus,value)} onOrder={value=>filter('order',value)} onShuffle={shuffle}/>
    <button type="button" aria-expanded={primaryFiltersOpen} aria-controls="exam-primary-filters" onClick={()=>setPrimaryFiltersOpen(open=>!open)} className="mb-2 min-h-11 rounded-pill border border-hairline bg-card px-4 text-[12px] font-semibold sm:hidden">{primaryFiltersOpen?'Hide filters':'Subject, topic & search'}{[subjectId,topicId,search].filter(Boolean).length?` · ${[subjectId,topicId,search].filter(Boolean).length} active`:''}</button>
    {(subjectId||topicId||search)&&<div aria-label="Selected question filters" className="mb-2 flex flex-wrap gap-2">
      {subjectId&&<button type="button" onClick={()=>taxonomyFilter('subject_id','')} aria-label="Remove subject filter" className="min-h-11 max-w-full break-words rounded-lg border border-hairline bg-card px-3 text-left text-xs">{selectedSubject?learningSubjectTitle(selectedSubject.id,selectedSubject.title,collectionId):'Selected subject'} <span aria-hidden="true">×</span></button>}
      {topicId&&<button type="button" onClick={()=>taxonomyFilter('topic_id','')} aria-label="Remove topic filter" className="min-h-11 max-w-full break-words rounded-lg border border-hairline bg-card px-3 text-left text-xs">{selectedTopic?.title||'Selected topic'} <span aria-hidden="true">×</span></button>}
      {search&&<button type="button" onClick={()=>update(setSearch,'')} aria-label="Remove question search" className="min-h-11 max-w-full break-words rounded-lg border border-hairline bg-card px-3 text-left text-xs">Search: {search} <span aria-hidden="true">×</span></button>}
    </div>}
    <div id="exam-primary-filters" className={`${primaryFiltersOpen?'grid':'hidden sm:grid'} mb-3 gap-3 rounded-[14px] border border-hairline bg-card p-4 sm:grid-cols-3`}>
      <label className="text-[12px] font-semibold">Subject<select value={subjectId} onChange={e=>taxonomyFilter('subject_id',e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All subjects</option>{subjectId&&!selectedSubject&&<option value={subjectId}>Selected subject</option>}{taxonomy?.subjects.map(subject=><option key={subject.id} value={subject.id}>{learningSubjectTitle(subject.id,subject.title,collectionId)} · {subject.questions}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Topic<select value={topicId} onChange={e=>taxonomyFilter('topic_id',e.target.value)} disabled={!subjectId} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px] disabled:opacity-60"><option value="">All topics</option>{selectedSubject?.topics.map(topic=><option key={topic.id} value={topic.id}>{topic.title} · {topic.questions}</option>)}</select></label>

      <label className="text-[12px] font-semibold">Search<input maxLength={120} value={search} onChange={(e)=>update(setSearch,e.target.value)} placeholder="Question or option text" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]" /></label>
    </div>
    {subjectId==='gk-gs'&&topicId==='gk-gs:science'&&selectedTopic&&<nav aria-label="Science branches" className="mb-3 flex flex-wrap items-center gap-2">
      <span className="mr-1 text-[12px] font-semibold text-secondary">Science:</span>
      {[{id:'',title:'All Science'},...selectedTopic.subtopics].map(branch=><button key={branch.id} type="button" aria-pressed={subtopicId===branch.id} onClick={()=>taxonomyFilter('subtopic_id',branch.id)} className={`min-h-11 rounded-pill border px-4 text-[12px] font-semibold ${subtopicId===branch.id?'border-ink bg-ink text-paper':'border-hairline bg-card'}`}>{branch.title}</button>)}
    </nav>}
    <details className="rounded-[12px] border border-hairline bg-card px-3 py-1">
      <summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">More filters &amp; answer layout{[paperId&&'paper',sectionPath&&'section',subtopicId&&'subtopic',answerStatus&&answerStatus,pool!==initialPool&&pool].filter(Boolean).length?` · ${[paperId&&'paper selected',sectionPath&&'section selected',subtopicId&&'subtopic selected',answerStatus,pool!==initialPool&&pool].filter(Boolean).join(' · ')}`:''}</summary>
    <nav aria-label="Answer verification lists" className="mb-4 flex flex-wrap gap-2">{[['','All questions'],['needs-review','Needs review'],['verified','Verified answers'],['official','Official keys'],['unsolved','No answer yet']].map(([value,label])=><button type="button" key={value} aria-pressed={(answerStatus||'')===value} onClick={()=>setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set('answer_status',value);else next.delete('answer_status');next.set('pool','all');next.delete('offset');return next},{replace:true})} className={'min-h-11 rounded-pill border px-4 text-[13px] '+((answerStatus||'')===value?'border-ink bg-ink text-paper':'border-hairline bg-card')}>{label}</button>)}</nav>
    <AnswerLayoutControl/>
    <div className={`${combined?'cp-filters':'grid gap-3 rounded-[14px] border border-hairline bg-card p-4 sm:grid-cols-2 lg:grid-cols-5'}`}>
      <label className="text-[12px] font-semibold">Subtopic<select value={subtopicId} onChange={e=>taxonomyFilter('subtopic_id',e.target.value)} disabled={!topicId} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px] disabled:opacity-60"><option value="">All subtopics</option>{selectedTopic?.subtopics.map(subtopic=><option key={subtopic.id} value={subtopic.id}>{subtopic.title} · {subtopic.questions}</option>)}</select></label>
      <label hidden={!!studyArea} className="text-[12px] font-semibold">Section<select disabled={metadataLoading} value={sectionPath} onChange={(e)=>update(setSectionPath,e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All sections</option>{sections.map((s)=><option key={s.path} value={s.path}>{s.title}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Paper<select disabled={metadataLoading} value={paperId} onChange={(e)=>update(setPaperId,e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All papers</option>{paperId&&!papers.some(p=>p.id===paperId)&&<option value={paperId}>Selected paper · loading details</option>}{papers.map((p)=><option key={p.id} value={p.id}>{p.year?`${p.year} · `:''}{p.id.split('/').pop()?.replace(/\.pdf$/i,'')||p.title}</option>)}</select></label>
      <label className="text-[12px] font-semibold">Answer pool<select value={pool} onChange={(e)=>update(setPool,e.target.value as typeof pool)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="all">All questions</option><option value="scorable">Verified keys only</option><option value="practice">Questions with an answer</option></select></label>

    </div>
    </details>
    <div className="mt-4 flex justify-between text-[13px] text-secondary"><span>{!pending&&page ? `${page.total.toLocaleString('en-IN')} ${page.total===1?'question':'questions'}` : page?'Updating questions…':'Loading questions…'}</span>{!pending&&page && <span>{page.total ? offset+1 : 0}–{Math.min(offset+page.items.length,page.total)} of {page.total}</span>}</div>
    {error && <p role="alert" className="mt-3 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error} <button type="button" onClick={()=>setReload(n=>n+1)} className="underline">Retry</button></p>}
    {(combined||collectionId==='udc')&&!paperId&&<p className="mt-2 text-[12px] text-secondary">Identical text copies from booklet series are grouped. Figures and source differences stay separate.</p>}
    {metadataLoading&&<p role="status" className="mt-2 text-[12px] text-muted">Paper details are loading. You can start with the available questions.</p>}
    {checkpointError&&<p role="status" className="mt-2 text-[12px] text-mypick">Could not save your place: {checkpointError}</p>}
    {practice&&<p className="mt-3 text-[12px] text-secondary">Tap an option to submit your answer. Show answer opens reading mode.</p>}
    {page&&<Pagination page={currentPage} pages={pages} disabled={pending} onPageChange={goPage} label={practice?'Practice question navigator':'Exam question pages'}/>}
    {pending&&!page&&!error&&<p role="status" className="min-h-[320px] py-10 text-center text-secondary">Loading questions…</p>}
    <div className={`exam-reading-area mt-2 divide-y divide-hairline ${pending&&page?'opacity-50':''}`} data-results-current={!pending}>
      {page?.items.map((q,index)=>{
        const result=results[q.id]
        return <StudyQuestionCard showPanelNext={false} key={q.id} q={q} collectionId={collectionId} paperId={paperId} sourceCollections={sourceCollections}
          result={result} pick={picks[q.id]} viewed={viewed[q.id]} busy={answerBusy[q.id]} disabled={pending}
          onPick={i=>void answer(q,i)}
          onViewed={value=>setViewed(old=>({...old,[q.id]:value}))} onBusy={v=>setAnswerBusy(old=>({...old,[q.id]:v}))}
          onRetry={()=>{setPicks(old=>{const next={...old};delete next[q.id];return next});setResults(old=>{const next={...old};delete next[q.id];return next})}}
          onNext={()=>{const next=page.items[index+1];if(next)document.getElementById('question-'+next.id)?.scrollIntoView({block:'start',behavior:'smooth'});else if(currentPage<pages)goPage(currentPage+1);else setError('You reached the end of these results. Change filters to continue.')}}/>
      })}
      {!pending&&page && !page.items.length && <div className="py-10 text-center text-[14px] text-secondary">No questions match these filters. <button type="button" onClick={resetFilters} className="min-h-11 underline">Reset filters</button></div>}
    </div>
    {page&&<Pagination page={currentPage} pages={pages} disabled={pending} onPageChange={goPage} label={practice?'Practice question navigator':'Exam question pages'}/>}
  </section>
}

export function ModuleProgressPanel({ collectionId, collectionTitle, totalScorable, totalQuestions = totalScorable, practiceAvailable=true, practiceHref, papersHref }: { collectionId: string; collectionTitle: string; totalScorable: number; totalQuestions?: number; practiceAvailable?:boolean; practiceHref?:string; papersHref?:string }) {
  const practiceLink=practiceHref||`/exams/${collectionId}?view=practice`,paperLink=papersHref||`/exams/${collectionId}?view=papers`
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
  if (!practiceAvailable && progress.answered === 0 && mistakes.length === 0) return <section className="learning-dashboard">
    <header className="learning-header"><div><p className="learning-eyebrow">Your study map · {collectionTitle}</p><h2>Reading & written preparation</h2><p className="learning-intro">This collection currently has source papers to study. Answer-ready MCQ practice is not available yet.</p></div></header>
    <section className="learning-start-panel"><div className="learning-start-icon" aria-hidden="true">↗</div><div className="learning-start-copy"><h3>Build your preparation from an original paper.</h3><p>Keep your written answers in your own notes. Reading and written work are not automatically graded or recorded as answer attempts, accuracy or completion.</p></div><div className="learning-start-actions"><Link to={paperLink} className="learning-primary-button">Choose a paper →</Link></div></section>
  </section>

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
      <div><p className="learning-eyebrow">Your study map · {collectionTitle}</p><h2>Your progress</h2><p className="learning-intro">{practiceAvailable?'A clear record of what you’ve practised in this exam, what’s going well, and where to focus next.':'Your previous answer activity is preserved here. Current preparation uses source papers; reading and written work do not add automatic scores.'}</p></div>
      <div className="learning-storage"><span className="learning-storage-dot"/><div><strong>{practiceAvailable?'Progress saved automatically':'Recorded answer activity'}</strong><small>{progress.last_active_at ? `Last practice ${new Date(progress.last_active_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}` : 'No practice recorded yet.'}</small></div></div>
    </header>

    {!started ? <section className="learning-start-panel"><div className="learning-start-icon" aria-hidden="true">↗</div><div className="learning-start-copy"><p className="learning-eyebrow">A fresh start</p><h3>Your {collectionTitle} progress starts with one question.</h3><p>{practiceAvailable?'Try a short practice set. Your answers, accuracy, section coverage and review list will build here automatically.':'This collection currently offers source reading and written preparation. Written work is not automatically graded or counted as answer attempts.'}</p></div><div className="learning-start-actions">{practiceAvailable&&<Link to={practiceLink} className="learning-primary-button">Start practice →</Link>}<Link to={paperLink} className="learning-secondary-button">Choose a paper</Link></div></section> : <section className="learning-overall"><div className="learning-overall-copy"><span>Question coverage</span><strong>{progress.unique_questions.toLocaleString('en-IN')} <small>of {totalQuestions.toLocaleString('en-IN')}</small></strong></div><div className="learning-overall-meter" role="progressbar" aria-label={`${collectionTitle} question coverage`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={coverage}><span style={{ width: `${coverage}%` }} /></div><div className="learning-overall-foot"><span>{coverage}% of the question set explored</span><Link to={practiceAvailable?practiceLink:paperLink}>{practiceAvailable?'Keep practising →':'Read source papers →'}</Link></div></section>}

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
        })}</div> : <div className="learning-empty-state"><span aria-hidden="true">◎</span><p>{!practiceAvailable?'Reading and written preparation do not produce automatic section scores.':started ? 'Section details will appear as you practise questions from this exam.' : 'Answer a few questions and this view will show your activity in each section.'}</p><Link to={practiceAvailable?practiceLink:paperLink}>{practiceAvailable?'Choose a practice set →':'Choose a source paper →'}</Link></div>}
      </section>

      <div className="learning-side-column">
        <section className="learning-panel"><div className="learning-panel-heading"><div><p className="learning-eyebrow">Last 28 days</p><h3>Practice activity</h3></div><span className="learning-status is-developing">{progress.active_days_30} active</span></div><div className="learning-activity-grid" aria-label="Daily answers over the last 28 days">{activity.map((item) => <div key={item.day} title={`${item.day}: ${item.count} answers`} aria-label={`${item.day}, ${item.count} answers`} className={`learning-activity-day ${item.count ? 'has-activity' : ''}`}><span>{item.count || ''}</span></div>)}</div><div className="learning-activity-legend"><span>Less</span>{[0, 1, 3, 6].map((level) => <i key={level} className={level ? 'has-activity' : ''} style={level ? { opacity: .25 + level * .1 } : undefined} />)}<span>More</span></div><p className="learning-panel-note">{started ? `${progress.answered.toLocaleString('en-IN')} answers recorded in this exam.` : 'Your daily activity will appear here after your first practice.'}</p></section>

        <section className="learning-panel"><div className="learning-panel-heading compact"><div><p className="learning-eyebrow">Review queue</p><h3>Questions to revisit</h3></div><span className={`learning-status ${mistakes.length ? 'is-weak' : 'is-developing'}`}>{mistakes.length} due</span></div>
          {collectionId==='udc'&&mistakes.length>0&&<Link to="/exams/udc?view=practice&status=wrong#exam-question-browser" className="mb-3 inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Practise UDC mistakes →</Link>}
          {mistakes.length ? <div className="learning-queue-list">{mistakes.slice(0, 8).map((m) => <Link className="learning-queue-row" key={m.id} to={`/bank/${m.id}`}><span><strong>{m.question}</strong><small>Missed {m.times_wrong} times · Review question</small></span><b>{m.times_wrong}</b><span className="learning-queue-arrow">›</span></Link>)}</div> : <div className="learning-queue-empty"><span aria-hidden="true">✓</span><p>{started ? 'Nothing is waiting for review right now.' : 'Missed questions will be collected here so you can revisit them later.'}</p>{!started&&practiceAvailable && <Link to={practiceLink}>Start a practice set →</Link>}</div>}
        </section>
      </div>
    </div>
  </section>
}
