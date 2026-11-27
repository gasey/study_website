import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import type { AvatarLook } from '../lib/avatar'
import AvatarArt from '../components/AvatarArt'
import { CatLoader } from '../components/CatLoader'

type BoardTabId = 'xp' | 'daily' | 'cup' | 'blocks' | 'speed' | 'gauntlet' | 'duel'
type BlocksPeriod = 'week' | 'daily' | 'all'

interface BoardMeta {
  id: BoardTabId
  label: string
  shortLabel: string
  kicker: string
  subtitle: string
  unit: string
  playTo: string
  playLabel: string
}

const BOARDS: readonly BoardMeta[] = [
  {
    id: 'xp',
    label: 'Weekly XP',
    shortLabel: 'Weekly XP',
    kicker: 'WEEKLY XP DIVISION',
    subtitle: 'Earned from verified practice, mocks, reviews, and games this India week.',
    unit: 'XP',
    playTo: '/practice',
    playLabel: 'Start practicing →',
  },
  {
    id: 'daily',
    label: 'Daily Five',
    shortLabel: 'Daily Five',
    kicker: 'DAILY FIVE STREAK',
    subtitle: 'Consecutive completed 5-question Daily Five sprints inside this IST week.',
    unit: 'd',
    playTo: '/games?mode=daily',
    playLabel: 'Play Daily Five →',
  },
  {
    id: 'cup',
    label: 'Weekly Cup',
    shortLabel: 'Weekly Cup',
    kicker: 'WEEKEND TOURNAMENT',
    subtitle: 'Best timed 15-question Weekly Cup score in the current cup window.',
    unit: 'pts',
    playTo: '/games?mode=cup',
    playLabel: 'Enter Weekly Cup →',
  },
  {
    id: 'blocks',
    label: 'Finna Blocks',
    shortLabel: 'Blocks',
    kicker: '8×8 MCQ PUZZLE',
    subtitle: 'Highest verified Finna Blocks score — clear lines and answer MCQs to keep your run alive.',
    unit: 'pts',
    playTo: '/games/blocks',
    playLabel: 'Play Finna Blocks →',
  },
  {
    id: 'speed',
    label: 'Speed Sprint',
    shortLabel: 'Speed',
    kicker: '60-SECOND BLITZ',
    subtitle: 'Top single-run Speed Sprint score recorded this week.',
    unit: 'pts',
    playTo: '/games?mode=speed',
    playLabel: 'Play Speed Sprint →',
  },
  {
    id: 'gauntlet',
    label: 'Gauntlet',
    shortLabel: 'Gauntlet',
    kicker: '20-GATE SURVIVAL',
    subtitle: 'Highest 3-life Gauntlet survival run recorded this week.',
    unit: 'pts',
    playTo: '/games?mode=gauntlet',
    playLabel: 'Play Gauntlet →',
  },
  {
    id: 'duel',
    label: '1v1 Duels',
    shortLabel: 'Duels',
    kicker: 'HEAD-TO-HEAD WINS',
    subtitle: 'Completed 1v1 duel victories won against live opponents this week.',
    unit: 'wins',
    playTo: '/games?mode=duel',
    playLabel: 'Start a Duel →',
  },
] as const

const VALID_TABS = new Set<string>(BOARDS.map((b) => b.id))

interface StandingsRow {
  handle: string
  rank: number
  xp?: number
  score?: number
  avatar?: AvatarLook | null
  level?: number
  profile_public?: boolean
  user_id?: string | null
  lines_cleared?: number
  questions_correct?: number
  best_streak?: number
}

interface StandingsResponse {
  top?: StandingsRow[]
  nearby?: StandingsRow[]
  items?: StandingsRow[]
  total?: number
  placement?: {
    rank: number
    xp?: number
    score?: number
    public: boolean
    lines_cleared?: number
    questions_correct?: number
  } | null
  league?: { name: string; floor_xp?: number; next_xp?: number | null }
  period_start?: string | null
  period_end?: string | null
  today_ist?: string
  neighborhood_truncated?: boolean
}

