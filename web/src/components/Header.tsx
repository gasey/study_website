import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  getAccountSession,
  getProgressSummary,
  listCollections,
  isLaterExamCollection,
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
import { Avatar } from './ui'
import QuickFind from './QuickFind'
import NavIcon from './NavIcon'
import BrowseAllowance from './BrowseAllowance'

const NAV_ITEMS = destinationsForSurface('nav')
const QUICK_ITEMS = destinationsForSurface('quick')
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

/** Unified desktop nav (§VII.3.3, pure dropdown trigger pattern):
 *  Sections with sub-pages (`Exams`, `Practice`, `Guides`, `Community`) are
 *  pure `<button>` dropdown toggles — hovering OR clicking opens/closes the
 *  menu without navigating away. Every destination (including the featured
 *  `All Guides →` / `All Exams →` overview card) is chosen cleanly inside the
 *  dropdown. Plain leaf items (`Papers`) remain direct `<Link>` elements. */
export default function Header() {
  const { pathname, search } = useLocation()
  const scope = useExamScope()
  const [theme, setTheme] = useStudyTheme()
  const [access, setAccess] = useState<ReviewAccess>({ grants: [], assigned: false })
  const [account, setAccount] = useState<AccountSession>({ authenticated: false })
  const [unread, setUnread] = useState<number | null>(null)
  const [streak, setStreak] = useState<number | null>(null)
  const [exams, setExams] = useState<Collection[]>([])
  const [menu, setMenu] = useState<string | null>(null)
  const selected = usePreferredExam(exams)
  const shell = useRef<HTMLElement>(null)
  const menuPanel = useRef<HTMLDivElement>(null)
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
    const load = () => {
      const run = ++version
      setUnread(null)
      setStreak(null)
      setAccess({ grants: [], assigned: false })
      setAccount({ authenticated: false })
      getProgressSummary()
        .then((p) => {
          if (live && run === version) setStreak(p.current_streak)
        })
        .catch(() => {})
      getAccountSession()
        .then(async (a) => {
          if (!live || run !== version) return
          setAccount(a)
          if (!a.authenticated) return
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
    load()
    const events = ['ism-auth-change', 'ism-avatar-change', 'ism-notifications-change', 'focus']
    events.forEach((e) => window.addEventListener(e, load))
    return () => {
      live = false
      events.forEach((e) => window.removeEventListener(e, load))
    }
  }, [])

  useEffect(() => {
    let live = true
    setExams([])
    listCollections()
      .then((rows) => {
        if (live) setExams(rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)))
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [scope])

  useEffect(() => {
    cancelTimers()
    setMenu(null)
  }, [pathname, search])

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
  }

  const focused = focusedSession(pathname, search)
  const openFind = () => window.dispatchEvent(new Event('finna-open-find'))
  const openHelp = () => window.dispatchEvent(new Event('finna-open-help'))
  const active = (id: string) =>
    id === 'exams'
      ? /^\/(exams|group-b)/.test(pathname)
      : id === 'papers'
        ? pathname === '/past-papers'
        : id === 'practice'
          ? /^\/(practice|bank|tests|revise|games)/.test(pathname)
          : id === 'guides'
            ? /^\/(guides|library|english|arithmetic|mizo|atlas|chronicle|stats)/.test(pathname)
            : id === 'community'
              ? /^\/(community|creators|materials|create)/.test(pathname)
              : pathname === INDEX_PATH
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

      {!focused && (
        <div className="finna-top">
          <div className="finna-wrap finna-top-inner">
            <span className="finna-top-tag">Study</span>
            <span className="finna-top-note">Past papers. Clear sources. Your next step.</span>
            <div className="finna-top-actions">
              {streak !== null && streak > 0 && (
                <Link to={PROFILE_PATH} className="text-[#FFC83D]">
                  {streak} day streak
                </Link>
              )}
              {account.authenticated && (
                <Link to={INBOX_PATH}>
                  Inbox{' '}
                  {unread !== null && <span className="finna-unread-pill">{unread}</span>}
                </Link>
              )}
              <button
                type="button"
                className="finna-theme"
                onClick={openHelp}
                aria-label="Help and keyboard shortcuts"
                title="Help & shortcuts (?)"
              >
                ?
              </button>
              <button
                type="button"
                className="finna-theme"
                onClick={() => setTheme(theme === 'night' ? 'paper' : 'night')}
                aria-label={`Switch to ${theme === 'night' ? 'light' : 'dark'} theme`}
              >
                {theme === 'night' ? 'Light' : 'Dark'}
              </button>
              {staff.length > 0 && (
                <nav aria-label="Workspaces" className="flex items-center gap-4">
                  {staff.slice(0, 2).map((link) => (
                    <Link key={link.to} to={link.to}>
                      {link.label}
                    </Link>
                  ))}
                </nav>
              )}
            </div>
          </div>
        </div>
      )}

      {!focused && (
        <div className="finna-phone-header">
          <div className="finna-phone-heading">
            {pathname !== HOME_PATH && (
              <Link
                to={
                  /^\/(bank|exams)\//.test(pathname)
                    ? EXAMS_PATH
                    : pathname.startsWith('/library/')
                      ? LIBRARY_PATH
                      : HOME_PATH
                }
                aria-label="Back to home"
                className="finna-phone-back"
              >
                ‹
              </Link>
            )}
            <h1>{mobileTitle(pathname)}</h1>
          </div>
          <nav aria-label="Phone quick actions">
            {pathname === HOME_PATH && streak !== null && (
              <Link to={PROFILE_PATH} className="finna-phone-streak">
                {streak} day streak
              </Link>
            )}
            <button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog">
              <NavIcon name="search" />
            </button>
            <Link to={CREATE_PATH} aria-label="Create">
              <NavIcon name="create" />
            </Link>
            <Link to={INBOX_PATH} aria-label={unread ? 'Inbox, ' + unread + ' unread' : 'Inbox'}>
              <span aria-hidden="true">✉</span>
              {unread !== null && unread > 0 && (
                <span className="finna-phone-unread">{unread > 99 ? '99+' : unread}</span>
              )}
            </Link>
            <Link to={INDEX_PATH} aria-label="Index and appearance">
              <NavIcon name="more" />
            </Link>
          </nav>
        </div>
      )}

      <div className="finna-brand-row">
        <div className="finna-wrap finna-brand-inner">
          <Link to={HOME_PATH} className="finna-brand" aria-label="Finna home" onClick={closeMenu}>
            Finna<span>.</span>
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
              <span>Find an exam, question or guide</span>
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
            <Link to={CREATE_PATH} className="finna-create" onClick={closeMenu}>
              Create
            </Link>
          )}
          {focused && (
            <Link to={HOME_PATH} className="ml-auto text-sm font-semibold text-link">
              Home →
            </Link>
          )}
          {account.authenticated ? (
            <Link to={PROFILE_PATH} className="finna-account" aria-label="Your profile" onClick={closeMenu}>
              <Avatar look={account.avatar} initials={account.email?.slice(0, 2).toUpperCase() || 'Me'} />
            </Link>
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

      {!focused && (
        <div
          className="finna-nav"
          onPointerLeave={(e) => {
            if (e.pointerType === 'mouse' && menu) scheduleClose()
          }}
        >
          <div className="finna-wrap finna-nav-inner">
            <nav aria-label="Primary navigation" className="flex items-center gap-1">
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
              {QUICK_ITEMS.map((item) => (
                <Link
                  key={item.id}
                  to={item.path}
                  className={item.id === 'desk' ? 'finna-secondary-tool' : undefined}
                  onPointerEnter={(e) => {
                    if (e.pointerType === 'mouse' && menu) scheduleClose()
                  }}
                  onClick={closeMenu}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                to={selected ? '/exams/' + selected.id : EXAMS_PATH}
                className="finna-exam-chip"
                onClick={closeMenu}
              >
                {selected
                  ? 'My exam: ' + selected.title.replace(/\s*[·(].*$/, '').slice(0, 24)
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
                    <span>All {activeNavParent.label} →</span>
                    <small>{activeNavParent.blurb}</small>
                  </Link>
                  {activeMenuItems.map((d) => (
                    <Link
                      key={d.id}
                      to={d.path}
                      aria-current={pathname === d.path ? 'page' : undefined}
                      onClick={closeMenu}
                    >
                      <span>{d.label}</span>
                      <small>{d.blurb}</small>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {!focused && <QuickFind access={access} trigger={false} />}
      {!focused &&
        (/^\/(?:bank|exams|library|practice|english|arithmetic|group-b|past-papers)(?:\/|$)/.test(
          pathname,
        ) ||
          (scope === 'all' && /^\/desk(?:\/|$)/.test(pathname))) && <BrowseAllowance />}
    </header>
  )
}
