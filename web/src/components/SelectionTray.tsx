import { Link, useLocation } from 'react-router-dom'
import { useSelectionTray } from '../lib/selectionTray'

/** Floating site-wide selection tray (§VII.10.2). Survives navigation across
 *  `/bank`, `/exams/:id`, `/past-papers`, `/library/*` and `/guides/*`. */
export default function SelectionTray() {
  const { ids, clear, buildHref, limit } = useSelectionTray()
  const { pathname } = useLocation()
  if (!ids.length || pathname === '/practice/build' || pathname.startsWith('/admin')) return null
  return (
    <aside
      aria-label="Selected questions for test builder"
      className="fixed bottom-16 left-1/2 z-40 flex w-[min(640px,calc(100%-24px))] -translate-x-1/2 flex-wrap items-center justify-between gap-3 rounded-xl border border-ink bg-ink px-4 py-3 text-paper md:bottom-5"
    >
      <span className="font-mono text-sm font-semibold">
        {ids.length}/{limit} selected
      </span>
      <div className="flex flex-wrap items-center gap-2">
        <Link
          to={buildHref}
          className="inline-flex min-h-11 items-center rounded-lg bg-[#FFC83D] px-4 py-2 text-sm font-bold text-[#0E1330]"
        >
          Make a test from these ({ids.length})
        </Link>
        <button
          type="button"
          onClick={clear}
          className="inline-flex min-h-11 items-center rounded-lg border border-paper/30 px-3 py-2 text-sm font-semibold text-paper"
        >
          Clear
        </button>
      </div>
    </aside>
  )
}
