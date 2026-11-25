import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  getAccountSession,
  getProgressSummary,
  listCollections,
  logoutAccount,
  isLaterExamCollection,
  isSubjectModule,
  moduleHref,
  type AccountSession,
  type Collection,
} from '../lib/api'
import { reviewRequest, reviewSession } from '../lib/review'
import { reviewDestinations, type ReviewAccess } from '../lib/reviewNavigation'
import { useExamScope } from '../lib/examScope'
import { focusedSession, mobileTitle } from '../lib/navigation'
import {
  destinationPath,
  destinationsForSurface,
  menuFor,
  type Destination,
  type NavMenu,
} from '../lib/siteMap'
import { useStudyTheme } from '../lib/theme'
import { usePreferredExam } from '../lib/preferredExam'
import { resolveTrackedExams, shortExamLabel, useTrackedExamIds } from '../lib/trackedExams'
import { FLAGSHIP_EXAM_IDS } from '../lib/examPresentation'
import { Avatar } from './ui'
import AvatarArt, { DEFAULT_HERO_LOOK } from './AvatarArt'
import QuickFind from './QuickFind'
import NavIcon from './NavIcon'
import BrowseAllowance from './BrowseAllowance'
import VaultSafeIllustration from './VaultSafeIllustration'
import { readLocalVault } from '../lib/vault'

const NAV_ITEMS = destinationsForSurface('nav')
const HOME_PATH = destinationPath('home')
const INBOX_PATH = destinationPath('inbox')
const PROFILE_PATH = destinationPath('profile')
const CREATE_PATH = destinationPath('create')
const INDEX_PATH = destinationPath('index')
const EXAMS_PATH = destinationPath('exams')
const LIBRARY_PATH = destinationPath('library')
const MENUS: Record<string, Destination[]> = Object.fromEntries(
  NAV_ITEMS.filter((i) => i.menu).map((i) => [i.id, menuFor(i.menu as NavMenu)]),
)

