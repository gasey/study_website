import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import QuestionCard from '../components/QuestionCard'
import { AnswerLayoutControl } from '../components/AnswerLayout'
import {
  currentMock,
  getCollection,
  isLaterExamCollection,
  listCollections,
  listQuestions,
  listTaxonomy,
  type Collection,
  type CollectionDetail,
  type CollectionPaper,
  type MockSession,
  type Question,
  type TaxonomyFacet,
} from '../lib/api'
import { usePreferredExam } from '../lib/preferredExam'
import { resolveTrackedExams, shortExamLabel, useTrackedExamIds } from '../lib/trackedExams'
import { FLAGSHIP_EXAM_IDS } from '../lib/examPresentation'
import { useSelectionTray } from '../lib/selectionTray'
import { mockResumePath } from '../lib/sharedTests'
import { paperIdentity } from '../lib/paperIdentity'
import { nextBrowseOffset, type StudyStatus } from '../lib/questionBrowse'

type StudioMode = 'practice' | 'mock'
type PracticePace = '50' | '25' | 'step'
type PracticeQueue = 'unseen' | 'ever_wrong' | 'all'
type PracticeFormat = 'mcq' | 'written'

function estimateFullPaperMinutes(qCount: number, configured?: number | null): number {
  if (configured && configured >= 15) return configured
  return Math.max(30, Math.min(180, Math.round(Math.max(20, qCount) * 1.2)))
}

function paperMockCount(p: CollectionPaper): { count: number; useOfficial: boolean } {
  if (p.allow_timed_test && p.scorable >= 20) {
    return { count: p.scorable, useOfficial: true }
  }
  return { count: p.practice_count || p.answerable_count || p.scorable || 0, useOfficial: false }
}

/** Unified `/practice` studio — ONE place for both Guided Practice and real Full-Paper Mocks.
 *  - Guided Practice: 50-by-50, 25-by-25, or Step 1-by-1 through Unattempted / Missed / All MCQs
 *    filtered by exam, subject, and topic (English, GK, Polity, etc.), with instant explanations.
 *  - Full-Paper Mock: always a full exam paper (real original past paper OR full-length 100-Q exam mock),
 *    server-timed countdown, answers locked until submit. */
