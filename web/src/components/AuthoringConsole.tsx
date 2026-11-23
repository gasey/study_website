import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { reviewRequest, type TaxonomyNode } from '../lib/review'

type QueueKind = 'untagged' | 'legacy' | 'reported' | 'conflicts' | 'missed' | 'no-explanation'

interface VoiceWarning {
  code: string
  match: string
  guidance: string
}

/** Contribution-producing edit kinds. decide() accepts all of these
 *  (`admin_bank_edits.py:50`), but only one may be in flight per question — it
 *  flips the contribution to `accepted` immediately, and the next write is
 *  rejected while that is unpublished (`admin_bank_edits.py:75-77`). */
type EditKind = 'transcription' | 'taxonomy' | 'explanation' | 'source_reference'

const EDIT_KIND_LABELS: Record<EditKind, string> = {
  transcription: 'text & options',
  taxonomy: 'tags',
  explanation: 'explanation',
  source_reference: 'source locator',
}

interface QueueItem {
  id: string
  appearance_id: string
  paper_id: string
  qnum: string | null
  page: number | null
  question: string
  options: (string | null)[]
  answer_index: number | null
  answer_source: string | null
  explanation: string | null
  subject_id: string | null
  topic_id: string | null
  subtopic_id: string | null
  period: 'legacy' | 'current' | 'unknown'
  time_behavior: 'static' | 'dated-event' | 'changes-over-time' | 'unknown'
  scheme_status: 'current' | 'superseded' | 'unknown'
  superseded_note: string
  baseline_hash: string
  source_version: string
  voice_warnings: VoiceWarning[]
  shape?: string
  official_answer?: string | null
  solution_answer?: string | null
  attempts?: number | null
  accuracy?: number | null
}

/** Keyboard-first authoring console (§VI.6 / §VII.11, Phases V.16–V.17).
 *  - Left queue prefetches up to 50 rows with `baseline_hash` and `source_version`
 *    so moving (`j` / `k`) needs zero round-trips.
 *  - Search-as-you-type taxonomy picker over the active registry.
 *  - `.` repeats the previous question's full taxonomy path.
 *  - `⌘↵` / `Ctrl+↵` saves and advances without navigating; publish status renders
 *    per row in place.
 *  - Inline currency/context editor (`period`, `time_behavior`, `scheme_status`)
 *    and explanation voice lint warnings. */