interface ViewerWallet {
  public: boolean
  weekly_xp?: number
  lifetime_xp?: number
  level?: number
  league?: { name: string; floor_xp: number; next_xp: number | null; xp_to_promote: number }
}

function handleInitials(handle: string): string {
  const clean = handle.replace(/^@+/, '').trim()
  const parts = clean.split(/[._\-\s]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return clean.slice(0, 2).toUpperCase() || 'FN'
}

function BoardAvatar({
  look,
  handle,
  size,
  className,
  borderColor,
}: {
  look?: AvatarLook | null
  handle: string
  size: number
  className: string
  borderColor?: string
}) {
  return (
    <span
      className={className}
      style={{
        width: size,
        height: size,
        ...(borderColor ? { borderColor } : {}),
      }}
    >
      {look ? (
        <AvatarArt look={look} size={Math.max(20, borderColor ? size - 4 : size)} />
      ) : (
        handleInitials(handle)
      )}
    </span>
  )
}

function rowValue(row: { xp?: number; score?: number }): number {
  return row.xp ?? row.score ?? 0
}

function formatScore(val: number, unit: string): string {
  if (unit === 'd') return `${val.toLocaleString('en-IN')}d`
  return `${val.toLocaleString('en-IN')} ${unit}`
}

function formatWindow(data: StandingsResponse | null, tab: BoardTabId, blocksPeriod: BlocksPeriod): string {
  if (tab === 'blocks') {
    if (blocksPeriod === 'daily') return data?.today_ist ? `Daily board · ${data.today_ist} IST` : 'Today · India time'
    if (blocksPeriod === 'all') return 'All-time verified high scores'
    return 'This India week · resets Monday IST'
  }
  if (data?.period_start && data?.period_end) {
    const start = new Date(data.period_start).toLocaleDateString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
    })
    const end = new Date(Date.parse(data.period_end) - 1).toLocaleDateString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
    })
    return `${start} – ${end} · India time`
  }
  return 'Current India week · resets Monday IST'
}

