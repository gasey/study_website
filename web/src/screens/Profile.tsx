import { OwnCommunityStanding } from '../components/ContributorStanding'
import AccountTools from '../components/AccountTools'
import ReviewDigestPreference from '../components/ReviewDigestPreference'
import ReferralPanel from '../components/ReferralPanel'
import IdentityEditor from '../components/IdentityEditor'
import MasteryMap from '../components/MasteryMap'
import StudyAnalyticsDeck from '../components/StudyAnalyticsDeck'
import VaultShowcaseCard from '../components/VaultShowcaseCard'
import { UserAvatar } from '../components/AvatarArt'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  getProfile,
  getScoreSummary,
  logoutAccount,
  updateProfile,
  type PrivateProfile,
  type ScoreSummary,
} from '../lib/api'
import { reviewRequest } from '../lib/review'

type ProfileTab = 'overview' | 'account' | 'community' | 'studio'

function initials(name: string) {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || 'S'
  )
}

export default function Profile() {
  const location = useLocation()
  const [profile, setProfile] = useState<PrivateProfile | null>(null)
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [editing, setEditing] = useState(false)
  const [scoreSummary, setScoreSummary] = useState<ScoreSummary | null>(null)
  const [credit, setCredit] = useState<number | null>(null)
  const [creditError, setCreditError] = useState('')
  const [tab, setTab] = useState<ProfileTab>(() =>
    location.hash === '#account-tools-title' ? 'account' : 'overview',
  )

  useEffect(() => {
    if (location.hash === '#account-tools-title') setTab('account')
  }, [location.hash])

  useEffect(() => {
    let generation = 0
    const load = () => {
      const run = ++generation
      setProfile(null)
      setScoreSummary(null)
      setCredit(null)
      setCreditError('')
      setName('')
      setEditing(false)
      setError('')
      setLoading(true)
      getScoreSummary()
        .then((data) => {
          if (run === generation) setScoreSummary(data)
        })
        .catch(() => {})
      getProfile()
        .then((data) => {
          if (run === generation) {
            setProfile(data)
            setName(data.name ?? '')
          }
        })
        .catch((e) => {
          if (run === generation)
            setError(e.message || 'Could not load your profile.')
        })
        .finally(() => {
          if (run === generation) setLoading(false)
        })
    }
    load()
    window.addEventListener('ism-auth-change', load)
    window.addEventListener('ism-auth-expired', load)
    return () => {
      generation++
      window.removeEventListener('ism-auth-change', load)
      window.removeEventListener('ism-auth-expired', load)
    }
  }, [])

  useEffect(() => {
    if (tab !== 'community' || profile?.account_type !== 'account') return
    let live = true
    reviewRequest<{ credit: number }>('/contributions/summary')
      .then((r) => {
        if (live) setCredit(r.credit)
      })
      .catch((e) => {
        if (live) setCreditError(e.message)
      })
    return () => {
      live = false
    }
  }, [tab, profile?.account_type])

  const saveName = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSaved(false)
    try {
      const updated = await updateProfile(name)
      setProfile(updated)
      setName(updated.name ?? '')
      setSaved(true)
      setEditing(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save your profile.')
    } finally {
      setSaving(false)
    }
  }

  const activity = useMemo(() => {
    const byDay = new Map(
      profile?.progress.daily_activity.map((d) => [d.day, d]) ?? [],
    )
    const today = new Date()
    return Array.from({ length: 30 }, (_, i) => {
      const date = new Date(today)
      date.setDate(today.getDate() - i)
      const day = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      return { ...(byDay.get(day) ?? { answered: 0, correct: 0 }), day }
    }).filter((d) => d.answered > 0)
  }, [profile])

  const p = profile?.progress
  const todayKey = new Date().toLocaleDateString('en-CA')
  const todayAnswered =
    p?.daily_activity.find((day) => day.day === todayKey)?.answered ?? 0
  const isAccount = profile?.account_type === 'account'

  const tabs: { id: ProfileTab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'account', label: 'Account & setup' },
    { id: 'community', label: 'Rewards & community' },
    { id: 'studio', label: 'Materials & studio' },
  ]

  return (
    <main className="finna-page finna-profile-v2">
      {error && (
        <div
          role="alert"
          className="mb-4 rounded-[12px] border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark"
        >
          {error}
        </div>
      )}
      {loading && (
        <div className="finna-card text-sm text-secondary">
          Loading your profile…
        </div>
      )}
      {!loading && !profile && (
        <div className="finna-card text-sm text-secondary">
          Your profile could not be loaded. Please refresh to try again.
        </div>
      )}

      {profile && (
        <>
          <section className="finna-prof-hero">
            <div className="finna-prof-id">
              <div className="finna-prof-avcol">
                <UserAvatar
                  look={profile.avatar}
                  initials={initials(profile.name || profile.handle)}
                  size={74}
                />
                <Link to="/profile/avatar" className="finna-prof-avlink">
                  Edit pixel sprite
                </Link>
              </div>
              <div className="finna-prof-meta">
                <div className="finna-prof-title-row">
                  <h1>{profile.name || 'Set your display name'}</h1>
                  <span className="finna-prof-lvl">Level {profile.level}</span>
                </div>
                <div className="finna-prof-sub">
                  <span className="font-mono">@{profile.handle}</span>
                  <span aria-hidden="true">·</span>
                  <span>
                    {isAccount
                      ? profile.email
                      : 'Guest profile on this browser'}
                  </span>
                </div>
                <p className="finna-prof-priv">
                  Study progress stays private unless you opt in to community
                  boards or a public creator page.
                </p>
              </div>
            </div>

            <div className="finna-prof-actions">
              <button
                type="button"
                onClick={() => setEditing((v) => !v)}
                className={
                  'finna-st-btn' + (editing ? ' finna-st-btn--primary' : '')
                }
              >
                {editing ? 'Close editor' : 'Edit profile'}
              </button>
              <Link to="/account/security" className="finna-st-btn">
                Settings
              </Link>
              <Link to="/creators/settings" className="finna-st-btn">
                Creator visibility
              </Link>
              {isAccount ? (
                <>
                  <Link to="/billing" className="finna-st-btn">
                    Plan &amp; billing
                  </Link>
                  <button
                    type="button"
                    onClick={() =>
                      void logoutAccount().then(() => {
                        window.dispatchEvent(new Event('ism-auth-change'))
                        window.location.assign('/')
                      })
                    }
                    className="finna-st-btn finna-st-btn--quiet"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <Link
                  to="/join"
                  className="finna-st-btn finna-st-btn--primary"
                >
                  Join free · sync progress
                </Link>
              )}
            </div>
          </section>

          {editing && isAccount && (
            <section id="profile-identity-editor" className="mt-4">
              <IdentityEditor />
            </section>
          )}
          {editing && !isAccount && (
            <form
              onSubmit={(event) => void saveName(event)}
              className="finna-card mt-4 flex flex-wrap items-end gap-3"
            >
              <div className="min-w-[220px] flex-1">
                <label htmlFor="profile-name" className="text-sm font-semibold">
                  Display name
                </label>
                <input
                  id="profile-name"
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value)
                    setSaved(false)
                  }}
                  maxLength={60}
                  autoComplete="nickname"
                  placeholder="Your display name"
                  className="mt-1.5 h-11 w-full rounded-[10px] border border-hairline bg-paper px-3 text-sm outline-none focus:border-ink"
                />
              </div>
              <button
                disabled={saving || name === (profile.name ?? '')}
                className="finna-st-btn finna-st-btn--primary"
              >
                {saving ? 'Saving…' : 'Save profile'}
              </button>
              {saved && (
                <span role="status" className="text-xs text-correct-dark">
                  Saved
                </span>
              )}
            </form>
          )}

          <nav
            aria-label="Profile sections"
            className="finna-prof-tabs"
          >
            {tabs.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setTab(item.id)}
                aria-current={tab === item.id ? 'page' : undefined}
                className={
                  'finna-prof-tab' + (tab === item.id ? ' is-active' : '')
                }
              >
                {item.label}
              </button>
            ))}
          </nav>

          {tab === 'overview' && (
            <div className="finna-prof-stack">
              <StudyAnalyticsDeck progress={p} todayAnswered={todayAnswered} />

              <div className="finna-prof-two">
                <div className="finna-prof-main">
                  {isAccount && (
                    <div id="mastery" className="scroll-mt-32">
                      <MasteryMap />
                    </div>
                  )}

                  <section className="finna-card">
                    <div className="finna-section-top">
                      <div>
                        <h2 className="text-lg">Recent practice log</h2>
                        <p className="mt-0.5 text-xs text-secondary">
                          {todayAnswered} answers recorded today · last 30 days
                        </p>
                      </div>
                      <Link
                        to="/bank"
                        className="text-xs font-bold text-link hover:underline"
                      >
                        Question bank →
                      </Link>
                    </div>
                    {activity.length ? (
                      <div className="finna-prof-log">
                        {activity.slice(0, 12).map((d) => (
                          <div key={d.day} className="finna-prof-log-row">
                            <span className="finna-prof-log-day">
                              {d.day === todayKey
                                ? 'Today'
                                : new Date(`${d.day}T12:00:00`).toLocaleDateString(
                                    'en-IN',
                                    { day: 'numeric', month: 'short' },
                                  )}
                            </span>
                            <span className="finna-prof-log-desc">
                              {d.answered} answered · {d.correct} correct
                            </span>
                            <span className="finna-prof-log-num">
                              {d.answered > 0
                                ? `${Math.round((d.correct / d.answered) * 100)}%`
                                : '0%'}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-secondary">
                        No practice activity yet. Answer a question to start
                        building your study history.
                      </p>
                    )}
                  </section>

                  {scoreSummary && (
                    <section className="finna-card">
                      <div className="finna-section-top">
                        <h2 className="text-lg">Mock &amp; score summary</h2>
                        <Link
                          to="/exams"
                          className="text-xs font-bold text-link hover:underline"
                        >
                          Saved mock results →
                        </Link>
                      </div>
                      <p className="mt-2 text-xs text-secondary">
                        {scoreSummary.profile_basis}
                      </p>
                      <div className="finna-prof-score-strip">
                        <div>
                          <strong>
                            {scoreSummary.mocks_original.completed}
                          </strong>
                          <span>Completed mocks</span>
                        </div>
                        <div>
                          <strong>
                            {scoreSummary.mocks_original.original_marks}
                          </strong>
                          <span>Original marks</span>
                        </div>
                        <div>
                          <strong>
                            {scoreSummary.practice_adjusted.correct}
                          </strong>
                          <span>Assessed correct</span>
                        </div>
                      </div>
                    </section>
                  )}
                </div>

                <aside className="finna-prof-side">
                  <section className="finna-card finna-prof-desk">
                    <div className="finna-st-h1row">
                      <span className="finna-st-badge">Private until joined</span>
                    </div>
                    <h2 className="mt-2 text-lg">Study desk</h2>
                    <p className="mt-1.5 text-sm leading-relaxed text-secondary">
                      Invite friends to a private study desk and share only the
                      focus stats you choose.
                    </p>
                    <Link
                      to="/desk"
                      className="finna-st-btn finna-st-btn--primary mt-3"
                    >
                      Open study desk →
                    </Link>
                  </section>

                  <VaultShowcaseCard compact />

                  <section className="finna-card">
                    <h2 className="text-base">Quick shortcuts</h2>
                    <div className="finna-prof-links">
                      {[
                        ['My Question Vault', '/vault'],
                        ['Revise & mistakes', '/revise?tab=queue'],
                        ['XP & reward wallet', '/profile/rewards'],
                        ['Inbox & updates', '/inbox'],
                        ['My contributions', '/create/submissions'],
                        ['Account settings', '/account/security'],
                        ['Appearance & theme', '/account/appearance'],
                      ].map(([label, href]) => (
                        <Link key={href} to={href} className="finna-prof-link">
                          <span>{label}</span>
                          <span aria-hidden="true">↗</span>
                        </Link>
                      ))}
                    </div>
                  </section>
                </aside>
              </div>
            </div>
          )}

          {tab === 'account' && (
            <div className="finna-prof-stack">
              {isAccount ? (
                <>
                  <AccountTools
                    key={profile.handle}
                    userKey={profile.handle}
                    onEdit={() => {
                      setEditing(true)
                      requestAnimationFrame(() =>
                        document
                          .getElementById('profile-identity-editor')
                          ?.scrollIntoView({ block: 'center' }),
                      )
                    }}
                  />
                  <div className="finna-prof-pair">
                    <ReviewDigestPreference />
                    <ReferralPanel />
                  </div>
                </>
              ) : (
                <section className="finna-card">
                  <h2 className="text-xl">Sync your study account</h2>
                  <p className="mt-2 text-sm text-secondary">
                    Guest progress is stored only in this browser. Create a free
                    account to sync progress across devices, unlock evening
                    review emails, and manage security settings.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link
                      to="/join"
                      className="finna-st-btn finna-st-btn--primary"
                    >
                      Join free →
                    </Link>
                    <Link to="/account/appearance" className="finna-st-btn">
                      Appearance &amp; theme
                    </Link>
                  </div>
                </section>
              )}
            </div>
          )}

          {tab === 'community' && (
            <div className="finna-prof-stack">
              {isAccount && <OwnCommunityStanding />}
              <div className="finna-prof-pair">
                <section className="finna-card">
                  <span className="finna-st-badge">Learning rewards</span>
                  <h2 className="mt-2 text-xl">XP, streaks &amp; Pro days</h2>
                  <p className="mt-1.5 text-sm text-secondary">
                    Track your daily quest rings, weekly league division, and
                    points toward free Pro days.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link
                      to="/profile/rewards"
                      className="finna-st-btn finna-st-btn--primary"
                    >
                      Open rewards wallet →
                    </Link>
                    <Link to="/creators/settings" className="finna-st-btn">
                      Creator visibility
                    </Link>
                  </div>
                </section>

                <section className="finna-card">
                  <span className="finna-st-badge">Contributions</span>
                  <h2 className="mt-2 text-xl">Contribution credit</h2>
                  {!isAccount ? (
                    <p className="mt-2 text-sm text-secondary">
                      Sign in to contribute MCQs and earn publication credit.
                    </p>
                  ) : creditError ? (
                    <p role="alert" className="mt-2 text-sm text-wrong-dark">
                      {creditError}
                    </p>
                  ) : credit === null ? (
                    <p className="mt-2 text-sm text-secondary">
                      Loading publication credit…
                    </p>
                  ) : (
                    <div className="mt-2 text-3xl font-bold">
                      {credit.toLocaleString('en-IN')}
                    </div>
                  )}
                  <p className="mt-2 text-xs text-secondary">
                    25 for a published new MCQ, 10 for a published improvement.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link to="/create/submissions" className="finna-st-btn">
                      My contributions →
                    </Link>
                    <Link to="/community/contributors" className="finna-st-btn">
                      Contributor board
                    </Link>
                  </div>
                </section>
              </div>
            </div>
          )}

          {tab === 'studio' && (
            <div className="finna-prof-pair">
              <section className="finna-card">
                <span className="finna-st-badge">Content studio</span>
                <h2 className="mt-2 text-xl">Your study materials</h2>
                <p className="mt-1.5 text-sm text-secondary">
                  Draft and revise your own study notes, track review status,
                  and open saved materials.
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link
                    to="/studio"
                    className="finna-st-btn finna-st-btn--primary"
                  >
                    My drafts &amp; publications →
                  </Link>
                  <Link to="/materials?saved=true" className="finna-st-btn">
                    Saved materials →
                  </Link>
                </div>
              </section>

              <section className="finna-card">
                <span className="finna-st-badge">Community presence</span>
                <h2 className="mt-2 text-xl">Public creator profile</h2>
                <p className="mt-1.5 text-sm text-secondary">
                  Control whether learners can discover your handle, read your
                  bio, and follow your published work.
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link
                    to="/creators/settings"
                    className="finna-st-btn finna-st-btn--primary"
                  >
                    Creator settings →
                  </Link>
                  <Link to="/creators" className="finna-st-btn">
                    Find creators
                  </Link>
                </div>
              </section>
            </div>
          )}
        </>
      )}
    </main>
  )
}
