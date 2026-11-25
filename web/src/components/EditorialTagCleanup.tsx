import CleanupSavedViews from './CleanupSavedViews'
import TaxonomyReviewProgress from './TaxonomyReviewProgress'
import QuestionOrganizationContext from './QuestionOrganizationContext'
import { learningChoices, learningSubjectId } from '../lib/learningTaxonomy'
import type { Provider } from '../lib/bankOrganization'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import SearchableTaxonomyPicker, { pathLabel } from './SearchableTaxonomyPicker'
import EditorialSourcePicker from './EditorialSourcePicker'
import QuestionCorrectionEditor from './QuestionCorrectionEditor'
import { SourceQuestionText } from './SourceQuestionText'
import { reviewRequest, reviewSession, type BankSnapshot, type TaxonomyNode } from '../lib/review'
import type { Classification } from '../lib/learningTaxonomy'
import { tagPaperScope, updateTagFilter, tagQuery, tagReturn } from '../lib/editorialTagFilters'

const INPUT =
  'min-h-11 min-w-0 max-w-full rounded-lg border border-hairline bg-paper px-3 py-2 text-sm'
const BUTTON =
  'min-h-10 rounded-pill border border-hairline px-3.5 py-1.5 text-sm font-semibold disabled:opacity-40'

type Row = {
  id: string
  appearance_id: string
  question: string
  subject_label: string | null
  topic_label: string | null
  paper_id: string
  paper_title: string
  qnum: string | null
  bank: string
  report_count: number
  reported_at: string | null
  invalid: boolean
}
type Preview = {
  question_id: string
  appearance_id: string
  baseline_hash: string
  source_version: string
  shared_papers: number
  record: {
    question: string
    classification: Classification
    relatedClassifications?: Classification[]
  }
  source: { title: string | null }
}
type Batch = {
  id: string
  items: {
    id: string
    state: string
    lock_version: number
    relatedClassifications?: Classification[]
    record: Preview['record']
    classification: Classification
  }[]
}

const EXAM_SHORTCUTS: [string, string][] = [
  ['', 'All exams'],
  ['ldc', 'LDC'],
  ['udc', 'UDC'],
  ['combined-prelims', 'MCS Prelims'],
  ['assistant', 'Assistant'],
  ['group-b-non-gazetted', 'Group B NG'],
]

const QUICK_TAG_SPECS: {
  label: string
  subject_id: string
  topic_id?: string
}[] = [
  { label: '🌿 Mizo · Grammar', subject_id: 'mizo', topic_id: 'mizo/grammar' },
  { label: '🌿 Mizo · Literature', subject_id: 'mizo', topic_id: 'mizo/literature' },
  { label: '🪶 English · Grammar', subject_id: 'english', topic_id: 'english/grammar' },
  { label: '🪶 English · Vocab', subject_id: 'english', topic_id: 'english/vocabulary' },
  { label: '💻 Computer · Systems', subject_id: 'computer-science', topic_id: 'computer-science/computer-systems-and-architecture' },
  { label: '⚖️ Indian Polity', subject_id: 'general-studies', topic_id: 'general-studies/indian-polity' },
  { label: '⛰️ Geography', subject_id: 'general-studies', topic_id: 'general-studies/geography' },
  { label: '⛰️ Mizoram GS', subject_id: 'general-studies', topic_id: 'general-studies/mizoram' },
  { label: '🏛️ Indian History', subject_id: 'general-studies', topic_id: 'general-studies/indian-history' },
  { label: '🪙 Indian Economy', subject_id: 'general-studies', topic_id: 'general-studies/indian-economy' },
  { label: '🔬 Science', subject_id: 'science' },
  { label: '📐 Maths · Arithmetic', subject_id: 'mathematics', topic_id: 'mathematics/arithmetic' },
  { label: '🧠 Reasoning', subject_id: 'reasoning-and-aptitude', topic_id: 'reasoning-and-aptitude/verbal-reasoning' },
  { label: '📚 Static GK', subject_id: 'general-knowledge', topic_id: 'general-knowledge/static-gk' },
]

/** Fast client-side language/subject spotter to help owners sweep mis-tagged or untagged rows rapidly. */
function detectLikelyHint(text: string): { id: 'mizo' | 'maths' | 'computer'; badge: string } | null {
  const s = (text || '').toLowerCase()
  // Common high-signal Mizo words & particles rarely seen in English stems
  if (
    /\b(tawng|ṭawng|thumal|ziak|hming|thlang|thlan|chhanna|hrilhfiah|hnena|chuan|emaw|dik\s+zawk|a\s+ni|tih\s+hi|tihna|mizo\s+tawng|tawngkam|tawng\s+upa|thu\s+bul|thufing|lehkha|chhiar)\b/.test(
      s,
    )
  ) {
    return { id: 'mizo', badge: '🌿 Likely Mizo' }
  }
  if (/\b(ms\s+word|ms\s+excel|powerpoint|windows\s+os|tcp\/ip|osi\s+layer|shortcut|ram\s+memory|cpu|sql|html|spreadsheet)\b/.test(s)) {
    return { id: 'computer', badge: '💻 Likely Computer' }
  }
  if (/\b(compound interest|simple interest|lcm|hcf|km\/h|perimeter|circumference|cost price|selling price)\b/.test(s)) {
    return { id: 'maths', badge: '📐 Likely Maths' }
  }
  return null
}

