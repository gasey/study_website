import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  getCollection,
  isLaterExamCollection,
  listCollections,
  type Collection,
  type CollectionDetail,
} from '../lib/api'
import { useExamScope } from '../lib/examScope'
import { choosePreferredExam, usePreferredExam } from '../lib/preferredExam'
import { resolveTrackedExams, shortExamLabel, useTrackedExamIds } from '../lib/trackedExams'
import { FLAGSHIP_EXAM_IDS } from '../lib/examPresentation'
import { sortArchivePapers } from '../lib/paperArchive'
import { groupSourceBooklets } from '../lib/sourceBooklets'
import ExamPaperList from '../components/ExamPaperList'
import Pagination from '../components/Pagination'
import { pageNumber, scrollToResults } from '../lib/pagination'

const SIZE = 21

/** /papers is reserved for original PDF assets; this directory is /past-papers. */
export default function Papers() {
  const [params, setParams] = useSearchParams()
  const scope = useExamScope()
  const [exams, setExams] = useState<Collection[]>([])
  const [data, setData] = useState<CollectionDetail | null>(null)
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)

  const preferred = usePreferredExam(exams)
  const trackedIds = useTrackedExamIds()
  const trackedExams = useMemo(
    () => resolveTrackedExams(exams, trackedIds, preferred),
    [exams, trackedIds, preferred],
  )
  const exam = exams.find((e) => e.id === params.get('exam')) || preferred
  const query = params.get('q') || ''
  const page = pageNumber(params.get('page'))
  const year = params.get('year') || ''
  const layout: 'cards' | 'list' = params.get('layout') === 'list' ? 'list' : 'cards'

  function filter(key: string, value: string) {
    setParams(
      (old) => {
        const next = new URLSearchParams(old)
        if (value) next.set(key, value)
        else next.delete(key)
        if (key !== 'page') next.delete('page')
        return next
      },
      { replace: key !== 'page' },
    )
  }

  function selectExam(examId: string) {
    choosePreferredExam(examId)
    setParams((old) => {
      const next = new URLSearchParams(old)
      next.set('exam', examId)
      next.delete('page')
      next.delete('year')
      return next
    })
  }

  useEffect(() => {
    let live = true
    setExams([])
    setCatalogLoading(true)
    setError('')
    listCollections()
      .then((rows) => {
        if (live) setExams(rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)))
      })
      .catch(() => {
        if (live) setError('The exam directory could not load. Please try again.')
      })
      .finally(() => {
        if (live) setCatalogLoading(false)
      })
    return () => {
      live = false
    }
  }, [scope, retry])

  useEffect(() => {
    if (!exam) return
    let live = true
    setData(null)
    setError('')
    getCollection(exam.id)
      .then((result) => {
        if (live) setData(result)
      })
      .catch((e) => {
        if (live) {
          setError(e instanceof Error ? e.message : 'The paper archive could not load.')
        }
      })
    return () => {
      live = false
    }
  }, [exam?.id, retry])

  const quickExamPills = useMemo(() => {
    const out: Collection[] = []
    const seen = new Set<string>()
    for (const e of trackedExams) {
      if (!seen.has(e.id)) {
        out.push(e)
        seen.add(e.id)
      }
    }
    for (const id of FLAGSHIP_EXAM_IDS) {
      if (out.length >= 8) break
      if (seen.has(id)) continue
      const match = exams.find((e) => e.id === id)
      if (match) {
        out.push(match)
        seen.add(match.id)
      }
    }
    return out
  }, [trackedExams, exams])

  const current = data?.id === exam?.id ? data : null
  const papers = useMemo(
    () =>
      sortArchivePapers(
        (current?.paper_list || []).filter(
          (p) =>
            p.allow_browse &&
            (!year || String(p.year) === year) &&
            (!query ||
              [p.title, p.exam, p.subject, p.paper_number, p.source_file]
                .filter(Boolean)
                .join(' ')
                .toLowerCase()
                .includes(query.toLowerCase())),
        ),
        'newest',
      ),
    [current, year, query],
  )
  const groups = groupSourceBooklets(papers)
  const pages = Math.max(1, Math.ceil(groups.length / SIZE))
  const visible = groups.slice((page - 1) * SIZE, page * SIZE)

  useEffect(() => {
    if (current && page > pages) {
      setParams(
        (old) => {
          const next = new URLSearchParams(old)
          if (pages > 1) next.set('page', String(pages))
          else next.delete('page')
          return next
        },
        { replace: true },
      )
    }
  }, [current, page, pages, setParams])

  const years = [
    ...new Set(current?.paper_list.flatMap((p) => (p.year ? [p.year] : [])) || []),
  ].sort((a, b) => b - a)

  return (
    <div className="finna-page pp-shell" data-screen="papers">
      <header className="av-hero pp-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">Original source archive · Verified PDFs &amp; keys</span>
          <h1>Past papers</h1>
          <p>
            Browse original MPSC question booklets by exam and year, open full paper questions, or
            inspect source PDFs alongside official answer keys.
          </p>
        </div>
        <div className="av-hero-actions">
          <Link className="cr-glass-btn cr-glass-btn--accent" to="/exams">
            Browse all exams →
          </Link>
          <Link className="cr-glass-btn" to="/exams?exam_filter=subjects">
            Subject books
          </Link>
        </div>
      </header>

      {/* 1-click Tracked & Flagship Exam Switcher */}
      {quickExamPills.length > 0 && (
        <section className="pp-exam-strip mt-5" aria-label="Quick switch exam archive">
          <span className="pp-strip-label">Switch exam</span>
          <div className="pp-pill-row">
            {quickExamPills.map((item) => {
              const isCurrent = exam?.id === item.id
              const isTracked = trackedExams.some((t) => t.id === item.id)
              return (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={isCurrent}
                  onClick={() => selectExam(item.id)}
                  className={`pp-exam-pill${isCurrent ? ' is-active' : ''}`}
                >
                  {isTracked && <span aria-hidden="true">★</span>}
                  <span>{shortExamLabel(item)}</span>
                </button>
              )
            })}
          </div>
        </section>
      )}

      {/* Search, Full Exam Selector, Year & Layout Bar */}
      <form
        onSubmit={(e) => e.preventDefault()}
        className="pp-toolbar mt-4"
      >
        <label className="min-w-0 flex-1 basis-64">
          <span className="sr-only">Search past papers</span>
          <input
            type="search"
            aria-label="Search past papers"
            placeholder="Search paper title, subject, paper number or year…"
            value={query}
            onChange={(e) => filter('q', e.target.value)}
            className="pp-input"
          />
        </label>

        <label className="min-w-0 max-w-full">
          <span className="sr-only">Exam papers</span>
          <select
            aria-label="Exam papers"
            disabled={catalogLoading}
            value={exam?.id || ''}
            onChange={(e) => selectExam(e.target.value)}
            className="pp-select"
          >
            {!exams.length && (
              <option value="">{catalogLoading ? 'Loading exams…' : 'Choose an exam'}</option>
            )}
            {exams.map((e) => (
              <option key={e.id} value={e.id}>
                {e.title}
              </option>
            ))}
          </select>
        </label>

        <div className="av-tabs" role="group" aria-label="Paper display layout">
          <button
            type="button"
            className={`av-tab${layout === 'cards' ? ' is-active' : ''}`}
            aria-pressed={layout === 'cards'}
            onClick={() => filter('layout', '')}
          >
            Sheets
          </button>
          <button
            type="button"
            className={`av-tab${layout === 'list' ? ' is-active' : ''}`}
            aria-pressed={layout === 'list'}
            onClick={() => filter('layout', 'list')}
          >
            Table
          </button>
        </div>
      </form>

      {/* Quick Year Filter Chips */}
      {years.length > 1 && (
        <div className="pp-year-strip mt-3" role="group" aria-label="Filter papers by year">
          <button
            type="button"
            aria-pressed={!year}
            onClick={() => filter('year', '')}
            className={`pp-year-pill${!year ? ' is-active' : ''}`}
          >
            All years
          </button>
          {years.slice(0, 14).map((y) => (
            <button
              key={y}
              type="button"
              aria-pressed={year === String(y)}
              onClick={() => filter('year', String(y))}
              className={`pp-year-pill${year === String(y) ? ' is-active' : ''}`}
            >
              {y}
            </button>
          ))}
        </div>
      )}

      <div className="mb-4 mt-6 flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h2
            id="paper-results"
            tabIndex={-1}
            className="scroll-mt-36 font-reading text-2xl font-semibold text-ink"
          >
            {exam ? `${exam.title} · original papers` : 'Original papers'}
          </h2>
          {exam && (
            <Link to={'/exams/' + exam.id} className="text-sm font-bold text-link hover:underline">
              Open full exam page →
            </Link>
          )}
        </div>
        <span role="status" className="finna-st-pill finna-st-pill--gray">
          {current
            ? `${groups.length.toLocaleString('en-IN')} ${groups.length === 1 ? 'paper' : 'papers'}`
            : error
              ? 'Unavailable'
              : 'Loading…'}
        </span>
      </div>

      {error && (
        <section className="finna-card" role="alert">
          <h2>The paper archive couldn’t load</h2>
          <p className="mt-2 text-sm text-secondary">{error}</p>
          <button className="finna-btn mt-4" onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </section>
      )}

      {!current && !error && (
        <div role="status" className="pp-cards-grid" aria-label="Loading source papers">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-52 animate-pulse rounded-[18px] border border-hairline bg-card"
            />
          ))}
        </div>
      )}

      {current && !visible.length && (
        <section className="finna-card text-center">
          <h2>No papers match these filters</h2>
          <p className="mt-2 text-sm text-secondary">
            Try another search term or switch back to all years.
          </p>
          <button
            className="finna-btn finna-btn-quiet mt-4"
            onClick={() => setParams(exam ? { exam: exam.id } : {})}
          >
            Clear filters
          </button>
        </section>
      )}

      {current && exam && visible.length > 0 && (
        <ExamPaperList papers={papers} groups={visible} examId={exam.id} layout={layout} />
      )}

      {current && groups.length > SIZE && (
        <div className="mt-6">
          <Pagination
            page={page}
            pages={pages}
            onPageChange={(n) => {
              filter('page', String(n))
              requestAnimationFrame(() => scrollToResults('paper-results'))
            }}
            label="Past paper pages"
          />
        </div>
      )}
    </div>
  )
}
