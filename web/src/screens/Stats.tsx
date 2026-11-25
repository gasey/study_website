import { useId, useState } from 'react'
import { Link, Route, Routes, useLocation, useParams, useSearchParams } from 'react-router-dom'
import { statsDate, statsNumber, statsPlaces, statsRankingPath, statsSegments, useStatsRead } from '../lib/stats'
import type {
  StatsCard,
  StatsDetail,
  StatsFreshness,
  StatsObservation,
  StatsOverview,
  StatsRankings,
  StatsSource,
  StatsSurvey,
} from '../lib/stats-types'
import '../styles/stats.css'

type ReadState = { error: string; offlineAt: number | null; retry: () => void }

function categoryTone(category: string): 'cobalt' | 'teal' | 'violet' | 'amber' {
  const c = category.toLowerCase()
  if (c.includes('econom') || c.includes('gdp') || c.includes('price')) return 'cobalt'
  if (c.includes('health') || c.includes('people') || c.includes('pop')) return 'teal'
  if (c.includes('develop') || c.includes('index') || c.includes('human')) return 'violet'
  return 'amber'
}

/** Animated SVG radial ring gauge for bounded index scores (0–1 or 0–100). */
function RadialGauge({
  ratio,
  size = 128,
  stroke = 10,
  label,
  sublabel,
  accent = '#FFC83D',
  track = 'rgba(255,255,255,0.16)',
  compact = false,
}: {
  ratio: number
  size?: number
  stroke?: number
  label: string
  sublabel?: string
  accent?: string
  track?: string
  compact?: boolean
}) {
  const gradId = 'rg-' + useId().replace(/:/g, '')
  const clamped = Math.max(0.04, Math.min(1, Number.isFinite(ratio) ? ratio : 0))
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c * (1 - clamped)
  return (
    <div
      className={'stats-ring' + (compact ? ' is-compact' : '')}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={accent} />
            <stop offset="100%" stopColor="#38BDF8" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={track}
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="stats-ring-arc"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="stats-ring-center">
        <span className="stats-ring-val">{label}</span>
        {sublabel && <span className="stats-ring-sub">{sublabel}</span>}
      </div>
    </div>
  )
}

function indexRatio(item: StatsCard): number | null {
  const val = item.observation?.value
  if (val == null || !Number.isFinite(val)) return null
  if (item.id === 'hdi' || (val > 0 && val <= 1 && item.unit.includes('0'))) return val
  if (item.kind === 'index' && val >= 0 && val <= 100) return val / 100
  return null
}

function ReadNotice({ state, loading = false }: { state: ReadState; loading?: boolean }) {
  return (
    <>
      {loading && !state.error && (
        <p className="stats-notice" role="status">
          Loading official statistics…
        </p>
      )}
      {state.error && (
        <div className="stats-notice stats-warning" role="alert">
          <p>{state.error}</p>
          <button type="button" className="finna-btn finna-btn-quiet" onClick={state.retry}>
            Try again
          </button>
        </div>
      )}
      {state.offlineAt && (
        <p className="stats-notice stats-warning" role="status">
          Showing a saved snapshot from {new Date(state.offlineAt).toLocaleString('en-IN')}. Live updates are
          unavailable.{' '}
          <button type="button" className="stats-link" onClick={state.retry}>
            Reconnect
          </button>
        </p>
      )}
    </>
  )
}

function Freshness({ value }: { value: StatsFreshness }) {
  return (
    <p className={'stats-freshness' + (value.delayed ? ' stats-delayed' : '')}>
      <span className={'stats-pulse-dot' + (value.delayed ? ' is-delayed' : '')} aria-hidden="true" />
      <span>
        {value.delayed ? 'Update delayed · ' : ''}
        {value.message || `Source checked: ${statsDate(value.last_checked_at)}`}
      </span>
    </p>
  )
}

function SourceLink({ url, children }: { url: string; children: React.ReactNode }) {
  return (
    <a className="stats-link" href={url} target="_blank" rel="noopener noreferrer">
      {children} <span aria-label="opens in a new tab">↗</span>
    </a>
  )
}

