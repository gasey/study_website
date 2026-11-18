import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
import {useDebouncedValue} from '../lib/useDebouncedValue'
import {AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import FilterRail, { type Filters } from '../components/FilterRail'
import {powerFilterQuery} from '../lib/publicBrowse'
import {currentExamScope} from '../lib/examScope'
import QuestionCard from '../components/QuestionCard'
import { listQuestions, prefetchQuestionPage, listTaxonomy, listCollections, type Collection, type QuestionPage, type TaxonomyFacet } from '../lib/api'

const PAGE = 25
const SOURCES = ['official','key','derived','inferred','none'] as const
/** Reference sort group. Values are the API's existing `order`, not a new field. */
const ORDERS = [['repeated','Most asked'],['mixed','Mixed'],['paper','Paper order']] as const
/** Coverage rail: the bank has no year facet, so each bar is a real count query. */
const COVERAGE_YEARS = 6

export default function Bank() {
  const [params,setParams]=useSearchParams()
  const query=params.get('q')||'',search=query.trim(),collectionId=params.get('collection_id')||'',paperId=params.get('paper_id')||'',paperLabel=params.get('paper_label')||''
  const pool=(['all','scorable','practice'].includes(params.get('pool')||'')?params.get('pool'):'all') as 'all'|'scorable'|'practice'
  const order=(['repeated','mixed','paper'].includes(params.get('order')||'')?params.get('order'):'repeated') as 'repeated'|'mixed'|'paper'
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
  const base=useMemo(()=>({pool,q:search.length>=2?search:undefined,source:filters.sources.length?filters.sources:undefined,year_from:/^\d{4}$/.test(filters.yearFrom)?Number(filters.yearFrom):undefined,year_to:/^\d{4}$/.test(filters.yearTo)?Number(filters.yearTo):undefined,subject_id:filters.subjectId||undefined,topic_id:filters.topicId||undefined,collection_id:collectionId||undefined,paper_id:paperId||undefined,order}),[pool,search,sourceKey,filters.yearFrom,filters.yearTo,filters.subjectId,filters.topicId,collectionId,paperId,order])
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
  // Selection drives the reference's dark action bar. Kept in the screen, not the
  // URL: it is a scratch list, and sharing a link should not share someone's picks.
  const [selected,setSelected]=useState<string[]>([])
  const toggleSelected=(qid:string)=>setSelected(previous=>previous.includes(qid)?previous.filter(v=>v!==qid):[...previous,qid])
  const setOrder=(value:typeof order)=>setParams(previous=>{const n=new URLSearchParams(previous);if(value==='repeated')n.delete('order');else n.set('order',value);n.delete('page');return n},{replace:true})
  const [collections,setCollections]=useState<Collection[]>([])
  useEffect(()=>{let live=true;listCollections().then(v=>{if(live)setCollections(v)}).catch(()=>{if(live)setCollections([])});return()=>{live=false}},[])
  const pickCollection=(id:string)=>setParams(previous=>{const n=new URLSearchParams(previous);if(id&&id!==collectionId)n.set('collection_id',id);else n.delete('collection_id');n.delete('paper_id');n.delete('paper_label');n.delete('page');return n},{replace:true})

  const total=data?.total??0,pages=Math.max(1,Math.ceil(total/PAGE))
  // Real per-year totals for the active filter. No facet endpoint exists, so each
  // year is a `limit:1` count read; the shared page cache de-duplicates them.
  const [coverage,setCoverage]=useState<{year:number;n:number}[]>([])
  const [coverageRestricted,setCoverageRestricted]=useState(false)
  useEffect(()=>{
    let live=true
    if(key!==settledKey){return()=>{live=false}}
    const latest=new Date().getFullYear()
    const years=Array.from({length:COVERAGE_YEARS},(_,i)=>latest-i)
    if(years.some(year=>powerFilterQuery({...base,exam_scope:currentExamScope(),year_from:year,year_to:year}))){setCoverage([]);setCoverageRestricted(true);return()=>{live=false}}
    setCoverageRestricted(false)
    Promise.all(years.map(year=>listQuestions({...base,year_from:year,year_to:year,limit:1,offset:0}).then(v=>({year,n:v.total})).catch(()=>({year,n:-1}))))
      .then(rows=>{if(live)setCoverage(rows.filter(r=>r.n>=0))})
    return()=>{live=false}
  },[key,settledKey,retryKey])
  const coverageMax=Math.max(1,...coverage.map(c=>c.n))
  const rangeLabel=total===0?'No questions':`Showing ${(offset+1).toLocaleString('en-IN')}–${Math.min(offset+PAGE,total).toLocaleString('en-IN')} of ${total.toLocaleString('en-IN')}`
  const hasFilters=search.length>0||collectionId!==''||paperId!==''||filters.sources.length>0||filters.yearFrom!==''||filters.yearTo!==''||filters.subjectId!==''||filters.topicId!==''
  const clearFilters=()=>setParams(previous=>{const n=new URLSearchParams(previous);for(const k of ['q','collection_id','paper_id','paper_label','subject_id','topic_id','source','year_from','year_to','page'])n.delete(k);return n},{replace:true})

  return (
    <div className="finna-bank" data-screen="bank" data-sec="practice">
      <header className="finna-bank-head">
        <div className="finna-bank-titles">
          <div>
            <div className="finna-eyebrow">Browse questions</div>
            <h1>{collections.find((c) => c.id === collectionId)?.title || 'Question bank'} · {taxonomy.find((t) => t.subject_id === filters.subjectId)?.subject || 'All subjects'}</h1>
          </div>
          <div className="finna-bank-search">
            <input
              maxLength={120}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              type="search"
              placeholder="Search question text"
              aria-label="Search questions"
            />
          </div>
        </div>
        <div className="finna-bank-scopes">
          <div className="finna-segments" role="group" aria-label="Browse mode">
            <button type="button" aria-pressed="true">Questions</button>
            <Link to="/past-papers">Papers</Link>
          </div>
          {collections.slice(0, 5).map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => pickCollection(c.id)}
              aria-pressed={collectionId === c.id}
              className="finna-bank-exam"
            >
              {c.title}
            </button>
          ))}
          {paperId && <button type="button" onClick={() => setParams((p) => { const n = new URLSearchParams(p); n.delete('paper_id'); n.delete('paper_label'); n.delete('page'); return n })} className="finna-bank-exam" aria-pressed="true">Paper · {paperLabel || paperId.split('/').pop()} ×</button>}
        </div>
      </header>
      {query.trim().length === 1 && (
        <p className="text-[12px] text-muted">Enter at least two characters to search.</p>
      )}

      {/* Reference frame: filter rail, results, coverage rail. */}
      <div className="finna-bank-body">
        <FilterRail
          value={filters}
          pool={pool}
          taxonomy={taxonomy}
          onChange={setFilters}
        />

        <section id="bank-results" tabIndex={-1} className="finna-bank-results scroll-mt-28 focus:outline-none">
          <div className="finna-segments" role="group" aria-label="Question pool">
            {(
              [
                ['all', 'All questions'],
                ['scorable', 'Official answer keys'],
                ['practice', 'All answered'],
              ] as const
            ).map(([k, label]) => (
              <button key={k} type="button" onClick={() => changePool(k)} aria-pressed={pool === k}>
                {label}
              </button>
            ))}
          </div>

          <div className="finna-bank-toolbar">
            <span className="finna-bank-count" aria-live="polite">
              {loading ? 'Loading…' : `${total.toLocaleString('en-IN')} questions`}
            </span>
            {hasFilters && (
              <button type="button" onClick={clearFilters} className="min-h-11 rounded-pill px-2 text-[13px] font-semibold text-link hover:underline">
                Clear filters
              </button>
            )}
            <div className="finna-segments" role="group" aria-label="Sort questions" style={{ marginLeft: 'auto' }}>
              {ORDERS.map(([k, label]) => (
                <button key={k} type="button" onClick={() => setOrder(k)} aria-pressed={order === k}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {selected.length > 0 && (
            <div className="finna-bank-selbar">
              <strong>{selected.length} selected</strong>
              <div>
                <Link to={`/tests/make?${new URLSearchParams(selected.map((qid) => ['ids', qid]))}`} className="finna-bank-make">Make a test</Link>
                <button type="button" onClick={() => setSelected([])} className="finna-bank-clear">Clear</button>
              </div>
            </div>
          )}

          <div className="sr-only" role="status" aria-live="polite">
            {loading ? 'Loading questions' : error ? 'Could not load questions' : `${total.toLocaleString('en-IN')} questions found`}
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
            ) : !error && data?.items.map((q,index) => (
              <div key={q.id} className="finna-bank-row">
                <button
                  type="button"
                  className="finna-bank-check"
                  aria-pressed={selected.includes(q.id)}
                  aria-label={selected.includes(q.id) ? 'Remove this question from the selection' : 'Add this question to the selection'}
                  onClick={() => toggleSelected(q.id)}
                >
                  {selected.includes(q.id) ? '✓' : ''}
                </button>
                <QuestionCard q={q} onNext={()=>{const next=data.items[index+1];if(next)document.getElementById('question-'+next.id)?.scrollIntoView({block:'start',behavior:'smooth'});else if(page<pages){setParams(previous=>{const next=new URLSearchParams(previous);next.set('page',String(page+1));return next});requestAnimationFrame(()=>scrollToResults('bank-results'))}}} />
              </div>
            ))}
            {!loading && !error && data?.items.length === 0 && (
              <div className="rounded-[14px] border border-hairline bg-card p-7 text-center">
                <h2 className="font-display text-[23px] font-medium">No questions found</h2>
                <p className="mt-2 text-[14px] leading-relaxed text-secondary">Try a different search or remove one of the filters.</p>
                {hasFilters && <button type="button" onClick={clearFilters} className="mt-4 min-h-11 rounded-pill bg-ink px-5 py-2 text-[13px] font-semibold text-paper">Clear filters</button>}
              </div>
            )}
          </div>

          {!error && (
            <div className="finna-bank-range">
              <span>{loading ? 'Loading…' : rangeLabel}</span>
              <div style={{ marginLeft: 'auto' }}>
                <Pagination label="Question pages" page={page} pages={pages} disabled={loading} onPageChange={goPage}/>
              </div>
            </div>
          )}

        </section>

        <aside className="finna-bank-rail">
          <section className="finna-card">
            <h2>Coverage by year</h2>
            <p className="mt-1 text-[12px] text-muted">Questions matching the current filters.</p>
            <div className="mt-3 grid gap-2.5">
              {coverageRestricted ? <p className="text-[13px] text-muted">Year coverage is shown with basic filters. Background counts never use your combined-search allowance.</p> : coverage.length === 0 ? (
                <p className="text-[13px] text-muted">Counting…</p>
              ) : coverage.every((c) => c.n === 0) ? (
                <p className="text-[13px] text-muted">No questions in the last {COVERAGE_YEARS} years for these filters.</p>
              ) : (
                coverage.map((c) => (
                  <div key={c.year} className="finna-bank-coverage">
                    <span>{c.year}</span>
                    <div><div style={{ width: `${Math.round((c.n / coverageMax) * 100)}%` }} /></div>
                    <span>{c.n.toLocaleString('en-IN')}</span>
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
