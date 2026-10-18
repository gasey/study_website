import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { getProgress, type Progress } from '../lib/api'
import { Avatar, CountBadge, GroupTitle, PillButton } from './ui'

/** App shell header, ported from markup line 34.
 *
 *  Note for anyone comparing against an earlier version: the six coloured
 *  area dots are NOT in the header. They appear in the landing hero and the
 *  footer mark. They were invented here once; don't put them back. */

const QUICK_NAV = [
  { to: '/bank', label: 'Bank' },
  { to: '/exams', label: 'Exams' },
  { to: '/news', label: 'News' },
  { to: '/desk', label: 'Study desk' },
  { to: '/games', label: 'Games' },
]

/** The mega-menu's columns. Items carry an optional badge and a one-line
 *  description, per markup line 61. Routes that do not exist yet fall
 *  through to the Placeholder screen, which is honest about it. */
const MENU: {
  title: string
  items: { to: string; title: string; tag: string; badge?: string; badgeBg?: string }[]
}[] = [
  {
    title: 'Practice',
    items: [
      { to: '/bank', title: 'Question bank', tag: '77,751 questions from 1,938 papers' },
      { to: '/exams', title: 'Exams & tools', tag: 'Saved sets over the bank' },
      { to: '/mistakes', title: 'Mistakes', tag: 'What you got wrong, grouped' },
    ],
  },
  {
    title: 'Compete',
    items: [
      { to: '/games', title: 'Games', tag: 'Gauntlet, speed round, Locate', badge: 'Soon', badgeBg: 'bg-practice' },
      { to: '/duel', title: 'Duel', tag: '1v1 challenge', badge: 'Soon', badgeBg: 'bg-practice' },
      { to: '/board', title: 'Leaderboard', tag: 'Weekly cup placings', badge: 'Soon', badgeBg: 'bg-rewards' },
    ],
  },
  {
    title: 'Community',
    items: [
      { to: '/feed', title: 'Feed', tag: 'Doubts, materials, challenges', badge: 'Soon', badgeBg: 'bg-community' },
      { to: '/desk', title: 'Study desks', tag: 'Group and class spaces', badge: 'Soon', badgeBg: 'bg-community' },
      { to: '/create', title: 'Create', tag: 'Notes, flashcards, mocks', badge: 'Soon', badgeBg: 'bg-learn' },
    ],
  },
  {
    title: 'You',
    items: [
      { to: '/profile', title: 'Profile', tag: 'Your materials and progress', badge: 'Soon', badgeBg: 'bg-exams' },
      { to: '/calendar', title: 'Exam calendar', tag: 'MPSC dates, mock openings', badge: 'Soon', badgeBg: 'bg-exams' },
      { to: '/scoring', title: 'How scoring works', tag: 'XP, negative marking' },
    ],
  },
]

function ProgressPill() {
  const [p, setP] = useState<Progress | null>(null)
  const { pathname } = useLocation()
  useEffect(() => {
    getProgress()
      .then(setP)
      .catch(() => setP(null))
  }, [pathname])
  if (!p || p.answered === 0) return null
  return (
    <span className="whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.08em] text-muted">
      {p.answered} answered · {Math.round((p.correct / p.answered) * 100)}%
    </span>
  )
}

export default function Header() {
  const [menu, setMenu] = useState(false)
  const [query, setQuery] = useState('')
  const nav = useNavigate()
  const { pathname } = useLocation()
  const ref = useRef<HTMLElement>(null)

  useEffect(() => setMenu(false), [pathname])

  // Dismiss on outside click and on Escape — a full-width overlay that only
  // closes via its own button is a trap.
  useEffect(() => {
    if (!menu) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setMenu(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenu(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [menu])

  return (
    <header
      ref={ref}
      className="sticky top-0 z-50 border-b border-hairline bg-card"
    >
      <div className="mx-auto flex min-h-[54px] max-w-shell flex-wrap items-center gap-3 px-6 py-2">
        <NavLink
          to="/bank"
          className="whitespace-nowrap font-display text-[22px] font-semibold -tracking-[0.01em]"
        >
          India Study Map
        </NavLink>

        <nav className="flex flex-wrap items-center gap-0.5">
          <button
            onClick={() => setMenu((m) => !m)}
            aria-expanded={menu}
            className={`whitespace-nowrap rounded-pill border border-ink px-3 py-2 text-[14px] font-semibold ${
              menu ? 'bg-ink text-paper' : 'bg-transparent text-ink'
            }`}
          >
            Sections ▾
          </button>
          {QUICK_NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                [
                  'hidden whitespace-nowrap px-3 py-2 text-[14px] font-medium sm:block',
                  isActive
                    ? 'text-ink underline decoration-2 underline-offset-[6px]'
                    : 'text-secondary',
                ].join(' ')
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="min-w-0 flex-1" />

        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (query.trim().length >= 2) nav(`/bank?q=${encodeURIComponent(query.trim())}`)
          }}
          className="hidden md:block"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search questions, people, notes"
            aria-label="Search"
            className="h-9 w-[260px] min-w-[140px] rounded-pill border border-hairline bg-[#F7F3EA] px-3 text-[13px] text-ink outline-none placeholder:text-placeholder"
          />
        </form>

        <ProgressPill />

        <NavLink
          to="/inbox"
          className="hidden items-center gap-1.5 px-1.5 py-2 text-[14px] font-medium md:flex"
        >
          Inbox <CountBadge>0</CountBadge>
        </NavLink>

        <PillButton onClick={() => nav('/create')}>Post</PillButton>

        <NavLink to="/profile" className="flex items-center">
          <Avatar initials="VH" />
          <span className="-ml-3.5 rounded-pill bg-rewards-dark px-1.5 py-px font-mono text-[10px] font-medium text-white">
            L1
          </span>
        </NavLink>
      </div>

      {menu && (
        <div className="absolute inset-x-0 top-full border-b border-hairline bg-card shadow-[0_18px_40px_rgba(29,27,24,.12)]">
          <div className="mx-auto grid max-w-shell gap-x-10 gap-y-7 px-6 pb-8 pt-7 [grid-template-columns:repeat(auto-fit,minmax(240px,1fr))]">
            {MENU.map((col) => (
              <div key={col.title}>
                <GroupTitle>{col.title}</GroupTitle>
                {col.items.map((it) => (
                  <NavLink key={it.to + it.title} to={it.to} className="block py-2">
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1 font-display text-[18px] font-medium">
                      {it.title}
                      {it.badge && (
                        <span
                          className={`shrink-0 whitespace-nowrap rounded-pill px-[7px] py-[2px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-[#FBF8F1] ${it.badgeBg}`}
                        >
                          {it.badge}
                        </span>
                      )}
                    </span>
                    <span className="mt-0.5 block text-[13px] text-muted [text-wrap:pretty]">
                      {it.tag}
                    </span>
                  </NavLink>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}
