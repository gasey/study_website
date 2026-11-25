import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ContributorName, GuideStrip } from '../components/ContributorStanding'
import { CommunityFeedback } from '../components/BlockAuthor'
import { EditMarker } from '../components/PostEditing'
import CommunityText from '../components/CommunityText'
import { UserAvatar } from '../components/AvatarArt'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { Card } from '../components/ui'
import {
  getCommunityFeed,
  type CommunityFeedItem,
  type CommunityFeedResponse,
} from '../lib/api'

const Materials = lazy(() => import('./Materials'))
const FollowingMaterials = lazy(() =>
  import('./Creators').then((m) => ({ default: m.FollowingMaterials })),
)
const CommunityQuestions = lazy(() => import('./CommunityQuestions'))
const StudyComposer = lazy(() =>
  import('../components/StudyPosts').then((m) => ({ default: m.StudyComposer })),
)
const StudyPostDetail = lazy(() =>
  import('../components/StudyPosts').then((m) => ({ default: m.StudyPostDetail })),
)

const TABS: { id: CommunityFeedResponse['tab']; label: string }[] = [
  { id: 'for-you', label: 'For you' },
  { id: 'following', label: 'Following' },
  { id: 'questions', label: 'Doubts' },
  { id: 'mcqs', label: 'MCQs' },
  { id: 'materials', label: 'Materials' },
]

const COMPOSE_ITEMS = [
  {
    type: 'Doubt',
    title: 'Ask a doubt',
    desc: 'Link a past-paper question and ask how others solved it.',
    accent: 'amber',
  },
  {
    type: 'Note',
    title: 'Share a study note',
    desc: 'Post a concise summary, mnemonic, or revision sheet.',
    accent: 'violet',
  },
  {
    type: 'Share material',
    title: 'Share a material',
    desc: 'Recommend a reviewed reading guide with your notes.',
    accent: 'teal',
  },
  {
    type: 'MCQ',
    title: 'Contribute an MCQ',
    desc: 'Draft a practice question for community review.',
    accent: 'cobalt',
  },
] as const