export default function Leaderboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab') || 'xp'
  const tab: BoardTabId = VALID_TABS.has(rawTab) ? (rawTab as BoardTabId) : 'xp'
  const [blocksPeriod, setBlocksPeriod] = useState<BlocksPeriod>('week')

  const [board, setBoard] = useState<StandingsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshTick, setRefreshTick] = useState(0)

  const [wallet, setWallet] = useState<ViewerWallet | null>(null)
  const [walletChecked, setWalletChecked] = useState(false)
  const [visBusy, setVisBusy] = useState(false)
  const [visNotice, setVisNotice] = useState('')

  const activeBoard = useMemo(() => BOARDS.find((b) => b.id === tab) || BOARDS[0], [tab])

  const loadWallet = useCallback(() => {
    let live = true
    reviewRequest<ViewerWallet>('/rewards/me')
      .then((res) => {
        if (live) {
          setWallet(res)
          setWalletChecked(true)
        }
      })
      .catch(() => {
        if (live) {
          setWallet(null)
          setWalletChecked(true)
        }
      })
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    const cleanup = loadWallet()
    const onAuth = () => {
      loadWallet()
      setRefreshTick((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', onAuth)
    window.addEventListener('ism-community-standing-change', onAuth)
    return () => {
      cleanup()
      window.removeEventListener('ism-auth-change', onAuth)
      window.removeEventListener('ism-community-standing-change', onAuth)
    }
  }, [loadWallet])

  useEffect(() => {
    let live = true
    setLoading(true)
    setError('')
    const endpoint =
      tab === 'xp'
        ? '/rewards/leaderboard?contract=2'
        : tab === 'blocks'
          ? `/blocks/leaderboard?period=${blocksPeriod}&limit=20`
          : `/games/leaderboard?contract=2&track=${tab}`
    reviewRequest<StandingsResponse>(endpoint)
      .then((res) => {
        if (live) setBoard(res)
      })
      .catch((err) => {
        if (live) {
          setBoard(null)
          setError(err instanceof Error ? err.message : 'Could not load standings right now.')
        }
      })
      .finally(() => {
        if (live) setLoading(false)
      })
    return () => {
      live = false
    }
  }, [tab, blocksPeriod, refreshTick])

  async function toggleVisibility() {
    if (!wallet || visBusy) return
    setVisBusy(true)
    setVisNotice('')
    try {
      const next = !wallet.public
      await reviewRequest('/rewards/visibility', { public: next })
      setWallet((w) => (w ? { ...w, public: next } : w))
      setVisNotice(
        next
          ? 'You are now live on the public leaderboards.'
          : 'Your handle and scores are now hidden from public boards.',
      )
      window.dispatchEvent(new Event('ism-community-standing-change'))
      setRefreshTick((n) => n + 1)
    } catch (err) {
      setVisNotice(err instanceof Error ? err.message : 'Could not update visibility.')
    } finally {
      setVisBusy(false)
    }
  }

  function selectTab(next: BoardTabId) {
    setSearchParams(next === 'xp' ? {} : { tab: next }, { replace: true })
  }

  const rows = useMemo(() => {
    if (!board) return []
    return board.top?.length ? board.top : board.items || []
  }, [board])

  const nearbyExtra = useMemo(() => {
    if (!board?.nearby?.length) return []
    const topHandles = new Set(rows.map((r) => r.handle))
    const hasExtra = board.nearby.some((r) => !topHandles.has(r.handle))
    return hasExtra ? board.nearby : []
  }, [board, rows])

  const podiumSlots = useMemo(() => {
    const top3 = rows.slice(0, 3)
    return [
      { row: top3[1] ?? null, rank: 2, size: 46, ring: '#A9BCFF', h: 62, bg: '#E0E7FF' },
      { row: top3[0] ?? null, rank: 1, size: 58, ring: '#FFC83D', h: 86, bg: '#FFC83D' },
      { row: top3[2] ?? null, rank: 3, size: 42, ring: '#FB923C', h: 48, bg: '#FED7AA' },
    ] as {
      row: StandingsRow | null
      rank: number
      size: number
      ring: string
      h: number
      bg: string
    }[]
  }, [rows])

  const placement = board?.placement || null
  const myScore = placement ? rowValue(placement) : 0
  const aboveRow =
    placement && placement.rank > 1
      ? [...rows, ...(board?.nearby || [])].find((r) => r.rank === placement.rank - 1)
      : undefined
  const gapToNext =
    aboveRow && rowValue(aboveRow) > myScore ? rowValue(aboveRow) - myScore : null

  const leagueLabel =
    tab === 'xp' ? board?.league?.name || wallet?.league?.name || 'Weekly League' : activeBoard.label

  function renderStandingRows(list: StandingsRow[]) {
    return (
      <ol className="finna-lb-list">
        {list.map((row, idx) => {
          const val = rowValue(row)
          const medalCls =
            row.rank === 1
              ? 'is-gold'
              : row.rank === 2
                ? 'is-silver'
                : row.rank === 3
                  ? 'is-bronze'
                  : ''
          const inner = (
            <>
              <span className={`finna-lb-rank ${medalCls}`}>#{row.rank}</span>
              <BoardAvatar
                look={row.avatar}
                handle={row.handle}
                size={36}
                className="finna-podium-row-av"
              />
              <span className="finna-lb-player">
                <strong>
                  @{row.handle}
                  {row.user_id && row.profile_public !== false && (
                    <span className="finna-lb-ext" aria-hidden="true">
                      {' '}
                      ↗
                    </span>
                  )}
                </strong>
                <small>
                  {row.level != null ? `Lv ${row.level}` : 'Finna learner'}
                  {tab === 'blocks' && row.lines_cleared != null
                    ? ` · ${row.lines_cleared} lines · ${row.questions_correct ?? 0} Qs`
                    : ''}
                </small>
              </span>
              <span className="finna-lb-score">{formatScore(val, activeBoard.unit)}</span>
            </>
          )
          return (
            <li key={`${row.user_id || row.handle}-${row.rank}-${idx}`}>
              {row.user_id && row.profile_public !== false ? (
                <Link
                  to={`/creators/${encodeURIComponent(row.user_id)}`}
                  className="finna-lb-row is-link"
                >
                  {inner}
                </Link>
              ) : (
                <div className="finna-lb-row">{inner}</div>
              )}
            </li>
          )
        })}
      </ol>
    )
  }

  return (
    <main className="finna-lb-page">
      {/* 1. Midnight Navy Podium Hero */}
      <section className="finna-lb-hero" aria-labelledby="finna-lb-heading">
        <div className="finna-lb-hero-top">
          <div className="finna-lb-hero-copy">
            <span className="finna-podium-kicker">
              LIVE STANDINGS · {tab === 'xp' ? leagueLabel : activeBoard.kicker}
            </span>
            <h1 id="finna-lb-heading" className="finna-lb-title">
              {tab === 'xp' ? 'Weekly leaderboard' : `${activeBoard.label} leaderboard`}
            </h1>
            <p className="finna-lb-sub">
              {activeBoard.subtitle}
              <span className="finna-lb-window"> · {formatWindow(board, tab, blocksPeriod)}</span>
            </p>
          </div>

          <div className="finna-lb-hero-actions">
            {wallet ? (
              <button
                type="button"
                disabled={visBusy}
                onClick={() => void toggleVisibility()}
                className={`finna-lb-vis-btn${wallet.public ? ' is-public' : ''}`}
              >
                <span className="finna-lb-vis-dot" aria-hidden="true" />
                {visBusy
                  ? 'Saving…'
                  : wallet.public
                    ? 'Public on board'
                    : 'Private · Join board'}
              </button>
            ) : walletChecked ? (
              <Link to="/login" className="finna-lb-vis-btn is-cta">
                Sign in to join →
              </Link>
            ) : null}
            <Link to="/profile/rewards" className="finna-lb-ghost-btn">
              Rewards &amp; quests →
            </Link>
          </div>
        </div>

        {visNotice && (
          <div className="finna-lb-notice" role="status">
            {visNotice}
          </div>
        )}

        {/* Top-3 Podium Stage */}
        {loading ? (
          <div className="finna-lb-podium-empty">
            <span>Loading live podium…</span>
          </div>
        ) : rows.length > 0 ? (
          <div className="finna-lb-podium-stage" aria-label="Top three learners">
            {podiumSlots.map((p) => {
              if (!p.row) {
                return (
                  <div key={`empty-${p.rank}`} className="finna-podium-col">
                    <span
                      className="finna-podium-av is-empty"
                      style={{ width: p.size, height: p.size, borderColor: p.ring }}
                    >
                      —
                    </span>
                    <span className="finna-podium-handle is-empty">Open seat</span>
                    <div
                      className="finna-podium-block finna-lb-podium-block is-empty"
                      style={{ height: p.h }}
                    >
                      <strong>#{p.rank}</strong>
                      <span>—</span>
                    </div>
                  </div>
                )
              }
              const inner = (
                <>
                  <BoardAvatar
                    look={p.row.avatar}
                    handle={p.row.handle}
                    size={p.size}
                    borderColor={p.ring}
                    className="finna-podium-av"
                  />
                  <span className="finna-podium-handle">@{p.row.handle}</span>
                  {p.row.level != null && (
                    <span className="finna-lb-podium-lv">Lv {p.row.level}</span>
                  )}
                  <div
                    className="finna-podium-block finna-lb-podium-block"
                    style={{ height: p.h, background: p.bg }}
                  >
                    <strong>#{p.rank}</strong>
                    <span>{formatScore(rowValue(p.row), activeBoard.unit)}</span>
                  </div>
                </>
              )
              return p.row.user_id && p.row.profile_public !== false ? (
                <Link
                  key={`${p.rank}-${p.row.handle}`}
                  to={`/creators/${encodeURIComponent(p.row.user_id)}`}
                  className="finna-podium-col"
                >
                  {inner}
                </Link>
              ) : (
                <div key={`${p.rank}-${p.row.handle}`} className="finna-podium-col">
                  {inner}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="finna-lb-podium-empty">
            <div>
              <strong>No public scores on {activeBoard.label} yet this week.</strong>
              <p>
                {wallet && !wallet.public
                  ? 'Your board visibility is currently private — opt in or record a run to claim #1.'
                  : 'Complete a verified set or game run to claim #1 on the podium.'}
              </p>
            </div>
            <div className="finna-lb-empty-actions">
              <Link to={activeBoard.playTo} className="finna-lb-gold-btn">
                {activeBoard.playLabel}
              </Link>
              {wallet && !wallet.public && (
                <button
                  type="button"
                  disabled={visBusy}
                  onClick={() => void toggleVisibility()}
                  className="finna-lb-ghost-btn"
                >
                  Join public board
                </button>
              )}
            </div>
          </div>
        )}
      </section>

      {/* 2. Board Switcher Tabs */}
      <div className="finna-lb-controls">
        <div className="finna-lb-tabs" role="tablist" aria-label="Choose leaderboard">
          {BOARDS.map((b) => {
            const active = b.id === tab
            return (
              <button
                key={b.id}
                type="button"
                role="tab"
                aria-selected={active}
                className={`finna-lb-tab${active ? ' is-active' : ''}`}
                onClick={() => selectTab(b.id)}
              >
                {b.label}
              </button>
            )
          })}
        </div>

        {tab === 'blocks' && (
          <div className="finna-lb-subpills" role="group" aria-label="Finna Blocks timeframe">
            {(
              [
                ['week', 'This week'],
                ['daily', 'Daily board'],
                ['all', 'All time'],
              ] as const
            ).map(([p, label]) => (
              <button
                key={p}
                type="button"
                aria-pressed={blocksPeriod === p}
                className={`finna-lb-subpill${blocksPeriod === p ? ' is-active' : ''}`}
                onClick={() => setBlocksPeriod(p)}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 3. Your Placement Strip */}
      <section className="finna-lb-placement" aria-label="Your standing">
        {placement ? (
          <>
            <div className="finna-lb-placement-left">
              <span className="finna-lb-placement-rank">#{placement.rank}</span>
              <div>
                <strong>
                  {placement.public ? 'Your live rank' : 'Your private placement'} ·{' '}
                  {formatScore(myScore, activeBoard.unit)}
                </strong>
                <p>
                  {placement.public
                    ? gapToNext !== null
                      ? `${formatScore(gapToNext, activeBoard.unit)} behind #${placement.rank - 1}.`
                      : placement.rank === 1
                        ? 'You are leading the board right now!'
                        : 'Your handle and score are visible on the public board.'
                    : 'Only you can see this rank. Opt in anytime to appear publicly.'}
                </p>
              </div>
            </div>
            <div className="finna-lb-placement-actions">
              {!placement.public && wallet && (
                <button
                  type="button"
                  disabled={visBusy}
                  onClick={() => void toggleVisibility()}
                  className="finna-lb-primary-btn"
                >
                  Appear on public board
                </button>
              )}
              <Link to={activeBoard.playTo} className="finna-lb-secondary-btn">
                {activeBoard.playLabel}
              </Link>
            </div>
          </>
        ) : wallet ? (
          <>
            <div className="finna-lb-placement-left">
              <span className="finna-lb-placement-rank">—</span>
              <div>
                <strong>No score recorded on {activeBoard.label} yet</strong>
                <p>
                  {tab === 'xp' && wallet.league
                    ? `${wallet.league.name} · ${wallet.weekly_xp ?? 0} XP this week${wallet.league.next_xp ? ` · ${wallet.league.xp_to_promote} XP to promote` : ''}`
                    : 'Record your first verified activity this week to get placed.'}
                </p>
              </div>
            </div>
            <Link to={activeBoard.playTo} className="finna-lb-primary-btn">
              {activeBoard.playLabel}
            </Link>
          </>
        ) : (
          <>
            <div className="finna-lb-placement-left">
              <span className="finna-lb-placement-rank">★</span>
              <div>
                <strong>Track your rank &amp; weekly division</strong>
                <p>
                  Sign in for free to earn verified XP, unlock daily quest rings, and opt into
                  public standings whenever you choose.
                </p>
              </div>
            </div>
            <Link to="/login" className="finna-lb-primary-btn">
              Sign in or join →
            </Link>
          </>
        )}
      </section>

      {/* 4. Main Standings Grid */}
      <div className="finna-lb-grid">
        <section className="finna-card finna-lb-card" aria-labelledby="finna-lb-list-title">
          <div className="finna-lb-card-head">
            <div>
              <div className="finna-eyebrow">
                {tab === 'xp' ? leagueLabel : activeBoard.kicker}
              </div>
              <h2 id="finna-lb-list-title" className="finna-lb-card-title">
                Top standings
              </h2>
            </div>
            {typeof board?.total === 'number' && board.total > 0 && (
              <span className="finna-lb-count">
                {board.total.toLocaleString('en-IN')} ranked
              </span>
            )}
          </div>

          {loading ? (
            <div className="py-10 flex justify-center">
              <CatLoader size="md" label={`Loading ${activeBoard.label} standings…`} />
            </div>
          ) : error ? (
            <div className="finna-lb-error" role="alert">
              <p>{error}</p>
              <button
                type="button"
                className="finna-lb-secondary-btn"
                onClick={() => setRefreshTick((n) => n + 1)}
              >
                Try again
              </button>
            </div>
          ) : rows.length > 0 ? (
            renderStandingRows(rows)
          ) : (
            <div className="finna-lb-empty-body">
              <p>No public scores recorded for {activeBoard.label} in this window yet.</p>
              <Link to={activeBoard.playTo} className="finna-lb-primary-btn">
                {activeBoard.playLabel}
              </Link>
            </div>
          )}
        </section>

        <aside className="finna-lb-side">
          {nearbyExtra.length > 0 && (
            <section className="finna-card finna-lb-card" aria-labelledby="finna-lb-nearby-title">
              <div className="finna-lb-card-head">
                <div>
                  <div className="finna-eyebrow">Around your rank</div>
                  <h2 id="finna-lb-nearby-title" className="finna-lb-card-title">
                    Nearby learners
                  </h2>
                </div>
              </div>
              {renderStandingRows(nearbyExtra)}
              {board?.neighborhood_truncated && (
                <p className="finna-lb-foot-note">
                  Several learners share these ranks. Showing up to 25 nearby learners.
                </p>
              )}
            </section>
          )}

          <section className="finna-card finna-lb-card" aria-labelledby="finna-lb-rules-title">
            <div className="finna-eyebrow">Fair play &amp; privacy</div>
            <h2 id="finna-lb-rules-title" className="finna-lb-card-title">
              How standings work
            </h2>
            <ul className="finna-lb-rules">
              <li>
                <strong>Opt-in by default.</strong> Your scores stay private until you choose to
                appear on public boards.
              </li>
              <li>
                <strong>India week reset.</strong> Weekly XP and game boards reset every Monday at
                midnight IST.
              </li>
              <li>
                <strong>Reward points stay separate.</strong> Spending points on Pro days, streak
                shields, or cosmetics never lowers your XP or rank.
              </li>
              <li>
                <strong>Ties share a rank.</strong> Tap any learner with a public profile to view
                their target exams and hero.
              </li>
            </ul>
            <div className="finna-lb-side-links">
              <Link to="/profile/rewards" className="finna-lb-secondary-btn">
                XP wallet &amp; quests →
              </Link>
              <Link to="/community/contributors" className="finna-lb-secondary-btn">
                Contributor board →
              </Link>
            </div>
          </section>
        </aside>
      </div>
    </main>
  )
}
