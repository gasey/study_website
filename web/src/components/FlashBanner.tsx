import type { ReactNode } from 'react'

export default function FlashBanner({
  kind,
  title,
  message,
  actionLabel,
  onAction,
  onDismiss,
  extra,
}: {
  kind: 'success' | 'error'
  title?: string
  message: string
  actionLabel?: string
  onAction?: () => void
  onDismiss?: () => void
  extra?: ReactNode
}) {
  const isOk = kind === 'success'
  return (
    <div
      role={isOk ? 'status' : 'alert'}
      className={'finna-flash ' + (isOk ? 'finna-flash--ok' : 'finna-flash--err')}
    >
      <div className="finna-flash-orb-wrap" aria-hidden="true">
        <span className="finna-flash-orb">
          {isOk ? (
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="9" cy="10" r="1.4" fill="currentColor" />
              <circle cx="15" cy="10" r="1.4" fill="currentColor" />
              <path
                d="M8.5 14.5c1 1.5 2.2 2.2 3.5 2.2s2.5-.7 3.5-2.2"
                stroke="currentColor"
                strokeWidth="1.9"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="9" cy="10" r="1.4" fill="currentColor" />
              <circle cx="15" cy="10" r="1.4" fill="currentColor" />
              <path
                d="M8.5 16.2c1-1.4 2.2-2.1 3.5-2.1s2.5.7 3.5 2.1"
                stroke="currentColor"
                strokeWidth="1.9"
                strokeLinecap="round"
              />
            </svg>
          )}
        </span>
        <span className="finna-flash-shadow" />
      </div>

      <div className="finna-flash-copy">
        <strong>{title || (isOk ? 'Success' : 'Something went wrong')}</strong>
        <p>{message}</p>
        {extra}
      </div>

      <div className="finna-flash-actions">
        {actionLabel && onAction && (
          <button
            type="button"
            onClick={onAction}
            className="finna-flash-btn"
          >
            {actionLabel}
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            aria-label="Dismiss message"
            onClick={onDismiss}
            className="finna-flash-x"
          >
            ×
          </button>
        )}
      </div>
    </div>
  )
}
