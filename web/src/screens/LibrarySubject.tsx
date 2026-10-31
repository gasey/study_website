import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
import {useDebouncedValue} from '../lib/useDebouncedValue'
import {AnswerLayoutControl} from '../components/AnswerLayout'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import QuestionCard from '../components/QuestionCard'
import { getProgress, listQuestions, prefetchQuestionPage, listTaxonomy, type Progress, type QuestionPage, type TaxonomyFacet } from '../lib/api'

const PAGE_SIZE = 25

export default function LibrarySubject() {
  const { subjectId = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const topicId = params.get('topic_id') || ''
  const paperId = params.get('paper_id') || ''
  const paperLabel = params.get('paper_label') || ''
  const [facets, setFacets] = useState<TaxonomyFacet[]>([])
  const [progress, setProgress] = useState<Progress | null>(null)
  const [page, setPage] = useState<QuestionPage | null>(null)
  const currentPage=pageNumber(params.get('page')),offset=(currentPage-1)*PAGE_SIZE
  const pool:'all'|'practice'=params.get('pool')==='all'?'all':'practice'
  const query=params.get('q')||'',search=query.trim(),settledSearch=useDebouncedValue(search)
  function filter(key:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);next.delete('page');return next},{replace:true})}
  const setPool=(value:string)=>filter('pool',value),setQuery=(value:string)=>filter('q',value)
  const goPage=(value:number)=>{setParams(previous=>{const next=new URLSearchParams(previous);if(value>1)next.set('page',String(value));else next.delete('page');return next});requestAnimationFrame(()=>scrollToResults('library-results'))}
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    listTaxonomy('all',subjectId==='gk-gs').then((rows) => { if (live) setFacets(rows) }).catch(() => {})
    getProgress().then((p) => { if (live) setProgress(p) }).catch(() => {})
    return () => { live = false }
  }, [subjectId])
  useEffect(() => {
    if (!subjectId) return
    let live=true,timer:number|undefined
    setLoading(true);setError('')
    if(search!==settledSearch)return()=>{live=false}
    const base={subject_id:subjectId,topic_id:topicId||undefined,paper_id:paperId||undefined,pool,q:search.length>=2?search:undefined,limit:PAGE_SIZE}
    listQuestions({...base,offset}).then(result=>{
      if(!live)return
      const last=Math.max(1,Math.ceil(result.total/PAGE_SIZE))
      if(currentPage>last){setParams(previous=>{const next=new URLSearchParams(previous);next.set('page',String(last));return next},{replace:true});return}
      setPage(result)
      if(offset+PAGE_SIZE<result.total)timer=window.setTimeout(()=>prefetchQuestionPage({...base,offset:offset+PAGE_SIZE}),250)
    }).catch(e=>{if(live)setError(e.message||'Questions could not be loaded.')}).finally(()=>{if(live)setLoading(false)})
    return()=>{live=false;if(timer!==undefined)window.clearTimeout(timer)}
  },[subjectId,topicId,paperId,pool,search,settledSearch,offset])

  const subject = facets.find((f) => f.subject_id === subjectId)
  const topics = useMemo(() => facets.filter((f) => f.subject_id === subjectId && f.topic_id), [facets, subjectId])
  const stats = progress?.subjects.find((s) => s.subject_id === subjectId)
  const total = page?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <Link to="/library" className="text-[13px] font-semibold text-link">← Study library</Link>
    <div className="mt-5 flex flex-wrap items-end justify-between gap-4 border-b border-hairline pb-6"><div><div className="font-mono text-[10px] uppercase tracking-[.1em] text-practice-dark">Subject practice</div><h1 className="mt-1 font-display text-[clamp(34px,5vw,50px)] font-medium">{subject?.subject || subjectId.replace(/-/g, ' ')}</h1><p className="mt-2 max-w-[720px] text-[15px] leading-relaxed text-secondary">Browse topics and answer questions here. Your answers contribute to account progress; every item keeps its original paper and key provenance.</p></div>{stats && <div className="rounded-[12px] border border-hairline bg-card px-4 py-3 text-[12px] text-secondary"><strong className="font-display text-[22px] text-ink">{stats.unique_questions}</strong> unique answered · {stats.answered ? Math.round(stats.correct / stats.answered * 100) : 0}% accuracy</div>}</div>
    <MaterialDiscovery subjectId={subjectId} title="Read alongside your practice"/>
    {paperId && <div className="mt-4 inline-flex max-w-full items-center gap-2 rounded-pill bg-practice-soft px-4 py-2 text-[12px] text-practice-dark"><span className="truncate">Paper · {paperLabel || paperId.split('/').pop()}</span><button type="button" onClick={() => { const next = new URLSearchParams(params); next.delete('paper_id'); next.delete('paper_label'); next.delete('page'); setParams(next,{replace:true}) }} className="font-semibold underline">Clear</button></div>}
    <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(220px,320px)]"><input type="search" maxLength={120} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search within this subject" aria-label="Search subject questions" className="h-11 rounded-pill border border-hairline bg-card px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" /><select value={topicId} onChange={(e) => filter('topic_id',e.target.value)} aria-label="Choose a topic" className="h-11 rounded-pill border border-hairline bg-card px-4 text-[13px]"><option value="">All topics</option>{topics.map((t) => <option key={t.topic_id} value={t.topic_id!}>{t.topic} · {t.questions}</option>)}</select></div>
    {search.length===1&&<p className="mt-2 text-[12px] text-muted">Enter at least two characters to search.</p>}
    <div className="mt-3 flex flex-wrap items-center gap-2" role="group" aria-label="Question availability"><button type="button" onClick={() => setPool('practice')} aria-pressed={pool === 'practice'} className={`rounded-pill px-4 py-2 text-[12px] font-semibold ${pool === 'practice' ? 'bg-ink text-paper' : 'border border-hairline bg-card'}`}>Answerable practice</button><button type="button" onClick={() => setPool('all')} aria-pressed={pool === 'all'} className={`rounded-pill px-4 py-2 text-[12px] font-semibold ${pool === 'all' ? 'bg-ink text-paper' : 'border border-hairline bg-card'}`}>All questions, including unkeyed</button><span className="ml-auto font-mono text-[11px] text-muted">{loading ? 'Loading…' : `${total.toLocaleString('en-IN')} questions`}</span></div>
    {error && <p role="alert" className="mt-5 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}</p>}
    {loading && <div className="mt-6 grid gap-3">{[1,2,3].map((n) => <div key={n} className="h-44 animate-pulse rounded-[14px] border border-hairline bg-card" />)}</div>}
    {!loading && !error && total === 0 && <p className="mt-6 rounded-[12px] border border-hairline bg-card p-5 text-[14px] text-secondary">No questions match these filters. Try another topic or show all questions.</p>}
    <section id="library-results" tabIndex={-1} className="scroll-mt-28 focus:outline-none" aria-busy={loading}>
    <Pagination page={currentPage} pages={pages} disabled={loading||!!error} onPageChange={goPage} label="Subject question pages"/>
    <AnswerLayoutControl/>
    {!loading && !error && <div className="mt-6">{page?.items.map((q) => <QuestionCard key={q.id} q={q} onAnswered={() => { getProgress().then(setProgress).catch(() => {}) }} />)}</div>}
    {!error&&<Pagination page={currentPage} pages={pages} disabled={loading} onPageChange={goPage} label="Subject question pages"/>}
    </section>
  </div>
}
