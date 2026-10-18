import { useEffect, useState } from 'react'
import FilterRail, { type Filters } from '../components/FilterRail'
import QuestionCard from '../components/QuestionCard'
import { listQuestions, type QuestionPage } from '../lib/api'

const PAGE = 20

export default function Bank() {
  const [pool, setPool] = useState<'scorable' | 'practice'>('scorable')
  const [filters, setFilters] = useState<Filters>({ sources: [], repeatsOnly: false })
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<QuestionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // The search index is sub-millisecond, but a request per keystroke is
  // still pointless traffic.
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(query.trim())
      setOffset(0)
    }, 250)
    return () => clearTimeout(t)
  }, [query])

  const sourceKey = filters.sources.join(',')
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listQuestions({
      pool,
      q: search.length >= 2 ? search : undefined,
      source: filters.sources.length ? filters.sources : undefined,
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
  }, [pool, search, offset, sourceKey, filters.repeatsOnly, filters.sources])

  const total = data?.total ?? 0
  const page = Math.floor(offset / PAGE) + 1
  const pages = Math.max(1, Math.ceil(total / PAGE))

  return (
    <div className="mx-auto max-w-shell px-6 py-10">
      <div className="label text-practice-dark">Question bank</div>
      <h1 className="mt-1 font-display text-[34px] font-semibold leading-tight">
        Browse the bank
      </h1>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search questions…"
          aria-label="Search questions"
          className="h-10 min-w-[260px] grow rounded-panel border border-hairline bg-card px-3 text-[15px] placeholder:text-placeholder focus:border-ink focus:outline-none"
        />
        <div
          role="group"
          aria-label="Answer pool"
          className="flex rounded-pill border border-hairline bg-card p-[3px]"
        >
          {(
            [
              ['scorable', 'Official keys'],
              ['practice', 'All answered'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              onClick={() => {
                setPool(k)
                setOffset(0)
              }}
              aria-pressed={pool === k}
              className={`rounded-pill px-3 py-1 font-mono text-[11px] uppercase tracking-[0.06em] transition-colors ${
                pool === k ? 'bg-ink text-paper' : 'text-muted hover:text-ink'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Rail + list, matching the prototype's 40px gutter and flex ratios. */}
      <div className="mt-6 flex flex-wrap items-start gap-10">
        <FilterRail
          value={filters}
          onChange={(f) => {
            setFilters(f)
            setOffset(0)
          }}
        />

        <section className="min-w-0 flex-[999_1_520px]">
          <div className="flex flex-wrap items-center justify-between gap-2.5 border-b border-ink pb-3">
            <span className="text-[14px] text-secondary">
              {loading ? (
                'Loading…'
              ) : (
                <>
                  <b className="text-ink">{total.toLocaleString('en-IN')}</b> questions shown
                  {total > 0 && (
                    <>
                      {' '}
                      · page {page} of {pages.toLocaleString('en-IN')}
                    </>
                  )}
                </>
              )}
            </span>
            <span className="font-mono text-[11px] text-muted">Tap an option to check it</span>
          </div>

          <p className="mt-3 text-[13px] text-muted">
            {pool === 'scorable' ? (
              <>Only questions with an official answer key — what mocks score against.</>
            ) : (
              <>
                Everything with an answer, including{' '}
                <span className="text-attention-dark">unverified</span> ones. Practice only;
                never scored.
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
                className="rounded-pill border border-hairline px-4 py-2 text-[14px] disabled:opacity-40"
              >
                ← Previous
              </button>
              <button
                disabled={offset + PAGE >= total}
                onClick={() => setOffset((o) => o + PAGE)}
                className="rounded-pill border border-hairline px-4 py-2 text-[14px] disabled:opacity-40"
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
