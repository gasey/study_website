import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { getProgress, type Progress } from '../lib/api'

/** The six area colours, in the order the design uses them in the mark.
 *  The nav shows each area's colour as a dot, so the menu doubles as the
 *  legend — that is why the dot colour and the section colour must agree. */
const AREAS = [
  { key: 'practice', cls: 'bg-practice' },
  { key: 'learn', cls: 'bg-learn' },
  { key: 'map', cls: 'bg-map' },
  { key: 'community', cls: 'bg-community' },
  { key: 'exams', cls: 'bg-exams' },
  { key: 'rewards', cls: 'bg-rewards' },
] as const

const NAV = [
  { to: '/bank', label: 'Bank', dot: 'bg-practice' },
  { to: '/exams', label: 'Exams & tools', dot: 'bg-exams' },
  { to: '/feed', label: 'Community', dot: 'bg-community' },
] as const

export function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <span className="grid grid-cols-3 gap-[2px]">
        {AREAS.map((a) => (
          <span key={a.key} className={`h-[7px] w-[7px] rounded-[2px] ${a.cls}`} />
        ))}
      </span>
      <span className="font-display text-[22px] font-semibold -tracking-[0.01em]">
        India Study Map
      </span>
    </span>
  )
}

/** Anonymous progress. Refetched on navigation, which is enough: the only
 *  thing that changes it is answering a question, and that is followed by a
 *  route change back to the bank often enough to stay honest. */
function ProgressPill() {
  const [p, setP] = useState<Progress | null>(null)
  const { pathname } = useLocation()
  useEffect(() => {
    getProgress()
      .then(setP)
      .catch(() => setP(null))
  }, [pathname])

  if (!p || p.answered === 0) return null
  const pct = Math.round((p.correct / p.answered) * 100)
  return (
    <span className="label" title={`${p.unique_questions} distinct questions`}>
      {p.answered} answered · {pct}% correct
    </span>
  )
}

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-card">
      <div className="mx-auto flex min-h-[54px] max-w-shell flex-wrap items-center gap-4 px-6 py-2">
        <NavLink to="/" className="shrink-0">
          <Logo />
        </NavLink>
        <nav className="flex flex-wrap items-center gap-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                [
                  'flex items-center gap-2 rounded-pill px-3 py-1.5 text-[14px] transition-colors',
                  isActive ? 'bg-paper text-ink' : 'text-secondary hover:bg-paper',
                ].join(' ')
              }
            >
              <span className={`h-[6px] w-[6px] rounded-full ${n.dot}`} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <span className="grow" />
        <ProgressPill />
      </div>
    </header>
  )
}
