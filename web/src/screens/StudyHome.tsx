import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import {
  currentMock,
  listCollections,
  isLaterExamCollection,
  getExamProgress,
  getExamBookmarks,
  getProgress,
  setPrimaryExam,
  type MockSession,
  type Collection,
  type ExamProgressSummary,
  type Progress,
} from '../lib/api'
import { reviewSession } from '../lib/review'
import { learningRequest, type ResumePage, type ResumeItem } from '../lib/learning'
import { accountContext } from '../lib/accountContext'
import { useExamScope } from '../lib/examScope'
import { choosePreferredExam, usePreferredExam } from '../lib/preferredExam'
import { examPresentation } from '../lib/examPresentation'
import { calendarRead, indiaToday, type CalendarEvent } from '../lib/calendar'
import { subjectChipClass, subjectInitials } from '../lib/subjectChips'
import QuickStudy from '../components/QuickStudy'
import TodayCard from '../components/TodayCard'
import OfflineBanner from '../components/OfflineBanner'
import WelcomeBackBar from '../components/WelcomeBackBar'
import ExploreDeckRail from '../components/ExploreDeckRail'
import VaultShowcaseCard from '../components/VaultShowcaseCard'
import { mockResumePath } from '../lib/sharedTests'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

type StudyData = {
  exams: Collection[]
  examProgress: ExamProgressSummary[]
  saved: string[]
  progress: Progress | null
  resumeItems: ResumeItem[]
  mock: MockSession | null
  calendarEvents: CalendarEvent[]
  loading: boolean
  primaryError: boolean
  lastLoadedAt: number | null
}

const EMPTY: StudyData = {
  exams: [],
  examProgress: [],
  saved: [],
  progress: null,
  resumeItems: [],
  mock: null,
  calendarEvents: [],
  loading: true,
  primaryError: false,
  lastLoadedAt: null,
}

