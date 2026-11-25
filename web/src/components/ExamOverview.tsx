import {paperBrowseLink} from '../lib/browsePosition'
import { useMemo, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { CollectionDetail } from '../lib/api'
import { examOverviewGroups, type OverviewPaper } from '../lib/examOverview'
import { examPresentation } from '../lib/examPresentation'
import { paperIdentity } from '../lib/paperIdentity'
import { withoutBooklet } from '../lib/sourceBooklets'
import { bookletLabel } from '../lib/mcsBooklets'
import '../styles/exam-experience.css'
import '../styles/exam-overview.css'

const count = (n: number) => n.toLocaleString('en-IN')

/** Paper summaries lead into the existing Browse, Practice and source-paper views. */
export default function ExamOverview({ title, collections, loading = false, error, onRetry, navigation, children, viewKey = 'overview', headerAction, description, presentationId }: {
  title: string
  collections: CollectionDetail[]
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  navigation?: ReactNode
  children?: ReactNode
  viewKey?: string
  headerAction?: ReactNode
  description?: string
  presentationId?: string
}) {
  const [params, setParams] = useSearchParams()
  const order = params.get('paper_sort') === 'oldest' ? 'oldest' : 'newest'
  const groups = useMemo(() => examOverviewGroups(collections, order), [collections, order])
  const papers = groups.flatMap(g => g.papers)
  const stats = [
    [papers.length, 'paper groups'],
    [collections.reduce((n, c) => n + c.questions, 0), 'source questions'],
    [collections.reduce((n, c) => n + c.answerable_count, 0), 'answers for study'],
    [collections.reduce((n, c) => n + c.scorable, 0), 'official keys'],
  ] as const
  const compactHeader = viewKey !== 'overview' && viewKey !== 'home'
  return <div className="exam-experience exam-overview" data-compact-header={compactHeader ? 'true' : undefined} data-exam-tone={examPresentation(presentationId || collections[0]?.id || '').tone}>
    {compactHeader ? (
      <div className="exam-compact-masthead">
        <div className="exam-compact-title-wrap">
          <div className="exam-compact-title-row">
            <h1 className="font-display">{title}</h1>
            {headerAction}
          </div>
        </div>
        <div id="exam-module-tabs" className="exam-compact-tabs">{navigation}</div>
      </div>
    ) : (
      <>
        <header className="exam-overview-heading">
          <p className="font-mono text-xs uppercase tracking-[.1em] text-exams-dark">Past papers · exam preparation</p>
          <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="mt-2 font-display text-[clamp(30px,4vw,38px)] leading-tight">{title}</h1>{headerAction}</div>
          <p className="mt-3 text-sm leading-relaxed text-secondary">{description || 'Explore past papers, browse by subject, or keep practising through the question bank.'}</p>
        </header>
        <div id="exam-module-tabs">{navigation}</div>
      </>
    )}
    <div key={viewKey} className="exam-module-panel">
    {children ?? <>
    {!loading && !error && <>
      <dl className="exam-overview-stats">{stats.map(([n, label]) => <div key={label}><dd>{count(n)}</dd><dt>{label}</dt></div>)}</dl>
      <div className="exam-overview-note">Browse opens the selected paper’s questions. Answer labels and source PDFs remain available there; written questions are included for reading.</div>
      <div className="exam-overview-toolbar">
        <h2 className="font-display text-lg">Past papers</h2>
        <label className="flex items-center gap-2 text-sm text-secondary">Order<select aria-label="Paper order" value={order} onChange={e => setParams(previous => {
          const next = new URLSearchParams(previous)
          if (e.target.value === 'oldest') next.set('paper_sort', 'oldest'); else next.delete('paper_sort')
          next.delete('paper_page')
          return next
        }, { replace: true })} className="min-h-11 rounded-lg border border-hairline bg-card px-3 text-ink"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label>
      </div>
      <div className="exam-overview-papers" aria-label="Past paper summaries">{papers.map(source => <OverviewPaperCard key={source.collectionId + ':' + source.paper.id} source={source}/>)}</div>
      {!papers.length && <p className="py-8 text-secondary">No original exam papers are available yet.</p>}
    </>}
    {loading && <p role="status" className="py-8 text-sm text-secondary">Loading exam papers…</p>}
    {error && <div role="alert" className="my-5 rounded-xl border border-hairline bg-card p-4"><p>{error}</p>{onRetry && <button className="mt-2 min-h-11 text-link underline" onClick={onRetry}>Retry exam papers</button>}</div>}
    </>}
    </div>
  </div>
}

function OverviewPaperCard({ source }: { source: OverviewPaper }) {
  const { paper: p, collectionId, booklets } = source
  const identity = paperIdentity(p)
  const compactGrouped = collectionId === 'combined-prelims' && booklets.papers.length > 1
  const title = compactGrouped ? booklets.title : booklets.papers.length > 1 ? withoutBooklet(identity.title) : identity.title
  const exam = withoutBooklet(identity.exam || p.title)
  const base = `/exams/${collectionId}`
  const encoded = encodeURIComponent(p.id)
  const browse = paperBrowseLink(collectionId,p.id)
  const canBrowse = p.allow_browse !== false && p.questions > 0
  const canPractice = p.allow_practice && p.answerable_count > 0
  return <article className="overview-paper-card">
    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
      <span className="font-mono font-semibold text-exams-dark">{p.year ?? 'Year not listed'}</span>
      {booklets.papers.length > 1 && <details className="overview-booklets"><summary>{booklets.papers.length} booklet originals</summary><ul>{booklets.papers.map(b => <li key={b.id}><Link className="inline-flex min-h-11 items-center text-link underline" to={`${base}/paper?paper=${encodeURIComponent(b.id)}`}>{bookletLabel(b)}</Link></li>)}</ul></details>}
    </div>
    <h3 className="mt-2 font-display text-md leading-snug">{canBrowse ? <Link to={browse} className="hover:underline">{title}</Link> : title}</h3>
    {exam && exam !== title && !compactGrouped && <p className="overview-paper-exam" title={exam}>{exam}</p>}
    <p className="mt-2 text-sm text-secondary"><strong className="text-ink">{count(p.questions)}</strong> questions{p.descriptive ? ` · ${count(p.descriptive)} written` : ''}</p>
    <p className="mt-1 text-xs text-secondary">{count(p.answerable_count)} answers for study · {count(p.scorable)} official keys</p>
    {!!p.blocked_count && <p className="mt-2 text-xs text-mypick">{count(p.blocked_count)} source/key {p.blocked_count === 1 ? 'issue' : 'issues'} · unscored</p>}
    {!canBrowse && <p className="mt-2 text-xs text-secondary">{p.source_pdf_url ? 'Read the original PDF.' : 'Questions are not available for browsing yet.'}</p>}
    <div className="overview-paper-actions">
      {canBrowse && <Link className="overview-paper-browse" to={browse}>Browse questions →</Link>}
      {canPractice && <Link className="overview-paper-link" to={`${base}?view=practice&paper=${encoded}#exam-question-browser`}>Practice</Link>}
      {p.source_pdf_url && <a className="overview-paper-link" href={p.source_pdf_url} target="_blank" rel="noreferrer">PDF ↗</a>}
    </div>

  </article>
}
