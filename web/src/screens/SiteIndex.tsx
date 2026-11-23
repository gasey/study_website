import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAccountSession } from '../lib/api'
import { reviewRequest, reviewSession, type ReviewSession } from '../lib/review'
import { reviewDestinations } from '../lib/reviewNavigation'
import { SITE_MAP, type Destination } from '../lib/siteMap'
import { STUDY_THEMES, useStudyTheme } from '../lib/theme'

const GROUPS: { id: string; title: string; match: (d: Destination) => boolean }[] = [
  {
    id: 'study',
    title: 'Exams & Practice',
    match: (d) =>
      d.section === 'practice' ||
      ['home', 'exams', 'papers', 'bank', 'calendar'].includes(d.id),
  },
  {
    id: 'guides',
    title: 'Guides & Reference',
    match: (d) =>
      d.section === 'guides' ||
      d.menu === 'guides' ||
      d.id === 'desk',
  },
  {
    id: 'community',
    title: 'Community & Account',
    match: (d) =>
      d.section === 'community' ||
      (d.section === 'you' && d.id !== 'desk'),
  },
]

/** Compact single-screen directory (`/index`): groups all destinations into
 *  3 tight cards with instant filtering and inline appearance controls so
 *  everything is visible at a glance without scrolling a long wall of rows. */
export default function SiteIndex() {
  const [theme, setTheme] = useStudyTheme()
  const [query, setQuery] = useState('')
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)
  const [session, setSession] = useState<ReviewSession | null>(null)
  const [assigned, setAssigned] = useState(false)

  useEffect(() => {
    let live = true
    let version = 0
    const load = () => {
      const run = ++version
      setSession(null)
      setAssigned(false)
      getAccountSession()
        .then(async (a) => {
          if (!live || run !== version) return
          setAuthenticated(a.authenticated)
          if (!a.authenticated) return
          const s = await reviewSession()
          const hasAssigned = s.grants.length
            ? false
            : (await reviewRequest<{ items: { state: string }[] }>('/editorial/assignments')).items.some(
                (x) => x.state === 'active' || x.state === 'pending',
              )
          if (live && run === version) {
            setSession(s)
            setAssigned(hasAssigned)
          }
        })
        .catch(() => {})
    }
    load()
    window.addEventListener('ism-auth-change', load)
    return () => {
      live = false
      window.removeEventListener('ism-auth-change', load)
    }
  }, [])

  const staffLinks = reviewDestinations({ grants: session?.grants || [], assigned })

  const allItems = useMemo(
    () => SITE_MAP.filter((d) => d.surfaces.includes('index') && d.id !== 'index'),
    [],
  )

  const needle = query.trim().toLowerCase()
  const matches = (d: Destination) =>
    !needle ||
    d.label.toLowerCase().includes(needle) ||
    d.blurb.toLowerCase().includes(needle) ||
    (d.keywords || '').toLowerCase().includes(needle)

  const visibleGroups = useMemo(
    () =>
      GROUPS.map((g) => ({
        ...g,
        items: allItems.filter((d) => g.match(d) && matches(d)),
      })).filter((g) => g.items.length > 0),
    [allItems, needle],
  )

  return (
    <div className="finna-page" data-screen="index">
      <header className="mb-5 flex flex-wrap items-center justify-between gap-4 border-b border-hairline pb-4">
        <div>
          <div className="finna-eyebrow">All pages</div>
          <h1 className="mt-1 text-2xl font-bold text-ink">Everything on Finna</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter pages…"
            aria-label="Filter pages"
            className="min-h-10 w-52 rounded-xl border border-hairline bg-card px-3 text-sm"
          />
          <div className="finna-segments" role="group" aria-label="Reading theme">
            {STUDY_THEMES.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={theme === item.id}
                onClick={() => setTheme(item.id)}
              >
                {item.shortLabel}
              </button>
            ))}
          </div>
        </div>
      </header>

      {visibleGroups.length === 0 ? (
        <div className="finna-card text-center">
          <p className="text-sm text-secondary">No pages match “{query.trim()}”.</p>
          <button
            type="button"
            onClick={() => setQuery('')}
            className="finna-btn finna-btn-quiet mt-3"
          >
            Clear filter
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {visibleGroups.map((group) => (
            <section
              key={group.id}
              aria-labelledby={`index-${group.id}`}
              className="finna-card flex flex-col gap-1"
            >
              <h2
                id={`index-${group.id}`}
                className="mb-2 border-b border-hairline pb-2 font-mono text-xs font-semibold uppercase tracking-[0.08em] text-muted"
              >
                {group.title}
              </h2>
              <div className="flex flex-col gap-0.5">
                {group.items.map((item) => (
                  <Link
                    key={item.id}
                    to={item.path}
                    className="flex items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-sm font-semibold text-ink transition-colors hover:bg-canvas hover:text-link"
                    title={item.blurb}
                  >
                    <span>{item.label}</span>
                    <span className="text-xs text-muted" aria-hidden="true">→</span>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {(staffLinks.length > 0 || authenticated === false) && (
        <section className="finna-card mt-4 flex flex-wrap items-center justify-between gap-3">
          {staffLinks.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Staff
              </span>
              {staffLinks.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="rounded-lg border border-hairline bg-paper px-3 py-1.5 text-xs font-bold text-link hover:bg-canvas"
                >
                  {item.label} →
                </Link>
              ))}
            </div>
          )}
          {authenticated === false && (
            <div className="ml-auto flex flex-wrap gap-2">
              <Link to="/login?next=%2Fhome" className="finna-btn finna-btn-quiet">
                Sign in
              </Link>
              <Link to="/join?next=%2Fhome" className="finna-btn">
                Join free
              </Link>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
