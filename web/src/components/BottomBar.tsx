import { NavLink, useLocation } from 'react-router-dom'

/** Mobile bottom tab bar, from `India Study Map Mobile.dc.html`.
 *  Home / Bank / Desk / Exams / Me, with the handoff's 44px minimum hit
 *  target. Hidden from `sm` up, where the header's nav takes over.
 *
 *  Hidden entirely during a mock: a timed paper is full-attention, and the
 *  prototype's exam screen has no bottom bar either. Tapping "Home"
 *  mid-paper would abandon an attempt the server still has open. */
const TABS = [
  { to: '/feed', label: 'Home', dot: 'bg-community' },
  { to: '/bank', label: 'Bank', dot: 'bg-practice' },
  { to: '/desk', label: 'Desk', dot: 'bg-learn' },
  { to: '/exams', label: 'Exams', dot: 'bg-exams' },
  { to: '/mistakes', label: 'Me', dot: 'bg-rewards' },
]

export default function BottomBar() {
  const { pathname } = useLocation()
  if (/^\/exams\/[^/]+\/mock$/.test(pathname)) return null

  return (
    <nav
      aria-label="Sections"
      className="sticky bottom-0 z-40 border-t border-hairline bg-card sm:hidden"
    >
      <div className="mx-auto flex max-w-shell">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) =>
              [
                'flex min-h-[52px] flex-1 flex-col items-center justify-center gap-1 py-1.5 text-[11px]',
                isActive ? 'text-ink' : 'text-muted',
              ].join(' ')
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`h-[7px] w-[7px] rounded-full ${t.dot} ${isActive ? '' : 'opacity-35'}`}
                />
                {t.label}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
