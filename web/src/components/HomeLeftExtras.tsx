import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import type { Progress } from '../lib/api'
import type { AvatarLook } from '../lib/avatar'
import AvatarArt, { DEFAULT_HERO_LOOK, UserAvatar } from './AvatarArt'

type BoardTab = 'xp' | 'daily' | 'cup'

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
    tone: 'amber',
  },
  {
    id: 'cup',
    to: '/games?mode=cup',
    title: 'Weekly Cup',
    subtitle: 'Weekend 15-Q MPSC tournament',
    tag: 'Cup',
    tone: 'cobalt',
  },
  {
    id: 'duel',
    to: '/games?mode=duel',
    title: '1v1 Duel & Speed',
    subtitle: 'Live battles & 60-second blitz',
    tag: 'Live',
    tone: 'teal',
  },
] as const

export default function HomeLeftExtras({ progress }: { progress: Progress | null }) {
  const [boardTab, setBoardTab] = useState<BoardTab>('xp')
  const [board, setBoard] = useState<StandingsPayload | null>(null)
  const [boardLoading, setBoardLoading] = useState(true)
  const [boardError, setBoardError] = useState('')

  useEffect(() => {
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
  }, [boardTab])

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

  return (
    <>
      {/* 1. Live Leaderboard Snapshot */}
      <section className="finna-card hl-card" aria-labelledby="home-board-title">
        <div className="finna-section-top">
          <div className="min-w-0">
            <div className="finna-eyebrow">Live standings</div>
            <h2 id="home-board-title">Leaderboard</h2>
          </div>
          <Link to="/profile/rewards" className="text-xs font-bold text-link hover:underline">
            Full board →
          </Link>
        </div>

        <div className="hl-tabs" role="tablist" aria-label="Leaderboard track">
          {(
            [
              ['xp', 'Weekly XP'],
              ['daily', 'Daily Five'],
              ['cup', 'Weekly Cup'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={boardTab === key}
              onClick={() => setBoardTab(key)}
              className={`hl-tab${boardTab === key ? ' is-on' : ''}`}
            >
              {label}
            </button>
          ))}
        </div>

        {board?.league?.name && boardTab === 'xp' && (
          <p className="hl-league-note">{board.league.name}</p>
        )}

        {boardLoading ? (
          <p className="hl-muted">Loading standings…</p>
        ) : boardError ? (
          <p className="hl-muted">
            {boardTab !== 'xp' ? (
              <>
                Sign in to view live {boardTab === 'daily' ? 'Daily Five' : 'Weekly Cup'} ranks.{' '}
                <Link to="/login" className="font-semibold text-link underline">
                  Sign in
                </Link>
              </>
            ) : (
              'Standings temporarily unavailable.'
            )}
          </p>
        ) : topRows.length === 0 ? (
          <p className="hl-muted">
            No public scores yet this week.{' '}
            <Link to="/games?mode=daily" className="font-semibold text-link underline">
              Claim #1 in Daily Five →
            </Link>
          </p>
        ) : (
          <ol className="hl-board-list">
            {topRows.map((row, idx) => {
              const val = (row.xp ?? row.score ?? 0).toLocaleString('en-IN')
              const inner = (
                <>
                  <span className={`hl-rank${row.rank <= 3 ? ` is-top-${row.rank}` : ''}`}>
                    #{row.rank}
                  </span>
                  <UserAvatar look={row.avatar} initials={row.handle} size={30} />
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
          <div className="hl-placement">
            <span>
              {board.placement.public ? 'Your rank' : 'Private rank'} ·{' '}
              <strong>#{board.placement.rank}</strong>
            </span>
            <span className="font-mono text-xs font-bold">
              {(board.placement.xp ?? board.placement.score ?? 0).toLocaleString('en-IN')} {unit}
            </span>
          </div>
        )}
      </section>

      {/* 2. Popular Games (Option B — Left Rail Play Hub) */}
      <section className="finna-card hl-card" aria-labelledby="home-games-title">
        <div className="finna-section-top">
          <div className="min-w-0">
            <div className="finna-eyebrow">Play &amp; compete</div>
            <h2 id="home-games-title">Popular games</h2>
          </div>
          <Link to="/games" className="text-xs font-bold text-link hover:underline">
            All games →
          </Link>
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

      {/* 3. Compact 7-Day Study Pulse & Stats */}
      <section className="finna-card hl-card" aria-labelledby="home-pulse-title">
        <div className="finna-section-top">
          <div className="min-w-0">
            <div className="finna-eyebrow">Your momentum</div>
            <h2 id="home-pulse-title">7-day pulse</h2>
          </div>
          <Link to="/stats" className="text-xs font-bold text-link hover:underline">
            India Stats →
          </Link>
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
    </>
  )
}
