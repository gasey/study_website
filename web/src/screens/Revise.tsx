import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { getReviewQueue, startSmartReview, type ReviewQueue } from '../lib/api'
import UdcStudySessions from '../components/UdcStudySessions'

const Mistakes = lazy(() => import('./Mistakes'))
const Vocabulary = lazy(() => import('./Vocabulary'))
const SavedSession = lazy(() => import('./DailyRevision'))

export default function Revise() {
  const [params, setParams] = useSearchParams()
  const nav = useNavigate()
  const [queue, setQueue] = useState<ReviewQueue | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [busy, setBusy] = useState(false)
  const [focused, setFocused] = useState(false)

  const request = useRef<{ signature: string; key: string } | null>(null)
  const generation = useRef(0)
  const starting = useRef(false)

  const tab = ['review', 'queue', 'vocabulary', 'legacy'].includes(params.get('tab') || '')
    ? params.get('tab')!
    : 'review'
  const vocabulary = tab === 'vocabulary'
  const legacy = tab === 'legacy' && /^rev_[a-f0-9]+$/.test(params.get('session') || '')
  const wordDeck = params.get('word_deck') || undefined
  const itemType = params.get('item_type') === 'vocab' ? 'vocab' : 'all'
  const sid = !vocabulary && !legacy ? params.get('session') : null
  const through = params.get('through') || undefined

  async function more() {
    if (!queue || starting.current) return
    starting.current = true
    setBusy(true)
    const run = generation.current
    try {
      const page = await getReviewQueue(queue.items.length, wordDeck)
      if (run === generation.current) {
        setQueue((old) =>
          old
            ? {
                ...page,
                items: [
                  ...old.items,
                  ...page.items.filter(
                    (q) => !old.items.some((previous) => previous.item_id === q.item_id),
                  ),
                ],
              }
            : page,
        )
      }
    } catch (e) {
      if (run === generation.current) setError((e as Error).message)
    } finally {
      starting.current = false
      setBusy(false)
    }
  }

  useEffect(() => {
    let live = true
    generation.current++
    setQueue(null)
    setError('')
    if (!sid && !vocabulary && !legacy) {
      getReviewQueue(0, wordDeck)
        .then((q) => {
          if (live) setQueue(q)
        })
        .catch((e) => {
          if (live) setError(e.message)
        })
    }
    const refresh = () => {
      generation.current++
      setQueue(null)
      request.current = null
      setRetry((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', refresh)
    return () => {
      live = false
      generation.current++
      window.removeEventListener('ism-auth-change', refresh)
    }
  }, [sid, vocabulary, legacy, retry, wordDeck])

  async function start() {
    if (starting.current) return
    starting.current = true
    setBusy(true)
    setError('')
    const run = generation.current
    const signature = JSON.stringify({ focused, through, itemType, wordDeck })
    if (request.current?.signature !== signature) {
      request.current = { signature, key: crypto.randomUUID() }
    }
    try {
      const s = await startSmartReview(request.current.key, focused, through, itemType, wordDeck)
      if (run === generation.current) {
        nav('/revise?' + new URLSearchParams({ session: s.id, exam_scope: 'all' }))
      }
    } catch (e) {
      if (run === generation.current) setError((e as Error).message)
    } finally {
      starting.current = false
      setBusy(false)
    }
  }

  const dueCount = queue
    ? itemType === 'vocab'
      ? queue.vocabulary_due_count || 0
      : queue.due_count
    : null
  const scheduledCount = queue
    ? itemType === 'vocab'
      ? queue.vocabulary_scheduled_count || 0
      : queue.scheduled_count
    : null
  const startDisabled =
    !queue ||
    busy ||
    (queue.curated_writes_enabled === false &&
      (through ? queue.scheduled_count : queue.due_count) -
        (through ? queue.curated_scheduled_count || 0 : queue.curated_due_count || 0) <=
        0) ||
    !(itemType === 'vocab'
      ? through
        ? queue.vocabulary_scheduled_count
        : queue.vocabulary_due_count
      : through
        ? queue.scheduled_count
        : queue.due_count)

  return (
    <div data-screen="revise" className="finna-page rv-shell">
      {!sid && (
        <header className="av-hero rv-hero print:hidden">
          <div className="av-hero-copy">
            <span className="cr-eyebrow">Spaced repetition · Revisit &amp; remember</span>
            <h1>Revise</h1>
            <p>
              Clear your scheduled spaced-review queue, re-test past mistakes, and build lasting
              recall across every exam and subject.
            </p>
          </div>
          <div className="av-hero-actions">
            <Link to="/practice" className="cr-glass-btn">
              New practice →
            </Link>
            <Link to="/bank?study_status=ever_wrong" className="cr-glass-btn">
              Missed questions
            </Link>
          </div>
        </header>
      )}

      {!sid && (
        <nav
          aria-label="Revision views"
          className="mt-5 flex flex-wrap items-center justify-between gap-3 print:hidden"
        >
          <div className="finna-segments" role="tablist">
            {(
              [
                ['review', 'Smart Review'],
                ['queue', 'Queue & mistakes'],
                ['vocabulary', 'Vocabulary'],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                aria-pressed={tab === value}
                aria-selected={tab === value}
                onClick={() =>
                  setParams((old) => {
                    const p = new URLSearchParams(old)
                    for (const key of ['session', 'review', 'question_id', 'return_to']) {
                      p.delete(key)
                    }
                    p.set('tab', value)
                    return p
                  })
                }
              >
                {label}
              </button>
            ))}
          </div>
        </nav>
      )}

      <Suspense fallback={<p role="status" className="mt-6 text-secondary">Loading revision…</p>}>
        {sid ? (
          <>
            <Link
              className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-link hover:underline"
              to="/revise"
            >
              ← Your full queue
            </Link>
            <UdcStudySessions papers={[]} review />
          </>
        ) : vocabulary ? (
          <div className="mt-5">
            <Vocabulary embedded />
          </div>
        ) : legacy ? (
          <SavedSession />
        ) : (
          <>
            {error && (
              <div
                role="alert"
                className="finna-card mt-5 border-wrong bg-wrong-soft text-wrong-dark"
              >
                <p className="text-sm font-semibold">{error}</p>
                <div className="mt-3 flex flex-wrap gap-3">
                  <button
                    type="button"
                    className="finna-btn finna-btn-quiet"
                    onClick={() => setRetry((n) => n + 1)}
                  >
                    Try again
                  </button>
                  <Link className="finna-btn" to="/login?next=%2Frevise">
                    Sign in to your account
                  </Link>
                </div>
              </div>
            )}

            {!queue && !error && (
              <div role="status" className="finna-card mt-5 text-sm text-secondary">
                Loading your review queue…
              </div>
            )}

            {queue && (
              <section className="finna-card rv-main-card mt-5 print:hidden">
                <div className="rv-stats-row">
                  <div className="rv-stat-box is-primary">
                    <strong>{(dueCount ?? 0).toLocaleString('en-IN')}</strong>
                    <span>{itemType === 'vocab' ? 'Vocab due now' : 'Reviews due now'}</span>
                  </div>
                  <div className="rv-stat-box">
                    <strong>{(scheduledCount ?? 0).toLocaleString('en-IN')}</strong>
                    <span>Total scheduled</span>
                  </div>
                  <div className="rv-stat-box">
                    <strong>20</strong>
                    <span>Questions per session</span>
                  </div>
                </div>

                <h2 className="mt-5 font-reading text-2xl font-semibold text-ink">
                  {dueCount}{' '}
                  {itemType === 'vocab' ? 'vocabulary ' : ''}
                  {dueCount === 1 ? 'review due' : 'reviews due'}
                </h2>
                <p className="mt-1.5 max-w-[65ch] text-[15px] leading-relaxed text-secondary">
                  {queue.scheduled_count
                    ? `${queue.scheduled_count.toLocaleString('en-IN')} items are scheduled across your study history. Each session serves up to 20 questions, oldest due first.`
                    : 'Your review queue is clear. Questions you miss and vocabulary you start learning enter this queue automatically.'}
                </p>

                {itemType === 'vocab' && (
                  <p className="mt-3 text-sm text-secondary">
                    This saved session includes due vocabulary questions and reviewed word cards.{' '}
                    <Link className="font-bold text-link underline" to="/revise">
                      Include every due question
                    </Link>
                  </p>
                )}
                {wordDeck && (
                  <p className="mt-3 text-sm text-secondary">
                    This set uses the selected reviewed word deck.{' '}
                    <Link
                      to="/revise?item_type=vocab"
                      className="font-bold text-link underline"
                    >
                      Include all vocabulary
                    </Link>
                  </p>
                )}
                {queue.curated_writes_enabled === false && !!queue.curated_due_count && (
                  <p role="status" className="mt-3 text-sm text-secondary">
                    Word-card practice is paused. Available bank questions can still be reviewed.
                  </p>
                )}
                {through && (
                  <p className="mt-3 text-sm text-secondary">
                    Early review through {through}. Your next interval starts from the day you
                    answer.
                  </p>
                )}

                <label className="mt-5 flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-hairline bg-paper px-4 py-2.5 text-sm font-semibold text-ink">
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-link"
                    checked={focused}
                    disabled={busy}
                    onChange={(e) => setFocused(e.target.checked)}
                  />
                  <span>
                    Focus subjects only for this session
                    <span className="block text-xs font-normal text-secondary">
                      The full due count above always includes every subject.
                    </span>
                  </span>
                </label>

                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    className="finna-btn min-h-12 px-7 text-[15px] disabled:opacity-45"
                    disabled={startDisabled}
                    onClick={() => void start()}
                  >
                    {busy
                      ? 'Preparing your saved review…'
                      : through
                        ? 'Start early review →'
                        : 'Start Smart Review →'}
                  </button>
                  {dueCount === 0 && (
                    <Link to="/practice" className="finna-btn finna-btn-quiet">
                      Practise new questions →
                    </Link>
                  )}
                </div>
              </section>
            )}

            {tab === 'queue' && (
              <div data-revision-sheet className="mt-5 space-y-5">
                {queue && (
                  <section className="finna-card">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <span className="finna-eyebrow">Due-date order</span>
                        <h2 className="mt-0.5 font-reading text-2xl font-semibold">
                          Scheduled questions
                        </h2>
                      </div>
                      <button
                        type="button"
                        className="finna-btn finna-btn-quiet print:hidden"
                        onClick={() => window.print()}
                      >
                        Print revision sheet
                      </button>
                    </div>
                    <p className="mt-2 text-sm text-secondary">
                      Showing the first {queue.items.length} scheduled questions in due-date order.
                      Print includes the questions currently loaded below.
                    </p>
                    <div className="mt-4 divide-y divide-hairline">
                      {queue.items.map((q) => (
                        <article key={q.item_id} className="py-4">
                          <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-secondary">
                            <span className="rounded-pill bg-practice-soft px-2.5 py-0.5 font-bold text-practice-dark">
                              {q.item_type === 'vocab' ? 'Vocabulary · ' : ''}
                              {q.subject_label}
                            </span>
                            <span>Box {q.box}</span>
                            <span>· Due {q.due_on}</span>
                            {q.focused && (
                              <span className="rounded-pill bg-exams-soft px-2 py-0.5 font-bold text-exams-dark">
                                Focus
                              </span>
                            )}
                          </div>
                          <Link
                            to={
                              q.curated
                                ? '/revise?' +
                                  new URLSearchParams({
                                    tab: 'vocabulary',
                                    curated_deck: q.deck_id || '',
                                    word_card: q.item_id,
                                    exam_scope: 'all',
                                  })
                                : '/bank/' + encodeURIComponent(q.item_id) + '?exam_scope=all'
                            }
                            className="mt-2 block break-words font-reading text-[18px] font-medium leading-snug text-ink hover:text-link hover:underline"
                          >
                            {q.question}
                          </Link>
                        </article>
                      ))}
                    </div>
                    {queue.has_more && (
                      <button
                        type="button"
                        className="finna-btn finna-btn-quiet mt-4 print:hidden"
                        disabled={busy}
                        onClick={() => void more()}
                      >
                        {busy ? 'Loading…' : 'Load more scheduled questions'}
                      </button>
                    )}
                  </section>
                )}
                <Mistakes />
              </div>
            )}
          </>
        )}
      </Suspense>
    </div>
  )
}
