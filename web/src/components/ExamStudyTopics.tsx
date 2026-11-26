import { learningSubjectTitle } from '../lib/groupBStudy'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import guidesCatalog from '../data/guides-catalog.json'
import MaterialDiscovery from './MaterialDiscovery'
import {
  getExamStudyTopics,
  isSubjectModule,
  listCollections,
  moduleHref,
  type Collection,
  type GroupBStudyArea,
  type ExamStudySubject,
  type ExamStudyTopics as StudyTopics,
} from '../lib/api'

type Selection = { subject_id?: string; topic_id?: string; subtopic_id?: string }

interface LiveGuideSummary {
  slug: string
  title: string
  subject_id?: string | null
  topic_id?: string | null
  summary: string
  reading_minutes: number
  chapter_count?: number
  chapters?: unknown[]
}

const SEED_GUIDES = guidesCatalog as LiveGuideSummary[]

const SUBJECT_GUIDE_ALIASES: Record<string, string[]> = {
  'gk-gs': ['gk-gs', 'general-knowledge', 'general-studies', 'polity', 'history', 'geography', 'economy', 'science', 'environment', 'mizoram'],
  english: ['english', 'grammar', 'vocabulary'],
  mathematics: ['mathematics', 'math', 'arithmetic', 'quantitative'],
  reasoning: ['reasoning', 'aptitude', 'logic', 'csat'],
  'computer-science': ['computer-science', 'computer', 'it'],
  science: ['science', 'physics', 'chemistry', 'biology'],
  mizo: ['mizo'],
}

function guideMatchesSubject(guide: LiveGuideSummary, subjectId: string): boolean {
  const gSub = (guide.subject_id || '').trim().toLowerCase()
  if (!gSub) return false
  const target = subjectId.replace(/^subject-/, '').toLowerCase()
  if (gSub === target || gSub.startsWith(target + ':') || gSub.startsWith(target + '/')) return true
  const aliases = SUBJECT_GUIDE_ALIASES[target]
  return aliases ? aliases.some((a) => gSub === a || gSub.includes(a)) : false
}

function guideTone(slug: string, idx: number): 'teal' | 'cobalt' | 'amber' | 'emerald' {
  if (slug.includes('tense') || slug.includes('english')) return 'teal'
  if (slug.includes('polity')) return 'cobalt'
  if (slug.includes('quick') || slug.includes('revision')) return 'emerald'
  const palette: ('teal' | 'cobalt' | 'amber' | 'emerald')[] = ['teal', 'cobalt', 'amber', 'emerald']
  return palette[idx % palette.length]
}