const SAFE_RESUME_RE = /^\/(bank|exams|group-b|english|mizo|arithmetic|essay|library|desk|tests|practice|revise|guides)([/?#]|$)/

export default function StudyHome() {
  const [params] = useSearchParams()
  const scope = useExamScope()
  const [retry, setRetry] = useState(0)
  const [data, setData] = useState<StudyData>(EMPTY)
  const [examError, setExamError] = useState('')
  const [savingExam, setSavingExam] = useState(false)
  const [monthOffset, setMonthOffset] = useState(0)

  const today = indiaToday()

  async function chooseExam(id: string) {
    setSavingExam(true)
    setExamError('')
    try {
      if ((await accountContext()).authenticated) await setPrimaryExam(id)
      choosePreferredExam(id)
    } catch (e) {
      setExamError((e as Error).message)
    } finally {
      setSavingExam(false)
    }
  }

  useEffect(() => {
    let live = true
    setData((prev) => ({ ...EMPTY, lastLoadedAt: prev.lastLoadedAt }))
    const patch = (values: Partial<StudyData>) => {
      if (live) setData((previous) => ({ ...previous, ...values }))
    }

    // Primary study requests — isolated from secondary enhancements (§VII.19.8)
    const primaryRequests = [
      listCollections().then((rows) =>
        patch({ exams: rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)) }),
      ),
      getProgress().then((progress) => patch({ progress })),
      getExamProgress().then((examProgress) => patch({ examProgress })),
    ]

    // Secondary requests fail independently so they never blank the whole home screen
    void getExamBookmarks()
      .then((saved) => {
        if (!live) return
        patch({ saved: saved.collection_ids })
        if (saved.primary_collection_id) choosePreferredExam(saved.primary_collection_id)
      })
      .catch(() => {})

    void currentMock()
      .then((mock) => patch({ mock }))
      .catch(() => {})

    void accountContext()
      .then((a) =>
        a.authenticated
          ? reviewSession()
              .then((s) => learningRequest<ResumePage>('/resume?exam_scope=' + scope, s.user_id))
              .then((r) =>
                patch({
                  resumeItems: (r.items || [])
                    .filter((i) => i.kind !== 'desk' && SAFE_RESUME_RE.test(i.url))
                    .slice(0, 3),
                }),
              )
          : undefined,
      )
      .catch(() => {})

    Promise.allSettled(primaryRequests).then((results) => {
      const anySucceeded = results.some((r) => r.status === 'fulfilled')
      const allFailed = results.every((r) => r.status === 'rejected')
      patch({
        loading: false,
        primaryError: allFailed,
        ...(anySucceeded ? { lastLoadedAt: Date.now() } : {}),
      })
    })

    return () => {
      live = false
    }
  }, [scope, retry])

  // Load month calendar exam dates for the visible mini-calendar month
  const calBase = useMemo(() => {
    const [y, m] = today.split('-').map(Number)
    const d = new Date(Date.UTC(y, m - 1 + monthOffset, 1))
    const year = d.getUTCFullYear()
    const month = d.getUTCMonth()
    const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate()
    const firstDow = (d.getUTCDay() + 6) % 7 // Monday-first
    const ym = `${year}-${String(month + 1).padStart(2, '0')}`
    return { year, month, daysInMonth, firstDow, start: `${ym}-01`, end: `${ym}-${String(daysInMonth).padStart(2, '0')}`, ym }
  }, [today, monthOffset])

  useEffect(() => {
    let live = true
    calendarRead<{ items: CalendarEvent[] }>(
      `/calendar/events?start=${calBase.start}&end=${calBase.end}&limit=100`,
    )
      .then((r) => {
        if (live) setData((prev) => ({ ...prev, calendarEvents: r.items || [] }))
      })
      .catch(() => {
        if (live) setData((prev) => ({ ...prev, calendarEvents: [] }))
      })
    return () => {
      live = false
    }
  }, [calBase.start, calBase.end])

  useEffect(() => {
    const refresh = () => setRetry((n) => n + 1)
    window.addEventListener('ism-auth-change', refresh)
    return () => window.removeEventListener('ism-auth-change', refresh)
  }, [])

  const exam = usePreferredExam(data.exams)
  const examProgress = data.examProgress.find((p) => p.collection_id === exam?.id)
  const coverage =
    exam && examProgress && exam.questions
      ? Math.min(100, Math.round((examProgress.unique_questions / exam.questions) * 100))
      : null
  const p = data.progress
  const subjects = [...(p?.subjects || [])].sort((a, b) => b.answered - a.answered).slice(0, 6)
  const examTitle = exam
    ? exam.id === 'udc'
      ? 'UDC'
      : exam.id === 'ldc'
        ? 'LDC'
        : exam.id === 'combined-prelims'
          ? 'Prelims'
          : exam.title
    : 'Choose your exam'

  const weekCutoff = new Date(Date.parse(today + 'T12:00:00Z') - 6 * 86400000).toISOString().slice(0, 10)
  const week = p?.daily_activity.filter((d) => d.day >= weekCutoff) || []
  const weekAnswers = week.reduce((n, d) => n + d.answered, 0)
  const weekCorrect = week.reduce((n, d) => n + d.correct, 0)
  // Strict null vs "0%" honesty (§VII.19.8): 0 denominator displays "—", never "0%"
  const weekAccuracy = weekAnswers > 0 ? `${Math.round((weekCorrect / weekAnswers) * 100)}%` : null

  const practisedDays = useMemo(() => {
    const set = new Set<number>()
    for (const d of p?.daily_activity || []) {
      if (d.answered > 0 && d.day.startsWith(calBase.ym + '-')) {
        set.add(Number(d.day.slice(8, 10)))
      }
    }
    return set
  }, [p?.daily_activity, calBase.ym])

  const examEventDays = useMemo(() => {
    const set = new Set<number>()
    for (const ev of data.calendarEvents) {
      if (ev.starts_on && ev.starts_on.startsWith(calBase.ym + '-')) {
        set.add(Number(ev.starts_on.slice(8, 10)))
      }
    }
    return set
  }, [data.calendarEvents, calBase.ym])

  const returnRows = useMemo(() => {
    const rows: { key: string; eyebrow: string; title: string; detail: string; url: string; cta: string }[] = []
    if (data.mock) {
      rows.push({
        key: 'mock-' + data.mock.id,
        eyebrow: 'Test in progress',
        title: 'Resume your timed run',
        detail: `${data.mock.questions.length} questions · ${Math.max(0, Math.ceil(data.mock.seconds_remaining / 60))} min remaining`,
        url: mockResumePath(data.mock),
        cta: 'Resume test',
      })
    }
    for (const item of data.resumeItems) {
      if (rows.length >= 3) break
      rows.push({
        key: `${item.kind}-${item.url}`,
        eyebrow: 'Continue',
        title: item.title,
        detail: item.detail,
        url: item.url,
        cta: 'Continue',
      })
    }
    return rows
  }, [data.mock, data.resumeItems])

  // Previously shared community links retain their original destinations and filters.
  if (params.has('section') || params.has('tab') || params.has('discussion')) {
    const nextParams = new URLSearchParams(params)
    nextParams.delete('section')
    return <Navigate replace to={'/community?' + nextParams} />
  }

  return (
    <div className="ed-gutter-shell" data-screen="home">
      <div className="finna-page finna-home">
        <h1 className="sr-only">Your study home</h1>

      <OfflineBanner
        lastLoadedAt={data.lastLoadedAt}
        onRetry={() => setRetry((n) => n + 1)}
        retrying={data.loading}
      />

      <WelcomeBackBar resumeUrl={returnRows[0]?.url ?? null} />

      {/* 4-Tile KPI Strip (§VII.19.8, Dashboards v2) */}
      <section className="finna-kpi-strip" aria-label="Study snapshot">
        <div className="finna-kpi-tile">
          <div className="finna-kpi-icon bg-practice-soft text-practice-dark" aria-hidden="true">✎</div>
          <div className="finna-kpi-body">
            <div className="finna-kpi-value">{p ? weekAnswers.toLocaleString('en-IN') : '—'}</div>
            <div className="finna-kpi-label">Answered this week</div>
          </div>
        </div>
        <div className="finna-kpi-tile">
          <div className="finna-kpi-icon bg-correct-soft text-correct-dark" aria-hidden="true">✓</div>
          <div className="finna-kpi-body">
            <div className={`finna-kpi-value${weekAccuracy === null ? ' finna-kpi-value--na' : ''}`}>
              {weekAccuracy ?? '—'}
            </div>
            <div className="finna-kpi-label">7-day accuracy</div>
          </div>
        </div>
        <div className="finna-kpi-tile">
          <div className="finna-kpi-icon bg-exams-soft text-exams-dark" aria-hidden="true">★</div>
          <div className="finna-kpi-body">
            <div className={`finna-kpi-value${!p ? ' finna-kpi-value--na' : ''}`}>
              {p ? `${p.current_streak}d` : '—'}
            </div>
            <div className="finna-kpi-label">
              {p?.streak_basis === 'device activity' ? 'Device streak' : 'Current streak'}
            </div>
          </div>
        </div>
        <div className="finna-kpi-tile">
          <div className="finna-kpi-icon bg-learn-soft text-learn-dark" aria-hidden="true">◎</div>
          <div className="finna-kpi-body">
            <div className={`finna-kpi-value${coverage === null ? ' finna-kpi-value--na' : ''}`}>
              {coverage !== null ? `${coverage}%` : '—'}
            </div>
            <div className="finna-kpi-label">{exam ? `${examTitle} coverage` : 'Exam coverage'}</div>
          </div>
        </div>
      </section>

      {data.primaryError && (
        <section className="finna-card mb-4 border-wrong bg-wrong-soft" role="alert">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-semibold text-wrong-dark">
              Couldn’t load your study dashboard right now.
            </p>
            <button
              type="button"
              onClick={() => setRetry((n) => n + 1)}
              className="finna-btn"
            >
              Try again
            </button>
          </div>
        </section>
      )}

      <div className="finna-home-grid">
        {/* Left Column: Exam Hero + Today Plan */}
        <aside className="finna-home-side" aria-label="Your exam and study plan">
          <section className="finna-exam-hero" aria-labelledby="my-exam-title">
            <div className="finna-hero-head">
              <div className="min-w-0">
                <div className="finna-eyebrow">My exam</div>
                <h2 id="my-exam-title" className="mt-1 text-3xl font-bold leading-none tracking-tight">
                  {data.loading && !exam ? 'Your exam' : examTitle}
                </h2>
                {exam && (
                  <p className="finna-exam-description">
                    {exam.id === 'udc'
                      ? 'Upper Division Clerk'
                      : exam.id === 'ldc'
                        ? 'Lower Division Clerk'
                        : examPresentation(exam.id).category}
                  </p>
                )}
              </div>
              {data.exams.length > 0 ? (
                <label className="finna-hero-change relative">
                  Change
                  <select
                    aria-label="Choose my exam"
                    value={exam?.id || ''}
                    disabled={savingExam}
                    onChange={(e) => void chooseExam(e.target.value)}
                    className="absolute inset-0 w-full cursor-pointer opacity-0"
                  >
                    {data.exams.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.title}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <Link className="finna-hero-change" to="/exams">
                  Find
                </Link>
              )}
            </div>
            <div className="finna-hero-stats">
              <div>
                <strong>{exam ? exam.questions.toLocaleString('en-IN') : '—'}</strong>
                <small>questions in your exam bank</small>
              </div>
              <div>
                <strong>{coverage !== null ? `${coverage}%` : '—'}</strong>
                <small>of bank answered</small>
              </div>
            </div>
            <div className="finna-hero-actions">
              <Link to={exam ? '/practice?exam=' + encodeURIComponent(exam.id) : '/practice'}>
                Practice
              </Link>
              <Link
                to={
                  exam
                    ? '/practice?exam=' + encodeURIComponent(exam.id) + '&timer=on'
                    : '/practice?timer=on'
                }
              >
                Timed run
              </Link>
            </div>
          </section>
          {examError && (
            <p role="alert" className="text-sm text-wrong">
              {examError}
            </p>
          )}
          <TodayCard exams={data.exams} />
        </aside>

        {/* Center Main Stream: Today-Led Study Workspace (Return Block + QuickStudy + Subject Mastery) */}
        <section className="finna-home-stream" aria-label="Continue learning and subject progress">
          {returnRows.length > 0 && (
            <section className="finna-card" aria-labelledby="return-block-title">
              <div className="finna-section-top">
                <h2 id="return-block-title">Pick up where you left off</h2>
                <Link to="/revise">Revision queue →</Link>
              </div>
              <div className="finna-return-list">
                {returnRows.map((row) => (
                  <div key={row.key} className="finna-return-row">
                    <div className="min-w-0 flex-1">
                      <span className="finna-eyebrow">{row.eyebrow}</span>
                      <strong>{row.title}</strong>
                      <small>{row.detail}</small>
                    </div>
                    <Link to={row.url} className="finna-btn">
                      {row.cta}
                    </Link>
                  </div>
                ))}
              </div>
            </section>
          )}

          {!data.mock && <QuickStudy compact initialExam={exam?.id} />}

          {/* Deterministic Subject Progress with 6-slot colour chips (§VII.19.8) */}
          <section className="finna-card" aria-labelledby="subject-progress-title">
            <div className="finna-section-top">
              <h2 id="subject-progress-title">Subject progress</h2>
              <Link to="/library">All subjects →</Link>
            </div>
            {subjects.length > 0 ? (
              <div className="flex flex-col gap-3">
                {subjects.map((s) => {
                  const pct = s.answered ? Math.round((s.correct / s.answered) * 100) : null
                  return (
                    <Link
                      key={s.subject_id}
                      to={'/bank?subject_id=' + encodeURIComponent(s.subject_id)}
                      className="flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-canvas"
                    >
                      <span
                        className={`${subjectChipClass(s.subject)} finna-subj-chip--sq`}
                        aria-hidden="true"
                      >
                        {subjectInitials(s.subject)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-baseline justify-between gap-2 text-sm">
                          <span className="truncate font-semibold text-ink">{s.subject}</span>
                          <span className="font-mono text-xs font-semibold text-secondary">
                            {pct !== null ? `${pct}%` : '—'} · {s.answered.toLocaleString('en-IN')} Q
                          </span>
                        </div>
                        <div className="finna-progress">
                          <span style={{ width: `${Math.min(100, pct ?? 0)}%` }} />
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm leading-relaxed text-secondary">
                {data.loading
                  ? 'Loading your subject progress…'
                  : 'Answer a few questions to see which subjects are getting stronger.'}
              </p>
            )}
          </section>

          {/* Personal Question Vault showcase card with animated opening safe */}
          <VaultShowcaseCard />

          {/* Compact Community & Creation Gateway (replaces embedded social feed clutter) */}
          <section className="finna-card" aria-labelledby="community-gateway-title">
            <div className="finna-section-top">
              <h2 id="community-gateway-title">Community & study guides</h2>
              <Link to="/community">Open feed →</Link>
            </div>
            <p className="text-sm leading-relaxed text-secondary">
              Discuss tricky past-paper questions, read first-party concept guides, or share worked explanations.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link to="/bank?study_status=ever_wrong" className="finna-btn">
                Missed questions
              </Link>
              <Link to="/guides" className="finna-btn finna-btn-quiet">
                Concept guides
              </Link>
              <Link to="/community?tab=questions" className="finna-btn finna-btn-quiet">
                Ask a doubt
              </Link>
              <Link to="/create/new?kind=new_question" className="finna-btn finna-btn-quiet">
                Submit MCQ
              </Link>
            </div>
          </section>
        </section>

        {/* Right Rail: Compact Month Calendar + Saved Collections + Desk */}
        <aside className="finna-home-side finna-home-right" aria-label="Calendar, saved work and study desk">
          {/* Compact Month Calendar (§VII.19.8, Dashboards v2) */}
          <section className="finna-card" aria-labelledby="mini-cal-title">
            <div className="finna-section-top">
              <h2 id="mini-cal-title">Study & exam calendar</h2>
              <Link to="/calendar">Full view</Link>
            </div>
            <div className="finna-mini-cal-head">
              <button
                type="button"
                className="finna-mini-cal-nav"
                onClick={() => setMonthOffset((m) => m - 1)}
                aria-label="Previous month"
              >
                ‹
              </button>
              <strong>
                {MONTHS[calBase.month]} {calBase.year}
              </strong>
              <button
                type="button"
                className="finna-mini-cal-nav"
                onClick={() => setMonthOffset((m) => m + 1)}
                aria-label="Next month"
              >
                ›
              </button>
            </div>
            <div className="finna-mini-cal-grid" role="grid" aria-label={`${MONTHS[calBase.month]} ${calBase.year}`}>
              {WEEKDAYS.map((w) => (
                <span key={w} className="finna-mini-cal-dow">
                  {w}
                </span>
              ))}
              {Array.from({ length: calBase.firstDow }).map((_, i) => (
                <span key={`pad-${i}`} />
              ))}
              {Array.from({ length: calBase.daysInMonth }).map((_, i) => {
                const day = i + 1
                const dayStr = `${calBase.ym}-${String(day).padStart(2, '0')}`
                const isToday = dayStr === today
                const hasPractice = practisedDays.has(day)
                const hasExam = examEventDays.has(day)
                return (
                  <span
                    key={day}
                    className={`finna-mini-cal-day${isToday ? ' is-today' : ''}`}
                    title={
                      [
                        hasPractice ? 'Practised' : '',
                        hasExam ? 'Exam calendar event' : '',
                      ]
                        .filter(Boolean)
                        .join(' · ') || undefined
                    }
                  >
                    {day}
                    {(hasPractice || hasExam) && (
                      <span className="finna-mini-cal-dots" aria-hidden="true">
                        {hasPractice && <i className="finna-dot-practice" />}
                        {hasExam && <i className="finna-dot-exam" />}
                      </span>
                    )}
                  </span>
                )
              })}
            </div>
            <div className="finna-mini-cal-legend">
              <span>
                <i className="finna-dot-practice" /> Practised
              </span>
              <span>
                <i className="finna-dot-exam" /> Exam date
              </span>
            </div>
          </section>

          <section className="finna-card">
            <div className="finna-section-top">
              <h2>Saved collections</h2>
              <Link to="/library?library_view=saved">View all</Link>
            </div>
            {data.saved.length > 0 ? (
              data.exams
                .filter((e) => data.saved.includes(e.id))
                .slice(0, 4)
                .map((e) => (
                  <Link to={'/exams/' + e.id} key={e.id} className="finna-plan-item">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-learn-soft text-xs font-bold text-learn-dark">
                      {examPresentation(e.id).short}
                    </span>
                    <span className="text-sm font-semibold">{e.title}</span>
                  </Link>
                ))
            ) : (
              <p className="text-sm leading-relaxed text-secondary">
                Save an exam or study material to find it here.
              </p>
            )}
            <Link to="/revise" className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-link">
              Revise questions & mistakes →
            </Link>
          </section>

          <section className="finna-card">
            <h2>Make room for learning</h2>
            <p className="mt-2 text-sm leading-relaxed text-secondary">
              One focused session. Your questions, notes and study companions in one place.
            </p>
            <Link to="/desk" className="finna-btn finna-btn-quiet mt-4 w-full">
              Open study desk →
            </Link>
          </section>

          <section className="finna-card">
            <h2>Today’s quests</h2>
            <p className="mt-2 text-sm leading-relaxed text-secondary">
              See your daily learning goals and earned rewards.
            </p>
            <Link
              to="/profile/rewards"
              className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-rewards-dark"
            >
              View your quests →
            </Link>
          </section>
        </aside>
      </div>
      </div>

      {/* Outer Margin Feature Spotlight Deck (sits outside the 3-col page margin to preserve Calendar space) */}
      <div className="ed-gutter-dock">
        <ExploreDeckRail heading="Also on Finna" compact />
      </div>
    </div>
  )
}