function MetricCard({ item }: { item: StatsCard }) {
  const tone = categoryTone(item.category)
  const ratio = indexRatio(item)
  return (
    <Link to={'/stats/metric/' + item.id} className={`finna-card stats-metric-card stats-tone-${tone}`}>
      <div className="stats-card-top">
        <span className="stats-cat-badge">{item.category}</span>
        {item.observation?.rank != null ? (
          <span className="stats-rank-chip">Rank #{item.observation.rank}</span>
        ) : (
          <span className="stats-card-arrow" aria-hidden="true">
            ↗
          </span>
        )}
      </div>
      <div className="stats-card-main">
        <div className="min-w-0 flex-1">
          <h3>{item.title}</h3>
          <strong className="stats-value">{statsNumber(item.observation?.value)}</strong>
          <p className="stats-unit">{item.release ? item.unit : 'Publisher access needed'}</p>
        </div>
        {ratio !== null && (
          <RadialGauge
            ratio={ratio}
            size={60}
            stroke={6}
            label={`${Math.round(ratio * 100)}%`}
            accent={tone === 'violet' ? '#A78BFA' : tone === 'teal' ? '#14B8A6' : '#3B82F6'}
            track="rgba(148,163,184,0.22)"
            compact
          />
        )}
      </div>
      <p className="stats-card-period">
        {item.observation?.name || 'India'}
        {item.observation ? ` · ${item.observation.period}` : ''}
        {item.observation?.rank != null ? ` · Rank ${item.observation.rank}` : ''}
      </p>
      <div className="stats-card-source">
        <span className="stats-source-name">{item.source.title}</span>
        <Freshness value={item.freshness} />
      </div>
    </Link>
  )
}

function StatsHome() {
  const state = useStatsRead<StatsOverview>('/overview?country=IND')
  const [category, setCategory] = useState('All')
  const [query, setQuery] = useState('')
  const categories = ['All', ...new Set(state.data?.items.map((item) => item.category) || [])]
  const items =
    state.data?.items.filter(
      (item) =>
        (category === 'All' || item.category === category) &&
        `${item.title} ${item.category}`.toLowerCase().includes(query.toLowerCase()),
    ) || []
  const hdi = state.data?.items.find((item) => item.id === 'hdi')
  const hdiScore = hdi?.observation?.value ?? null
  const gdp = state.data?.items.find((item) => item.id === 'gdp')
  const gdpGrowth = state.data?.items.find((item) => item.id === 'gdp-growth')
  const pop = state.data?.items.find((item) => item.id === 'population')

  return (
    <>
      <section className="stats-hero">
        <div className="stats-hero-copy">
          <p className="stats-kicker">India in perspective · Official verified releases</p>
          <h2>
            Understand the numbers.
            <br />
            Keep the source close.
          </h2>
          <p>
            Explore India, compare countries and read the official reports behind the rankings. Every figure
            keeps its reference year.
          </p>
          {state.data && (
            <div className="stats-hero-kpis" aria-label="Headline India indicators">
              <div className="stats-hero-kpi">
                <span>GDP</span>
                <strong>{statsNumber(gdp?.observation?.value)}</strong>
              </div>
              <div className="stats-hero-kpi">
                <span>GDP Growth</span>
                <strong>
                  {gdpGrowth?.observation?.value != null
                    ? `${statsNumber(gdpGrowth.observation.value)}%`
                    : '—'}
                </strong>
              </div>
              <div className="stats-hero-kpi">
                <span>Population</span>
                <strong>{statsNumber(pop?.observation?.value)}</strong>
              </div>
            </div>
          )}
          <a className="stats-hero-action" href="#stats-indicators">
            Explore indicators <span aria-hidden="true">↓</span>
          </a>
        </div>

        <div className="stats-hero-aside">
          <span className="stats-kicker">Human Development Index</span>
          <div className="stats-hero-ring-row">
            <RadialGauge
              ratio={hdiScore != null ? hdiScore : 0.685}
              size={128}
              stroke={10}
              label={hdi?.observation?.rank != null ? `#${hdi.observation.rank}` : '—'}
              sublabel={hdiScore != null ? `HDI ${hdiScore.toFixed(3)}` : 'India'}
            />
            <div>
              <strong className="sr-only">
                {hdi?.observation?.rank != null ? `#${hdi.observation.rank}` : '—'}
              </strong>
              <p className="stats-hero-aside-meta">
                {hdi?.observation ? `India · ${hdi.observation.period} data` : 'India’s published position'}
              </p>
              <Link to="/stats/metric/hdi">View score, history &amp; countries →</Link>
            </div>
          </div>
        </div>
      </section>

      <ReadNotice state={state} loading={!state.data} />

      <section id="stats-indicators" className="stats-section">
        <div className="finna-section-top">
          <div>
            <p className="finna-eyebrow">Indicators &amp; indices</p>
            <h2>India at a glance</h2>
          </div>
          <label className="stats-search">
            <span className="sr-only">Find an indicator</span>
            <input
              type="search"
              aria-label="Find an indicator"
              placeholder="Find an indicator"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
        </div>

        <div className="finna-segments stats-category" role="group" aria-label="Indicator category">
          {categories.map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={category === value}
              onClick={() => setCategory(value)}
            >
              {value}
            </button>
          ))}
        </div>

        <div className="stats-metric-grid">
          {items.map((item) => (
            <MetricCard key={item.id} item={item} />
          ))}
        </div>

        {state.data && !items.length && (
          <p className="stats-notice">No indicators match. Try a different search or category.</p>
        )}
      </section>

      {state.data?.surveys.map((survey) => (
        <section className="finna-card stats-survey-entry" key={survey.id}>
          <div>
            <p className="finna-eyebrow">The official annual view</p>
            <h2>{survey.title}</h2>
            <p>{survey.description}</p>
          </div>
          <Link className="finna-btn" to={'/stats/survey/' + survey.id}>
            Chapters &amp; tables →
          </Link>
        </section>
      ))}

      <section className="stats-method-note">
        <span aria-hidden="true">ⓘ</span>
        <div>
          <strong>Checked recently ≠ measured recently</strong>
          <p>
            Most indicators are annual. World Bank series update automatically after validation. New report
            editions need review; the Passport Index needs permitted publisher access.{' '}
            <Link to="/stats/sources" className="stats-link">
              How updates work →
            </Link>
          </p>
        </div>
      </section>
    </>
  )
}