export default function AuthoringConsole({ taxonomy }: { taxonomy: TaxonomyNode[] }) {
  const [queueKind, setQueueKind] = useState<QueueKind>('untagged')
  const [items, setItems] = useState<QueueItem[]>([])
  const [index, setIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [rowStatus, setRowStatus] = useState<Record<string, 'saving' | 'saved' | 'error'>>({})
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})

  // Form state for active question
  const [taxFilter, setTaxFilter] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [subtopicId, setSubtopicId] = useState('')
  const [period, setPeriod] = useState<'legacy' | 'current' | 'unknown'>('unknown')
  const [timeBehavior, setTimeBehavior] = useState<'static' | 'dated-event' | 'changes-over-time' | 'unknown'>('unknown')
  const [schemeStatus, setSchemeStatus] = useState<'current' | 'superseded' | 'unknown'>('unknown')
  const [supersededNote, setSupersededNote] = useState('')
  const [explanation, setExplanation] = useState('')
  const [note, setNote] = useState('')
  const [voiceWarnings, setVoiceWarnings] = useState<VoiceWarning[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [bulkStatus, setBulkStatus] = useState('')
  // Explanations are per-question text, so a "batch" here means publishing several
  // together in ONE bank write — not applying one text to many. That is what the
  // worker's grouped apply exists for (§VIII.5.2 #4): 10 explanations become one
  // sync-bank.sh run instead of ten. Keyed by canonical id.
  const [explanationDrafts, setExplanationDrafts] = useState<Record<string, string>>({})

  // Source text / options / locator (§VIII.5.1)
  const [questionText, setQuestionText] = useState('')
  const [optionDrafts, setOptionDrafts] = useState<(string | null)[]>([])
  const [answerIndex, setAnswerIndex] = useState<number | null>(null)
  const [qnum, setQnum] = useState('')
  const [page, setPage] = useState('')
  const [chosenKind, setChosenKind] = useState<EditKind | null>(null)

  const lastTagRef = useRef<{ subjectId: string; topicId: string; subtopicId: string } | null>(null)
  const current = items[index] || null

  const loadQueue = useCallback(async (kind: QueueKind) => {
    setLoading(true)
    setError('')
    setSelectedIds([])
    setExplanationDrafts({})
    try {
      const res = await reviewRequest<{ items: QueueItem[] }>(
        `/admin/bank/authoring-queue?queue=${encodeURIComponent(kind)}&limit=50`,
      )
      setItems(res.items || [])
      setIndex(0)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load authoring queue.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadQueue(queueKind)
  }, [queueKind, loadQueue])

  useEffect(() => {
    if (!current) return
    setSubjectId(current.subject_id || '')
    setTopicId(current.topic_id || '')
    setSubtopicId(current.subtopic_id || '')
    setPeriod(current.period || 'unknown')
    setTimeBehavior(current.time_behavior || 'unknown')
    setSchemeStatus(current.scheme_status || 'unknown')
    setSupersededNote(current.superseded_note || '')
    setExplanation(current.explanation || '')
    setVoiceWarnings(current.voice_warnings || [])
    setNote('')
    setQuestionText(current.question || '')
    setOptionDrafts([...(current.options || [])])
    setAnswerIndex(current.answer_index)
    setQnum(current.qnum || '')
    setPage(current.page == null ? '' : String(current.page))
    setChosenKind(null)
  }, [current?.id])

  const subjects = useMemo(() => taxonomy.filter((n) => n.level === 'subject'), [taxonomy])
  const topics = useMemo(
    () => taxonomy.filter((n) => n.level === 'topic' && (!subjectId || n.parent_id === subjectId)),
    [taxonomy, subjectId],
  )
  const subtopics = useMemo(
    () => taxonomy.filter((n) => n.level === 'subtopic' && (!topicId || n.parent_id === topicId)),
    [taxonomy, topicId],
  )
  const quickMatches = useMemo(() => {
    const q = taxFilter.trim().toLowerCase()
    if (q.length < 2) return []
    return taxonomy.filter((n) => n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)).slice(0, 8)
  }, [taxonomy, taxFilter])

  function applyTaxonomyNode(node: TaxonomyNode) {
    if (node.level === 'subject') {
      setSubjectId(node.id)
      setTopicId('')
      setSubtopicId('')
    } else if (node.level === 'topic') {
      setSubjectId(node.parent_id || '')
      setTopicId(node.id)
      setSubtopicId('')
    } else {
      const parentTopic = taxonomy.find((t) => t.id === node.parent_id)
      setSubjectId(parentTopic?.parent_id || '')
      setTopicId(node.parent_id || '')
      setSubtopicId(node.id)
    }
    setTaxFilter('')
  }

  const optionsChanged = useMemo(() => {
    const base = current?.options || []
    if (base.length !== optionDrafts.length) return true
    return optionDrafts.some((o, i) => (o ?? '') !== (base[i] ?? ''))
  }, [current, optionDrafts])

  const basePage = current?.page == null ? '' : String(current.page)

  const contextChanged =
    !!current &&
    (timeBehavior !== current.time_behavior ||
      schemeStatus !== current.scheme_status ||
      period !== current.period)

  /** Which contribution-producing kinds the operator has touched. */
  const dirty = useMemo((): Record<EditKind, boolean> => {
    if (!current) {
      return { transcription: false, taxonomy: false, explanation: false, source_reference: false }
    }
    return {
      transcription: questionText !== (current.question || '') || optionsChanged,
      taxonomy:
        !!subjectId &&
        (subjectId !== (current.subject_id || '') ||
          topicId !== (current.topic_id || '') ||
          subtopicId !== (current.subtopic_id || '')),
      explanation:
        explanation.trim() !== (current.explanation || '').trim() && explanation.trim().length >= 20,
      source_reference: qnum !== (current.qnum || '') || page !== basePage,
    }
  }, [current, questionText, optionsChanged, subjectId, topicId, subtopicId, explanation, qnum, page, basePage])

  const dirtyKinds = useMemo(() => (Object.keys(dirty) as EditKind[]).filter((k) => dirty[k]), [dirty])
  const activeKind: EditKind | null = (chosenKind && dirty[chosenKind] ? chosenKind : dirtyKinds[0]) || null

  /** Would this option edit move the recorded answer? decide() then requires a
   *  worked explanation or mapped official-key evidence (`admin_bank_edits.py:73`). */
  const answerTextMoves = useMemo(() => {
    if (!current || !optionsChanged || current.answer_index == null) return false
    const before = current.options?.[current.answer_index] ?? null
    const after = answerIndex == null ? null : optionDrafts[answerIndex] ?? null
    return before !== after
  }, [current, optionsChanged, answerIndex, optionDrafts])

  /** The server caps a batch at 20 targets; mirror it so the cap is visible here. */
  const BATCH_CAP = 20
  const draftIds = useMemo(() => Object.keys(explanationDrafts), [explanationDrafts])

  const addToBatch = useCallback(() => {
    if (!current) return
    const text = explanation.trim()
    if (text.length < 20) {
      setRowErrors((prev) => ({ ...prev, [current.id]: 'An explanation needs at least 20 characters.' }))
      return
    }
    if (!(current.id in explanationDrafts) && draftIds.length >= BATCH_CAP) {
      setBulkStatus(`A batch publishes at most ${BATCH_CAP} explanations. Publish these first.`)
      return
    }
    setExplanationDrafts((prev) => ({ ...prev, [current.id]: text }))
    setRowErrors((prev) => {
      const next = { ...prev }
      delete next[current.id]
      return next
    })
    setBulkStatus('')
    setIndex((i) => Math.min(items.length - 1, i + 1))
  }, [current, explanation, explanationDrafts, draftIds.length, items.length])

  async function publishExplanationBatch() {
    type Target = { question_id: string; appearance_id: string; baseline_hash: string; source_version: string; explanation: string }
    const targets: Target[] = []
    for (const qid of draftIds) {
      const row = items.find((it) => it.id === qid)
      if (row) {
        targets.push({
          question_id: qid,
          appearance_id: row.appearance_id,
          baseline_hash: row.baseline_hash,
          source_version: row.source_version,
          explanation: explanationDrafts[qid],
        })
      }
    }
    if (!targets.length) return
    setBulkStatus(`Publishing ${targets.length} explanation${targets.length === 1 ? '' : 's'} as one batch…`)
    setRowStatus((prev) => {
      const next = { ...prev }
      targets.forEach((t) => { next[t.question_id] = 'saving' })
      return next
    })
    try {
      await reviewRequest(
        '/admin/bank/explanations/apply',
        { targets, reason: note },
        'expl-batch-' + crypto.randomUUID(),
      )
      setRowStatus((prev) => {
        const next = { ...prev }
        targets.forEach((t) => { next[t.question_id] = 'saved' })
        return next
      })
      setBulkStatus(`Published ${targets.length} explanation${targets.length === 1 ? '' : 's'} in one bank write.`)
      setExplanationDrafts({})
    } catch (e) {
      setRowStatus((prev) => {
        const next = { ...prev }
        targets.forEach((t) => { next[t.question_id] = 'error' })
        return next
      })
      setBulkStatus(e instanceof Error ? e.message : 'Batch publish failed')
    }
  }

  const saveAndNext = useCallback(async () => {
    if (!current) return
    const qid = current.id
    const advance = () => setIndex((i) => Math.min(items.length - 1, i + 1))
    if (!activeKind && !contextChanged) {
      advance()
      return
    }
    if (activeKind === 'transcription' && answerTextMoves && explanation.trim().length < 20) {
      setRowErrors((prev) => ({
        ...prev,
        [qid]: 'Moving the recorded answer needs a worked explanation of at least 20 characters.',
      }))
      return
    }
    setRowStatus((prev) => ({ ...prev, [qid]: 'saving' }))
    setRowErrors((prev) => {
      const next = { ...prev }
      delete next[qid]
      return next
    })
    const base = {
      canonical_id: current.id,
      appearance_id: current.appearance_id,
      note,
      baseline_hash: current.baseline_hash,
      source_version: current.source_version,
    }
    try {
      // Currency/context writes `bank_question_contexts` — versioned metadata,
      // not a contribution — so it never trips the one-correction-in-flight
      // guard and may always ride along with the chosen edit.
      if (contextChanged) {
        await reviewRequest(
          '/admin/bank/contexts/apply',
          {
            targets: [
              {
                question_id: current.id,
                appearance_id: current.appearance_id,
                source_version: current.source_version,
                time_behavior: timeBehavior,
                scheme_status: schemeStatus,
                superseded_note: supersededNote,
              },
            ],
            paper_period: period !== current.period ? period : null,
            reason: note,
          },
          'ctx-' + crypto.randomUUID(),
        )
      }

      // Exactly one contribution-producing correction per save: decide() flips
      // the contribution to `accepted` immediately and rejects the next write
      // until it publishes (`admin_bank_edits.py:75-77`).
      if (activeKind === 'taxonomy') {
        await reviewRequest(
          '/admin/bank/routine-edits',
          {
            ...base,
            kind: 'taxonomy',
            patch: {
              classification: {
                subject_id: subjectId,
                topic_id: topicId || null,
                subtopic_id: subtopicId || null,
              },
            },
          },
          'tax-' + crypto.randomUUID(),
        )
        lastTagRef.current = { subjectId, topicId, subtopicId }
      } else if (activeKind === 'transcription') {
        const patch: Record<string, unknown> = {}
        if (questionText !== (current.question || '')) patch.question = questionText
        if (optionsChanged) {
          patch.options = optionDrafts
          // review_policy.validate_target refuses an option change that does not
          // explicitly re-map an existing recorded answer.
          if (current.answer_index != null) patch.answerIndex = answerIndex
        }
        if (answerTextMoves) patch.explanation = explanation.trim()
        await reviewRequest('/admin/bank/routine-edits', { ...base, kind: 'transcription', patch }, 'txn-' + crypto.randomUUID())
      } else if (activeKind === 'source_reference') {
        const patch: Record<string, unknown> = {}
        if (qnum !== (current.qnum || '')) patch.qnum = qnum
        if (page !== basePage) patch.page = page.trim() === '' ? null : Number(page)
        await reviewRequest('/admin/bank/routine-edits', { ...base, kind: 'source_reference', patch }, 'src-' + crypto.randomUUID())
      } else if (activeKind === 'explanation') {
        await reviewRequest(
          '/admin/bank/explanations/apply',
          {
            targets: [
              {
                question_id: current.id,
                appearance_id: current.appearance_id,
                baseline_hash: current.baseline_hash,
                source_version: current.source_version,
                explanation: explanation.trim(),
              },
            ],
            reason: note,
          },
          'exp-' + crypto.randomUUID(),
        )
      }

      setRowStatus((prev) => ({ ...prev, [qid]: 'saved' }))
      advance()
    } catch (e) {
      setRowStatus((prev) => ({ ...prev, [qid]: 'error' }))
      setRowErrors((prev) => ({
        ...prev,
        [qid]: e instanceof Error ? e.message : 'Save failed',
      }))
    }
  }, [
    current,
    activeKind,
    contextChanged,
    answerTextMoves,
    optionsChanged,
    questionText,
    optionDrafts,
    answerIndex,
    qnum,
    page,
    basePage,
    subjectId,
    topicId,
    subtopicId,
    period,
    timeBehavior,
    schemeStatus,
    supersededNote,
    explanation,
    note,
    items.length,
  ])

  async function bulkApplyContext() {
    if (!selectedIds.length) return
    const selectedItems = items.filter((it) => selectedIds.includes(it.id))
    const batches: QueueItem[][] = []
    for (let i = 0; i < selectedItems.length; i += 20) batches.push(selectedItems.slice(i, i + 20))
    setBulkStatus(`Applying 0 of ${batches.length} batches…`)
    try {
      for (let b = 0; b < batches.length; b++) {
        setBulkStatus(`Applying ${b + 1} of ${batches.length} batches…`)
        await reviewRequest(
          '/admin/bank/contexts/apply',
          {
            targets: batches[b].map((it) => ({
              question_id: it.id,
              appearance_id: it.appearance_id,
              source_version: it.source_version,
              time_behavior: timeBehavior,
              scheme_status: schemeStatus,
              superseded_note: supersededNote,
            })),
            paper_period: period !== 'unknown' ? period : null,
            reason: note || 'Bulk context update from authoring console.',
          },
          'bulkctx-' + crypto.randomUUID(),
        )
      }
      setBulkStatus(`Applied context to ${selectedItems.length} questions (${batches.length} batches).`)
      setSelectedIds([])
    } catch (e) {
      setBulkStatus(e instanceof Error ? e.message : 'Bulk apply failed')
    }
  }

  // Keyboard shortcuts: j/k move, . repeat last tag, Cmd/Ctrl+Enter save & next
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      const typing = target && (/INPUT|TEXTAREA|SELECT/.test(target.tagName) || target.isContentEditable)
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'Enter') {
        e.preventDefault()
        addToBatch()
        return
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault()
        void saveAndNext()
        return
      }
      if (typing) return
      if (e.key === 'j') {
        e.preventDefault()
        setIndex((i) => Math.min(Math.max(0, items.length - 1), i + 1))
      } else if (e.key === 'k') {
        e.preventDefault()
        setIndex((i) => Math.max(0, i - 1))
      } else if (e.key === '.' && lastTagRef.current) {
        e.preventDefault()
        setSubjectId(lastTagRef.current.subjectId)
        setTopicId(lastTagRef.current.topicId)
        setSubtopicId(lastTagRef.current.subtopicId)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [items.length, saveAndNext, addToBatch])

  async function runVoiceCheck() {
    try {
      const res = await reviewRequest<{ warnings: VoiceWarning[] }>('/admin/bank/explanations/voice-check', {
        explanation,
      })
      setVoiceWarnings(res.warnings || [])
    } catch {
      // Non-blocking warning helper
    }
  }

  return (
    <div className="mt-4 grid items-start gap-5 lg:grid-cols-[300px_minmax(0,1fr)]" data-screen="authoring-console">
      {/* Left Queue */}
      <aside className="rounded-xl border border-hairline bg-card p-4">
        <div className="flex flex-wrap gap-1.5 border-b border-hairline pb-3" role="group" aria-label="Queue filter">
          {(
            [
              ['untagged', 'Untagged'],
              ['legacy', 'Legacy'],
              ['reported', 'Reported'],
              ['conflicts', 'Conflicts'],
              ['missed', 'Most missed'],
              ['no-explanation', 'Needs explanation'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              aria-pressed={queueKind === id}
              onClick={() => setQueueKind(id)}
              className={
                'min-h-9 rounded-lg border px-2.5 text-xs font-semibold ' +
                (queueKind === id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
              }
            >
              {label}
            </button>
          ))}
        </div>

        <p className="mt-2 font-mono text-xs text-muted">
          j/k move · . repeat tag · ⌘↵ save · ⌘⇧↵ queue
        </p>
        <p className="mt-1 text-xs text-secondary">
          Edits text, options, tags, currency, explanation and the printed locator.
        </p>

        {loading && <p role="status" className="mt-3 text-sm text-secondary">Prefetching 50 rows…</p>}
        {error && <p role="alert" className="mt-3 text-sm text-wrong-dark">{error}</p>}

        <ul className="mt-3 max-h-[60vh] divide-y divide-hairline overflow-y-auto">
          {items.map((it, idx) => {
            const st = rowStatus[it.id]
            const active = idx === index
            return (
              <li key={it.id} className="flex items-center gap-2 py-2">
                <input
                  type="checkbox"
                  aria-label={`Select ${it.id}`}
                  checked={selectedIds.includes(it.id)}
                  onChange={() =>
                    setSelectedIds((prev) =>
                      prev.includes(it.id) ? prev.filter((x) => x !== it.id) : [...prev, it.id],
                    )
                  }
                />
                <button
                  type="button"
                  onClick={() => setIndex(idx)}
                  className={
                    'min-w-0 flex-1 rounded-md px-2 py-1 text-left text-xs ' +
                    (active ? 'bg-canvas font-bold text-ink' : 'text-secondary hover:bg-paper')
                  }
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-mono">Q{it.qnum || idx + 1}</span>
                    {st && (
                      <span
                        className={
                          'font-mono text-xs ' +
                          (st === 'saved' ? 'text-correct-dark' : st === 'error' ? 'text-wrong-dark' : 'text-muted')
                        }
                      >
                        {st === 'saved' ? '✓' : st === 'error' ? '!' : '…'}
                      </span>
                    )}
                  </div>
                  <div className="truncate text-ink">{it.question}</div>
                  {it.id in explanationDrafts && (
                    <div className="font-mono text-xs font-semibold text-link">queued for batch</div>
                  )}
                  {it.attempts ? (
                    <div className="font-mono text-xs text-muted">
                      {it.attempts} answered · {Math.round((it.accuracy ?? 0) * 100)}% correct
                    </div>
                  ) : null}
                </button>
              </li>
            )
          })}
          {!loading && !items.length && (
            <li className="py-4 text-sm text-secondary">Queue is empty.</li>
          )}
        </ul>

        {selectedIds.length > 0 && (
          <div className="mt-3 border-t border-hairline pt-3">
            <p className="text-xs font-semibold text-ink">{selectedIds.length} rows selected</p>
            <button
              type="button"
              onClick={() => void bulkApplyContext()}
              className="mt-2 min-h-10 w-full rounded-lg border border-ink bg-paper px-3 text-xs font-bold text-ink"
            >
              Bulk apply context (20/batch)
            </button>
            {bulkStatus && <p className="mt-1 text-xs text-secondary">{bulkStatus}</p>}
          </div>
        )}
      </aside>

      {/* Right Editor */}
      <section className="min-w-0 rounded-xl border border-hairline bg-card p-5">
        {!current ? (
          <p className="text-sm text-secondary">Select a question from the queue to start authoring.</p>
        ) : (
          <div className="space-y-5">
            <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-hairline pb-3">
              <div>
                <p className="font-mono text-xs text-muted">
                  {current.paper_id} · Q{current.qnum || '?'} · {current.id}
                </p>
              </div>
              <span className="font-mono text-xs text-muted">
                {index + 1} / {items.length}
              </span>
            </header>

            {current.shape && (
              <div className="rounded-lg border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark">
                <strong>Conflict ({current.shape}):</strong> Official key: {current.official_answer || '—'} · Reviewed
                solution: {current.solution_answer || '—'}
              </div>
            )}

            {rowErrors[current.id] && (
              <p role="alert" className="rounded-lg border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark">
                {rowErrors[current.id]}
              </p>
            )}

            {/* Source text, options and printed locator (§VIII.5.1) */}
            <div className="space-y-3 rounded-lg border border-hairline bg-paper p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label htmlFor="ac-question" className="text-xs font-bold uppercase tracking-[0.06em] text-muted">
                  Question text
                </label>
                <span className="font-mono text-xs text-muted">
                  {current.answer_source ? 'answer: ' + current.answer_source : 'no recorded answer'}
                </span>
              </div>
              <textarea
                id="ac-question"
                rows={3}
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                className="w-full rounded-lg border border-hairline2 bg-card p-3 text-sm text-ink"
              />

              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-[0.06em] text-muted">Options</span>
                {optionDrafts.map((opt, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="ac-answer"
                      aria-label={`Correct answer is option ${i + 1}`}
                      checked={answerIndex === i}
                      disabled={current.answer_index == null}
                      onChange={() => setAnswerIndex(i)}
                    />
                    <input
                      value={opt ?? ''}
                      aria-label={`Option ${i + 1}`}
                      onChange={(e) =>
                        setOptionDrafts((prev) => prev.map((o, j) => (j === i ? e.target.value : o)))
                      }
                      className="min-h-10 min-w-0 flex-1 rounded-lg border border-hairline2 bg-card px-3 text-sm text-ink"
                    />
                  </div>
                ))}
                {!optionDrafts.length && (
                  <p className="text-xs text-secondary">No printed options — written question.</p>
                )}
                {current.answer_index == null && optionDrafts.length > 0 && (
                  <p className="text-xs text-secondary">
                    No recorded answer. Setting one is an answer decision, not a transcription fix.
                  </p>
                )}
              </div>

              {answerTextMoves && (
                <p role="alert" className="rounded-lg border border-exams bg-exams-soft p-3 text-xs text-exams-dark">
                  This moves the recorded answer from “{current.options?.[current.answer_index ?? 0] ?? '—'}” to “
                  {(answerIndex == null ? null : optionDrafts[answerIndex]) ?? '—'}”. A worked explanation of at
                  least 20 characters is required before this can be saved.
                </p>
              )}

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-xs text-muted">
                  Printed question number
                  <input
                    value={qnum}
                    onChange={(e) => setQnum(e.target.value)}
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-3 text-sm text-ink"
                  />
                </label>
                <label className="text-xs text-muted">
                  Source page
                  <input
                    inputMode="numeric"
                    value={page}
                    onChange={(e) => setPage(e.target.value)}
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-3 text-sm text-ink"
                  />
                </label>
              </div>
            </div>

            {/* Search-as-you-type taxonomy picker */}
            <div className="space-y-3 rounded-lg border border-hairline bg-paper p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className="text-xs font-bold uppercase tracking-[0.06em] text-muted">
                  Taxonomy (type to search or press . to repeat last)
                </label>
                {lastTagRef.current && (
                  <button
                    type="button"
                    onClick={() => {
                      if (!lastTagRef.current) return
                      setSubjectId(lastTagRef.current.subjectId)
                      setTopicId(lastTagRef.current.topicId)
                      setSubtopicId(lastTagRef.current.subtopicId)
                    }}
                    className="text-xs font-semibold text-link underline"
                  >
                    Repeat last tag (.)
                  </button>
                )}
              </div>

              <input
                type="search"
                value={taxFilter}
                onChange={(e) => setTaxFilter(e.target.value)}
                placeholder="Type 3 letters to jump to any subject/topic/subtopic…"
                className="min-h-10 w-full rounded-lg border border-hairline2 bg-card px-3 text-sm"
              />
              {quickMatches.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {quickMatches.map((node) => (
                    <button
                      key={node.id}
                      type="button"
                      onClick={() => applyTaxonomyNode(node)}
                      className="rounded-md border border-ink bg-card px-2.5 py-1 text-xs font-semibold text-ink hover:bg-canvas"
                    >
                      {node.label} ({node.level})
                    </button>
                  ))}
                </div>
              )}

              <div className="grid gap-3 sm:grid-cols-3">
                <label className="text-xs text-muted">
                  Subject
                  <select
                    value={subjectId}
                    onChange={(e) => {
                      setSubjectId(e.target.value)
                      setTopicId('')
                      setSubtopicId('')
                    }}
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                  >
                    <option value="">Unclassified</option>
                    {subjects.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-muted">
                  Topic
                  <select
                    value={topicId}
                    onChange={(e) => {
                      setTopicId(e.target.value)
                      setSubtopicId('')
                    }}
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                  >
                    <option value="">None</option>
                    {topics.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-muted">
                  Subtopic
                  <select
                    value={subtopicId}
                    onChange={(e) => setSubtopicId(e.target.value)}
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                  >
                    <option value="">None</option>
                    {subtopics.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            {/* Currency / Context selects (§VII.7 & §VII.11.2) */}
            <div className="grid gap-3 rounded-lg border border-hairline bg-paper p-4 sm:grid-cols-3">
              <label className="text-xs text-muted">
                Paper period
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value as typeof period)}
                  className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                >
                  <option value="unknown">unknown</option>
                  <option value="current">current</option>
                  <option value="legacy">legacy</option>
                </select>
              </label>
              <label className="text-xs text-muted">
                Time behavior
                <select
                  value={timeBehavior}
                  onChange={(e) => setTimeBehavior(e.target.value as typeof timeBehavior)}
                  className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                >
                  <option value="unknown">unknown</option>
                  <option value="static">static</option>
                  <option value="dated-event">dated-event</option>
                  <option value="changes-over-time">changes-over-time</option>
                </select>
              </label>
              <label className="text-xs text-muted">
                Scheme status
                <select
                  value={schemeStatus}
                  onChange={(e) => setSchemeStatus(e.target.value as typeof schemeStatus)}
                  className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-2 text-sm text-ink"
                >
                  <option value="unknown">unknown</option>
                  <option value="current">current</option>
                  <option value="superseded">superseded</option>
                </select>
              </label>
              {schemeStatus === 'superseded' && (
                <label className="text-xs text-muted sm:col-span-3">
                  Superseded note (≥20 chars)
                  <input
                    value={supersededNote}
                    onChange={(e) => setSupersededNote(e.target.value)}
                    placeholder="Explain which scheme replaced this…"
                    className="mt-1 min-h-10 w-full rounded-lg border border-hairline2 bg-card px-3 text-sm text-ink"
                  />
                </label>
              )}
            </div>

            {/* Explanation + Voice lint warnings (§VII.8) */}
            <div>
              <div className="flex items-center justify-between gap-2">
                <label className="text-xs font-bold uppercase tracking-[0.06em] text-muted">Explanation</label>
                <button
                  type="button"
                  onClick={() => void runVoiceCheck()}
                  className="text-xs font-semibold text-link underline"
                >
                  Check voice
                </button>
              </div>
              <textarea
                rows={4}
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                onBlur={() => void runVoiceCheck()}
                className="mt-1 w-full rounded-lg border border-hairline2 bg-paper p-3 text-sm text-ink"
              />
              {voiceWarnings.length > 0 && (
                <ul className="mt-2 space-y-1 rounded-lg border border-exams bg-exams-soft p-3 text-xs text-exams-dark">
                  {voiceWarnings.map((w, i) => (
                    <li key={i}>
                      <strong>{w.code}</strong> (“{w.match}”): {w.guidance}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="space-y-3 border-t border-hairline pt-4">
              {dirtyKinds.length > 1 && (
                <div className="rounded-lg border border-exams bg-exams-soft p-3 text-xs text-exams-dark">
                  <p className="font-semibold">
                    One correction publishes at a time, so only the change you pick is saved now.
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {dirtyKinds.map((k) => (
                      <button
                        key={k}
                        type="button"
                        aria-pressed={activeKind === k}
                        onClick={() => setChosenKind(k)}
                        className={
                          'min-h-9 rounded-lg border px-2.5 text-xs font-semibold ' +
                          (activeKind === k
                            ? 'border-ink bg-ink text-paper'
                            : 'border-hairline bg-paper text-ink')
                        }
                      >
                        {EDIT_KIND_LABELS[k]}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {draftIds.length > 0 && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-ink bg-canvas p-3">
                  <p className="text-sm font-semibold text-ink">
                    {draftIds.length} explanation{draftIds.length === 1 ? '' : 's'} queued
                    <span className="ml-2 font-normal text-secondary">
                      — publishing together is one bank write instead of {draftIds.length}
                    </span>
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => { setExplanationDrafts({}); setBulkStatus('') }}
                      className="min-h-10 rounded-lg border border-hairline bg-paper px-3 text-sm font-semibold text-ink"
                    >
                      Discard queue
                    </button>
                    <button
                      type="button"
                      onClick={() => void publishExplanationBatch()}
                      className="min-h-10 rounded-lg bg-ink px-4 text-sm font-bold text-paper"
                    >
                      Publish {draftIds.length} as one batch
                    </button>
                  </div>
                </div>
              )}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <input
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note…"
                  className="min-h-11 min-w-0 flex-1 rounded-lg border border-hairline2 bg-paper px-3 text-sm"
                />
                {explanation.trim().length >= 20 && explanation.trim() !== (current.explanation || '').trim() && (
                  <button
                    type="button"
                    onClick={() => addToBatch()}
                    className="min-h-11 rounded-lg border border-ink bg-paper px-4 py-2 text-sm font-semibold text-ink"
                  >
                    {current.id in explanationDrafts ? 'Update in batch' : 'Add to batch'} (⌘⇧↵)
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => void saveAndNext()}
                  className="min-h-11 rounded-lg bg-ink px-5 py-2 text-sm font-bold text-paper"
                >
                  {activeKind
                    ? `Save ${EDIT_KIND_LABELS[activeKind]}${contextChanged ? ' + currency' : ''} & next (⌘↵)`
                    : contextChanged
                      ? 'Save currency & next (⌘↵)'
                      : 'Skip to next (⌘↵)'}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
