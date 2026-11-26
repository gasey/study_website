import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import { contentRequest } from '../lib/materials'
import type { AvatarLook } from '../lib/avatar'
import type { HomeWidgetId } from '../lib/homePrefs'
import { UserAvatar } from './AvatarArt'
import { CatXpBar } from './CatLoader'

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
  { to: '/chronicle', t: 'Finna Chronicle', d: 'History & polity timeline + Era Quiz' },
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
  { label: 'Blocks', to: '/games/blocks' },
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
  const [moreTab, setMoreTab] = useState<'Play' | 'People' | 'Tools'>('Play')
  const [discover, setDiscover] = useState<DiscoverPayload | null>(null)
  const [seed, setSeed] = useState('')

  const showBoard = !hidden.has('leaderboard')
  const showTabbed = !hidden.has('quests') || !hidden.has('games') || !hidden.has('discover') || !hidden.has('shortcuts')

  useEffect(() => {
    if (!showBoard) return
    let live = true
    reviewRequest<StandingsPayload>('/rewards/leaderboard')
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
  }, [showBoard])

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
  const podiumOrder = [
    top3[1] ? { row: top3[1], rank: 2, size: 36, ring: '#A9BCFF', h: 46, bg: '#E0E7FF' } : null,
    top3[0] ? { row: top3[0], rank: 1, size: 44, ring: '#FFC83D', h: 62, bg: '#FFC83D' } : null,
    top3[2] ? { row: top3[2], rank: 3, size: 34, ring: '#FB923C', h: 36, bg: '#FED7AA' } : null,
  ].filter(Boolean) as {
    row: StandingsRow
    rank: number
    size: number
    ring: string
    h: number
    bg: string
  }[]

  const placement = board?.placement || null
  const leagueName = board?.league?.name || 'Weekly League'

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
                <Link to="/profile/rewards" className="finna-podium-link">
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

            {podiumOrder.length > 0 && (
              <div className="finna-podium-stage" aria-label="Top weekly learners">
                {podiumOrder.map((p) => {
                  const content = (
                    <>
                      <span
                        className="finna-podium-av"
                        style={{ width: p.size, height: p.size, borderColor: p.ring }}
                      >
                        <UserAvatar look={p.row.avatar} initials={p.row.handle} size={p.size - 4} />
                      </span>
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
            )}
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
                    <UserAvatar look={r.avatar} initials={r.handle} size={28} />
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

            {placement && (
              <Link to="/profile/rewards" className="finna-podium-you">
                <span className="finna-podium-you-rank">#{placement.rank}</span>
                <span className="finna-podium-you-main">
                  {placement.public ? 'You' : 'Private rank'} ·{' '}
                  {(placement.xp ?? placement.score ?? 0).toLocaleString('en-IN')} XP
                </span>
                <span className="finna-podium-you-cta">
                  {placement.public ? 'Rewards →' : 'Opt in →'}
                </span>
              </Link>
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
                    {quests.slice(0, 3).map((q) => (
                      <div key={q.key} className="finna-calm-quest-row">
                        <CatXpBar
                          value={q.progress}
                          max={Math.max(1, q.target)}
                          tone={q.completed ? 'gold' : 'quest'}
                          showCat={q.progress > 0}
                          label={q.title}
                          meta={q.claimed ? '✓ Claimed' : `${q.progress}/${q.target}`}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="py-2 text-xs text-secondary">
                    Complete daily practice &amp; games to claim XP quest bonuses.
                  </p>
                )}

                <div className="finna-calm-games-grid">
                  {POPULAR_GAMES.map((g) => (
                    <Link key={g.id} to={g.to} className="finna-calm-game-tile">
                      <span className="finna-calm-game-tag">{g.tag}</span>
                      <strong>{g.title}</strong>
                      <small>{g.meta}</small>
                    </Link>
                  ))}
                </div>
                <div className="mt-3 flex items-center justify-between text-xs font-bold">
                  <Link to="/profile/rewards" className="text-rewards-dark hover:underline">
                    View quests →
                  </Link>
                  <Link to="/games" className="text-practice-dark hover:underline">
                    All games →
                  </Link>
                </div>
              </>
            )}

            {moreTab === 'People' && (
              <>
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-secondary">
                    Rotating learners
                  </span>
                  <button
                    type="button"
                    className="text-xs font-bold text-practice-dark hover:underline"
                    onClick={() => setSeed(Date.now().toString(36))}
                  >
                    ↻ Shuffle
                  </button>
                </div>

                {discover?.learners?.length ? (
                  <div className="divide-y divide-hairline">
                    {discover.learners.slice(0, 3).map((l) => (
                      <Link
                        key={l.id}
                        to={`/creators/${encodeURIComponent(l.id)}`}
                        className="finna-calm-person"
                      >
                        <UserAvatar look={l.avatar} initials={l.handle} size={32} />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-bold text-ink">@{l.handle}</div>
                          <div className="truncate text-xs text-secondary">
                            Lv {l.level} · {l.match_reason}
                          </div>
                        </div>
                        <span className="text-xs text-muted">↗</span>
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
                    <div className="mt-0.5 text-sm font-bold leading-snug text-ink">
                      {discover.materials[0].title}
                    </div>
                  </Link>
                )}

                <div className="mt-3 flex items-center justify-between text-xs font-bold">
                  <Link to="/creators" className="text-practice-dark hover:underline">
                    Find learners →
                  </Link>
                  <Link to="/community" className="text-secondary hover:text-ink">
                    Community feed →
                  </Link>
                </div>
              </>
            )}

            {moreTab === 'Tools' && (
              <div className="divide-y divide-hairline">
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
        <div className="finna-eyebrow mb-2.5">Everything on Finna</div>
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
