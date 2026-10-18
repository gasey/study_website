import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMistakes, listMocks, type Mistake, type MockSummary } from '../lib/api'
import { mmss } from '../components/MockResultView'

/** Mistakes wall (prototype 1546) plus a list of past papers.
 *
 *  "Mistake" means the LATEST attempt on a question was wrong. Get it right
 *  later and it leaves the list — showing questions you have since learned
 *  would waste your time and understate your progress. */
export default function Mistakes() {
  const [items, setItems] = useState<Mistake[] | null>(null)
  const [mocks, setMocks] = useState<MockSummary[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getMistakes().then(setItems).catch((e) => setError(e.message))
    listMocks().then(setMocks).catch(() => setMocks([]))
  }, [])

  return (
    <div className="mx-auto max-w-shell px-6 pb-24 pt-10">
      <div className="label text-practice-dark">Review</div>
      <h1 className="mt-1 font-display text-[34px] font-semibold leading-tight">Mistakes</h1>
      <p className="mt-2 max-w-2xl text-[14px] text-secondary">
        Questions your latest answer got wrong. Answer one correctly anywhere in the app and it
        leaves this list.
      </p>

      {mocks.length > 0 && (
        <section className="mt-8">
          <h2 className="border-b border-hairline pb-2 font-display text-[22px] font-medium">
            Past papers
          </h2>
          <div className="mt-3 flex flex-col gap-2">
            {mocks.map((m) => (
              <div
                key={m.id}
                className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-[14px] border border-hairline bg-card px-5 py-3.5"
              >
                <span className="font-display text-[17px] font-medium">{m.collection_title}</span>
                {m.submitted_at ? (
                  <>
                    <span className="font-mono text-[12px] text-muted">
                      {m.n_correct}/{m.total} correct
                      {m.elapsed_seconds != null && ` · ${mmss(m.elapsed_seconds)}`}
                      {m.late && ' · late'}
                    </span>
                    <span className="grow" />
                    <Link to={`/results/${m.id}`} className="text-[13px] font-semibold text-link">
                      See result →
                    </Link>
                  </>
                ) : (
                  <>
                    <span className="font-mono text-[12px] text-attention-dark">In progress</span>
                    <span className="grow" />
                    <Link
                      to={`/exams/${m.collection_id}/mock`}
                      className="text-[13px] font-semibold text-link"
                    >
                      Resume →
                    </Link>
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mt-9">
        <h2 className="border-b border-hairline pb-2 font-display text-[22px] font-medium">
          {items ? `${items.length} to review` : 'Loading…'}
        </h2>

        {error && (
          <div className="mt-4 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick">
            {error}
          </div>
        )}

        {items?.length === 0 && (
          <p className="mt-4 rounded-[14px] border border-hairline bg-card p-6 text-muted">
            Nothing here. Either you have not answered anything wrong yet, or you have since got
            them all right.
          </p>
        )}

        <div className="mt-3 flex flex-col gap-3">
          {items?.map((m) => (
            <div
              key={m.id}
              className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]"
            >
              <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-[0.06em]">
                <span className="rounded-pill bg-mypick-soft px-2 py-[2px] text-mypick">
                  Wrong {m.times_wrong}×
                </span>
                <span className="text-muted">
                  {new Date(m.last_attempt).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                  })}
                </span>
                <span className="grow" />
                <Link to={`/bank/${m.id}`} className="text-link">
                  Try again ↗
                </Link>
              </div>
              <p className="mt-2 font-display text-[19px] leading-snug">{m.question}</p>
              <div className="mt-2 grid gap-1 text-[14px]">
                <span className="text-mypick">You chose: {m.chosen_text}</span>
                <span className="text-keyed">Answer: {m.answer_text}</span>
              </div>
              {m.explanation && (
                <p className="mt-2 text-[14px] leading-[1.6] text-secondary">{m.explanation}</p>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
