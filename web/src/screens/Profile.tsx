import { OwnCommunityStanding } from '../components/ContributorStanding'
import AccountTools from '../components/AccountTools'
import ReviewDigestPreference from '../components/ReviewDigestPreference'
import ReferralPanel from '../components/ReferralPanel'
import IdentityEditor from '../components/IdentityEditor'
import MasteryMap from '../components/MasteryMap'
import StudyAnalyticsDeck from '../components/StudyAnalyticsDeck'
import VaultShowcaseCard from '../components/VaultShowcaseCard'
import { CatLoader, CatXpBar } from '../components/CatLoader'
import { UserAvatar } from '../components/AvatarArt'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  getProfile,
  getScoreSummary,
  logoutAccount,
  updateProfile,
  type PrivateProfile,
  type ScoreSummary,
} from '../lib/api'
import { reviewRequest } from '../lib/review'

type ProfileTab = 'overview' | 'mastery' | 'account' | 'community' | 'studio'

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
  const navigate = useNavigate()
  const [profile, setProfile] = useState<PrivateProfile | null>(null)
  const [name, setName] = useState('')
  const [learnerQuery, setLearnerQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [editing, setEditing] = useState(false)
  const [scoreSummary, setScoreSummary] = useState<ScoreSummary | null>(null)
  const [credit, setCredit] = useState<number | null>(null)
  const [creditError, setCreditError] = useState('')
  const [walletXp, setWalletXp] = useState<{ xp: number; floor?: number; next?: number; league?: string } | null>(null)
  const [tab, setTab] = useState<ProfileTab>(() =>
    location.hash === '#account-tools-title'
      ? 'account'
      : location.hash === '#mastery'
        ? 'mastery'
        : 'overview',
  )

  useEffect(() => {
    if (location.hash === '#account-tools-title') setTab('account')
    else if (location.hash === '#mastery') setTab('mastery')
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
      reviewRequest<{ lifetime_xp?: number; level_floor_xp?: number; next_level_xp?: number; league?: { name?: string } }>('/rewards/me')
        .then((r) => {
          if (run === generation && typeof r.lifetime_xp === 'number') {
            setWalletXp({
              xp: r.lifetime_xp,
              floor: r.level_floor_xp,
              next: r.next_level_xp,
              league: r.league?.name,
            })
          }
        })
        .catch(() => {
          if (run === generation) setWalletXp(null)
        })
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
    { id: 'mastery', label: 'Mastery & log' },
    { id: 'community', label: 'Rewards & community' },
    { id: 'account', label: 'Account & setup' },
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
        <div className="finna-card flex justify-center py-10">
          <CatLoader size="md" label="Loading your profile…" />
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
                {walletXp && (() => {
                  const lvl = Math.max(1, profile.level)
                  const floorXp = walletXp.floor ?? (lvl <= 1 ? 0 : lvl * lvl * 40)
                  const nextXp = walletXp.next ?? (lvl + 1) * (lvl + 1) * 40
                  const inLevel = Math.max(0, walletXp.xp - floorXp)
                  const span = Math.max(40, nextXp - floorXp)
                  return (
                    <CatXpBar
                      value={inLevel}
                      max={span}
                      tone="xp"
                      label={`Level ${lvl} → Level ${lvl + 1}${walletXp.league ? ` · ${walletXp.league}` : ''}`}
                      meta={`${walletXp.xp.toLocaleString('en-IN')} / ${nextXp.toLocaleString('en-IN')} XP`}
                      className="mt-3 max-w-md"
                    />
                  )
                })()}
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
              <Link to="/creators" className="finna-st-btn">
                🔎 Find learners
              </Link>
              <Link to="/creators/settings" className="finna-st-btn">
                Public visibility
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
                      <div className="finna-prof-score-strip mt-3">
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

                  <section className="finna-card">
                    <div className="finna-section-top">
                      <div>
                        <h2 className="text-lg">Recent activity</h2>
                        <p className="mt-0.5 text-xs text-secondary">
                          {todayAnswered} answers today · {activity.length} active days in last 30d
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setTab('mastery')}
                        className="text-xs font-bold text-link hover:underline"
                      >
                        Full Mastery &amp; Log →
                      </button>
                    </div>
                    {activity.length ? (
                      <div className="finna-prof-log">
                        {activity.slice(0, 5).map((d) => (
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
                </div>

                <aside className="finna-prof-side">
                  {/* Direct Profile Finder Card */}
                  <section className="finna-card pf-finder" aria-labelledby="pf-finder-title">
                    <div className="finna-section-top">
                      <h2 id="pf-finder-title" className="text-base">Find learner profiles</h2>
                      <Link to="/creators" className="text-xs font-bold text-link hover:underline">
                        Browse all →
                      </Link>
                    </div>
                    <p className="mt-1 text-xs text-secondary">
                      Search by @handle to see another learner’s pixel hero, target exams, scores &amp; notes.
                    </p>
                    <form
                      className="pf-finder-form"
                      onSubmit={(e) => {
                        e.preventDefault()
                        const q = learnerQuery.trim()
                        navigate(q ? `/creators?q=${encodeURIComponent(q)}` : '/creators')
                      }}
                    >
                      <input
                        type="search"
                        value={learnerQuery}
                        onChange={(e) => setLearnerQuery(e.target.value)}
                        placeholder="Search @handle…"
                        aria-label="Search learner handle"
                        maxLength={80}
                      />
                      <button type="submit">Find</button>
                    </form>
                    <div className="pf-finder-links">
                      <Link to="/profile/rewards" className="text-xs font-semibold text-link hover:underline">
                        🏆 Weekly standings
                      </Link>
                      <Link to="/creators/settings" className="text-xs font-semibold text-secondary hover:text-ink">
                        My public visibility
                      </Link>
                    </div>
                  </section>

                  <VaultShowcaseCard compact />

                  <section className="finna-card">
                    <h2 className="text-base">Quick shortcuts</h2>
                    <div className="finna-prof-links">
                      {[
                        ['Study desk & rooms', '/desk'],
                        ['My Question Vault', '/vault'],
                        ['Revise & mistakes', '/revise?tab=queue'],
                        ['XP & reward wallet', '/profile/rewards'],
                        ['Account & security', '/account/security'],
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

          {tab === 'mastery' && (
            <div className="finna-prof-stack">
              {isAccount ? (
                <div id="mastery" className="scroll-mt-32">
                  <MasteryMap />
                </div>
              ) : (
                <section className="finna-card">
                  <h2 className="text-lg">Topic mastery</h2>
                  <p className="mt-1.5 text-sm text-secondary">
                    Sign in to track verified topic mastery and rusty-topic alerts across your target exams.
                  </p>
                  <Link to="/join" className="finna-st-btn finna-st-btn--primary mt-3">
                    Join free →
                  </Link>
                </section>
              )}

              <section className="finna-card">
                <div className="finna-section-top">
                  <div>
                    <h2 className="text-lg">30-day practice log</h2>
                    <p className="mt-0.5 text-xs text-secondary">
                      {todayAnswered} answers recorded today · {activity.length} active days
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
                    {activity.map((d) => (
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
                    No practice activity yet. Answer a question to start building your study history.
                  </p>
                )}
              </section>
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