export default function Practice() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const tray = useSelectionTray()

  const [exams, setExams] = useState<Collection[]>([])
  const [taxonomy, setTaxonomy] = useState<TaxonomyFacet[]>([])
  const [activeMock, setActiveMock] = useState<MockSession | null>(null)
  const [catalogError, setCatalogError] = useState('')

  const preferredExam = usePreferredExam(exams)
  const trackedIds = useTrackedExamIds()
  const examCollections = useMemo(() => exams.filter((e) => e.kind === 'exam'), [exams])

  const quickExams = useMemo(() => {
    const tracked = resolveTrackedExams(examCollections, trackedIds, preferredExam)
    const out: Collection[] = []
    const seen = new Set<string>()
    for (const e of tracked) {
      if (!seen.has(e.id)) {
        out.push(e)
        seen.add(e.id)
      }
    }
    for (const id of FLAGSHIP_EXAM_IDS) {
      if (out.length >= 6) break
      if (seen.has(id)) continue
      const match = examCollections.find((e) => e.id === id)
      if (match) {
        out.push(match)
        seen.add(match.id)
      }
    }
    return out
  }, [examCollections, trackedIds, preferredExam])

  const initialStudio: StudioMode =
    params.get('mode') === 'mock' || params.get('timer') === 'on' ? 'mock' : 'practice'

  const [studioMode, setStudioMode] = useState<StudioMode>(initialStudio)
  const [examId, setExamId] = useState(params.get('exam') || '')
  const [subjectId, setSubjectId] = useState(params.get('subject') || '')
  const [topicId, setTopicId] = useState(params.get('topic') || '')
  const [query, setQuery] = useState(params.get('q') || '')
  const [queue, setQueue] = useState<PracticeQueue>(() => {
    const raw = params.get('status')
    if (raw === 'ever_wrong' || raw === 'wrong') return 'ever_wrong'
    if (raw === 'all') return 'all'
    return 'unseen'
  })
  const [pace, setPace] = useState<PracticePace>(() => {
    const raw = params.get('pace') || params.get('count')
    if (raw === 'step' || raw === '1') return 'step'
    if (raw === '25') return '25'
    return '50'
  })
  const [format, setFormat] = useState<PracticeFormat>(
    params.get('mode') === 'written' ? 'written' : 'mcq',
  )

  // Full-Paper Mock exam details (cached in memory per exam so switching pills is instant)
  const detailCacheRef = useRef<Map<string, CollectionDetail>>(new Map())
  const [examDetail, setExamDetail] = useState<CollectionDetail | null>(null)
  const [loadingPapers, setLoadingPapers] = useState(false)
  const [paperFilter, setPaperFilter] = useState('')

  // Active guided practice run state (supports 50-by-50, 25-by-25, and Step 1-by-1 progression)
  const [running, setRunning] = useState(params.get('autostart') === '1')
  const [items, setItems] = useState<Question[]>([])
  const [totalAvailable, setTotalAvailable] = useState<number | null>(null)
  const [loadingRun, setLoadingRun] = useState(false)
  const [runError, setRunError] = useState('')
  const [batchOffset, setBatchOffset] = useState(0)
  const [batchNumber, setBatchNumber] = useState(1)
  const [stepIndex, setStepIndex] = useState(0)
  const [runSeed, setRunSeed] = useState('')
  const [batchOutcomes, setBatchOutcomes] = useState<Record<string, boolean>>({})
  const [runConfig, setRunConfig] = useState<{
    exam: string
    subject: string
    topic: string
    format: PracticeFormat
    queue: PracticeQueue
    batchSize: number
    q: string
  } | null>(null)
  const runSectionRef = useRef<HTMLElement | null>(null)

  const examInitializedRef = useRef(Boolean(params.get('exam')))

  useEffect(() => {
    let live = true
    Promise.all([
      listCollections().then((rows) => {
        if (!live) return
        setExams(rows.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)))
      }),
      listTaxonomy('all', true).then((rows) => {
        if (live) setTaxonomy(rows)
      }),
      currentMock()
        .then((m) => {
          if (live) setActiveMock(m)
        })
        .catch(() => {}),
    ]).catch((e) => {
      if (live) setCatalogError(e instanceof Error ? e.message : 'Could not load exams and subjects.')
    })
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    if (examInitializedRef.current || !preferredExam) return
    examInitializedRef.current = true
    setExamId(preferredExam.id)
  }, [preferredExam])

  // Load real papers for the selected exam whenever in Full-Paper Mock mode
  const mockExamId = examId || preferredExam?.id || examCollections[0]?.id || ''
  useEffect(() => {
    if (studioMode !== 'mock' || !mockExamId) return
    const cached = detailCacheRef.current.get(mockExamId)
    if (cached) {
      setExamDetail(cached)
      setLoadingPapers(false)
      return
    }
    let live = true
    setLoadingPapers(true)
    getCollection(mockExamId)
      .then((detail) => {
        detailCacheRef.current.set(mockExamId, detail)
        if (live) setExamDetail(detail)
      })
      .catch(() => {
        if (live) setExamDetail(null)
      })
      .finally(() => {
        if (live) setLoadingPapers(false)
      })
    return () => {
      live = false
    }
  }, [studioMode, mockExamId])

  const subjects = useMemo(() => {
    const map = new Map<string, string>()
    for (const f of taxonomy) {
      if (!map.has(f.subject_id)) map.set(f.subject_id, f.subject)
    }
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1]))
  }, [taxonomy])

  const topicsForSubject = useMemo(() => {
    if (!subjectId) return []
    const map = new Map<string, { id: string; label: string; count: number }>()
    for (const f of taxonomy) {
      if (f.subject_id !== subjectId || !f.topic_id || !f.topic) continue
      const prev = map.get(f.topic_id)
      if (prev) prev.count += f.questions
      else map.set(f.topic_id, { id: f.topic_id, label: f.topic, count: f.questions })
    }
    return [...map.values()].sort((a, b) => b.count - a.count)
  }, [taxonomy, subjectId])

  const eligiblePapers = useMemo(() => {
    const raw = examDetail?.paper_list ?? []
    const needle = paperFilter.trim().toLowerCase()
    return raw
      .filter((p) => {
        const { count } = paperMockCount(p)
        if (count < 15) return false
        if (!needle) return true
        const id = paperIdentity(p)
        return `${id.title} ${id.exam} ${p.year ?? ''}`.toLowerCase().includes(needle)
      })
      .sort((a, b) => (b.year ?? 0) - (a.year ?? 0) || paperMockCount(b).count - paperMockCount(a).count)
  }, [examDetail, paperFilter])

  const generatedFullPaper = useMemo(() => {
    if (!examDetail) return null
    const officialCount = examDetail.scorable || 0
    const practiceCount = examDetail.practice_count || examDetail.answerable_count || 0
    const useOfficial = officialCount >= 100 || (officialCount >= 20 && officialCount >= practiceCount)
    const pool = useOfficial ? officialCount : practiceCount
    const qCount = Math.min(100, pool)
    if (qCount < 20) return null
    return {
      qCount,
      minutes: estimateFullPaperMinutes(qCount),
      useOfficial,
    }
  }, [examDetail])

  async function loadPracticeBatch(opts: {
    exam: string
    subject: string
    topic: string
    format: PracticeFormat
    queue: PracticeQueue
    batchSize: number
    q: string
    offset: number
    batchNo: number
    seed: string
    scrollIntoView?: boolean
  }) {
    setLoadingRun(true)
    setRunError('')
    setBatchOutcomes({})
    setStepIndex(0)
    try {
      const rawYear = params.get('year') || ''
      const yearNum = /^\d{4}$/.test(rawYear) ? Number(rawYear) : undefined
      const res = await listQuestions({
        pool: opts.format === 'written' ? 'all' : 'practice',
        answer_status: opts.format === 'written' ? 'written' : undefined,
        collection_id: opts.exam || undefined,
        subject_id: opts.subject || undefined,
        topic_id: opts.topic || undefined,
        year_from: yearNum,
        year_to: yearNum,
        study_status: opts.format === 'written' ? undefined : opts.queue,
        q: opts.q.trim().length >= 2 ? opts.q.trim() : undefined,
        order: opts.format === 'written' ? 'repeated' : 'mixed',
        seed: opts.format === 'written' ? undefined : opts.seed,
        limit: opts.batchSize,
        offset: opts.offset,
      })
      const filtered =
        opts.format === 'written'
          ? res.items.filter((q) => q.type === 'descriptive')
          : res.items.filter((q) => q.type === 'mcq')
      setItems(filtered)
      setTotalAvailable(res.total)
      setBatchOffset(opts.offset)
      setBatchNumber(opts.batchNo)
      setRunSeed(opts.seed)
      setRunConfig({
        exam: opts.exam,
        subject: opts.subject,
        topic: opts.topic,
        format: opts.format,
        queue: opts.queue,
        batchSize: opts.batchSize,
        q: opts.q,
      })
      setRunning(true)
      if (opts.scrollIntoView) {
        requestAnimationFrame(() => runSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
      }
    } catch (e) {
      setRunError(e instanceof Error ? e.message : 'Could not load questions for practice.')
    } finally {
      setLoadingRun(false)
    }
  }

  async function launchUntimedRun(
    targetExam = examId,
    targetSubject = subjectId,
    targetTopic = topicId,
    targetFormat = format,
    targetQueue = queue,
    targetPace = pace,
  ) {
    const batchSize = targetPace === '25' ? 25 : 50
    const seed = 'practice-' + Date.now().toString(36)
    await loadPracticeBatch({
      exam: targetExam,
      subject: targetSubject,
      topic: targetTopic,
      format: targetFormat,
      queue: targetQueue,
      batchSize,
      q: query,
      offset: 0,
      batchNo: 1,
      seed,
    })
  }

  function handleNextBatch() {
    if (!runConfig) return
    const resultsArr = items.map((q) =>
      q.id in batchOutcomes ? { correct: batchOutcomes[q.id] } : undefined,
    )
    const nextOffset = nextBrowseOffset(
      batchOffset,
      runConfig.batchSize,
      runConfig.queue as StudyStatus,
      resultsArr,
    )
    void loadPracticeBatch({
      ...runConfig,
      offset: nextOffset,
      batchNo: batchNumber + 1,
      seed: runSeed || 'practice-' + Date.now().toString(36),
      scrollIntoView: true,
    })
  }

  function handlePrevBatch() {
    if (!runConfig || batchOffset <= 0) return
    const prevOffset = Math.max(0, batchOffset - runConfig.batchSize)
    void loadPracticeBatch({
      ...runConfig,
      offset: prevOffset,
      batchNo: Math.max(1, batchNumber - 1),
      seed: runSeed || 'practice-' + Date.now().toString(36),
      scrollIntoView: true,
    })
  }

  useEffect(() => {
    if (params.get('autostart') === '1' && initialStudio === 'practice') {
      const rawStatus = params.get('status')
      const startQueue: PracticeQueue =
        rawStatus === 'ever_wrong' || rawStatus === 'wrong'
          ? 'ever_wrong'
          : rawStatus === 'all'
            ? 'all'
            : 'unseen'
      const rawPace = params.get('pace') || params.get('count')
      const startPace: PracticePace =
        rawPace === 'step' || rawPace === '1' ? 'step' : rawPace === '25' ? '25' : '50'
      void launchUntimedRun(
        params.get('exam') || '',
        params.get('subject') || '',
        params.get('topic') || '',
        params.get('mode') === 'written' ? 'written' : 'mcq',
        startQueue,
        startPace,
      )
    }
    // Run once on initial autostart navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function switchStudioMode(next: StudioMode) {
    setStudioMode(next)
    const p = new URLSearchParams(params)
    if (next === 'mock') {
      p.set('mode', 'mock')
      p.delete('timer')
    } else if (p.get('mode') === 'mock') {
      p.delete('mode')
    }
    setParams(p, { replace: true })
  }

  function handleStartPractice(e: React.FormEvent) {
    e.preventDefault()
    const next = new URLSearchParams()
    if (examId) next.set('exam', examId)
    if (subjectId) next.set('subject', subjectId)
    if (topicId) next.set('topic', topicId)
    if (query.trim()) next.set('q', query.trim())
    next.set('status', queue)
    next.set('pace', pace)
    if (format === 'written') next.set('mode', 'written')
    setParams(next, { replace: true })
    void launchUntimedRun()
  }

  function startFullPaperMock(paper?: CollectionPaper) {
    const target = mockExamId || 'udc'
    const qs = new URLSearchParams()
    if (paper) {
      const { count, useOfficial } = paperMockCount(paper)
      qs.set('paper', paper.id)
      qs.set('minutes', String(estimateFullPaperMinutes(count, paper.duration_minutes)))
      if (!useOfficial) qs.set('mode', 'derived')
    } else if (generatedFullPaper) {
      qs.set('count', String(generatedFullPaper.qCount))
      qs.set('minutes', String(generatedFullPaper.minutes))
      if (!generatedFullPaper.useOfficial) qs.set('mode', 'derived')
    }
    navigate(`/exams/${encodeURIComponent(target)}/mock?${qs.toString()}`)
  }

  return (
    <div className="finna-page pr-shell" data-screen="practice">
      <header className="av-hero pr-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">One workspace · two clear modes</span>
          <h1>Practice &amp; Full-Paper Mock</h1>
          <p>
            Use <strong>Guided Practice</strong> to clear questions <strong>50 by 50</strong>, <strong>Step 1-by-1</strong>, or{' '}
            <strong>Unattempted only</strong> by exam, subject, or topic (English, GK, Polity…).
            Switch to <strong>Full-Paper Mock</strong> for a real full-length timed exam paper.
          </p>
        </div>
        <div className="av-hero-actions">
          <Link to="/revise" className="cr-glass-btn cr-glass-btn--accent">
            ↻ Smart Review
          </Link>
          <Link to="/practice/build" className="cr-glass-btn">
            Build custom test
          </Link>
          <Link to="/tests" className="cr-glass-btn">
            Shared tests
          </Link>
        </div>
      </header>

      {activeMock && (
        <section className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border-2 border-ink bg-card p-4 shadow-[var(--ism-card-shadow)]">
          <div>
            <p className="font-mono text-xs font-bold uppercase tracking-[0.08em] text-exams-dark">
              Full-Paper Mock in progress
            </p>
            <p className="mt-1 text-base font-semibold text-ink">
              {activeMock.questions.length} questions · {Math.max(0, Math.ceil(activeMock.seconds_remaining / 60))} min remaining
            </p>
          </div>
          <Link
            to={mockResumePath(activeMock)}
            className="inline-flex min-h-11 items-center rounded-lg bg-ink px-4 py-2 text-sm font-bold text-paper"
          >
            Resume Full-Paper Mock →
          </Link>
        </section>
      )}

      {catalogError && (
        <p role="alert" className="mt-4 rounded-lg border border-wrong bg-wrong-soft p-3 text-sm text-wrong-dark">
          {catalogError}
        </p>
      )}

      {/* Primary 2-mode switch: Practice (untimed) vs Full-Paper Mock (real timed paper) */}
      <div className="mt-6 grid gap-3 sm:grid-cols-2" role="tablist" aria-label="Study mode">
        <button
          type="button"
          role="tab"
          aria-selected={studioMode === 'practice'}
          onClick={() => switchStudioMode('practice')}
          className={`flex flex-col items-start gap-1 rounded-[18px] border-2 p-4 text-left transition ${
            studioMode === 'practice'
              ? 'border-ink bg-card shadow-[var(--ism-card-shadow)]'
              : 'border-hairline bg-paper/70 hover:border-hairline2'
          }`}
        >
          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-practice-dark">
            Mode 1 · Guided untimed study
          </span>
          <strong className="font-display text-xl text-ink">Practice (50 by 50 · Step-by-Step)</strong>
          <span className="text-xs leading-relaxed text-secondary">
            Filter by exam, subject, or topic · clear Unattempted or Missed MCQs systematically with instant answers.
          </span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={studioMode === 'mock'}
          onClick={() => switchStudioMode('mock')}
          className={`flex flex-col items-start gap-1 rounded-[18px] border-2 p-4 text-left transition ${
            studioMode === 'mock'
              ? 'border-ink bg-card shadow-[var(--ism-card-shadow)]'
              : 'border-hairline bg-paper/70 hover:border-hairline2'
          }`}
        >
          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-exams-dark">
            Mode 2 · Always full paper
          </span>
          <strong className="font-display text-xl text-ink">Full-Paper Mock</strong>
          <span className="text-xs leading-relaxed text-secondary">
            Real past paper or full 100-question exam · server countdown · answers scored at submit.
          </span>
        </button>
      </div>

      {studioMode === 'practice' ? (
        <form
          onSubmit={handleStartPractice}
          className="pr-setup-card mt-5 space-y-6 rounded-[22px] border border-hairline bg-card p-6 shadow-[var(--ism-card-shadow)] sm:p-7"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-4">
            <div className="finna-segments" role="group" aria-label="Question format">
              <button
                type="button"
                aria-pressed={format === 'mcq'}
                onClick={() => setFormat('mcq')}
              >
                ◉ MCQs
              </button>
              <button
                type="button"
                aria-pressed={format === 'written'}
                onClick={() => setFormat('written')}
              >
                ✎ Written answers
              </button>
            </div>
            <Link to="/bank" className="text-sm font-bold text-link hover:underline">
              Full question bank →
            </Link>
          </div>

          <div>
            <p className="finna-eyebrow">01 · What to practise</p>
            {quickExams.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-2" role="group" aria-label="Quick exam picks">
                <button
                  type="button"
                  aria-pressed={examId === ''}
                  onClick={() => {
                    examInitializedRef.current = true
                    setExamId('')
                  }}
                  className={`pp-exam-pill${examId === '' ? ' is-active' : ''}`}
                >
                  All exams
                </button>
                {quickExams.map((ex) => (
                  <button
                    key={ex.id}
                    type="button"
                    aria-pressed={examId === ex.id}
                    onClick={() => {
                      examInitializedRef.current = true
                      setExamId(ex.id)
                    }}
                    className={`pp-exam-pill${examId === ex.id ? ' is-active' : ''}`}
                  >
                    {shortExamLabel(ex)}
                  </button>
                ))}
              </div>
            )}
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                Exam
                <select
                  aria-label="Exam"
                  value={examId}
                  onChange={(e) => {
                    examInitializedRef.current = true
                    setExamId(e.target.value)
                  }}
                  className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
                >
                  <option value="">All exams</option>
                  {examCollections.map((ex) => (
                    <option key={ex.id} value={ex.id}>
                      {ex.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                Subject
                <select
                  aria-label="Subject"
                  value={subjectId}
                  onChange={(e) => {
                    setSubjectId(e.target.value)
                    setTopicId('')
                  }}
                  className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
                >
                  <option value="">All subjects</option>
                  {subjects.map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                {topicsForSubject.length > 0 ? 'Topic' : 'Search'}
                {topicsForSubject.length > 0 ? (
                  <select
                    aria-label="Topic"
                    value={topicId}
                    onChange={(e) => setTopicId(e.target.value)}
                    className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
                  >
                    <option value="">All topics in subject</option>
                    {topicsForSubject.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.label} ({t.count.toLocaleString('en-IN')})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="search"
                    aria-label="Search topic or text"
                    placeholder="Optional keyword…"
                    value={query}
                    maxLength={120}
                    onChange={(e) => setQuery(e.target.value)}
                    className="min-h-11 rounded-lg border border-hairline2 bg-paper px-3 text-sm font-normal normal-case tracking-normal text-ink"
                  />
                )}
              </label>
            </div>

            {topicsForSubject.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Quick topic filter">
                <button
                  type="button"
                  aria-pressed={!topicId}
                  onClick={() => setTopicId('')}
                  className={`min-h-9 rounded-full border px-3 text-xs font-semibold ${!topicId ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink'}`}
                >
                  All topics
                </button>
                {topicsForSubject.slice(0, 10).map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    aria-pressed={topicId === t.id}
                    onClick={() => setTopicId(topicId === t.id ? '' : t.id)}
                    className={`min-h-9 rounded-full border px-3 text-xs font-semibold ${topicId === t.id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink'}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {format === 'mcq' && (
              <div>
                <p className="finna-eyebrow">02 · Question queue</p>
                <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Question queue">
                  {([
                    ['unseen', 'Unattempted'],
                    ['ever_wrong', 'Missed only'],
                    ['all', 'All MCQs'],
                  ] as const).map(([val, label]) => (
                    <button
                      key={val}
                      type="button"
                      aria-pressed={queue === val}
                      onClick={() => setQueue(val)}
                      className={
                        'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
                        (queue === val ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <p className="finna-eyebrow">{format === 'mcq' ? '03 · Pace' : '02 · Batch size'}</p>
              <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Practice pace">
                {([
                  ['50', '50 by 50'],
                  ['25', '25 by 25'],
                  ['step', 'Step 1-by-1'],
                ] as const).map(([val, label]) => (
                  <button
                    key={val}
                    type="button"
                    aria-pressed={pace === val}
                    onClick={() => setPace(val)}
                    className={
                      'min-h-11 rounded-lg border px-4 py-2 text-sm font-semibold ' +
                      (pace === val ? 'border-ink bg-ink text-paper' : 'border-hairline bg-paper text-ink')
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-5">
            <p className="text-xs font-medium text-secondary">
              Work through the entire filtered pool systematically — move batch by batch with instant answers &amp; guide links.
            </p>
            <button
              type="submit"
              disabled={loadingRun}
              className="finna-btn min-h-12 px-7 text-[15px] disabled:opacity-50"
            >
              {loadingRun
                ? 'Loading…'
                : format === 'written'
                  ? 'Browse written prompts →'
                  : pace === 'step'
                    ? 'Start Step-by-Step →'
                    : `Start ${pace} by ${pace} Practice →`}
            </button>
          </div>
        </form>
      ) : (
        <section className="pr-setup-card mt-5 space-y-6 rounded-[22px] border border-hairline bg-card p-6 shadow-[var(--ism-card-shadow)] sm:p-7">
          <div>
            <p className="finna-eyebrow">01 · Choose your exam</p>
            {quickExams.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-2" role="group" aria-label="Exam for full-paper mock">
                {quickExams.map((ex) => (
                  <button
                    key={ex.id}
                    type="button"
                    aria-pressed={mockExamId === ex.id}
                    onClick={() => setExamId(ex.id)}
                    className={`pp-exam-pill${mockExamId === ex.id ? ' is-active' : ''}`}
                  >
                    {shortExamLabel(ex)}
                  </button>
                ))}
              </div>
            )}
            <div className="mt-3 max-w-md">
              <select
                aria-label="Exam for full-paper mock"
                value={mockExamId}
                onChange={(e) => setExamId(e.target.value)}
                className="min-h-11 w-full rounded-lg border border-hairline2 bg-paper px-3 text-sm text-ink"
              >
                {examCollections.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Option A: Full-Length Fresh Exam Paper (100 Qs · 120 min) */}
          {generatedFullPaper && examDetail && (
            <div className="rounded-[16px] border-2 border-ink/20 bg-paper p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-exams-dark">
                    Full-length generated paper · {generatedFullPaper.useOfficial ? 'Official keys' : 'Reviewed keys'}
                  </span>
                  <h2 className="mt-1 font-display text-xl text-ink">
                    {examDetail.title} · Full Mock Paper
                  </h2>
                  <p className="mt-1 text-sm text-secondary">
                    <strong>{generatedFullPaper.qCount} questions</strong> · <strong>{generatedFullPaper.minutes} minutes</strong> · real exam timer, question palette, scored at submit.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => startFullPaperMock()}
                  className="finna-btn min-h-12 px-6 text-[15px]"
                >
                  Start Full-Length Mock →
                </button>
              </div>
            </div>
          )}

          {/* Option B: Real Original Past Papers in Printed Order */}
          <div>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="finna-eyebrow">02 · Or sit an exact past paper (printed Q1–Q100 order)</p>
                <p className="mt-1 text-xs text-secondary">
                  Every past paper loads all eligible MCQs from that booklet — never cut down to a 20-question mini-quiz.
                </p>
              </div>
              {eligiblePapers.length > 4 && (
                <input
                  type="search"
                  aria-label="Filter past papers"
                  placeholder="Filter by year or paper…"
                  value={paperFilter}
                  onChange={(e) => setPaperFilter(e.target.value)}
                  className="min-h-10 rounded-lg border border-hairline2 bg-paper px-3 text-sm text-ink"
                />
              )}
            </div>

            {loadingPapers ? (
              <p className="mt-4 text-sm text-secondary">Loading full papers…</p>
            ) : eligiblePapers.length === 0 ? (
              <p className="mt-4 rounded-xl border border-hairline bg-paper p-4 text-sm text-secondary">
                No single past paper with enough MCQs matched your filter for this exam — use the Full-Length Generated Paper above or switch to Practice.
              </p>
            ) : (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {eligiblePapers.slice(0, 12).map((p) => {
                  const id = paperIdentity(p)
                  const { count, useOfficial } = paperMockCount(p)
                  const mins = estimateFullPaperMinutes(count, p.duration_minutes)
                  return (
                    <article
                      key={p.id}
                      className="flex flex-col justify-between gap-3 rounded-[14px] border border-hairline bg-paper p-4"
                    >
                      <div>
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <span className="rounded-md border border-hairline bg-card px-2 py-0.5 font-mono font-bold text-ink">
                            {p.year || 'Past paper'}
                          </span>
                          <span
                            className={`rounded-full px-2.5 py-0.5 font-mono text-[11px] font-semibold ${
                              useOfficial
                                ? 'bg-correct-soft text-correct-dark'
                                : 'bg-practice-soft text-practice-dark'
                            }`}
                          >
                            {useOfficial ? 'Official key' : 'Reviewed key'}
                          </span>
                        </div>
                        <h3 className="mt-2 font-display text-base font-semibold leading-snug text-ink">
                          {id.title}
                        </h3>
                        <p className="mt-1 text-xs text-secondary">
                          {count} MCQs · {mins} min{p.descriptive > 0 ? ` · ${p.descriptive} written excluded` : ''}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => startFullPaperMock(p)}
                        className="inline-flex min-h-11 items-center justify-center rounded-pill border border-ink bg-ink px-4 py-2 text-sm font-semibold text-paper hover:opacity-90"
                      >
                        Start Full Paper ({count} Qs) →
                      </button>
                    </article>
                  )
                })}
              </div>
            )}
          </div>

          <p className="border-t border-hairline pt-4 text-xs font-medium text-secondary">
            Free tier includes 1 Full-Paper Mock per month · Pro includes unlimited mocks · untimed Practice is always available.
          </p>
        </section>
      )}

      {runError && (
        <div role="alert" className="mt-5 rounded-xl border border-wrong bg-wrong-soft p-4 text-sm text-wrong-dark">
          {runError}
        </div>
      )}

      {studioMode === 'practice' && running && !loadingRun && (() => {
        const answeredInBatch = Object.keys(batchOutcomes).length
        const rightInBatch = Object.values(batchOutcomes).filter(Boolean).length
        const accPct = answeredInBatch > 0 ? Math.round((rightInBatch / answeredInBatch) * 100) : null
        const progressPct = items.length > 0 ? Math.round((answeredInBatch / items.length) * 100) : 0
        const activeBatchSize = runConfig?.batchSize || 50
        const activeQueue = runConfig?.queue || queue
        const hasMoreBatches =
          totalAvailable !== null &&
          (batchOffset + items.length < totalAvailable ||
            (activeQueue === 'unseen' && answeredInBatch > 0 && totalAvailable > answeredInBatch))
        const queueLabel =
          activeQueue === 'unseen' ? 'unattempted' : activeQueue === 'ever_wrong' ? 'missed' : 'matching'
        const currentStepQ = items[Math.min(stepIndex, Math.max(0, items.length - 1))]

        return (
          <section ref={runSectionRef} className="mt-8 scroll-mt-24" aria-label="Practice questions">
            <div className="mb-4 rounded-[18px] border border-hairline bg-card p-4 shadow-[var(--ism-card-shadow)]">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-ink">
                    {format === 'written'
                      ? `Written prompts · Batch ${batchNumber}`
                      : `Batch ${batchNumber} · ${items.length} questions`}
                    {totalAvailable !== null ? ` (${totalAvailable.toLocaleString('en-IN')} ${queueLabel})` : ''}
                  </h2>
                  {format === 'mcq' && (
                    <p className="mt-0.5 text-xs font-medium text-secondary">
                      {answeredInBatch} / {items.length} answered
                      {answeredInBatch > 0 ? ` · ${rightInBatch} right (${accPct}%)` : ' · tap any option for instant feedback'}
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {format === 'mcq' && items.length > 1 && (
                    <div className="finna-segments" role="group" aria-label="Practice view mode">
                      <button
                        type="button"
                        aria-pressed={pace !== 'step'}
                        onClick={() => setPace(activeBatchSize === 25 ? '25' : '50')}
                      >
                        List ({activeBatchSize})
                      </button>
                      <button
                        type="button"
                        aria-pressed={pace === 'step'}
                        onClick={() => setPace('step')}
                      >
                        Step 1-by-1
                      </button>
                    </div>
                  )}
                  {format === 'mcq' && <AnswerLayoutControl compact />}
                </div>
              </div>
              {format === 'mcq' && items.length > 0 && (
                <div
                  className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-paper"
                  role="progressbar"
                  aria-label="Current batch progress"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={progressPct}
                >
                  <div
                    className="h-full rounded-full bg-ink transition-[width] duration-200"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              )}
            </div>

            {!items.length ? (
              <div className="rounded-xl border border-hairline bg-card p-6 text-center">
                <h3 className="text-lg font-bold text-ink">
                  {activeQueue === 'unseen' ? 'All caught up in this filter!' : 'No matching questions'}
                </h3>
                <p className="mt-2 text-sm text-secondary">
                  {activeQueue === 'unseen'
                    ? 'You have already attempted every matching MCQ here. Revise your missed questions or practice the full pool.'
                    : 'Try clearing a subject, topic, or keyword filter, or switch to all exams.'}
                </p>
                {activeQueue === 'unseen' && format === 'mcq' && (
                  <div className="mt-4 flex flex-wrap justify-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setQueue('ever_wrong')
                        void launchUntimedRun(examId, subjectId, topicId, format, 'ever_wrong', pace)
                      }}
                      className="finna-btn min-h-11 px-5 text-sm"
                    >
                      Revise missed only
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setQueue('all')
                        void launchUntimedRun(examId, subjectId, topicId, format, 'all', pace)
                      }}
                      className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-paper px-5 text-sm font-semibold text-ink"
                    >
                      Practice all MCQs
                    </button>
                  </div>
                )}
              </div>
            ) : pace === 'step' && currentStepQ ? (
              <div className="space-y-4">
                <div key={currentStepQ.id} className="finna-bank-row">
                  <button
                    type="button"
                    className="finna-bank-check"
                    aria-pressed={tray.has(currentStepQ.id)}
                    aria-label={tray.has(currentStepQ.id) ? 'Remove from test tray' : 'Add to test tray'}
                    onClick={() => tray.toggle(currentStepQ.id)}
                  >
                    {tray.has(currentStepQ.id) ? '✓' : ''}
                  </button>
                  <QuestionCard
                    key={currentStepQ.id}
                    q={currentStepQ}
                    onAnswered={(res) => {
                      setBatchOutcomes((old) => ({ ...old, [currentStepQ.id]: Boolean(res?.correct) }))
                    }}
                    onNext={() => {
                      if (stepIndex + 1 < items.length) setStepIndex((i) => i + 1)
                      else if (hasMoreBatches) handleNextBatch()
                    }}
                  />
                </div>
                <nav
                  aria-label="Step-by-step practice navigation"
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-hairline bg-card px-4 py-3 shadow-[var(--ism-card-shadow)]"
                >
                  <button
                    type="button"
                    disabled={stepIndex <= 0 && batchOffset <= 0}
                    onClick={() => {
                      if (stepIndex > 0) setStepIndex((i) => i - 1)
                      else handlePrevBatch()
                    }}
                    className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-paper px-4 text-sm font-semibold text-ink disabled:opacity-40"
                  >
                    ← Previous
                  </button>
                  <span className="font-mono text-xs font-bold text-secondary">
                    Q{stepIndex + 1} of {items.length} · Batch {batchNumber}
                  </span>
                  {stepIndex + 1 < items.length ? (
                    <button
                      type="button"
                      onClick={() => setStepIndex((i) => i + 1)}
                      className="finna-btn min-h-11 px-5 text-sm"
                    >
                      {currentStepQ.id in batchOutcomes ? 'Next question →' : 'Skip →'}
                    </button>
                  ) : hasMoreBatches ? (
                    <button
                      type="button"
                      onClick={handleNextBatch}
                      className="finna-btn min-h-11 px-5 text-sm"
                    >
                      Load Next {activeBatchSize} →
                    </button>
                  ) : (
                    <span className="text-xs font-semibold text-secondary">End of pool</span>
                  )}
                </nav>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {items.map((q) => (
                    <div key={q.id} className="finna-bank-row">
                      <button
                        type="button"
                        className="finna-bank-check"
                        aria-pressed={tray.has(q.id)}
                        aria-label={tray.has(q.id) ? 'Remove from test tray' : 'Add to test tray'}
                        onClick={() => tray.toggle(q.id)}
                      >
                        {tray.has(q.id) ? '✓' : ''}
                      </button>
                      <QuestionCard
                        q={q}
                        onAnswered={(res) => {
                          setBatchOutcomes((old) => ({ ...old, [q.id]: Boolean(res?.correct) }))
                        }}
                      />
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-hairline bg-card p-4 shadow-[var(--ism-card-shadow)]">
                  <div>
                    <strong className="block text-sm text-ink">
                      Batch {batchNumber} · {answeredInBatch} / {items.length} answered
                      {answeredInBatch > 0 ? ` · ${rightInBatch} right (${accPct}%)` : ''}
                    </strong>
                    <span className="text-xs text-secondary">
                      {activeQueue === 'unseen'
                        ? 'Answered questions leave your Unattempted queue automatically when you load the next batch.'
                        : 'Move to the next batch to keep working through the filtered pool.'}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {batchOffset > 0 && (
                      <button
                        type="button"
                        onClick={handlePrevBatch}
                        className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-paper px-4 text-sm font-semibold text-ink"
                      >
                        ← Previous {activeBatchSize}
                      </button>
                    )}
                    {hasMoreBatches && (
                      <button
                        type="button"
                        onClick={handleNextBatch}
                        className="finna-btn min-h-11 px-5 text-sm"
                      >
                        Next {activeBatchSize} questions →
                      </button>
                    )}
                  </div>
                </div>
              </>
            )}
          </section>
        )
      })()}
    </div>
  )
}
