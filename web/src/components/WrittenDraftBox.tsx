import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAccountSession, getEssayDraft, saveEssayDraft } from '../lib/api'

/** Private written-answer draft editor (§VII.9.1).
 *  Works for all four descriptive kinds (`essay`, `letter`, `precis`, `comprehension`)
 *  via GET/PUT `/api/me/essay-drafts/{question_id}`. No auto-marking, no public visibility. */
export default function WrittenDraftBox({ questionId }: { questionId: string }) {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)
  const [body, setBody] = useState('')
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    setLoading(true)
    setError('')
    setNotice('')
    getAccountSession()
      .then(async (session) => {
        if (!live) return
        setAuthenticated(session.authenticated)
        if (!session.authenticated) return
        const draft = await getEssayDraft(questionId)
        if (!live) return
        setBody(draft.body || '')
        setUpdatedAt(draft.updated_at || null)
      })
      .catch((e) => {
        if (live) setError(e instanceof Error ? e.message : 'Could not load your draft.')
      })
      .finally(() => {
        if (live) setLoading(false)
      })
    return () => {
      live = false
    }
  }, [questionId])

  async function save() {
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const saved = await saveEssayDraft(questionId, body)
      setUpdatedAt(saved.updated_at)
      setNotice('Draft saved privately to your account.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save your draft.')
    } finally {
      setSaving(false)
    }
  }

  const words = body.trim() ? body.trim().split(/\s+/).length : 0

  return (
    <section aria-label="Practice written answer" className="mt-5 rounded-xl border border-hairline bg-paper p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-base font-bold text-ink">Practice written answer</h2>
        <span className="font-mono text-xs text-muted">{words} words</span>
      </div>
      <p className="mt-1 text-xs text-secondary">
        Private to your account. Written answers are not auto-marked or published.
      </p>

      {loading ? (
        <p role="status" className="mt-3 text-sm text-secondary">
          Loading draft…
        </p>
      ) : authenticated === false ? (
        <p className="mt-3 text-sm text-secondary">
          <Link
            to={'/login?next=' + encodeURIComponent('/bank/' + questionId)}
            className="font-semibold text-link underline"
          >
            Sign in
          </Link>{' '}
          to write and save a private practice draft for this prompt.
        </p>
      ) : (
        <>
          <textarea
            aria-label="Your practice answer"
            rows={8}
            maxLength={30000}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write your response using the printed directions above…"
            className="mt-3 w-full rounded-lg border border-hairline2 bg-card p-3 text-base text-ink"
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs text-secondary">
              {updatedAt ? `Last saved ${new Date(updatedAt).toLocaleString('en-IN')}` : 'Not saved yet'}
            </span>
            <button
              type="button"
              disabled={saving}
              onClick={() => void save()}
              className="min-h-11 rounded-lg bg-ink px-4 py-2 text-sm font-bold text-paper disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save private draft'}
            </button>
          </div>
          {notice && (
            <p role="status" className="mt-2 text-xs font-medium text-correct-dark">
              {notice}
            </p>
          )}
          {error && (
            <p role="alert" className="mt-2 text-xs font-medium text-wrong-dark">
              {error}
            </p>
          )}
        </>
      )}
    </section>
  )
}
