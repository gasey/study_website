import { useEffect, useState } from 'react'

/**
 * Tracks browser connectivity via navigator.onLine + online/offline events.
 * Ported from ShikshaCom's Dashboards v2 OfflineBanner.jsx (§VII.19.8).
 */
export function useIsOffline(): boolean {
  const [offline, setOffline] = useState(
    () => typeof navigator !== 'undefined' && navigator.onLine === false,
  )
  useEffect(() => {
    const onOnline = () => setOffline(false)
    const onOffline = () => setOffline(true)
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    return () => {
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
    }
  }, [])
  return offline
}

/**
 * Honest offline status strip: only cites "Showing what was saved at …"
 * when `lastLoadedAt` records an actual successful load, never fabricating a time.
 */
export default function OfflineBanner({
  lastLoadedAt,
  onRetry,
  retrying = false,
}: {
  lastLoadedAt?: number | null
  onRetry?: () => void
  retrying?: boolean
}) {
  const offline = useIsOffline()
  if (!offline) return null

  const savedAt = lastLoadedAt
    ? ` Showing what was saved at ${new Date(lastLoadedAt).toLocaleTimeString('en-IN', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata',
      })}.`
    : ''

  return (
    <div className="finna-offline-banner" role="status">
      <span aria-hidden="true" className="finna-offline-dot" />
      <span className="min-w-0 flex-1">
        You’re offline.{savedAt} Submitting answers and syncing progress need a connection.
      </span>
      {onRetry && (
        <button
          type="button"
          className="finna-offline-retry"
          onClick={onRetry}
          disabled={retrying}
        >
          {retrying ? 'Retrying…' : 'Retry'}
        </button>
      )}
    </div>
  )
}
