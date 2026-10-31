import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { listQuestionPapers, listTaxonomy, type QuestionPaperSummary, type TaxonomyFacet } from '../lib/api'

const PAGE = 8

export default function Mizo() {
  const [facets, setFacets] = useState<TaxonomyFacet[]>([])
  const [papers, setPapers] = useState<QuestionPaperSummary[]>([])
  const [totalPapers, setTotalPapers] = useState(0)
  const [offset, setOffset] = useState(0)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { listTaxonomy('all').then(setFacets).catch(() => {}) }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { setSearch(query.trim()); setOffset(0) }, 250)
    return () => window.clearTimeout(timer)
  }, [query])
  useEffect(() => {
    let live = true
    setLoading(true); setError('')
    listQuestionPapers({ subject_id: 'mizo', q: search.length >= 2 ? search : undefined, limit: PAGE, offset })
      .then((page) => { if (live) { setPapers(page.items); setTotalPapers(page.total) } })
      .catch((e) => { if (live) setError(e.message || 'Mizo papers could not be loaded.') })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [search, offset])

  const mizo = useMemo(() => facets.filter((f) => f.subject_id === 'mizo'), [facets])
  const count = mizo[0]?.subject_questions ?? mizo.reduce((sum, f) => sum + f.questions, 0)
  const literature = mizo.find((f) => f.topic_id === 'mizo/literature')?.questions ?? 0
  const pages = Math.max(1, Math.ceil(totalPapers / PAGE))

  return <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <Link to="/library" className="text-[13px] font-semibold text-link">← Study library</Link>
    <header className="mt-5 rounded-[18px] bg-[#E3F1EF] px-6 py-8 sm:px-9">
      <div className="font-mono text-[11px] uppercase tracking-[.12em] text-[#176F72]">Language · literature · culture</div>
      <h1 className="mt-2 font-display text-[clamp(38px,5vw,56px)] font-medium leading-tight">Mizo</h1>
      <p className="mt-3 max-w-[740px] text-[16px] leading-relaxed text-[#315A58]">Practise Mizo questions from past papers, explore literature, and return to each question’s printed source. Answers keep their official or derived labels.</p>
      <div className="mt-5 flex flex-wrap items-center gap-3"><Link to="/library/subjects/mizo" className="inline-flex min-h-11 items-center rounded-pill bg-[#176F72] px-5 text-[13px] font-semibold text-white">Start Mizo practice →</Link><a href="#mizo-papers" className="inline-flex min-h-11 items-center rounded-pill border border-[#8DBFBC] px-5 text-[13px] font-semibold text-[#176F72]">Browse source papers ↓</a><span className="font-mono text-[11px] text-[#315A58]">{count.toLocaleString('en-IN')} tagged questions</span></div>
    </header>

    <section className="mt-8 grid gap-3 md:grid-cols-3" aria-label="Mizo study routes">
      <Link to="/library/subjects/mizo" className="rounded-[14px] border border-hairline bg-card p-5 hover:border-[#176F72]"><div className="font-mono text-[10px] uppercase tracking-wide text-[#176F72]">All Mizo questions</div><h2 className="mt-2 font-display text-[23px]">Read and practise</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">Mizo language, expression, customs and other tagged questions. Check answers inline and save your progress.</p><span className="mt-4 inline-block text-[13px] font-semibold text-link">Open questions →</span></Link>
      <Link to="/library/subjects/mizo?topic_id=mizo%2Fliterature" className="rounded-[14px] border border-hairline bg-card p-5 hover:border-[#176F72]"><div className="font-mono text-[10px] uppercase tracking-wide text-[#176F72]">Literature</div><h2 className="mt-2 font-display text-[23px]">Writers and works</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">Browse the literature-tagged questions with their answer provenance and original papers.</p><span className="mt-4 inline-block text-[13px] font-semibold text-link">{literature.toLocaleString('en-IN')} questions →</span></Link>
      <Link to="/library/subjects/general-studies?topic_id=general-studies%2Fmizoram" className="rounded-[14px] border border-hairline bg-card p-5 hover:border-[#176F72]"><div className="font-mono text-[10px] uppercase tracking-wide text-[#176F72]">Related shelf</div><h2 className="mt-2 font-display text-[23px]">Mizoram GK</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">State history, geography and public affairs belong in General Studies. Practise them in that subject flow.</p><span className="mt-4 inline-block text-[13px] font-semibold text-link">Open Mizoram GK →</span></Link>
    </section>

    <section id="mizo-papers" className="mt-10 scroll-mt-24"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-ink pb-3"><div><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Source papers</div><h2 className="mt-1 font-display text-[28px]">Mizo questions by paper</h2><p className="mt-1 max-w-[700px] text-[13px] text-secondary">A paper can cover several subjects. Browse opens its Mizo-tagged questions here; the PDF shows the complete original paper.</p></div><span className="font-mono text-[11px] text-muted">{totalPapers.toLocaleString('en-IN')} papers</span></div>
      <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find an exam or paper" aria-label="Search Mizo source papers" className="mt-4 h-11 w-full rounded-pill border border-hairline bg-card px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" />
      {error && <p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}</p>}
      {loading ? <p className="mt-5 text-[13px] text-muted">Loading papers…</p> : <div className="mt-4 grid gap-3 md:grid-cols-2">{papers.map((paper) => {
        const title = paper.exam || paper.source_file?.split('/').pop()?.replace(/\.pdf$/i, '') || 'MPSC paper'
        return <article key={paper.id} className="rounded-[13px] border border-hairline bg-card p-4"><div className="font-mono text-[10px] uppercase tracking-wide text-[#176F72]">{[paper.year, paper.month, paper.paper_number ? `Paper ${paper.paper_number}` : null].filter(Boolean).join(' · ')}</div><h3 className="mt-2 line-clamp-2 font-display text-[19px]">{title}</h3><p className="mt-2 text-[12px] text-muted">{paper.questions} questions in full paper · {paper.scorable} verified-key MCQs</p><div className="mt-4 flex flex-wrap gap-3"><Link to={`/library/subjects/mizo?paper_id=${encodeURIComponent(paper.id)}&paper_label=${encodeURIComponent(title)}`} className="rounded-pill bg-ink px-3 py-2 text-[12px] font-semibold text-paper">Browse Mizo questions →</Link>{paper.source_pdf_url && <a href={paper.source_pdf_url} target="_blank" rel="noreferrer" className="py-2 text-[12px] font-semibold text-link underline">Original PDF</a>}</div></article>
      })}</div>}
      {!loading && !error && papers.length === 0 && <p className="mt-4 text-[13px] text-secondary">No papers match that search.</p>}
      {!loading && pages > 1 && <nav aria-label="Mizo paper pages" className="mt-5 flex items-center justify-between"><button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} className="min-h-11 rounded-pill border border-hairline px-4 text-[13px] disabled:opacity-40">← Previous</button><span className="font-mono text-[11px] text-muted">Page {Math.floor(offset / PAGE) + 1} of {pages}</span><button type="button" disabled={offset + PAGE >= totalPapers} onClick={() => setOffset(offset + PAGE)} className="min-h-11 rounded-pill border border-hairline px-4 text-[13px] disabled:opacity-40">Next →</button></nav>}
    </section>
  </div>
}
