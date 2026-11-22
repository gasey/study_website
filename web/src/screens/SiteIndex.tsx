import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAccountSession } from '../lib/api'
import { reviewRequest, reviewSession, type ReviewSession } from '../lib/review'
import { reviewDestinations } from '../lib/reviewNavigation'
import { SECTION_ORDER, SITE_MAP } from '../lib/siteMap'
import { STUDY_THEMES, useStudyTheme } from '../lib/theme'

/** `/index` — the honest contents page (§VII.3.2).
 *  Generated directly from `siteMap.ts`. Replaces `/more`, mega-menus and
 *  duplicated footer link grids. No icons, no cards, no invented counts. */
export default function SiteIndex() {
  const [theme, setTheme] = useStudyTheme()
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

  return (
    <div className="mx-auto max-w-[850px] px-4 pb-20 pt-8 sm:px-6" data-screen="index">
      <header className="border-b border-hairline pb-5">
        <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">Directory</p>
        <h1 className="mt-1 text-3xl font-bold text-ink">Finna Index</h1>
        <p className="mt-2 text-base text-secondary">
          Every study surface, tool and account page on Finna, in one plain list.
        </p>
      </header>

      <div className="mt-8 space-y-10">
        {SECTION_ORDER.map((section) => {
          const items = SITE_MAP.filter(
            (d) => d.section === section.id && d.surfaces.includes('index') && d.id !== 'index',
          )
          if (!items.length) return null
          return (
            <section key={section.id} aria-labelledby={`index-${section.id}`}>
              <h2
                id={`index-${section.id}`}
                className="border-b border-hairline pb-2 font-mono text-xs font-semibold uppercase tracking-[0.08em] text-muted"
              >
                {section.title}
              </h2>
              <ul className="divide-y divide-hairline">
                {items.map((item) => (
                  <li key={item.id}>
                    <Link
                      to={item.path}
                      className="flex flex-col gap-1 py-3.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6 hover:underline"
                    >
                      <span className="shrink-0 text-base font-semibold text-link">{item.label}</span>
                      <span className="text-sm text-secondary sm:text-right">{item.blurb}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )
        })}

        {staffLinks.length > 0 && (
          <section aria-labelledby="index-staff">
            <h2
              id="index-staff"
              className="border-b border-hairline pb-2 font-mono text-xs font-semibold uppercase tracking-[0.08em] text-muted"
            >
              Staff &amp; Review
            </h2>
            <ul className="divide-y divide-hairline">
              {staffLinks.map((item) => (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className="flex flex-col gap-1 py-3.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6 hover:underline"
                  >
                    <span className="shrink-0 text-base font-semibold text-link">{item.label}</span>
                    <span className="text-sm text-secondary sm:text-right">{item.description}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="index-appearance" className="border-t border-hairline pt-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 id="index-appearance" className="text-base font-bold text-ink">
                Reading appearance
              </h2>
              <p className="text-sm text-secondary">Daytime paper or low-light night mode.</p>
            </div>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Select study theme">
              {STUDY_THEMES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={theme === item.id}
                  onClick={() => setTheme(item.id)}
                  className={
                    'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
                    (theme === item.id
                      ? 'border-ink bg-ink text-paper'
                      : 'border-hairline bg-card text-ink hover:border-hairline2')
                  }
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          {authenticated === false && (
            <div className="mt-5 flex flex-wrap gap-4 border-t border-hairline pt-4 text-sm">
              <Link to="/login?next=%2Findex" className="font-semibold text-link hover:underline">
                Sign in
              </Link>
              <Link to="/join?next=%2Findex" className="font-semibold text-link hover:underline">
                Create an account
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