/** Interactive multi-series SVG area & line trend chart with hover/focus year inspection. */
function Trend({ data, places }: { data: StatsDetail; places: string[] }) {
  const areaGradId = 'area-' + useId().replace(/:/g, '')
  const periods = [...new Set(data.history.map((row) => row.period))].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true }),
  )
  const [activePeriod, setActivePeriod] = useState<string | null>(null)
  const rows = data.history.filter((row) => places.includes(row.place))
  const values = rows.flatMap((row) => (row.value != null && Number.isFinite(row.value) ? [row.value] : []))
  if (!values.length) {
    return <p className="stats-notice">No historical observations are available for this selection.</p>
  }

  const lookup = new Map(rows.map((r) => [`${r.place}:${r.period}`, r.value]))
  const inspected = activePeriod && periods.includes(activePeriod) ? activePeriod : periods.at(-1) || null
  const low = Math.min(...values)
  const high = Math.max(...values)
  const spread = high - low || Math.max(Math.abs(high) * 0.1, 1)
  const bottom = low - spread * 0.08
  const top = high + spread * 0.12
  const x = (period: string) =>
    68 + (periods.length === 1 ? 0.5 : periods.indexOf(period) / (periods.length - 1)) * 622
  const y = (value: number) => 214 - ((value - bottom) / (top - bottom)) * 180
  const primarySegments = statsSegments(rows, periods, places[0])
  const tickPeriods = [
    ...new Set([periods[0], periods[Math.floor((periods.length - 1) / 2)], periods.at(-1)]),
  ].filter((p): p is string => Boolean(p))

  return (
    <div className="stats-trend" onMouseLeave={() => setActivePeriod(null)}>
      {inspected && (
        <div className="stats-inspector" aria-live="polite">
          <span className="stats-inspector-year">{inspected}</span>
          <div className="stats-inspector-vals">
            {places.map((place, idx) => {
              const v = lookup.get(`${place}:${inspected}`) ?? null
              const prevPeriod = periods[periods.indexOf(inspected) - 1]
              const prevVal = prevPeriod ? (lookup.get(`${place}:${prevPeriod}`) ?? null) : null
              const delta =
                v != null && prevVal != null && prevVal !== 0
                  ? ((v - prevVal) / Math.abs(prevVal)) * 100
                  : null
              const label = data.places.find((r) => r.id === place)?.title || place
              return (
                <span key={place} className="stats-inspector-item">
                  <span className={'stats-dot stats-series-' + idx} />
                  <span>{label}:</span>
                  <strong>{statsNumber(v)}</strong>
                  {delta !== null && Math.abs(delta) >= 0.05 && (
                    <em className={delta >= 0 ? 'is-up' : 'is-down'}>
                      {delta >= 0 ? '+' : ''}
                      {delta.toFixed(1)}%
                    </em>
                  )}
                </span>
              )
            })}
          </div>
        </div>
      )}

      <svg
        viewBox="0 0 720 258"
        role="img"
        aria-label={`${data.metric.title} history for selected places. Exact values follow in the table.`}
      >
        <title>{data.metric.title} history</title>
        <defs>
          <linearGradient id={areaGradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgb(var(--ism-practice-rgb))" stopOpacity="0.24" />
            <stop offset="100%" stopColor="rgb(var(--ism-practice-rgb))" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((f) => {
          const v = bottom + (top - bottom) * f
          return (
            <g key={f}>
              <line x1="68" x2="690" y1={y(v)} y2={y(v)} className="stats-gridline" />
              {(f === 0 || f === 0.5 || f === 1) && (
                <text x="58" y={y(v) + 4} textAnchor="end">
                  {statsNumber(v)}
                </text>
              )}
            </g>
          )
        })}

        {/* Soft gradient area beneath primary series */}
        {primarySegments.map(
          (segment, i) =>
            segment.length > 1 && (
              <polygon
                key={`area-${i}`}
                fill={`url(#${areaGradId})`}
                points={`${x(segment[0].period)},214 ${segment
                  .map((r) => `${x(r.period)},${y(r.value)}`)
                  .join(' ')} ${x(segment[segment.length - 1].period)},214`}
              />
            ),
        )}

        {/* Active vertical crosshair */}
        {inspected && (
          <line
            x1={x(inspected)}
            x2={x(inspected)}
            y1="30"
            y2="214"
            className="stats-crosshair"
          />
        )}

        {/* Multi-series lines & active glowing nodes */}
        {places.map((place, index) => (
          <g key={place} className={'stats-series stats-series-' + index}>
            {statsSegments(rows, periods, place).map((segment, i) =>
              segment.length === 1 ? (
                <circle key={i} cx={x(segment[0].period)} cy={y(segment[0].value)} r="4" />
              ) : (
                <polyline
                  key={i}
                  points={segment.map((row) => `${x(row.period)},${y(row.value)}`).join(' ')}
                  fill="none"
                  strokeWidth="2.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="stats-line-draw"
                />
              ),
            )}
            {inspected && lookup.get(`${place}:${inspected}`) != null && (
              <circle
                cx={x(inspected)}
                cy={y(lookup.get(`${place}:${inspected}`)!)}
                r="5.5"
                className="stats-active-dot"
              />
            )}
          </g>
        ))}

        {/* Interactive invisible scrub hit targets per period */}
        {periods.map((period) => {
          const cx = x(period)
          const colW = periods.length > 1 ? 622 / periods.length : 622
          return (
            <rect
              key={`hit-${period}`}
              x={cx - colW / 2}
              y="24"
              width={Math.max(18, colW)}
              height="196"
              fill="transparent"
              style={{ cursor: 'crosshair' }}
              onMouseEnter={() => setActivePeriod(period)}
              onClick={() => setActivePeriod(period)}
            />
          )
        })}

        {tickPeriods.map((period) => (
          <text key={period} x={x(period)} y="242" textAnchor="middle">
            {period}
          </text>
        ))}
      </svg>

      <ul className="stats-legend">
        {places.map((place, index) => (
          <li key={place}>
            <span className={'stats-dot stats-series-' + index} />
            {data.places.find((row) => row.id === place)?.title || place}
          </li>
        ))}
      </ul>
    </div>
  )
}