type MenuTone = 'cobalt' | 'teal' | 'amber' | 'emerald' | 'violet' | 'rose'
const MENU_CARD_META: Record<string, { tone: MenuTone; tag: string; icon: string }> = {
  papers: { tone: 'cobalt', tag: 'Archive', icon: 'M7 3h8l4 4v14H7V3Zm7 1v4h4M10 12h6M10 16h6' },
  calendar: { tone: 'amber', tag: 'Schedule', icon: 'M4 7h16v13H4V7Zm3-4v4m10-4v4M4 11h16' },
  'subject-books': { tone: 'teal', tag: 'All-Exam', icon: 'M4 5h5v14H4V5Zm6 0h5v14h-5V5Zm6 1 4 13' },
  'subject-gk-gs': { tone: 'cobalt', tag: 'Volume I', icon: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-9 9h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18' },
  'subject-english': { tone: 'teal', tag: 'Volume II', icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z' },
  'subject-mathematics': { tone: 'amber', tag: 'Volume III', icon: 'M4 6h16M4 12h16M4 18h10M16 15l4 4m0-4-4 4' },
  'subject-reasoning': { tone: 'violet', tag: 'Volume IV', icon: 'M9 3H5v4h4V3Zm10 0h-4v4h4V3ZM9 17H5v4h4v-4Zm6-7h4v4h-4v-4ZM9 5h6M7 7v10m8-7-6 7' },
  'subject-mizo': { tone: 'emerald', tag: 'Volume V', icon: 'M4 19h16M6 15l6-11 6 11M8.5 11h7' },
  revise: { tone: 'teal', tag: 'Memory', icon: 'M4 12a8 8 0 0 1 13.7-5.6L20 8.5M20 4v4.5h-4.5M20 12a8 8 0 0 1-13.7 5.6L4 15.5M4 20v-4.5h4.5' },
  'practice-build': { tone: 'cobalt', tag: 'Custom', icon: 'M12 5v14M5 12h14' },
  tests: { tone: 'amber', tag: 'Timed', icon: 'M12 7v5l3 2M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z' },
  quest: { tone: 'rose', tag: '16-Bit RPG', icon: 'M14.5 17.5 3 6V3h3l11.5 11.5M13 19l6-6m-3 3 4 4m-1 1 2-2' },
  games: { tone: 'violet', tag: 'Arcade', icon: 'M6 12h4M8 10v4m7-2h.01M18 10h.01M5 7h14a3 3 0 0 1 3 3v4a4 4 0 0 1-4 4h-2l-2-2h-4l-2 2H6a4 4 0 0 1-4-4v-4a3 3 0 0 1 3-3Z' },
  'games-daily': { tone: 'amber', tag: 'Daily 5', icon: 'M12 3v3m0 12v3M4.9 4.9l2.1 2.1m10 10 2.1 2.1M3 12h3m12 0h3M4.9 19.1 7 17m10-10 2.1-2.1M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z' },
  'games-cup': { tone: 'cobalt', tag: 'Weekend', icon: 'M6 4h12v4a6 6 0 0 1-12 0V4ZM6 6H3v2a3 3 0 0 0 3 3m12-5h3v2a3 3 0 0 1-3 3M12 14v5m-4 0h8' },
  'games-duel': { tone: 'teal', tag: '1v1 Live', icon: 'M8 12h8M12 8v8M5 6h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z' },
  'games-speed': { tone: 'violet', tag: '60s Blitz', icon: 'M13 2 4 14h7l-1 8 9-12h-7l1-8Z' },
  'games-standings': { tone: 'emerald', tag: 'Ranks', icon: 'M5 19V11m7 8V5m7 14v-7' },
  bank: { tone: 'emerald', tag: 'Full Bank', icon: 'M4 6h16M4 12h16M4 18h16' },
  atlas: { tone: 'emerald', tag: 'Maps', icon: 'M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6Zm6-2v14m6-12v14' },
  chronicle: { tone: 'rose', tag: 'Timeline', icon: 'M12 4v16M8 8h8M6 14h12M9 19h6' },
  stats: { tone: 'cobalt', tag: 'Rankings', icon: 'M5 19V11m7 8V5m7 14v-7' },
  desk: { tone: 'amber', tag: 'Workspace', icon: 'M3 10h18M5 10V7h14v3M6 10v11M18 10v11M9 17h6' },
}

/** Streamlined 2-row student-loop desktop header + phone bar.
 *  Row 1: Brand · Search (Ctrl K) · Streak · Vault · Create · Utilities · Account
 *  Row 2: Home · Exams ▾ · Subjects ▾ · Practice ▾ · Tools & Guides ▾ · Community ▾  |  Revise · Desk · My exams */
export default function Header() {
  const { pathname, search } = useLocation()
  const navigate = useNavigate()
  const scope = useExamScope()
  const [theme, setTheme] = useStudyTheme()
  const [access, setAccess] = useState<ReviewAccess>({ grants: [], assigned: false })
  const [account, setAccount] = useState<AccountSession>({ authenticated: false })
  const [unread, setUnread] = useState<number | null>(null)
  const [streak, setStreak] = useState<number | null>(null)
  const [exams, setExams] = useState<Collection[]>([])
  const [subjectModules, setSubjectModules] = useState<Collection[]>([])
  const [menu, setMenu] = useState<string | null>(null)
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const [vaultCount, setVaultCount] = useState<number>(() => readLocalVault().length)
  const [vaultHover, setVaultHover] = useState(false)
  const selected = usePreferredExam(exams)
  const trackedIds = useTrackedExamIds()
  const trackedExams = useMemo(
    () => resolveTrackedExams(exams, trackedIds, selected),
    [exams, trackedIds, selected],
  )

  const quickJumpExams = useMemo(() => {
    const out: Collection[] = []
    const seen = new Set<string>()
    for (const e of trackedExams) {
      if (!seen.has(e.id)) {
        out.push(e)
        seen.add(e.id)
      }
    }
    for (const id of FLAGSHIP_EXAM_IDS) {
      if (out.length >= 7) break
      if (seen.has(id)) continue
      const match = exams.find((e) => e.id === id)
      if (match) {
        out.push(match)
        seen.add(match.id)
      }
    }
    return out
  }, [trackedExams, exams])

  useEffect(() => {
    const syncVault = () => setVaultCount(readLocalVault().length)
    window.addEventListener('finna-vault-change', syncVault)
    return () => window.removeEventListener('finna-vault-change', syncVault)
  }, [])

  const shell = useRef<HTMLElement>(null)
  const menuPanel = useRef<HTMLDivElement>(null)
  const accountWrap = useRef<HTMLDivElement>(null)
  const accountBtn = useRef<HTMLButtonElement>(null)
  const triggers = useRef<Record<string, HTMLElement | null>>({})
  const openTimer = useRef<number | null>(null)
  const closeTimer = useRef<number | null>(null)

  const cancelTimers = () => {
    if (openTimer.current !== null) {
      window.clearTimeout(openTimer.current)
      openTimer.current = null
    }
    if (closeTimer.current !== null) {
      window.clearTimeout(closeTimer.current)
      closeTimer.current = null
    }
  }

  const scheduleOpen = (id: string) => {
    cancelTimers()
    if (menu === id) return
    openTimer.current = window.setTimeout(() => {
      openTimer.current = null
      setMenu(id)
    }, menu ? 40 : 90)
  }

  const scheduleClose = () => {
    cancelTimers()
    closeTimer.current = window.setTimeout(() => {
      closeTimer.current = null
      setMenu(null)
    }, 180)
  }

  useEffect(() => () => cancelTimers(), [])

  useEffect(() => {
    let live = true
    let version = 0
    let lastFocusRefresh = 0
    const load = (reset = false) => {
      const run = ++version
      if (reset) {
        setUnread(null)
        setStreak(null)
        setAccess({ grants: [], assigned: false })
        setAccount({ authenticated: false })
      }
      getProgressSummary()
        .then((p) => {
          if (live && run === version) setStreak(p.current_streak)
        })
        .catch(() => {})
      getAccountSession()
        .then(async (a) => {
          if (!live || run !== version) return
          setAccount(a)
          if (!a.authenticated) {
            setUnread(null)
            setAccess({ grants: [], assigned: false })
            return
          }
          const s = await reviewSession()
          if (!live || run !== version) return
          setAccess({
            grants: s.grants,
            assigned: s.grants.length
              ? false
              : (
                  await reviewRequest<{ items: { state: string }[] }>('/editorial/assignments')
                ).items.some((x) => x.state === 'active' || x.state === 'pending'),
          })
          reviewRequest<{ unread: number }>('/inbox/unread')
            .then((r) => {
              if (live && run === version) setUnread(r.unread)
            })
            .catch(() => {})
        })
        .catch(() => {})
    }
    const onAuthChange = () => load(true)
    const onSoftRefresh = () => load(false)
    const onFocus = () => {
      const now = Date.now()
      if (now - lastFocusRefresh < 45_000) return
      lastFocusRefresh = now
      load(false)
    }
    load(false)
    window.addEventListener('ism-auth-change', onAuthChange)
    window.addEventListener('ism-avatar-change', onSoftRefresh)
    window.addEventListener('ism-notifications-change', onSoftRefresh)
    window.addEventListener('focus', onFocus)
    return () => {
      live = false
      window.removeEventListener('ism-auth-change', onAuthChange)
      window.removeEventListener('ism-avatar-change', onSoftRefresh)
      window.removeEventListener('ism-notifications-change', onSoftRefresh)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  useEffect(() => {
    let live = true
    setExams([])
    setSubjectModules([])
    listCollections()
      .then((rows) => {
        if (!live) return
        setExams(rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)))
        setSubjectModules(rows.filter(isSubjectModule))
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [scope])

  useEffect(() => {
    cancelTimers()
    setMenu(null)
    setAccountMenuOpen(false)
  }, [pathname, search])

  useEffect(() => {
    if (!accountMenuOpen) return
    const onPointerDown = (e: PointerEvent) => {
      if (!accountWrap.current?.contains(e.target as Node)) {
        setAccountMenuOpen(false)
      }
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        setAccountMenuOpen(false)
        accountBtn.current?.focus()
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [accountMenuOpen])

  useEffect(() => {
    if (!menu) return
    const onPointerDown = (e: PointerEvent) => {
      if (!shell.current?.contains(e.target as Node)) {
        cancelTimers()
        setMenu(null)
      }
    }
    const onFocusIn = (e: FocusEvent) => {
      if (e.target instanceof Node && !shell.current?.contains(e.target)) {
        cancelTimers()
        setMenu(null)
      }
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        cancelTimers()
        const prev = menu
        setMenu(null)
        triggers.current[prev]?.focus()
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('focusin', onFocusIn)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('focusin', onFocusIn)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [menu])

  const openMenuAndFocusFirst = (id: string) => {
    cancelTimers()
    setMenu(id)
    requestAnimationFrame(() => {
      menuPanel.current?.querySelector<HTMLAnchorElement>('a')?.focus()
    })
  }

  const onMenuKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp' && e.key !== 'Home' && e.key !== 'End') return
    const links = Array.from(menuPanel.current?.querySelectorAll<HTMLAnchorElement>('a') || [])
    if (!links.length) return
    e.preventDefault()
    if (e.key === 'Home') {
      links[0]?.focus()
      return
    }
    if (e.key === 'End') {
      links[links.length - 1]?.focus()
      return
    }
    const idx = links.indexOf(document.activeElement as HTMLAnchorElement)
    const nextIdx =
      e.key === 'ArrowDown'
        ? (idx + 1) % links.length
        : (idx - 1 + links.length) % links.length
    links[nextIdx]?.focus()
  }

  const closeMenu = () => {
    cancelTimers()
    setMenu(null)
    setAccountMenuOpen(false)
  }

  async function handleLogout() {
    if (signingOut) return
    setSigningOut(true)
    try {
      await logoutAccount()
      setAccountMenuOpen(false)
      window.dispatchEvent(new Event('ism-auth-change'))
      window.location.assign('/home')
    } catch {
      setSigningOut(false)
    }
  }

  const focused = focusedSession(pathname, search)
  const openFind = () => window.dispatchEvent(new Event('finna-open-find'))
  const openHelp = () => window.dispatchEvent(new Event('finna-open-help'))

  const active = (id: string) =>
    id === 'home'
      ? pathname === '/home' || pathname === '/'
      : id === 'exams'
        ? /^\/(exams|group-b|past-papers|calendar)(\/|$)/.test(pathname)
        : id === 'library'
          ? /^\/(library|subjects|english|arithmetic|mizo)(\/|$)/.test(pathname)
          : id === 'practice'
            ? /^\/(practice|bank|tests|revise|vault|results)(\/|$)/.test(pathname)
            : id === 'games'
              ? /^\/(games|profile\/rewards)(\/|$)/.test(pathname)
              : id === 'guides'
                ? /^\/(guides|atlas|chronicle|stats|desk|index)(\/|$)/.test(pathname)
                : /^\/(community|creators|materials|create)(\/|$)/.test(pathname)

  const staff = reviewDestinations(access)
  const activeNavParent = menu ? NAV_ITEMS.find((i) => i.id === menu) || null : null
  const activeMenuItems = menu ? MENUS[menu] || [] : []

  return (
    <header ref={shell} data-app-header className={'finna-shell' + (focused ? ' finna-focused' : '')}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-[80] focus:rounded-lg focus:bg-card focus:p-3 focus:text-ink"
      >
        Skip to content
      </a>

      {/* Compact Phone Header */}
      {!focused && (
        <div className="finna-phone-header">
          <div className="finna-phone-heading">
            {pathname !== HOME_PATH && (
              <button
                type="button"
                onClick={() => {
                  const canStepBack =
                    typeof window !== 'undefined' &&
                    window.history.state &&
                    typeof window.history.state.idx === 'number' &&
                    window.history.state.idx > 0
                  if (canStepBack) {
                    navigate(-1)
                    return
                  }
                  navigate(
                    /^\/(bank|exams)\//.test(pathname)
                      ? EXAMS_PATH
                      : pathname.startsWith('/library/') || pathname.startsWith('/subjects/')
                        ? LIBRARY_PATH
                        : pathname.startsWith('/games/')
                          ? '/games'
                          : HOME_PATH,
                  )
                }}
                aria-label="Go back"
                className="finna-phone-back"
              >
                ‹
              </button>
            )}
            <h1>{mobileTitle(pathname)}</h1>
          </div>
          <nav aria-label="Phone quick actions">
            {pathname === HOME_PATH && streak !== null && streak > 0 && (
              <Link to={PROFILE_PATH} className="finna-phone-streak">
                ★ {streak}d
              </Link>
            )}
            <button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog">
              <NavIcon name="search" />
            </button>
            <button
              type="button"
              onClick={() => setTheme(theme === 'night' ? 'paper' : 'night')}
              aria-label={`Switch to ${theme === 'night' ? 'light' : 'dark'} theme`}
            >
              {theme === 'night' ? '☀' : '☾'}
            </button>
            <Link to={INBOX_PATH} aria-label={unread ? 'Inbox, ' + unread + ' unread' : 'Inbox'}>
              <span aria-hidden="true">✉</span>
              {unread !== null && unread > 0 && (
                <span className="finna-phone-unread">{unread > 99 ? '99+' : unread}</span>
              )}
            </Link>
            <Link to={INDEX_PATH} aria-label="All pages and appearance">
              <NavIcon name="more" />
            </Link>
          </nav>
        </div>
      )}

      {/* Row 1: Brand + Search + Unified Utilities & Account (slimmer 2-row desktop header) */}
      <div className="finna-brand-row">
        <div className="finna-wrap finna-brand-inner">
          <Link to={HOME_PATH} className="finna-brand" aria-label="Finna home" onClick={closeMenu}>
            <span className="finna-brand-word">
              Finna<i>.</i>
            </span>
            <small className="finna-brand-tag">MPSC Study</small>
          </Link>

          {!focused && (
            <button
              type="button"
              className="finna-search-trigger"
              onClick={() => {
                closeMenu()
                openFind()
              }}
              aria-label="Quick find"
              aria-haspopup="dialog"
            >
              <NavIcon name="search" />
              <span>Find an exam, subject, question or guide</span>
              <kbd>Ctrl K</kbd>
            </button>
          )}

          <div className="finna-mobile-tools">
            {!focused && (
              <>
                <button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog">
                  <NavIcon name="search" />
                </button>
                <button
                  type="button"
                  aria-label={`Switch to ${theme === 'night' ? 'light' : 'dark'} theme`}
                  onClick={() => setTheme(theme === 'night' ? 'paper' : 'night')}
                >
                  {theme === 'night' ? '☀' : '☾'}
                </button>
              </>
            )}
          </div>

          {!focused && (
            <div className="finna-brand-utils">
              {streak !== null && streak > 0 && (
                <Link
                  to={PROFILE_PATH}
                  className="finna-streak-badge"
                  onClick={closeMenu}
                  title={`${streak}-day study streak`}
                >
                  ★ {streak}d
                </Link>
              )}

              <Link
                to="/vault"
                className="vs-header-pill"
                onClick={closeMenu}
                onMouseEnter={() => setVaultHover(true)}
                onMouseLeave={() => setVaultHover(false)}
                aria-label="My Personal Question Vault"
              >
                <VaultSafeIllustration
                  size="mini"
                  isOpen={vaultHover || pathname.startsWith('/vault')}
                  interactive={false}
                />
                <span>Vault</span>
                {vaultCount > 0 && <span className="vs-header-count">{vaultCount}</span>}
              </Link>

              <Link to={CREATE_PATH} className="finna-create" onClick={closeMenu}>
                Create
              </Link>

              <div className="finna-util-group" aria-label="Utilities">
                {account.authenticated && (
                  <Link
                    to={INBOX_PATH}
                    className="finna-util-btn"
                    onClick={closeMenu}
                    aria-label={unread ? `Inbox, ${unread} unread` : 'Inbox'}
                    title="Inbox"
                  >
                    <span aria-hidden="true">✉</span>
                    {unread !== null && unread > 0 && (
                      <span className="finna-util-badge">{unread > 99 ? '99+' : unread}</span>
                    )}
                  </Link>
                )}
                <button
                  type="button"
                  className="finna-util-btn"
                  onClick={() => setTheme(theme === 'night' ? 'paper' : 'night')}
                  aria-label={`Switch to ${theme === 'night' ? 'light' : 'dark'} theme`}
                  title={theme === 'night' ? 'Switch to light theme' : 'Switch to dark theme'}
                >
                  {theme === 'night' ? '☀' : '☾'}
                </button>
                <button
                  type="button"
                  className="finna-util-btn"
                  onClick={openHelp}
                  aria-label="Help and keyboard shortcuts"
                  title="Help & shortcuts (?)"
                >
                  ?
                </button>
              </div>

              {staff.length > 0 && (
                <nav aria-label="Staff workspaces" className="finna-staff-links">
                  {staff.slice(0, 2).map((link) => (
                    <Link key={link.to} to={link.to} className="finna-staff-pill" onClick={closeMenu}>
                      {link.label}
                    </Link>
                  ))}
                </nav>
              )}
            </div>
          )}

          {focused && (
            <Link to={HOME_PATH} className="ml-auto text-sm font-semibold text-link">
              Home →
            </Link>
          )}

          {account.authenticated ? (
            <div ref={accountWrap} className="finna-account-wrap">
              <button
                ref={accountBtn}
                type="button"
                className={'finna-account finna-account--avatar' + (accountMenuOpen ? ' is-open' : '')}
                aria-label="Account menu"
                aria-haspopup="menu"
                aria-expanded={accountMenuOpen}
                onClick={() => {
                  cancelTimers()
                  setMenu(null)
                  setAccountMenuOpen((open) => !open)
                }}
              >
                <Avatar
                  look={account.avatar}
                  initials={account.email?.slice(0, 2).toUpperCase() || 'Me'}
                />
                <svg
                  className="finna-account-caret"
                  width="12"
                  height="12"
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M4 6l4 4 4-4" />
                </svg>
              </button>

              {accountMenuOpen && (
                <div className="finna-account-menu" role="menu" aria-label="Account shortcuts">
                  <div className="finna-account-head">
                    <div className="finna-account-sprite-box" aria-hidden="true">
                      <AvatarArt
                        look={account.avatar || DEFAULT_HERO_LOOK}
                        size={44}
                        variant="sprite"
                        pose="idle"
                        facing="down"
                        animate
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-bold text-ink">
                        {account.email || 'Signed in'}
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-1.5">
                        <span className="finna-acc-chip">
                          {account.plan_status === 'active' || account.plan_code === 'pro'
                            ? '★ Pro'
                            : account.plan_status === 'trialing'
                              ? 'Trial'
                              : 'Free'}
                        </span>
                        {streak !== null && streak > 0 && (
                          <span className="finna-acc-chip is-streak">🔥 {streak}d</span>
                        )}
                        {selected && (
                          <span className="finna-acc-chip">{shortExamLabel(selected)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="finna-account-section">
                    <Link to={PROFILE_PATH} role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">👤</span>
                      <span>My Profile &amp; Progress</span>
                    </Link>
                    <Link to="/profile/avatar" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">👾</span>
                      <span>Edit Pixel RPG Sprite</span>
                    </Link>
                    <Link to="/profile/rewards" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">🏆</span>
                      <span>Quests, XP &amp; Rewards</span>
                    </Link>
                    <Link to="/vault" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">🔐</span>
                      <span>Personal Vault</span>
                      {vaultCount > 0 && <span className="finna-acc-count">{vaultCount}</span>}
                    </Link>
                    <Link to="/desk" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">📚</span>
                      <span>Study Desk &amp; Rooms</span>
                    </Link>
                    <Link to="/games/quest" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">⚔️</span>
                      <span>Finna Quest RPG</span>
                    </Link>
                  </div>

                  <div className="finna-account-section">
                    <Link to="/creators/settings" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">🌐</span>
                      <span>Public Profile &amp; Visibility</span>
                    </Link>
                    <Link to="/account/security" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">⚙️</span>
                      <span>Account &amp; Security</span>
                    </Link>
                    <Link to="/billing" role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                      <span className="finna-acc-ico" aria-hidden="true">💳</span>
                      <span>Plan &amp; Billing</span>
                    </Link>
                    {staff.length > 0 && (
                      <Link to={staff[0].to} role="menuitem" className="finna-acc-item" onClick={closeMenu}>
                        <span className="finna-acc-ico" aria-hidden="true">🛠️</span>
                        <span>{staff[0].label}</span>
                      </Link>
                    )}
                    <button
                      type="button"
                      role="menuitem"
                      className="finna-acc-item"
                      onClick={() => setTheme(theme === 'night' ? 'paper' : 'night')}
                    >
                      <span className="finna-acc-ico" aria-hidden="true">{theme === 'night' ? '☀' : '☾'}</span>
                      <span>{theme === 'night' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
                    </button>
                  </div>

                  <div className="finna-account-footer">
                    <button
                      type="button"
                      role="menuitem"
                      disabled={signingOut}
                      className="finna-acc-item finna-acc-logout"
                      onClick={() => void handleLogout()}
                    >
                      <span className="finna-acc-ico" aria-hidden="true">↪</span>
                      <span>{signingOut ? 'Signing out…' : 'Sign out'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link
              to={'/login?next=' + encodeURIComponent(pathname + search)}
              className="finna-account"
              onClick={closeMenu}
            >
              Sign in
            </Link>
          )}
        </div>
      </div>

      {/* Row 2: Student Study-Loop Primary Navigation + Revise + My Exams */}
      {!focused && (
        <div
          className="finna-nav"
          onPointerLeave={(e) => {
            if (e.pointerType === 'mouse' && menu) scheduleClose()
          }}
        >
          <div className="finna-wrap finna-nav-inner">
            <nav aria-label="Primary navigation" className="finna-nav-list">
              {NAV_ITEMS.map((item) => {
                const items = MENUS[item.id] || []
                const hasMenu = items.length > 0
                const isOpen = menu === item.id
                const isCurrent = active(item.id)
                if (!hasMenu) {
                  return (
                    <Link
                      key={item.id}
                      to={item.path}
                      className="finna-nav-link"
                      aria-current={isCurrent ? 'page' : undefined}
                      onPointerEnter={(e) => {
                        if (e.pointerType === 'mouse' && menu) scheduleClose()
                      }}
                      onClick={closeMenu}
                    >
                      <span>{item.label}</span>
                    </Link>
                  )
                }
                return (
                  <button
                    key={item.id}
                    type="button"
                    ref={(el) => {
                      triggers.current[item.id] = el
                    }}
                    className={'finna-nav-link' + (isOpen ? ' is-open' : '')}
                    aria-current={isCurrent ? 'page' : undefined}
                    aria-haspopup="true"
                    aria-expanded={isOpen}
                    aria-controls={isOpen ? 'finna-mega-menu' : undefined}
                    onPointerEnter={(e) => {
                      if (e.pointerType === 'mouse') scheduleOpen(item.id)
                    }}
                    onClick={() => {
                      cancelTimers()
                      setMenu((cur) => (cur === item.id ? null : item.id))
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'ArrowDown') {
                        e.preventDefault()
                        openMenuAndFocusFirst(item.id)
                      }
                    }}
                  >
                    <span>{item.label}</span>
                    <svg
                      className="finna-nav-chevron"
                      width="13"
                      height="13"
                      viewBox="0 0 16 16"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M4 6l4 4 4-4" />
                    </svg>
                  </button>
                )
              })}
            </nav>

            <div className="finna-quick">
              <Link
                to="/revise"
                className={'finna-revise-pill' + (pathname === '/revise' ? ' is-current' : '')}
                onPointerEnter={(e) => {
                  if (e.pointerType === 'mouse' && menu) scheduleClose()
                }}
                onClick={closeMenu}
              >
                <span aria-hidden="true">↻</span>
                <span>Revise</span>
              </Link>

              <Link
                to="/desk"
                className="finna-secondary-tool"
                onPointerEnter={(e) => {
                  if (e.pointerType === 'mouse' && menu) scheduleClose()
                }}
                onClick={closeMenu}
              >
                Desk
              </Link>

              <Link
                to={
                  trackedExams.length > 1
                    ? '/home?view=exams'
                    : selected
                      ? '/exams/' + selected.id
                      : EXAMS_PATH
                }
                className="finna-exam-chip"
                onClick={closeMenu}
              >
                {selected
                  ? trackedExams.length > 1
                    ? `My exams: ${shortExamLabel(selected)} +${trackedExams.length - 1}`
                    : 'My exam: ' + shortExamLabel(selected)
                  : 'Choose your exam'}
              </Link>
            </div>
          </div>

          {menu && activeNavParent && activeMenuItems.length > 0 && (
            <div
              id="finna-mega-menu"
              ref={menuPanel}
              className="finna-menu"
              role="region"
              aria-label={`${activeNavParent.label} navigation`}
              onPointerEnter={(e) => {
                if (e.pointerType === 'mouse') cancelTimers()
              }}
              onKeyDown={onMenuKeyDown}
            >
              <div className="finna-wrap">
                <div className="finna-menu-inner">
                  <Link
                    to={activeNavParent.path}
                    className="finna-menu-featured"
                    aria-current={pathname === activeNavParent.path ? 'page' : undefined}
                    onClick={closeMenu}
                  >
                    <span className="finna-menu-feat-kicker">Start here</span>
                    <strong className="finna-menu-feat-title">
                      {activeNavParent.id === 'library'
                        ? 'Subject Library'
                        : activeNavParent.id === 'guides'
                          ? 'All Concept Guides'
                          : `All ${activeNavParent.label}`}
                    </strong>
                    <small>{activeNavParent.blurb}</small>
                    <span className="finna-menu-feat-go">Open overview →</span>
                  </Link>
                  {activeMenuItems.map((d) => {
                    const meta = MENU_CARD_META[d.id] || {
                      tone: 'cobalt' as MenuTone,
                      tag: 'Explore',
                      icon: 'M5 12h14m-6-6 6 6-6 6',
                    }
                    return (
                      <Link
                        key={d.id}
                        to={d.path}
                        className={`finna-menu-card finna-mtone-${meta.tone}`}
                        aria-current={pathname === d.path ? 'page' : undefined}
                        onClick={closeMenu}
                      >
                        <span className="finna-menu-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                            <path d={meta.icon} />
                          </svg>
                        </span>
                        <div className="finna-menu-card-copy">
                          <div className="finna-menu-card-head">
                            <strong className="finna-menu-card-title">{d.label}</strong>
                            <span className="finna-menu-arrow" aria-hidden="true">→</span>
                          </div>
                          <small>{d.blurb}</small>
                        </div>
                      </Link>
                    )
                  })}
                </div>

                {/* Live Quick-Jump strip inside the Subjects mega-menu (auto-includes future subject books) */}
                {activeNavParent.id === 'library' && subjectModules.length > 0 && (
                  <div className="finna-menu-exams-bar">
                    <span className="finna-menu-exams-label">Topic-wise books</span>
                    <div className="finna-menu-exams-pills">
                      {subjectModules.map((s) => (
                        <Link
                          key={s.id}
                          to={`${moduleHref(s)}?view=topics`}
                          className={'finna-menu-exam-pill' + (pathname === moduleHref(s) ? ' is-tracked' : '')}
                          onClick={closeMenu}
                        >
                          <span>{s.title}</span>
                        </Link>
                      ))}
                    </div>
                    <Link
                      to="/guides"
                      className="finna-menu-exam-pill finna-menu-exam-pill--manage"
                      onClick={closeMenu}
                    >
                      Concept Guides →
                    </Link>
                  </div>
                )}

                {/* Live Quick-Jump strip inside the Exams mega-menu */}
                {activeNavParent.id === 'exams' && quickJumpExams.length > 0 && (
                  <div className="finna-menu-exams-bar">
                    <span className="finna-menu-exams-label">Quick jump</span>
                    <div className="finna-menu-exams-pills">
                      {quickJumpExams.map((e) => {
                        const isTracked = trackedExams.some((t) => t.id === e.id)
                        return (
                          <Link
                            key={e.id}
                            to={'/exams/' + e.id}
                            className={'finna-menu-exam-pill' + (isTracked ? ' is-tracked' : '')}
                            onClick={closeMenu}
                          >
                            {isTracked && <span className="finna-menu-star" aria-hidden="true">★</span>}
                            <span>{shortExamLabel(e)}</span>
                          </Link>
                        )
                      })}
                    </div>
                    <Link
                      to="/home?view=exams"
                      className="finna-menu-exam-pill finna-menu-exam-pill--manage"
                      onClick={closeMenu}
                    >
                      Manage my exams →
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {!focused && <QuickFind access={access} trigger={false} />}
      {!focused &&
        (/^\/(?:bank|exams|library|subjects|practice|english|arithmetic|group-b|past-papers)(?:\/|$)/.test(
          pathname,
        ) ||
          (scope === 'all' && /^\/desk(?:\/|$)/.test(pathname))) && <BrowseAllowance />}
    </header>
  )
}
