import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getCommunityFeed,
  type CommunityFeedItem,
  type CommunityFeedResponse,
} from '../lib/api'
import { UserAvatar } from './AvatarArt'
import { ContributorName } from './ContributorStanding'
import CommunityText from './CommunityText'

type FeedFilter = 'for-you' | 'doubts' | 'unanswered' | 'following'

const COMPACT_TABS: { id: FeedFilter; label: string }[] = [
  { id: 'for-you', label: 'For you' },
  { id: 'doubts', label: 'Doubts' },
  { id: 'unanswered', label: 'Needs help' },
]

const FULL_TABS: { id: FeedFilter; label: string }[] = [
  { id: 'for-you', label: 'For you' },
  { id: 'following', label: 'Following' },
  { id: 'doubts', label: 'Doubts' },
  { id: 'unanswered', label: 'Needs help' },
]

function kindMeta(kind: CommunityFeedItem['kind']): { label: string; cls: string } {
  switch (kind) {
    case 'doubt':
      return { label: 'Doubt', cls: 'bg-exams-soft text-exams-dark' }
    case 'study':
      return { label: 'Study note', cls: 'bg-learn-soft text-learn-dark' }
    case 'material-share':
      return { label: 'Shared material', cls: 'bg-map-soft text-map-dark' }
    default:
      return { label: 'Explanation', cls: 'bg-community-soft text-community-dark' }
  }
}

