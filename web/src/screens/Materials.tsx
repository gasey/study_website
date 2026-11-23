import { UserAvatar } from '../components/AvatarArt'
import { bookToneFor } from '../components/ConceptBook'
import { MaterialCard } from '../components/MaterialDiscovery'
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom'
import { contentRequest, type MaterialItem, type MaterialRead } from '../lib/materials'
import MaterialBody from '../components/MaterialBody'
import { SourceQuestionText } from '../components/SourceQuestionText'

export const CONTENT_BUTTON =
  'inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold disabled:opacity-40'
export const CONTENT_INPUT =
  'min-h-11 min-w-0 w-full rounded-[6px] border border-[#CFC5B2] bg-[#FBF8F1] px-3 py-2 text-sm'

const QUICK_TAGS: ReadonlyArray<{ label: string; value: string }> = [
  { label: 'All topics', value: '' },
  { label: 'SSC PYQ', value: 'SSC PYQ' },
  { label: 'Polity', value: 'Polity' },
  { label: 'History', value: 'History' },
  { label: 'Geography', value: 'Geography' },
  { label: 'Economy', value: 'Economy' },
  { label: 'Science', value: 'Science' },
  { label: 'General Knowledge', value: 'General Knowledge' },
]

const ACCESS_OPTIONS: ReadonlyArray<{ label: string; value: string }> = [
  { label: 'All', value: 'all' },
  { label: 'Free', value: 'free' },
  { label: 'Pro', value: 'pro' },
  { label: 'Previews', value: 'paid-preview' },
]

