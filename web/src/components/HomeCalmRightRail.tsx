import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import { contentRequest } from '../lib/materials'
import type { AvatarLook } from '../lib/avatar'
import type { HomeWidgetId } from '../lib/homePrefs'
import AvatarArt from './AvatarArt'

function handleInitials(handle: string): string {
  const clean = handle.replace(/^@+/, '').trim()
  const parts = clean.split(/[._\-\s]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return clean.slice(0, 2).toUpperCase() || 'FN'
}

function TileAvatar({
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
  nearby?: StandingsRow[]
  items?: StandingsRow[]
  placement?: { rank: number; xp?: number; score?: number; public: boolean } | null
  league?: { name: string }
}

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

export interface CalmQuestItem {
  key: string
  title: string
  progress: number
  target: number
  completed: boolean
  claimed: boolean
}

const POPULAR_GAMES = [
  { id: 'blocks', to: '/games/blocks', title: 'Finna Blocks', meta: '8×8 MCQ Puzzle', tag: 'Puzzle' },
  { id: 'quest', to: '/games/quest', title: 'Finna Quest', meta: '16-bit Pixel RPG', tag: 'RPG' },
  { id: 'daily', to: '/games?mode=daily', title: 'Daily Five', meta: '5-Q daily sprint', tag: 'Daily' },
  { id: 'cup', to: '/games?mode=cup', title: 'Weekly Cup', meta: '15-Q tournament', tag: 'Cup' },
] as const

const SHORTCUTS = [
  { to: '/revise', t: 'Revision queue', d: 'Spaced reviews & mistakes' },
  { to: '/vocabulary', t: 'Vocabulary builder', d: 'Idioms, synonyms & word decks' },
  { to: '/past-papers', t: 'Original past papers', d: 'Full MPSC question papers by year' },
  { to: '/guides', t: 'Concept guides (11)', d: 'Polity, Computer, Science, Maths & more' },
  { to: '/games/quest', t: '⚔️ Finna Quest RPG', d: 'Battle Realm Guardians & Daily 10-Q' },
  { to: '/desk', t: 'Study desk', d: 'One focused session with your study companions' },
] as const

const EVERYTHING_LINKS = [
  { label: 'Exams', to: '/exams' },
  { label: 'Past papers', to: '/past-papers' },
  { label: 'Practice', to: '/practice' },
  { label: 'Mocks', to: '/practice?mode=mock' },
  { label: 'Revise', to: '/revise' },
  { label: 'Vocabulary', to: '/vocabulary' },
  { label: 'Guides', to: '/guides' },
  { label: 'Atlas', to: '/atlas' },
  { label: 'Chronicle', to: '/chronicle' },
  { label: 'Stats', to: '/stats' },
  { label: 'Calendar', to: '/calendar' },
  { label: 'Games', to: '/games' },
  { label: 'Desk', to: '/desk' },
  { label: 'Community', to: '/community' },
  { label: 'Vault', to: '/vault' },
  { label: 'Rewards', to: '/profile/rewards' },
] as const

export default function HomeCalmRightRail({
  quests,
  hidden,
  onHide,
}: {
  quests?: CalmQuestItem[]
  hidden: Set<HomeWidgetId>
  onHide: (id: HomeWidgetId) => void
}) {
  const [board, setBoard] = useState<StandingsPayload | null>(null)
  const [boardLoaded, setBoardLoaded] = useState(false)
  const [boardTick, setBoardTick] = useState(0)
  const [moreTab, setMoreTab] = useState<'Play' | 'People' | 'Tools'>('Play')
  const [discover, setDiscover] = useState<DiscoverPayload | null>(null)
  const [seed, setSeed] = useState('')

  const showBoard = !hidden.has('leaderboard')
  const showTabbed = !hidden.has('quests') || !hidden.has('games') || !hidden.has('discover') || !hidden.has('shortcuts')

  useEffect(() => {
    const refresh = () => setBoardTick((n) => n + 1)
    window.addEventListener('ism-auth-change', refresh)
    window.addEventListener('ism-community-standing-change', refresh)
    return () => {
      window.removeEventListener('ism-auth-change', refresh)
      window.removeEventListener('ism-community-standing-change', refresh)
    }
  }, [])

  useEffect(() => {
    if (!showBoard) return
    let live = true
    reviewRequest<StandingsPayload>('/rewards/leaderboard?contract=2')
      .then((res) => {
        if (live) {
          setBoard(res)
          setBoardLoaded(true)
        }
      })
      .catch(() => {
        if (live) setBoardLoaded(true)
      })
    return () => {
      live = false
    }
  }, [showBoard, boardTick])

  useEffect(() => {
    if (moreTab !== 'People' && discover) return
    let live = true
    const qs = new URLSearchParams({ limit: '3' })
    if (seed) qs.set('seed', seed)
    contentRequest<DiscoverPayload>(`/creators/discover?${qs.toString()}`)
      .then((res) => {
        if (live) setDiscover(res)
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [moreTab, seed]) // eslint-disable-line react-hooks/exhaustive-deps

  const rows = board?.top || board?.items || []
  const top3 = rows.slice(0, 3)
  const rest = rows.slice(3, 5)
  const podiumSlots: {
    row: StandingsRow | null
    rank: number
    size: number
    ring: string
    h: number
    bg: string
  }[] = [
    { row: top3[1] ?? null, rank: 2, size: 36, ring: '#A9BCFF', h: 46, bg: '#E0E7FF' },
    { row: top3[0] ?? null, rank: 1, size: 44, ring: '#FFC83D', h: 62, bg: '#FFC83D' },
    { row: top3[2] ?? null, rank: 3, size: 34, ring: '#FB923C', h: 36, bg: '#FED7AA' },
  ]

  const placement = board?.placement || null
  const leagueName = board?.league?.name || 'Weekly League'
  const allKnownRows = [...rows, ...(board?.nearby || [])]
  const aboveRow =
    placement && placement.rank > 1
      ? allKnownRows.find((r) => r.rank === placement.rank - 1)
      : undefined
  const myXp = placement ? (placement.xp ?? placement.score ?? 0) : 0
  const xpToNext =
    aboveRow && (aboveRow.xp ?? aboveRow.score ?? 0) > myXp
      ? (aboveRow.xp ?? aboveRow.score ?? 0) - myXp
      : null

  return (
    <aside className="finna-home-side finna-calm-right" aria-label="Standings, games, people and shortcuts">
      {/* 1. Navy Podium Weekly Leaderboard Card */}
      {showBoard && (
        <section className="finna-podium-card" aria-labelledby="calm-board-title">
          <div className="finna-podium-head">
            <div className="finna-podium-top">
              <div>
                <div className="finna-podium-kicker">LIVE STANDINGS · {leagueName}</div>
                <h2 id="calm-board-title" className="finna-podium-title">
                  Weekly leaderboard
                </h2>
              </div>
              <div className="finna-podium-head-actions">
                <Link to="/board" className="finna-podium-link">
                  Full board →
                </Link>
                <button
                  type="button"
                  className="finna-podium-hide"
                  aria-label="Hide leaderboard card"
                  title="Hide leaderboard card"
                  onClick={() => onHide('leaderboard')}
                >
                  ×
                </button>
              </div>
            </div>

            <div className="finna-podium-stage" aria-label="Top weekly learners">
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
                        className="finna-podium-block is-empty"
                        style={{ height: p.h }}
                      >
                        <strong>#{p.rank}</strong>
                        <span>—</span>
                      </div>
                    </div>
                  )
                }
                const content = (
                  <>
                    <TileAvatar
                      look={p.row.avatar}
                      handle={p.row.handle}
                      size={p.size}
                      borderColor={p.ring}
                      className="finna-podium-av"
                    />
                    <span className="finna-podium-handle">@{p.row.handle}</span>
                    <div
                      className="finna-podium-block"
                      style={{ height: p.h, background: p.bg }}
                    >
                      <strong>#{p.rank}</strong>
                      <span>{(p.row.xp ?? p.row.score ?? 0).toLocaleString('en-IN')}</span>
                    </div>
                  </>
                )
                return p.row.user_id && p.row.profile_public !== false ? (
                  <Link
                    key={p.rank + '-' + p.row.handle}
                    to={`/creators/${encodeURIComponent(p.row.user_id)}`}
                    className="finna-podium-col"
                  >
                    {content}
                  </Link>
                ) : (
                  <div key={p.rank + '-' + p.row.handle} className="finna-podium-col">
                    {content}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="finna-podium-body">
            {!boardLoaded ? (
              <p className="py-3 text-xs text-secondary">Loading weekly standings…</p>
            ) : rows.length === 0 ? (
              <div className="py-2">
                <p className="text-xs leading-relaxed text-secondary">
                  No public scores yet this week. Claim #1 on the board!
                </p>
                <Link
                  to="/games?mode=daily"
                  className="mt-2 inline-flex text-xs font-bold text-practice-dark hover:underline"
                >
                  Play Daily Five →
                </Link>
              </div>
            ) : (
              rest.map((r) => {
                const rowInner = (
                  <>
                    <span className="finna-podium-rank">#{r.rank}</span>
                    <TileAvatar
                      look={r.avatar}
                      handle={r.handle}
                      size={28}
                      className="finna-podium-row-av"
                    />
                    <span className="finna-podium-name">@{r.handle}</span>
                    <span className="finna-podium-xp">
                      {(r.xp ?? r.score ?? 0).toLocaleString('en-IN')} XP
                    </span>
                  </>
                )
                return r.user_id && r.profile_public !== false ? (
                  <Link
                    key={r.rank + '-' + r.handle}
                    to={`/creators/${encodeURIComponent(r.user_id)}`}
                    className="finna-podium-row is-link"
                  >
                    {rowInner}
                  </Link>
                ) : (
                  <div key={r.rank + '-' + r.handle} className="finna-podium-row">
                    {rowInner}
                  </div>
                )
              })
            )}

            {placement ? (
              <Link to="/board" className="finna-podium-you">
                <span className="finna-podium-you-rank">#{placement.rank}</span>
                <span className="finna-podium-you-main">
                  {placement.public ? 'You' : 'Private rank'} ·{' '}
                  {myXp.toLocaleString('en-IN')} XP
                </span>
                <span className="finna-podium-you-cta">
                  {!placement.public
                    ? 'Opt in →'
                    : xpToNext !== null
                      ? `${xpToNext.toLocaleString('en-IN')} XP to #${placement.rank - 1}`
                      : 'Full board →'}
                </span>
              </Link>
            ) : (
              boardLoaded && (
                <Link to="/board" className="finna-podium-you">
                  <span className="finna-podium-you-rank">—</span>
                  <span className="finna-podium-you-main">You · 0 XP this week</span>
                  <span className="finna-podium-you-cta">Join board →</span>
                </Link>
              )
            )}
          </div>
        </section>
      )}

      {/* 2. Unified Tabbed Card: Play / People / Tools */}
      {showTabbed && (
        <section className="finna-calm-tabs-card" aria-label="Play, people and study tools">
          <div className="finna-calm-tabbar" role="tablist" aria-label="Quick hub">
            {(['Play', 'People', 'Tools'] as const).map((label) => {
              const active = moreTab === label
              return (
                <button
                  key={label}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setMoreTab(label)}
                  className={`finna-calm-tab${active ? ' is-active' : ''}`}
                >
                  {label}
                </button>
              )
            })}
          </div>

          <div className="finna-calm-tabpanel">
            {moreTab === 'Play' && (
              <>
                {quests && quests.length > 0 ? (
                  <div className="finna-calm-quests">
                    {quests.slice(0, 3).map((q) => {
                      const pct = Math.max(
                        0,
                        Math.min(100, Math.round((q.progress / Math.max(1, q.target)) * 100)),
                      )
                      const done = q.completed || q.claimed
                      return (
                        <div key={q.key} className="finna-calm-quest-row">
                          <div className="finna-calm-quest-head">
                            <span className="finna-calm-quest-title">{q.title}</span>
                            <span className="finna-calm-quest-meta">
                              {q.claimed ? '✓ Claimed' : `${q.progress}/${q.target}`}
                            </span>
                          </div>
                          <div
                            className="finna-calm-quest-track"
                            role="progressbar"
                            aria-label={q.title}
                            aria-valuemin={0}
                            aria-valuemax={Math.max(1, q.target)}
                            aria-valuenow={Math.min(q.target, q.progress)}
                          >
                            <div
                              className={`finna-calm-quest-fill${done ? ' is-done' : ''}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="py-2 text-xs text-secondary">
                    Complete daily practice &amp; games to claim XP quest bonuses.
                  </p>
                )}

                <div className="finna-calm-games-grid">
                  {POPULAR_GAMES.map((g) => (
                    <Link key={g.id} to={g.to} className="finna-calm-game-tile">
                      <strong>{g.title}</strong>
                      <small>{g.meta}</small>
                    </Link>
                  ))}
                </div>
              </>
            )}

            {moreTab === 'People' && (
              <>
                {discover?.learners?.length ? (
                  <div className="finna-calm-people-list">
                    {discover.learners.slice(0, 2).map((l) => (
                      <Link
                        key={l.id}
                        to={`/creators/${encodeURIComponent(l.id)}`}
                        className="finna-calm-person"
                      >
                        <TileAvatar
                          look={l.avatar}
                          handle={l.handle}
                          size={32}
                          className="finna-calm-person-av"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-[13.5px] font-bold text-ink">@{l.handle}</div>
                          <div className="truncate text-[11.5px] text-secondary">
                            Lv {l.level} · {l.match_reason}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="py-3 text-xs text-secondary">
                    Explore learners preparing for the same exams.
                  </p>
                )}

                {discover?.materials?.[0] && (
                  <Link
                    to={`/materials/${encodeURIComponent(discover.materials[0].id)}`}
                    className="finna-calm-note-box mt-3 block"
                  >
                    <div className="font-mono text-[10px] uppercase tracking-wider text-secondary">
                      {discover.materials[0].kind} · by @{discover.materials[0].author}
                    </div>
                    <div className="mt-0.5 text-[13.5px] font-bold leading-snug text-ink">
                      {discover.materials[0].title}
                    </div>
                  </Link>
                )}

                <div className="mt-2.5 flex items-center justify-between text-xs font-bold">
                  <button
                    type="button"
                    className="text-practice-dark hover:underline"
                    onClick={() => setSeed(Date.now().toString(36))}
                  >
                    ↻ Shuffle
                  </button>
                  <Link to="/creators" className="text-secondary hover:text-ink">
                    All learners →
                  </Link>
                </div>
              </>
            )}

            {moreTab === 'Tools' && (
              <div className="finna-calm-tools-list">
                {SHORTCUTS.map((s) => (
                  <Link key={s.to} to={s.to} className="finna-calm-tool-row">
                    <strong>{s.t}</strong>
                    <small>{s.d}</small>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* 3. Everything on Finna Chip Index Card */}
      <section className="finna-everything-card" aria-label="Everything on Finna">
        <div className="finna-eyebrow mb-2">Everything on Finna</div>
        <div className="finna-everything-chips">
          {EVERYTHING_LINKS.map((item) => (
            <Link key={item.to} to={item.to} className="finna-everything-chip">
              {item.label}
            </Link>
          ))}
        </div>
      </section>
    </aside>
  )
}
