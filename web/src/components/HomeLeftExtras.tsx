import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import { contentRequest } from '../lib/materials'
import type { Progress } from '../lib/api'
import type { AvatarLook } from '../lib/avatar'
import type { HomeWidgetId } from '../lib/homePrefs'
import AvatarArt, { DEFAULT_HERO_LOOK, UserAvatar } from './AvatarArt'

type BoardTab = 'xp' | 'daily' | 'cup'

interface DiscoverLearner {
  id: string
  handle: string
  avatar?: AvatarLook | null
  level: number
  match_reason: string
  weekly_xp?: number | null
}

interface DiscoverMaterial {
  id: string
  title: string
  kind: string
  author: string
  helpful: number
}

interface DiscoverPayload {
  learners: DiscoverLearner[]
  materials: DiscoverMaterial[]
}

interface StandingsRow {
  handle: string
  rank: number
  xp?: number
  score?: number
  avatar?: AvatarLook | null
  level?: number
  profile_public?: boolean
  user_id?: string | null
}

interface StandingsPayload {
  top?: StandingsRow[]
  items?: StandingsRow[]
  placement?: { rank: number; xp?: number; score?: number; public: boolean } | null
  league?: { name: string }
}

const POPULAR_GAMES = [
  {
    id: 'blocks',
    to: '/games/blocks',
    title: 'Finna Blocks',
    subtitle: '8×8 Bank-MCQ Puzzle · Endless & Daily Seed',
    tag: 'Puzzle',
    tone: 'amber',
  },
  {
    id: 'quest',
    to: '/games/quest',
    title: 'Finna Quest',
    subtitle: '16-bit Pixel RPG · Bosses & Daily Gauntlet',
    tag: 'RPG',
    tone: 'rose',
  },
  {
    id: 'daily',
    to: '/games?mode=daily',
    title: 'Daily Five',
    subtitle: '5-question daily ranked sprint',
    tag: 'Daily',
    tone: 'cobalt',
  },
  {
    id: 'cup',
    to: '/games?mode=cup',
    title: 'Weekly Cup',
    subtitle: 'Weekend 15-Q MPSC tournament',
    tag: 'Cup',
    tone: 'teal',
  },
] as const

