import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ProvenanceTag, { RepeatBadge } from '../components/ProvenanceTag'
import {
  getQuestion,
  submitAnswer,
  type AnswerResult,
  type QuestionDetail as QD,
} from '../lib/api'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

export default function QuestionDetail() {
  const { id = '' } = useParams()
  const [q, setQ] = useState<QD | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [picked, setPicked] = useState<number | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setQ(null)
    setPicked(null)
    setResult(null)
    setError(null)
    getQuestion(id)
      .then(setQ)
      .catch((e) => setError(e.message))
  }, [id])

  async function reveal() {
    if (picked === null || result) return
    setSubmitting(true)
    try {
      // The client does not know the answer until this returns — the server
      // never sent it with the question.
      setResult(await submitAnswer(id, picked))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-card border border-wrong bg-wrong-soft p-5 text-wrong-dark">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">× Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to="/bank" className="label mt-4 inline-block underline">
          ← Back to the bank
        </Link>
      </div>
    )
  }

  if (!q) return <div className="mx-auto max-w-3xl px-6 py-10 label">Loading…</div>

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <Link to="/bank" className="label underline">
        ← Bank
      </Link>

      <div className="mt-4 rounded-card border border-hairline bg-card p-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="label text-practice-dark">
            {q.last_year ?? q.first_year ?? '—'}
          </span>
          <span className="text-hairline2">·</span>
          <span className="label">{q.type === 'mcq' ? 'MCQ' : 'Descriptive'}</span>
          <span className="grow" />
          <RepeatBadge times={q.times_asked} />
          <ProvenanceTag source={q.answer_source} />
        </div>

        <h1 className="font-display text-[24px] font-medium leading-snug">{q.question}</h1>

        {q.options.length > 0 && (
          <ol className="mt-5 grid gap-2">
            {q.options.map((o, i) => {
              const isPicked = picked === i
              const isAnswer = result?.answer_index === i
              const wrongPick = !!result && isPicked && !result.correct

              let cls = 'border-hairline bg-card hover:border-ink'
              if (result) {
                if (isAnswer) cls = 'border-correct bg-correct-soft'
                else if (wrongPick) cls = 'border-wrong bg-wrong-soft'
                else cls = 'border-hairline bg-card opacity-60'
              } else if (isPicked) {
                cls = 'border-ink bg-paper'
              }

              return (
                <li key={i}>
                  <button
                    disabled={!!result}
                    onClick={() => setPicked(i)}
                    aria-pressed={isPicked}
                    className={`flex w-full items-start gap-3 rounded-panel border p-3 text-left text-[15px] transition-colors ${cls}`}
                  >
                    <span className="label mt-[2px] shrink-0">{LETTERS[i]}</span>
                    <span className="grow">{o}</span>
                    {/* States always carry a symbol, never colour alone. */}
                    {result && isAnswer && <span className="text-correct-dark">✓</span>}
                    {wrongPick && <span className="text-wrong-dark">×</span>}
                  </button>
                </li>
              )
            })}
          </ol>
        )}

        {!result && q.options.length > 0 && (
          <button
            disabled={picked === null || submitting}
            onClick={reveal}
            className="mt-5 rounded-pill bg-ink px-5 py-2 text-[14px] text-paper disabled:opacity-40"
          >
            {submitting ? 'Checking…' : 'Check answer'}
          </button>
        )}

        {result && (
          <div
            className={`mt-5 rounded-panel p-4 ${
              result.correct ? 'bg-correct-soft' : 'bg-wrong-soft'
            }`}
          >
            <span
              className={`font-mono text-[11px] uppercase tracking-[0.06em] ${
                result.correct ? 'text-correct-dark' : 'text-wrong-dark'
              }`}
            >
              {result.correct ? '✓ Correct' : '× Not quite'}
            </span>
            <p className="mt-1 text-[15px]">
              {LETTERS[result.answer_index]}. {result.answer_text}
            </p>
            {!result.verified && (
              <p className="mt-2 text-[13px] text-attention-dark">
                ! This answer has no official key — it was{' '}
                {result.answer_source === 'inferred' ? 'suggested by a model' : 'derived'} and is
                not used for scoring. Check the source paper before trusting it.
              </p>
            )}
            {result.explanation && (
              <p className="mt-2 text-[14px] text-secondary">{result.explanation}</p>
            )}
          </div>
        )}
      </div>

      <section className="mt-6">
        <h2 className="label text-exams-dark">
          Appeared in {q.appearances.length} paper{q.appearances.length === 1 ? '' : 's'}
        </h2>
        <ul className="mt-2 grid gap-2">
          {q.appearances.map((a, i) => (
            <li
              key={i}
              className="rounded-panel border border-hairline bg-card px-4 py-3 text-[14px]"
            >
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="label text-exams-dark">{a.year ?? '—'}</span>
                <span className="text-secondary">{a.exam ?? a.paper_id}</span>
                {a.paper && <span className="label">Paper {a.paper}</span>}
                {a.qnum && <span className="label">Q{a.qnum}</span>}
                {a.page && <span className="label">p.{a.page}</span>}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
