import { UserAvatar } from './AvatarArt'
import { bookToneFor } from './ConceptBook'
import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { contentRequest, type MaterialItem } from '../lib/materials'

export function materialLink(id: string) {
  return '/materials/' + encodeURIComponent(id) + (id === 'cms-paid-demo' ? '?preview=true' : '')
}

function accessLabel(access: string) {
  if (access === 'paid-preview') return 'Paid demo'
  if (access === 'pro') return 'Pro'
  return 'Free'
}

export function MaterialCard({ item: m }: { item: MaterialItem }) {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  params.set('read_material', m.id)
  if (m.id === 'cms-paid-demo') params.set('material_preview', 'true')
  else params.delete('material_preview')
  const readerURL = location.pathname + '?' + params.toString() + location.hash

  const toneSeed = [m.payload.subject_id || '', ...(m.payload.tags || []), m.payload.title].join(' ')
  const tone = bookToneFor(toneSeed)
  const isOfficial = m.author_id === 'team'

  return (
    <article className={`mt-card mt-tone-${tone}`}>
      <div className="mt-card-band" aria-hidden="true" />
      <div className="mt-card-body">
        <div className="mt-card-meta">
          <span className="mt-kind-pill">{m.payload.kind}</span>
          <span className={`mt-access-pill is-${m.payload.access}`}>
            {accessLabel(m.payload.access)}
          </span>
          {isOfficial && <span className="mt-official-pill">Editorial</span>}
        </div>

        <h3 className="mt-card-title">
          <Link
            to={readerURL}
            state={{
              ...location.state,
              materialReaderFrom: location.pathname + location.search + location.hash,
            }}
            preventScrollReset
          >
            {m.payload.title}
          </Link>
        </h3>

        <p className="mt-card-summary">{m.payload.summary}</p>

        {m.payload.tags.length > 0 && (
          <div className="mt-card-tags">
            {m.payload.tags.slice(0, 4).map(t => (
              <span key={t} className="mt-tag-chip">
                {t}
              </span>
            ))}
          </div>
        )}

        <div className="mt-card-foot">
          <span className="mt-card-author">
            <UserAvatar look={m.avatar} initials={m.author} size={24} />
            {m.creator_public ? (
              <Link to={'/creators/' + encodeURIComponent(m.author_id)} className="mt-author-link">
                {m.author}
              </Link>
            ) : (
              <span>{m.author}</span>
            )}
          </span>
          <span className="mt-card-stats">
            <span title="Helpful votes">▲ {m.helpful}</span>
            <span aria-hidden="true">·</span>
            <span title="Learners studied">{m.studied} studied</span>
          </span>
        </div>
      </div>
    </article>
  )
}

/** Only approved publication metadata. No lesson bodies or question-bank scans. */
export default function MaterialDiscovery({
  collectionId,
  subjectId,
  title = 'Study materials & revision sheets',
  compact = false,
  hideEmpty = false,
}: {
  collectionId?: string
  subjectId?: string
  title?: string
  compact?: boolean
  hideEmpty?: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<{ items: MaterialItem[]; total: number } | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const context = new URLSearchParams()
  if (collectionId) context.set('collection_id', collectionId)
  if (subjectId) context.set('subject_id', subjectId)
  const query = context.toString()
  const key = query + ':' + retry + ':' + expanded + ':' + offset
  const [loadedKey, setLoadedKey] = useState('')

  useEffect(() => {
    let live = true
    setError('')
    setData(null)
    contentRequest<{ items: MaterialItem[]; total: number }>(
      '/materials?' +
        query +
        (query ? '&' : '') +
        'sort=helpful&limit=' +
        (expanded ? 12 : 3) +
        '&offset=' +
        offset,
    )
      .then(r => {
        if (live) {
          setData(r)
          setLoadedKey(key)
        }
      })
      .catch(e => {
        if (live) {
          setError(e.message)
          setLoadedKey(key)
        }
      })
    return () => {
      live = false
    }
  }, [query, key])

  const current = loadedKey === key
  const items = current ? data?.items : null

  if (hideEmpty && ((!current && !error) || (current && data?.total === 0))) return null

  return (
    <section aria-label={title} className="mt-discovery">
      <div className="mt-discovery-head">
        <div>
          <div className="mt-eyebrow">Editorial &amp; Community Notes</div>
          <h2 className="mt-discovery-title">{title}</h2>
          <p className="mt-discovery-sub">
            Published revision guides and notes · helpful votes reflect reader feedback.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setExpanded(v => !v)
            setOffset(0)
          }}
          aria-expanded={expanded}
          className="mt-pill-btn"
        >
          {expanded ? 'Show highlights' : 'View all here'} →
        </button>
      </div>

      {(!current || (!data && !error)) && (
        <p role="status" className="mt-status-msg">
          Loading study materials…
        </p>
      )}
      {current && error && (
        <p role="alert" className="mt-status-msg">
          Materials couldn’t load.{' '}
          <button type="button" onClick={() => setRetry(n => n + 1)} className="mt-inline-link">
            Try again
          </button>
        </p>
      )}
      {items && items.length > 0 && (
        <div className={`mt-grid${compact ? ' is-compact' : ''}`}>
          {items.map(m => (
            <MaterialCard key={m.id} item={m} />
          ))}
        </div>
      )}
      {expanded && current && data && data.total > 12 && (
        <nav aria-label="Related material pages" className="mt-pager">
          <button
            type="button"
            disabled={!offset}
            onClick={() => setOffset(n => Math.max(0, n - 12))}
            className="mt-pill-btn"
          >
            ← Previous
          </button>
          <span className="mt-pager-count">
            {offset + 1}–{Math.min(offset + 12, data.total)} of {data.total}
          </span>
          <button
            type="button"
            disabled={offset + 12 >= data.total}
            onClick={() => setOffset(n => n + 12)}
            className="mt-pill-btn"
          >
            Next →
          </button>
        </nav>
      )}
      {items?.length === 0 && (
        <div className="mt-empty-box">
          <p>
            {collectionId
              ? 'No materials have been published for this exam yet.'
              : subjectId
                ? 'No materials have been published for this subject yet.'
                : 'No materials have been published yet.'}
          </p>
          <Link to={'/studio/new' + (query ? '?' + query : '')} className="mt-inline-link">
            Create a study note →
          </Link>
        </div>
      )}
    </section>
  )
}