function FeedItemCard({
  item,
  compact,
}: {
  item: CommunityFeedItem
  compact: boolean
}) {
  const isStudy = item.kind === 'study' || item.kind === 'material-share'
  const meta = kindMeta(item.kind)
  const targetUrl = isStudy
    ? `/community?study=${item.id}`
    : item.question_id
      ? `/bank/${item.question_id}?post=${item.id}#discussion`
      : '/community'

  return (
    <article className={`finna-feed-card${compact ? ' is-compact' : ''}`}>
      <div className="finna-feed-card-head">
        <UserAvatar look={item.avatar} initials={item.author} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5 text-sm">
            <ContributorName {...item} />
            <span className="text-xs text-muted">
              · {new Date(item.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
            </span>
          </div>
          {item.source_context && (
            <div className="truncate text-xs text-secondary">{item.source_context}</div>
          )}
        </div>
        <span className={`finna-feed-kind ${meta.cls}`}>{meta.label}</span>
      </div>

      {isStudy ? (
        <>
          {item.topic_label && (
            <p className="mt-2 font-mono text-xs text-secondary">{item.topic_label}</p>
          )}
          <div className={compact ? 'finna-feed-clamp mt-2' : 'mt-2.5'}>
            <CommunityText body={item.body} className="text-sm leading-relaxed text-ink" />
          </div>
          {item.material && (
            <Link
              to={'/materials/' + encodeURIComponent(item.material.id)}
              className="mt-2.5 block rounded-xl border border-hairline bg-paper px-3.5 py-2.5 text-xs font-semibold text-link hover:border-practice"
            >
              {item.material.label}
              <span className="mt-0.5 block font-normal text-secondary">
                Reviewed {item.material.format} →
              </span>
            </Link>
          )}
        </>
      ) : (
        <>
          {item.question && (
            <Link
              to={targetUrl}
              className="mt-2.5 block font-reading text-[17.5px] font-semibold leading-snug text-ink hover:text-link"
            >
              {item.question}
            </Link>
          )}
          <div className={compact ? 'finna-feed-clamp mt-1.5' : 'mt-2'}>
            <CommunityText body={item.body} className="text-[15px] leading-relaxed text-secondary" />
          </div>
          {item.accepted_answer && (
            <div className="mt-2.5 rounded-xl bg-correct-soft px-3 py-2 text-xs text-correct-dark">
              <strong className="font-semibold">✓ Accepted reply</strong>
              {!compact && (
                <CommunityText
                  body={item.accepted_answer}
                  className="mt-1 text-xs leading-relaxed text-ink"
                />
              )}
            </div>
          )}
        </>
      )}

      <div className="finna-feed-card-foot">
        <span className="text-xs font-semibold text-secondary">▲ {item.helpful} helpful</span>
        <Link to={targetUrl} className="text-xs font-bold text-link hover:underline">
          {isStudy ? 'Open note →' : 'Open discussion →'}
        </Link>
      </div>
    </article>
  )
}

export default function HomeFeedPreview({
  mode = 'compact',
  onExpandToFeedTab,
}: {
  mode?: 'compact' | 'full'
  onExpandToFeedTab?: () => void
}) {
  const compact = mode === 'compact'
  const tabs = compact ? COMPACT_TABS : FULL_TABS
  const [filter, setFilter] = useState<FeedFilter>('for-you')
  const [offset, setOffset] = useState(0)
  const [result, setResult] = useState<CommunityFeedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [reload, setReload] = useState(0)
  const generation = useRef(0)

  useEffect(() => {
    const refresh = () => {
      ++generation.current
      setOffset(0)
      setResult(null)
      setReload((n) => n + 1)
    }
    window.addEventListener('ism-auth-change', refresh)
    window.addEventListener('ism-community-change', refresh)
    return () => {
      window.removeEventListener('ism-auth-change', refresh)
      window.removeEventListener('ism-community-change', refresh)
    }
  }, [])

  useEffect(() => {
    let active = true
    const run = ++generation.current
    if (offset === 0) setResult(null)
    setLoading(true)
    setError(false)

    const apiTab: CommunityFeedResponse['tab'] =
      filter === 'following'
        ? 'following'
        : filter === 'doubts' || filter === 'unanswered'
          ? 'questions'
          : 'for-you'
    const discussion: 'all' | 'doubts' | 'unanswered' =
      filter === 'doubts' ? 'doubts' : filter === 'unanswered' ? 'unanswered' : 'all'

    getCommunityFeed(apiTab, offset, discussion)
      .then((res) => {
        if (!active || run !== generation.current) return
        setResult((prev) =>
          offset === 0 || !prev
            ? res
            : {
                ...res,
                items: [
                  ...prev.items,
                  ...res.items.filter((item) => !prev.items.some((old) => old.id === item.id)),
                ],
              },
        )
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
  }, [filter, offset, reload])

  const visibleItems = compact ? (result?.items || []).slice(0, 3) : result?.items || []

  return (
    <section
      className={`finna-card finna-home-feed${compact ? ' is-compact' : ' is-full'}`}
      aria-labelledby="home-feed-title"
    >
      <div className="finna-section-top">
        <div>
          <span className="finna-eyebrow text-community-dark">Community pulse</span>
          <h2 id="home-feed-title" className="mt-0.5">
            {compact ? 'Latest from learners' : 'Community feed'}
          </h2>
        </div>
        <Link to="/community">Open full feed →</Link>
      </div>

      {/* Quick composer & filter bar */}
      <div className="finna-feed-toolbar">
        <div className="finna-feed-pills" role="tablist" aria-label="Home community feed filter">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={filter === t.id}
              onClick={() => {
                setOffset(0)
                setFilter(t.id)
              }}
              className={`finna-feed-pill${filter === t.id ? ' is-active' : ''}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="finna-feed-quick-actions">
          <Link to="/community?tab=questions" className="finna-feed-action-chip">
            Ask a doubt
          </Link>
          <Link to="/community?compose=study" className="finna-feed-action-chip">
            Share a note
          </Link>
          <Link to="/create/new?kind=new_question" className="finna-feed-action-chip">
            Submit MCQ
          </Link>
        </div>
      </div>

      <div className="finna-feed-list" aria-live="polite">
        {loading && offset === 0 ? (
          <div className="finna-feed-empty">
            <p className="text-sm text-secondary">Loading recent doubts and study notes…</p>
          </div>
        ) : error && offset === 0 ? (
          <div className="finna-feed-empty">
            <p className="text-sm text-secondary">Couldn’t load the community feed right now.</p>
            <button
              type="button"
              onClick={() => setReload((n) => n + 1)}
              className="mt-2 min-h-10 rounded-xl border border-hairline px-3.5 text-xs font-bold text-link"
            >
              Try again
            </button>
          </div>
        ) : !result?.available ? (
          <div className="finna-feed-empty">
            <p className="text-sm font-semibold text-ink">Community feed is quiet right now</p>
            <p className="mt-1 text-xs leading-relaxed text-secondary">
              {result?.message ||
                'Discuss any past-paper question after answering it, or share a study note with other learners.'}
            </p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              <Link to="/bank" className="finna-btn">
                Browse questions →
              </Link>
              <Link to="/guides" className="finna-btn finna-btn-quiet">
                Concept guides
              </Link>
            </div>
          </div>
        ) : visibleItems.length === 0 ? (
          <div className="finna-feed-empty">
            <p className="text-sm font-semibold text-ink">
              {filter === 'unanswered'
                ? 'No unanswered doubts right now'
                : filter === 'following'
                  ? 'No posts from followed creators yet'
                  : 'No posts to show yet'}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-secondary">
              {result.message ||
                'Answer a question first; its published explanation or doubt will appear here.'}
            </p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              <Link to="/bank" className="finna-btn finna-btn-quiet">
                Explore question bank →
              </Link>
              {filter === 'following' && (
                <Link to="/creators" className="finna-btn finna-btn-quiet">
                  Find creators →
                </Link>
              )}
            </div>
          </div>
        ) : (
          <>
            {visibleItems.map((item) => (
              <FeedItemCard key={item.id} item={item} compact={compact} />
            ))}
          </>
        )}
      </div>

      {/* Footer actions */}
      <div className="finna-feed-footer">
        {compact ? (
          <>
            {onExpandToFeedTab && (result?.items.length || 0) > 0 && (
              <button
                type="button"
                onClick={onExpandToFeedTab}
                className="finna-btn finna-btn-quiet"
              >
                Read more posts here
              </button>
            )}
            <Link to="/community?tab=mcqs" className="finna-btn finna-btn-quiet">
              Community MCQs
            </Link>
            <Link to="/guides" className="finna-btn finna-btn-quiet">
              Concept guides
            </Link>
          </>
        ) : (
          <>
            {(result?.has_more || (error && offset > 0)) && (
              <button
                type="button"
                disabled={loading}
                onClick={() => (error ? setReload((n) => n + 1) : setOffset((v) => v + 20))}
                className="finna-btn finna-btn-quiet"
              >
                {loading ? 'Loading…' : error ? 'Retry loading more' : 'Load more posts'}
              </button>
            )}
            <Link to="/community?tab=mcqs" className="finna-btn finna-btn-quiet">
              Community MCQs →
            </Link>
            <Link to="/community?tab=materials" className="finna-btn finna-btn-quiet">
              Study materials →
            </Link>
          </>
        )}
      </div>
    </section>
  )
}
