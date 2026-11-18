import {learnerExplanation} from '../lib/answerStatus'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMistakes, type Mistake } from '../lib/api'

/** Mistakes wall (prototype 1546) plus a list of past papers.
 *
 *  "Mistake" means the LATEST attempt on a question was wrong. Get it right
 *  later and it leaves the list — showing questions you have since learned
 *  would waste your time and understate your progress. */
export default function Mistakes() {
  const [items, setItems] = useState<Mistake[] | null>(null)
  const [retry, setRetry] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let live = true
    setItems(null); setError(null)
    getMistakes().then(rows => {if(live)setItems(rows)}).catch(e => {if(live)setError(e.message)})
    const refresh = () => {live=false;setItems(null);setRetry(n=>n+1)}
    window.addEventListener('ism-auth-change', refresh)
    window.addEventListener('ism-progress-change', refresh)
    return () => {live=false;window.removeEventListener('ism-auth-change',refresh);window.removeEventListener('ism-progress-change',refresh)}
  }, [retry])

  return (
    <section className="mt-5 rounded-panel border border-hairline bg-card p-4" aria-label="Latest mistakes">
      <h2 className="font-display text-[24px] font-semibold">Latest mistakes</h2>
      <p className="mt-2 max-w-2xl text-[14px] text-secondary">
        Questions your latest answer got wrong. Answer one correctly anywhere in the app and it
        leaves this list.
      </p>

      <div className="mt-4">
        <h2 className="border-b border-hairline pb-2 font-display text-[22px] font-medium">
          {items ? `${items.length} to review` : 'Loading…'}
        </h2>

        {error && (
          <div role="alert" className="mt-4 rounded-[14px] border border-mypick bg-mypick-soft p-4 text-mypick">
            {error} <button className="min-h-11 underline print:hidden" onClick={()=>setRetry(n=>n+1)}>Try again</button>
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
                <p className="mt-2 text-[14px] leading-[1.6] text-secondary">{learnerExplanation(m.explanation)}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