export default function EditorialTagCleanup({
  nodes,
  canWrite,
  needsMfa = false,
  onBusy,
}: {
  onBusy?: (busy: boolean) => void
  nodes: TaxonomyNode[]
  canWrite: boolean
  needsMfa?: boolean
}) {
  const [params, setParams] = useSearchParams()
  const batchId = params.get('retag_batch') || ''
  const issue = params.get('tag_issue') || (tagQuery(params) ? 'all' : 'attention')
  const query = tagQuery(params)
  const bank = params.get('tag_bank') || 'all'
  const module = params.get('tag_module') || ''
  const subject = params.get('tag_subject') || ''
  const sort = params.get('tag_sort') || 'priority'
  const topic = params.get('tag_topic') || ''
  const subtopic = params.get('tag_subtopic') || ''
  const pathScope = params.get('tag_path') || 'primary'
  const period = params.get('tag_period') || 'all'
  const region = params.get('tag_region') || ''
  const timeBehavior = params.get('tag_time') || 'all'
  const paper = tagPaperScope(params)
  const year = params.get('tag_year') || ''
  const offset = Math.max(0, Number(params.get('tag_offset')) || 0)

  const [data, setData] = useState<{ items: Row[]; total: number } | null>(null)
  const [selection, setSelection] = useState<Row[]>([])
  const [preview, setPreview] = useState<Preview[] | null>(null)
  const [batch, setBatch] = useState<Batch | null>(null)
  const [lastBatchId, setLastBatchId] = useState<string>('')
  const [path, setPath] = useState<Classification>({ subject_id: '' })
  const [operation, setOperation] = useState('replace_primary')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [refresh, setRefresh] = useState(0)
  const [providers, setProviders] = useState<Provider[]>([])
  const [modules, setModules] = useState<{ id: string; title: string }[]>([])
  const [snapshot, setSnapshot] = useState<BankSnapshot | null>(null)
  const [user, setUser] = useState('')
  const [solo, setSolo] = useState(false)

  const selectedId = params.get('tag_selected') || ''
  const selectedAppearance = params.get('tag_appearance') || ''
  const selected: Row | null = selectedId
    ? data?.items.find((q) => q.id === selectedId) || {
        id: selectedId,
        appearance_id: selectedAppearance,
        question: '',
        subject_label: null,
        topic_label: null,
        paper_id: paper,
        paper_title: 'Selected source',
        qnum: null,
        bank,
        report_count: 0,
        reported_at: null,
        invalid: false,
      }
    : null

  const [yearInput, setYearInput] = useState(year)
  const pendingNext = useRef(false)
  const learningNodes = learningChoices(nodes, subject)
  const subjects = useMemo(
    () => [
      ...new Map(
        nodes
          .filter((n) => n.level === 'subject')
          .map((n) => [
            learningSubjectId(n.id),
            {
              id: learningSubjectId(n.id),
              label:
                learningSubjectId(n.id) === 'gk-gs'
                  ? 'General Knowledge & Studies'
                  : n.label,
            },
          ]),
      ).values(),
    ],
    [nodes],
  )

  // Only show quick-tag chips whose subject_id (and topic_id if set) exist in live taxonomy nodes
  const validQuickTags = useMemo(() => {
    const nodeIds = new Set(nodes.map((n) => n.id))
    return QUICK_TAG_SPECS.filter(
      (spec) =>
        nodeIds.has(spec.subject_id) &&
        (!spec.topic_id || nodeIds.has(spec.topic_id)),
    )
  }, [nodes])

  const rowHints = useMemo(() => {
    const map = new Map<string, { id: 'mizo' | 'maths' | 'computer'; badge: string }>()
    for (const row of data?.items || []) {
      const hint = detectLikelyHint(row.question)
      if (hint) map.set(row.id, hint)
    }
    return map
  }, [data?.items])

  const likelyMizoRows = useMemo(
    () => (data?.items || []).filter((r) => rowHints.get(r.id)?.id === 'mizo'),
    [data?.items, rowHints],
  )

  function select(q: Row | null) {
    setParams(
      (old) => {
        const p = new URLSearchParams(old)
        for (const [key, value] of [
          ['tag_selected', q?.id || ''],
          ['tag_appearance', q?.appearance_id || ''],
        ]) {
          value ? p.set(key, value) : p.delete(key)
        }
        return p
      },
      { replace: true },
    )
  }

  function next() {
    if (!data || !selected) return
    const index = data.items.findIndex((q) => q.id === selected.id)
    if (index >= 0 && index + 1 < data.items.length) select(data.items[index + 1])
    else if (offset + 20 < data.total) {
      pendingNext.current = true
      page(20)
    } else {
      select(null)
      setNotice('End of this filtered page. Refresh to see published changes.')
    }
  }

  // Keyboard triage inside single-question Inspect & Fix view: J = Next, Esc = Back
  useEffect(() => {
    if (!selected) return
    const onKey = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return
      }
      if (e.key === 'Escape' && !busy) {
        select(null)
        setSnapshot(null)
      } else if ((e.key === 'j' || e.key === 'J') && !busy) {
        next()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  useEffect(() => {
    if (pendingNext.current && !loading && data?.items.length) {
      pendingNext.current = false
      select(data.items[0])
    }
  }, [data, loading])

  const request = useRef({ payload: '', key: crypto.randomUUID() })
  const saving = useRef(false)

  useEffect(() => {
    onBusy?.(busy)
    return () => onBusy?.(false)
  }, [busy, onBusy])

  function filter(key: string, value: string) {
    setPreview(null)
    setParams((old) => updateTagFilter(old, key, value), { replace: true })
  }

  useEffect(() => {
    setYearInput(year)
  }, [year])

  useEffect(() => {
    if (
      yearInput === year ||
      !(
        yearInput === '' ||
        (/^\d{4}$/.test(yearInput) && Number(yearInput) >= 1900 && Number(yearInput) <= 2100)
      )
    )
      return
    const timer = window.setTimeout(() => filter('tag_year', yearInput), 300)
    return () => window.clearTimeout(timer)
  }, [yearInput, year])

  useEffect(() => {
    let live = true
    reviewSession()
      .then((s) => {
        if (live) {
          setUser(s.user_id)
          setSolo(!!s.grants?.some((g) => g.role === 'owner' && g.subject_id === null))
        }
      })
      .catch((e) => {
        if (live) setError(e.message)
      })
    reviewRequest<Provider[]>('/admin/bank/organization/providers')
      .then(setProviders)
      .catch(() => {})
    reviewRequest<{ id: string; title: string }[]>('/collections')
      .then((m) => {
        if (live) setModules(m)
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    let live = true
    setLoading(true)
    setError('')
    const qs = new URLSearchParams({
      q: query,
      issue,
      offset: String(offset),
      bank,
      sort,
      subject,
      module,
      paper,
      topic,
      subtopic,
      path: pathScope,
      period,
      region,
      time_behavior: timeBehavior,
    })
    if (year) qs.set('year', year)
    const timer = window.setTimeout(
      () =>
        reviewRequest<{ items: Row[]; total: number }>('/admin/bank/tag-issues?' + qs)
          .then((r) => {
            if (live) setData(r)
          })
          .catch((e) => {
            if (live) {
              pendingNext.current = false
              setData(null)
              setError(e.message)
            }
          })
          .finally(() => {
            if (live) setLoading(false)
          }),
      250,
    )
    return () => {
      live = false
      clearTimeout(timer)
    }
  }, [
    query,
    issue,
    offset,
    bank,
    sort,
    subject,
    module,
    paper,
    topic,
    subtopic,
    pathScope,
    period,
    region,
    timeBehavior,
    year,
    refresh,
  ])

  useEffect(() => {
    let live = true
    setSnapshot(null)
    if (selected)
      reviewRequest<BankSnapshot>(
        '/review/questions/' +
          encodeURIComponent(selected.id) +
          (selectedAppearance || selected.appearance_id
            ? '?appearance_id=' + encodeURIComponent(selectedAppearance || selected.appearance_id)
            : ''),
      )
        .then((s) => {
          if (live) setSnapshot(s)
        })
        .catch((e) => {
          if (live) setError(e.message)
        })
    return () => {
      live = false
    }
  }, [selectedId, selectedAppearance, refresh])

  useEffect(() => {
    if (!batchId) return
    let live = true
    let timer: number | undefined
    let source: EventSource | undefined
    let lastDone = -1
    const load = (schedule: boolean) =>
      reviewRequest<Batch>('/admin/bank/retag/batches/' + encodeURIComponent(batchId))
        .then((b) => {
          if (!live) return
          setBatch(b)
          if (schedule && b.items.some((i) => ['publishing', 'accepted'].includes(i.state)))
            timer = window.setTimeout(() => load(true), 12000)
        })
        .catch((e) => {
          if (live) setError(e.message)
        })
    const fallback = () => {
      if (!live || timer !== undefined) return
      void load(true)
    }
    try {
      source = new EventSource(
        '/api/admin/bank/batches/' + encodeURIComponent(batchId) + '/events',
        { withCredentials: true },
      )
      source.onmessage = (event) => {
        if (!live) return
        try {
          const progress = JSON.parse(event.data) as { done?: number }
          if (progress.done !== lastDone) {
            lastDone = progress.done ?? -1
            void load(false)
          }
        } catch {
          /* ignore malformed frame */
        }
      }
      source.onerror = () => {
        source?.close()
        source = undefined
        fallback()
      }
    } catch {
      source = undefined
    }
    void load(!source)
    return () => {
      live = false
      clearTimeout(timer)
      source?.close()
    }
  }, [batchId, refresh])

  function toggle(q: Row) {
    setPreview(null)
    setSelection((old) =>
      old.some((x) => x.id === q.id)
        ? old.filter((x) => x.id !== q.id)
        : old.length < 20
          ? [...old, q]
          : old,
    )
  }

  function selectRows(rows: Row[]) {
    setPreview(null)
    setSelection((old) => {
      const byId = new Map(old.map((r) => [r.id, r]))
      for (const r of rows) {
        if (byId.size >= 20) break
        byId.set(r.id, r)
      }
      return [...byId.values()]
    })
  }

  async function showPreview() {
    setBusy(true)
    setError('')
    try {
      setPreview(
        (
          await reviewRequest<{ items: Preview[] }>('/admin/bank/retag/preview', {
            targets: selection.map((q) => ({
              question_id: q.id,
              appearance_id: q.appearance_id,
            })),
          })
        ).items,
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function apply() {
    if (!preview?.length || saving.current) return
    saving.current = true
    setBusy(true)
    setError('')
    const body = {
      targets: preview.map(({ question_id, appearance_id, baseline_hash, source_version }) => ({
        question_id,
        appearance_id,
        baseline_hash,
        source_version,
      })),
      classification: path,
      operation,
      reason: reason.trim(),
    }
    const payload = JSON.stringify(body)
    if (request.current.payload !== payload)
      request.current = { payload, key: crypto.randomUUID() }
    try {
      const result = await reviewRequest<{ id: string }>(
        '/admin/bank/retag/apply',
        body,
        request.current.key,
      )
      setParams((old) => {
        const p = new URLSearchParams(old)
        p.set('retag_batch', result.id)
        return p
      })
      setNotice('Admin decisions saved. Publication status appears below.')
      setPreview(null)
      setSelection([])
      setRefresh((n) => n + 1)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      saving.current = false
      setBusy(false)
    }
  }

  /** Solo-owner express flow: fetches baseline hashes + queues the batch in one click,
   *  keeping you right on your filtered list so you can sweep hundreds of rows smoothly. */
  async function expressOwnerApply(targetRows: Row[] = selection, targetPath: Classification = path) {
    if (!solo || !targetRows.length || !targetPath.subject_id || saving.current) return
    saving.current = true
    setBusy(true)
    setError('')
    try {
      const previewRes = await reviewRequest<{ items: Preview[] }>('/admin/bank/retag/preview', {
        targets: targetRows.map((q) => ({
          question_id: q.id,
          appearance_id: q.appearance_id,
        })),
      })
      if (!previewRes.items.length) {
        throw new Error('No eligible questions were returned for retagging.')
      }
      const body = {
        targets: previewRes.items.map(
          ({ question_id, appearance_id, baseline_hash, source_version }) => ({
            question_id,
            appearance_id,
            baseline_hash,
            source_version,
          }),
        ),
        classification: targetPath,
        operation,
        reason: reason.trim(),
      }
      const key = crypto.randomUUID()
      const result = await reviewRequest<{ id: string }>('/admin/bank/retag/apply', body, key)
      setLastBatchId(result.id)
      setNotice(
        `✓ Queued ${previewRes.items.length} question${previewRes.items.length === 1 ? '' : 's'} → ${pathLabel(targetPath, nodes)}. Publishing in background.`,
      )
      setPreview(null)
      setSelection((old) =>
        old.filter((r) => !targetRows.some((t) => t.id === r.id)),
      )
      setRefresh((n) => n + 1)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      saving.current = false
      setBusy(false)
    }
  }

  function page(delta: number) {
    setParams((old) => {
      const p = new URLSearchParams(old)
      p.set('tag_offset', String(Math.max(0, offset + delta)))
      return p
    })
  }

  return (
    <section aria-label="Find and fix learning tags" className="mt-4 min-w-0">
      <TaxonomyReviewProgress refresh={refresh} />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-display text-xl">Cross-check &amp; fast-fix questions</h2>
          <p className="mt-1 text-sm text-secondary">
            Filter by exam (e.g. LDC) and tag issue, bulk-select up to 20 rows with 1-click tag chips, or open any question to fix tags, answer, wording, or explanation.
          </p>
        </div>
        <button disabled={busy} className={BUTTON} onClick={() => setRefresh((n) => n + 1)}>
          Refresh
        </button>
      </div>

      {error && (
        <p role="alert" className="mt-3 break-words rounded-lg bg-mypick-soft p-3 text-sm">
          {error}
        </p>
      )}
      {notice && (
        <div
          role="status"
          className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-practice-soft p-3 text-sm"
        >
          <span>{notice}</span>
          {lastBatchId && !batchId && (
            <button
              type="button"
              className="text-xs font-bold text-link underline"
              onClick={() => filter('retag_batch', lastBatchId)}
            >
              View batch status →
            </button>
          )}
        </div>
      )}
      {needsMfa && (
        <p className="mt-3 text-sm">
          Verify your authenticator before applying changes.{' '}
          <Link className="text-link underline" to="/account/security">
            Account security →
          </Link>
        </p>
      )}

      <CleanupSavedViews
        params={params}
        onOpen={(view) =>
          setParams(new URLSearchParams({ tab: 'retag', ...Object.fromEntries(view) }))
        }
      />
      {tagReturn(params) && (
        <Link className={BUTTON + ' mt-3 inline-flex items-center text-link'} to={tagReturn(params)}>
          ← Return to review
        </Link>
      )}

      {batchId ? (
        <>
          <button
            disabled={busy}
            className={BUTTON + ' mt-3'}
            onClick={() => {
              filter('retag_batch', '')
              setBatch(null)
            }}
          >
            ← Back to question list
          </button>
          {batch?.items.some((i) => i.state === 'publication_failed') && (
            <button
              disabled={busy || needsMfa || !canWrite}
              className={BUTTON + ' ml-2 mt-3'}
              onClick={async () => {
                if (!batch) return
                setBusy(true)
                setError('')
                try {
                  await reviewRequest(
                    '/admin/bank/retag/batches/' + encodeURIComponent(batchId) + '/retry',
                    {
                      expected_versions: Object.fromEntries(
                        batch.items.map((i) => [i.id, i.lock_version]),
                      ),
                    },
                  )
                  setRefresh((n) => n + 1)
                  setNotice('Retry queued for the same tag decisions. Source checks still apply.')
                } catch (e) {
                  setError((e as Error).message)
                } finally {
                  setBusy(false)
                }
              }}
            >
              Retry failed tag publications together
            </button>
          )}
          {!batch ? (
            <p role="status" className="mt-3">
              Loading saved batch…
            </p>
          ) : (
            <div className="mt-3 grid gap-2">
              {batch.items.map((item) => (
                <article
                  key={item.id}
                  className="min-w-0 rounded-xl border border-hairline bg-card p-4"
                >
                  <SourceQuestionText text={item.record.question} />
                  <p className="mt-2 break-words text-sm">
                    {pathLabel(item.record.classification, nodes)} →{' '}
                    {pathLabel(item.classification, nodes)}
                  </p>
                  <p className="mt-1 break-words text-xs text-secondary">
                    Related:{' '}
                    {item.relatedClassifications?.map((p) => pathLabel(p, nodes)).join('; ') ||
                      'None'}
                  </p>
                  <p className="mt-2 text-sm font-semibold">
                    {item.state === 'published'
                      ? 'Applied'
                      : item.state === 'publication_failed'
                        ? 'Needs attention'
                        : item.state === 'publishing'
                          ? 'Publishing'
                          : item.state.replace(/_/g, ' ')}
                  </p>
                  <Link
                    className="inline-flex min-h-11 items-center text-sm text-link underline"
                    to={'/contributions/' + item.id}
                  >
                    Decision, history &amp;{' '}
                    {item.state === 'publication_failed' ? 'retry' : 'details'} →
                  </Link>
                </article>
              ))}
            </div>
          )}
        </>
      ) : selected ? (
        <>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <button
              disabled={busy}
              className={BUTTON}
              onClick={() => {
                select(null)
                setSnapshot(null)
                setNotice('Returned to your filtered list.')
                setRefresh((n) => n + 1)
              }}
            >
              ← Back to list (Esc)
            </button>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-muted">Keys: J next · Esc back</span>
              <button className={BUTTON} disabled={busy} onClick={next}>
                Skip / Next →
              </button>
            </div>
          </div>
          <article className="my-3 rounded-xl border border-hairline bg-card p-4">
            <p className="text-xs text-secondary">
              {selected.paper_title} · Q{selected.qnum || '?'} ·{' '}
              {providers.find((p) => p.id === selected.bank)?.label || selected.bank}
            </p>
            <div className="mt-2 text-base">
              <SourceQuestionText text={snapshot?.record.questionMarkup || selected.question} />
            </div>
            {snapshot && (
              <ol className="mt-3 grid gap-2 sm:grid-cols-2">
                {snapshot.record.options.map((o, i) => (
                  <li
                    key={i}
                    className={
                      'rounded-lg border p-3 text-sm ' +
                      (snapshot.record.answerIndex === i
                        ? 'border-correct bg-correct-soft font-semibold'
                        : 'border-hairline')
                    }
                  >
                    {String.fromCharCode(65 + i)}.{' '}
                    <SourceQuestionText
                      text={snapshot.record.optionsMarkup?.[i] || o || 'Missing option'}
                    />
                  </li>
                ))}
              </ol>
            )}
            {snapshot?.paper.source_pdf_url && (
              <a
                className="inline-flex min-h-11 items-center text-sm font-semibold text-link underline"
                href={snapshot.paper.source_pdf_url + '#page=' + (snapshot.record.page || 1)}
                target="_blank"
                rel="noreferrer"
              >
                Compare original PDF (p. {snapshot.record.page || 1}) ↗
              </a>
            )}
          </article>
          {snapshot ? (
            <fieldset disabled={needsMfa} className="min-w-0">
              <QuestionCorrectionEditor
                key={snapshot.baseline_token}
                snapshot={snapshot}
                user={user}
                onBusy={setBusy}
                onNext={next}
              />
            </fieldset>
          ) : (
            <p role="status">Opening source…</p>
          )}
          {snapshot && (
            <QuestionOrganizationContext
              key={snapshot.record.id + snapshot.baseline_token}
              snapshot={snapshot}
              canWrite={canWrite && !needsMfa}
            />
          )}
          <div className="mt-3 flex flex-wrap gap-3">
            <button className={BUTTON} disabled={busy} onClick={next}>
              Skip / next question →
            </button>
            <Link
              className={BUTTON + ' inline-flex items-center'}
              to={
                '/admin/bank?tab=organization&organization_paper=' +
                encodeURIComponent(snapshot?.paper.id || selected.paper_id)
              }
            >
              Source, scheme &amp; readiness →
            </Link>
          </div>
        </>
      ) : (
        <>
          {/* Fast 1-click Exam & Issue Triage Bar */}
          <div className="mt-4 space-y-3 rounded-xl border border-hairline bg-card p-4">
            <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Quick exam scope">
              <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-muted">
                Exam:
              </span>
              {EXAM_SHORTCUTS.map(([id, label]) => (
                <button
                  key={id || 'all'}
                  type="button"
                  disabled={busy}
                  aria-pressed={module === id}
                  onClick={() => filter('tag_module', id)}
                  className={
                    'min-h-9 rounded-pill border px-3 text-xs font-bold ' +
                    (module === id
                      ? 'border-ink bg-ink text-paper'
                      : 'border-hairline bg-paper text-ink hover:border-ink/60')
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Tag issue filters">
              <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-muted">
                Filter:
              </span>
              {(
                [
                  ['no-subject', 'No subject'],
                  ['no-topic', 'No topic'],
                  ['attention', 'Needs attention'],
                  ['reported', 'Reported'],
                  ['invalid', 'Invalid paths'],
                  ['all', 'All questions'],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  disabled={busy}
                  aria-pressed={issue === value}
                  className={
                    'min-h-9 rounded-pill border px-3 text-xs font-bold ' +
                    (issue === value
                      ? 'border-ink bg-ink text-paper'
                      : 'border-hairline bg-paper text-ink hover:border-ink/60')
                  }
                  onClick={() => filter('tag_issue', value)}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Always-visible primary filter controls */}
            <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
              <label className="grid gap-1 text-xs font-semibold text-secondary">
                Search wording / ID
                <input
                  className={INPUT + ' w-full'}
                  type="search"
                  maxLength={200}
                  placeholder="e.g. Mizo word, question text, or ID…"
                  value={query}
                  onChange={(e) => filter('tag_q', e.target.value)}
                />
              </label>

              <label className="grid gap-1 text-xs font-semibold text-secondary">
                Exam / Module
                <select
                  value={module}
                  className={INPUT}
                  onChange={(e) => filter('tag_module', e.target.value)}
                >
                  <option value="">All exam modules</option>
                  {modules.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1 text-xs font-semibold text-secondary">
                Current subject
                <select
                  value={subject}
                  className={INPUT}
                  onChange={(e) =>
                    setParams((old) => {
                      const p = updateTagFilter(old, 'tag_subject', e.target.value)
                      p.delete('tag_topic')
                      p.delete('tag_subtopic')
                      return p
                    })
                  }
                >
                  <option value="">All current subjects</option>
                  {subjects.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1 text-xs font-semibold text-secondary">
                Sort order
                <select
                  className={INPUT}
                  value={sort}
                  onChange={(e) => filter('tag_sort', e.target.value)}
                >
                  <option value="paper">Paper order (Q1 → Q100)</option>
                  <option value="priority">Priority, oldest report first</option>
                  <option value="reported">Most reported</option>
                </select>
              </label>
            </div>

            {(paper || module || subject || year) && (
              <div aria-label="Active tag search filters" className="flex flex-wrap gap-2">
                {[
                  [
                    paper ? 'tag_paper' : '',
                    paper
                      ? data?.items.find((q) => q.paper_id === paper)?.paper_title ||
                        paper.split('/').pop() ||
                        'Selected paper'
                      : '',
                  ],
                  [module ? 'tag_module' : '', modules.find((m) => m.id === module)?.title || module],
                  [subject ? 'tag_subject' : '', nodes.find((n) => n.id === subject)?.label || subject],
                  [year ? 'tag_year' : '', year ? 'Year: ' + year : ''],
                ]
                  .filter(([key]) => key)
                  .map(([key, label]) => (
                    <button
                      type="button"
                      key={key}
                      disabled={busy}
                      className="rounded-pill border border-hairline bg-paper px-3 py-1 text-xs font-semibold hover:border-ink"
                      onClick={() => filter(key, '')}
                    >
                      {label} ×
                    </button>
                  ))}
              </div>
            )}

            <details className="border-t border-hairline pt-2">
              <summary className="cursor-pointer py-1.5 text-xs font-semibold text-secondary">
                More filters (specific paper, topic, subtopic, year, bank, era)
              </summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <label className="grid gap-1 text-xs">
                  Bank
                  <select
                    className={INPUT}
                    value={bank}
                    onChange={(e) => filter('tag_bank', e.target.value)}
                  >
                    <option value="all">All sources</option>
                    {providers.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Exam year
                  <input
                    aria-label="Tag exam year"
                    type="number"
                    min={1900}
                    max={2100}
                    placeholder="All years"
                    value={yearInput}
                    onChange={(e) => {
                      setYearInput(e.target.value)
                      setPreview(null)
                    }}
                    className={INPUT}
                  />
                </label>
                <label className="grid gap-1 text-xs">
                  Current topic
                  <select
                    aria-label="Current topic"
                    className={INPUT}
                    value={topic}
                    onChange={(e) =>
                      setParams((old) => {
                        const p = updateTagFilter(old, 'tag_topic', e.target.value)
                        p.delete('tag_subtopic')
                        return p
                      })
                    }
                  >
                    <option value="">All topics</option>
                    {learningNodes
                      .filter(
                        (n) =>
                          n.path.topic_id &&
                          !n.path.subtopic_id &&
                          (!subject ||
                            learningSubjectId(n.path.subject_id) === learningSubjectId(subject)),
                      )
                      .map((n) => (
                        <option key={n.id} value={n.path.topic_id!}>
                          {n.label}
                        </option>
                      ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Subtopic
                  <select
                    aria-label="Current subtopic"
                    className={INPUT}
                    value={subtopic}
                    onChange={(e) => filter('tag_subtopic', e.target.value)}
                  >
                    <option value="">All subtopics</option>
                    {nodes
                      .filter((n) => n.level === 'subtopic' && (!topic || n.parent_id === topic))
                      .map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.label}
                        </option>
                      ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Match path
                  <select
                    aria-label="Classification path scope"
                    className={INPUT}
                    value={pathScope}
                    onChange={(e) => filter('tag_path', e.target.value)}
                  >
                    <option value="primary">Primary tags</option>
                    <option value="related">Related tags</option>
                    <option value="any">Any approved path</option>
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Region
                  <select
                    className={INPUT}
                    value={region}
                    onChange={(e) => filter('tag_region', e.target.value)}
                  >
                    {[
                      ['', 'All regions'],
                      ['mizoram', 'Mizoram'],
                      ['india', 'India'],
                      ['international', 'International'],
                      ['other', 'Other region'],
                    ].map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Exam era
                  <select
                    aria-label="Exam era"
                    className={INPUT}
                    value={period}
                    onChange={(e) => filter('tag_period', e.target.value)}
                  >
                    <option value="all">All eras</option>
                    <option value="legacy">Legacy exams</option>
                    <option value="current">Current exams</option>
                    <option value="unknown">Era not assigned</option>
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Time context
                  <select
                    aria-label="Time context"
                    className={INPUT}
                    value={timeBehavior}
                    onChange={(e) => filter('tag_time', e.target.value)}
                  >
                    {[
                      ['all', 'All time contexts'],
                      ['unknown', 'Unknown'],
                      ['static', 'Static concept'],
                      ['dated-event', 'Dated event / edition'],
                      ['changes-over-time', 'Changes over time'],
                    ].map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="sm:col-span-2 lg:col-span-3">
                  <EditorialSourcePicker
                    value={paper}
                    bank={bank}
                    module={module}
                    onChange={(id) => filter('tag_paper', id)}
                  />
                </div>
              </div>
            </details>
          </div>

          {/* Sticky Express Bulk-Retag Panel when >= 1 row selected */}
          {selection.length > 0 && (
            <div className="sticky top-2 z-20 mt-4 rounded-xl border-2 border-ink bg-card p-4 shadow-lg">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong className="text-sm text-ink">
                  {selection.length} / 20 selected · choose target tag
                </strong>
                <button
                  type="button"
                  disabled={busy}
                  className={BUTTON}
                  onClick={() => {
                    setSelection([])
                    setPreview(null)
                  }}
                >
                  Clear selection
                </button>
              </div>

              <fieldset disabled={busy || needsMfa || !canWrite} className="mt-3 min-w-0 space-y-3">
                {/* 1-Click Quick-Tag Chips */}
                {validQuickTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5" role="group" aria-label="Quick tag targets">
                    {validQuickTags.map((spec) => {
                      const active =
                        path.subject_id === spec.subject_id &&
                        (path.topic_id || undefined) === spec.topic_id
                      return (
                        <button
                          key={spec.label}
                          type="button"
                          onClick={() => {
                            setPath({
                              subject_id: spec.subject_id,
                              ...(spec.topic_id ? { topic_id: spec.topic_id } : {}),
                            })
                            setPreview(null)
                          }}
                          className={
                            'min-h-9 rounded-pill border px-3 text-xs font-bold ' +
                            (active
                              ? 'border-ink bg-ink text-paper'
                              : 'border-hairline bg-paper text-ink hover:border-ink')
                          }
                        >
                          {spec.label}
                        </button>
                      )
                    })}
                  </div>
                )}

                <div className="grid gap-3 sm:grid-cols-[200px_minmax(0,1fr)]">
                  <label className="block text-xs font-semibold text-secondary">
                    Operation
                    <select
                      className={INPUT + ' mt-1 w-full'}
                      value={operation}
                      onChange={(e) => {
                        setOperation(e.target.value)
                        setPreview(null)
                      }}
                    >
                      <option value="replace_primary">Replace primary tags</option>
                      <option value="add_related">Add related topic</option>
                      <option value="remove_related">Remove related topic</option>
                    </select>
                  </label>
                  <div>
                    <SearchableTaxonomyPicker
                      value={path}
                      nodes={nodes}
                      onChange={(p) => {
                        setPath(p)
                        setPreview(null)
                      }}
                    />
                  </div>
                </div>

                {!solo && (
                  <label className="block text-xs font-semibold text-secondary">
                    Why do these tags fit?
                    <textarea
                      minLength={20}
                      maxLength={4000}
                      rows={2}
                      className={INPUT + ' mt-1 w-full'}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="One explanation supporting the selected questions and path."
                    />
                  </label>
                )}

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {solo && (
                    <button
                      type="button"
                      disabled={busy || !path.subject_id}
                      className={BUTTON + ' border-ink bg-ink text-paper'}
                      onClick={() => void expressOwnerApply()}
                    >
                      {busy
                        ? 'Applying…'
                        : `⚡ Apply ${path.subject_id ? pathLabel(path, nodes) : 'tag'} to ${selection.length} selected`}
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={busy || !path.subject_id || (!solo && reason.trim().length < 20)}
                    className={BUTTON}
                    onClick={() => void showPreview()}
                  >
                    Preview {selection.length} changes
                  </button>
                </div>
              </fieldset>
            </div>
          )}

          {preview && (
            <section
              aria-label="Confirm tag changes"
              className="mt-3 rounded-xl border border-ink bg-card p-4"
            >
              <h3 className="font-display text-xl">Apply these changes?</h3>
              {preview.map((p) => (
                <article key={p.question_id} className="mt-3 border-b border-hairline pb-3">
                  <SourceQuestionText text={p.record.question} />
                  <p className="mt-2 break-words text-sm">
                    {operation === 'replace_primary'
                      ? pathLabel(p.record.classification, nodes) + ' → '
                      : operation === 'add_related'
                        ? 'Add related: '
                        : 'Remove related: '}
                    {pathLabel(path, nodes)}
                  </p>
                  <p className="mt-1 text-xs text-secondary">
                    {p.source.title} · Used in {p.shared_papers} printed appearance(s)
                  </p>
                  <button
                    disabled={busy}
                    className={BUTTON + ' mt-2'}
                    onClick={() => {
                      setPreview((old) =>
                        old?.filter((q) => q.question_id !== p.question_id) || null,
                      )
                      setSelection((old) => old.filter((q) => q.id !== p.question_id))
                    }}
                  >
                    Exclude this question
                  </button>
                </article>
              ))}
              <button
                type="button"
                disabled={busy || needsMfa || !preview.length}
                className={BUTTON + ' mt-4 border-ink bg-ink text-paper'}
                onClick={() => void apply()}
              >
                {busy ? 'Saving…' : 'Apply tags to ' + preview.length + ' questions'}
              </button>
            </section>
          )}

          {/* Question list with 1-click page & likely-Mizo bulk selectors */}
          <div aria-busy={loading} className="mt-4 rounded-xl border border-hairline bg-card">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline p-3">
              <p role="status" className="text-xs font-semibold text-secondary">
                {loading
                  ? 'Loading matching questions…'
                  : `${(data?.total || 0).toLocaleString('en-IN')} matching questions`}
              </p>
              {canWrite && !loading && !!data?.items.length && (
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={busy || needsMfa}
                    className="min-h-8 rounded-pill border border-hairline bg-paper px-3 text-xs font-bold hover:border-ink"
                    onClick={() => selectRows(data.items)}
                  >
                    ☑ Select page ({Math.min(20, data.items.length)})
                  </button>
                  {likelyMizoRows.length > 0 && (
                    <button
                      type="button"
                      disabled={busy || needsMfa}
                      className="min-h-8 rounded-pill border border-emerald-600/40 bg-emerald-500/10 px-3 text-xs font-bold text-emerald-800 dark:text-emerald-300"
                      onClick={() => {
                        selectRows(likelyMizoRows)
                        const mizoSpec = validQuickTags.find((t) => t.subject_id === 'mizo')
                        if (mizoSpec) {
                          setPath({
                            subject_id: mizoSpec.subject_id,
                            ...(mizoSpec.topic_id ? { topic_id: mizoSpec.topic_id } : {}),
                          })
                        }
                      }}
                    >
                      🌿 Select likely Mizo ({likelyMizoRows.length})
                    </button>
                  )}
                  {selection.length > 0 && (
                    <button
                      type="button"
                      disabled={busy}
                      className="min-h-8 rounded-pill border border-hairline px-2.5 text-xs font-semibold text-secondary"
                      onClick={() => {
                        setSelection([])
                        setPreview(null)
                      }}
                    >
                      Clear
                    </button>
                  )}
                </div>
              )}
            </div>

            {!loading &&
              data?.items.map((q) => {
                const hint = rowHints.get(q.id)
                const isChecked = selection.some((x) => x.id === q.id)
                return (
                  <article
                    key={q.id}
                    className={
                      'flex min-w-0 gap-3 border-b border-hairline p-4 transition ' +
                      (isChecked ? 'bg-practice-soft/40' : '')
                    }
                  >
                    {canWrite && (
                      <input
                        aria-label={'Select ' + q.id}
                        type="checkbox"
                        className="mt-1 h-5 w-5 shrink-0 cursor-pointer"
                        disabled={busy || needsMfa || (!isChecked && selection.length >= 20)}
                        checked={isChecked}
                        onChange={() => toggle(q)}
                      />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="mb-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                        <span className="rounded-pill bg-paper px-2.5 py-0.5 font-mono font-semibold text-ink">
                          {q.subject_label || '⚠ No subject'}
                          {q.topic_label ? ` / ${q.topic_label}` : ''}
                        </span>
                        {hint && (
                          <span className="rounded-pill border border-emerald-600/30 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-[11px] font-bold text-emerald-800 dark:text-emerald-300">
                            {hint.badge}
                          </span>
                        )}
                        {q.invalid && (
                          <span className="rounded-pill bg-wrong-soft px-2 py-0.5 font-mono text-[11px] font-bold text-wrong-dark">
                            Invalid path
                          </span>
                        )}
                        {q.report_count > 0 && (
                          <span className="rounded-pill bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-bold text-amber-800 dark:text-amber-300">
                            {q.report_count} report{q.report_count === 1 ? '' : 's'}
                          </span>
                        )}
                      </div>
                      <SourceQuestionText text={q.question} />
                      <p className="mt-1.5 break-words text-xs text-secondary">
                        {q.paper_title} · Q{q.qnum || '?'} ·{' '}
                        {providers.find((p) => p.id === q.bank)?.label || q.bank}
                      </p>
                      <div className="mt-2.5 flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          disabled={busy}
                          className={BUTTON + ' text-link'}
                          onClick={() => select(q)}
                        >
                          Inspect &amp; fix (Tags / Answer / Text) →
                        </button>
                        {solo && hint?.id === 'mizo' && (
                          <button
                            type="button"
                            disabled={busy || needsMfa}
                            className="min-h-10 rounded-pill border border-emerald-600/40 bg-emerald-500/10 px-3.5 text-xs font-bold text-emerald-800 hover:bg-emerald-500/20 dark:text-emerald-300"
                            onClick={() =>
                              void expressOwnerApply([q], {
                                subject_id: 'mizo',
                                topic_id: 'mizo/grammar',
                              })
                            }
                          >
                            ⚡ Tag Mizo / Grammar
                          </button>
                        )}
                      </div>
                    </div>
                  </article>
                )
              })}

            {!loading && !data?.items.length && (
              <p className="p-5 text-sm text-secondary">No questions match these filters.</p>
            )}

            <nav
              aria-label="Tag question pages"
              className="flex flex-wrap items-center justify-between gap-2 p-3"
            >
              <button
                disabled={busy || loading || !offset}
                className={BUTTON}
                onClick={() => page(-20)}
              >
                ← Previous 20
              </button>
              <span className="font-mono text-xs text-secondary">
                {data?.total ? offset + 1 : 0}–{Math.min(offset + 20, data?.total || 0)} of{' '}
                {(data?.total || 0).toLocaleString('en-IN')}
              </span>
              <button
                disabled={busy || loading || offset + 20 >= (data?.total || 0)}
                className={BUTTON}
                onClick={() => page(20)}
              >
                Next 20 →
              </button>
            </nav>
          </div>
        </>
      )}
    </section>
  )
}
