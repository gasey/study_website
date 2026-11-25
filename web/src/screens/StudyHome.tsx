import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import {
  currentMock,
  listCollections,
  listTaxonomy,
  isLaterExamCollection,
  isSubjectModule,
  getExamProgress,
  getExamBookmarks,
  getFocusSubjects,
  getProgress,
  removeExamBookmark,
  saveExamBookmark,
  saveFocusSubjects,
  setPrimaryExam,
  type MockSession,
  type Collection,
  type ExamProgressSummary,
  type Progress,
  type TaxonomyFacet,
} from '../lib/api'
import { reviewSession } from '../lib/review'
import { learningRequest, type ResumePage, type ResumeItem } from '../lib/learning'
import { accountContext } from '../lib/accountContext'
import { useExamScope } from '../lib/examScope'
import { choosePreferredExam, usePreferredExam } from '../lib/preferredExam'
import {
  MAX_FOCUS_SUBJECTS,
  addLocalTrackedExam,
  hydrateTrackedExams,
  removeLocalTrackedExam,
  resolveTrackedExams,
  shortExamLabel,
  useLocalFocusSubjectIds,
  useTrackedExamIds,
  writeLocalFocusSubjects,
} from '../lib/trackedExams'
import { FLAGSHIP_EXAM_IDS, examPresentation } from '../lib/examPresentation'
import { calendarRead, indiaToday, type CalendarEvent } from '../lib/calendar'
import { subjectChipClass, subjectInitials } from '../lib/subjectChips'
import QuickStudy from '../components/QuickStudy'
import TodayCard from '../components/TodayCard'
import OfflineBanner from '../components/OfflineBanner'
import WelcomeBackBar from '../components/WelcomeBackBar'
import ExploreDeckRail from '../components/ExploreDeckRail'
import VaultShowcaseCard from '../components/VaultShowcaseCard'
import ExamPickerDialog from '../components/ExamPickerDialog'
import HomeFeedPreview from '../components/HomeFeedPreview'
import SubjectBookshelf from '../components/SubjectBookshelf'
import { mockResumePath } from '../lib/sharedTests'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

type HomeView = 'overview' | 'exams' | 'feed'

type SubjectOption = {
  id: string
  label: string
  questions: number
}

type StudyData = {
  exams: Collection[]
  subjectModules: Collection[]
  examProgress: ExamProgressSummary[]
  saved: string[]
  progress: Progress | null
  resumeItems: ResumeItem[]
  mock: MockSession | null
  calendarEvents: CalendarEvent[]
  taxonomy: TaxonomyFacet[]
  authenticated: boolean
  loading: boolean
  primaryError: boolean
  lastLoadedAt: number | null
}

const EMPTY: StudyData = {
  exams: [],
  subjectModules: [],
  examProgress: [],
  saved: [],
  progress: null,
  resumeItems: [],
  mock: null,
  calendarEvents: [],
  taxonomy: [],
  authenticated: false,
  loading: true,
  primaryError: false,
  lastLoadedAt: null,
}

