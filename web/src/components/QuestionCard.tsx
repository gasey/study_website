import { useState } from 'react'
import { Link } from 'react-router-dom'
import { submitAnswer, type AnswerResult, type Question } from '../lib/api'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

/** Bank question card, ported from `India Study Map v3.dc.html` line 407.
 *  Exact values and the README-vs-markup disagreements are recorded in
 *  docs/DESIGN-FIDELITY.md — read that before changing anything here. */
export default function QuestionCard({ q }: { q: Question }) {
  const [picked, setPicked] = useState<number | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [busy, setBusy] = useState(false)

  // The prototype answers inline on the list: "Tap an option to check it".
  async function pick(i: number) {
    if (result || busy) return
    setPicked(i)
    setBusy(true)
    try {
      setResult(await submitAnswer(q.id, i))
    } catch {
      setPicked(null) // let them try again rather than stranding a selection
    } finally {
      setBusy(false)
    }
  }

  const years = [q.first_year, q.last_year].filter(Boolean)
  const yearLabel = years.length === 2 && years[0] !== years[1]
    ? `${years[0]}, ${years[1]}`
    : String(years[0] ?? '—')

  return (
    <article className="mb-3 rounded-[14px] border border-hairline bg-card px-[22px] py-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span className="font-mono text-[11px] text-muted">
          {q.last_year ?? q.first_year ?? '—'} · {q.type === 'mcq' ? 'MCQ' : 'Descriptive'}
        </span>

        {/* Provenance is an OUTLINED pill, not a filled one. Official keys
            read green; everything else reads blue and is never scored. */}
        <span
          className={`rounded-pill border px-2 py-[2px] font-mono text-[10px] uppercase tracking-[0.06em] ${
            q.verified ? 'border-keyed text-keyed' : 'border-prov text-prov'
          }`}
        >
          {q.answer_source === 'official'
            ? 'Official key'
            : q.answer_source === 'key'
              ? 'Transcribed key'
              : q.answer_source === 'derived'
                ? 'Derived answer'
                : q.answer_source === 'inferred'
                  ? 'Unverified'
                  : 'No published key'}
        </span>

        {q.times_asked > 1 && (
          <span
            title={yearLabel}
            className="rounded-pill bg-ink px-[9px] py-[3px] font-mono text-[10px] uppercase tracking-[0.06em] text-paper"
          >
            Asked {q.times_asked}× · {yearLabel}
          </span>
        )}

        <Link
          to={`/bank/${q.id}`}
          className="ml-auto min-h-11 rounded-pill px-2 font-mono text-[11px] font-medium text-link hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-link"
        >
          Details ↗
        </Link>
      </div>

      <div className="my-[10px] mb-[14px] font-display text-[21px] leading-[1.35] [text-wrap:pretty]">
        {q.question}
      </div>

      {q.options.length > 0 && (
        <div className="grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(220px,1fr))]">
          {q.options.map((text, i) => {
            const isCorrect = result?.answer_index === i
            const isPick = picked === i
            let cls = 'bg-opt-bg border-opt-border text-ink'
            let mark = ''
            if (result) {
              if (isCorrect) {
                cls = 'bg-keyed-soft border-keyed text-ink'
                mark = isPick ? 'Correct' : 'Answer'
              } else if (isPick) {
                cls = 'bg-mypick-soft border-mypick text-ink'
                mark = 'Your pick'
              } else {
                cls = 'bg-opt-bg border-opt-border text-opt-muted'
              }
            }
            return (
              <button
                key={i}
                onClick={() => pick(i)}
                disabled={!!result || busy}
                className={`flex min-h-[44px] items-center gap-3 rounded-[6px] border px-[14px] py-[11px] text-left text-[15px] ${cls} ${
                  result ? 'cursor-default' : 'cursor-pointer'
                }`}
              >
                <span className="w-4 shrink-0 font-mono text-[12px]">{LETTERS[i]}</span>
                <span className="flex-1">{text}</span>
                {/* The prototype marks state with a WORD, not a symbol. */}
                {mark && <span className="shrink-0 font-mono text-[11px]">{mark}</span>}
              </button>
            )
          })}
        </div>
      )}

      {result && (
        <div className="mt-3 text-[14px] leading-[1.6] text-secondary [text-wrap:pretty]">
          Correct answer: {result.answer_text}.{' '}
          {result.verified
            ? 'This is the answer keyed for the source paper.'
            : 'This answer has no official key — it is not used for scoring. Check the source paper before trusting it.'}
          {result.explanation && ` ${result.explanation}`}
        </div>
      )}
    </article>
  )
}