function ExactHistory({ data, places }: { data: StatsDetail; places: string[] }) {
  const periods = [...new Set(data.history.map((row) => row.period))].sort((a, b) =>
    b.localeCompare(a, undefined, { numeric: true }),
  )
  const lookup = new Map(data.history.map((row) => [row.place + ':' + row.period, row]))
  return (
    <details className="stats-exact">
      <summary>Exact values by year</summary>
      <div className="stats-table-scroll" role="region" aria-label="Historical observations" tabIndex={0}>
        <table>
          <caption>
            {data.metric.title} · {data.metric.unit}
          </caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              {places.map((place) => (
                <th key={place} scope="col">
                  {data.places.find((row) => row.id === place)?.title || place}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {periods.map((period) => (
              <tr key={period}>
                <th scope="row">{period}</th>
                {places.map((place) => (
                  <td key={place}>{statsNumber(lookup.get(place + ':' + period)?.value, false)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function RankRow({
  row,
  unit,
  maxVal,
  pinned = false,
}: {
  row: StatsObservation
  unit: string
  maxVal: number
  pinned?: boolean
}) {
  const pct =
    row.value != null && Number.isFinite(row.value) && maxVal > 0
      ? Math.max(3, Math.min(100, Math.round((Math.abs(row.value) / maxVal) * 100)))
      : 0
  return (
    <tr className={pinned ? 'stats-pinned' : ''}>
      <td className="stats-rank-num">{row.rank == null ? '—' : `#${row.rank}`}</td>
      <th scope="row">
        <div className="stats-rank-name-row">
          <span>{row.name}</span>
          {pinned && <span className="stats-pill">Pinned</span>}
        </div>
        {pct > 0 && (
          <div className="stats-bar-track" aria-hidden="true">
            <span className={'stats-bar-fill' + (pinned ? ' is-pinned' : '')} style={{ width: `${pct}%` }} />
          </div>
        )}
      </th>
      <td className="stats-rank-val">
        {statsNumber(row.value)}
        <span className="sr-only"> {unit}</span>
      </td>
    </tr>
  )
}

function Rankings({ detail }: { detail: StatsDetail }) {
  const [group, setGroup] = useState('')
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const state = useStatsRead<StatsRankings>(
    detail.release ? statsRankingPath(detail.metric.id, detail.release.id, detail.period, group, search, page) : null,
  )
  const data = state.data
  const visibleVals = [
    ...(data?.india?.value != null ? [Math.abs(data.india.value)] : []),
    ...(data?.items || []).flatMap((r) => (r.value != null && Number.isFinite(r.value) ? [Math.abs(r.value)] : [])),
  ]
  const maxVal = visibleVals.length ? Math.max(...visibleVals) : 0

  return (
    <section className="finna-card stats-rankings">
      <div className="finna-section-top">
        <div>
          <p className="finna-eyebrow">
            {detail.metric.scope === 'states' ? 'State comparisons' : 'Global comparison'}
          </p>
          <h2>{detail.metric.scope === 'states' ? 'States & union territories' : 'Countries & economies'}</h2>
        </div>
        {data && (
          <span className="stats-pill">
            {data.period} · {data.coverage} with data
          </span>
        )}
      </div>
      <p className="stats-muted">
        {data?.derived
          ? 'Calculated ordering from reported values; this is not a publisher index rank.'
          : detail.metric.kind === 'index'
            ? 'Ranks as published in the selected edition. Historical scores may have no published rank.'
            : 'Ordering is shown where observations are available.'}
      </p>

      <div className="stats-rank-controls">
        {detail.metric.scope === 'states' && (
          <label className="stats-field">
            Comparison group
            <select
              aria-label="Comparison group"
              value={group || data?.group || 'Smaller states'}
              onChange={(e) => {
                setGroup(e.target.value)
                setPage(1)
              }}
            >
              {(data?.groups || ['Smaller states', 'Larger states', 'Union Territories']).map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
        )}
        <form
          className="stats-rank-search"
          onSubmit={(e) => {
            e.preventDefault()
            setSearch(query.trim())
            setPage(1)
          }}
        >
          <label>
            <span className="sr-only">Search rankings</span>
            <input
              type="search"
              placeholder={detail.metric.scope === 'states' ? 'Find a state' : 'Find a country'}
              aria-label="Search rankings"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <button className="finna-btn finna-btn-quiet" type="submit">
            Search
          </button>
          {search && (
            <button
              className="stats-link"
              type="button"
              onClick={() => {
                setQuery('')
                setSearch('')
                setPage(1)
              }}
            >
              Clear
            </button>
          )}
        </form>
      </div>

      <ReadNotice state={state} loading={!data} />

      {data && (
        <>
          <div className="stats-table-scroll" role="region" aria-label="Ranking table" tabIndex={0}>
            <table>
              <caption>
                {data.derived ? 'Calculated rank' : 'Publisher rank'} · {data.period || 'No common year'} ·{' '}
                {detail.metric.unit}
                {data.group ? ` · ${data.group}` : ''}
              </caption>
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">{detail.metric.scope === 'states' ? 'State / UT' : 'Country / economy'}</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                {data.india && <RankRow row={data.india} unit={detail.metric.unit} maxVal={maxVal} pinned />}
                {data.items.map((row) => (
                  <RankRow key={row.place} row={row} unit={detail.metric.unit} maxVal={maxVal} />
                ))}
              </tbody>
            </table>
          </div>
          {!data.items.length && <p className="stats-notice">No results for this search and year.</p>}
          <nav className="stats-pagination" aria-label="Ranking pages">
            <button
              type="button"
              className="finna-btn finna-btn-quiet"
              disabled={page === 1}
              onClick={() => setPage((n) => n - 1)}
            >
              ← Previous
            </button>
            <span aria-live="polite">
              Page {page} of {Math.max(1, Math.ceil(data.total / 25))}
            </span>
            <button
              type="button"
              className="finna-btn finna-btn-quiet"
              disabled={page * 25 >= data.total}
              onClick={() => setPage((n) => n + 1)}
            >
              Next →
            </button>
          </nav>
        </>
      )}
    </section>
  )
}

function MetricDetail({ id }: { id: string }) {
  const [params, setParams] = useSearchParams()
  const [placeQuery, setPlaceQuery] = useState('')
  const initialPlaces = statsPlaces(params.get('places'), id === 'state-health' ? 'IN-MZ' : 'IND')
  const placesKey = initialPlaces.join(',')
  const release = params.get('release_id') || ''
  const period = params.get('period') || ''
  const query = new URLSearchParams({
    places: placesKey,
    ...(release ? { release_id: release } : {}),
    ...(period ? { period } : {}),
  })
  const state = useStatsRead<StatsDetail>(`/metrics/${encodeURIComponent(id)}?${query}`)
  const releases = useStatsRead<{
    items: { id: string; edition: string; reference_period: string; published_at: string }[]
  }>(`/metrics/${encodeURIComponent(id)}/releases`)
  const data = state.data

  function change(name: string, value: string) {
    setParams((previous) => {
      const next = new URLSearchParams(previous)
      if (value) next.set(name, value)
      else next.delete(name)
      if (name === 'release_id') next.delete('period')
      return next
    })
  }

  const choices =
    data?.places.filter(
      (place) => !initialPlaces.includes(place.id) && place.title.toLowerCase().includes(placeQuery.toLowerCase()),
    ) || []

  const compValues = initialPlaces.flatMap((place) => {
    const v = data?.observations.find((r) => r.place === place)?.value
    return v != null && Number.isFinite(v) ? [Math.abs(v)] : []
  })
  const compMax = compValues.length ? Math.max(...compValues) : 0

  return (
    <>
      <ReadNotice state={state} loading={!data} />
      {data && (
        <>
          <header className="stats-detail-heading">
            <div>
              <p className="finna-eyebrow">
                {data.metric.category} · {data.metric.scope === 'states' ? 'State index' : 'India & the world'}
              </p>
              <h2>{data.metric.title}</h2>
              <p>{data.metric.definition}</p>
            </div>
            <span className="stats-pill">{data.metric.unit}</span>
          </header>

          {!data.release ? (
            <section className="finna-card stats-empty">
              <h2>Publisher access is needed</h2>
              <p>
                No dataset is published here yet. The Passport Index needs permitted publisher data access
                before ranks can be imported or updated.
              </p>
              <SourceLink url={data.source.url}>Publisher &amp; methodology</SourceLink>
            </section>
          ) : (
            <>
              <section className="stats-filter-bar" aria-label="Statistical release and year">
                <label className="stats-field">
                  Release
                  <select
                    aria-label="Statistical release"
                    value={release}
                    onChange={(e) => change('release_id', e.target.value)}
                  >
                    <option value="">Latest published release</option>
                    {releases.data?.items.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.edition} · {statsDate(item.published_at)} · {item.id.slice(-6)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="stats-field">
                  Reference year
                  <select
                    aria-label="Reference year"
                    value={period}
                    onChange={(e) => change('period', e.target.value)}
                  >
                    <option value="">Latest common year</option>
                    {data.periods.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <Freshness value={data.freshness} />
              </section>
              <ReadNotice state={releases} />

              <div className="stats-detail-layout">
                <div className="stats-main-column">
                  <section className="finna-card">
                    <div className="finna-section-top">
                      <h2>Compare the same year</h2>
                      <span className="stats-pill">{data.period || 'No common year'}</span>
                    </div>
                    <p className="stats-muted">
                      {data.metric.scope === 'states'
                        ? 'Choose up to four states or territories. Rankings retain the report’s separate comparison groups.'
                        : 'India stays selected. Add up to three countries or economies.'}{' '}
                      Missing observations stay unavailable.
                    </p>

                    <div className="stats-comparison-cards">
                      {initialPlaces.map((place, index) => {
                        const observation = data.observations.find((row) => row.place === place)
                        const barPct =
                          observation?.value != null && Number.isFinite(observation.value) && compMax > 0
                            ? Math.max(4, Math.round((Math.abs(observation.value) / compMax) * 100))
                            : 0
                        return (
                          <article key={place} className={'stats-comp-card stats-series-' + index}>
                            <div className="stats-card-top">
                              <span className={'stats-dot stats-series-' + index} />
                              {index > 0 && (
                                <button
                                  type="button"
                                  aria-label={`Remove ${data.places.find((row) => row.id === place)?.title || place}`}
                                  onClick={() =>
                                    change('places', initialPlaces.filter((p) => p !== place).join(','))
                                  }
                                >
                                  Remove
                                </button>
                              )}
                            </div>
                            <h3>{data.places.find((row) => row.id === place)?.title || place}</h3>
                            <strong>{statsNumber(observation?.value)}</strong>
                            <p>
                              {observation?.rank != null
                                ? `Publisher rank #${observation.rank}`
                                : data.metric.unit}
                            </p>
                            {barPct > 0 && (
                              <div className="stats-comp-meter" aria-hidden="true">
                                <span style={{ width: `${barPct}%` }} />
                              </div>
                            )}
                          </article>
                        )
                      })}
                    </div>

                    {initialPlaces.length < 4 && (
                      <div className="stats-place-picker">
                        <label className="stats-field">
                          Find a place
                          <input
                            type="search"
                            aria-label="Filter comparison places"
                            value={placeQuery}
                            onChange={(e) => setPlaceQuery(e.target.value)}
                            placeholder="Type a country or state"
                          />
                        </label>
                        <label className="stats-field">
                          Add to comparison
                          <select
                            value=""
                            aria-label="Add comparison place"
                            onChange={(e) => {
                              if (e.target.value) {
                                change('places', [...initialPlaces, e.target.value].join(','))
                                setPlaceQuery('')
                              }
                            }}
                          >
                            <option value="">{choices.length ? 'Choose a place…' : 'No matching places'}</option>
                            {choices.map((place) => (
                              <option key={place.id} value={place.id}>
                                {place.title}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    )}
                  </section>

                  <section className="finna-card">
                    <div className="finna-section-top">
                      <h2>Through the years</h2>
                      <span className="stats-muted">{data.metric.unit}</span>
                    </div>
                    <Trend data={data} places={initialPlaces} />
                    <ExactHistory data={data} places={initialPlaces} />
                  </section>

                  <Rankings key={data.release.id + ':' + data.period} detail={data} />
                </div>

                <aside className="stats-source-aside">
                  <section className="finna-card">
                    <p className="finna-eyebrow">Source &amp; context</p>
                    <h2>{data.source.title}</h2>
                    <dl>
                      <dt>Published edition</dt>
                      <dd>{data.release.edition}</dd>
                      <dt>Reference period</dt>
                      <dd>{data.release.reference_period}</dd>
                      <dt>Fetched</dt>
                      <dd>{statsDate(data.release.fetched_at)}</dd>
                      <dt>Update method</dt>
                      <dd>{data.source.method}</dd>
                    </dl>
                    <Freshness value={data.freshness} />
                    <SourceLink url={data.release.source_url}>Open original dataset or report</SourceLink>
                  </section>
                  <section className="finna-card">
                    <h2>Read the methodology</h2>
                    <p>{data.release.methodology}</p>
                    {data.release.note && <p>{data.release.note}</p>}
                    <Link to="/stats/sources" className="stats-link">
                      How updates work →
                    </Link>
                  </section>
                </aside>
              </div>
            </>
          )}
        </>
      )}
    </>
  )
}

function MetricRoute() {
  const { id = '' } = useParams()
  return <MetricDetail key={id} id={id} />
}

function Survey({ edition }: { edition: string }) {
  const state = useStatsRead<StatsSurvey>('/surveys/' + encodeURIComponent(edition))
  const [query, setQuery] = useState('')
  const [view, setView] = useState('chapters')
  const data = state.data
  const paused = !!data?.catalogue_status?.changed
  const tables =
    data?.tables?.filter((row) => `${row.id} ${row.title}`.toLowerCase().includes(query.toLowerCase())) || []

  function documentLink(url: string, label: string) {
    return paused ? (
      <span className="stats-muted">Document paused pending edition check</span>
    ) : (
      <SourceLink url={url}>{label}</SourceLink>
    )
  }

  return (
    <>
      <ReadNotice state={state} loading={!data} />
      {data && (
        <>
          <section className="stats-hero stats-survey-hero">
            <div>
              <p className="stats-kicker">Ministry of Finance · Government of India</p>
              <h2>{data.title}</h2>
              <p>{data.description}</p>
              {!paused && (
                <div className="stats-survey-links">
                  <SourceLink url={data.source_url}>Official Survey</SourceLink>
                  <SourceLink url={data.appendix_url}>Statistical appendix</SourceLink>
                </div>
              )}
            </div>
            <div className="stats-hero-aside">
              <strong className="stats-survey-big">{data.chapters.length}</strong>
              <p>official chapter / part links</p>
              <p>{data.tables?.length || 0} appendix tables</p>
            </div>
          </section>

          {paused && (
            <p className="stats-notice stats-warning" role="status">
              The publisher’s catalogue has changed. Document links are paused until their edition is checked.
              Stored figures below retain their original period.
            </p>
          )}
          {data.catalogue_status?.delayed && (
            <p className="stats-notice stats-warning">
              The catalogue check is delayed. These are the saved {data.id} edition links.
            </p>
          )}
          <p className="stats-muted stats-survey-check">
            Official catalogue checked: {statsDate(data.catalogue_status?.last_checked_at)}
          </p>

          <div className="finna-segments stats-category" role="group" aria-label="Economic Survey content">
            {[
              ['chapters', 'Chapters'],
              ['figures', 'Key figures'],
              ['tables', 'Appendix tables'],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                aria-pressed={view === value}
                onClick={() => setView(value)}
              >
                {label}
              </button>
            ))}
          </div>

          {view === 'chapters' && (
            <div className="stats-chapters">
              {data.chapters.map((chapter) => (
                <article key={chapter.id} className="finna-card stats-chapter-card">
                  <p className="finna-eyebrow">{chapter.id.replace(/-/g, ' ')}</p>
                  <h2>{chapter.title}</h2>
                  {chapter.brief && <p>{chapter.brief}</p>}
                  {documentLink(chapter.source_url, 'Read official chapter')}
                </article>
              ))}
            </div>
          )}

          {view === 'figures' && (
            <section className="stats-figures">
              <p className="stats-notice">
                Source-checked figures from the opening chapter. Other chapters are available in the official
                PDFs; complete chapter briefs and table transcriptions are not included yet.
              </p>
              {data.chapters.flatMap((chapter) =>
                (chapter.figures || []).map((figure, index) => (
                  <article className="finna-card stats-figure-card" key={chapter.id + index}>
                    <p className="finna-eyebrow">
                      {figure.period} · {figure.status.replace(/_/g, ' ')}
                    </p>
                    <h2>{figure.title}</h2>
                    <strong className="stats-value">{figure.value}</strong>
                    <p>{figure.citation}</p>
                    {documentLink(chapter.source_url, 'Check the source chapter')}
                  </article>
                )),
              )}
            </section>
          )}

          {view === 'tables' && (
            <section className="finna-card">
              <div className="finna-section-top">
                <h2>Statistical appendix</h2>
                <span className="stats-pill">{tables.length} tables</span>
              </div>
              <label className="stats-search">
                <span className="sr-only">Find an appendix table</span>
                <input
                  type="search"
                  aria-label="Find an appendix table"
                  placeholder="Search population, prices, GDP…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </label>
              <ul className="stats-appendix">
                {tables.map((table) => (
                  <li key={table.id}>
                    <span className="stats-table-id">{table.id}</span>
                    <div>
                      <h3>{table.title}</h3>
                      {documentLink(table.source_url, 'Open official table')}
                    </div>
                  </li>
                ))}
              </ul>
              {!tables.length && <p className="stats-notice">No tables match this search.</p>}
            </section>
          )}
        </>
      )}
    </>
  )
}

function SurveyRoute() {
  const { edition = '' } = useParams()
  return <Survey key={edition} edition={edition} />
}

function Sources() {
  const state = useStatsRead<{
    items: (StatsSource & { metrics: { id: string; title: string; freshness: StatsFreshness }[] })[]
  }>('/sources')
  const explanations: Record<string, string> = {
    'world-bank':
      'Daily API checks. Approved series publish automatically after validation. Unusual revisions and methodology changes wait for review.',
    undp: 'Dataset checks run automatically. Changed HDI data waits for review before a new release is published.',
    niti: 'Official report links and labels are watched. New report tables need a source-checked import; the displayed Round IV data refers to 2019–20.',
    survey:
      'The official chapter and table catalogue is watched. New figures and briefs need source checking. Catalogue changes pause old edition document links.',
    henley: 'Permitted publisher data access is required. No Passport Index dataset is published here yet.',
  }
  return (
    <>
      <div className="stats-detail-heading">
        <div>
          <p className="finna-eyebrow">Trace every figure</p>
          <h2>Sources &amp; updates</h2>
          <p>
            Checks run daily around 2:10–2:25 a.m. India time. Publishers release measurements on their own
            schedules.
          </p>
        </div>
      </div>
      <section className="stats-method-note">
        <span aria-hidden="true">ⓘ</span>
        <div>
          <strong>Automation has a review boundary</strong>
          <p>
            We keep the last good published release if a check fails. New report editions and material changes
            need review. Catalogue watching detects changed links and labels; an unchanged PDF URL can still
            contain a changed file.
          </p>
        </div>
      </section>
      <ReadNotice state={state} loading={!state.data} />
      <div className="stats-sources-grid">
        {state.data?.items.map((source) => (
          <section className="finna-card stats-source-card" key={source.id}>
            <div className="stats-card-top">
              <p className="finna-eyebrow">{source.method}</p>
              <span className="stats-pill">{source.cadence}</span>
            </div>
            <h2>{source.title}</h2>
            <p>{explanations[source.id]}</p>
            <SourceLink url={source.url}>Official source</SourceLink>
            <ul className="stats-source-metrics">
              {source.metrics.map((metric) => (
                <li key={metric.id}>
                  <Link className="stats-link" to={'/stats/metric/' + metric.id}>
                    {metric.title} →
                  </Link>
                  <Freshness value={metric.freshness} />
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </>
  )
}

export default function Stats() {
  const location = useLocation()
  const section = location.pathname.includes('/sources')
    ? 'sources'
    : location.pathname.includes('/survey/')
      ? 'survey'
      : 'indicators'
  return (
    <div className="finna-page finna-stats" data-screen="stats">
      <header className="finna-page-heading">
        <div>
          <Link to="/library" className="stats-back">
            ← Library
          </Link>
          <h1>
            Stats<span className="stats-title-dot">.</span>
          </h1>
          <p className="stats-muted">India, the world and the evidence behind the numbers.</p>
        </div>
        <nav className="finna-segments" aria-label="Stats sections">
          <Link to="/stats" aria-current={section === 'indicators' ? 'page' : undefined}>
            India &amp; rankings
          </Link>
          <Link to="/stats/survey/2025-26" aria-current={section === 'survey' ? 'page' : undefined}>
            Economic Survey
          </Link>
          <Link to="/stats/sources" aria-current={section === 'sources' ? 'page' : undefined}>
            Sources
          </Link>
        </nav>
      </header>
      <Routes>
        <Route index element={<StatsHome />} />
        <Route path="metric/:id" element={<MetricRoute />} />
        <Route path="survey/:edition" element={<SurveyRoute />} />
        <Route path="sources" element={<Sources />} />
        <Route
          path="*"
          element={
            <section className="finna-card">
              <h2>This Stats page could not be found</h2>
              <Link to="/stats" className="stats-link">
                Back to Stats →
              </Link>
            </section>
          }
        />
      </Routes>
      {section === 'indicators' && location.pathname !== '/stats' && (
        <Link to="/stats" className="stats-back stats-bottom-back">
          ← All indicators
        </Link>
      )}
    </div>
  )
}