export default function Feed({ embedded = false }: { embedded?: boolean }) {
  const nav = useNavigate()
  const [feedParams, setFeedParams] = useSearchParams()

  useEffect(() => {
    if (feedParams.get('section') === 'community') {
      document.getElementById('community-section')?.scrollIntoView({ block: 'start' })
    }
  }, [feedParams])

  const [localTab, setLocalTab] = useState<CommunityFeedResponse['tab']>('for-you')
  const [localDiscussion, setLocalDiscussion] = useState<'all' | 'doubts' | 'unanswered'>('all')
  const rawTab = embedded
    ? localTab
    : feedParams.get('tab') === 'doubts'
      ? 'questions'
      : feedParams.get('tab')
  const tab: CommunityFeedResponse['tab'] = TABS.some((t) => t.id === rawTab)
    ? (rawTab as CommunityFeedResponse['tab'])
    : 'for-you'
  const rawDiscussion = embedded
    ? localDiscussion
    : feedParams.get('discussion') ?? (feedParams.get('tab') === 'doubts' ? 'doubts' : 'all')
  const discussion: 'all' | 'doubts' | 'unanswered' =
    rawDiscussion === 'doubts' || rawDiscussion === 'unanswered' ? rawDiscussion : 'all'

  const setTab = (value: CommunityFeedResponse['tab']) => {
    setOffset(0)
    if (embedded) {
      setLocalTab(value)
      return
    }
    setFeedParams(
      (previous) => {
        const next = new URLSearchParams()
        if (previous.has('exam_scope')) next.set('exam_scope', previous.get('exam_scope')!)
        next.set('tab', value)
        return next
      },
      { replace: true },
    )
  }

  const [result, setFeed] = useState<CommunityFeedResponse | null>(null)
  const feed = result?.tab === tab ? result : null
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [reload, setReload] = useState(0)
  const [offset, setOffset] = useState(0)
  const [composeType, setComposeType] = useState<string | null>(null)

  const studyId = /^\d+$/.test(feedParams.get('study') || '')
    ? Number(feedParams.get('study'))
    : null
  const composeKind =
    feedParams.get('compose') === 'material-share' ? 'material-share' : 'study'
  const composingStudy = ['study', 'material-share'].includes(feedParams.get('compose') || '')

  const closeStudy = () => {
    setFeedParams(
      (previous) => {
        const next = new URLSearchParams(previous)
        next.delete('study')
        next.delete('compose')
        return next
      },
      { replace: true },
    )
    setReload((n) => n + 1)
  }

  const generation = useRef(0)

  useEffect(() => {
    const update = () => {
      ++generation.current
      setFeed(null)
      setLoading(true)
      setComposeType(null)
      setOffset(0)
      setReload((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', update)
    window.addEventListener('ism-auth-expired', update)
    window.addEventListener('ism-community-change', update)
    return () => {
      ++generation.current
      window.removeEventListener('ism-auth-change', update)
      window.removeEventListener('ism-auth-expired', update)
      window.removeEventListener('ism-community-change', update)
    }
  }, [])

  useEffect(() => {
    if (tab === 'materials' || tab === 'mcqs') return
    let active = true
    const run = ++generation.current
    if (offset === 0) setFeed(null)
    setLoading(true)
    setError(false)
    getCommunityFeed(tab, offset, tab === 'questions' ? discussion : 'all')
      .then((res) => {
        if (active && run === generation.current) {
          setFeed((previous) =>
            offset === 0 || previous?.tab !== res.tab
              ? res
              : {
                  ...res,
                  items: [
                    ...previous.items,
                    ...res.items.filter(
                      (item) => !previous.items.some((old) => old.id === item.id),
                    ),
                  ],
                },
          )
        }
      })
      .catch(() => {
        if (active && run === generation.current) setError(true)
      })
      .finally(() => {
        if (active && run === generation.current) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [tab, discussion, offset, reload])

  const startCompose = (type: string) =>
    type === 'MCQ'
      ? nav('/create/new?kind=new_question')
      : type === 'Note'
        ? nav('/community?compose=study')
        : type === 'Share material'
          ? nav('/community?compose=material-share')
          : ['Material', 'Post'].includes(type)
            ? nav('/studio/new')
            : setComposeType(type)

  const setDiscussionFilter = (value: 'all' | 'doubts' | 'unanswered') => {
    setOffset(0)
    if (embedded) {
      setLocalDiscussion(value)
      return
    }
    setFeedParams((previous) => {
      const next = new URLSearchParams(previous)
      next.set('tab', 'questions')
      next.set('discussion', value)
      return next
    })
  }

  return (
    <div className={embedded ? 'finna-embedded-community' : 'finna-page fd-shell'}>
      {!embedded && (
        <header className="av-hero fd-hero">
          <div className="av-hero-copy">
            <span className="cr-eyebrow">Learn together · Study reading room</span>
            <h1>Community feed</h1>
            <p>
              Discuss tricky past-paper questions, read worked explanations, and share
              concise study notes with learners across Mizoram.
            </p>
          </div>
          <div className="av-hero-actions">
            <button
              type="button"
              onClick={() => startCompose('Note')}
              className="cr-glass-btn cr-glass-btn--accent"
            >
              + Share a study note
            </button>
            <button
              type="button"
              onClick={() => startCompose('Doubt')}
              className="cr-glass-btn"
            >
              Ask a doubt
            </button>
            <Link to="/create" className="cr-glass-btn">
              Create &amp; contribute →
            </Link>
          </div>
        </header>
      )}

      <div className={embedded ? 'min-w-0' : 'fd-layout'}>
        {/* Main wide editorial reading stream */}
        <div className="fd-main min-w-0">
          {!studyId && (
            <>
              <CommunityFeedback />
              <GuideStrip />
            </>
          )}
          {composingStudy && (
            <Suspense fallback={<p role="status">Opening note composer…</p>}>
              <StudyComposer
                key={composeKind}
                kind={composeKind}
                onClose={closeStudy}
                onSaved={(id) => {
                  setFeedParams(
                    (previous) => {
                      const next = new URLSearchParams(previous)
                      next.delete('compose')
                      next.set('study', String(id))
                      return next
                    },
                    { replace: true },
                  )
                  setReload((n) => n + 1)
                }}
              />
            </Suspense>
          )}
          {studyId && (
            <Suspense fallback={<p role="status">Opening study note…</p>}>
              <StudyPostDetail id={studyId} onClose={closeStudy} />
            </Suspense>
          )}

          <section id="community-section" className="min-w-0 scroll-mt-32">
            <h2 className="sr-only">Community feed</h2>

            <div className="fd-tabbar-wrap">
              <div
                className="fd-tabs"
                role="tablist"
                aria-label="Community feed filters"
              >
                {TABS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    id={`community-tab-${item.id}`}
                    role="tab"
                    aria-controls="community-tab-panel"
                    tabIndex={tab === item.id ? 0 : -1}
                    aria-selected={tab === item.id}
                    onKeyDown={(event) => {
                      const index = TABS.findIndex((t) => t.id === tab)
                      const next =
                        event.key === 'Home'
                          ? 0
                          : event.key === 'End'
                            ? TABS.length - 1
                            : event.key === 'ArrowRight'
                              ? (index + 1) % TABS.length
                              : event.key === 'ArrowLeft'
                                ? (index - 1 + TABS.length) % TABS.length
                                : -1
                      if (next >= 0) {
                        event.preventDefault()
                        setTab(TABS[next].id)
                        document.getElementById(`community-tab-${TABS[next].id}`)?.focus()
                      }
                    }}
                    onClick={() => {
                      setOffset(0)
                      setTab(item.id)
                    }}
                    className={`fd-tab${tab === item.id ? ' is-active' : ''}`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div
              id="community-tab-panel"
              role="tabpanel"
              aria-labelledby={`community-tab-${tab}`}
              tabIndex={0}
              className="mt-5 min-w-0"
            >
              {tab === 'materials' ? (
                <Suspense fallback={<p role="status" className="p-6 text-muted">Loading materials…</p>}>
                  <Materials embedded />
                </Suspense>
              ) : tab === 'mcqs' ? (
                <Suspense fallback={<p role="status" className="p-6 text-muted">Loading community practice…</p>}>
                  <CommunityQuestions embedded />
                </Suspense>
              ) : (
                <>
                  {tab === 'following' && (
                    <section className="fd-banner-card mb-4">
                      <h2 className="fd-banner-title">From people you follow</h2>
                      <p className="mt-1.5 text-[15px] leading-relaxed text-secondary">
                        Study notes, material shares and published discussions, newest first. Linked
                        question content unlocks after you check or show its answer.
                      </p>
                      <div className="mt-3 flex flex-wrap items-center gap-4">
                        <Link
                          to="/creators"
                          className="inline-flex min-h-11 items-center text-sm font-bold text-link hover:underline"
                        >
                          Find creators →
                        </Link>
                      </div>
                      <details className="mt-2 border-t border-hairline pt-2">
                        <summary className="min-h-11 cursor-pointer py-2 text-sm font-bold">
                          Materials from followed creators
                        </summary>
                        <Suspense fallback={<p>Loading followed materials…</p>}>
                          <FollowingMaterials key={reload} embedded />
                        </Suspense>
                      </details>
                    </section>
                  )}

                  {tab === 'questions' && (
                    <div className="fd-banner-card mb-4">
                      <h2 className="fd-banner-title">Questions &amp; Doubts</h2>
                      <p className="mt-1.5 text-[15px] leading-relaxed text-secondary">
                        Discuss a question, explain your reasoning, or help another learner clear a
                        doubt. Answer a question first to reveal its full discussion; active mocks
                        stay protected.
                      </p>
                      <div
                        className="mt-4 flex flex-wrap items-center gap-2"
                        role="group"
                        aria-label="Question discussion filters"
                      >
                        {(
                          [
                            ['all', 'All discussions'],
                            ['doubts', 'Doubts'],
                            ['unanswered', 'Unanswered doubts'],
                          ] as const
                        ).map(([value, label]) => (
                          <button
                            key={value}
                            type="button"
                            aria-pressed={discussion === value}
                            onClick={() => setDiscussionFilter(value)}
                            className={`fd-subpill${discussion === value ? ' is-active' : ''}`}
                          >
                            {label}
                          </button>
                        ))}
                        <Link
                          to="/bank"
                          className="ml-auto inline-flex min-h-11 items-center px-3 text-sm font-bold text-link hover:underline"
                        >
                          Find a question to discuss →
                        </Link>
                      </div>
                      <p className="mt-2.5 text-xs text-muted">
                        Unanswered means no published reply visible to you yet. For an incorrect
                        question or answer key, use Suggest correction on the question page.
                      </p>
                    </div>
                  )}

                  {tab === 'for-you' && (
                    <div className="mb-4">
                      <MaterialDiscovery title="Reading for your next study break" compact />
                    </div>
                  )}

                  <div aria-live="polite" className="fd-stream">
                    {loading && offset === 0 ? (
                      <Card className="p-10 text-center text-base text-muted">
                        Loading discussions…
                      </Card>
                    ) : error && offset === 0 ? (
                      <Card className="p-10 text-center">
                        <p className="text-base font-semibold">
                          The community feed couldn’t load.
                        </p>
                        <button
                          type="button"
                          className="finna-btn finna-btn-quiet mt-3"
                          onClick={() => setReload((n) => n + 1)}
                        >
                          Try again
                        </button>
                      </Card>
                    ) : !feed?.available ? (
                      <Card className="p-10 text-center">
                        <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-community-soft text-lg text-community-dark">
                          ···
                        </div>
                        <p className="mt-4 font-reading text-xl font-semibold text-ink">
                          This space is not open yet
                        </p>
                        <p className="mx-auto mt-2 max-w-md text-[15px] leading-relaxed text-secondary">
                          {feed?.message}
                        </p>
                      </Card>
                    ) : feed.items.length === 0 ? (
                      <EmptyFeed
                        title={
                          tab === 'questions' && discussion === 'unanswered'
                            ? 'No unanswered doubts to show'
                            : 'No posts to show yet'
                        }
                        message={
                          feed?.message ??
                          'Answer a question first; its published explanation or doubt will then appear here.'
                        }
                      />
                    ) : (
                      <>
                        {feed.items.map((item) =>
                          ['study', 'material-share'].includes(item.kind) ? (
                            <StudyCard key={item.id} item={item} />
                          ) : (
                            <Discussion key={item.id} item={item} />
                          ),
                        )}
                        {(feed.has_more || (error && offset > 0)) && (
                          <div className="py-4 text-center">
                            <button
                              type="button"
                              disabled={loading}
                              onClick={() =>
                                error ? setReload((n) => n + 1) : setOffset((value) => value + 20)
                              }
                              className="finna-btn finna-btn-quiet"
                            >
                              {loading
                                ? 'Loading…'
                                : error
                                  ? 'Retry loading discussions'
                                  : 'Load more discussions'}
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </section>
        </div>

        {/* Sticky Right Sidebar for full-width desktop Community workspace */}
        {!embedded && (
          <aside className="fd-aside" aria-label="Community shortcuts and study tools">
            <section className="finna-card fd-compose-panel" aria-labelledby="fd-compose-title">
              <span className="finna-eyebrow text-community-dark">Contribute</span>
              <h2 id="fd-compose-title" className="mt-1">
                Share or ask
              </h2>
              <div className="fd-compose-list mt-3">
                {COMPOSE_ITEMS.map((c) => (
                  <button
                    key={c.type}
                    type="button"
                    onClick={() => startCompose(c.type)}
                    className={`fd-compose-btn fd-accent-${c.accent}`}
                  >
                    <strong>{c.title}</strong>
                    <span>{c.desc}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="finna-card" aria-labelledby="fd-spaces-title">
              <span className="finna-eyebrow">Community spaces</span>
              <h2 id="fd-spaces-title" className="mt-1">
                Explore more
              </h2>
              <div className="finna-shortcut-list mt-2">
                <button
                  type="button"
                  onClick={() => setDiscussionFilter('unanswered')}
                  className="finna-shortcut-link text-left"
                >
                  <strong>Unanswered doubts</strong>
                  <small>Help a fellow student clear a tricky question</small>
                </button>
                <button
                  type="button"
                  onClick={() => setTab('mcqs')}
                  className="finna-shortcut-link text-left"
                >
                  <strong>Community MCQs</strong>
                  <small>Practise reviewed learner-submitted questions</small>
                </button>
                <button
                  type="button"
                  onClick={() => setTab('materials')}
                  className="finna-shortcut-link text-left"
                >
                  <strong>Study materials</strong>
                  <small>Read shared summaries and curated notes</small>
                </button>
                <Link to="/creators" className="finna-shortcut-link">
                  <strong>Creators directory</strong>
                  <small>Follow helpful contributors &amp; mentors</small>
                </Link>
              </div>
            </section>

            <section className="finna-card fd-books-callout" aria-labelledby="fd-books-title">
              <span className="finna-eyebrow">Subject-wise volumes</span>
              <h2 id="fd-books-title" className="mt-1">
                Open a subject book
              </h2>
              <p className="mt-1.5 text-sm leading-relaxed text-secondary">
                Study English, GK/GS, Mathematics, Reasoning, or Mizo across every MPSC exam.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link to="/exams?exam_filter=subjects" className="finna-btn">
                  Subject books →
                </Link>
                <Link to="/library" className="finna-btn finna-btn-quiet">
                  Library
                </Link>
              </div>
            </section>
          </aside>
        )}
      </div>

      {composeType && (
        <div
          className="fixed inset-0 z-[70] grid place-items-center bg-ink/55 p-4"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setComposeType(null)
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="compose-preview-title"
            className="w-full max-w-md rounded-[22px] border border-hairline bg-card p-6 shadow-[0_20px_60px_rgba(0,0,0,.25)]"
          >
            <div className="label text-community-dark">Community contribution</div>
            <h2 id="compose-preview-title" className="mt-2 font-reading text-2xl font-semibold">
              {composeType === 'Post'
                ? 'Share with the community'
                : `Create a ${composeType.toLowerCase()}`}
            </h2>
            <p className="mt-2.5 text-[15px] leading-relaxed text-secondary">
              Choose a question in the bank or an exam, then use <strong>Discuss / Ask a doubt</strong>.
              The question and its source stay linked, and published topics appear right here in
              the feed.
            </p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => setComposeType(null)}
                className="finna-btn finna-btn-quiet"
              >
                Close
              </button>
              <Link
                to="/bank"
                onClick={() => setComposeType(null)}
                className="finna-btn"
              >
                Browse questions →
              </Link>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function EmptyFeed({ message, title }: { message: string; title: string }) {
  return (
    <Card className="p-10 text-center">
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-community-soft text-lg text-community-dark">
        ✳
      </div>
      <p className="mt-4 font-reading text-2xl font-semibold text-ink">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-[15px] leading-relaxed text-secondary">{message}</p>
      <Link to="/bank" className="finna-btn mt-5">
        Explore the question bank →
      </Link>
    </Card>
  )
}

function StudyCard({ item }: { item: CommunityFeedItem }) {
  const isMaterial = item.kind === 'material-share'
  return (
    <article
      className={`fd-post-card ${isMaterial ? 'fd-post--material' : 'fd-post--study'}`}
    >
      <div className="fd-post-head">
        <UserAvatar look={item.avatar} initials={item.author} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-[15px]">
            <ContributorName {...item} />
          </div>
          <div className="mt-0.5 text-xs font-medium text-muted">
            {new Date(item.created_at).toLocaleDateString('en-IN', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}
            {item.topic_label ? ` · ${item.topic_label}` : ''}
          </div>
        </div>
        <span
          className={`fd-kind-pill ${
            isMaterial
              ? 'bg-map-soft text-map-dark'
              : 'bg-learn-soft text-learn-dark'
          }`}
        >
          {isMaterial ? 'Material share' : 'Study note'}
        </span>
      </div>

      <EditMarker post={item} />

      <div className="fd-post-body">
        <CommunityText body={item.body} className="text-[16.5px] leading-[1.7] text-ink" />
      </div>

      {item.material && (
        <Link
          to={'/materials/' + encodeURIComponent(item.material.id)}
          className="fd-material-embed"
        >
          <span className="fd-material-spine" aria-hidden="true" />
          <span className="min-w-0 flex-1">
            <strong className="block text-[15px] font-bold text-ink">{item.material.label}</strong>
            <span className="mt-0.5 block text-xs text-secondary">
              Reviewed {item.material.format} ·{' '}
              {item.material.access === 'pro'
                ? 'Pro access'
                : item.material.access === 'paid-preview'
                  ? 'Preview available'
                  : 'Free to read'}{' '}
              →
            </span>
          </span>
        </Link>
      )}

      <div className="fd-post-foot">
        <span className="fd-helpful-chip">▲ {item.helpful} helpful</span>
        {item.study_reference && (
          <span className="text-xs font-medium text-secondary">
            Linked {item.study_reference.kind}
          </span>
        )}
        <Link to={'/community?study=' + item.id} className="fd-open-link">
          {isMaterial ? 'Open material share →' : 'Open study note →'}
        </Link>
      </div>
    </article>
  )
}

function Discussion({ item }: { item: CommunityFeedItem }) {
  const isDoubt = item.kind === 'doubt'
  return (
    <article
      className={`fd-post-card ${isDoubt ? 'fd-post--doubt' : 'fd-post--explanation'}`}
    >
      <div className="fd-post-head">
        <UserAvatar look={item.avatar} initials={item.author} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-[15px]">
            <ContributorName {...item} />
            <span className="rounded-pill bg-canvas px-2.5 py-0.5 text-xs font-semibold text-secondary">
              {item.author_role}
            </span>
          </div>
          <div className="mt-0.5 text-xs font-medium text-muted">
            {item.source_context ?? 'Question bank discussion'} ·{' '}
            {new Date(item.created_at).toLocaleDateString('en-IN', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}
          </div>
        </div>
        <span
          className={`fd-kind-pill ${
            isDoubt
              ? 'bg-exams-soft text-exams-dark'
              : 'bg-community-soft text-community-dark'
          }`}
        >
          {isDoubt ? 'Doubt' : 'Explanation'}
        </span>
      </div>

      {item.question && (
        <Link
          to={`/bank/${item.question_id}?post=${item.id}#discussion`}
          className="fd-post-question"
        >
          {item.question}
        </Link>
      )}

      <EditMarker post={item} />

      <div className="fd-post-body">
        <CommunityText body={item.body} className="text-[16px] leading-[1.68] text-ink" />
      </div>

      {item.accepted_answer && (
        <div className="fd-accepted-box">
          <div className="text-xs font-bold uppercase tracking-wider text-correct-dark">
            ✓ Accepted reply · community feedback
          </div>
          {item.accepted_answer_edited_at && (
            <p className="mt-1 text-xs text-secondary">
              Edited · {new Date(item.accepted_answer_edited_at).toLocaleDateString('en-IN')}
            </p>
          )}
          <CommunityText
            body={item.accepted_answer}
            className="mt-2 text-[15px] leading-relaxed text-ink"
          />
        </div>
      )}

      <div className="fd-post-foot">
        <span className="fd-helpful-chip">▲ {item.helpful} helpful</span>
        <Link
          to={`/bank/${item.question_id}?post=${item.id}#discussion`}
          className="fd-open-link"
        >
          Open discussion →
        </Link>
      </div>
    </article>
  )
}
