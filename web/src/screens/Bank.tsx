import Pagination from '../components/Pagination'
import { pageNumber, scrollToResults } from '../lib/pagination'
import { useDebouncedValue } from '../lib/useDebouncedValue'
import { AnswerLayoutControl } from '../components/AnswerLayout'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import FilterRail, { type Filters } from '../components/FilterRail'
import QuestionCard from '../components/QuestionCard'
import { useSelectionTray } from '../lib/selectionTray'
import { FLAGSHIP_EXAM_IDS } from '../lib/examPresentation'
import {
  getQuestionFacets,
  isLaterExamCollection,
  isSubjectModule,
  listCollections,
  listQuestions,
  listTaxonomy,
  moduleHref,
  prefetchQuestionPage,
  type Collection,
  type QuestionPage,
  type QuestionYearFacet,
  type TaxonomyFacet,
} from '../lib/api'

const PAGE = 25
const SOURCES = ['official', 'key', 'derived', 'inferred', 'none'] as const
/** Reference sort group (FINNAPLAN v2 P5: retired dead `repeated` control from UI; API parameter kept). */
const ORDERS = [
  ['paper', 'Paper order'],
  ['mixed', 'Mixed'],
] as const
const STUDY_STATUSES = [
  ['all', 'All'],
  ['unseen', 'Unseen'],
  ['ever_wrong', 'Ever wrong'],
  ['answered', 'Answered'],
] as const
type StudyStatus = (typeof STUDY_STATUSES)[number][0]

const FLAGSHIP_SET = new Set<string>(FLAGSHIP_EXAM_IDS)

/** Chooser-first full bank surface (FINNAPLAN v2 P5 / V.28b).
 *  Renders ZERO questions on arrival until the user chooses a shelf (exam,
 *  subject, paper, year or search), avoiding the confusing raw corpus wall.
 *  Replaces the 6-request year loop with one `/api/questions/facets` call. */
