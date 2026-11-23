import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { Progress } from '../lib/api'

type DeckView = 'overview' | 'subjects' | 'modules'

const FUN_KEY = 'finna.study-fun-mode'
const DAILY_TARGET = 10
const ACCURACY_TARGET = 70

function readFunPref(): boolean {
  try {
    return typeof localStorage !== 'undefined' && localStorage.getItem(FUN_KEY) === 'on'
  } catch {
    return false
  }
}

function monogram(label: string): string {
  const parts = label.trim().split(/[\s/&,-]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return label.trim().slice(0, 2).toUpperCase() || 'ST'
}

function shortDay(iso: string, isToday: boolean): string {
  if (isToday) return 'Today'
  const d = new Date(`${iso}T12:00:00`)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function statusPill(pct: number): { label: string; cls: string } {
  if (pct >= 75) return { label: 'Strong', cls: 'giz-pill giz-pill--good' }
  if (pct >= 50) return { label: 'Building', cls: 'giz-pill giz-pill--mid' }
  return { label: 'Focus', cls: 'giz-pill giz-pill--low' }
}

function burstConfetti(origin: HTMLElement) {
  if (typeof document === 'undefined' || typeof window === 'undefined') return
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  const { left, top, width, height } = origin.getBoundingClientRect()
  const burst = document.createElement('div')
  burst.className = 'giz-confetti'
  burst.setAttribute('aria-hidden', 'true')
  burst.style.left = `${left + width / 2}px`
  burst.style.top = `${top + height / 2}px`
  const count = 24
  for (let i = 0; i < count; i++) {
    const dot = document.createElement('i')
    const angle = (i / count) * Math.PI * 2
    const dist = 78 + (i % 3) * 38
    const hue = Math.round(200 - (i / count) * 170)
    dot.style.setProperty('--dx', `${Math.round(Math.cos(angle) * dist)}px`)
    dot.style.setProperty('--dy', `${Math.round(Math.sin(angle) * dist)}px`)
    dot.style.background = `hsl(${hue} 70% 55%)`
    burst.appendChild(dot)
  }
  document.body.appendChild(burst)
  window.setTimeout(() => burst.remove(), 1050)
}

function WaveTitle({ text }: { text: string }) {
  const chars = [...text]
  return (
    <h2 className="giz-title" aria-label={text}>
      {chars.map((ch, idx) => (
        <span
          key={`${idx}-${ch}`}
          aria-hidden="true"
          style={{ '--i': idx, '--n': chars.length } as CSSProperties}
        >
          {ch}
        </span>
      ))}
    </h2>
  )
}

export default function StudyAnalyticsDeck({
  progress,
  todayAnswered,
}: {
  progress?: Progress | null
  todayAnswered: number
}) {
  const [view, setView] = useState<DeckView>('overview')
  const [fun, setFun] = useState<boolean>(readFunPref)
  const funBtnRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    try {
      localStorage.setItem(FUN_KEY, fun ? 'on' : 'off')
    } catch {
      /* ignore storage errors */
    }
  }, [fun])

  const p = progress
  const answered = p?.answered ?? 0
  const correct = p?.correct ?? 0
  const wrong = Math.max(0, answered - correct)
  const accuracy = answered > 0 ? p?.accuracy ?? Math.round((correct / answered) * 100) : 0
  const correctPct = answered > 0 ? Math.round((correct / answered) * 100) : 0
  const reviewPct = answered > 0 ? 100 - correctPct : 0

  const subjects = useMemo(
    () =>
      [...(p?.subjects ?? [])]
        .map((s) => ({
          ...s,
          pct: s.answered > 0 ? Math.round((s.correct / s.answered) * 100) : 0,
        }))
        .sort((a, b) => b.answered - a.answered),
    [p?.subjects],
  )

  const modules = useMemo(
    () =>
      (p?.collections ?? [])
        .filter((c) => c.scope_id !== 'general')
        .sort((a, b) => b.answered - a.answered),
    [p?.collections],
  )

  const bars = useMemo(() => {
    const byDay = new Map((p?.daily_activity ?? []).map((d) => [d.day, d]))
    const today = new Date()
    const todayIso = today.toLocaleDateString('en-CA')
    return Array.from({ length: 10 }, (_, idx) => {
      const d = new Date(today)
      d.setDate(today.getDate() - (9 - idx))
      const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      const hit = byDay.get(iso)
      return {
        iso,
        label: shortDay(iso, iso === todayIso),
        isToday: iso === todayIso,
        answered: hit?.answered ?? 0,
        correct: hit?.correct ?? 0,
      }
    })
  }, [p?.daily_activity])

  const maxBar = Math.max(DAILY_TARGET * 1.4, ...bars.map((b) => b.answered))
  const targetBottomPct = Math.min(92, Math.round((DAILY_TARGET / maxBar) * 100))
  const activeLast10 = bars.reduce((sum, b) => sum + b.answered, 0)
  const topSubject = subjects[0] ?? null

  const kpis = [
    {
      label: 'Questions answered',
      value: answered.toLocaleString('en-IN'),
      pill: `${todayAnswered} today`,
      note: `${activeLast10.toLocaleString('en-IN')} in last 10d`,
      good: todayAnswered > 0,
    },
    {
      label: 'Accuracy',
      value: answered > 0 ? `${accuracy}%` : '—',
      pill: answered > 0 ? (accuracy >= ACCURACY_TARGET ? 'On target' : 'Building') : 'Start practicing',
      note: `Target ${ACCURACY_TARGET}%+`,
      good: accuracy >= ACCURACY_TARGET,
    },
    {
      label: 'Unique questions',
      value: (p?.unique_questions ?? 0).toLocaleString('en-IN'),
      pill: `${subjects.length} ${subjects.length === 1 ? 'subject' : 'subjects'}`,
      note: 'Distinct bank items',
      good: (p?.unique_questions ?? 0) > 0,
    },
    {
      label: 'Correct answers',
      value: correct.toLocaleString('en-IN'),
      pill: `${correctPct}% share`,
      note: `${wrong.toLocaleString('en-IN')} to revisit`,
      good: correct > 0,
    },
    {
      label: 'Active days · 30d',
      value: String(p?.active_days_30 ?? 0),
      pill: `${Math.round(((p?.active_days_30 ?? 0) / 30) * 100)}% of month`,
      note: 'Consistency window',
      good: (p?.active_days_30 ?? 0) >= 7,
    },
    {
      label: p?.streak_basis === 'device activity' ? 'Device activity' : 'Day streak',
      value: String(p?.current_streak ?? 0),
      pill: (p?.current_streak ?? 0) >= 3 ? 'In rhythm' : 'Daily habit',
      note: `Goal ${DAILY_TARGET} Qs/day`,
      good: (p?.current_streak ?? 0) > 0,
    },
  ]

  function toggleFun() {
    setFun((prev) => {
      const next = !prev
      if (next && funBtnRef.current) burstConfetti(funBtnRef.current)
      return next
    })
  }

  const titleText =
    view === 'overview'
      ? 'Study overview'
      : view === 'subjects'
        ? 'Subject mastery'
        : 'Module attainment'

  return (
    <section
      className="giz-deck"
      data-fun={fun ? 'on' : 'off'}
      aria-label="Study analytics dashboard"
    >
      <header className="giz-header">
        <div className="giz-header-copy">
          <p className="giz-kicker">Last 10 days · Personal study analytics</p>
          <WaveTitle text={titleText} />
        </div>

        <div className="giz-controls">
          <button
            ref={funBtnRef}
            type="button"
            aria-pressed={fun}
            onClick={toggleFun}
            className="giz-fun-btn"
          >
            <svg
              className="giz-fun-spark"
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z" />
              <path d="M19 15l.7 1.8L21.5 17.5l-1.8.7L19 20l-.7-1.8-1.8-.7 1.8-.7L19 15z" />
            </svg>
            <span>Fun mode</span>
            <span className="giz-fun-track" aria-hidden="true">
              <span className="giz-fun-knob" />
            </span>
          </button>

          <div className="giz-views" role="group" aria-label="Analytics view">
            {(
              [
                ['overview', 'Overview', null],
                ['subjects', 'Subjects', subjects.length || null],
                ['modules', 'Modules', modules.length || null],
              ] as [DeckView, string, number | null][]
            ).map(([id, label, count]) => (
              <button
                key={id}
                type="button"
                aria-pressed={view === id}
                onClick={() => setView(id)}
                className="giz-view-btn"
              >
                <span>{label}</span>
                {count != null && <em className="giz-view-count">{count}</em>}
              </button>
            ))}
          </div>
        </div>
      </header>

      {view === 'overview' && (
        <div key="overview" className="giz-pane">
          <div className="giz-kpi-grid">
            {kpis.map((k, idx) => (
              <div
                key={k.label}
                className="giz-card giz-kpi"
                style={{ '--i': idx, '--n': kpis.length } as CSSProperties}
              >
                <span className="giz-kpi-label">{k.label}</span>
                <strong className="giz-kpi-val">{k.value}</strong>
                <div className="giz-kpi-foot">
                  <span className={k.good ? 'giz-pill giz-pill--good' : 'giz-pill giz-pill--neutral'}>
                    {k.pill}
                  </span>
                  <span className="giz-kpi-note">{k.note}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="giz-split">
            <article className="giz-card giz-panel">
              <div className="giz-panel-head">
                <div>
                  <h3 className="giz-card-title">Daily practice</h3>
                  <p className="giz-card-sub">Last 10 days, questions answered</p>
                </div>
                <ul className="giz-legend">
                  <li>
                    <span className="giz-swatch giz-swatch--brand" />
                    Today
                  </li>
                  <li>
                    <span className="giz-swatch giz-swatch--soft" />
                    Previous
                  </li>
                  <li>
                    <span className="giz-swatch-line" />
                    Target {DAILY_TARGET}/day
                  </li>
                </ul>
              </div>

              <div className="giz-chart" role="img" aria-label={`Daily practice over the last 10 days totaling ${activeLast10} answers`}>
                <div className="giz-target-line" style={{ bottom: `${targetBottomPct}%` }}>
                  <span>{DAILY_TARGET}</span>
                </div>
                <div className="giz-bars">
                  {bars.map((b, idx) => {
                    const heightPct = b.answered > 0 ? Math.max(8, Math.round((b.answered / maxBar) * 100)) : 3
                    return (
                      <div
                        key={b.iso}
                        className="giz-bar-col"
                        title={`${b.label}: ${b.answered} answered (${b.correct} correct)`}
                      >
                        <div className="giz-bar-well">
                          <span
                            className={'giz-bar' + (b.isToday ? ' is-today' : '') + (b.answered === 0 ? ' is-zero' : '')}
                            style={{ height: `${heightPct}%`, '--i': idx, '--n': bars.length } as CSSProperties}
                          >
                            {b.answered > 0 && <em className="giz-bar-tip">{b.answered}</em>}
                          </span>
                        </div>
                        <span className={'giz-bar-label' + (b.isToday ? ' is-today' : '')}>{b.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </article>

            <article className="giz-card giz-panel">
              <div>
                <h3 className="giz-card-title">Answer split</h3>
                <p className="giz-card-sub">Share of recorded practice answers</p>
              </div>

              <div className="giz-stacked" aria-label={`${correctPct}% correct, ${reviewPct}% needs review`}>
                {answered > 0 ? (
                  <>
                    <div
                      className="giz-stacked-seg giz-seg--brand"
                      style={{ width: `${correctPct}%`, '--i': 0, '--n': 2 } as CSSProperties}
                    />
                    <div
                      className="giz-stacked-seg giz-seg--accent"
                      style={{ width: `${reviewPct}%`, '--i': 1, '--n': 2 } as CSSProperties}
                    />
                  </>
                ) : (
                  <div className="giz-stacked-empty" />
                )}
              </div>

              <ul className="giz-channel-list">
                <li style={{ '--i': 0, '--n': 2 } as CSSProperties}>
                  <span className="giz-swatch giz-swatch--brand" />
                  <div className="giz-channel-copy">
                    <strong>Correct answers</strong>
                    <small>Verified matches</small>
                  </div>
                  <div className="giz-channel-nums">
                    <strong>{correct.toLocaleString('en-IN')}</strong>
                    <small>{correctPct}%</small>
                  </div>
                </li>
                <li style={{ '--i': 1, '--n': 2 } as CSSProperties}>
                  <span className="giz-swatch giz-swatch--accent" />
                  <div className="giz-channel-copy">
                    <strong>Needs review</strong>
                    <small>Queued for revision</small>
                  </div>
                  <div className="giz-channel-nums">
                    <strong>{wrong.toLocaleString('en-IN')}</strong>
                    <small>{reviewPct}%</small>
                  </div>
                </li>
              </ul>

              <p className="giz-callout">
                {topSubject ? (
                  <>
                    Most practised subject: <strong>{topSubject.subject}</strong> ({topSubject.answered} answers · {topSubject.pct}% accuracy).
                  </>
                ) : (
                  <>
                    Answer a few questions in <Link to="/bank" className="giz-callout-link">the question bank</Link> to unlock daily charts and subject splits.
                  </>
                )}
              </p>
            </article>
          </div>
        </div>
      )}

      {view === 'subjects' && (
        <div key="subjects" className="giz-pane">
          {!subjects.length ? (
            <div className="giz-card giz-empty">
              <h3 className="giz-card-title">No subject data yet</h3>
              <p className="giz-card-sub">
                Subject performance cards appear automatically once you answer tagged questions.
              </p>
              <Link to="/bank" className="finna-btn mt-4">
                Open question bank →
              </Link>
            </div>
          ) : (
            <>
              <div className="giz-fan-grid">
                {subjects.slice(0, 4).map((s, idx, arr) => {
                  const pill = statusPill(s.pct)
                  const spread = idx - (arr.length - 1) / 2
                  return (
                    <Link
                      key={s.subject_id}
                      to={`/library/subjects/${encodeURIComponent(s.subject_id)}`}
                      className="giz-card giz-fan-card"
                      style={{ '--i': idx, '--n': arr.length, '--spread': spread } as CSSProperties}
                    >
                      <div className="giz-fan-icon">{monogram(s.subject)}</div>
                      <div className="giz-fan-head">
                        <div className="min-w-0">
                          <h3 className="giz-card-title">{s.subject}</h3>
                          <span className="giz-card-sub">{s.unique_questions} unique items</span>
                        </div>
                        <span className={pill.cls}>{pill.label}</span>
                      </div>
                      <div className="giz-fan-stats">
                        <div>
                          <small>Answered</small>
                          <strong>{s.answered}</strong>
                        </div>
                        <div>
                          <small>Correct</small>
                          <strong>{s.correct}</strong>
                        </div>
                      </div>
                      <div className="giz-meter-wrap">
                        <div className="giz-meter-top">
                          <span>Accuracy</span>
                          <strong>{s.pct}%</strong>
                        </div>
                        <div className="giz-meter">
                          <div
                            className={'giz-meter-fill' + (s.pct >= ACCURACY_TARGET ? ' is-target' : ' is-below')}
                            style={{ width: `${s.pct}%`, '--i': idx, '--n': arr.length } as CSSProperties}
                          />
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>

              <div className="giz-card giz-table-card">
                <div className="giz-table-head">
                  <div>
                    <h3 className="giz-card-title">Accuracy by subject</h3>
                    <p className="giz-card-sub">Attainment against {ACCURACY_TARGET}% study target</p>
                  </div>
                </div>
                <div className="giz-table-scroll">
                  <table className="giz-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th className="is-right">Answered</th>
                        <th className="is-right">Correct</th>
                        <th>Target attainment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subjects.map((s, idx) => (
                        <tr key={s.subject_id} style={{ '--i': idx, '--n': subjects.length } as CSSProperties}>
                          <td>
                            <Link to={`/library/subjects/${encodeURIComponent(s.subject_id)}`} className="giz-row-entity">
                              <span className="giz-badge">{monogram(s.subject)}</span>
                              <strong>{s.subject}</strong>
                            </Link>
                          </td>
                          <td className="is-right is-num">{s.answered}</td>
                          <td className="is-right is-num">{s.correct}</td>
                          <td>
                            <div className="giz-attain">
                              <div className="giz-meter">
                                <div
                                  className={'giz-meter-fill' + (s.pct >= ACCURACY_TARGET ? ' is-target' : ' is-below')}
                                  style={{ width: `${s.pct}%`, '--i': idx, '--n': subjects.length } as CSSProperties}
                                />
                              </div>
                              <span className="giz-attain-pct">{s.pct}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <ul className="giz-table-foot">
                  <li>
                    <span className="giz-swatch giz-swatch--brand" />
                    On target ({ACCURACY_TARGET}%+)
                  </li>
                  <li>
                    <span className="giz-swatch giz-swatch--accent" />
                    Below target
                  </li>
                </ul>
              </div>
            </>
          )}
        </div>
      )}

      {view === 'modules' && (
        <div key="modules" className="giz-pane">
          {!modules.length ? (
            <div className="giz-card giz-empty">
              <h3 className="giz-card-title">No exam modules tracked yet</h3>
              <p className="giz-card-sub">
                Start practicing inside any exam collection to track accuracy and coverage per module.
              </p>
              <Link to="/exams" className="finna-btn mt-4">
                Browse exams →
              </Link>
            </div>
          ) : (
            <div className="giz-card giz-table-card">
              <div className="giz-table-head">
                <div>
                  <h3 className="giz-card-title">Exam module attainment</h3>
                  <p className="giz-card-sub">Accuracy against {ACCURACY_TARGET}% target across your exams</p>
                </div>
              </div>
              <div className="giz-table-scroll">
                <table className="giz-table">
                  <thead>
                    <tr>
                      <th>Module</th>
                      <th className="is-right">Answered</th>
                      <th className="is-right">Unique</th>
                      <th>Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modules.map((m, idx) => (
                      <tr key={m.scope_id} style={{ '--i': idx, '--n': modules.length } as CSSProperties}>
                        <td>
                          <Link to={`/exams/${m.scope_id}?view=progress`} className="giz-row-entity">
                            <span className="giz-badge">{monogram(m.label)}</span>
                            <strong>{m.label}</strong>
                          </Link>
                        </td>
                        <td className="is-right is-num">{m.answered}</td>
                        <td className="is-right is-num">{m.unique_questions}</td>
                        <td>
                          <div className="giz-attain">
                            <div className="giz-meter">
                              <div
                                className={'giz-meter-fill' + (m.accuracy >= ACCURACY_TARGET ? ' is-target' : ' is-below')}
                                style={{ width: `${m.accuracy}%`, '--i': idx, '--n': modules.length } as CSSProperties}
                              />
                            </div>
                            <span className="giz-attain-pct">{m.accuracy}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ul className="giz-table-foot">
                <li>
                  <span className="giz-swatch giz-swatch--brand" />
                  On target ({ACCURACY_TARGET}%+)
                </li>
                <li>
                  <span className="giz-swatch giz-swatch--accent" />
                  Below target
                </li>
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