export default function HomeLeftExtras({
  progress,
  hidden,
  onHide,
  section = 'all',
}: {
  progress: Progress | null
  hidden?: Set<HomeWidgetId>
  onHide?: (id: HomeWidgetId) => void
  section?: 'all' | 'left' | 'community'
}) {
  const showLeaderboard = (section === 'all' || section === 'community') && !hidden?.has('leaderboard')
  const showGames = (section === 'all' || section === 'left') && !hidden?.has('games')
  const showDiscover = (section === 'all' || section === 'community') && !hidden?.has('discover')
  const showPulse = (section === 'all' || section === 'left') && !hidden?.has('pulse')

  const [boardTab, setBoardTab] = useState<BoardTab>('xp')
  const [board, setBoard] = useState<StandingsPayload | null>(null)
  const [boardLoading, setBoardLoading] = useState(true)
  const [boardError, setBoardError] = useState('')
  const [discover, setDiscover] = useState<DiscoverPayload | null>(null)
  const [discoverSeed, setDiscoverSeed] = useState('')
  const [discoverBusy, setDiscoverBusy] = useState(false)

  useEffect(() => {
    if (!showDiscover) return
    let live = true
    setDiscoverBusy(true)
    const qs = discoverSeed ? `?seed=${encodeURIComponent(discoverSeed)}&limit=4` : '?limit=4'
    contentRequest<DiscoverPayload>('/creators/discover' + qs)
      .then((res) => {
        if (live) setDiscover(res)
      })
      .catch(() => {})
      .finally(() => {
        if (live) setDiscoverBusy(false)
      })
    return () => {
      live = false
    }
  }, [discoverSeed, showDiscover])

  useEffect(() => {
    if (!showLeaderboard) return
    let live = true
    setBoardLoading(true)
    setBoardError('')
    const endpoint =
      boardTab === 'xp'
        ? '/rewards/leaderboard'
        : boardTab === 'daily'
          ? '/games/leaderboard?track=daily'
          : '/games/leaderboard?track=cup'
    reviewRequest<StandingsPayload>(endpoint)
      .then((res) => {
        if (live) setBoard(res)
      })
      .catch((err) => {
        if (live) {
          setBoard(null)
          setBoardError(err instanceof Error ? err.message : 'Could not load standings.')
        }
      })
      .finally(() => {
        if (live) setBoardLoading(false)
      })
    return () => {
      live = false
    }
  }, [boardTab, showLeaderboard])

  const topRows = useMemo(() => {
    const raw = board?.top?.length ? board.top : board?.items || []
    return raw.slice(0, 5)
  }, [board])

  const unit = boardTab === 'xp' ? 'XP' : boardTab === 'daily' ? 'd' : 'pts'

  const last7Days = useMemo(() => {
    const byDay = new Map((progress?.daily_activity || []).map((d) => [d.day, d]))
    const out: { day: string; label: string; count: number }[] = []
    const now = new Date()
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now)
      d.setHours(12, 0, 0, 0)
      d.setDate(d.getDate() - i)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      const weekday = d.toLocaleDateString('en-IN', { weekday: 'narrow' })
      out.push({ day: key, label: weekday, count: byDay.get(key)?.answered ?? 0 })
    }
    return out
  }, [progress?.daily_activity])

  const maxDayCount = Math.max(1, ...last7Days.map((d) => d.count))
  const weekTotal = last7Days.reduce((acc, d) => acc + d.count, 0)

  const discoverCard =
    showDiscover && discover && (discover.learners.length > 0 || discover.materials.length > 0) ? (
      <section className="finna-card hl-card" aria-labelledby="home-discover-title">
        <div className="hl-card-head">
          <div className="min-w-0">
            <span className="hl-eyebrow">For you · rotating</span>
            <h2 id="home-discover-title" className="hl-title">Discover</h2>
          </div>
          <div className="finna-card-head-right">
            <button
              type="button"
              disabled={discoverBusy}
              onClick={() => setDiscoverSeed(Date.now().toString(36))}
              className="hl-shuffle-btn"
              title="Shuffle fresh profiles & study notes"
            >
              ↻ {discoverBusy ? '…' : 'Shuffle'}
            </button>
            {onHide && (
              <button
                type="button"
                className="finna-card-hide-btn"
                aria-label="Hide Discover card"
                title="Hide this card"
                onClick={() => onHide('discover')}
              >
                ×
              </button>
            )}
          </div>
        </div>

        {discover.learners.length > 0 && (
          <div className="hl-disc-list" aria-label="Suggested learners">
            {discover.learners.slice(0, 3).map((l) => (
              <Link
                key={l.id}
                to={`/creators/${encodeURIComponent(l.id)}`}
                className="hl-board-row is-link"
              >
                <UserAvatar look={l.avatar} initials={l.handle} size={32} />
                <span className="hl-player">
                  <strong>@{l.handle}</strong>
                  <small>Lv {l.level} · {l.match_reason}</small>
                </span>
                <span aria-hidden="true" className="text-xs text-secondary">↗</span>
              </Link>
            ))}
          </div>
        )}

        {discover.materials.length > 0 && (
          <div className="hl-disc-notes" aria-label="Spotlight study notes">
            {discover.materials.slice(0, 2).map((m) => (
              <Link
                key={m.id}
                to={`/materials/${encodeURIComponent(m.id)}`}
                className="hl-disc-note"
              >
                <span className="hl-disc-kind">{m.kind}</span>
                <strong>{m.title}</strong>
                <small>by {m.author}{m.helpful > 0 ? ` · ${m.helpful} helpful` : ''}</small>
              </Link>
            ))}
          </div>
        )}

        <div className="hl-card-foot">
          <Link to="/creators" className="hl-foot-link is-primary">
            All learners →
          </Link>
          <Link to="/materials" className="hl-foot-link">
            Study notes ↗
          </Link>
        </div>
      </section>
    ) : null

  return (
    <>
      {section === 'community' && discoverCard}
      {/* 1. Live Leaderboard Snapshot */}
      {showLeaderboard && (
      <section className="finna-card hl-card hl-board-card" aria-labelledby="home-board-title">
        <div className="hl-card-head">
          <div className="min-w-0">
            <span className="hl-eyebrow">Live standings</span>
            <h2 id="home-board-title" className="hl-title">Leaderboard</h2>
          </div>
          <div className="finna-card-head-right">
            {onHide && (
              <button
                type="button"
                className="finna-card-hide-btn"
                aria-label="Hide Leaderboard card"
                title="Hide this card"
                onClick={() => onHide('leaderboard')}
              >
                ×
              </button>
            )}
          </div>
        </div>

        <div className="hl-tabs" role="tablist" aria-label="Leaderboard track">
          {(
            [
              ['xp', 'Weekly XP', 'XP'],
              ['daily', 'Daily Five', 'Daily 5'],
              ['cup', 'Weekly Cup', 'Cup'],
            ] as const
          ).map(([key, fullLabel, shortLabel]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-label={fullLabel}
              aria-selected={boardTab === key}
              onClick={() => setBoardTab(key)}
              className={`hl-tab${boardTab === key ? ' is-on' : ''}`}
            >
              {shortLabel}
            </button>
          ))}
        </div>

        {board?.league?.name && boardTab === 'xp' && (
          <div className="hl-league-row">
            <span className="hl-league-pill">
              <span aria-hidden="true">🏅</span>
              <span>{board.league.name}</span>
            </span>
          </div>
        )}

        {boardLoading ? (
          <div className="hl-empty-box">
            <p className="hl-empty-copy">Loading standings…</p>
          </div>
        ) : boardError ? (
          <div className="hl-empty-box">
            <p className="hl-empty-copy">
              {boardTab !== 'xp'
                ? `Sign in to view live ${boardTab === 'daily' ? 'Daily Five' : 'Weekly Cup'} ranks.`
                : 'Standings temporarily unavailable.'}
            </p>
            {boardTab !== 'xp' && (
              <Link to="/login" className="hl-empty-cta">
                Sign in →
              </Link>
            )}
          </div>
        ) : topRows.length === 0 ? (
          <div className="hl-empty-box">
            <p className="hl-empty-copy">
              No public scores yet this week. Be the first on the board!
            </p>
            <Link
              to={boardTab === 'cup' ? '/games?mode=cup' : '/games?mode=daily'}
              className="hl-empty-cta"
            >
              {boardTab === 'cup' ? 'Play Weekly Cup →' : 'Claim #1 in Daily Five →'}
            </Link>
          </div>
        ) : (
          <ol className="hl-board-list">
            {topRows.map((row, idx) => {
              const val = (row.xp ?? row.score ?? 0).toLocaleString('en-IN')
              const inner = (
                <>
                  <span className={`hl-rank${row.rank <= 3 ? ` is-top-${row.rank}` : ''}`}>
                    #{row.rank}
                  </span>
                  <UserAvatar look={row.avatar} initials={row.handle} size={28} />
                  <span className="hl-player">
                    <strong>{row.handle}</strong>
                    {row.level != null && <small>Lv {row.level}</small>}
                  </span>
                  <span className="hl-score">
                    {val} {unit}
                  </span>
                </>
              )
              return (
                <li key={(row.user_id || row.handle) + '-' + idx}>
                  {row.user_id ? (
                    <Link
                      to={`/creators/${encodeURIComponent(row.user_id)}`}
                      className="hl-board-row is-link"
                    >
                      {inner}
                    </Link>
                  ) : (
                    <div className="hl-board-row">{inner}</div>
                  )}
                </li>
              )
            })}
          </ol>
        )}

        {board?.placement && (
          <Link to="/profile/rewards" className="hl-placement">
            <span className="hl-placement-left">
              <span className="hl-placement-rank">#{board.placement.rank}</span>
              <span className="hl-placement-meta">
                <strong>Your rank</strong>
                <small>{board.placement.public ? 'Public board' : 'Private · opt in anytime'}</small>
              </span>
            </span>
            <span className="hl-placement-val">
              {(board.placement.xp ?? board.placement.score ?? 0).toLocaleString('en-IN')} {unit}
            </span>
          </Link>
        )}

        <div className="hl-card-foot">
          <Link to="/creators" className="hl-foot-link is-primary">
            Find learners →
          </Link>
          <Link to="/profile/rewards" className="hl-foot-link">
            Full board ↗
          </Link>
        </div>
      </section>
      )}

      {/* 2. Popular Games (Option B — Left Rail Play Hub) */}
      {showGames && (
      <section className="finna-card hl-card" aria-labelledby="home-games-title">
        <div className="finna-section-top">
          <div className="min-w-0">
            <div className="finna-eyebrow">Play &amp; compete</div>
            <h2 id="home-games-title">Popular games</h2>
          </div>
          <div className="finna-card-head-right">
            <Link to="/games" className="text-xs font-bold text-link hover:underline">
              All games →
            </Link>
            {onHide && (
              <button
                type="button"
                className="finna-card-hide-btn"
                aria-label="Hide Popular games card"
                title="Hide this card"
                onClick={() => onHide('games')}
              >
                ×
              </button>
            )}
          </div>
        </div>

        <div className="hl-games-list">
          {POPULAR_GAMES.map((g) => (
            <Link key={g.id} to={g.to} className={`hl-game-row is-${g.tone}`}>
              <span className="hl-game-ico" aria-hidden="true">
                {g.id === 'quest' ? (
                  <AvatarArt look={DEFAULT_HERO_LOOK} size={32} />
                ) : g.id === 'daily' ? (
                  '☀'
                ) : g.id === 'cup' ? (
                  '🏆'
                ) : (
                  '⚡'
                )}
              </span>
              <span className="hl-game-copy">
                <strong>{g.title}</strong>
                <small>{g.subtitle}</small>
              </span>
              <span className="hl-game-tag">{g.tag}</span>
            </Link>
          ))}
        </div>
      </section>
      )}

      {/* 3. Algorithmic Discover: Rotating Learners & Study Notes */}
      {section !== 'community' && discoverCard}

      {/* 4. Compact 7-Day Study Pulse & Stats */}
      {showPulse && (
      <section className="finna-card hl-card" aria-labelledby="home-pulse-title">
        <div className="finna-section-top">
          <div className="min-w-0">
            <div className="finna-eyebrow">Your momentum</div>
            <h2 id="home-pulse-title">7-day pulse</h2>
          </div>
          <div className="finna-card-head-right">
            <Link to="/stats" className="text-xs font-bold text-link hover:underline">
              India Stats →
            </Link>
            {onHide && (
              <button
                type="button"
                className="finna-card-hide-btn"
                aria-label="Hide 7-day pulse card"
                title="Hide this card"
                onClick={() => onHide('pulse')}
              >
                ×
              </button>
            )}
          </div>
        </div>

        <div className="hl-pulse-bars" aria-label="Answers recorded over the last 7 days">
          {last7Days.map((d) => {
            const pct = d.count > 0 ? Math.max(18, Math.round((d.count / maxDayCount) * 100)) : 8
            return (
              <div key={d.day} className="hl-bar-col" title={`${d.day}: ${d.count} answers`}>
                <div className="hl-bar-track">
                  <span
                    className={`hl-bar-fill${d.count > 0 ? ' is-active' : ''}`}
                    style={{ height: `${pct}%` }}
                  />
                </div>
                <span className="hl-bar-lbl">{d.label}</span>
              </div>
            )
          })}
        </div>

        <div className="hl-pulse-stats">
          <div>
            <strong>{weekTotal.toLocaleString('en-IN')}</strong>
            <small>this week</small>
          </div>
          <div>
            <strong>{progress && progress.answered > 0 ? `${Math.round(progress.accuracy)}%` : '—'}</strong>
            <small>accuracy</small>
          </div>
          <div>
            <strong>{progress ? `${progress.current_streak}d` : '0d'}</strong>
            <small>streak</small>
          </div>
        </div>

        <div className="hl-pulse-foot">
          <Link to="/profile" className="text-xs font-bold text-link hover:underline">
            Full mastery &amp; progress →
          </Link>
          <Link to="/stats" className="text-xs font-semibold text-secondary hover:text-ink">
            Mizoram &amp; India data ↗
          </Link>
        </div>
      </section>
      )}
    </>
  )
}
