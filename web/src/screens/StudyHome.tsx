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
  getProfile,
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
import { reviewRequest, reviewSession } from '../lib/review'
import { learningRequest, type ResumePage, type ResumeItem } from '../lib/learning'
import { accountContext } from '../lib/accountContext'
import { useStudyBackground } from '../lib/theme'
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
import { examPresentation } from '../lib/examPresentation'
import { calendarRead, indiaToday, type CalendarEvent } from '../lib/calendar'
import { subjectChipClass, subjectInitials } from '../lib/subjectChips'
import QuickStudy from '../components/QuickStudy'
import TodayCard from '../components/TodayCard'
import HomeCalmRightRail from '../components/HomeCalmRightRail'
import OfflineBanner from '../components/OfflineBanner'
import WelcomeBackBar from '../components/WelcomeBackBar'
import ExploreDeckRail from '../components/ExploreDeckRail'
import VaultShowcaseCard from '../components/VaultShowcaseCard'
import ExamPickerDialog from '../components/ExamPickerDialog'
import HomeFeedPreview from '../components/HomeFeedPreview'
import AvatarArt, { DEFAULT_HERO_LOOK } from '../components/AvatarArt'
import { mockResumePath } from '../lib/sharedTests'
import HomeSetupWizard, { type WizardStep } from '../components/HomeSetupWizard'
import {
  PRESET_HIDDEN,
  syncHomePrefsWithServer,
  useHomePrefs,
  widgetLabel,
  type HomePreferences,
  type HomeWidgetId,
} from '../lib/homePrefs'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

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
  authResolved: boolean
  loading: boolean
  primaryError: boolean
  lastLoadedAt: number | null
}

interface HomeRewards {
  level: number
  title?: string
  lifetime_xp: number
  level_floor_xp: number
  next_level_xp: number
  daily_xp: number
  daily_cap: number
  points: number
  league?: { name: string }
  daily_quests?: {
    quests: {
      key: string
      title: string
      progress: number
      target: number
      completed: boolean
      claimed: boolean
    }[]
  }
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
  authResolved: false,
  loading: true,
  primaryError: false,
  lastLoadedAt: null,
}

