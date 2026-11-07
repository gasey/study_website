import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getScoringFacts, type ScoringFacts } from '../lib/api'

/** The scoring explainer, prototype line 1390.
 *
 *  The prototype's version is mostly about Score, Reputation and tiers —
 *  XP, leaderboards, Contributor/Mentor/Scholar. None of that exists yet
 *  (Phase 5), and publishing a rulebook for rules the app does not follow
 *  would be the worst kind of documentation. So this explains what is
 *  actually true today and labels the rest as planned, per CLAUDE.md:
 *  "where a control cannot be honest on today's data, say why".
 *
 *  Numbers come from the API rather than being typed in, so this page
 *  cannot drift away from the database. */
export default function Scoring() {
  const [f, setF] = useState<ScoringFacts | null>(null)
  const [failed,setFailed]=useState(false),[retry,setRetry]=useState(0)
  useEffect(() => {
    let live=true;setFailed(false)
    getScoringFacts().then(value=>{if(live)setF(value)}).catch(()=>{if(live)setFailed(true)})
    return()=>{live=false}
  }, [retry])

  const n = (x?: number) => (x == null ? '—' : x.toLocaleString('en-IN'))

  return (
    <main className="mx-auto max-w-shell px-6 pb-24 pt-9">
      <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-rewards-dark">
        Scoring
      </div>
      <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)] font-medium -tracking-[0.02em]">
        How marks work
      </h1>
      <p className="mt-3 max-w-[720px] text-[17px] leading-[1.6] text-secondary [text-wrap:pretty]">
        One rule matters more than the rest: a mock only ever draws from questions with a
        published answer key. Everything else — how many marks, whether wrong answers cost
        you — is set per paper and shown before you start.
      </p>

      {failed&&<p role="alert" className="mt-4 rounded-lg border border-hairline bg-card p-4 text-sm">Question counts could not load. <button className="min-h-11 px-3 font-semibold text-link underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>}
      {!f&&!failed&&<p role="status" className="mt-4 text-sm text-secondary">Loading question counts…</p>}
      <h2 className="mt-8 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        What can be scored
      </h2>
      <div className="mt-4 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(300px,1fr))]">
        <div className="rounded-panel bg-[#DCEBD9] px-5 py-[18px]">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-[#3F8350]">
            Scored
          </div>
          <div className="mt-1.5 font-display text-[22px] font-medium">
            {n(f?.scorable)} questions
          </div>
          <p className="mt-1.5 text-[13.5px] leading-[1.55] text-[#2F4A33]">
            These questions have answers from official examination keys, including keys copied from the original documents.
          </p>
        </div>
        <div className="rounded-panel bg-[#DAE3F1] px-5 py-[18px]">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-[#33609E]">
            Practice only
          </div>
          <div className="mt-1.5 font-display text-[22px] font-medium">
            {n(f?.practice)} questions
          </div>
          <p className="mt-1.5 text-[13.5px] leading-[1.55] text-[#2B3F5E]">
            These answers do not come from an official key. Reviewed solutions may be used for practice estimates; answers awaiting review are not used in scored tests.
          </p>
        </div>
        <div className="rounded-panel bg-[#EDE5D4] px-5 py-[18px]">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-attention-dark">
            Held back
          </div>
          <div className="mt-1.5 font-display text-[22px] font-medium">
            {n(f?.dup_defect)} questions
          </div>
          <p className="mt-1.5 text-[13.5px] leading-[1.55] text-[#4A4335]">
            The same option text is printed twice, so there is no way to say which position
            was correct. These questions cannot be scored until the options are corrected.
          </p>
        </div>
      </div>

      <p className="mt-4 max-w-[720px] text-[14px] leading-[1.6] text-secondary">
        Official keys and reviewed worked solutions are labelled separately. Check the
        answer source when revising, especially when a key is provisional or disputed.{' '}
        <Link to="/bank" className="text-link underline">
          Every question shows where its answer came from.
        </Link>
      </p>

      <h2 className="mt-9 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        Marks in a mock
      </h2>
      <div className="mt-1 hidden gap-2.5 border-b border-hairline2 py-2 font-mono text-[10.5px] uppercase tracking-[0.06em] text-muted sm:grid sm:[grid-template-columns:minmax(140px,2fr)_minmax(80px,1fr)_minmax(180px,2fr)]">
        <span>Outcome</span>
        <span>Marks</span>
        <span>Notes</span>
      </div>
      {[
        ['Correct', '+1', 'Default. A paper can set its own value.'],
        ['Wrong', '0', 'No negative marking by default — several Mizoram PSC papers have none.'],
        ['Skipped', '0', 'Never penalised beyond the mark you did not earn.'],
        ['Submitted late', 'unchanged', 'Recorded and flagged, not voided. A slow network should not cost you a paper.'],
      ].map(([a, b, c]) => (
        <div
          key={a}
          className="flex flex-col gap-1 border-b border-hairline2 py-3 sm:grid sm:items-center sm:gap-2.5 sm:py-2.5 sm:[grid-template-columns:minmax(140px,2fr)_minmax(80px,1fr)_minmax(180px,2fr)]"
        >
          <span className="flex items-baseline gap-2 text-[14px]">
            {a}
            <span className="font-mono text-[13px] text-muted sm:hidden">{b}</span>
          </span>
          <span className="hidden font-mono text-[13px] sm:block">{b}</span>
          <span className="text-[13px] text-secondary">{c}</span>
        </div>
      ))}
      <p className="mt-3 max-w-[720px] text-[14px] leading-[1.6] text-secondary">
        Marking is fixed when the paper starts and stored with it, so changing a rule later
        can never silently re-score a mock you have already sat.
      </p>

      <h2 className="mt-9 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        The clock
      </h2>
      <p className="mt-3 max-w-[720px] text-[15px] leading-[1.6] text-secondary">
        The timer starts when you open the test. Pausing the tab or reloading the page
        does not pause the timer.
        Submit after time and the attempt still counts — it is just marked late.
      </p>

      <h2 className="mt-9 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        Mistakes
      </h2>
      <p className="mt-3 max-w-[720px] text-[15px] leading-[1.6] text-secondary">
        A question is a mistake when your <em>latest</em> answer to it was wrong. Get it right
        anywhere — practice, another mock — and it leaves{' '}
        <Link to="/mistakes" className="text-link underline">
          your mistakes list
        </Link>
        . Showing questions you have already learned would waste your time and make your
        progress look worse than it is.
      </p>

      <h2 className="mt-9 font-display text-[26px]">XP and reward points</h2><p className="mt-3 text-[15px] leading-relaxed text-secondary">Your first correct verified-key answer to a unique question earns 10 XP and 1 reward point, with a shared 300 daily study/game XP cap. Repeats, guests and unverified answers do not earn question rewards. Published contribution credit also earns XP and points; reversals remain in history. Exam marks stay separate.</p><p className="mt-3 text-[15px] text-secondary">Monthly XP drives the activity leaderboard; lifetime XP determines your level. Spending reward points on an enabled benefit never reduces XP. Public participation is optional.</p><Link to="/rewards" className="mt-4 inline-block min-h-11 text-link underline">Open rewards, rules and point history →</Link>
    </main>
  )
}