export default function Bank() {
  const [params, setParams] = useSearchParams()
  const tray = useSelectionTray()
  const query = params.get('q') || ''
  const search = query.trim()
  const collectionId = params.get('collection_id') || ''
  const paperId = params.get('paper_id') || ''
  const paperLabel = params.get('paper_label') || ''
  const writtenMode = params.get('mode') === 'written'
  const pool = (
    writtenMode
      ? 'all'
      : ['all', 'scorable', 'practice'].includes(params.get('pool') || '')
        ? params.get('pool')
        : 'all'
  ) as 'all' | 'scorable' | 'practice'
  const requested = params.get('order') || ''
  const order = (requested === 'mixed' ? 'mixed' : 'paper') as 'mixed' | 'paper'
  const rawStatus = params.get('study_status') || 'all'
  const studyStatus = (STUDY_STATUSES.some(([k]) => k === rawStatus) ? rawStatus : 'all') as StudyStatus

  const setStudyStatus = (value: StudyStatus) =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        if (value === 'all') n.delete('study_status')
        else n.set('study_status', value)
        n.delete('page')
        return n
      },
      { replace: true },
    )

  const filters: Filters = {
    sources: params
      .getAll('source')
      .filter((s): s is Filters['sources'][number] => SOURCES.some((v) => v === s)),
    yearFrom: params.get('year_from') || '',
    yearTo: params.get('year_to') || '',
    subjectId: params.get('subject_id') || '',
    topicId: params.get('topic_id') || '',
  }
  const page = pageNumber(params.get('page'))
  const offset = (page - 1) * PAGE

  const hasSelection =
    search.length >= 2 ||
    collectionId !== '' ||
    paperId !== '' ||
    writtenMode ||
    filters.sources.length > 0 ||
    filters.yearFrom !== '' ||
    filters.yearTo !== '' ||
    filters.subjectId !== '' ||
    filters.topicId !== '' ||
    studyStatus !== 'all'

  const [taxonomy, setTaxonomy] = useState<TaxonomyFacet[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [examSearch, setExamSearch] = useState('')
  const [data, setData] = useState<QuestionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [retryKey, setRetryKey] = useState(0)
  const [coverage, setCoverage] = useState<QuestionYearFacet[]>([])

  const setFilters = (next: Filters) =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        for (const k of ['source', 'year_from', 'year_to', 'subject_id', 'topic_id', 'page']) {
          n.delete(k)
        }
        next.sources.forEach((v) => n.append('source', v))
        for (const [k, v] of Object.entries({
          year_from: next.yearFrom,
          year_to: next.yearTo,
          subject_id: next.subjectId,
          topic_id: next.topicId,
        })) {
          if (v) n.set(k, v)
        }
        return n
      },
      { replace: true },
    )

  const setQuery = (value: string) =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        if (value) n.set('q', value)
        else n.delete('q')
        n.delete('page')
        return n
      },
      { replace: true },
    )

  const goPage = (value: number) => {
    setParams((previous) => {
      const n = new URLSearchParams(previous)
      if (value > 1) n.set('page', String(value))
      else n.delete('page')
      return n
    })
    requestAnimationFrame(() => scrollToResults('bank-results'))
  }

  useEffect(() => {
    let live = true
    listTaxonomy(pool, true)
      .then((v) => {
        if (live) setTaxonomy(v)
      })
      .catch(() => {
        if (live) setTaxonomy([])
      })
    return () => {
      live = false
    }
  }, [pool])

  useEffect(() => {
    let live = true
    listCollections()
      .then((v) => {
        if (live) setCollections(v.filter((c) => !isLaterExamCollection(c)))
      })
      .catch(() => {
        if (live) setCollections([])
      })
    return () => {
      live = false
    }
  }, [])

  const sourceKey = filters.sources.join(',')
  const base = useMemo(
    () => ({
      pool,
      q: search.length >= 2 ? search : undefined,
      source: filters.sources.length ? filters.sources : undefined,
      year_from: /^\d{4}$/.test(filters.yearFrom) ? Number(filters.yearFrom) : undefined,
      year_to: /^\d{4}$/.test(filters.yearTo) ? Number(filters.yearTo) : undefined,
      subject_id: filters.subjectId || undefined,
      topic_id: filters.topicId || undefined,
      collection_id: collectionId || undefined,
      paper_id: paperId || undefined,
      order: order === 'mixed' ? ('mixed' as const) : paperId ? ('paper' as const) : ('repeated' as const),
      seed: order === 'mixed' ? 'bank-mixed-v2' : undefined,
      study_status: studyStatus !== 'all' ? studyStatus : undefined,
    }),
    [
      pool,
      search,
      sourceKey,
      filters.yearFrom,
      filters.yearTo,
      filters.subjectId,
      filters.topicId,
      collectionId,
      paperId,
      order,
      studyStatus,
    ],
  )
  const key = JSON.stringify(base)
  const settledKey = useDebouncedValue(key)

  useEffect(() => {
    if (!hasSelection) {
      setData(null)
      setLoading(false)
      setError(null)
      return
    }
    let live = true
    let timer: number | undefined
    setLoading(true)
    setError(null)
    if (key !== settledKey) return () => { live = false }
    listQuestions({ ...base, limit: PAGE, offset })
      .then((value) => {
        if (!live) return
        const last = Math.max(1, Math.ceil(value.total / PAGE))
        if (page > last) {
          setParams(
            (previous) => {
              const n = new URLSearchParams(previous)
              if (last > 1) n.set('page', String(last))
              else n.delete('page')
              return n
            },
            { replace: true },
          )
          return
        }
        setData(value)
        if (offset + PAGE < value.total) {
          timer = window.setTimeout(
            () => prefetchQuestionPage({ ...base, limit: PAGE, offset: offset + PAGE }),
            250,
          )
        }
      })
      .catch((e) => {
        if (live) setError(e.message)
      })
      .finally(() => {
        if (live) setLoading(false)
      })
    return () => {
      live = false
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [hasSelection, key, settledKey, offset, retryKey])

  useEffect(() => {
    const refresh = () => setRetryKey((v) => v + 1)
    window.addEventListener('ism-auth-change', refresh)
    window.addEventListener('ism-content-change', refresh)
    return () => {
      window.removeEventListener('ism-auth-change', refresh)
      window.removeEventListener('ism-content-change', refresh)
    }
  }, [])

  // Single facet request replaces the old 6-requests-per-year coverage loop (FINNAPLAN v2 P4).
  useEffect(() => {
    if (!hasSelection) {
      setCoverage([])
      return
    }
    let live = true
    if (key !== settledKey) return () => { live = false }
    getQuestionFacets({
      collection_id: collectionId || undefined,
      paper_id: paperId || undefined,
      subject_id: filters.subjectId || undefined,
      pool,
    })
      .then((res) => {
        if (live) setCoverage(res.years.slice(0, 10))
      })
      .catch(() => {
        if (live) setCoverage([])
      })
    return () => {
      live = false
    }
  }, [hasSelection, collectionId, paperId, filters.subjectId, pool, key, settledKey, retryKey])

  const selected = tray.ids
  const toggleSelected = (qid: string) => tray.toggle(qid)
  const setOrder = (value: typeof order) =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        if (value === 'paper') n.delete('order')
        else n.set('order', value)
        n.delete('page')
        return n
      },
      { replace: true },
    )

  const pickCollection = (id: string) =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        if (id) n.set('collection_id', id)
        else n.delete('collection_id')
        n.delete('paper_id')
        n.delete('paper_label')
        n.delete('page')
        return n
      },
      { replace: true },
    )

  const subjectModules = useMemo(
    () => collections.filter((c) => isSubjectModule(c)),
    [collections],
  )
  const examModules = useMemo(
    () => collections.filter((c) => c.kind === 'exam'),
    [collections],
  )
  const flagshipExams = useMemo(
    () => examModules.filter((c) => FLAGSHIP_SET.has(c.id)),
    [examModules],
  )
  const filteredExamChoices = useMemo(() => {
    const q = examSearch.trim().toLowerCase()
    if (!q) return examModules.slice(0, 24)
    return examModules
      .filter((c) => `${c.title} ${c.id}`.toLowerCase().includes(q))
      .slice(0, 30)
  }, [examModules, examSearch])

  const total = data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / PAGE))
  const coverageMax = Math.max(1, ...coverage.map((c) => c.questions))
  const rangeLabel =
    total === 0
      ? 'No questions'
      : `Showing ${(offset + 1).toLocaleString('en-IN')}–${Math.min(offset + PAGE, total).toLocaleString('en-IN')} of ${total.toLocaleString('en-IN')}`
  const clearFilters = () =>
    setParams(
      (previous) => {
        const n = new URLSearchParams(previous)
        for (const k of [
          'q',
          'collection_id',
          'paper_id',
          'paper_label',
          'subject_id',
          'topic_id',
          'source',
          'year_from',
          'year_to',
          'study_status',
          'mode',
          'page',
        ]) {
          n.delete(k)
        }
        return n
      },
      { replace: true },
    )

  const practiceFilteredHref = useMemo(() => {
    const p = new URLSearchParams()
    if (collectionId) p.set('exam', collectionId)
    if (filters.subjectId) p.set('subject', filters.subjectId)
    if (search.length >= 2) p.set('q', search)
    return '/practice' + (p.size ? '?' + p : '')
  }, [collectionId, filters.subjectId, search])

  return (
    <div className="finna-bank" data-screen="bank" data-sec="practice">
      <header className="finna-bank-head">
        <div className="finna-bank-titles">
          <div>
            <div className="finna-eyebrow">Advanced corpus chooser</div>
            <h1>
              {collections.find((c) => c.id === collectionId)?.title ||
                (hasSelection ? 'Filtered questions' : 'Choose a shelf first')}
              {filters.subjectId
                ? ` · ${taxonomy.find((t) => t.subject_id === filters.subjectId)?.subject || filters.subjectId}`
                : ''}
            </h1>
          </div>
          <div className="finna-bank-search">
            <input
              maxLength={120}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              type="search"
              placeholder="Search question text (2+ chars)"
              aria-label="Search questions"
            />
          </div>
        </div>
        <div className="finna-bank-scopes">
          <div className="finna-segments" role="group" aria-label="Browse mode">
            <button type="button" aria-pressed="true">
              Questions
            </button>
            <Link to="/past-papers">Papers</Link>
            <Link to="/exams">All exams</Link>
          </div>
          <label className="inline-flex items-center gap-2 text-xs font-semibold text-secondary">
            <span className="sr-only">Filter by exam or subject module</span>
            <select
              value={collectionId}
              onChange={(e) => pickCollection(e.target.value)}
              aria-label="Choose exam or subject module"
              className="min-h-10 max-w-[260px] rounded-pill border border-hairline bg-card px-3 text-xs font-semibold text-ink"
            >
              <option value="">All modules (choose one)</option>
              {subjectModules.length > 0 && (
                <optgroup label="Cross-exam subjects">
                  {subjectModules.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} ({c.questions.toLocaleString('en-IN')})
                    </option>
                  ))}
                </optgroup>
              )}
              <optgroup label="Exams">
                {examModules.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} ({c.questions.toLocaleString('en-IN')})
                  </option>
                ))}
              </optgroup>
            </select>
          </label>
          {paperId && (
            <button
              type="button"
              onClick={() =>
                setParams((p) => {
                  const n = new URLSearchParams(p)
                  n.delete('paper_id')
                  n.delete('paper_label')
                  n.delete('page')
                  return n
                })
              }
              className="finna-bank-exam"
              aria-pressed="true"
            >
              Paper · {paperLabel || paperId.split('/').pop()} ×
            </button>
          )}
        </div>
      </header>
      {query.trim().length === 1 && (
        <p className="text-xs text-muted">Enter at least two characters to search.</p>
      )}

      {/* Chooser-first empty arrival state: ZERO questions rendered until a shelf is chosen */}
      {!hasSelection ? (
        <section
          aria-label="Choose an exam or subject"
          className="mt-6 grid gap-6"
        >
          <div className="rounded-[16px] border border-hairline bg-card p-6">
            <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">
              Start with a focused shelf
            </p>
            <h2 className="mt-1 font-display text-xl font-medium">
              Pick a cross-exam subject or an exam booklet
            </h2>
            <p className="mt-1 text-sm text-secondary">
              Instead of dumping 70,000+ raw questions at once, choose a subject
              or exam below — or type a keyword above to search the full bank.
            </p>

            {subjectModules.length > 0 && (
              <div className="mt-5">
                <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                  Cross-exam subjects
                </h3>
                <div className="mt-2.5 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                  {subjectModules.map((c) => (
                    <Link
                      key={c.id}
                      to={moduleHref(c)}
                      className="flex items-center justify-between rounded-[12px] border border-hairline bg-canvas px-4 py-3 text-sm font-semibold text-ink transition hover:border-ink"
                    >
                      <span>{c.title}</span>
                      <span className="font-mono text-xs text-muted">
                        {c.questions.toLocaleString('en-IN')} →
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                  Featured exams
                </h3>
                <Link to="/exams" className="text-xs font-semibold text-link hover:underline">
                  Browse all {examModules.length} exams →
                </Link>
              </div>
              <div className="mt-2.5 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                {flagshipExams.map((c) => (
                  <Link
                    key={c.id}
                    to={moduleHref(c)}
                    className="flex items-center justify-between rounded-[12px] border border-hairline bg-canvas px-4 py-3 text-sm font-semibold text-ink transition hover:border-ink"
                  >
                    <span className="truncate pr-2">{c.title}</span>
                    <span className="shrink-0 font-mono text-xs text-muted">
                      {c.questions.toLocaleString('en-IN')} →
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="mt-6 border-t border-hairline pt-5">
              <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                Find any of {examModules.length} exams
              </h3>
              <input
                type="search"
                value={examSearch}
                onChange={(e) => setExamSearch(e.target.value)}
                placeholder="Type exam name (e.g. MCS, ACF, Legal Metrology, JE, Excise, Nurse…)"
                className="mt-2 block min-h-11 w-full max-w-lg rounded-[10px] border border-hairline bg-canvas px-3 text-sm"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                {filteredExamChoices.map((c) => (
                  <Link
                    key={c.id}
                    to={moduleHref(c)}
                    className="inline-flex min-h-9 items-center gap-1.5 rounded-pill border border-hairline bg-canvas px-3 py-1 text-xs font-semibold text-ink hover:border-ink"
                  >
                    <span>{c.title}</span>
                    <span className="font-mono text-[11px] text-muted">{c.questions}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>
      ) : (
        <div className="finna-bank-body">
          <FilterRail
            value={filters}
            pool={pool}
            taxonomy={taxonomy}
            onChange={setFilters}
          />

          <section
            id="bank-results"
            tabIndex={-1}
            className="finna-bank-results scroll-mt-28 focus:outline-none"
          >
            <div className="flex flex-wrap items-center gap-2">
              <div className="finna-segments" role="group" aria-label="Question pool">
                <button
                  type="button"
                  onClick={() =>
                    setParams(
                      (prev) => {
                        const n = new URLSearchParams(prev)
                        n.delete('mode')
                        n.set('pool', 'all')
                        n.delete('page')
                        return n
                      },
                      { replace: true },
                    )
                  }
                  aria-pressed={!writtenMode && pool === 'all'}
                >
                  All questions
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setParams(
                      (prev) => {
                        const n = new URLSearchParams(prev)
                        n.delete('mode')
                        n.set('pool', 'practice')
                        n.delete('page')
                        return n
                      },
                      { replace: true },
                    )
                  }
                  aria-pressed={!writtenMode && pool === 'practice'}
                >
                  With answers
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setParams(
                      (prev) => {
                        const n = new URLSearchParams(prev)
                        n.set('mode', 'written')
                        n.set('pool', 'all')
                        n.delete('page')
                        return n
                      },
                      { replace: true },
                    )
                  }
                  aria-pressed={writtenMode}
                >
                  Written answers
                </button>
              </div>
              <div className="finna-segments" role="group" aria-label="Your status">
                {STUDY_STATUSES.map(([k, label]) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setStudyStatus(k)}
                    aria-pressed={studyStatus === k}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="finna-bank-toolbar">
              <span className="finna-bank-count" aria-live="polite">
                {loading ? 'Loading…' : `${total.toLocaleString('en-IN')} questions`}
              </span>
              {!loading && total > 0 && !writtenMode && (
                <Link
                  to={practiceFilteredHref}
                  className="inline-flex min-h-10 items-center rounded-pill bg-practice-soft px-3 text-xs font-bold text-practice-dark hover:underline"
                >
                  Practice these →
                </Link>
              )}
              <button
                type="button"
                onClick={clearFilters}
                className="min-h-11 rounded-pill px-2 text-sm font-semibold text-link hover:underline"
              >
                Clear filters
              </button>
              <div
                className="finna-segments"
                role="group"
                aria-label="Sort questions"
                style={{ marginLeft: 'auto' }}
              >
                {ORDERS.map(([k, label]) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setOrder(k)}
                    aria-pressed={order === k}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {selected.length > 0 && (
              <div className="finna-bank-selbar">
                <strong>{selected.length} selected</strong>
                <div>
                  <Link to={tray.buildHref} className="finna-bank-make">
                    Make a test
                  </Link>
                  <button
                    type="button"
                    onClick={() => tray.clear()}
                    className="finna-bank-clear"
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}

            <div className="sr-only" role="status" aria-live="polite">
              {loading
                ? 'Loading questions'
                : error
                  ? 'Could not load questions'
                  : `${total.toLocaleString('en-IN')} questions found`}
            </div>

            <p className="mt-3 text-sm text-muted">
              {writtenMode ? (
                <>
                  Descriptive and written-response prompts from past papers.
                  Read the instructions and save a private draft on any prompt.
                </>
              ) : pool === 'all' ? (
                <>All published questions, including those without an answer key yet.</>
              ) : pool === 'scorable' ? (
                <>Questions with an official answer key.</>
              ) : (
                <>Questions with an official key or a worked solution.</>
              )}
            </p>

            {error && (
              <div
                className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick"
                role="alert"
              >
                <div>
                  <span className="font-mono text-xs uppercase tracking-[0.06em]">
                    Error
                  </span>
                  <p className="mt-1 text-sm">{error}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setRetryKey((n) => n + 1)}
                  className="min-h-11 rounded-pill border border-mypick px-4 py-2 text-sm font-semibold hover:bg-white/50"
                >
                  Try again
                </button>
              </div>
            )}

            {!error && (
              <Pagination
                label="Question pages, top"
                page={page}
                pages={pages}
                disabled={loading}
                onPageChange={goPage}
              />
            )}
            <AnswerLayoutControl />
            <div className="mt-4" aria-busy={loading}>
              {loading ? (
                <div className="grid gap-3" aria-hidden="true">
                  {Array.from({ length: 4 }, (_, i) => (
                    <div
                      key={i}
                      className="animate-pulse rounded-[14px] border border-hairline bg-card px-[22px] py-5"
                    >
                      <div className="h-3 w-40 rounded bg-[#EDE5D4]" />
                      <div className="mt-4 h-5 w-11/12 rounded bg-[#EDE5D4]" />
                      <div className="mt-2 h-5 w-3/5 rounded bg-[#EDE5D4]" />
                      <div className="mt-5 grid gap-2 sm:grid-cols-2">
                        <div className="h-11 rounded-[6px] bg-[#F1EBDF]" />
                        <div className="h-11 rounded-[6px] bg-[#F1EBDF]" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                !error &&
                (writtenMode
                  ? data?.items.filter((q) => q.type === 'descriptive')
                  : data?.items
                )?.map((q, index, visibleItems) => (
                  <div key={q.id} className="finna-bank-row">
                    <button
                      type="button"
                      className="finna-bank-check"
                      aria-pressed={selected.includes(q.id)}
                      aria-label={
                        selected.includes(q.id)
                          ? 'Remove this question from the selection'
                          : 'Add this question to the selection'
                      }
                      onClick={() => toggleSelected(q.id)}
                    >
                      {selected.includes(q.id) ? '✓' : ''}
                    </button>
                    <QuestionCard
                      q={q}
                      onNext={() => {
                        const next = visibleItems[index + 1]
                        if (next) {
                          document
                            .getElementById('question-' + next.id)
                            ?.scrollIntoView({ block: 'start', behavior: 'smooth' })
                        } else if (page < pages) {
                          setParams((previous) => {
                            const nextP = new URLSearchParams(previous)
                            nextP.set('page', String(page + 1))
                            return nextP
                          })
                          requestAnimationFrame(() => scrollToResults('bank-results'))
                        }
                      }}
                    />
                  </div>
                ))
              )}
              {!loading && !error && data?.items.length === 0 && (
                <div className="rounded-[14px] border border-hairline bg-card p-7 text-center">
                  <h2 className="font-display text-lg font-medium">
                    No questions found
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-secondary">
                    Try a different search or remove one of the filters.
                  </p>
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="mt-4 min-h-11 rounded-pill bg-ink px-5 py-2 text-sm font-semibold text-paper"
                  >
                    Clear filters
                  </button>
                </div>
              )}
            </div>

            {!error && (
              <div className="finna-bank-range">
                <span>{loading ? 'Loading…' : rangeLabel}</span>
                <div style={{ marginLeft: 'auto' }}>
                  <Pagination
                    label="Question pages"
                    page={page}
                    pages={pages}
                    disabled={loading}
                    onPageChange={goPage}
                  />
                </div>
              </div>
            )}
          </section>

          <aside className="finna-bank-rail">
            <section className="finna-card">
              <h2>Coverage by year</h2>
              <p className="mt-1 text-xs text-muted">
                Tap a year to narrow these questions.
              </p>
              <div className="mt-3 grid gap-2.5">
                {coverage.length === 0 ? (
                  <p className="text-sm text-muted">
                    No dated years recorded for this selection.
                  </p>
                ) : (
                  coverage.map((c) => {
                    const active =
                      filters.yearFrom === String(c.year) &&
                      filters.yearTo === String(c.year)
                    return (
                      <button
                        key={c.year}
                        type="button"
                        onClick={() =>
                          setFilters({
                            ...filters,
                            yearFrom: active ? '' : String(c.year),
                            yearTo: active ? '' : String(c.year),
                          })
                        }
                        aria-pressed={active}
                        className="finna-bank-coverage text-left hover:opacity-80"
                      >
                        <span className={active ? 'font-bold text-ink' : undefined}>
                          {c.year}
                        </span>
                        <div>
                          <div
                            style={{
                              width: `${Math.round((c.questions / coverageMax) * 100)}%`,
                            }}
                          />
                        </div>
                        <span>{c.questions.toLocaleString('en-IN')}</span>
                      </button>
                    )
                  })
                )}
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  )
}
