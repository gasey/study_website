import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import MockResultView, { mmss } from '../components/MockResultView'
import {
  currentMock,
  getCollection,
  isLaterExamCollection,
  startMock,
  submitMock,
  type MockResult,
  type MockSession,
} from '../lib/api'

/** The timed paper — the prototype's `exam` screen, line 579.
 *  Named MockRunner because `exam` is ambiguous here; see
 *  docs/DESIGN-FIDELITY.md.
 *
 *  The countdown below is DISPLAY ONLY. The server recorded started_at and
 *  recomputes elapsed time on submit, so stopping this timer in a debugger
 *  buys nothing. */

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

export default function MockRunner() {
  const { id: collectionId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const sectionPath = searchParams.get('section') || undefined
  const [mock, setMock] = useState<MockSession | null>(null)
  const [paperTitle, setPaperTitle] = useState('Preparing your paper')
  const [result, setResult] = useState<MockResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [at, setAt] = useState(0)
  const [picks, setPicks] = useState<Record<string, number>>({})
  const [marked, setMarked] = useState<Record<string, boolean>>({})
  const [left, setLeft] = useState(0)
  const [busy, setBusy] = useState(false)
  const submitted = useRef(false)

  // Resume an open mock if there is one, else start a fresh 20-question /
  // 20-minute paper. Resuming matters: the server allows only one open mock
  // per device, so a reload must rejoin rather than fail with a 409.
  useEffect(() => {
    let dead = false
    ;(async () => {
      try {
        const selectedCollection = await getCollection(collectionId)
        if (isLaterExamCollection(selectedCollection)) {
          throw new Error('LDE exam practice will be added as the exam library grows.')
        }
        const existing = await currentMock()
        const m = existing ?? (await startMock({
          collection_id: collectionId,
          section_path: sectionPath,
          count: 20,
          duration_minutes: 20,
        }))
        const collection = m.collection_id === collectionId ? selectedCollection : await getCollection(m.collection_id)
        const section = collection.section_list.find((s) => s.path === m.section_path)
        if (!dead) {
          setMock(m)
          setLeft(m.seconds_remaining)
          setPaperTitle(`${collection.title}${section ? ` · ${section.title}` : ''} · Mock`)
        }
      } catch (e) {
        if (!dead) setError((e as Error).message)
      }
    })()
    return () => {
      dead = true
    }
  }, [collectionId, sectionPath])

  const send = useCallback(async () => {
    if (!mock || submitted.current) return
    submitted.current = true
    setBusy(true)
    try {
      setResult(
        await submitMock(
          mock.id,
          Object.entries(picks).map(([question_id, chosen_index]) => ({ question_id, chosen_index })),
        ),
      )
    } catch (e) {
      setError((e as Error).message)
      submitted.current = false
    } finally {
      setBusy(false)
    }
  }, [mock, picks])

  // Tick for display, and auto-submit at zero so an abandoned tab still
  // produces a result rather than an orphaned open session.
  useEffect(() => {
    if (!mock || result) return
    const t = setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          clearInterval(t)
          void send()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [mock, result, send])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="rounded-[14px] border border-mypick bg-mypick-soft p-5 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to={`/exams/${collectionId}`} className="label mt-4 inline-block underline">
          ← Back to the exam
        </Link>
      </div>
    )
  }
  if (result)
    return <MockResultView result={result} backTo={`/exams/${collectionId}`} />
  if (!mock) return <div className="mx-auto max-w-shell px-6 py-12 label">Preparing your paper…</div>

  const q = mock.questions[at]
  const answered = Object.keys(picks).length
  const nMarked = Object.values(marked).filter(Boolean).length
  const low = left <= 60

  return (
    <>
      {/* Sticky dark bar, markup line 579. */}
      <div className="sticky top-0 z-40 bg-ink text-paper">
        <div className="mx-auto flex max-w-shell flex-wrap items-center gap-x-5 gap-y-2.5 px-6 py-2.5">
          <Link to={`/exams/${collectionId}`} className="text-[14px] font-medium text-[#D9D0BF]">
            ← Exit
          </Link>
          <div className="min-w-0 flex-[1_1_280px]">
            <div className="font-display text-[19px] font-medium">{paperTitle}</div>
            <div className="font-mono text-[11px] text-[#BDB3A0]">
              {mock.questions.length} questions · timed practice
            </div>
          </div>
          <div
            className={`font-mono text-[22px] font-medium tracking-[0.02em] ${low ? 'text-mypick-soft' : ''}`}
            aria-live="off"
          >
            {mmss(left)}
          </div>
          <button
            onClick={send}
            disabled={busy}
            className="rounded-pill bg-paper px-[18px] py-[9px] text-[14px] font-semibold text-ink disabled:opacity-50"
          >
            {busy ? 'Submitting…' : 'Submit paper'}
          </button>
        </div>
      </div>

      <main className="mx-auto flex max-w-shell flex-wrap items-start gap-10 px-6 pb-24 pt-8">
        <section className="min-w-0 flex-[999_1_560px]">
          <div className="flex justify-between gap-2.5 border-b border-ink pb-2.5 font-mono text-[12px] text-muted">
            <span>Question {at + 1} of {mock.questions.length}</span>
            <span>{marked[q.id] ? 'Marked for review' : ''}</span>
          </div>

          <div className="my-6 font-display text-[clamp(22px,2.6vw,28px)] leading-[1.35] [text-wrap:pretty]">
            {q.question}
          </div>

          <div className="flex flex-col gap-2.5">
            {q.options.map((text, i) => {
              const on = picks[q.id] === i
              return (
                <button
                  key={i}
                  onClick={() => setPicks((p) => ({ ...p, [q.id]: i }))}
                  aria-pressed={on}
                  className={`flex items-center gap-3.5 rounded-[6px] border p-4 text-left text-[16px] ${
                    on ? 'border-ink bg-[#EDE5D4]' : 'border-opt-border bg-opt-bg hover:border-ink'
                  }`}
                >
                  <span
                    className={`flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border border-ink font-mono text-[12px] ${
                      on ? 'bg-ink text-paper' : 'bg-transparent text-ink'
                    }`}
                  >
                    {LETTERS[i]}
                  </span>
                  <span>{text}</span>
                </button>
              )
            })}
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setAt((n) => Math.max(0, n - 1))}
              disabled={at === 0}
              className="rounded-pill border border-ink px-[18px] py-[11px] text-[14px] font-semibold disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setMarked((m) => ({ ...m, [q.id]: !m[q.id] }))}
              className="rounded-pill border border-prov px-[18px] py-[11px] text-[14px] font-semibold text-prov"
            >
              {marked[q.id] ? 'Unmark' : 'Mark for review'}
            </button>
            <button
              onClick={() =>
                setPicks((p) => {
                  const { [q.id]: _drop, ...rest } = p
                  return rest
                })
              }
              className="px-[18px] py-[11px] text-[14px] text-secondary"
            >
              Clear
            </button>
            <div className="flex-1" />
            <button
              onClick={() => setAt((n) => Math.min(mock.questions.length - 1, n + 1))}
              disabled={at === mock.questions.length - 1}
              className="rounded-pill bg-ink px-[22px] py-[11px] text-[14px] font-semibold text-paper disabled:opacity-40"
            >
              Save &amp; next
            </button>
          </div>
        </section>

        <aside className="min-w-0 max-w-[380px] flex-[1_1_300px]">
          <div className="flex justify-between border-b border-ink pb-2 font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
            <span>Paper</span>
            <span>{answered} answered · {nMarked} marked</span>
          </div>
          <div className="mt-3.5 grid grid-cols-6 gap-[5px] sm:grid-cols-10">
            {mock.questions.map((mq, i) => {
              const isAns = picks[mq.id] !== undefined
              const isMark = !!marked[mq.id]
              const cur = i === at
              const cls = isMark
                ? 'bg-[#DCE5EE] text-prov'
                : isAns
                  ? 'bg-ink text-paper'
                  : 'bg-transparent text-secondary'
              const border = cur
                ? 'border-mypick'
                : isMark
                  ? 'border-prov'
                  : isAns
                    ? 'border-ink'
                    : 'border-[#CFC5B2]'
              return (
                <button
                  key={mq.id}
                  onClick={() => setAt(i)}
                  className={`flex aspect-square items-center justify-center rounded-[4px] border font-mono text-[11px] ${cls} ${border}`}
                >
                  {i + 1}
                </button>
              )
            })}
          </div>
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-[12px] text-secondary">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] bg-ink" />Answered
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] bg-[#DCE5EE]" />Marked
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] border border-[#CFC5B2]" />Not seen
            </span>
          </div>
        </aside>
      </main>
    </>
  )
}
