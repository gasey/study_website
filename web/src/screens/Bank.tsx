import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import FilterRail, { type Filters } from '../components/FilterRail'
import QuestionCard from '../components/QuestionCard'
import { listQuestions, type QuestionPage } from '../lib/api'

const PAGE = 20

export default function Bank() {
  const [params, setParams] = useSearchParams()
  const queryFromUrl = params.get('q') ?? ''
  const [pool, setPool] = useState<'scorable' | 'practice'>('scorable')
  const [filters, setFilters] = useState<Filters>({ sources: [], yearFrom: '', yearTo: '' })
  const [yearRange, setYearRange] = useState({ from: '', to: '' })
  const [query, setQuery] = useState(queryFromUrl)
  const [search, setSearch] = useState(queryFromUrl)
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<QuestionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setQuery(queryFromUrl)
    setSearch(queryFromUrl)
    setOffset(0)
  }, [queryFromUrl])

  // The search index is sub-millisecond, but a request per keystroke is
  // still pointless traffic.
  useEffect(() => {
    const t = setTimeout(() => {
      const next = query.trim()
      setSearch(next)
      setOffset(0)
      setParams((current) => {
        const updated = new URLSearchParams(current)
        if (next) updated.set('q', next)
        else updated.delete('q')
        return updated
      }, { replace: true })
    }, 250)
    return () => clearTimeout(t)
  }, [query, setParams])

  useEffect(() => {
    const t = setTimeout(() => {
      setYearRange({ from: filters.yearFrom, to: filters.yearTo })
      setOffset(0)
    }, 300)
    return () => clearTimeout(t)
  }, [filters.yearFrom, filters.yearTo])

  const sourceKey = filters.sources.join(',')
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listQuestions({
      pool,
      q: search.length >= 2 ? search : undefined,
      source: filters.sources.length ? filters.sources : undefined,
      year_from: /^\d{4}$/.test(yearRange.from) ? Number(yearRange.from) : undefined,
      year_to: /^\d{4}$/.test(yearRange.to) ? Number(yearRange.to) : undefined,
      limit: PAGE,
      offset,
    })
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
    // sourceKey stands in for the array so a new-but-equal array does not refetch
  }, [pool, search, offset, sourceKey, filters.sources, yearRange.from, yearRange.to])

  const total = data?.total ?? 0
  const page = Math.floor(offset / PAGE) + 1
  const pages = Math.max(1, Math.ceil(total / PAGE))
  const hasFilters = query.trim().length > 0 || filters.sources.length > 0 || filters.yearFrom !== '' || filters.yearTo !== ''

  const clearFilters = () => {
    setQuery('')
    setSearch('')
    setParams((current) => {
      const updated = new URLSearchParams(current)
      updated.delete('q')
      return updated
    }, { replace: true })
    setFilters({ sources: [], yearFrom: '', yearTo: '' })
    setYearRange({ from: '', to: '' })
    setOffset(0)
  }

  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">
        Engine · Mizoram PSC
      </div>
      <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)] font-medium leading-[1.05] -tracking-[0.02em]">
        Question bank
      </h1>
      <p className="mt-3 max-w-[720px] text-[17px] leading-relaxed text-secondary [text-wrap:pretty]">
        Browse questions from Mizoram Public Service Commission (MPSC) past papers. Each answer
        shows whether it comes from an official key, a transcribed key or a practice-only answer.
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          type="search"
          placeholder="Search question text…"
          aria-label="Search questions"
          className="h-[46px] min-w-[260px] grow rounded-pill border border-hairline bg-card px-[18px] text-[15px] placeholder:text-placeholder focus:border-ink focus:outline-none"
        />
        <div
          role="group"
          aria-label="Answer pool"
          className="flex min-h-[46px] rounded-pill border border-hairline bg-card p-[3px]"
        >
          {(
            [
              ['scorable', 'Scorable keys'],
              ['practice', 'All answered'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              onClick={() => {
                setPool(k)
                if (k === 'scorable') {
                  setFilters((f) => ({
                    ...f,
                    sources: f.sources.filter((s) => s === 'official' || s === 'key'),
                  }))
                }
                setOffset(0)
              }}
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
          onChange={(f) => {
            setFilters(f)
            setOffset(0)
          }}
        />

        <section className="min-w-0 flex-[999_1_520px]">
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
            <span className="font-mono text-[11px] text-muted">Tap an option to check it</span>
          </div>

          <p className="mt-3 text-[13px] text-muted">
            {pool === 'scorable' ? (
              <>Official and transcribed keys only. Scored mocks use this pool.</>
            ) : (
              <>
                Includes derived and <span className="text-attention-dark">unverified</span> answers
                for practice. This pool is never scored.
              </>
            )}
          </p>

          {error && (
            <div className="mt-4 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick">
              <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
              <p className="mt-1 text-[14px]">{error}</p>
            </div>
          )}

          <div className="mt-4">
            {data?.items.map((q) => <QuestionCard key={q.id} q={q} />)}
            {!loading && data?.items.length === 0 && (
              <p className="rounded-[14px] border border-hairline bg-card p-6 text-muted">
                No questions match those filters.
              </p>
            )}
          </div>

          {total > PAGE && (
            <div className="flex items-center justify-between">
              <button
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - PAGE))}
                className="min-h-[44px] rounded-pill border border-hairline px-4 py-2 text-[14px] disabled:opacity-40"
              >
                ← Previous
              </button>
              <button
                disabled={offset + PAGE >= total}
                onClick={() => setOffset((o) => o + PAGE)}
                className="min-h-[44px] rounded-pill border border-hairline px-4 py-2 text-[14px] disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
