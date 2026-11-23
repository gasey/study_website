import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'

type Status = {
  user_id: string
  available: boolean
  verified: boolean
  code: { code: string; enabled: boolean; version: number } | null
  credited_this_rolling_year: number
  signup_referral: { state: string; scored_attempts: number } | null
}

export default function ReferralPanel() {
  const [data, setData] = useState<Status | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [retry, setRetry] = useState(0)
  const generation = useRef(0)
  const saving = useRef(false)

  useEffect(() => {
    let live = true
    const epoch = ++generation.current
    setData(null)
    setError('')
    setBusy(false)
    saving.current = false
    reviewRequest<Status>('/referrals/me')
      .then((v) => {
        if (live && epoch === generation.current) setData(v)
      })
      .catch((e) => {
        if (live && epoch === generation.current) setError((e as Error).message)
      })
    const refresh = () => {
      generation.current++
      setData(null)
      setRetry((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', refresh)
    return () => {
      live = false
      generation.current++
      window.removeEventListener('ism-auth-change', refresh)
    }
  }, [retry])

  async function save() {
    if (!data || saving.current) return
    saving.current = true
    setBusy(true)
    setError('')
    const epoch = generation.current
    try {
      const next = await reviewRequest<Status>('/referrals/code', {
        user_id: data.user_id,
        expected_version: data.code?.version || 0,
        enabled: !data.code?.enabled,
      })
      if (epoch === generation.current) setData(next)
    } catch (e) {
      if (epoch === generation.current) setError((e as Error).message)
    } finally {
      if (epoch === generation.current) {
        saving.current = false
        setBusy(false)
      }
    }
  }

  return (
    <section className="at-card" aria-labelledby="referral-title">
      <div className="at-card-head">
        <div>
          <h2 id="referral-title">Invite a study friend</h2>
          <p>7 Pro days each after 10 verified answers</p>
        </div>
        {data && (
          <span className="finna-st-pill finna-st-pill--teal">
            {data.credited_this_rolling_year} / 5 credited
          </span>
        )}
      </div>

      <p className="text-xs leading-relaxed text-secondary">
        When a friend joins through your link, verifies their email and completes
        10 scored answers, you each receive 7 Pro days (up to 5 per rolling
        year).
      </p>

      {!data && !error && (
        <p role="status" className="mt-3 text-xs text-secondary">
          Loading invitations…
        </p>
      )}
      {error && (
        <p role="alert" className="at-inline-err mt-3">
          {error}{' '}
          <button
            type="button"
            className="underline"
            onClick={() => setRetry((n) => n + 1)}
          >
            Reload invitations
          </button>
        </p>
      )}
      {data && (
        <div className="mt-3 flex flex-col gap-2">
          {!data.available && (
            <p className="text-xs text-secondary">
              Invitation rewards open after paid plans launch. You can still turn
              an existing link off.
            </p>
          )}
          {!data.verified && (
            <p className="text-xs text-secondary">
              Verify your email in{' '}
              <Link to="/account/security" className="font-bold text-link underline">
                Account security
              </Link>{' '}
              before creating a link.
            </p>
          )}
          <p className="text-xs text-secondary">
            Credited invitations in the past year:{' '}
            <strong className="text-ink">
              {data.credited_this_rolling_year} / 5
            </strong>
          </p>
          {data.code?.enabled && (
            <label className="at-field mt-1">
              <span>Your invitation link</span>
              <input
                readOnly
                aria-label="Your invitation link"
                value={window.location.origin + '/join?ref=' + data.code.code}
                onFocus={(e) => e.currentTarget.select()}
              />
              <small className="text-xs text-secondary">
                Select and copy to share. Turning it off prevents new signups.
              </small>
            </label>
          )}
          <div className="mt-1">
            <button
              type="button"
              onClick={() => void save()}
              disabled={
                busy || (!data.code?.enabled && (!data.available || !data.verified))
              }
              className={data.code?.enabled ? 'finna-st-btn' : 'cr-primary-btn'}
            >
              {busy
                ? 'Saving…'
                : data.code?.enabled
                  ? 'Turn invitation link off'
                  : data.code
                    ? 'Turn invitation link on'
                    : 'Create invitation link'}
            </button>
          </div>
          {data.signup_referral && (
            <p role="status" className="text-xs text-secondary">
              {data.signup_referral.state === 'pending'
                ? `Your signup invitation: ${data.signup_referral.scored_attempts} / 10 scored answers.`
                : data.signup_referral.state === 'credited'
                  ? 'Your signup invitation added 7 Pro days.'
                  : data.signup_referral.state === 'capped'
                    ? 'Your inviter reached the yearly limit before this invitation qualified.'
                    : 'Your signup invitation is no longer eligible.'}{' '}
              <Link to="/billing" className="font-bold text-link underline">
                Plan &amp; billing
              </Link>
            </p>
          )}
        </div>
      )}
    </section>
  )
}

export function SignupReferral({
  code,
  onRemove,
  disabled = false,
}: {
  code: string
  onRemove: () => void
  disabled?: boolean
}) {
  const [available, setAvailable] = useState<boolean | null>(null)
  useEffect(() => {
    let live = true
    setAvailable(null)
    fetch('/api/referrals/invite/' + encodeURIComponent(code), {
      credentials: 'omit',
      cache: 'no-store',
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((v) => {
        if (live) setAvailable(v?.available === true)
      })
      .catch(() => {
        if (live) setAvailable(false)
      })
    return () => {
      live = false
    }
  }, [code])
  return (
    <aside className="mt-4 rounded-lg border border-hairline bg-paper p-3 text-sm">
      <p>
        {available === null
          ? 'Checking your invitation…'
          : available
            ? 'An invitation is attached. After you verify your email and complete 10 scored answers, you and your inviter can each receive 7 Pro days, subject to their 5-per-year limit.'
            : 'Invitation rewards are unavailable for this link. You can still create your account.'}
      </p>
      <button
        type="button"
        disabled={disabled}
        onClick={onRemove}
        className="mt-1 min-h-11 text-link underline disabled:opacity-50"
      >
        Remove invitation
      </button>
    </aside>
  )
}
