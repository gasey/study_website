import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
import {useDebouncedValue} from '../lib/useDebouncedValue'
import {AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import FilterRail, { type Filters } from '../components/FilterRail'
import QuestionCard from '../components/QuestionCard'
import { listQuestions, prefetchQuestionPage, listTaxonomy, type QuestionPage, type TaxonomyFacet } from '../lib/api'

const PAGE = 25
const SOURCES = ['official','key','derived','inferred','none'] as const

export default function Bank() {
  const [params,setParams]=useSearchParams()
  const query=params.get('q')||'',search=query.trim(),collectionId=params.get('collection_id')||'',paperId=params.get('paper_id')||'',paperLabel=params.get('paper_label')||''
  const pool=(['all','scorable','practice'].includes(params.get('pool')||'')?params.get('pool'):'all') as 'all'|'scorable'|'practice'
  const filters:Filters={sources:params.getAll('source').filter((s):s is Filters['sources'][number]=>SOURCES.some(v=>v===s)),yearFrom:params.get('year_from')||'',yearTo:params.get('year_to')||'',subjectId:params.get('subject_id')||'',topicId:params.get('topic_id')||''}
  const page=pageNumber(params.get('page')),offset=(page-1)*PAGE
  const [taxonomy,setTaxonomy]=useState<TaxonomyFacet[]>([])
  const [data,setData]=useState<QuestionPage|null>(null),[error,setError]=useState<string|null>(null),[loading,setLoading]=useState(true),[retryKey,setRetryKey]=useState(0)
  const setFilters=(next:Filters)=>setParams(previous=>{const n=new URLSearchParams(previous);for(const k of ['source','year_from','year_to','subject_id','topic_id','page'])n.delete(k);next.sources.forEach(v=>n.append('source',v));for(const [k,v]of Object.entries({year_from:next.yearFrom,year_to:next.yearTo,subject_id:next.subjectId,topic_id:next.topicId}))if(v)n.set(k,v);return n},{replace:true})
  const setQuery=(value:string)=>setParams(previous=>{const n=new URLSearchParams(previous);if(value)n.set('q',value);else n.delete('q');n.delete('page');return n},{replace:true})
  const changePool=(value:typeof pool)=>setParams(previous=>{const n=new URLSearchParams(previous);n.set('pool',value);n.delete('page');if(value==='scorable'){const kept=n.getAll('source').filter(v=>v==='official'||v==='key');n.delete('source');kept.forEach(v=>n.append('source',v))}return n},{replace:true})
  const goPage=(value:number)=>{setParams(previous=>{const n=new URLSearchParams(previous);if(value>1)n.set('page',String(value));else n.delete('page');return n});requestAnimationFrame(()=>scrollToResults('bank-results'))}
  useEffect(()=>{let live=true;listTaxonomy(pool,true).then(v=>{if(live)setTaxonomy(v)}).catch(()=>{if(live)setTaxonomy([])});return()=>{live=false}},[pool])
  const sourceKey=filters.sources.join(',')
  const base=useMemo(()=>({pool,q:search.length>=2?search:undefined,source:filters.sources.length?filters.sources:undefined,year_from:/^\d{4}$/.test(filters.yearFrom)?Number(filters.yearFrom):undefined,year_to:/^\d{4}$/.test(filters.yearTo)?Number(filters.yearTo):undefined,subject_id:filters.subjectId||undefined,topic_id:filters.topicId||undefined,collection_id:collectionId||undefined,paper_id:paperId||undefined}),[pool,search,sourceKey,filters.yearFrom,filters.yearTo,filters.subjectId,filters.topicId,collectionId,paperId])
  const key=JSON.stringify(base),settledKey=useDebouncedValue(key)
  useEffect(()=>{
    let live=true,timer:number|undefined;setLoading(true);setError(null)
    if(key!==settledKey)return()=>{live=false}
    listQuestions({...base,limit:PAGE,offset}).then(value=>{
      if(!live)return
      const last=Math.max(1,Math.ceil(value.total/PAGE))
      if(page>last){setParams(previous=>{const n=new URLSearchParams(previous);if(last>1)n.set('page',String(last));else n.delete('page');return n},{replace:true});return}
      setData(value)
      if(offset+PAGE<value.total)timer=window.setTimeout(()=>prefetchQuestionPage({...base,limit:PAGE,offset:offset+PAGE}),250)
    }).catch(e=>{if(live)setError(e.message)}).finally(()=>{if(live)setLoading(false)})
    return()=>{live=false;if(timer!==undefined)window.clearTimeout(timer)}
  },[key,settledKey,offset,retryKey])
  useEffect(()=>{const refresh=()=>setRetryKey(v=>v+1);window.addEventListener('ism-auth-change',refresh);window.addEventListener('ism-content-change',refresh);return()=>{window.removeEventListener('ism-auth-change',refresh);window.removeEventListener('ism-content-change',refresh)}},[])
  const total=data?.total??0,pages=Math.max(1,Math.ceil(total/PAGE))
  const hasFilters=search.length>0||collectionId!==''||paperId!==''||filters.sources.length>0||filters.yearFrom!==''||filters.yearTo!==''||filters.subjectId!==''||filters.topicId!==''
  const clearFilters=()=>setParams(previous=>{const n=new URLSearchParams(previous);for(const k of ['q','collection_id','paper_id','paper_label','subject_id','topic_id','source','year_from','year_to','page'])n.delete(k);return n},{replace:true})

  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">
        Engine · Mizoram PSC
      </div>
      <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)] font-medium leading-[1.05] -tracking-[0.02em]">
        Question bank
      </h1>
      <p className="mt-3 max-w-[720px] text-[17px] leading-relaxed text-secondary [text-wrap:pretty]">
        Browse the full collection from Mizoram Public Service Commission (MPSC) papers. Filter it
        to build a focused set, or open an exam for a ready-made path. Every answer is labelled by
        where it came from; questions without a published key remain browse-only.
      </p>
      {collectionId && <div className="mt-4 inline-flex items-center gap-2 rounded-pill bg-exams-soft px-4 py-2 text-[13px] font-semibold text-exams-dark">Filtered to this exam collection <button type="button" onClick={() => setParams((p) => { const n = new URLSearchParams(p); n.delete('collection_id'); n.delete('page'); return n })} className="underline">Clear</button></div>}
      {paperId && <div className="mt-4 inline-flex max-w-full flex-wrap items-center gap-2 rounded-pill bg-practice-soft px-4 py-2 text-[13px] font-semibold text-practice-dark">Paper · {paperLabel || paperId.split('/').pop()} <button type="button" onClick={() => setParams((p) => { const n = new URLSearchParams(p); n.delete('paper_id'); n.delete('paper_label'); n.delete('page'); return n })} className="underline">Clear</button></div>}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <input
          maxLength={120}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          type="search"
          placeholder="Search by keyword or question text"
          aria-label="Search questions"
          className="h-[46px] min-w-[260px] grow rounded-pill border border-hairline bg-card px-[18px] text-[15px] placeholder:text-placeholder focus:border-ink focus:outline-none"
        />
        <div
          role="group"
          aria-label="Question pool"
          className="flex min-h-[46px] rounded-pill border border-hairline bg-card p-[3px]"
        >
          {(
            [
              ['all', 'All questions'],
              ['scorable', 'Official answer keys'],
              ['practice', 'All answered'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              onClick={() => changePool(k)}
              aria-pressed={pool === k}
              className={`min-h-[44px] rounded-pill px-3 py-2 font-mono text-[11px] uppercase tracking-[0.06em] transition-colors ${
                pool === k ? 'bg-ink text-paper' : 'text-muted hover:text-ink'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {query.trim().length === 1 && (
        <p className="mt-2 text-[12px] text-muted">Enter at least two characters to search.</p>
      )}

      {/* Rail + list, matching the prototype's 40px gutter and flex ratios. */}
      <div className="mt-6 flex flex-wrap items-start gap-10">
        <FilterRail
          value={filters}
          pool={pool}
          taxonomy={taxonomy}
          onChange={setFilters}
        />

        <section id="bank-results" tabIndex={-1} className="min-w-0 flex-[999_1_520px] scroll-mt-28 focus:outline-none">
          <div className="flex flex-wrap items-center justify-between gap-2.5 border-b border-ink pb-3">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[14px] text-secondary" aria-live="polite">
              {loading ? (
                'Loading…'
              ) : (
                <>
                  <b className="text-ink">{total.toLocaleString('en-IN')}</b> questions
                  {total > 0 && (
                    <>
                      {' '}
                      <span className="text-muted">· page {page} of {pages.toLocaleString('en-IN')}</span>
                    </>
                  )}
                </>
              )}
              {hasFilters && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="ml-1 min-h-11 rounded-pill px-2 text-[13px] font-semibold text-link hover:underline"
                >
                  Clear filters
                </button>
              )}
            </div>
            <span className="font-mono text-[11px] text-muted">
              {pool === 'all' ? 'Questions without keys are browse-only' : 'Tap an option to check it'}
            </span>
          </div>

          <div className="sr-only" role="status" aria-live="polite">
            {loading ? 'Loading questions' : error ? 'Could not load questions' : `${total.toLocaleString('en-IN')} questions found`}
          </div>

          <p className="mt-3 text-[13px] text-muted">
            {pool === 'all' ? (
              <>All published questions, including those without an answer key. Unkeyed questions are browse-only.</>
            ) : pool === 'scorable' ? (
              <>Official and transcribed keys only. Scored mocks use this pool.</>
            ) : (
              <>
                Includes worked solutions and <span className="text-attention-dark">unverified</span> answers
                for practice. This pool is never scored.
              </>
            )}
          </p>

          {error && (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick" role="alert">
              <div>
              <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
              <p className="mt-1 text-[14px]">{error}</p>
              </div>
              <button type="button" onClick={() => setRetryKey((n) => n + 1)} className="min-h-11 rounded-pill border border-mypick px-4 py-2 text-[13px] font-semibold hover:bg-white/50">
                Try again
              </button>
            </div>
          )}

          {!error && <Pagination label="Question pages, top" page={page} pages={pages} disabled={loading} onPageChange={goPage}/>}
          <AnswerLayoutControl/>
          <div className="mt-4" aria-busy={loading}>
            {loading ? (
              <div className="grid gap-3" aria-hidden="true">
                {Array.from({ length: 4 }, (_, i) => (
                  <div key={i} className="animate-pulse rounded-[14px] border border-hairline bg-card px-[22px] py-5">
                    <div className="h-3 w-40 rounded bg-[#EDE5D4]" />
                    <div className="mt-4 h-5 w-11/12 rounded bg-[#EDE5D4]" />
                    <div className="mt-2 h-5 w-3/5 rounded bg-[#EDE5D4]" />
                    <div className="mt-5 grid gap-2 sm:grid-cols-2"><div className="h-11 rounded-[6px] bg-[#F1EBDF]" /><div className="h-11 rounded-[6px] bg-[#F1EBDF]" /></div>
                  </div>
                ))}
              </div>
            ) : !error && data?.items.map((q,index) => <QuestionCard key={q.id} q={q} onNext={()=>{const next=data.items[index+1];if(next)document.getElementById('question-'+next.id)?.scrollIntoView({block:'start',behavior:'smooth'});else if(page<pages){setParams(previous=>{const next=new URLSearchParams(previous);next.set('page',String(page+1));return next});requestAnimationFrame(()=>scrollToResults('bank-results'))}}} />)}
            {!loading && !error && data?.items.length === 0 && (
              <div className="rounded-[14px] border border-hairline bg-card p-7 text-center">
                <h2 className="font-display text-[23px] font-medium">No questions found</h2>
                <p className="mt-2 text-[14px] leading-relaxed text-secondary">Try a different search or remove one of the filters.</p>
                {hasFilters && <button type="button" onClick={clearFilters} className="mt-4 min-h-11 rounded-pill bg-ink px-5 py-2 text-[13px] font-semibold text-paper">Clear filters</button>}
              </div>
            )}
          </div>

          {!error && <Pagination label="Question pages" page={page} pages={pages} disabled={loading} onPageChange={goPage}/>}

        </section>
      </div>
    </div>
  )
}