const TOPIC_COMPANIONS: Record<string, { label: string; to: string }> = {
  'english/grammar': { label: 'Read Tenses & Voice guide →', to: '/guides/tenses-and-voice' },
  'english/vocabulary': { label: 'Open Vocabulary Builder →', to: '/vocabulary' },
  'mathematics/arithmetic': { label: 'Maths & Arithmetic Handbook →', to: '/guides/maths-and-arithmetic' },
  'mathematics/algebra': { label: 'Algebra & Indices chapter →', to: '/guides/maths-and-arithmetic#algebra-probability-pnc' },
  'mathematics/mensuration': { label: '2D & 3D Mensuration formulas →', to: '/guides/maths-and-arithmetic#mensuration-2d-3d' },
  'mathematics/geometry': { label: 'Geometry & Trig chapter →', to: '/guides/maths-and-arithmetic#geometry-trig-di-stats' },
  'gk-gs:indian-polity': { label: 'Read Indian Polity Codex →', to: '/guides/polity-codex' },
  'gk-gs:geography': { label: 'Read Geography Guide →', to: '/guides/geography-essentials' },
  'gk-gs:environment': { label: 'Forests & Protected Areas →', to: '/guides/geography-essentials#forests' },
  'gk-gs:mizoram': { label: 'Mizoram Geography chapter →', to: '/guides/geography-essentials#mizoram-geography' },
  'gk-gs:indian-history': { label: 'Read History Guide →', to: '/guides/history-essentials' },
  'gk-gs:world-history': { label: 'History Milestones & Chronicle →', to: '/guides/history-essentials#modern-india-mizoram-world-milestones' },
  'gk-gs:indian-economy': { label: 'Indian Economy & Banking →', to: '/guides/indian-economy' },
  'general-studies/indian-economy': { label: 'Indian Economy & Banking →', to: '/guides/indian-economy' },
  'computer-science/computer-systems-and-architecture': { label: 'Computer Hardware & Memory →', to: '/guides/computer-fundamentals#hardware-memory-architecture' },
  'computer-science/operating-systems': { label: 'OS & Windows Shortcuts →', to: '/guides/computer-fundamentals#os-windows-shortcuts' },
  'computer-science/office-applications': { label: 'MS Word, Excel & PPT Guide →', to: '/guides/computer-fundamentals#ms-office-word-excel-ppt' },
  'computer-science/networking': { label: 'Networks & Cybersecurity →', to: '/guides/computer-fundamentals#networking-internet-cyber' },
  'computer-science/databases': { label: 'DBMS & SQL Basics →', to: '/guides/computer-fundamentals#databases-sql-basics' },
  'science/physics': { label: 'Physics SI Units & Optics →', to: '/guides/general-science#physics-units-optics-electricity' },
  'science/chemistry': { label: 'Chemistry Essentials →', to: '/guides/general-science#chemistry-periodic-acids-everyday' },
  'science/biology': { label: 'Biology, Hormones & Vitamins →', to: '/guides/general-science#biology-human-body-diseases' },
  'reasoning-and-aptitude/series': { label: 'Series & EJOTY Shortcuts →', to: '/guides/reasoning-aptitude#series-ejoty-patterns' },
  'reasoning-and-aptitude/verbal-reasoning': { label: 'Reasoning & Coding Guide →', to: '/guides/reasoning-aptitude#coding-analogy-classification' },
  'reasoning-and-aptitude/data-interpretation': { label: 'DI & Decision-Making →', to: '/guides/reasoning-aptitude#data-interpretation-decision' },
}

function studyLink(
  examId: string,
  view: 'browse' | 'practice',
  selection: Selection,
  area?: GroupBStudyArea,
  basePath?: string,
) {
  const params = new URLSearchParams({ view })
  if (examId === 'combined-prelims') {
    const section = new URLSearchParams(window.location.search).get('section')
    if (section === 'gs' || section === 'aptitude') params.set('section', section)
  }
  if (area) params.set('study_area', area)
  if (basePath && !basePath.startsWith('/subjects/')) params.set('collection', examId)
  if (view === 'practice') params.set('pool', 'practice')
  for (const [key, value] of Object.entries(selection)) if (value) params.set(key, value)
  return `${basePath || `/exams/${encodeURIComponent(examId)}`}?${params}#exam-question-browser`
}

