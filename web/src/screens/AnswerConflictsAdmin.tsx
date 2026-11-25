import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'

interface ConflictSummary {
  shape_b_count: number
  shape_a_count: number
  total: number
}

interface ClusteredPaper {
  paper_id: string
  conflicts: number
}

interface ConflictRow {
  canonical_id: string
  paper_id: string
  qnum: number | null
  shape: 'key-won' | 'solution-won'
  official_answer: string | null
  solution_answer: string | null
  solution_publication_id: string | null
  detected_from: string | null
  question: string
  exposure_attempts: number
  paper_conflicts: number
  cluster_flagged: boolean
}

interface ConflictDetail {
  canonical_id: string
  conflicts: (ConflictRow & {
    options?: (string | null)[]
    answer_text?: string | null
    answer_source?: string | null
    key_disputed?: boolean
    dispute_note?: string | null
    explanation?: string | null
  })[]
  publications: {
    id: string
    state: string
    finished_at: string | null
    admin_decision: Record<string, unknown> | null
  }[]
}

interface ConflictsResponse {
  summary: ConflictSummary
  cluster_threshold: number
  clustered_papers: ClusteredPaper[]
  items: ConflictRow[]
}

export default function AnswerConflictsAdmin({ isOwner = false }: { isOwner?: boolean }) {
  const [shape, setShape] = useState<'all' | 'key-won' | 'solution-won'>('all')
  const [paperId, setPaperId] = useState('')
  const [data, setData] = useState<ConflictsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ConflictDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  async function load(nextShape = shape, nextPaper = paperId) {
    setLoading(true)
    setError('')
    try {
      const qs = new URLSearchParams({ shape: nextShape, limit: '100' })
      if (nextPaper.trim()) qs.set('paper_id', nextPaper.trim())
      const res = await reviewRequest<ConflictsResponse>('/admin/bank/conflicts?' + qs.toString())
      setData(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load answer conflicts.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(shape, paperId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shape, paperId])

  async function refreshMaterializedView() {
    setRefreshing(true)
    setError('')
    setNotice('')
    try {
      const res = await reviewRequest<{ refreshed: boolean; shape_b: number; shape_a: number }>(
        '/admin/bank/conflicts/refresh',
        {},
      )
      setNotice(
        `Refreshed v_answer_conflicts (${res.shape_b} key-won · ${res.shape_a} solution-won) and recorded worker heartbeat.`,
      )
      await load(shape, paperId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not refresh conflicts view.')
    } finally {
      setRefreshing(false)
    }
  }

  async function inspectConflict(qid: string) {
    if (expandedId === qid) {
      setExpandedId(null)
      setDetail(null)
      return
    }
    setExpandedId(qid)
    setDetail(null)
    setLoadingDetail(true)
    try {
      const res = await reviewRequest<ConflictDetail>(
        '/admin/bank/conflicts/' + encodeURIComponent(qid),
      )
      setDetail(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load conflict detail.')
    } finally {
      setLoadingDetail(false)
    }
  }

  const summary = data?.summary || { total: 0, shape_b_count: 0, shape_a_count: 0 }

  return (
    <section className="mt-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-hairline bg-card p-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-ink">
            Key vs. Solution Conflicts
          </h2>
          <p className="mt-0.5 text-xs text-secondary">
            Disagreements between official exam answer keys and derived/reviewed solutions, ranked by paper cluster and learner exposure.
          </p>
        </div>
        {isOwner && (
          <button
            type="button"
            disabled={refreshing}
            onClick={() => void refreshMaterializedView()}
            className="min-h-10 rounded-pill bg-ink px-4 text-xs font-bold text-paper disabled:opacity-50"
          >
            {refreshing ? 'Refreshing…' : '↻ Refresh conflicts view'}
          </button>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-[10px] border border-mypick bg-mypick-soft px-4 py-3 text-sm text-mypick">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-[10px] border border-correct bg-correct-soft px-4 py-3 text-sm text-ink">
          {notice}
        </p>
      )}

      {/* Summary KPI Grid */}
      <div className="grid gap-3 sm:grid-cols-4">
        <div className="rounded-[12px] border border-hairline bg-card p-4">
          <div className="font-mono text-[11px] uppercase tracking-[.08em] text-muted">Active conflicts</div>
          <div className="mt-1 font-display text-2xl font-bold text-ink">{summary.total.toLocaleString('en-IN')}</div>
        </div>
        <div className="rounded-[12px] border border-hairline bg-card p-4">
          <div className="font-mono text-[11px] uppercase tracking-[.08em] text-muted">Key-won (Shape B)</div>
          <div className="mt-1 font-display text-2xl font-bold text-ink">{summary.shape_b_count.toLocaleString('en-IN')}</div>
        </div>
        <div className="rounded-[12px] border border-hairline bg-card p-4">
          <div className="font-mono text-[11px] uppercase tracking-[.08em] text-muted">Solution-won (Shape A)</div>
          <div className="mt-1 font-display text-2xl font-bold text-ink">{summary.shape_a_count.toLocaleString('en-IN')}</div>
        </div>
        <div className="rounded-[12px] border border-hairline bg-card p-4">
          <div className="font-mono text-[11px] uppercase tracking-[.08em] text-muted">Clustered papers</div>
          <div className="mt-1 font-display text-2xl font-bold text-ink">
            {(data?.clustered_papers.length || 0).toLocaleString('en-IN')}
          </div>
        </div>
      </div>

      {/* Clustered Papers Alert Strip */}
      {data && data.clustered_papers.length > 0 && (
        <div className="rounded-[12px] border border-attention bg-attention-soft p-4">
          <p className="text-xs font-bold text-ink">
            Cluster gate triggered (&gt;{data.cluster_threshold} key-won conflicts in one paper — check booklet series alignment before bulk edits):
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {data.clustered_papers.map((cp) => (
              <button
                key={cp.paper_id}
                type="button"
                onClick={() => setPaperId(paperId === cp.paper_id ? '' : cp.paper_id)}
                className={`min-h-8 rounded-pill border px-3 font-mono text-xs font-semibold ${
                  paperId === cp.paper_id
                    ? 'border-ink bg-ink text-paper'
                    : 'border-hairline bg-card text-ink'
                }`}
              >
                {cp.paper_id} ({cp.conflicts})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="finna-segments" role="group" aria-label="Conflict shape">
          {(
            [
              ['all', 'All'],
              ['key-won', 'Key-won'],
              ['solution-won', 'Solution-won'],
            ] as const
          ).map(([val, label]) => (
            <button
              key={val}
              type="button"
              aria-pressed={shape === val}
              onClick={() => setShape(val)}
            >
              {label}
            </button>
          ))}
        </div>
        {paperId && (
          <button
            type="button"
            onClick={() => setPaperId('')}
            className="min-h-9 rounded-pill border border-hairline bg-card px-3 font-mono text-xs font-semibold text-ink"
          >
            Paper: {paperId} ×
          </button>
        )}
      </div>

      {/* Conflict Queue */}
      {loading ? (
        <p className="py-8 text-sm text-muted">Loading conflicts…</p>
      ) : !data?.items.length ? (
        <div className="rounded-[14px] border border-hairline bg-card p-6 text-sm text-secondary">
          No active answer conflicts match this filter. Click <strong>Refresh conflicts view</strong> if new official keys or derived solutions were published recently.
        </div>
      ) : (
        <div className="space-y-3">
          {data.items.map((item) => {
            const isOpen = expandedId === item.canonical_id
            return (
              <article
                key={`${item.canonical_id}-${item.paper_id}`}
                className="rounded-[12px] border border-hairline bg-card p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-muted">
                    <span className="rounded-pill bg-paper px-2.5 py-0.5 font-bold text-ink">
                      {item.shape}
                    </span>
                    <span>{item.paper_id}{item.qnum ? ` · Q${item.qnum}` : ''}</span>
                    <span>· {item.exposure_attempts} attempts</span>
                    {item.cluster_flagged && (
                      <span className="rounded-pill bg-mypick-soft px-2 py-0.5 font-bold text-mypick">
                        Cluster ({item.paper_conflicts})
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void inspectConflict(item.canonical_id)}
                      className="min-h-9 rounded-pill border border-hairline bg-canvas px-3 text-xs font-bold text-ink hover:border-ink"
                    >
                      {isOpen ? 'Hide detail' : 'Inspect conflict'}
                    </button>
                    <Link
                      to={`/admin/bank?${new URLSearchParams({
                        tab: 'questions',
                        question: item.canonical_id,
                        issue: 'all',
                      })}`}
                      className="inline-flex min-h-9 items-center rounded-pill border border-ink px-3 text-xs font-bold text-ink"
                    >
                      Open workbench →
                    </Link>
                  </div>
                </div>

                <p className="mt-2 font-reading text-base text-ink">{item.question}</p>

                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-[9px] border border-hairline bg-canvas p-2.5 text-xs">
                    <span className="font-mono font-bold uppercase text-muted">Official key</span>
                    <p className="mt-1 font-semibold text-ink">{item.official_answer || '—'}</p>
                  </div>
                  <div className="rounded-[9px] border border-hairline bg-canvas p-2.5 text-xs">
                    <span className="font-mono font-bold uppercase text-muted">Derived / solution answer</span>
                    <p className="mt-1 font-semibold text-ink">{item.solution_answer || '—'}</p>
                  </div>
                </div>

                {isOpen && (
                  <div className="mt-3 border-t border-hairline pt-3 text-xs">
                    {loadingDetail ? (
                      <p className="text-muted">Loading full options &amp; publication history…</p>
                    ) : detail ? (
                      <div className="space-y-3">
                        {detail.conflicts[0]?.options && detail.conflicts[0].options.length > 0 && (
                          <div>
                            <span className="font-mono font-bold uppercase text-muted">Printed options</span>
                            <ul className="mt-1 grid gap-1 sm:grid-cols-2">
                              {detail.conflicts[0].options.map((opt, idx) => (
                                <li key={idx} className="rounded bg-canvas px-2.5 py-1.5 text-ink">
                                  <strong>{String.fromCharCode(65 + idx)}.</strong> {opt || '—'}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {detail.conflicts[0]?.explanation && (
                          <div>
                            <span className="font-mono font-bold uppercase text-muted">Current explanation</span>
                            <p className="mt-1 whitespace-pre-wrap text-secondary">
                              {detail.conflicts[0].explanation}
                            </p>
                          </div>
                        )}
                        {detail.publications.length > 0 && (
                          <div>
                            <span className="font-mono font-bold uppercase text-muted">
                              Recent publications ({detail.publications.length})
                            </span>
                            <ul className="mt-1 space-y-1 font-mono text-[11px] text-secondary">
                              {detail.publications.map((p) => (
                                <li key={p.id}>
                                  {p.id} · {p.state}
                                  {p.finished_at ? ` · ${new Date(p.finished_at).toLocaleDateString('en-IN')}` : ''}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
