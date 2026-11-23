import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import { accountGeneration } from '../lib/accountContext'
import {
  getToday,
  getHome,
  getExamBookmarks,
  setPrimaryExam,
  removeExamBookmark,
  type TodayPlan,
  type HomeData,
} from '../lib/api'
import { choosePreferredExam } from '../lib/preferredExam'
import { FocusPicker } from './TodayCard'
import AccountSessions from './AccountSessions'

type Tools = {
  user_id: string
  identity_version: number
  email_verified: boolean
  recent: boolean
  mfa_enabled: boolean
  creator_public: boolean
  points: number
  board_public: boolean
  closure_blockers: string[]
}

export default function AccountTools({
  userKey,
  onEdit,
}: {
  userKey: string
  onEdit: () => void
}) {
  const [data, setData] = useState<Tools | null>(null)
  const [plan, setPlan] = useState<TodayPlan | null>(null)
  const [exams, setExams] = useState<HomeData['collections']>([])
  const [saved, setSaved] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [retry, setRetry] = useState(0)
  const [confirmation, setConfirmation] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const download = useRef<AbortController | null>(null)

  useEffect(() => {
    let live = true
    setData(null)
    setPlan(null)
    setError('')
    setConfirmation('')
    Promise.all([
      reviewRequest<Tools>('/me/account-tools'),
      getToday(),
      getHome(),
      getExamBookmarks(),
    ])
      .then(([tools, today, home, bookmarks]) => {
        if (live) {
          setData(tools)
          setPlan(today)
          setExams(home.collections)
          setSaved(bookmarks.collection_ids)
        }
      })
      .catch((e) => {
        if (live) setError(e.message)
      })
    const refresh = () => {
      live = false
      download.current?.abort()
      dialog.current?.close()
      setData(null)
      setPlan(null)
      setConfirmation('')
      setRetry((n) => n + 1)
    }
    for (const event of [
      'ism-auth-change',
      'ism-calendar-change',
      'finna-exam-change',
      'ism-focus-change',
    ])
      window.addEventListener(event, refresh)
    return () => {
      live = false
      download.current?.abort()
      for (const event of [
        'ism-auth-change',
        'ism-calendar-change',
        'finna-exam-change',
        'ism-focus-change',
      ])
        window.removeEventListener(event, refresh)
    }
  }, [retry, userKey])

  async function mutate(path: string, body: unknown) {
    const generation = accountGeneration()
    setBusy(true)
    setError('')
    try {
      await reviewRequest(path, body)
      if (generation === accountGeneration()) {
        setRetry((n) => n + 1)
        if (path === '/rewards/visibility')
          window.dispatchEvent(new Event('ism-community-standing-change'))
      }
    } catch (e) {
      if (generation === accountGeneration()) setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function primary(id: string) {
    setBusy(true)
    setError('')
    try {
      await setPrimaryExam(id)
      choosePreferredExam(id)
      setRetry((n) => n + 1)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function unsave(id: string) {
    setBusy(true)
    setError('')
    try {
      await removeExamBookmark(id)
      window.dispatchEvent(new Event('finna-exam-change'))
      setRetry((n) => n + 1)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function exportData() {
    if (!data) return
    const generation = accountGeneration()
    const controller = new AbortController()
    download.current = controller
    setBusy(true)
    setError('')
    try {
      const response = await fetch(
        '/api/me/data-export?' + new URLSearchParams({ user_id: data.user_id }),
        { credentials: 'include', cache: 'no-store', signal: controller.signal },
      )
      if (!response.ok) {
        let message = 'Your export could not be created.'
        try {
          message = (await response.json()).detail || message
        } catch {
          /* ignore */
        }
        throw new Error(message)
      }
      const blob = await response.blob()
      if (generation !== accountGeneration() || controller.signal.aborted) return
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'finna-data.json'
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      if (!controller.signal.aborted && generation === accountGeneration())
        setError((e as Error).message)
    } finally {
      if (download.current === controller) download.current = null
      setBusy(false)
    }
  }

  async function leave(close: boolean) {
    if (!data) return
    setBusy(true)
    setError('')
    try {
      await reviewRequest(
        close ? '/me/account-close' : '/me/account-signout-all',
        close
          ? {
              user_id: data.user_id,
              expected_version: data.identity_version,
              confirmation,
            }
          : { user_id: data.user_id },
      )
      dialog.current?.close()
      window.dispatchEvent(new Event('ism-auth-change'))
      window.location.assign('/login' + (close ? '?closed=1' : ''))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-labelledby="account-tools-title" className="at-wrap">
      <div className="at-section-head">
        <div>
          <span className="cr-eyebrow">Account &amp; Workspace</span>
          <h2 id="account-tools-title">Your account tools</h2>
        </div>
        {data && (
          <Link to="/profile/rewards" className="at-wallet-pill">
            <strong>{data.points.toLocaleString('en-IN')}</strong>
            <span>reward points →</span>
          </Link>
        )}
      </div>

      {error && (
        <p role="alert" className="at-inline-err">
          {error}{' '}
          <button type="button" className="underline" onClick={() => setRetry((n) => n + 1)}>
            Reload tools
          </button>
        </p>
      )}
      {!data && !error ? (
        <div role="status" className="finna-card text-sm text-secondary">
          Loading your account settings…
        </div>
      ) : (
        data && (
          <div className="at-grid">
            <section className="at-card">
              <div className="at-card-head">
                <div>
                  <h3>Identity &amp; visibility</h3>
                  <p>Display name, avatar and weekly leaderboard presence</p>
                </div>
                <span className={data.creator_public ? 'finna-st-pill finna-st-pill--green' : 'finna-st-pill finna-st-pill--gray'}>
                  {data.creator_public ? 'Public creator' : 'Private creator'}
                </span>
              </div>

              <div className="at-btn-row">
                <button type="button" className="finna-st-btn" onClick={onEdit}>
                  Edit name, handle &amp; bio
                </button>
                <Link className="finna-st-btn" to="/profile/avatar">
                  Avatar &amp; inventory
                </Link>
                {data.creator_public && (
                  <Link
                    className="finna-st-btn"
                    to={'/creators/' + encodeURIComponent(data.user_id)}
                  >
                    My creator page
                  </Link>
                )}
              </div>

              <div className="finna-st-togglerow mt-3">
                <div className="finna-st-togglerow-txt">
                  <div className="finna-st-togglerow-title">
                    Show my handle on weekly boards
                  </div>
                  <div className="finna-st-togglerow-sub">
                    Opt in to appear on weekly XP leaderboards
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={data.board_public}
                  aria-label="Show my handle and score on weekly boards"
                  disabled={busy}
                  onClick={() =>
                    void mutate('/rewards/visibility', {
                      public: !data.board_public,
                    })
                  }
                  className={'finna-st-toggle' + (data.board_public ? ' is-on' : '')}
                >
                  <span className="finna-st-toggle-dot" />
                </button>
              </div>

              <div className="at-card-foot">
                <Link className="at-link" to="/creators/settings">
                  Creator visibility &amp; follows →
                </Link>
              </div>
            </section>

            <section className="at-card">
              <div className="at-card-head">
                <div>
                  <h3>Study setup</h3>
                  <p>Primary target exam, focus subjects and saved exams</p>
                </div>
                {plan?.exam_preparation && (
                  <span className="finna-st-pill finna-st-pill--teal">
                    {plan.exam_preparation.days_remaining}d left
                  </span>
                )}
              </div>

              {plan && (
                <div className="at-study-controls">
                  <label className="at-field">
                    <span>Primary exam</span>
                    <select
                      aria-label="Account primary exam"
                      value={plan.exam?.id || ''}
                      disabled={busy}
                      onChange={(e) => void primary(e.target.value)}
                    >
                      <option value="" disabled>
                        Choose an exam
                      </option>
                      {exams.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.title}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="at-focus-row">
                    <FocusPicker
                      focus={plan.focus}
                      onSaved={() => setRetry((n) => n + 1)}
                    />
                    <span className="text-xs text-secondary">
                      {plan.focus.items.map((i) => i.label).join(' · ') ||
                        'No focus subjects chosen yet'}
                    </span>
                  </div>

                  {plan.exam?.is_primary && (
                    <Link className="at-link" to="/onboarding">
                      Optional 10-question exam check-in →
                    </Link>
                  )}
                </div>
              )}

              <details className="at-saved-details">
                <summary>
                  <span>Saved exams</span>
                  <span className="finna-st-badge">{saved.length}</span>
                </summary>
                {saved.length ? (
                  <div className="at-saved-list">
                    {saved.map((id) => (
                      <div className="at-saved-chip" key={id}>
                        <Link to={'/exams/' + encodeURIComponent(id)}>
                          {exams.find((e) => e.id === id)?.title || id}
                        </Link>
                        <button
                          type="button"
                          disabled={busy}
                          aria-label={`Remove ${exams.find((e) => e.id === id)?.title || id}`}
                          onClick={() => void unsave(id)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-xs text-secondary">
                    Save an exam from its page to keep it pinned here.
                  </p>
                )}
              </details>

              <div className="at-card-foot">
                <Link className="at-link" to="/calendar">
                  Exam targets &amp; calendar →
                </Link>
              </div>
            </section>

            <section className="at-card at-card--wide">
              <div className="at-card-head">
                <div>
                  <h3>Privacy, security &amp; sessions</h3>
                  <p>
                    Desk progress, mistakes and focus times stay private until
                    shared in a chosen room.
                  </p>
                </div>
                <span className={data.mfa_enabled ? 'finna-st-pill finna-st-pill--green' : 'finna-st-pill finna-st-pill--amber'}>
                  {data.mfa_enabled ? 'MFA enabled' : 'MFA off'}
                </span>
              </div>

              <div className="at-sec-grid">
                <Link className="at-sec-tile" to="/account/security">
                  <strong>Authenticator</strong>
                  <small>{data.mfa_enabled ? 'Manage 2FA & codes' : 'Set up 6-digit MFA'}</small>
                </Link>
                <Link className="at-sec-tile" to="/creators/settings#blocked-users">
                  <strong>Blocked users</strong>
                  <small>Manage hidden accounts</small>
                </Link>
                <Link className="at-sec-tile" to="/desk">
                  <strong>Desk sharing</strong>
                  <small>Room visibility controls</small>
                </Link>
                <Link className="at-sec-tile" to="/account/security#account-password">
                  <strong>Password &amp; recovery</strong>
                  <small>Update sign-in password</small>
                </Link>
              </div>

              <AccountSessions />

              <div className="at-sec-actions">
                <button
                  type="button"
                  disabled={busy}
                  className="finna-st-btn"
                  onClick={() => void leave(false)}
                >
                  Sign out everywhere
                </button>
              </div>
            </section>

            <section className="at-card">
              <div className="at-card-head">
                <div>
                  <h3>Your data export</h3>
                  <p>Portable JSON archive of your account &amp; study history</p>
                </div>
              </div>
              <p className="text-xs leading-relaxed text-secondary">
                Download your account, answers, progress, posts, wallet history
                and private plans as JSON. Credentials and answer keys are
                excluded.
              </p>
              <div className="mt-3">
                <button
                  type="button"
                  disabled={busy}
                  className="cr-primary-btn"
                  onClick={() => void exportData()}
                >
                  {busy ? 'Preparing export…' : 'Download my data (JSON)'}
                </button>
              </div>
            </section>

            <section className="at-card at-card--danger">
              <details className="at-danger-details">
                <summary>
                  <div>
                    <h3>Close my account</h3>
                    <p>Permanently end access and sign out all devices</p>
                  </div>
                  <span className="finna-st-pill finna-st-pill--warn">
                    Danger zone
                  </span>
                </summary>
                <div className="at-danger-body">
                  <p className="text-xs leading-relaxed text-secondary">
                    Closing immediately ends account access, signs out every
                    device, and removes your sign-in details, avatar, bio,
                    private calendar and private desk plan. Export your data
                    first if you want a copy.
                  </p>
                  {data.email_verified ? (
                    <p className="mt-2 text-xs text-secondary">
                      You can reopen within 30 days via a single-use link sent
                      to your verified email.
                    </p>
                  ) : (
                    <p className="mt-2 text-xs text-secondary">
                      Your email is not verified, so self-service reopening will
                      not be available.{' '}
                      <Link className="text-link underline" to="/account/security">
                        Verify email first
                      </Link>
                      .
                    </p>
                  )}
                  {data.closure_blockers.map((reason) => (
                    <p key={reason} className="mt-2 text-xs font-semibold text-wrong-dark">
                      {reason}
                    </p>
                  ))}
                  {!data.recent && (
                    <Link
                      className="mt-2 inline-flex text-xs font-bold text-link underline"
                      to="/login?next=%2Fprofile"
                    >
                      Sign in again before closing →
                    </Link>
                  )}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Link to="/billing" className="finna-st-btn">
                      Plan &amp; billing
                    </Link>
                    <button
                      type="button"
                      className="at-danger-btn"
                      disabled={
                        busy || !data.recent || data.closure_blockers.length > 0
                      }
                      onClick={() => {
                        setConfirmation('')
                        dialog.current?.showModal()
                      }}
                    >
                      Review account closure
                    </button>
                  </div>
                </div>
              </details>
            </section>
          </div>
        )
      )}

      <dialog
        ref={dialog}
        aria-labelledby="close-account-title"
        className="at-dialog"
      >
        <h3 id="close-account-title" className="text-xl font-bold">
          Close your account?
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-secondary">
          This ends access and signs out every device immediately.{' '}
          {data?.email_verified
            ? 'You can reopen within 30 days using a single-use link sent to your verified email.'
            : 'This email is not verified, so self-service reopening will not be available.'}{' '}
          Private calendar and desk data are removed at closure.
        </p>
        <label className="mt-4 block text-xs font-bold uppercase tracking-wider text-secondary">
          Type DELETE MY ACCOUNT
          <input
            autoComplete="off"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            className="mt-2 min-h-11 w-full rounded-xl border border-hairline bg-paper px-3 text-sm text-ink"
          />
        </label>
        {error && (
          <p role="alert" className="mt-3 text-sm text-wrong">
            {error}
          </p>
        )}
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            disabled={busy}
            className="finna-st-btn"
            onClick={() => dialog.current?.close()}
          >
            Keep my account
          </button>
          <button
            type="button"
            disabled={busy || confirmation !== 'DELETE MY ACCOUNT'}
            className="at-danger-btn"
            onClick={() => void leave(true)}
          >
            Close account
          </button>
        </div>
      </dialog>
    </section>
  )
}
