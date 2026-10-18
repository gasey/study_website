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
  useEffect(() => {
    getScoringFacts().then(setF).catch(() => setF(null))
  }, [])

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
            Every one has an official published key ({n(f?.official)}) or a transcribed one
            ({n(f?.transcribed)}). Mocks and, later, duels and cups draw only from here.
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
            Has an answer, but one we cannot trace to a published key. Usable for practice,
            always labelled unverified, never scored.
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
            was correct. Excluded from both pools until a human fixes them.
          </p>
        </div>
      </div>

      <p className="mt-4 max-w-[720px] text-[14px] leading-[1.6] text-secondary">
        Why so strict: of {n(f?.total)} questions in the bank, most answers were worked out
        rather than published. Scoring you against a worked-out answer would teach you a
        wrong fact for a real exam, and you would have no way of knowing.{' '}
        <Link to="/bank" className="text-link underline">
          Every question shows where its answer came from.
        </Link>
      </p>

      <h2 className="mt-9 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        Marks in a mock
      </h2>
      <div className="mt-1 grid [grid-template-columns:minmax(180px,2fr)_minmax(90px,1fr)_minmax(200px,2fr)] gap-2.5 border-b border-hairline2 py-2 font-mono text-[10.5px] uppercase tracking-[0.06em] text-muted">
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
          className="grid items-center gap-2.5 border-b border-hairline2 py-2.5 [grid-template-columns:minmax(180px,2fr)_minmax(90px,1fr)_minmax(200px,2fr)]"
        >
          <span className="text-[14px]">{a}</span>
          <span className="font-mono text-[13px]">{b}</span>
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
        The countdown on screen is for you. The real timing is kept on the server from the
        moment the paper opens, so a paused tab, a reload or a stopped clock changes nothing.
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

      <h2 className="mt-9 border-b border-ink pb-2.5 font-display text-[26px] font-medium">
        Not built yet
      </h2>
      <p className="mt-3 max-w-[720px] text-[15px] leading-[1.6] text-secondary">
        The design has two more numbers beyond marks. Neither exists today, and this page
        will describe them properly when they do rather than in advance.
      </p>
      <div className="mt-4 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(260px,1fr))]">
        <div className="rounded-panel border border-hairline bg-card px-5 py-[18px]">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted">
            Score · planned
          </div>
          <div className="mt-1.5 font-display text-[20px] font-medium">Monthly XP</div>
          <p className="mt-1.5 text-[13.5px] leading-[1.55] text-secondary">
            Earned by practising and playing, resets monthly, drives the leaderboard. Arrives
            with games and duels.
          </p>
        </div>
        <div className="rounded-panel border border-hairline bg-card px-5 py-[18px]">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted">
            Reputation · planned
          </div>
          <div className="mt-1.5 font-display text-[20px] font-medium">Lifetime trust</div>
          <p className="mt-1.5 text-[13.5px] leading-[1.55] text-secondary">
            Earned when others confirm your explanations and error reports. Unlocks
            Contributor, Mentor and Scholar. Arrives with discussion.
          </p>
        </div>
      </div>
    </main>
  )
}
