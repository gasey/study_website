import { useEffect, useState } from 'react'
import { reviewRequest } from '../lib/review'

interface Session {
  id: string
  created_at: string
  expires_at: string
  current: boolean
}

export default function AccountSessions() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  async function load() {
    const r = await reviewRequest<{ items: Session[] }>('/auth/sessions')
    setSessions(r.items)
  }

  useEffect(() => {
    void load().catch((e) => setError(e.message))
  }, [])

  async function revoke(id?: string) {
    setBusy(true)
    setError('')
    try {
      await reviewRequest('/auth/sessions/revoke', { session_id: id })
      setNotice('Selected sessions have been signed out.')
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const otherCount = sessions.filter((s) => !s.current).length

  return (
    <section className="at-sessions" aria-label="Signed-in sessions">
      <div className="at-sessions-head">
        <div>
          <h3>Signed-in sessions</h3>
          <p>Review active browser sessions and sign out devices you no longer use.</p>
        </div>
        {otherCount > 0 && (
          <button
            type="button"
            disabled={busy}
            onClick={() => void revoke()}
            className="finna-st-btn"
          >
            Sign out {otherCount} other {otherCount === 1 ? 'session' : 'sessions'}
          </button>
        )}
      </div>

      {error && (
        <p role="alert" className="at-inline-err">
          {error}{' '}
          <button type="button" onClick={() => void load().catch((e) => setError(e.message))} className="underline">
            Retry
          </button>
        </p>
      )}
      {notice && (
        <p role="status" className="finna-st-notice mt-2">
          {notice}
        </p>
      )}

      <div className="at-session-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={'at-session-row' + (s.current ? ' is-current' : '')}
          >
            <span className="at-session-ico" aria-hidden="true">
              {s.current ? '●' : '○'}
            </span>
            <div className="at-session-meta">
              <div className="at-session-title">
                <strong>{s.current ? 'This session' : 'Other session'}</strong>
                {s.current && (
                  <span className="finna-st-pill finna-st-pill--green">
                    Active now
                  </span>
                )}
              </div>
              <small>
                Started {new Date(s.created_at).toLocaleString('en-IN')} · expires{' '}
                {new Date(s.expires_at).toLocaleDateString('en-IN')}
              </small>
            </div>
            {!s.current && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void revoke(s.id)}
                className="finna-st-btn"
              >
                Sign out
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
