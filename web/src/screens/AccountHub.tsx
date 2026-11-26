import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { STUDY_BACKGROUNDS, STUDY_THEMES, useStudyBackground, useStudyTheme } from '../lib/theme'
import { getAccountSession } from '../lib/api'
import {
  HOME_WIDGET_CATALOG,
  PRESET_DETAILS,
  syncHomePrefsWithServer,
  useHomePrefs,
} from '../lib/homePrefs'

const AccountSecurity = lazy(() => import('./AccountSecurity'))
const AccountPrivacy = lazy(() => import('./AccountPrivacy'))
const EmailPreferences = lazy(() => import('./EmailPreferences'))
const AccountRecovery = lazy(() => import('./AccountRecovery'))

type SectionId = 'security' | 'privacy' | 'email-preferences' | 'recovery' | 'appearance'

interface SectionDef {
  id: SectionId
  group: 'Security & account' | 'Preferences'
  label: string
  hint: string
  keywords: string
  icon: ReactNode
}

const ICONS: Record<SectionId, ReactNode> = {
  security: (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M10 2.5 4 5v4.6c0 3.7 2.5 6.8 6 7.9 3.5-1.1 6-4.2 6-7.9V5l-6-2.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M7.5 10l1.7 1.7 3.3-3.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  privacy: (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="4" y="9" width="12" height="8" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7 9V6.5a3 3 0 0 1 6 0V9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  'email-preferences': (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="3" y="4.5" width="14" height="11" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <path d="m4 6 6 4.5L16 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  recovery: (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M4.5 10a5.5 5.5 0 1 1 1.6 3.9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M4.5 6.5V10H8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  appearance: (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="3.2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.7 4.7l1.4 1.4M13.9 13.9l1.4 1.4M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
}

const SECTIONS: SectionDef[] = [
  {
    id: 'security',
    group: 'Security & account',
    label: 'Security & sign-in',
    hint: 'Password, authenticator MFA, Google sign-in & active sessions',
    keywords: 'security password mfa authenticator google login sessions sign out devices',
    icon: ICONS.security,
  },
  {
    id: 'privacy',
    group: 'Security & account',
    label: 'Privacy & data',
    hint: 'Access, export, correction & account closure requests',
    keywords: 'privacy data export download erase delete close account requests',
    icon: ICONS.privacy,
  },
  {
    id: 'email-preferences',
    group: 'Preferences',
    label: 'Email preferences',
    hint: 'Review digest reminders & notification controls',
    keywords: 'email notifications reminders digest unsubscribe alerts',
    icon: ICONS['email-preferences'],
  },
  {
    id: 'appearance',
    group: 'Preferences',
    label: 'Appearance & display',
    hint: 'Reading theme & study analytics Fun mode on this browser',
    keywords: 'appearance theme light dark night display fun mode colors',
    icon: ICONS.appearance,
  },
  {
    id: 'recovery',
    group: 'Security & account',
    label: 'Account recovery',
    hint: 'Reset password or reopen a recently closed account',
    keywords: 'recovery forgot password reset reopen locked out',
    icon: ICONS.recovery,
  },
]

const GROUPS: SectionDef['group'][] = ['Security & account', 'Preferences']

const SUGGESTIONS: { label: string; id: SectionId }[] = [
  { label: 'Password & MFA', id: 'security' },
  { label: 'Theme', id: 'appearance' },
  { label: 'Emails', id: 'email-preferences' },
  { label: 'Export data', id: 'privacy' },
  { label: 'Recovery', id: 'recovery' },
]

const FUN_KEY = 'finna.study-fun-mode'

function AppearancePanel() {
  const [theme, setTheme] = useStudyTheme()
  const [studyBg, setStudyBg] = useStudyBackground()
  const [fun, setFun] = useState(() => {
    try {
      return typeof localStorage !== 'undefined' && localStorage.getItem(FUN_KEY) === 'on'
    } catch {
      return false
    }
  })

  function toggleFun() {
    setFun((prev) => {
      const next = !prev
      try {
        localStorage.setItem(FUN_KEY, next ? 'on' : 'off')
      } catch {
        /* ignore storage errors */
      }
      return next
    })
  }

  const [authenticated, setAuthenticated] = useState(false)
  const { prefs, applyPreset, toggleWidget } = useHomePrefs(authenticated)

  useEffect(() => {
    let live = true
    getAccountSession()
      .then((s) => {
        if (!live) return
        const isAuth = Boolean(s.authenticated)
        setAuthenticated(isAuth)
        if (isAuth) void syncHomePrefsWithServer(true)
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [])

  return (
    <div className="finna-st-panel">
      <div className="finna-st-h1row">
        <h2 className="finna-st-h1">Appearance &amp; display</h2>
        <span className="finna-st-badge">This browser</span>
      </div>
      <p className="finna-st-caption">
        Choose how Finna looks while you study. Changes take effect immediately across every screen.
      </p>

      <div className="finna-st-grouplabel">Reading theme</div>
      <div className="finna-st-theme-grid" role="group" aria-label="Reading theme">
        {STUDY_THEMES.map((item) => {
          const active = theme === item.id
          return (
            <button
              key={item.id}
              type="button"
              aria-pressed={active}
              onClick={() => setTheme(item.id)}
              className={'finna-st-theme-card' + (active ? ' is-active' : '')}
            >
              <span className={'finna-st-theme-swatch finna-st-theme-swatch--' + item.id} aria-hidden="true" />
              <span className="finna-st-theme-txt">
                <strong>{item.label}</strong>
                <small>{item.description}</small>
              </span>
            </button>
          )
        })}
      </div>

      <div className="finna-st-grouplabel">Study home backdrop</div>
      <div className="hsw-preset-grid" role="group" aria-label="Study home backdrop">
        {STUDY_BACKGROUNDS.map((item) => {
          const active = studyBg === item.id
          return (
            <button
              key={item.id}
              type="button"
              aria-pressed={active}
              onClick={() => setStudyBg(item.id)}
              className={`hsw-preset-card${active ? ' is-active' : ''}`}
            >
              <div className="hsw-preset-top">
                <strong>{item.label}</strong>
              </div>
              <small>{item.description}</small>
            </button>
          )
        })}
      </div>

      <div className="finna-st-grouplabel">Interactive touches</div>
      <div className="finna-st-togglerow">
        <div className="finna-st-togglerow-txt">
          <div className="finna-st-togglerow-title">Profile analytics Fun mode</div>
          <div className="finna-st-togglerow-sub">
            Lively lagoon-to-sunset sticker cards &amp; wave titles on your Profile analytics deck
          </div>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={fun}
          aria-label="Profile analytics Fun mode"
          onClick={toggleFun}
          className={'finna-st-toggle' + (fun ? ' is-on' : '')}
        >
          <span className="finna-st-toggle-dot" />
        </button>
      </div>

      <div className="finna-st-grouplabel">Front page layout (/home)</div>
      <p className="finna-st-caption" style={{ marginTop: 0 }}>
        Choose a preset or hide individual cards so your front page stays calm and focused.
      </p>
      <div className="hsw-preset-grid" role="group" aria-label="Home layout presets">
        {PRESET_DETAILS.map((p) => {
          const active = prefs.preset === p.id
          return (
            <button
              key={p.id}
              type="button"
              aria-pressed={active}
              onClick={() => applyPreset(p.id, true)}
              className={`hsw-preset-card${active ? ' is-active' : ''}`}
            >
              <div className="hsw-preset-top">
                <strong>{p.title}</strong>
                {p.badge && <span className="hsw-preset-badge">{p.badge}</span>}
              </div>
              <small>{p.summary}</small>
            </button>
          )
        })}
      </div>
      <div className="hsw-toggle-list mt-3">
        {HOME_WIDGET_CATALOG.map((w) => {
          const shown = !prefs.hidden.includes(w.id)
          return (
            <div key={w.id} className="finna-st-togglerow">
              <div className="finna-st-togglerow-txt">
                <div className="finna-st-togglerow-title">{w.label}</div>
                <div className="finna-st-togglerow-sub">{w.description}</div>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={shown}
                aria-label={`${shown ? 'Hide' : 'Show'} ${w.label}`}
                onClick={() => toggleWidget(w.id)}
                className={'finna-st-toggle' + (shown ? ' is-on' : '')}
              >
                <span className="finna-st-toggle-dot" />
              </button>
            </div>
          )
        })}
      </div>
      <div className="finna-st-cardrow">
        <div>
          <div className="finna-st-cardrow-title">First-time setup wizard</div>
          <div className="finna-st-cardrow-sub">
            Re-pick your target exams, focus subjects and front page cards together
          </div>
        </div>
        <div className="finna-st-cardrow-act">
          <Link to="/home?setup=1" className="finna-st-btn">
            Run Home setup →
          </Link>
        </div>
      </div>

      <div className="finna-st-cardrow">
        <div>
          <div className="finna-st-cardrow-title">Profile &amp; study shortcuts</div>
          <div className="finna-st-cardrow-sub">Manage your display name, avatar, rewards and exam plan</div>
        </div>
        <div className="finna-st-cardrow-act">
          <Link to="/profile" className="finna-st-btn">Open profile</Link>
          <Link to="/billing" className="finna-st-btn">Plan &amp; billing</Link>
        </div>
      </div>
    </div>
  )
}

/** Consolidated `/account/:section?` settings shell — ShikshaCom compact sidebar + search layout. */
export default function AccountHub() {
  const { section = 'security' } = useParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const active: SectionId = SECTIONS.some((s) => s.id === section)
    ? (section as SectionId)
    : 'security'
  const activeMeta = SECTIONS.find((s) => s.id === active) || SECTIONS[0]

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return SECTIONS
    return SECTIONS.filter(
      (s) =>
        s.label.toLowerCase().includes(q) ||
        s.hint.toLowerCase().includes(q) ||
        s.keywords.includes(q),
    )
  }, [query])

  function openSection(id: SectionId) {
    setQuery('')
    navigate('/account/' + id)
  }

  return (
    <div className="finna-page finna-st-wrap">
      <div className="finna-st-shell">
        <header className="finna-st-head">
          <span className="finna-st-head-av" aria-hidden="true">⚙</span>
          <div className="finna-st-head-txt">
            <h1>Account &amp; settings</h1>
            <p>{activeMeta.hint}</p>
          </div>
          <div className="finna-st-head-actions">
            <Link to="/profile" className="finna-st-btn">← Profile</Link>
            <Link to="/billing" className="finna-st-btn">Billing</Link>
          </div>
        </header>

        <div className="finna-st-searchbar">
          <label className="finna-st-search-field">
            <span className="sr-only">Search settings</span>
            <svg className="finna-st-search-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.6" />
              <path d="m13.5 13.5 3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search password, MFA, privacy, theme, email…"
              className="finna-st-search-input"
            />
            {query && (
              <button
                type="button"
                aria-label="Clear search"
                onClick={() => setQuery('')}
                className="finna-st-search-clear"
              >
                ×
              </button>
            )}
          </label>
          <div className="finna-st-chips" aria-label="Quick settings jump">
            {SUGGESTIONS.map((chip) => (
              <button
                key={chip.label}
                type="button"
                onClick={() => openSection(chip.id)}
                className={'finna-st-chip' + (active === chip.id && !query ? ' is-current' : '')}
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        <div className="finna-st-body">
          <nav aria-label="Account sections" className="finna-st-side">
            {!filtered.length ? (
              <p className="finna-st-side-none">No settings match “{query}”.</p>
            ) : (
              GROUPS.map((group) => {
                const rows = filtered.filter((s) => s.group === group)
                if (!rows.length) return null
                return (
                  <div key={group} className="finna-st-side-group-wrap">
                    <div className="finna-st-side-group">{group}</div>
                    {rows.map((item) => (
                      <Link
                        key={item.id}
                        to={'/account/' + item.id}
                        aria-current={active === item.id ? 'page' : undefined}
                        className={'finna-st-navitem' + (active === item.id ? ' is-on' : '')}
                      >
                        <span className="finna-st-navitem-icon">{item.icon}</span>
                        <span className="finna-st-navitem-lbl">{item.label}</span>
                      </Link>
                    ))}
                  </div>
                )
              })
            )}
          </nav>

          <div className="finna-st-pane">
            <Suspense fallback={<p role="status" className="text-sm text-secondary">Loading account settings…</p>}>
              {active === 'security' && <AccountSecurity />}
              {active === 'privacy' && <AccountPrivacy />}
              {active === 'email-preferences' && <EmailPreferences />}
              {active === 'recovery' && <AccountRecovery />}
              {active === 'appearance' && <AppearancePanel />}
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  )
}