const SAFE_RESUME_RE = /^\/(bank|exams|group-b|english|mizo|arithmetic|essay|library|desk|tests|practice|revise|guides)([/?#]|$)/

export default function StudyHome() {
  const [params, setParams] = useSearchParams()
  const scope = useExamScope()
  const [retry, setRetry] = useState(0)
  const [data, setData] = useState<StudyData>(EMPTY)
  const [examError, setExamError] = useState('')
  const [busyExamId, setBusyExamId] = useState<string | null>(null)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [monthOffset, setMonthOffset] = useState(0)

  // Multi-subject focus UI state
  const localFocusIds = useLocalFocusSubjectIds()
  const [focusEditorOpen, setFocusEditorOpen] = useState(false)
  const [draftFocusIds, setDraftFocusIds] = useState<string[]>([])
  const [savingFocus, setSavingFocus] = useState(false)
  const [focusError, setFocusError] = useState('')
  const [subjectFilter, setSubjectFilter] = useState<'focus' | 'all'>('all')

  const rawView = params.get('view')
  const view: HomeView = rawView === 'exams' || rawView === 'feed' ? rawView : 'overview'
  const setView = (nextView: HomeView) => {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous)
        if (nextView === 'overview') next.delete('view')
        else next.set('view', nextView)
        return next
      },
      { replace: true },
    )
  }

  const today = indiaToday()
  const trackedIds = useTrackedExamIds()

  async function choosePrimaryExam(id: string) {
    setBusyExamId(id)
    setExamError('')
    addLocalTrackedExam(id)
    choosePreferredExam(id)
    try {
      const ctx = await accountContext()
      if (ctx.authenticated) {
        await setPrimaryExam(id)
      } else {
        await saveExamBookmark(id).catch(() => {})
      }
      setData((prev) => ({
        ...prev,
        saved: prev.saved.includes(id) ? prev.saved : [id, ...prev.saved],
      }))
    } catch (e) {
      setExamError((e as Error).message)
    } finally {
      setBusyExamId(null)
    }
  }

  async function toggleTrackExam(id: string) {
    const currentlyTracked = trackedExams.some((e) => e.id === id)
    if (currentlyTracked && trackedExams.length <= 1) return

    setBusyExamId(id)
    setExamError('')
    try {
      if (currentlyTracked) {
        removeLocalTrackedExam(id)
        const remaining = trackedExams.filter((e) => e.id !== id)
        if (exam?.id === id && remaining[0]) {
          choosePreferredExam(remaining[0].id)
        }
        await removeExamBookmark(id).catch(() => {})
        setData((prev) => ({ ...prev, saved: prev.saved.filter((item) => item !== id) }))
        if (exam?.id === id && remaining[0] && data.authenticated) {
          await setPrimaryExam(remaining[0].id).catch(() => {})
        }
      } else {
        addLocalTrackedExam(id)
        // Ensure active exam is also saved on the server so bookmarks reflect all tracked exams
        if (exam && !data.saved.includes(exam.id)) {
          addLocalTrackedExam(exam.id)
          await saveExamBookmark(exam.id).catch(() => {})
        }
        await saveExamBookmark(id).catch(() => {})
        setData((prev) => ({
          ...prev,
          saved: Array.from(new Set([...prev.saved, ...(exam ? [exam.id] : []), id])),
        }))
      }
    } catch (e) {
      setExamError((e as Error).message)
    } finally {
      setBusyExamId(null)
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
        patch({
          exams: rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)),
          subjectModules: rows.filter((c) => isSubjectModule(c)),
        }),
      ),
      getProgress().then((progress) => patch({ progress })),
      getExamProgress().then((examProgress) => patch({ examProgress })),
    ]

    // Secondary requests fail independently so they never blank the whole home screen
    void getExamBookmarks()
      .then((saved) => {
        if (!live) return
        patch({ saved: saved.collection_ids })
        hydrateTrackedExams(saved.collection_ids, saved.primary_collection_id)
      })
      .catch(() => {})

    void listTaxonomy('all', true)
      .then((taxonomy) => patch({ taxonomy }))
      .catch(() => {})

    void currentMock()
      .then((mock) => patch({ mock }))
      .catch(() => {})

    void accountContext()
      .then(async (a) => {
        patch({ authenticated: a.authenticated })
        if (!a.authenticated) return
        void getFocusSubjects()
          .then((f) => {
            if (!live) return
            const ids = f.items.map((item) => item.subject_id)
            writeLocalFocusSubjects(ids)
            if (ids.length > 0) setSubjectFilter('focus')
          })
          .catch(() => {})
        const s = await reviewSession()
        const r = await learningRequest<ResumePage>('/resume?exam_scope=' + scope, s.user_id)
        patch({
          resumeItems: (r.items || [])
            .filter((i) => i.kind !== 'desk' && SAFE_RESUME_RE.test(i.url))
            .slice(0, 3),
        })
      })
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

  // Keep local focus filter aligned if user saves focus subjects inside TodayCard
  useEffect(() => {
    const syncFocus = () => {
      void accountContext()
        .then((a) => (a.authenticated ? getFocusSubjects() : null))
        .then((f) => {
          if (f) writeLocalFocusSubjects(f.items.map((i) => i.subject_id))
        })
        .catch(() => {})
    }
    window.addEventListener('ism-focus-change', syncFocus)
    return () => window.removeEventListener('ism-focus-change', syncFocus)
  }, [])

  // Load month calendar exam dates for the visible mini-calendar month
  const calBase = useMemo(() => {
    const [y, m] = today.split('-').map(Number)
    const d = new Date(Date.UTC(y, m - 1 + monthOffset, 1))
    const year = d.getUTCFullYear()
    const month = d.getUTCMonth()
    const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate()
    const firstDow = (d.getUTCDay() + 6) % 7 // Monday-first
    const ym = `${year}-${String(month + 1).padStart(2, '0')}`
    return {
      year,
      month,
      daysInMonth,
      firstDow,
      start: `${ym}-01`,
      end: `${ym}-${String(daysInMonth).padStart(2, '0')}`,
      ym,
    }
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
  const trackedExams = useMemo(
    () => resolveTrackedExams(data.exams, trackedIds, exam),
    [data.exams, trackedIds, exam],
  )
  const progressByExam = useMemo(
    () => new Map(data.examProgress.map((row) => [row.collection_id, row])),
    [data.examProgress],
  )
  const progressRecord = useMemo(
    () => Object.fromEntries(data.examProgress.map((row) => [row.collection_id, row])),
    [data.examProgress],
  )

  const examProgress = exam ? progressByExam.get(exam.id) : undefined
  const coverage =
    exam && examProgress && exam.questions
      ? Math.min(100, Math.round((examProgress.unique_questions / exam.questions) * 100))
      : null
  const p = data.progress
  const examTitle = exam ? shortExamLabel(exam) : 'Choose your exam'

  // Popular sibling exams for quick 1-click multi-exam discovery
  const suggestedSiblingExams = useMemo(() => {
    const trackedSet = new Set(trackedExams.map((e) => e.id))
    const flagshipRank = (id: string) => {
      const i = FLAGSHIP_EXAM_IDS.indexOf(id as (typeof FLAGSHIP_EXAM_IDS)[number])
      return i >= 0 ? i : 99
    }
    return data.exams
      .filter((e) => !trackedSet.has(e.id))
      .sort((a, b) => flagshipRank(a.id) - flagshipRank(b.id) || b.questions - a.questions)
      .slice(0, 4)
  }, [data.exams, trackedExams])

  // Aggregate unique subjects from taxonomy + user progress for multi-subject focus picker
  const subjectCatalog = useMemo<SubjectOption[]>(() => {
    const map = new Map<string, SubjectOption>()
    for (const facet of data.taxonomy) {
      if (!facet.subject_id) continue
      const existing = map.get(facet.subject_id)
      const qCount = facet.subject_questions ?? facet.questions
      if (!existing) {
        map.set(facet.subject_id, {
          id: facet.subject_id,
          label: facet.subject,
          questions: qCount,
        })
      } else if (!facet.subject_questions) {
        existing.questions += facet.questions
      }
    }
    for (const s of p?.subjects || []) {
      if (!map.has(s.subject_id)) {
        map.set(s.subject_id, { id: s.subject_id, label: s.subject, questions: 0 })
      }
    }
    return Array.from(map.values()).sort((a, b) => b.questions - a.questions || a.label.localeCompare(b.label))
  }, [data.taxonomy, p?.subjects])

  const progressBySubject = useMemo(
    () => new Map((p?.subjects || []).map((s) => [s.subject_id, s])),
    [p?.subjects],
  )

  const activeFocusSubjects = useMemo(() => {
    const byId = new Map(subjectCatalog.map((s) => [s.id, s]))
    return localFocusIds
      .map((id) => byId.get(id) || (progressBySubject.has(id) ? { id, label: progressBySubject.get(id)!.subject, questions: 0 } : null))
      .filter((s): s is SubjectOption => s !== null)
  }, [localFocusIds, subjectCatalog, progressBySubject])

  const displayedSubjects = useMemo(() => {
    if (subjectFilter === 'focus' && activeFocusSubjects.length > 0) {
      return activeFocusSubjects.map((s) => {
        const stats = progressBySubject.get(s.id)
        return {
          subject_id: s.id,
          subject: s.label,
          answered: stats?.answered ?? 0,
          correct: stats?.correct ?? 0,
          focused: true,
        }
      })
    }
    const focusSet = new Set(localFocusIds)
    return [...(p?.subjects || [])]
      .sort((a, b) => {
        const aFocus = focusSet.has(a.subject_id) ? 0 : 1
        const bFocus = focusSet.has(b.subject_id) ? 0 : 1
        if (aFocus !== bFocus) return aFocus - bFocus
        return b.answered - a.answered
      })
      .slice(0, 6)
      .map((s) => ({
        subject_id: s.subject_id,
        subject: s.subject,
        answered: s.answered,
        correct: s.correct,
        focused: focusSet.has(s.subject_id),
      }))
  }, [subjectFilter, activeFocusSubjects, progressBySubject, p?.subjects, localFocusIds])

  function openFocusEditor() {
    setDraftFocusIds(localFocusIds)
    setFocusError('')
    setFocusEditorOpen((open) => !open)
  }

  function toggleDraftSubject(subjectId: string) {
    setDraftFocusIds((prev) => {
      if (prev.includes(subjectId)) return prev.filter((id) => id !== subjectId)
      if (prev.length >= MAX_FOCUS_SUBJECTS) return prev
      return [...prev, subjectId]
    })
  }

  async function commitFocusSubjects(nextIds: string[]) {
    setSavingFocus(true)
    setFocusError('')
    try {
      if (data.authenticated) {
        await saveFocusSubjects(nextIds)
      }
      writeLocalFocusSubjects(nextIds)
      if (nextIds.length > 0) setSubjectFilter('focus')
      else setSubjectFilter('all')
      setFocusEditorOpen(false)
      window.dispatchEvent(new Event('ism-focus-change'))
    } catch (e) {
      setFocusError((e as Error).message)
    } finally {
      setSavingFocus(false)
    }
  }

  const weekCutoff = new Date(Date.parse(today + 'T12:00:00Z') - 6 * 86400000)
    .toISOString()
    .slice(0, 10)
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
    const rows: {
      key: string
      eyebrow: string
      title: string
      detail: string
      url: string
      cta: string
    }[] = []
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
            <div className="finna-kpi-icon bg-practice-soft text-practice-dark" aria-hidden="true">
              ✎
            </div>
            <div className="finna-kpi-body">
              <div className="finna-kpi-value">{p ? weekAnswers.toLocaleString('en-IN') : '—'}</div>
              <div className="finna-kpi-label">Answered this week</div>
            </div>
          </div>
          <div className="finna-kpi-tile">
            <div className="finna-kpi-icon bg-correct-soft text-correct-dark" aria-hidden="true">
              ✓
            </div>
            <div className="finna-kpi-body">
              <div className={`finna-kpi-value${weekAccuracy === null ? ' finna-kpi-value--na' : ''}`}>
                {weekAccuracy ?? '—'}
              </div>
              <div className="finna-kpi-label">7-day accuracy</div>
            </div>
          </div>
          <div className="finna-kpi-tile">
            <div className="finna-kpi-icon bg-exams-soft text-exams-dark" aria-hidden="true">
              ★
            </div>
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
            <div className="finna-kpi-icon bg-learn-soft text-learn-dark" aria-hidden="true">
              ◎
            </div>
            <div className="finna-kpi-body">
              <div className={`finna-kpi-value${coverage === null ? ' finna-kpi-value--na' : ''}`}>
                {coverage !== null ? `${coverage}%` : '—'}
              </div>
              <div className="finna-kpi-label">
                {exam
                  ? trackedExams.length > 1
                    ? `${examTitle} · ${trackedExams.length} exams`
                    : `${examTitle} coverage`
                  : 'Exam coverage'}
              </div>
            </div>
          </div>
        </section>

        {data.primaryError && (
          <section className="finna-card mb-4 border-wrong bg-wrong-soft" role="alert">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-wrong-dark">
                Couldn’t load your study dashboard right now.
              </p>
              <button type="button" onClick={() => setRetry((n) => n + 1)} className="finna-btn">
                Try again
              </button>
            </div>
          </section>
        )}

        <div className="finna-home-grid">
          {/* Left Column: Multi-Exam Hero + Today Plan */}
          <aside className="finna-home-side" aria-label="Your exams and study plan">
            <section className="finna-exam-hero" aria-labelledby="my-exam-title">
              <div className="finna-hero-head">
                <div className="min-w-0">
                  <div className="finna-eyebrow">
                    {trackedExams.length > 1 ? `My exams · ${trackedExams.length} tracked` : 'My exam'}
                  </div>
                  <h2 id="my-exam-title" className="mt-1 text-3xl font-bold leading-none tracking-tight">
                    {data.loading && !exam ? 'Your exam' : examTitle}
                  </h2>
                  {exam && (
                    <p className="finna-exam-description">
                      {exam.id === 'udc'
                        ? 'Upper Division Clerk'
                        : exam.id === 'ldc'
                          ? 'Lower Division Clerk'
                          : examPresentation(exam.id, exam.title).category}
                    </p>
                  )}
                </div>
                {data.exams.length > 0 ? (
                  <button
                    type="button"
                    className="finna-hero-change"
                    onClick={() => setPickerOpen(true)}
                  >
                    {trackedExams.length > 1 ? 'Manage' : '+ Exams'}
                  </button>
                ) : (
                  <Link className="finna-hero-change" to="/exams">
                    Find
                  </Link>
                )}
              </div>

              {/* Quick switcher pills for students tracking multiple exams */}
              {trackedExams.length > 0 && (
                <div className="finna-hero-exam-pills" role="group" aria-label="Switch active exam">
                  {trackedExams.map((item) => {
                    const isActive = item.id === exam?.id
                    return (
                      <button
                        key={item.id}
                        type="button"
                        aria-pressed={isActive}
                        disabled={busyExamId === item.id}
                        onClick={() => void choosePrimaryExam(item.id)}
                        className={`finna-hero-pill${isActive ? ' is-active' : ''}`}
                        title={item.title}
                      >
                        {shortExamLabel(item)}
                      </button>
                    )
                  })}
                  <button
                    type="button"
                    onClick={() => setPickerOpen(true)}
                    className="finna-hero-pill finna-hero-pill--add"
                    aria-label="Add another exam"
                  >
                    + Add
                  </button>
                </div>
              )}

              <div className="finna-hero-stats">
                <div>
                  <strong>{exam ? exam.questions.toLocaleString('en-IN') : '—'}</strong>
                  <small>questions in bank</small>
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
              {exam && (
                <Link to={'/exams/' + exam.id} className="finna-hero-sublink">
                  Open {examTitle} papers &amp; syllabus →
                </Link>
              )}
            </section>
            {examError && (
              <p role="alert" className="text-sm text-wrong">
                {examError}
              </p>
            )}
            <TodayCard exams={data.exams} hideExamSelect />
          </aside>

          {/* Center Main Stream: View Switcher + Multi-Exam + Focus Subjects + Live Community Feed */}
          <section className="finna-home-stream" aria-label="Study workspace and community">
            {/* Workspace View Switcher */}
            <div className="finna-home-viewbar">
              <div className="finna-segments" role="tablist" aria-label="Home workspace views">
                <button
                  type="button"
                  role="tab"
                  aria-selected={view === 'overview'}
                  onClick={() => setView('overview')}
                >
                  Overview
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={view === 'exams'}
                  onClick={() => setView('exams')}
                >
                  My exams
                  {trackedExams.length > 0 && (
                    <span className="finna-tab-count">{trackedExams.length}</span>
                  )}
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={view === 'feed'}
                  onClick={() => setView('feed')}
                >
                  Community feed
                </button>
              </div>
            </div>

            {view === 'overview' && (
              <>
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

                {/* Multi-Exam Workspace Card */}
                {trackedExams.length > 1 ? (
                  <section className="finna-card" aria-labelledby="tracked-exams-title">
                    <div className="finna-section-top">
                      <div>
                        <span className="finna-eyebrow">Multi-exam board</span>
                        <h2 id="tracked-exams-title" className="mt-0.5">
                          Your exams side by side
                        </h2>
                      </div>
                      <button
                        type="button"
                        onClick={() => setPickerOpen(true)}
                        className="text-xs font-bold text-link hover:underline"
                      >
                        + Add / manage →
                      </button>
                    </div>
                    <div className="finna-multi-exam-grid">
                      {trackedExams.map((item) => {
                        const isPrimary = item.id === exam?.id
                        const pres = examPresentation(item.id, item.title)
                        const prog = progressByExam.get(item.id)
                        const pct =
                          prog && item.questions > 0
                            ? Math.min(100, Math.round((prog.unique_questions / item.questions) * 100))
                            : 0
                        const acc =
                          prog && prog.answered > 0
                            ? `${Math.round((prog.correct / prog.answered) * 100)}%`
                            : null
                        return (
                          <article
                            key={item.id}
                            className={`finna-mini-exam-card${isPrimary ? ' is-primary' : ''}`}
                          >
                            <div className="finna-mini-exam-top">
                              <span className="finna-exam-stamp" aria-hidden="true">
                                {pres.short}
                              </span>
                              <div className="min-w-0 flex-1">
                                <h3 className="truncate text-sm font-bold text-ink">{item.title}</h3>
                                <p className="text-xs text-secondary">
                                  {item.questions.toLocaleString('en-IN')} Q
                                  {prog && prog.answered > 0 ? ` · ${acc} acc.` : ''}
                                </p>
                              </div>
                              {isPrimary ? (
                                <span className="finna-primary-badge">Primary</span>
                              ) : (
                                <button
                                  type="button"
                                  disabled={busyExamId === item.id}
                                  onClick={() => void choosePrimaryExam(item.id)}
                                  className="finna-mini-switch-btn"
                                >
                                  Focus
                                </button>
                              )}
                            </div>
                            <div className="mt-2.5">
                              <div className="mb-1 flex justify-between text-[11px] font-semibold text-secondary">
                                <span>
                                  {prog ? `${prog.unique_questions.toLocaleString('en-IN')} covered` : 'Not started yet'}
                                </span>
                                <span className="font-mono">{pct}%</span>
                              </div>
                              <div className="finna-progress">
                                <span style={{ width: `${pct}%` }} />
                              </div>
                            </div>
                            <div className="finna-mini-exam-actions">
                              <Link
                                to={'/practice?exam=' + encodeURIComponent(item.id)}
                                className="finna-mini-act finna-mini-act--primary"
                              >
                                Practice
                              </Link>
                              <Link
                                to={'/past-papers?exam=' + encodeURIComponent(item.id)}
                                className="finna-mini-act"
                              >
                                Papers
                              </Link>
                              <Link to={'/exams/' + item.id} className="finna-mini-act">
                                Open
                              </Link>
                            </div>
                          </article>
                        )
                      })}
                    </div>
                  </section>
                ) : (
                  !data.loading &&
                  suggestedSiblingExams.length > 0 && (
                    <section className="finna-card finna-add-exam-banner" aria-labelledby="add-exam-title">
                      <div className="finna-section-top mb-2">
                        <div>
                          <span className="finna-eyebrow">Multi-exam prep</span>
                          <h2 id="add-exam-title" className="mt-0.5">
                            Preparing for more than one exam?
                          </h2>
                        </div>
                        <button
                          type="button"
                          onClick={() => setPickerOpen(true)}
                          className="text-xs font-bold text-link hover:underline"
                        >
                          All exams →
                        </button>
                      </div>
                      <p className="text-sm text-secondary">
                        Pin other exams to track progress side by side and switch in one tap without losing your plan.
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {suggestedSiblingExams.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            disabled={busyExamId === item.id}
                            onClick={() => void toggleTrackExam(item.id)}
                            className="finna-quick-add-exam-pill"
                          >
                            <span aria-hidden="true">+</span> {shortExamLabel(item)}
                          </button>
                        ))}
                      </div>
                    </section>
                  )
                )}

                {/* Unified All-Exam Subject Bookshelf + Focus Subjects & Live Progress */}
                {data.subjectModules.length > 0 ? (
                  <SubjectBookshelf
                    subjects={data.subjectModules}
                    progress={progressRecord}
                    focusedSubjectIds={localFocusIds}
                    variant="compact"
                    eyebrow="All-exam subject books"
                    heading="Subjects & your focus"
                    subtitle="Questions from UDC, LDC, MCS & Group B combined into 5 subject books — pick up to 5 focus subjects to guide your daily plan."
                    action={
                      <>
                        {subjectCatalog.length > 0 && (
                          <button
                            type="button"
                            onClick={openFocusEditor}
                            className="finna-inline-pill-btn"
                            aria-expanded={focusEditorOpen}
                          >
                            {focusEditorOpen
                              ? 'Close picker'
                              : `Focus subjects · ${activeFocusSubjects.length}/${MAX_FOCUS_SUBJECTS}`}
                          </button>
                        )}
                        <Link
                          to="/library"
                          className="text-xs font-bold text-link hover:underline"
                        >
                          Library →
                        </Link>
                      </>
                    }
                    footer={
                      <div aria-label="Focus subjects and subject accuracy">
                        {/* Inline Multi-Subject Picker */}
                        {focusEditorOpen && (
                          <div className="finna-focus-drawer">
                            <p className="text-xs leading-relaxed text-secondary">
                              Choose <strong>2–{MAX_FOCUS_SUBJECTS} subjects</strong> to focus on across your exams
                              (e.g., English + GK + Arithmetic). Selecting too many spreads practice thin; all due
                              reviews still stay in your queue.
                            </p>
                            <div className="finna-focus-chip-grid" role="group" aria-label="Select focus subjects">
                              {subjectCatalog.map((subj) => {
                                const selected = draftFocusIds.includes(subj.id)
                                const maxed = !selected && draftFocusIds.length >= MAX_FOCUS_SUBJECTS
                                return (
                                  <button
                                    key={subj.id}
                                    type="button"
                                    aria-pressed={selected}
                                    disabled={savingFocus || maxed}
                                    onClick={() => toggleDraftSubject(subj.id)}
                                    className={`finna-focus-toggle${selected ? ' is-selected' : ''}`}
                                  >
                                    <span
                                      className={`${subjectChipClass(subj.label)} finna-focus-dot`}
                                      aria-hidden="true"
                                    >
                                      {selected ? '✓' : subjectInitials(subj.label)}
                                    </span>
                                    <span className="truncate">{subj.label}</span>
                                    {subj.questions > 0 && (
                                      <span className="finna-focus-qcount">
                                        {subj.questions.toLocaleString('en-IN')}
                                      </span>
                                    )}
                                  </button>
                                )
                              })}
                            </div>
                            {focusError && (
                              <p role="alert" className="mt-2 text-xs font-semibold text-wrong">
                                {focusError}
                              </p>
                            )}
                            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-hairline pt-3">
                              <span className="text-xs text-secondary">
                                {draftFocusIds.length}/{MAX_FOCUS_SUBJECTS} selected
                                {!data.authenticated ? ' · Saved on this device' : ''}
                              </span>
                              <div className="flex items-center gap-2">
                                {draftFocusIds.length > 0 && (
                                  <button
                                    type="button"
                                    disabled={savingFocus}
                                    onClick={() => setDraftFocusIds([])}
                                    className="min-h-10 px-3 text-xs font-bold text-secondary hover:text-ink"
                                  >
                                    Clear
                                  </button>
                                )}
                                <button
                                  type="button"
                                  disabled={savingFocus}
                                  onClick={() => setFocusEditorOpen(false)}
                                  className="finna-btn finna-btn-quiet"
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  disabled={savingFocus}
                                  onClick={() => void commitFocusSubjects(draftFocusIds)}
                                  className="finna-btn"
                                >
                                  {savingFocus ? 'Saving…' : 'Save focus'}
                                </button>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Active Focus Subject Strip */}
                        {activeFocusSubjects.length > 0 && (
                          <div className="finna-focus-bar">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap gap-1.5">
                                {activeFocusSubjects.map((s) => (
                                  <Link
                                    key={s.id}
                                    to={
                                      exam
                                        ? `/practice?exam=${encodeURIComponent(exam.id)}&subject=${encodeURIComponent(s.id)}`
                                        : `/practice?subject=${encodeURIComponent(s.id)}`
                                    }
                                    className={`finna-active-focus-chip ${subjectChipClass(s.label)}`}
                                    title={`Practise ${s.label}`}
                                  >
                                    {s.label} →
                                  </Link>
                                ))}
                              </div>
                              <div className="finna-mini-seg" role="group" aria-label="Filter subject rows">
                                <button
                                  type="button"
                                  aria-pressed={subjectFilter === 'focus'}
                                  onClick={() => setSubjectFilter('focus')}
                                >
                                  My focus ({activeFocusSubjects.length})
                                </button>
                                <button
                                  type="button"
                                  aria-pressed={subjectFilter === 'all'}
                                  onClick={() => setSubjectFilter('all')}
                                >
                                  All
                                </button>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Subject Accuracy Progress Rows */}
                        {displayedSubjects.length > 0 ? (
                          <div className="mt-1 flex flex-col gap-1.5">
                            {displayedSubjects.map((s) => {
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
                                      <span className="flex min-w-0 items-center gap-1.5 font-semibold text-ink">
                                        <span className="truncate">{s.subject}</span>
                                        {s.focused && <span className="finna-focus-tag">Focus</span>}
                                      </span>
                                      <span className="shrink-0 font-mono text-xs font-semibold text-secondary">
                                        {s.answered > 0
                                          ? `${pct}% · ${s.answered.toLocaleString('en-IN')} Q`
                                          : 'Start →'}
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
                              : 'Pick a subject book above or choose 2–5 focus subjects to track your strongest and weakest areas.'}
                          </p>
                        )}
                      </div>
                    }
                  />
                ) : (
                  <section className="finna-card" aria-labelledby="subject-progress-title">
                    <div className="finna-section-top">
                      <div>
                        <span className="finna-eyebrow">All-exam subjects</span>
                        <h2 id="subject-progress-title" className="mt-0.5">
                          Subjects &amp; focus
                        </h2>
                      </div>
                      <Link to="/library">Library →</Link>
                    </div>
                    <p className="text-sm text-secondary">
                      {data.loading ? 'Loading subject books…' : 'Open the Study Library to practise by subject.'}
                    </p>
                  </section>
                )}

                {/* Live Study-First Community Feed Preview right on Home */}
                <HomeFeedPreview
                  mode="compact"
                  onExpandToFeedTab={() => setView('feed')}
                />

                {/* Personal Question Vault showcase card */}
                <VaultShowcaseCard />
              </>
            )}

            {view === 'exams' && (
              <>
                <section className="finna-card" aria-labelledby="all-my-exams-title">
                  <div className="finna-section-top">
                    <div>
                      <span className="finna-eyebrow">Active workspace</span>
                      <h2 id="all-my-exams-title" className="mt-0.5">
                        Tracked exams ({trackedExams.length})
                      </h2>
                    </div>
                    <Link to="/exams">Full exam catalog →</Link>
                  </div>
                  <p className="text-sm text-secondary">
                    Switch your primary exam anytime to steer Today’s plan, or launch practice and past papers for any tracked exam directly.
                  </p>
                  <div className="finna-multi-exam-grid mt-4">
                    {trackedExams.map((item) => {
                      const isPrimary = item.id === exam?.id
                      const pres = examPresentation(item.id, item.title)
                      const prog = progressByExam.get(item.id)
                      const pct =
                        prog && item.questions > 0
                          ? Math.min(100, Math.round((prog.unique_questions / item.questions) * 100))
                          : 0
                      const acc =
                        prog && prog.answered > 0
                          ? `${Math.round((prog.correct / prog.answered) * 100)}%`
                          : null
                      return (
                        <article
                          key={item.id}
                          className={`finna-mini-exam-card${isPrimary ? ' is-primary' : ''}`}
                        >
                          <div className="finna-mini-exam-top">
                            <span className="finna-exam-stamp" aria-hidden="true">
                              {pres.short}
                            </span>
                            <div className="min-w-0 flex-1">
                              <h3 className="truncate text-sm font-bold text-ink">{item.title}</h3>
                              <p className="text-xs text-secondary">
                                {item.questions.toLocaleString('en-IN')} Q · {pres.category}
                              </p>
                            </div>
                            {isPrimary ? (
                              <span className="finna-primary-badge">★ Primary</span>
                            ) : (
                              <button
                                type="button"
                                disabled={busyExamId === item.id}
                                onClick={() => void choosePrimaryExam(item.id)}
                                className="finna-mini-switch-btn"
                              >
                                Set primary
                              </button>
                            )}
                          </div>
                          <div className="mt-3">
                            <div className="mb-1 flex justify-between text-xs font-semibold text-secondary">
                              <span>
                                {prog
                                  ? `${prog.unique_questions.toLocaleString('en-IN')} covered${acc ? ` · ${acc} acc.` : ''}`
                                  : 'Not started yet'}
                              </span>
                              <span className="font-mono">{pct}%</span>
                            </div>
                            <div className="finna-progress">
                              <span style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                          <div className="finna-mini-exam-actions">
                            <Link
                              to={'/practice?exam=' + encodeURIComponent(item.id)}
                              className="finna-mini-act finna-mini-act--primary"
                            >
                              Practice
                            </Link>
                            <Link
                              to={'/practice?exam=' + encodeURIComponent(item.id) + '&timer=on'}
                              className="finna-mini-act"
                            >
                              Timed
                            </Link>
                            <Link to={'/exams/' + item.id} className="finna-mini-act">
                              Papers
                            </Link>
                            {trackedExams.length > 1 && (
                              <button
                                type="button"
                                disabled={busyExamId === item.id}
                                onClick={() => void toggleTrackExam(item.id)}
                                className="finna-mini-act finna-mini-act--remove"
                                aria-label={`Remove ${item.title} from tracked exams`}
                                title="Stop tracking"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        </article>
                      )
                    })}
                  </div>
                </section>

                <ExamPickerDialog
                  inline
                  exams={data.exams}
                  trackedIds={trackedIds}
                  activeExamId={exam?.id ?? null}
                  examProgress={data.examProgress}
                  busyId={busyExamId}
                  onToggleTrack={(id) => void toggleTrackExam(id)}
                  onSetPrimary={(id) => void choosePrimaryExam(id)}
                />

                {!data.mock && <QuickStudy initialExam={exam?.id} />}
              </>
            )}

            {view === 'feed' && <HomeFeedPreview mode="full" />}
          </section>

          {/* Right Rail: Compact Month Calendar + Study Tools + Desk + Quests */}
          <aside
            className="finna-home-side finna-home-right"
            aria-label="Calendar, study tools and study desk"
          >
            {/* Compact Month Calendar (§VII.19.8, Dashboards v2) */}
            <section className="finna-card" aria-labelledby="mini-cal-title">
              <div className="finna-section-top">
                <h2 id="mini-cal-title">Study &amp; exam calendar</h2>
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
              <div
                className="finna-mini-cal-grid"
                role="grid"
                aria-label={`${MONTHS[calBase.month]} ${calBase.year}`}
              >
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

            <section className="finna-card" aria-labelledby="quick-shortcuts-title">
              <div className="finna-section-top">
                <h2 id="quick-shortcuts-title">Study shortcuts</h2>
                <Link to="/library">Library</Link>
              </div>
              <div className="finna-shortcut-list">
                <Link to="/revise" className="finna-shortcut-link">
                  <strong>Revision queue</strong>
                  <small>Spaced reviews &amp; mistakes</small>
                </Link>
                <Link to="/bank?study_status=ever_wrong" className="finna-shortcut-link">
                  <strong>Missed questions</strong>
                  <small>Re-test questions you got wrong</small>
                </Link>
                <Link to="/past-papers" className="finna-shortcut-link">
                  <strong>Original past papers</strong>
                  <small>Full MPSC question papers by year</small>
                </Link>
                <Link to="/guides" className="finna-shortcut-link">
                  <strong>Concept guides</strong>
                  <small>Polity, grammar &amp; exam primers</small>
                </Link>
              </div>
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

      {/* Multi-Exam Modal Picker */}
      <ExamPickerDialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        exams={data.exams}
        trackedIds={trackedIds}
        activeExamId={exam?.id ?? null}
        examProgress={data.examProgress}
        busyId={busyExamId}
        onToggleTrack={(id) => void toggleTrackExam(id)}
        onSetPrimary={(id) => void choosePrimaryExam(id)}
      />

      {/* Outer Margin Feature Spotlight Deck (sits outside the 3-col page margin to preserve Calendar space) */}
      <div className="ed-gutter-dock">
        <ExploreDeckRail heading="Also on Finna" compact />
      </div>
    </div>
  )
}
