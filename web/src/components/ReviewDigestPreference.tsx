import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'

type Preference = {
  user_id: string
  enabled: boolean
  verified: boolean
  available: boolean
  version: number
}

export default function ReviewDigestPreference() {
  const [data, setData] = useState<Preference | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [retry, setRetry] = useState(0)
  const generation = useRef(0)
  const saving = useRef(false)

  useEffect(() => {
    let live = true
    const epoch = ++generation.current
    setData(null)
    setError('')
    setNotice('')
    setBusy(false)
    saving.current = false
    reviewRequest<Preference>('/review-digest/preferences')
      .then((value) => {
        if (live && epoch === generation.current) setData(value)
      })
      .catch((e) => {
        if (live && epoch === generation.current) setError((e as Error).message)
      })
    const refresh = () => {
      generation.current++
      setData(null)
      setNotice('')
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
    setNotice('')
    const epoch = generation.current
    try {
      const next = await reviewRequest<Preference>('/review-digest/preferences', {
        user_id: data.user_id,
        expected_version: data.version,
        enabled: !data.enabled,
      })
      if (epoch === generation.current) {
        setData(next)
        setNotice(
          next.enabled ? 'Evening reminders are on.' : 'Review reminders are off.',
        )
      }
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
    <section className="at-card" aria-labelledby="review-email-title">
      <div className="at-card-head">
        <div>
          <h2 id="review-email-title">Evening review email</h2>
          <p>At most one daily digest between 6 and 10 pm IST</p>
        </div>
        {data && (
          <span
            className={
              data.enabled
                ? 'finna-st-pill finna-st-pill--green'
                : 'finna-st-pill finna-st-pill--gray'
            }
          >
            {data.enabled ? 'On' : 'Off'}
          </span>
        )}
      </div>

      <p className="text-xs leading-relaxed text-secondary">
        Includes your due-review count, study streak and a Smart Review link.
        Empty queues stay quiet. Unsubscribe from any email without signing in.
      </p>

      {error && (
        <div role="alert" className="at-inline-err mt-3">
          {error}{' '}
          <button
            type="button"
            onClick={() => setRetry((n) => n + 1)}
            className="underline"
          >
            Reload preferences
          </button>
        </div>
      )}
      {!data && !error && (
        <p role="status" className="mt-3 text-xs text-secondary">
          Loading email preferences…
        </p>
      )}
      {data && (
        <div className="mt-3 flex flex-col gap-2">
          <p className="text-xs text-secondary">
            Reminders: <strong className="text-ink">{data.enabled ? 'On' : 'Off'}</strong>
          </p>
          {!data.verified && (
            <p className="text-xs text-secondary">
              Verify your email in{' '}
              <Link to="/account/security" className="font-bold text-link underline">
                Account security
              </Link>{' '}
              before subscribing.
            </p>
          )}
          {!data.available && (
            <p className="text-xs text-secondary">
              Evening reminders are not available yet. You can still turn an
              existing subscription off.
            </p>
          )}
          <div className="mt-1">
            <button
              type="button"
              onClick={() => void save()}
              disabled={busy || (!data.enabled && (!data.verified || !data.available))}
              className={data.enabled ? 'finna-st-btn' : 'cr-primary-btn'}
            >
              {busy
                ? 'Saving…'
                : data.enabled
                  ? 'Turn reminders off'
                  : 'Turn evening reminders on'}
            </button>
          </div>
        </div>
      )}
      {notice && (
        <p role="status" className="finna-st-notice mt-3">
          {notice}
        </p>
      )}
    </section>
  )
}
