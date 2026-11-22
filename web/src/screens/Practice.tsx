import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import QuestionCard from '../components/QuestionCard'
import { AnswerLayoutControl } from '../components/AnswerLayout'
import {
  currentMock,
  isLaterExamCollection,
  listCollections,
  listQuestions,
  listTaxonomy,
  type Collection,
  type MockSession,
  type Question,
  type TaxonomyFacet,
} from '../lib/api'
import { usePreferredExam } from '../lib/preferredExam'
import { useSelectionTray } from '../lib/selectionTray'
import { mockResumePath } from '../lib/sharedTests'

type CountChoice = '10' | '25' | '50' | 'full'
type PracticeMode = 'mcq' | 'written'

/** Unified `/practice` screen (§VII.4).
 *  Three controls and a button:
 *  - What (Exam, Subject, Search, or Written answers mode)
 *  - How many (10 / 25 / 50 / full paper)
 *  - Timer (Off: untimed immediate reveal; On: timed run scored at the end)
 *
 *  Free allowance: 1 timed run/month + 50 untimed answers/day. */
export default function Practice() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const tray = useSelectionTray()

  const [exams, setExams] = useState<Collection[]>([])
  const [taxonomy, setTaxonomy] = useState<TaxonomyFacet[]>([])
  const [activeMock, setActiveMock] = useState<MockSession | null>(null)
  const [catalogError, setCatalogError] = useState('')

  const preferredExam = usePreferredExam(exams)
  const [examId, setExamId] = useState(params.get('exam') || '')
  const [subjectId, setSubjectId] = useState(params.get('subject') || '')
  const [query, setQuery] = useState(params.get('q') || '')
  const [count, setCount] = useState<CountChoice>(
    (['10', '25', '50', 'full'].includes(params.get('count') || '')
      ? (params.get('count') as CountChoice)
      : '25'),
  )
  const [timed, setTimed] = useState(params.get('timer') === 'on')
  const [durationMinutes, setDurationMinutes] = useState(() => {
    const raw = Number(params.get('minutes') || 20)
    return Number.isFinite(raw) && raw >= 5 && raw <= 240 ? raw : 20
  })
  const [mode, setMode] = useState<PracticeMode>(params.get('mode') === 'written' ? 'written' : 'mcq')

  // Active untimed run state
  const [running, setRunning] = useState(params.get('autostart') === '1')
  const [items, setItems] = useState<Question[]>([])
  const [totalAvailable, setTotalAvailable] = useState<number | null>(null)
  const [loadingRun, setLoadingRun] = useState(false)
  const [runError, setRunError] = useState('')
  const [answeredCount, setAnsweredCount] = useState(0)

  useEffect(() => {
    let live = true
    Promise.all([
      listCollections().then((rows) => {
        if (!live) return
        setExams(rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)))
      }),
      listTaxonomy('all', true).then((rows) => {
        if (live) setTaxonomy(rows)
      }),
      currentMock()
        .then((m) => {
          if (live) setActiveMock(m)
        })
        .catch(() => {}),
    ]).catch((e) => {
      if (live) setCatalogError(e instanceof Error ? e.message : 'Could not load exams and subjects.')
    })
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    if (!examId && preferredExam) setExamId(preferredExam.id)
  }, [examId, preferredExam])

  const subjects = useMemo(() => {
    const map = new Map<string, string>()
    for (const f of taxonomy) {
      if (!map.has(f.subject_id)) map.set(f.subject_id, f.subject)
    }
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1]))
  }, [taxonomy])

  async function launchUntimedRun(targetExam = examId, targetSubject = subjectId, targetMode = mode) {
    setLoadingRun(true)
    setRunError('')
    setAnsweredCount(0)
    try {
      const limit = count === 'full' ? 100 : Number(count)
      const res = await listQuestions({
        pool: targetMode === 'written' ? 'all' : 'practice',
        collection_id: targetExam || undefined,
        subject_id: targetSubject || undefined,
        q: query.trim().length >= 2 ? query.trim() : undefined,
        order: targetMode === 'written' ? 'paper' : 'mixed',
        limit: targetMode === 'written' ? 100 : limit,
        offset: 0,
      })
      const filtered =
        targetMode === 'written'
          ? res.items.filter((q) => q.type === 'descriptive').slice(0, limit)
          : res.items.filter((q) => q.type === 'mcq')
      setItems(filtered)
      setTotalAvailable(targetMode === 'written' ? filtered.length : res.total)
      setRunning(true)
    } catch (e) {
      setRunError(e instanceof Error ? e.message : 'Could not load questions for practice.')
    } finally {
      setLoadingRun(false)
    }
  }

  useEffect(() => {
    if (params.get('autostart') === '1') {
      void launchUntimedRun(
        params.get('exam') || '',
        params.get('subject') || '',
        params.get('mode') === 'written' ? 'written' : 'mcq',
      )
    }
    // Run once on initial autostart navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleStart(e: React.FormEvent) {
    e.preventDefault()
    if (timed && mode === 'mcq') {
      const target = examId || exams[0]?.id || 'udc'
      const qs = new URLSearchParams()
      if (count === 'full') qs.set('simulation', 'full')
      qs.set('mode', 'derived')
      qs.set('minutes', String(durationMinutes))
      navigate(`/exams/${encodeURIComponent(target)}/mock` + (qs.toString() ? '?' + qs.toString() : ''))
      return
    }
    const next = new URLSearchParams()
    if (examId) next.set('exam', examId)
    if (subjectId) next.set('subject', subjectId)
    if (query.trim()) next.set('q', query.trim())
    next.set('count', count)
    if (mode === 'written') next.set('mode', 'written')
    setParams(next, { replace: true })
    void launchUntimedRun()
  }

  return (
    <div className="mx-auto max-w-[850px] px-4 pb-24 pt-8 sm:px-6" data-screen="practice">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-hairline pb-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">Practice &amp; Mock</p>
          <h1 className="mt-1 text-2xl font-bold text-ink">Practice</h1>
          <p className="mt-1 text-base text-secondary">
            Pick what, pick how many, and decide whether you want a timer.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/practice/build"
            className="inline-flex min-h-11 items-center rounded-lg border border-hairline bg-card px-4 py-2 text-sm font-semibold text-ink hover:border-ink"
          >
            Build a custom test
          </Link>
          <Link
            to="/tests"
            className="inline-flex min-h-11 items-center rounded-lg border border-hairline bg-card px-4 py-2 text-sm font-semibold text-link hover:border-ink"
          >
            Shared tests
          </Link>
        </div>
      </header>

      {activeMock && (
        <section className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-ink bg-card p-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">Timed paper in progress</p>
            <p className="mt-1 text-base font-semibold text-ink">
              {activeMock.questions.length} questions · {Math.max(0, Math.ceil(activeMock.seconds_remaining / 60))} min remaining
            </p>
          </div>
          <Link
            to={mockResumePath(activeMock)}
            className="inline-flex min-h-11 items-center rounded-lg bg-ink px-4 py-2 text-sm font-bold text-paper"
          >
            Resume timed run →
          </Link>
        </section>
      )}

      {catalogError && (
        <p role="alert" className="mt-4 rounded-lg border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark">
          {catalogError}
        </p>
      )}

      <form onSubmit={handleStart} className="mt-6 space-y-6 rounded-xl border border-hairline bg-card p-5 sm:p-6">
        {/* Mode tabs: MCQs vs Written answers (§VII.9.2) */}
        <div className="flex flex-wrap gap-2 border-b border-hairline pb-4" role="group" aria-label="Question format">
          <button
            type="button"
            aria-pressed={mode === 'mcq'}
            onClick={() => setMode('mcq')}
            className={
              'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
              (mode === 'mcq' ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
            }
          >
            MCQs
          </button>
          <button
            type="button"
            aria-pressed={mode === 'written'}
            onClick={() => {
              setMode('written')
              setTimed(false)
            }}
            className={
              'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
              (mode === 'written' ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
            }
          >
            Written answers
          </button>
        </div>

        {/* Control 1: What */}
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">1. What</p>
          <div className="mt-2 grid gap-3 sm:grid-cols-3">
            <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
              Exam
              <select
                aria-label="Exam"
                value={examId}
                onChange={(e) => setExamId(e.target.value)}
                className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
              >
                <option value="">All exams</option>
                {exams.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
              Subject
              <select
                aria-label="Subject"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
              >
                <option value="">All subjects</option>
                {subjects.map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
              Search
              <input
                type="search"
                aria-label="Search topic or text"
                placeholder="Optional keyword…"
                value={query}
                maxLength={120}
                onChange={(e) => setQuery(e.target.value)}
                className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
              />
            </label>
          </div>
        </div>

        {/* Control 2: How many */}
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">2. How many</p>
          <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Question count">
            {(
              [
                ['10', '10'],
                ['25', '25'],
                ['50', '50'],
                ['full', 'Full paper'],
              ] as const
            ).map(([val, label]) => (
              <button
                key={val}
                type="button"
                aria-pressed={count === val}
                onClick={() => setCount(val)}
                className={
                  'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
                  (count === val ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
                }
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Control 3: Timer */}
        {mode === 'mcq' && (
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">3. Timer</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <label className="flex min-h-11 cursor-pointer items-start gap-3 rounded-lg border border-hairline bg-paper p-3 text-sm">
                <input
                  type="radio"
                  name="practice-timer"
                  checked={!timed}
                  onChange={() => setTimed(false)}
                  className="mt-1"
                />
                <span>
                  <strong className="block text-ink">Off — check each answer as I go</strong>
                  <span className="text-xs text-secondary">Untimed, immediate reveal, 50 free answers/day.</span>
                </span>
              </label>

              <label className="flex min-h-11 cursor-pointer items-start gap-3 rounded-lg border border-hairline bg-paper p-3 text-sm">
                <input
                  type="radio"
                  name="practice-timer"
                  checked={timed}
                  onChange={() => setTimed(true)}
                  className="mt-1"
                />
                <span className="flex-1">
                  <strong className="block text-ink">On — score at the end</strong>
                  <span className="text-xs text-secondary">Server-timed snapshot, 1 free timed run/month.</span>
                  {timed && (
                    <span className="mt-2 flex items-center gap-2 text-xs text-ink">
                      Minutes:
                      <input
                        type="number"
                        min={5}
                        max={240}
                        value={durationMinutes}
                        onChange={(e) => setDurationMinutes(Number(e.target.value) || 20)}
                        className="w-20 rounded border border-hairline2 bg-card px-2 py-1 font-mono text-sm"
                      />
                    </span>
                  )}
                </span>
              </label>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4">
          <p className="text-xs text-secondary">
            Free tier: 1 timed run a month · 50 untimed answers a day · browse always free.
          </p>
          <button
            type="submit"
            disabled={loadingRun}
            className="min-h-11 rounded-lg bg-ink px-6 py-2.5 text-sm font-bold text-paper disabled:opacity-50"
          >
            {loadingRun ? 'Loading…' : timed && mode === 'mcq' ? 'Start timed run →' : mode === 'written' ? 'Browse written prompts →' : 'Start practice →'}
          </button>
        </div>
      </form>

      {runError && (
        <div role="alert" className="mt-5 rounded-xl border border-wrong bg-wrong-soft p-4 text-sm text-wrong-dark">
          {runError}
        </div>
      )}

      {running && !loadingRun && (
        <section className="mt-8" aria-label="Practice questions">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-3">
            <div>
              <h2 className="text-lg font-bold text-ink">
                {mode === 'written' ? 'Written prompts' : 'Untimed practice'}
              </h2>
              <p className="text-sm text-secondary">
                {items.length} shown
                {totalAvailable !== null ? ` · ${totalAvailable.toLocaleString('en-IN')} matching` : ''}
                {mode === 'mcq' ? ` · ${answeredCount} checked` : ''}
              </p>
            </div>
            {mode === 'mcq' && <AnswerLayoutControl />}
          </div>

          {!items.length ? (
            <div className="rounded-xl border border-hairline bg-card p-6 text-center">
              <h3 className="text-lg font-bold text-ink">No matching questions</h3>
              <p className="mt-2 text-sm text-secondary">
                Try clearing a subject or keyword filter, or uncheck the scored-only filter.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((q) => (
                <div key={q.id} className="finna-bank-row">
                  <button
                    type="button"
                    className="finna-bank-check"
                    aria-pressed={tray.has(q.id)}
                    aria-label={tray.has(q.id) ? 'Remove from test tray' : 'Add to test tray'}
                    onClick={() => tray.toggle(q.id)}
                  >
                    {tray.has(q.id) ? '✓' : ''}
                  </button>
                  <QuestionCard
                    q={q}
                    onAnswered={() => setAnsweredCount((n) => n + 1)}
                  />
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
