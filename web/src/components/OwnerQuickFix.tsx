import { lazy, Suspense, useEffect, useState } from 'react'
import { accountContext } from '../lib/accountContext'
import { reviewSession } from '../lib/review'

const InlineQuestionCorrection = lazy(() => import('./InlineQuestionCorrection'))

/** One-tap correction from a question's own learner-facing page (§VII.18.9, §VIII.5.2 #11).
 *
 *  An owner who spots a typo while browsing as a learner should fix it there rather than
 *  find the question again in the console. It is the same `routine-edits` call through the
 *  same inline editor, so every guard — stale-source token, baseline digest, answer-key
 *  protection, staff MFA, immutable history, guarded publication — applies unchanged.
 *
 *  Nothing renders for signed-out visitors, learners, or subject-scoped staff: the editor
 *  is only loaded after a global owner grant is confirmed, and `/review/session` is
 *  memoised for the page load, so a learner costs at most one cheap request and no bundle. */
export default function OwnerQuickFix({ qid }: { qid: string }) {
  const [allowed, setAllowed] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    let live = true
    accountContext()
      .then((account) => (account.authenticated ? reviewSession() : null))
      .then((session) => {
        if (live && session?.grants?.some((g) => g.role === 'owner' && g.subject_id === null)) {
          setAllowed(true)
        }
      })
      .catch(() => {
        /* Signed-out and non-staff accounts simply see nothing. */
      })
    return () => {
      live = false
    }
  }, [])

  useEffect(() => setOpen(false), [qid])

  if (!allowed) return null
  return (
    <section className="mt-6 rounded-xl border border-hairline bg-paper p-3" aria-label="Owner correction">
      {open ? (
        <Suspense fallback={<p role="status">Opening the exact source…</p>}>
          <InlineQuestionCorrection question={qid} />
        </Suspense>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="min-h-11 text-sm font-semibold text-link underline"
        >
          Fix this question →
        </button>
      )}
    </section>
  )
}