export default function ExamStudyTopics({
  examId,
  area,
  basePath,
  allowPractice = true,
  isSubjectView = false,
}: {
  examId: string
  area?: GroupBStudyArea
  basePath?: string
  allowPractice?: boolean
  isSubjectView?: boolean
}) {
  const [params] = useSearchParams()
  const section = examId === 'combined-prelims' ? params.get('section') || undefined : undefined
  const [data, setData] = useState<StudyTopics | null>(null)
  const [liveGuides, setLiveGuides] = useState<LiveGuideSummary[] | null>(null)
  const [subjectBooks, setSubjectBooks] = useState<Collection[]>([])
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'count' | 'alpha'>('count')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  useEffect(() => {
    let live = true
    setData(null)
    setError('')
    setExpanded({})
    getExamStudyTopics(examId, area, section)
      .then((value) => {
        if (live) setData(value)
      })
      .catch((e) => {
        if (live) setError(e instanceof Error ? e.message : 'Could not load subjects')
      })
    return () => {
      live = false
    }
  }, [examId, area, section])

  // Future-proof live discovery of published concept guides & subject books
  useEffect(() => {
    let live = true
    fetch('/api/guides')
      .then((r) => (r.ok ? r.json() : null))
      .then((payload) => {
        if (live && Array.isArray(payload?.items) && payload.items.length) {
          setLiveGuides(payload.items as LiveGuideSummary[])
        }
      })
      .catch(() => {})
    listCollections()
      .then((rows) => {
        if (live) setSubjectBooks(rows.filter(isSubjectModule))
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [])

  const displayTitle = (subject: ExamStudySubject) =>
    learningSubjectTitle(subject.id, subject.title, examId)
  const query = search.trim().toLocaleLowerCase()

  const singleSubjectMode = Boolean(
    data && (isSubjectView || data.subjects.length === 1),
  )
  const primarySubject = singleSubjectMode ? data?.subjects[0] ?? null : null

  const filteredSingleTopics = useMemo(() => {
    if (!primarySubject) return []
    const matched = primarySubject.topics.filter(
      (topic) =>
        !query ||
        topic.title.toLocaleLowerCase().includes(query) ||
        topic.subtopics.some((st) => st.title.toLocaleLowerCase().includes(query)),
    )
    return matched.slice().sort((a, b) =>
      sortBy === 'alpha' ? a.title.localeCompare(b.title) : b.questions - a.questions,
    )
  }, [primarySubject, query, sortBy])

  const subjects = useMemo(
    () =>
      data?.subjects.filter(
        (subject) =>
          !query ||
          subject.title.toLocaleLowerCase().includes(query) ||
          subject.topics.some(
            (topic) =>
              topic.title.toLocaleLowerCase().includes(query) ||
              topic.subtopics.some((subtopic) =>
                subtopic.title.toLocaleLowerCase().includes(query),
              ),
          ),
      ) ?? [],
    [data, query],
  )

  const matchedGuides = useMemo(() => {
    if (!primarySubject) return []
    const bySlug = new Map<string, LiveGuideSummary>()
    for (const g of SEED_GUIDES) bySlug.set(g.slug, g)
    if (liveGuides && liveGuides.length) {
      for (const g of liveGuides) {
        const seed = bySlug.get(g.slug)
        bySlug.set(g.slug, { ...seed, ...g })
      }
    }
    return [...bySlug.values()].filter((g) => guideMatchesSubject(g, primarySubject.id))
  }, [liveGuides, primarySubject])

  /* ── SINGLE-SUBJECT TOPIC-WISE STUDIO VIEW (/subjects/english?view=topics, etc.) ── */
  if (singleSubjectMode && data && primarySubject) {
    const subjectSelection: Selection = { subject_id: primarySubject.id }
    const subjectName = displayTitle(primarySubject)
    const totalSubtopics = primarySubject.topics.reduce(
      (sum, t) => sum + t.subtopics.length,
      0,
    )
    return (
      <section className="est-shell" aria-labelledby="exam-study-heading">
        {/* Dual Navigation Dock: Switch Subject Book + Jump Between Topics & Guides/Tools Sections */}
        <div className="est-nav-dock">
          {subjectBooks.length > 1 && (
            <nav aria-label="Switch subject book" className="est-subject-rail">
              <span className="est-rail-label">Subjects</span>
              <div className="est-rail-pills">
                {subjectBooks.map((book) => {
                  const active = book.id === examId
                  return (
                    <Link
                      key={book.id}
                      to={`${moduleHref(book)}?view=topics`}
                      aria-current={active ? 'page' : undefined}
                      className={`est-subj-pill${active ? ' is-active' : ''}`}
                    >
                      {book.title}
                    </Link>
                  )
                })}
              </div>
            </nav>
          )}

          <nav aria-label="Jump to section" className="est-section-nav">
            <div className="est-section-links">
              <a href="#est-topics-section" className="est-sec-link is-primary">
                <span>1. Topics</span>
                <b>{primarySubject.topics.length}</b>
              </a>
              <a href="#est-resources-section" className="est-sec-link">
                <span>2. Guides, Notes &amp; Tools</span>
                {matchedGuides.length > 0 && <b>{matchedGuides.length}</b>}
              </a>
            </div>
            <div className="est-section-actions">
              <Link
                to={studyLink(examId, 'browse', subjectSelection, area, basePath)}
                className="est-sec-action"
              >
                Browse all ({data.questions.toLocaleString('en-IN')}) →
              </Link>
              {allowPractice && (
                <Link
                  to={studyLink(examId, 'practice', subjectSelection, area, basePath)}
                  className="est-sec-action is-accent"
                >
                  Start practice →
                </Link>
              )}
            </div>
          </nav>
        </div>

        {/* Section 1: Topic-Wise Header, Filter & Direct 2-Column Topic Cards */}
        <div id="est-topics-section" className="est-section-block scroll-mt-28">
        <div className="est-toolbar">
          <div className="est-toolbar-copy">
            <h2 id="exam-study-heading">
              {displayTitle(primarySubject)} topics
            </h2>
            <p>
              {primarySubject.topics.length} topics
              {totalSubtopics > 0 ? ` · ${totalSubtopics} subtopics` : ''} ·{' '}
              {data.questions.toLocaleString('en-IN')} distinct questions across all exams
            </p>
          </div>
          <div className="est-toolbar-controls">
            <input
              type="search"
              aria-label="Find a topic or subtopic"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter topics or subtopics…"
              className="est-search"
            />
            <div className="est-sort-seg" role="group" aria-label="Sort topics">
              <button
                type="button"
                aria-pressed={sortBy === 'count'}
                className={sortBy === 'count' ? 'is-on' : ''}
                onClick={() => setSortBy('count')}
              >
                Most Qs
              </button>
              <button
                type="button"
                aria-pressed={sortBy === 'alpha'}
                className={sortBy === 'alpha' ? 'is-on' : ''}
                onClick={() => setSortBy('alpha')}
              >
                A–Z
              </button>
            </div>
            <Link
              to={studyLink(examId, 'browse', subjectSelection, area, basePath)}
              className="est-all-btn"
            >
              Browse all →
            </Link>
          </div>
        </div>

        {/* Direct 2-Column Topic Cards (Zero hidden 1-subject accordion!) */}
        {!filteredSingleTopics.length ? (
          <div className="est-empty">
            No topics match “{search}”.{' '}
            <button type="button" onClick={() => setSearch('')} className="underline font-semibold">
              Show all topics
            </button>
          </div>
        ) : (
          <div className="est-topic-grid">
            {filteredSingleTopics.map((topic, idx) => {
              const sharePct = data.questions > 0
                ? Math.max(2, Math.round((topic.questions / data.questions) * 100))
                : 0
              const visibleSubtopics = topic.subtopics.filter(
                (st) =>
                  !query ||
                  topic.title.toLocaleLowerCase().includes(query) ||
                  st.title.toLocaleLowerCase().includes(query),
              )
              const dynamicTopicGuide = matchedGuides.find(
                (g) => g.topic_id && g.topic_id === topic.id,
              )
              const companion = dynamicTopicGuide
                ? {
                    label: `Read ${dynamicTopicGuide.title} →`,
                    to: `/guides/${encodeURIComponent(dynamicTopicGuide.slug)}`,
                  }
                : TOPIC_COMPANIONS[topic.id]
              return (
                <article key={topic.id} className="est-topic-card">
                  <div className="est-topic-head">
                    <div className="est-topic-title-wrap">
                      <span className="est-topic-num">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <div>
                        <h3>{topic.title}</h3>
                        <span className="est-topic-submeta">
                          {topic.subtopics.length > 0
                            ? `${topic.subtopics.length} subtopics · `
                            : ''}
                          {sharePct}% of {displayTitle(primarySubject)}
                        </span>
                      </div>
                    </div>
                    <span className="est-topic-count">
                      {topic.questions.toLocaleString('en-IN')} Qs
                    </span>
                  </div>

                  <div className="est-topic-meter" aria-hidden="true">
                    <span style={{ width: `${Math.min(100, sharePct)}%` }} />
                  </div>

                  {visibleSubtopics.length > 0 && (
                    <div className="est-subtopic-list" aria-label={`${topic.title} subtopics`}>
                      {visibleSubtopics.map((st) => (
                        <Link
                          key={st.id}
                          to={studyLink(
                            examId,
                            'browse',
                            { ...subjectSelection, topic_id: topic.id, subtopic_id: st.id },
                            area,
                            basePath,
                          )}
                          className="est-subtopic-chip"
                        >
                          <span>{st.title}</span>
                          <b>{st.questions.toLocaleString('en-IN')}</b>
                        </Link>
                      ))}
                    </div>
                  )}

                  <div className="est-topic-foot">
                    <div className="est-topic-btns">
                      <Link
                        to={studyLink(
                          examId,
                          'browse',
                          { ...subjectSelection, topic_id: topic.id },
                          area,
                          basePath,
                        )}
                        className="est-btn-primary"
                      >
                        Browse topic →
                      </Link>
                      {allowPractice && (
                        <Link
                          to={studyLink(
                            examId,
                            'practice',
                            { ...subjectSelection, topic_id: topic.id },
                            area,
                            basePath,
                          )}
                          className="est-btn-ghost"
                        >
                          Practise
                        </Link>
                      )}
                    </div>
                    {companion && (
                      <Link to={companion.to} className="est-topic-companion">
                        {companion.label}
                      </Link>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        )}

        </div>

        {/* Section 2: Guides, Notes & Future Additions */}
        <div id="est-resources-section" className="est-section-block scroll-mt-28">
          {matchedGuides.length > 0 && (
            <div className="est-guide-strip" aria-label="Published concept guides for this subject">
              {matchedGuides.map((g, idx) => {
                const chCount = g.chapter_count ?? g.chapters?.length ?? 0
                return (
                  <Link
                    key={g.slug}
                    to={`/guides/${encodeURIComponent(g.slug)}`}
                    className={`est-guide-card est-gtone-${guideTone(g.slug, idx)}`}
                  >
                    <div className="est-guide-top">
                      <span className="est-guide-eyebrow">Concept Guide</span>
                      <span className="est-guide-meta">
                        {chCount > 0 ? `${chCount} chapters · ` : ''}
                        {g.reading_minutes} min read
                      </span>
                    </div>
                    <h3>{g.title}</h3>
                    <p>{g.summary}</p>
                    <span className="est-guide-cta">Read guide →</span>
                  </Link>
                )
              })}
            </div>
          )}

          {/* Live Published Notes & Lessons for This Subject (auto-populates as new materials publish) */}
          <MaterialDiscovery
            subjectId={primarySubject.id}
            title={`${subjectName} study notes & revision sheets`}
            hideEmpty
          />

          {/* Future-Update-Proof Subject Resources & Additions Hub */}
          <section
            className="est-future-hub"
            aria-label={`${subjectName} study tools and future additions`}
          >
            <div className="est-future-head">
              <div>
                <span className="est-future-eyebrow">Subject tools &amp; updates</span>
                <h3>More ways to master {subjectName}</h3>
                <p>
                  New concept guides, revision sheets, and tagged question sets published for {subjectName} appear here automatically.
                </p>
              </div>
              <div className="est-future-head-actions">
                <a href="#est-topics-section" className="est-back-top-link">
                  ↑ Back to topics
                </a>
                <Link to="/studio/new" className="est-future-add">
                  + Publish a note
                </Link>
              </div>
            </div>
            <div className="est-future-grid">
              <Link to="/guides" className="est-future-tile">
                <strong>Concept guides</strong>
                <span>
                  {matchedGuides.length > 0
                    ? `${matchedGuides.length} ${matchedGuides.length === 1 ? 'guide' : 'guides'} linked to ${subjectName}`
                    : `Browse reading room — new ${subjectName} guides appear automatically`}
                </span>
              </Link>
              <Link to="/revise" className="est-future-tile">
                <strong>Spaced revision</strong>
                <span>Review missed {subjectName} questions and scheduled flashcards</span>
              </Link>
              <Link to="/practice/build" className="est-future-tile">
                <strong>Custom practice test</strong>
                <span>Assemble a timed {subjectName} set from specific topics</span>
              </Link>
              <Link to="/materials" className="est-future-tile">
                <strong>Community study notes</strong>
                <span>Formula sheets, topic summaries, and contributor walkthroughs</span>
              </Link>
            </div>
          </section>
        </div>

        <p className="mt-1 text-xs leading-relaxed text-secondary">
          A question can carry more than one approved topic tag, so topic totals can overlap. Browse shows all available questions; Practise filters to answer-ready MCQs with review labels visible.
        </p>
      </section>
    )
  }

  /* ── MULTI-SUBJECT EXAM TOPIC VIEW (/exams/udc?view=topics, etc.) ── */
  return (
    <section className="mt-5" aria-labelledby="exam-study-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-xs uppercase tracking-[.12em] text-exams-dark">
            Your study route
          </div>
          <h2 id="exam-study-heading" className="mt-1 font-display text-2xl font-medium">
            Study by subject and topic
          </h2>
          <p className="mt-1.5 max-w-[700px] text-sm leading-relaxed text-secondary">
            Open a subject to explore its topics, or jump straight into questions.
          </p>
        </div>
        {data && (
          <span className="rounded-pill border border-hairline bg-card px-3 py-2 font-mono text-xs text-secondary">
            {data.subjects.length} subjects · {data.questions.toLocaleString('en-IN')} distinct questions
          </span>
        )}
      </div>
      {error && (
        <p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-sm text-mypick">
          Could not load this exam’s topic map: {error}
        </p>
      )}
      {!data && !error && (
        <p role="status" className="mt-4 rounded-[14px] border border-hairline bg-card p-5 text-sm text-secondary">
          Loading subjects and topics…
        </p>
      )}
      {data && (
        <>
          <div className="mt-4 flex flex-wrap items-end gap-3 rounded-[14px] border border-hairline bg-card p-4">
            <label className="min-w-0 basis-56 flex-1 text-xs font-semibold">
              Find a subject or topic
              <input
                type="search"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setExpanded({})
                }}
                placeholder="English, arithmetic, computer…"
                className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas px-3 text-sm placeholder:text-placeholder focus:border-ink focus:outline-none"
              />
            </label>
            <Link
              to={studyLink(examId, 'browse', {}, area, basePath)}
              className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-sm font-semibold"
            >
              Browse all exam questions →
            </Link>
          </div>
          {!subjects.length && (
            <p className="mt-5 rounded-[12px] border border-hairline bg-card p-5 text-sm text-secondary">
              No subject or topic matches that search.
            </p>
          )}
          {subjects.length > 1 && (
            <nav aria-label="Jump to subject" className="est-exam-jump">
              <span className="est-rail-label">Jump to subject</span>
              <div className="est-rail-pills">
                {subjects.map((subject) => (
                  <button
                    key={subject.id}
                    type="button"
                    className="est-exam-jump-btn"
                    onClick={() => {
                      setExpanded((previous) => ({ ...previous, [subject.id]: true }))
                      requestAnimationFrame(() => {
                        document
                          .getElementById('subject-card-' + subject.id)
                          ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                      })
                    }}
                  >
                    <span>{displayTitle(subject)}</span>
                    <b>{subject.questions.toLocaleString('en-IN')}</b>
                  </button>
                ))}
              </div>
            </nav>
          )}
          {subjects.length > 0 && (
            <div className="mt-2 flex items-center justify-between text-xs text-secondary">
              <span>{subjects.length} subjects shown</span>
              <button
                type="button"
                className="min-h-11 px-2 font-semibold text-link"
                onClick={() => {
                  const close = subjects.every((subject) => expanded[subject.id] ?? !!query)
                  setExpanded(
                    Object.fromEntries(subjects.map((subject) => [subject.id, !close])),
                  )
                }}
              >
                {subjects.every((subject) => expanded[subject.id] ?? !!query)
                  ? 'Collapse all'
                  : 'Expand all'}
              </button>
            </div>
          )}
          <div className="mt-2 grid items-start gap-3 md:grid-cols-2">
            {subjects.map((subject) => (
              <SubjectCard
                key={subject.id}
                subject={{ ...subject, title: displayTitle(subject) }}
                examId={examId}
                expanded={expanded[subject.id] ?? !!query}
                onToggle={() =>
                  setExpanded((previous) => ({
                    ...previous,
                    [subject.id]: !(previous[subject.id] ?? !!query),
                  }))
                }
                query={query}
                area={area}
                basePath={basePath}
                allowPractice={allowPractice}
              />
            ))}
          </div>
          {data.unclassified > 0 && (
            <p className="mt-4 text-xs leading-relaxed text-secondary">
              {data.unclassified.toLocaleString('en-IN')} questions do not yet have an approved subject tag. They remain available through “Browse all exam questions” and their paper pages.
            </p>
          )}
          <p className="mt-3 text-xs leading-relaxed text-secondary">
            A question can have more than one approved tag, so subject and topic counts can overlap. Browse includes questions without answers; practice uses questions with an available answer and keeps review labels visible.
          </p>
        </>
      )}
    </section>
  )
}

function SubjectCard({
  subject,
  examId,
  expanded,
  onToggle,
  query,
  area,
  basePath,
  allowPractice,
}: {
  subject: ExamStudySubject
  examId: string
  expanded: boolean
  onToggle: () => void
  query: string
  area?: GroupBStudyArea
  basePath?: string
  allowPractice: boolean
}) {
  const topics = subject.topics.filter(
    (topic) =>
      !query ||
      subject.title.toLocaleLowerCase().includes(query) ||
      topic.title.toLocaleLowerCase().includes(query) ||
      topic.subtopics.some((subtopic) =>
        subtopic.title.toLocaleLowerCase().includes(query),
      ),
  )
  const selection = { subject_id: subject.id }
  return (
    <article
      id={'subject-card-' + subject.id}
      className="exam-subject min-w-0 scroll-mt-28"
      data-expanded={expanded}
    >
      <h3>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={expanded}
          aria-controls={'subject-topics-' + subject.id}
          aria-label={`${expanded ? 'Hide' : 'Show'} topics in ${subject.title}`}
          className="exam-subject-toggle"
        >
          <span>
            <span className="exam-subject-title">{subject.title}</span>
            <span className="exam-subject-count">
              {subject.questions.toLocaleString('en-IN')}{' '}
              {subject.questions === 1 ? 'question' : 'questions'} · {subject.topics.length}{' '}
              {subject.topics.length === 1 ? 'topic' : 'topics'}
            </span>
          </span>
          <span className="exam-chevron" aria-hidden="true">
            ⌄
          </span>
        </button>
      </h3>
      <div className="exam-subject-body">
        {!area &&
          ['udc', 'ldc', 'assistant'].includes(examId) &&
          subject.id === 'gk-gs' &&
          subject.topics.some((topic) => topic.id === 'gk-gs:science') && (
            <p className="mt-3 text-xs leading-relaxed text-secondary">
              Includes Science. Open topics to choose Physics, Chemistry, Biology or science in the news.
            </p>
          )}
        {!area && ['udc', 'ldc', 'assistant'].includes(examId) && subject.id === 'science' && (
          <p className="mt-3 text-xs leading-relaxed text-secondary">
            Also included under General Knowledge → Science. Use this subject for deeper science topics.
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to={studyLink(examId, 'browse', selection, area, basePath)}
            className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-xs font-semibold text-paper"
          >
            Browse subject
          </Link>
          {allowPractice && (
            <Link
              to={studyLink(examId, 'practice', selection, area, basePath)}
              className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-xs font-semibold"
            >
              Practise answers
            </Link>
          )}
        </div>
        <div
          id={'subject-topics-' + subject.id}
          hidden={!expanded}
          className="mt-4 border-t border-hairline pt-3"
        >
          {topics.length ? (
            <ul className="space-y-2">
              {topics.map((topic) => (
                <li key={topic.id} className="rounded-[10px] bg-canvas p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <strong className="text-sm">{topic.title}</strong>
                      <span className="ml-2 font-mono text-xs text-muted">
                        {topic.questions.toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Link
                        className="inline-flex min-h-11 items-center px-2 text-xs font-semibold text-link underline"
                        to={studyLink(examId, 'browse', { ...selection, topic_id: topic.id }, area, basePath)}
                      >
                        Browse
                      </Link>
                      {allowPractice && (
                        <Link
                          className="inline-flex min-h-11 items-center px-2 text-xs font-semibold text-link underline"
                          to={studyLink(examId, 'practice', { ...selection, topic_id: topic.id }, area, basePath)}
                        >
                          Practise
                        </Link>
                      )}
                    </div>
                  </div>
                  {topic.subtopics.length > 0 && (
                    <ul className="mt-2 flex flex-wrap gap-2">
                      {topic.subtopics
                        .filter(
                          (subtopic) =>
                            !query ||
                            subject.title.toLocaleLowerCase().includes(query) ||
                            topic.title.toLocaleLowerCase().includes(query) ||
                            subtopic.title.toLocaleLowerCase().includes(query),
                        )
                        .map((subtopic) => (
                          <li key={subtopic.id}>
                            <Link
                              className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-3 text-xs font-semibold hover:border-ink"
                              to={studyLink(
                                examId,
                                'browse',
                                { ...selection, topic_id: topic.id, subtopic_id: subtopic.id },
                                area,
                                basePath,
                              )}
                            >
                              {subtopic.title} · {subtopic.questions}
                            </Link>
                          </li>
                        ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-secondary">
              No narrower approved topics yet. Use the subject buttons to study all its questions.
            </p>
          )}
        </div>
      </div>
    </article>
  )
}
