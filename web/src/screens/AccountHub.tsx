import { lazy, Suspense } from 'react'
import { Link, useParams } from 'react-router-dom'

const AccountSecurity = lazy(() => import('./AccountSecurity'))
const AccountPrivacy = lazy(() => import('./AccountPrivacy'))
const EmailPreferences = lazy(() => import('./EmailPreferences'))
const AccountRecovery = lazy(() => import('./AccountRecovery'))

const TABS = [
  ['security', 'Security & sign-in'],
  ['privacy', 'Privacy & data'],
  ['email-preferences', 'Email preferences'],
  ['recovery', 'Account recovery'],
] as const

/** Consolidated `/account/:section?` screen (§VII.14 — 4 account routes → 1). */
export default function AccountHub() {
  const { section = 'security' } = useParams()
  const active = TABS.some(([id]) => id === section) ? section : 'security'
  return (
    <div className="mx-auto max-w-[1160px] px-4 pb-16 pt-6 sm:px-6">
      <nav aria-label="Account sections" className="mb-6 flex flex-wrap gap-2 border-b border-hairline pb-3">
        {TABS.map(([id, label]) => (
          <Link
            key={id}
            to={'/account/' + id}
            aria-current={active === id ? 'page' : undefined}
            className={
              'inline-flex min-h-11 items-center rounded-lg border px-4 py-2 text-sm font-semibold ' +
              (active === id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card text-ink hover:border-ink')
            }
          >
            {label}
          </Link>
        ))}
      </nav>
      <Suspense fallback={<p role="status" className="text-sm text-secondary">Loading account settings…</p>}>
        {active === 'security' && <AccountSecurity />}
        {active === 'privacy' && <AccountPrivacy />}
        {active === 'email-preferences' && <EmailPreferences />}
        {active === 'recovery' && <AccountRecovery />}
      </Suspense>
    </div>
  )
}