const SAFE_RESUME_RE = /^\/(bank|exams|group-b|english|mizo|arithmetic|essay|library|desk|tests|practice|revise|guides)([/?#]|$)/

export default function StudyHome() {
  const [params, setParams] = useSearchParams()
  const scope = useExamScope()
  const [studyBg] = useStudyBackground()
  const [learnerName, setLearnerName] = useState<string>('')
  const [retry, setRetry] = useState(0)
  const [data, setData] = useState<StudyData>(EMPTY)
  const [examError, setExamError] = useState('')
  const [busyExamId, setBusyExamId] = useState<string | null>(null)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [wizardStep, setWizardStep] = useState<WizardStep>(1)
  const [wizardFirstTime, setWizardFirstTime] = useState(false)
  const [prefsSynced, setPrefsSynced] = useState(false)
  const [hiddenToast, setHiddenToast] = useState<HomeWidgetId | null>(null)
  const [homeRewards, setHomeRewards] = useState<HomeRewards | null>(null)
  const [welcomeDismissed, setWelcomeDismissed] = useState(() => {
    try {
      return typeof localStorage !== 'undefined' && localStorage.getItem('finna_welcome_dismissed_v1') === '1'
    } catch {
      return false
    }
  })

  const { prefs, hiddenSet, isHidden, save: saveHomePrefs, hideWidget, showWidget } = useHomePrefs(
    data.authenticated,
  )

  useEffect(() => {
    if (!data.authResolved) return
    let live = true
    void syncHomePrefsWithServer(data.authenticated).then(() => {
      if (live) setPrefsSynced(true)
    })
    return () => {
      live = false
    }
  }, [data.authResolved, data.authenticated])

  useEffect(() => {
    if (!data.authResolved) return
    if (!data.authenticated) {
      setHomeRewards(null)
      return
    }
    let live = true
    const fetchRewards = () => {
      reviewRequest<HomeRewards>('/rewards/me')
        .then((r) => {
          if (live) setHomeRewards(r)
        })
        .catch(() => {})
    }
    fetchRewards()
    window.addEventListener('ism-progress-change', fetchRewards)
    return () => {
      live = false
      window.removeEventListener('ism-progress-change', fetchRewards)
    }
  }, [data.authResolved, data.authenticated])

  useEffect(() => {
    if (params.get('setup') === '1') {
      setWizardStep(1)
      setWizardFirstTime(false)
      setWizardOpen(true)
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          next.delete('setup')
          return next
        },
        { replace: true },
      )
    }
  }, [params, setParams])

  useEffect(() => {
    if (!data.loading && data.authResolved && prefsSynced && !prefs.onboarded && !wizardOpen) {
      setWizardStep(1)
      setWizardFirstTime(true)
      setWizardOpen(true)
    }
  }, [data.loading, data.authResolved, prefsSynced, prefs.onboarded, wizardOpen])

  useEffect(() => {
    if (!hiddenToast) return
    const t = window.setTimeout(() => setHiddenToast(null), 6500)
    return () => window.clearTimeout(t)
  }, [hiddenToast])

  function handleHideCard(id: HomeWidgetId) {
    hideWidget(id)
    setHiddenToast(id)
  }

  function openCustomise(step: WizardStep = 3) {
    setWizardStep(step)
    setWizardFirstTime(false)
    setWizardOpen(true)
  }

  function handleSkipWizard() {
    saveHomePrefs({
      preset: prefs.preset || 'balanced',
      hidden: prefs.hidden.length ? prefs.hidden : [...PRESET_HIDDEN.balanced],
      onboarded: true,
    })
    setWizardOpen(false)
    setWizardFirstTime(false)
  }

  async function handleApplyWizard(payload: {
    examIds: string[]
    primaryExamId: string | null
    subjectIds: string[]
    prefs: HomePreferences
  }) {
    const prevExamSet = new Set(trackedIds)
    const nextExamSet = new Set(payload.examIds)
    for (const id of payload.examIds) {
      if (!prevExamSet.has(id)) {
        addLocalTrackedExam(id)
        if (data.authenticated) {
          try {
            await saveExamBookmark(id)
          } catch {
            /* keep local */
          }
        }
      }
    }
    for (const id of trackedIds) {
      if (!nextExamSet.has(id) && payload.examIds.length > 0) {
        removeLocalTrackedExam(id)
        if (data.authenticated) {
          try {
            await removeExamBookmark(id)
          } catch {
            /* keep local */
          }
        }
      }
    }
    if (payload.primaryExamId) {
      await choosePrimaryExam(payload.primaryExamId)
    }
    const prevSubjKey = [...localFocusIds].sort().join(',')
    const nextSubjKey = [...payload.subjectIds].sort().join(',')
    if (prevSubjKey !== nextSubjKey) {
      await commitFocusSubjects(payload.subjectIds)
    }
    saveHomePrefs({ ...payload.prefs, onboarded: true })
    setWizardOpen(false)
    setWizardFirstTime(false)
  }

  function dismissWelcome() {
    setWelcomeDismissed(true)
    try {
      localStorage.setItem('finna_welcome_dismissed_v1', '1')
    } catch {
      /* ignore */
    }
  }

  // Multi-subject focus UI state
  const localFocusIds = useLocalFocusSubjectIds()
  const [focusEditorOpen, setFocusEditorOpen] = useState(false)
  const [draftFocusIds, setDraftFocusIds] = useState<string[]>([])
  const [savingFocus, setSavingFocus] = useState(false)
  const [focusError, setFocusError] = useState('')

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
        patch({ authenticated: a.authenticated, authResolved: true })
        if (!a.authenticated) {
          setLearnerName('')
          return
        }
        void getProfile()
          .then((prof) => {
            if (!live) return
            const raw = (prof.name || prof.handle || '').trim()
            setLearnerName(raw.split(/\s+/)[0] || '')
          })
          .catch(() => {})
        void getFocusSubjects()
          .then((f) => {
            if (!live) return
            const ids = f.items.map((item) => item.subject_id)
            writeLocalFocusSubjects(ids)
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
      .catch(() => {
        patch({ authResolved: true })
      })

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

  // Load upcoming exam dates across the next 12 months for the editorial greeting countdown
  const calendarWindowEnd = useMemo(() => {
    const endMs = Date.parse(today + 'T12:00:00Z') + 365 * 86400000
    return new Date(endMs).toISOString().slice(0, 10)
  }, [today])

  useEffect(() => {
    let live = true
    calendarRead<{ items: CalendarEvent[] }>(
      `/calendar/events?start=${today}&end=${calendarWindowEnd}&limit=100`,
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
  }, [today, calendarWindowEnd])

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

  const examProgress = exam ? progressByExam.get(exam.id) : undefined
  const coverage =
    exam && examProgress && exam.questions
      ? Math.min(100, Math.round((examProgress.unique_questions / exam.questions) * 100))
      : null
  const p = data.progress
  const examTitle = exam ? shortExamLabel(exam) : 'Choose your exam'

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
    const focusSet = new Set(localFocusIds)
    const catalogById = new Map(subjectCatalog.map((s) => [s.id, s]))

    const merged = new Map<
      string,
      {
        subject_id: string
        subject: string
        done: number
        total: number
        answered: number
        correct: number
        focused: boolean
      }
    >()

    for (const s of p?.subjects || []) {
      const cat = catalogById.get(s.subject_id)
      merged.set(s.subject_id, {
        subject_id: s.subject_id,
        subject: s.subject,
        done: s.unique_questions ?? s.answered,
        total: cat?.questions ?? 0,
        answered: s.answered,
        correct: s.correct,
        focused: focusSet.has(s.subject_id),
      })
    }
    for (const cat of subjectCatalog) {
      if (!merged.has(cat.id)) {
        merged.set(cat.id, {
          subject_id: cat.id,
          subject: cat.label,
          done: 0,
          total: cat.questions,
          answered: 0,
          correct: 0,
          focused: focusSet.has(cat.id),
        })
      }
    }

    return Array.from(merged.values())
      .sort((a, b) => {
        const aFocus = a.focused ? 0 : 1
        const bFocus = b.focused ? 0 : 1
        if (aFocus !== bFocus) return aFocus - bFocus
        if (b.done !== a.done) return b.done - a.done
        return b.total - a.total
      })
      .slice(0, 6)
  }, [p?.subjects, subjectCatalog, localFocusIds])

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

  // Compute calm 3d editorial greeting metadata (IST time + next upcoming exam date)
  const greetingMeta = useMemo(() => {
    const nowIst = new Date(Date.now() + 5.5 * 3600_000)
    const hr = nowIst.getUTCHours()
    const salutation = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening'
    const dayName = nowIst.toLocaleDateString('en-IN', { weekday: 'long', timeZone: 'UTC' }).toUpperCase()
    const dayNum = nowIst.getUTCDate()
    const monthName = MONTHS[nowIst.getUTCMonth()].toUpperCase()
    const dateLine = `${dayName} · ${dayNum} ${monthName}`

    const upcoming = data.calendarEvents
      .filter((ev) => ev.starts_on && ev.starts_on >= today)
      .sort((a, b) => (a.starts_on || '').localeCompare(b.starts_on || ''))[0]
    let daysUntil: number | null = null
    if (upcoming?.starts_on) {
      const diff = Math.round(
        (Date.parse(upcoming.starts_on + 'T00:00:00Z') - Date.parse(today + 'T00:00:00Z')) /
          86400000,
      )
      if (diff >= 0 && diff <= 365) daysUntil = diff
    }
    return { salutation, dateLine, daysUntil }
  }, [data.calendarEvents, today])

  const hasRightRail = true
  const gridColClass = hasRightRail ? 'is-calm-three' : 'is-two-col'

  return (
    <div className={`finna-home-shell finna-bg--${studyBg}`} data-screen="home">
      {studyBg === 'library' && (
        <div className="finna-home-photo-band" aria-hidden="true">
          <img
            src="/images/discover/guides.jpg"
            alt=""
            className="finna-home-photo-img"
            loading="eager"
          />
          <div className="finna-home-photo-scrim" />
        </div>
      )}
      {studyBg === 'grid' && <div className="finna-home-bg-grid" aria-hidden="true" />}
      {studyBg === 'lamp' && <div className="finna-home-bg-lamp" aria-hidden="true" />}

      <div className="finna-page finna-home">
        <h1 className="sr-only">Your study home</h1>

        {/* 3d Editorial Greeting Row on top of the Library Reading-Room Photo Band */}
        {studyBg === 'library' && (
          <div className="finna-lib-greeting">
            <div>
              <div className="finna-lib-kicker">{greetingMeta.dateLine}</div>
              <p className="finna-lib-headline">
                {greetingMeta.salutation}
                {learnerName ? `, ${learnerName}` : ''}.
                {greetingMeta.daysUntil !== null && exam
                  ? ` ${greetingMeta.daysUntil} ${greetingMeta.daysUntil === 1 ? 'day' : 'days'} to ${shortExamLabel(exam)}.`
                  : ''}
              </p>
            </div>
            <span className="finna-lib-tagline">A little more, every day.</span>
          </div>
        )}

        <OfflineBanner
          lastLoadedAt={data.lastLoadedAt}
          onRetry={() => setRetry((n) => n + 1)}
          retrying={data.loading}
        />

        <WelcomeBackBar resumeUrl={returnRows[0]?.url ?? null} />

        {/* Adaptive First-Visit Hero (only for first-time guests with 0 answers; replaces empty KPI zeros) */}
        {!data.loading &&
        data.authResolved &&
        !data.authenticated &&
        (p?.answered ?? 0) === 0 &&
        !welcomeDismissed ? (
          <section className="finna-welcome-hero" aria-label="Welcome to Finna">
            <button
              type="button"
              onClick={dismissWelcome}
              aria-label="Dismiss welcome banner"
              className="finna-welcome-close"
              title="Hide welcome banner"
            >
              ×
            </button>
            <div className="finna-welcome-copy">
              <span className="finna-welcome-kicker">
                FINNA · MPSC &amp; MIZORAM EXAM STUDY
              </span>
              <h2>Master MPSC &amp; Mizoram exams with real past papers</h2>
              <p>
                82,000+ past-paper questions · 11 free Concept Guides · Full-Paper Mocks &amp;
                16-bit RPG drills — free to start, no sign-in needed.
              </p>
              <div className="finna-welcome-actions">
                <Link
                  to={exam ? '/practice?exam=' + encodeURIComponent(exam.id) : '/practice'}
                  className="finna-welcome-cta"
                >
                  Start Free Practice →
                </Link>
                <Link to="/exams" className="finna-welcome-ghost">
                  Browse Exams &amp; Papers
                </Link>
                <Link to="/games/blocks" className="finna-welcome-ghost">
                  🧱 Play Finna Blocks
                </Link>
              </div>
            </div>
            <div className="finna-welcome-side">
              <div className="finna-welcome-sprite" aria-hidden="true">
                <AvatarArt
                  look={DEFAULT_HERO_LOOK}
                  size={68}
                  variant="sprite"
                  pose="walk"
                  facing="down"
                  animate
                />
              </div>
              <Link to="/login" className="finna-welcome-signin">
                Sign in to save progress →
              </Link>
            </div>
          </section>
        ) : !isHidden('kpi') ? (
          /* 3d Slim Merged Navy XP + KPI Banner */
          (() => {
            const xpVal = homeRewards
              ? Math.max(0, homeRewards.lifetime_xp - homeRewards.level_floor_xp)
              : Math.min(100, weekAnswers * 10)
            const xpMax = homeRewards
              ? Math.max(40, homeRewards.next_level_xp - homeRewards.level_floor_xp)
              : 100
            const xpPct = Math.max(0, Math.min(100, Math.round((xpVal / xpMax) * 100)))
            const xpTitle = homeRewards
              ? `Level ${homeRewards.level} → Level ${homeRewards.level + 1} · ${homeRewards.lifetime_xp.toLocaleString('en-IN')} / ${homeRewards.next_level_xp.toLocaleString('en-IN')} XP`
              : data.authenticated
                ? 'Answer questions to earn XP'
                : 'Sign in to save XP'
            return (
              <section className="finna-calm-xp-bar" aria-label="Level, XP and weekly study stats">
                <span className="finna-home-xp-lvl">LV {homeRewards?.level ?? 1}</span>
                <div
                  className="finna-calm-xp-meter"
                  role="progressbar"
                  aria-label={xpTitle}
                  aria-valuemin={0}
                  aria-valuemax={xpMax}
                  aria-valuenow={Math.min(xpMax, Math.round(xpVal))}
                  title={xpTitle}
                >
                  <div className="finna-calm-xp-fill" style={{ width: `${xpPct}%` }} />
                </div>
                <div className="finna-calm-xp-metrics">
                  <span>
                    <b>{p ? weekAnswers.toLocaleString('en-IN') : '—'}</b> answered this week
                  </span>
                  <span>
                    <b>{weekAccuracy ?? '—'}</b> accuracy
                  </span>
                  <span>
                    <b>{p ? `${p.current_streak}d` : '—'}</b> streak
                  </span>
                </div>
                <div className="finna-calm-xp-right">
                  <Link
                    to={data.authenticated ? '/profile/rewards' : '/login'}
                    className="finna-home-xp-link"
                  >
                    {data.authenticated ? 'Rewards & XP →' : 'Sign in →'}
                  </Link>
                  <button
                    type="button"
                    className="finna-podium-hide"
                    aria-label="Hide study stats banner"
                    title="Hide stats banner"
                    onClick={() => handleHideCard('kpi')}
                  >
                    ×
                  </button>
                </div>
              </section>
            )
          })()
        ) : null}

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

        <div className={`finna-home-grid ${gridColClass}`}>
          {/* Left Column: Multi-Exam Hero + Today Plan */}
          <aside className="finna-home-side" aria-label="Your exams and study plan">
            <section className="finna-exam-hero" aria-labelledby="my-exam-title">
              <div className="finna-hero-head">
                <div className="min-w-0">
                  <div className="finna-eyebrow">
                    {trackedExams.length > 1 ? `My exams · ${trackedExams.length} tracked` : 'My exam'}
                  </div>
                  <h2 id="my-exam-title" className="mt-1 text-[32px] font-bold leading-none tracking-[-0.02em]">
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
                      ? '/practice?exam=' + encodeURIComponent(exam.id) + '&mode=mock'
                      : '/practice?mode=mock'
                  }
                >
                  Full-Paper Mock
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
            {!isHidden('today') && <TodayCard exams={data.exams} hideExamSelect />}
          </aside>

          {/* Center Main Stream: View Switcher + Multi-Exam + Focus Subjects + Live Community Feed */}
          <section className="finna-home-stream" aria-label="Study workspace and community">
            {/* Workspace View Switcher + Personalise Home button */}
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
              <button
                type="button"
                className="finna-customise-btn"
                onClick={() => openCustomise(3)}
                title="Choose which cards appear on your front page"
              >
                <span aria-hidden="true">⚙</span>
                <span>Customise Home</span>
              </button>
            </div>

            {view === 'overview' && (
              <>
                {!isHidden('return') && returnRows.length > 0 && (
                  <section className="finna-card" aria-labelledby="return-block-title">
                    <div className="finna-section-top">
                      <h2 id="return-block-title">Pick up where you left off</h2>
                      <div className="finna-card-head-right">
                        <Link to="/revise">Revision queue →</Link>
                        <button
                          type="button"
                          className="finna-card-hide-btn"
                          aria-label="Hide Pick up where you left off card"
                          title="Hide this card"
                          onClick={() => handleHideCard('return')}
                        >
                          ×
                        </button>
                      </div>
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

                {/* 3d Clean Subjects & Your Focus 2-Column Card */}
                {!isHidden('subjects') && (
                  <section className="finna-card finna-subjects-card" aria-labelledby="subject-progress-title">
                    <div className="finna-subjects-head">
                      <div className="min-w-0">
                        <span className="finna-eyebrow">All-exam subject books</span>
                        <h2 id="subject-progress-title" className="finna-subjects-title">
                          Subjects &amp; your focus
                        </h2>
                        <p className="finna-subjects-sub">
                          Questions from UDC, LDC, MCS &amp; Group B combined into{' '}
                          {data.subjectModules.length || 5} subject books — pick up to{' '}
                          {MAX_FOCUS_SUBJECTS} focus subjects to guide your daily plan.
                        </p>
                      </div>
                      <div className="finna-subjects-actions">
                        {subjectCatalog.length > 0 && (
                          <button
                            type="button"
                            onClick={openFocusEditor}
                            className="finna-subjects-focus-pill"
                            aria-expanded={focusEditorOpen}
                          >
                            {focusEditorOpen
                              ? 'Close picker'
                              : `Focus subjects · ${activeFocusSubjects.length}/${MAX_FOCUS_SUBJECTS}`}
                          </button>
                        )}
                        <Link to="/library" className="finna-subjects-lib-link">
                          Library →
                        </Link>
                      </div>
                    </div>

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

                    {/* 2-Column Subject Rows Grid (exact 3d design) */}
                    {displayedSubjects.length > 0 ? (
                      <div className="finna-subjects-grid">
                        {displayedSubjects.map((s) => {
                          const pct =
                            s.total > 0
                              ? Math.min(100, Math.round((s.done / s.total) * 100))
                              : s.answered > 0
                                ? Math.min(100, Math.round((s.correct / s.answered) * 100))
                                : 0
                          const countLabel =
                            s.total > 0
                              ? `${s.done.toLocaleString('en-IN')} / ${s.total.toLocaleString('en-IN')}`
                              : s.answered > 0
                                ? `${s.answered.toLocaleString('en-IN')} Q`
                                : 'Start →'
                          return (
                            <Link
                              key={s.subject_id}
                              to={'/bank?subject_id=' + encodeURIComponent(s.subject_id)}
                              className="finna-subjects-row"
                            >
                              <span
                                className={`${subjectChipClass(s.subject)} finna-subj-chip--sq`}
                                aria-hidden="true"
                              >
                                {subjectInitials(s.subject)}
                              </span>
                              <div className="finna-subjects-row-body">
                                <div className="finna-subjects-row-top">
                                  <span className="finna-subjects-row-name">
                                    <span className="truncate">{s.subject}</span>
                                    {s.focused && <span className="finna-focus-tag">Focus</span>}
                                  </span>
                                  <span className="finna-subjects-row-count">{countLabel}</span>
                                </div>
                                <div className="finna-subjects-bar">
                                  <span style={{ width: `${pct}%` }} />
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
                          : 'Open the Study Library or choose focus subjects to track your progress.'}
                      </p>
                    )}
                  </section>
                )}

                {/* 3d Centre 3-Across Editorial Photo Showcase ("Also on Finna") */}
                {!isHidden('explore') && (
                  <ExploreDeckRail
                    heading="Also on Finna"
                    variant="row3"
                    onHide={() => handleHideCard('explore')}
                  />
                )}

                {/* Live Study-First Community Feed Preview right on Home */}
                {!isHidden('feed') && (
                  <div className="finna-hideable-wrap">
                    <button
                      type="button"
                      className="finna-card-hide-btn finna-card-hide-float"
                      aria-label="Hide Community feed preview"
                      title="Hide Community feed preview"
                      onClick={() => handleHideCard('feed')}
                    >
                      ×
                    </button>
                    <HomeFeedPreview
                      mode="compact"
                      onExpandToFeedTab={() => setView('feed')}
                    />
                  </div>
                )}

                {/* Personal Question Vault showcase card */}
                {!isHidden('vault') && (
                  <div className="finna-hideable-wrap">
                    <button
                      type="button"
                      className="finna-card-hide-btn finna-card-hide-float"
                      aria-label="Hide Personal Question Vault card"
                      title="Hide Vault card"
                      onClick={() => handleHideCard('vault')}
                    >
                      ×
                    </button>
                    <VaultShowcaseCard />
                  </div>
                )}

                {isHidden('return') &&
                  isHidden('subjects') &&
                  isHidden('feed') &&
                  isHidden('vault') && (
                    <section className="finna-card">
                      <h2>Your centre workspace is clear</h2>
                      <p className="mt-2 text-sm text-secondary">
                        All centre overview cards are currently hidden. Turn any card back on whenever you want.
                      </p>
                      <button
                        type="button"
                        onClick={() => openCustomise(3)}
                        className="finna-btn mt-4"
                      >
                        ⚙ Customise Home
                      </button>
                    </section>
                  )}
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
                              to={'/practice?exam=' + encodeURIComponent(item.id) + '&mode=mock'}
                              className="finna-mini-act"
                            >
                              Mock
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

          {/* 3d Calm Right Column: Weekly Leaderboard Podium + Play/People/Tools Tabs + Everything on Finna */}
          {hasRightRail && (
            <HomeCalmRightRail
              quests={homeRewards?.daily_quests?.quests}
              hidden={hiddenSet}
              onHide={handleHideCard}
            />
          )}
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

      {/* First-Time Setup & Personalise Home Wizard */}
      <HomeSetupWizard
        open={wizardOpen}
        initialStep={wizardStep}
        isFirstTime={wizardFirstTime}
        exams={data.exams}
        trackedExamIds={trackedIds}
        primaryExamId={exam?.id ?? null}
        subjectChoices={subjectCatalog}
        focusSubjectIds={localFocusIds}
        prefs={prefs}
        onClose={() => setWizardOpen(false)}
        onSkip={handleSkipWizard}
        onApply={handleApplyWizard}
      />

      {/* Quick Undo Toast when hiding a card */}
      {hiddenToast && (
        <div role="status" className="finna-hide-toast">
          <span>
            Hidden <strong>{widgetLabel(hiddenToast)}</strong>
          </span>
          <button
            type="button"
            onClick={() => {
              showWidget(hiddenToast)
              setHiddenToast(null)
            }}
          >
            Undo
          </button>
          <button
            type="button"
            onClick={() => {
              setHiddenToast(null)
              openCustomise(3)
            }}
          >
            Customise
          </button>
        </div>
      )}
    </div>
  )
}
