import { useEffect, useState } from 'react'
import QuestionCard from '../components/QuestionCard'
import { listQuestions, type QuestionPage } from '../lib/api'

const PAGE = 20

export default function Bank() {
  const [pool, setPool] = useState<'scorable' | 'practice'>('scorable')
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<QuestionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Debounce: the search index is fast (<1 ms) but a request per keystroke
  // is still pointless traffic.
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(query.trim())
      setOffset(0)
    }, 250)
    return () => clearTimeout(t)
  }, [query])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listQuestions({ pool, q: search.length >= 2 ? search : undefined, limit: PAGE, offset })
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [pool, search, offset])

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

      <p className="mt-3 text-[13px] text-muted">
        {pool === 'scorable' ? (
          <>Only questions with an official answer key — these are the ones mocks score against.</>
        ) : (
          <>
            Everything with an answer, including{' '}
            <span className="text-attention-dark">unverified</span> ones. Practice only; never
            scored.
          </>
        )}
      </p>

      <div className="mt-6 flex items-baseline justify-between">
        <span className="label">
          {loading ? 'Loading…' : `${total.toLocaleString('en-IN')} questions`}
        </span>
        {!loading && total > 0 && (
          <span className="label">
            Page {page} of {pages.toLocaleString('en-IN')}
          </span>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-card border border-wrong bg-wrong-soft p-4 text-wrong-dark">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">× Error</span>
          <p className="mt-1 text-[14px]">{error}</p>
        </div>
      )}

      <div className="mt-4 grid gap-3">
        {data?.items.map((q) => <QuestionCard key={q.id} q={q} />)}
        {!loading && data?.items.length === 0 && (
          <p className="rounded-card border border-hairline bg-card p-6 text-muted">
            No questions match that search.
          </p>
        )}
      </div>

      {total > PAGE && (
        <div className="mt-6 flex items-center justify-between">
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
    </div>
  )
}