export default function Materials({
  embedded = false,
  savedOnly = false,
}: {
  embedded?: boolean
  savedOnly?: boolean
} = {}) {
  const Heading = embedded ? 'h2' : 'h1'
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState<{ items: MaterialItem[]; total: number } | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)

  const q = params.get('q') || ''
  const tag = params.get('tag') || ''
  const access = params.get('access') || 'all'
  const sort = params.get('sort') || 'recent'
  const offset = Math.max(0, Number(params.get('offset')) || 0)
  const saved = savedOnly || params.get('saved') === 'true'
  const collectionId = params.get('collection_id') || ''
  const subjectId = params.get('subject_id') || ''

  useEffect(() => {
    let live = true
    setData(null)
    setError('')
    const timer = window.setTimeout(() => {
      const qs = new URLSearchParams({
        q,
        access,
        sort,
        offset: String(offset),
        saved: String(saved),
        ...(tag ? { tag } : {}),
        ...(collectionId ? { collection_id: collectionId } : {}),
        ...(subjectId ? { subject_id: subjectId } : {}),
      })
      contentRequest<typeof data>('/materials?' + qs.toString())
        .then(r => {
          if (live) setData(r)
        })
        .catch(e => {
          if (live) setError(e.message)
        })
    }, 200)
    return () => {
      live = false
      window.clearTimeout(timer)
    }
  }, [q, tag, access, sort, offset, saved, collectionId, subjectId, retry])

  function filter(key: string, value: string) {
    setParams(
      p => {
        const next = new URLSearchParams(p)
        if (!value || (key === 'access' && value === 'all') || (key === 'saved' && value === 'false')) {
          next.delete(key)
        } else {
          next.set(key, value)
        }
        if (key !== 'offset') next.delete('offset')
        return next
      },
      { replace: true },
    )
  }

  function resetAllFilters() {
    setParams(
      p => {
        const next = new URLSearchParams(p)
        for (const k of ['q', 'tag', 'access', 'sort', 'saved', 'collection_id', 'subject_id', 'offset']) {
          next.delete(k)
        }
        return next
      },
      { replace: true },
    )
  }

  const hasActiveFilters = Boolean(q || tag || access !== 'all' || (!savedOnly && saved) || collectionId || subjectId)

  return (
    <div className={embedded ? 'mt-embedded' : 'mt-shell'}>
      {embedded ? (
        <div className="mt-embedded-head">
          <div>
            <div className="mt-eyebrow">Editorial &amp; Community Library</div>
            <Heading className="mt-embedded-title">
              {savedOnly ? 'Saved study materials' : 'Study materials & revision sheets'}
            </Heading>
            <p className="mt-embedded-sub">
              {savedOnly
                ? 'Notes and revision guides you bookmarked for later.'
                : 'Editorial SSC PYQ revision sheets and learner-contributed notes. For structured concept books, open '}
              {!savedOnly && (
                <>
                  <Link to="/guides" className="mt-inline-link">
                    Guides
                  </Link>
                  .
                </>
              )}
            </p>
          </div>
          <div className="mt-head-actions">
            <Link to="/creators" className="mt-pill-btn">
              Find creators →
            </Link>
            <Link to="/studio" className="mt-pill-btn is-primary">
              Creator studio →
            </Link>
          </div>
        </div>
      ) : (
        <header className="av-hero mt-hero">
          <div className="av-hero-copy">
            <div className="mt-eyebrow">Editorial &amp; Community Reading Room</div>
            <Heading>{savedOnly ? 'Saved study materials' : 'Study Materials & Revision Notes'}</Heading>
            <p>
              {savedOnly
                ? 'Notes and revision guides you bookmarked for quick review.'
                : 'High-yield SSC PYQ revision sheets published by the Finna desk alongside community-authored notes. Looking for long-form concept books? Open '}
              {!savedOnly && (
                <>
                  <Link to="/guides" className="mt-inline-link">
                    Guides
                  </Link>
                  .
                </>
              )}
            </p>
            {data && (
              <div className="mt-hero-pills">
                <span className="mt-hero-stat">
                  <strong>{data.total}</strong> {data.total === 1 ? 'published sheet' : 'published sheets'}
                </span>
                <span className="mt-hero-stat">SSC CGL · CHSL · MTS · CPO · JE · MPSC GS</span>
              </div>
            )}
          </div>
          <div className="av-hero-actions">
            <Link to="/creators" className="mt-pill-btn">
              Find creators →
            </Link>
            <Link to="/studio" className="mt-pill-btn is-primary">
              Open creator studio →
            </Link>
          </div>
        </header>
      )}

      <section className="mt-toolbar" aria-label="Filter study materials">
        <div className="mt-toolbar-row">
          <div className="mt-search-wrap">
            <span className="mt-search-icon" aria-hidden="true">
              ⌕
            </span>
            <input
              aria-label="Search materials"
              type="search"
              maxLength={160}
              placeholder="Search Polity, History, Biology, Static GK, or notes…"
              value={q}
              onChange={e => filter('q', e.target.value)}
              className="mt-search-input"
            />
          </div>

          <div className="mt-seg-group" role="group" aria-label="Access filter">
            {ACCESS_OPTIONS.map(opt => (
              <button
                key={opt.value}
                type="button"
                aria-pressed={access === opt.value}
                onClick={() => filter('access', opt.value)}
                className={`mt-seg-btn${access === opt.value ? ' is-on' : ''}`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <div className="mt-seg-group" role="group" aria-label="Sort materials">
            <button
              type="button"
              aria-pressed={sort === 'recent'}
              onClick={() => filter('sort', 'recent')}
              className={`mt-seg-btn${sort === 'recent' ? ' is-on' : ''}`}
            >
              Recent
            </button>
            <button
              type="button"
              aria-pressed={sort === 'helpful'}
              onClick={() => filter('sort', 'helpful')}
              className={`mt-seg-btn${sort === 'helpful' ? ' is-on' : ''}`}
            >
              ▲ Top voted
            </button>
          </div>

          {!savedOnly && (
            <button
              type="button"
              aria-pressed={saved}
              onClick={() => filter('saved', String(!saved))}
              className={`mt-saved-toggle${saved ? ' is-on' : ''}`}
            >
              {saved ? '★ Saved' : '☆ Saved'}
            </button>
          )}
        </div>

        <div className="mt-tag-rail" role="group" aria-label="Filter by topic">
          {QUICK_TAGS.map(item => (
            <button
              key={item.label}
              type="button"
              aria-pressed={tag === item.value}
              onClick={() => filter('tag', item.value)}
              className={`mt-topic-chip${tag === item.value ? ' is-on' : ''}`}
            >
              {item.label}
            </button>
          ))}
          {hasActiveFilters && (
            <button type="button" onClick={resetAllFilters} className="mt-reset-chip">
              Clear filters ✕
            </button>
          )}
        </div>
      </section>

      {(collectionId || subjectId) && (
        <div className="mt-context-bar">
          <span>
            Showing materials linked to this{' '}
            {collectionId && subjectId ? 'exam and subject' : collectionId ? 'exam' : 'subject'}.
          </span>
          <Link
            to={
              collectionId
                ? '/exams/' + encodeURIComponent(collectionId)
                : '/library/subjects/' + encodeURIComponent(subjectId)
            }
            className="mt-inline-link"
          >
            Back to {collectionId ? 'exam' : 'subject'} →
          </Link>
          <button
            type="button"
            onClick={() =>
              setParams(p => {
                const n = new URLSearchParams(p)
                n.delete('collection_id')
                n.delete('subject_id')
                n.delete('offset')
                return n
              })
            }
            className="mt-inline-link"
          >
            Browse all materials
          </button>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-alert-box is-error">
          {error}{' '}
          <button type="button" onClick={() => setRetry(n => n + 1)} className="mt-inline-link">
            Retry
          </button>
        </p>
      )}

      {!data && !error && (
        <div role="status" className={`mt-grid${embedded ? ' is-embedded' : ''}`} aria-label="Loading materials">
          {[0, 1, 2, 3, 4, 5].map(i => (
            <div key={i} className="mt-skeleton-card" aria-hidden="true" />
          ))}
        </div>
      )}

      {data && (
        <>
          <div className={`mt-grid${embedded ? ' is-embedded' : ''}`}>
            {data.items.map(m => (
              <MaterialCard key={m.id} item={m} />
            ))}
          </div>

          {data.items.length === 0 && (
            <div className="mt-empty-box">
              <p>No published materials match these filters.</p>
              {hasActiveFilters && (
                <button type="button" onClick={resetAllFilters} className="mt-pill-btn">
                  Reset filters
                </button>
              )}
            </div>
          )}

          {data.total > 0 && (
            <nav aria-label="Material pages" className="mt-pager">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => filter('offset', String(Math.max(0, offset - 12)))}
                className="mt-pill-btn"
              >
                ← Previous
              </button>
              <span className="mt-pager-count">
                Showing {offset + 1}–{Math.min(offset + data.items.length, data.total)} of {data.total} materials
              </span>
              <button
                type="button"
                disabled={offset + 12 >= data.total}
                onClick={() => filter('offset', String(offset + 12))}
                className="mt-pill-btn"
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  )
}

export function MaterialReader() {
  const { id = '' } = useParams()
  const [params] = useSearchParams()
  return (
    <MaterialReaderContent
      key={id + params.get('preview')}
      id={id}
      preview={params.get('preview') === 'true'}
    />
  )
}

export function MaterialReaderContent({
  id,
  preview = false,
  embedded = false,
}: {
  id: string
  preview?: boolean
  embedded?: boolean
}) {
  const location = useLocation()
  const from = location.state?.communityReturn
  const returnTo = typeof from === 'string' && /^\/(feed|community)(?:\?|$)/.test(from) ? from : null
  const [data, setData] = useState<MaterialRead | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [reportOpen, setReportOpen] = useState(false)
  const [report, setReport] = useState({ reason: 'incorrect', note: '' })

  async function load() {
    setData(
      await contentRequest<MaterialRead>(
        '/materials/' + encodeURIComponent(id) + (preview ? '?preview=true' : ''),
      ),
    )
  }

  useEffect(() => {
    let live = true
    setData(null)
    setError('')
    contentRequest<MaterialRead>(
      '/materials/' + encodeURIComponent(id) + (preview ? '?preview=true' : ''),
    )
      .then(r => {
        if (live) setData(r)
      })
      .catch(e => {
        if (live) setError(e.message)
      })
    return () => {
      live = false
    }
  }, [id, preview])

  async function react(body: Record<string, boolean>) {
    setBusy(true)
    setError('')
    try {
      await contentRequest('/materials/' + id + '/reaction', body)
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function sendReport(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await contentRequest('/materials/' + id + '/report', report)
      setNotice('Report saved for the CMS owner to review.')
      setReportOpen(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const doc = data?.document
  const Frame = embedded ? 'div' : 'main'
  const tone = doc
    ? bookToneFor([doc.subject_id || '', ...(doc.tags || []), doc.title].join(' '))
    : 'teal'
  const isOfficial = data?.author_id === 'team'

  return (
    <Frame className={embedded ? 'mt-reader-embedded' : 'mt-reader-shell'}>
      {!embedded && (
        <Link to={returnTo || '/materials'} className="mt-back-link">
          {returnTo ? '← Community' : '← All study materials'}
        </Link>
      )}

      {error && (
        <p role="alert" className="mt-alert-box is-error">
          {error}{' '}
          <Link to="/login" className="mt-inline-link">
            Sign in
          </Link>
        </p>
      )}
      {notice && (
        <p role="status" className="mt-alert-box is-ok">
          {notice}
        </p>
      )}
      {!data && !error && <p className="mt-status-msg">Loading study sheet…</p>}

      {data && doc && (
        <>
          <header className={`mt-reader-head mt-tone-${tone}`}>
            <div className="mt-reader-head-band" aria-hidden="true" />
            <div className="mt-reader-head-inner">
              <div className="mt-reader-tags">
                <span className="mt-kind-pill">{doc.kind}</span>
                {isOfficial && <span className="mt-official-pill">Editorial Desk</span>}
                {doc.tags.map((t, i) => (
                  <span key={i} className="mt-tag-chip">
                    {t}
                  </span>
                ))}
              </div>
              <h1 className="mt-reader-title">{doc.title}</h1>
              <p className="mt-reader-summary">{doc.summary}</p>

              <div className="mt-reader-bar">
                <span className="mt-reader-author">
                  <UserAvatar look={data.avatar} initials={data.author} size={30} />
                  <span>
                    {data.creator_public ? (
                      <Link
                        to={'/creators/' + encodeURIComponent(data.author_id)}
                        className="mt-author-link"
                      >
                        {data.author}
                      </Link>
                    ) : (
                      <strong>{data.author}</strong>
                    )}
                    <span className="mt-reader-meta-sep">
                      {' '}
                      · {new Date(data.published_at).toLocaleDateString('en-IN')} · Rev {data.published_revision}
                    </span>
                  </span>
                </span>

                <div className="mt-reader-actions">
                  <button
                    type="button"
                    disabled={busy || !data.can_read || data.is_author}
                    aria-pressed={data.reaction.helpful}
                    onClick={() => void react({ helpful: !data.reaction.helpful })}
                    className={`mt-pill-btn${data.reaction.helpful ? ' is-helpful' : ''}`}
                  >
                    ▲ Helpful · {data.helpful}
                  </button>
                  <button
                    type="button"
                    disabled={busy || !data.can_read || data.is_author}
                    aria-pressed={data.reaction.studied}
                    onClick={() => void react({ studied: !data.reaction.studied })}
                    className={`mt-pill-btn${data.reaction.studied ? ' is-studied' : ''}`}
                  >
                    {data.reaction.studied ? '✓ Studied' : 'Mark studied'}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    aria-pressed={data.saved}
                    onClick={() => void react({ saved: !data.saved })}
                    className={`mt-pill-btn${data.saved ? ' is-saved' : ''}`}
                  >
                    {data.saved ? '★ Saved' : '☆ Save'}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="mt-reader-layout">
            <article className="mt-paper-sheet">
              {data.can_read ? (
                <MaterialBody blocks={doc.blocks} />
              ) : (
                <>
                  <div className="mt-preview-excerpt">
                    <div className="mt-eyebrow">Public preview</div>
                    <p className="mt-body-p">
                      <SourceQuestionText text={doc.preview} />
                    </p>
                  </div>
                  <section className="mt-locked-card">
                    <div className="mt-eyebrow">
                      {doc.access === 'pro' ? 'Pro member lesson' : 'Paid-content demonstration'}
                    </div>
                    <h2 className="mt-locked-title">
                      {doc.access === 'pro' ? 'Continue with Pro' : 'A preview before you choose'}
                    </h2>
                    <p className="mt-locked-copy">
                      {doc.access === 'pro'
                        ? 'The full lesson is available to Pro members. Your earned Pro access also applies.'
                        : 'This sample shows how an individual paid lesson could look. Checkout and creator payouts are not enabled; no purchase can be made here.'}
                    </p>
                    {doc.access === 'pro' ? (
                      <Link to="/plans" className="mt-pill-btn is-primary">
                        View membership options →
                      </Link>
                    ) : (
                      <p className="mt-locked-price">
                        {doc.price_paise
                          ? 'Example price ₹' + (doc.price_paise / 100).toLocaleString('en-IN')
                          : 'Price to be set'}{' '}
                        · demo only
                      </p>
                    )}
                  </section>
                </>
              )}
            </article>

            <aside className="mt-reader-aside">
              <div className="mt-aside-card">
                <h2 className="mt-aside-title">About this study sheet</h2>
                <p className="mt-aside-copy">
                  {isOfficial
                    ? 'Compiled by the Finna editorial desk from authentic SSC previous-year papers for rapid subject revision. Cross-check exact statutory updates where applicable.'
                    : 'Community-authored content is distinct from official exam sources. Each question includes its original paper and answer source. Upvotes signal usefulness, not verified correctness.'}
                </p>
                <p className="mt-aside-note">
                  Votes and “studied” marks help you track revision and do not award XP or redeemable points.
                </p>
                <div className="mt-aside-links">
                  {doc.collection_id && (
                    <Link to={'/exams/' + doc.collection_id} className="mt-inline-link">
                      Related exam →
                    </Link>
                  )}
                  {doc.subject_id && (
                    <Link
                      to={'/library/subjects/' + encodeURIComponent(doc.subject_id)}
                      className="mt-inline-link"
                    >
                      Explore subject in Library →
                    </Link>
                  )}
                  {data.is_author && (
                    <Link to={'/studio/' + id} className="mt-inline-link">
                      Edit draft →
                    </Link>
                  )}
                  <button
                    type="button"
                    onClick={() => setReportOpen(v => !v)}
                    className="mt-report-trigger"
                  >
                    {reportOpen ? 'Close report form' : 'Report an issue'}
                  </button>
                </div>
              </div>

              {reportOpen && (
                <form onSubmit={sendReport} className="mt-aside-card mt-report-form">
                  <label className="mt-field-label">
                    Report reason
                    <select
                      value={report.reason}
                      onChange={e => setReport({ ...report, reason: e.target.value })}
                      className="mt-field-control"
                    >
                      {[
                        ['incorrect', 'Incorrect content'],
                        ['spam', 'Spam'],
                        ['copyright', 'Copyright concern'],
                        ['other', 'Other'],
                      ].map(([v, l]) => (
                        <option key={v} value={v}>
                          {l}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="mt-field-label">
                    What should be reviewed?
                    <textarea
                      required
                      minLength={10}
                      maxLength={2000}
                      rows={4}
                      value={report.note}
                      onChange={e => setReport({ ...report, note: e.target.value })}
                      className="mt-field-control"
                    />
                  </label>
                  <button type="submit" disabled={busy} className="mt-pill-btn is-primary">
                    Send report
                  </button>
                </form>
              )}
            </aside>
          </div>
        </>
      )}
    </Frame>
  )
}
