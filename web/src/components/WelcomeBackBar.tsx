import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const LAST_VISIT_KEY = 'finna.welcomeback.last_visit_ms'
const RECORD_KEY = 'finna.welcomeback.record'
const DAY_MS = 24 * 60 * 60 * 1000
const ABSENCE_THRESHOLD_DAYS = 45
const FULL_REFRESHER_DAYS = 120
const AUTO_EXPIRE_MS = 7 * DAY_MS
const COOLDOWN_MS = 45 * DAY_MS

interface WelcomeRecord {
  firstShownAt?: number
  suppressedUntil?: number
}

function readRecord(): WelcomeRecord | null {
  try {
    const raw = localStorage.getItem(RECORD_KEY)
    return raw ? (JSON.parse(raw) as WelcomeRecord) : null
  } catch {
    return null
  }
}

function writeRecord(record: WelcomeRecord) {
  try {
    localStorage.setItem(RECORD_KEY, JSON.stringify(record))
  } catch {
    // Private browsing or storage quota — fail open
  }
}

/**
 * Non-modal inline Welcome-Back refresher bar for long-absent learners (≥45 days).
 * Ported from ShikshaCom's shared/src/tour/WelcomeBackBar.jsx (§VII.19.3).
 * Never shows as a modal; auto-expires after 7 days; cools down for 45 days on dismiss.
 */
export default function WelcomeBackBar({
  resumeUrl,
}: {
  resumeUrl?: string | null
}) {
  const [mountTime] = useState(() => Date.now())
  const [absenceDays] = useState<number>(() => {
    try {
      const prev = Number(localStorage.getItem(LAST_VISIT_KEY) || 0)
      localStorage.setItem(LAST_VISIT_KEY, String(Date.now()))
      if (!prev || Number.isNaN(prev)) return 0
      return Math.floor((Date.now() - prev) / DAY_MS)
    } catch {
      return 0
    }
  })
  const [, bump] = useState(0)

  const record = readRecord()
  const eligible = absenceDays >= ABSENCE_THRESHOLD_DAYS
  const suppressedByCooldown = !!(
    record?.suppressedUntil && mountTime < record.suppressedUntil
  )
  const expired = !!(
    record?.firstShownAt &&
    !record?.suppressedUntil &&
    mountTime - record.firstShownAt > AUTO_EXPIRE_MS
  )

  useEffect(() => {
    if (!eligible) return
    if (!record?.firstShownAt) {
      writeRecord({ firstShownAt: mountTime })
    } else if (expired) {
      writeRecord({
        firstShownAt: record.firstShownAt,
        suppressedUntil: mountTime + COOLDOWN_MS,
      })
    }
  }, [eligible, expired, record?.firstShownAt, mountTime])

  if (!eligible || suppressedByCooldown || expired) return null

  const dismiss = () => {
    writeRecord({
      firstShownAt: mountTime,
      suppressedUntil: mountTime + COOLDOWN_MS,
    })
    bump((n) => n + 1)
  }

  const fullRefresher = absenceDays >= FULL_REFRESHER_DAYS

  return (
    <div className="finna-welcomeback" role="status">
      <div className="min-w-0 flex-1">
        <strong>Welcome back</strong>
        <p>
          {fullRefresher
            ? 'It’s been a while — want a quick tour of what’s new or jump straight back into practice?'
            : 'A few things have been streamlined since your last visit — want a 60-second refresher?'}
        </p>
      </div>
      <div className="finna-welcomeback-actions">
        <Link
          to={resumeUrl || '/guides/using-finna'}
          className="finna-btn"
          onClick={dismiss}
        >
          {resumeUrl ? 'Resume study' : 'Show me around'}
        </Link>
        <button
          type="button"
          className="finna-btn finna-btn-quiet"
          onClick={dismiss}
        >
          No thanks
        </button>
      </div>
    </div>
  )
}
