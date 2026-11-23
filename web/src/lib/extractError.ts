/**
 * Normalise API / proxy error payloads into a short, human-safe string.
 *
 * Ported from ShikshaCom's shared/extractError.js (§VII.19.2):
 * A 5xx from Caddy or FastAPI can return an HTML error document or an
 * oversized stack dump. Rejecting anything that starts with `<` or exceeds
 * 300 characters guarantees raw markup never leaks into learner alerts.
 */
const MAX_MESSAGE_LENGTH = 300

export function usableErrorMessage(raw: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (typeof raw !== 'string') return fallback
  const trimmed = raw.trim()
  if (!trimmed) return fallback
  if (trimmed.startsWith('<')) return fallback
  if (trimmed.length > MAX_MESSAGE_LENGTH) return fallback
  return trimmed
}

export function extractApiError(payload: unknown, statusText?: string, fallback = 'Something went wrong. Please try again.'): string {
  if (typeof payload === 'string') {
    return usableErrorMessage(payload, usableErrorMessage(statusText, fallback))
  }
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>
    if (typeof obj.detail === 'string') {
      return usableErrorMessage(obj.detail, fallback)
    }
    if (typeof obj.message === 'string') {
      return usableErrorMessage(obj.message, fallback)
    }
    for (const key of Object.keys(obj)) {
      if (key === 'code') continue
      const val = obj[key]
      if (Array.isArray(val) && typeof val[0] === 'string') {
        const msg = usableErrorMessage(val[0], '')
        if (msg) return msg
      }
      if (typeof val === 'string') {
        const msg = usableErrorMessage(val, '')
        if (msg) return msg
      }
    }
  }
  return usableErrorMessage(statusText, fallback)
}
