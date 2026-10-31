import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { listQuestionPapers, listTaxonomy, type QuestionPaperSummary, type TaxonomyFacet } from '../lib/api'

const LEGACY = 'https://map.hawayu.in/embed'

export default function English() {
  const [facets, setFacets] = useState<TaxonomyFacet[]>([])
  const [error, setError] = useState('')
  const [papers, setPapers] = useState<QuestionPaperSummary[]>([])
  const [paperTotal, setPaperTotal] = useState(0)
  const [paperLoading, setPaperLoading] = useState(true)
  const [paperError, setPaperError] = useState('')
  const [paperSearch, setPaperSearch] = useState('')
  const [paperQuery, setPaperQuery] = useState('')
  const [examType, setExamType] = useState('')
  const [year, setYear] = useState('')
  const [paperOffset, setPaperOffset] = useState(0)
  const paperPageSize = 24
  useEffect(() => { listTaxonomy('all').then(setFacets).catch((e) => setError(e.message)) }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { setPaperQuery(paperSearch.trim()); setPaperOffset(0) }, 250)
    return () => window.clearTimeout(timer)
  }, [paperSearch])
  useEffect(() => {
    let cancelled = false
    setPaperLoading(true)
    setPaperError('')
    const selectedYear = /^\d{4}$/.test(year) ? Number(year) : undefined
    listQuestionPapers({
      subject_id: 'english',
      q: paperQuery.length >= 2 ? paperQuery : undefined,
      year_from: selectedYear,
      year_to: selectedYear,
      exam_type: examType ? examType as QuestionPaperSummary['exam_type'] : undefined,
      limit: paperPageSize,
      offset: paperOffset,
    }).then((page) => {
      if (!cancelled) { setPapers(page.items); setPaperTotal(page.total) }
    }).catch((e) => { if (!cancelled) setPaperError(e.message) })
      .finally(() => { if (!cancelled) setPaperLoading(false) })
    return () => { cancelled = true }
  }, [paperQuery, examType, year, paperOffset])
  const english = facets.filter((f) => f.subject_id === 'english')
  const topics = english.filter((f) => f.topic_id)
  const topicCount = (id: string) => english.find((f) => f.topic_id === id)?.questions ?? 0
  // Topics may overlap; the API supplies a distinct subject total.
  const total = english[0]?.subject_questions ?? english.reduce((sum, f) => sum + f.questions, 0)
  const paperPages = Math.max(1, Math.ceil(paperTotal / paperPageSize))
  const paperPage = Math.floor(paperOffset / paperPageSize) + 1
  const years = useMemo(() => Array.from({ length: 2026 - 2010 + 1 }, (_, i) => String(2026 - i)), [])

  return <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">English · Mizoram PSC</div>
    <header className="mt-2 grid gap-5 border-b border-hairline pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
      <div><h1 className="font-display text-[clamp(36px,5vw,52px)] font-medium leading-[1.05] -tracking-[0.02em]">English practice</h1>
        <p className="mt-3 max-w-[720px] text-[17px] leading-relaxed text-secondary">Build the idea first, practise with real questions, then review the answer and its explanation. Grammar, vocabulary, and MCQs all draw from the shared question bank.</p>
      </div>
      <div className="rounded-[12px] border border-hairline bg-card px-4 py-3"><div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">English bank</div><div className="mt-1 font-display text-[25px]">{total.toLocaleString('en-IN')}</div><div className="text-[12px] text-secondary">approved topic tags</div></div>
    </header>

    <section className="mt-7">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">Choose a route</div><h2 className="mt-1 font-display text-[26px] font-medium">Learn, drill, and revisit</h2></div><Link to="/library/subjects/english" className="text-[13px] font-semibold text-link underline">Practise English questions →</Link></div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <article className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
          <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#1F6234]">01 · Grammar workshop</div><h3 className="mt-2 font-display text-[25px] font-medium">Tenses &amp; voice</h3>
          <p className="mt-2 text-[14px] leading-relaxed text-secondary">Start with when an action happens and whether the sentence centres the doer or the action. Then practise the grammar questions tagged in the bank.</p>
          <div className="mt-4 flex flex-wrap items-center gap-3"><Link to="/library/subjects/english?topic_id=english%2Fgrammar" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[13px] font-semibold text-paper">Practise grammar →</Link><a href={`${LEGACY}/tenses-voice`} target="_blank" rel="noreferrer" className="min-h-11 py-3 text-[13px] font-semibold text-link underline">Open full lesson</a><span className="font-mono text-[11px] text-muted">{topicCount('english/grammar').toLocaleString('en-IN')} tagged questions</span></div>
        </article>

        <article className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
          <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#72509A]">02 · Learn → test → review</div><h3 className="mt-2 font-display text-[25px] font-medium">English MCQ masterclass</h3>
          <p className="mt-2 text-[14px] leading-relaxed text-secondary">Work across grammar, vocabulary, and comprehension. Tap an option for immediate feedback; answer provenance and explanations stay visible so uncertain keys are never mistaken for official ones.</p>
          <div className="mt-4 flex flex-wrap items-center gap-3"><Link to="/library/subjects/english" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[13px] font-semibold text-paper">Start MCQ practice →</Link><a href={`${LEGACY}/eng-mcq-masterclass`} target="_blank" rel="noreferrer" className="min-h-11 py-3 text-[13px] font-semibold text-link underline">Open full masterclass</a></div>
        </article>

        <article className="rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
          <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#A35A22]">03 · Write and reflect</div><h3 className="mt-2 font-display text-[25px] font-medium">Essay practice</h3>
          <p className="mt-2 text-[14px] leading-relaxed text-secondary">Use the essay collection to choose a prompt, plan a clear argument, and draft a structured response. Descriptive writing stays separate from MCQ scoring.</p>
          <div className="mt-4 flex flex-wrap items-center gap-3"><Link to="/essay" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[13px] font-semibold text-paper">Open essay practice →</Link><a href={`${LEGACY}/essay`} target="_blank" rel="noreferrer" className="text-[12px] font-semibold text-link underline">See the original lesson</a></div>
        </article>

        <Link to="/vocabulary" className="rounded-[14px] bg-[#F1EBF7] p-5 transition-shadow hover:shadow-[0_8px_24px_rgba(29,27,24,.1)]">
          <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#72509A]">04 · Recall · spaced review</div><h3 className="mt-2 font-display text-[25px] font-medium">Vocabulary helper</h3>
          <p className="mt-2 text-[14px] leading-relaxed text-[#49385A]">Test yourself on verified vocabulary questions, track what is due, and revisit words over time.</p><div className="mt-4 text-[13px] font-semibold text-[#62418B]">Start a vocabulary review →</div>
        </Link>
      </div>
    </section>

    <section id="paper-browser" className="mt-10 scroll-mt-24">
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-ink pb-3">
        <div><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">Past papers · browse by exam</div><h2 className="mt-1 font-display text-[27px] font-medium">General English papers</h2><p className="mt-1 max-w-[680px] text-[14px] leading-relaxed text-secondary">Open a complete paper, browse every question in its printed order, and check available answers with their provenance. Papers without a reliable key remain readable.</p></div>
        <span className="rounded-pill border border-hairline bg-card px-3 py-2 font-mono text-[11px] text-secondary">{paperTotal.toLocaleString('en-IN')} papers</span>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_190px_150px]">
        <input value={paperSearch} onChange={(e) => setPaperSearch(e.target.value)} type="search" placeholder="Find an exam, post, or paper name" aria-label="Search General English papers" className="h-11 min-w-0 rounded-pill border border-hairline bg-card px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" />
        <select value={examType} onChange={(e) => { setExamType(e.target.value); setPaperOffset(0) }} aria-label="Filter by exam type" className="h-11 rounded-pill border border-hairline bg-card px-4 text-[13px] text-secondary"><option value="">All exam types</option><option value="Direct">Direct recruitment</option><option value="Direct_NG">Direct · non-gazetted</option><option value="LDE">Departmental promotion</option><option value="Departmental">Departmental</option></select>
        <select value={year} onChange={(e) => { setYear(e.target.value); setPaperOffset(0) }} aria-label="Filter by exam year" className="h-11 rounded-pill border border-hairline bg-card px-4 text-[13px] text-secondary"><option value="">All years</option>{years.map((y) => <option key={y} value={y}>{y}</option>)}</select>
      </div>
      {paperError && <p className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick" role="alert">Could not load papers: {paperError}</p>}
      {paperLoading ? <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading English papers">{Array.from({ length: 6 }, (_, i) => <div key={i} className="h-40 animate-pulse rounded-[14px] border border-hairline bg-card" />)}</div> : <>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-busy={paperLoading}>
          {papers.map((paper) => {
            const file = (paper.source_file || paper.id.split('/').pop() || 'Question paper').replace(/\.pdf$/i, '')
            const heading = paper.exam || file
            const metadata = [paper.year, paper.month, paper.paper_number ? `Paper ${paper.paper_number}` : null, paper.exam_type.replace('_', ' ')].filter(Boolean).join(' · ')
            return <article key={paper.id} className="flex min-h-[176px] flex-col rounded-[14px] border border-hairline bg-card p-4 shadow-[0_1px_2px_rgba(29,27,24,.04)]">
              <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-practice-dark">{metadata}</div>
              <h3 className="mt-2 line-clamp-2 font-display text-[20px] font-medium leading-snug">{heading}</h3>
              <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted" title={file}>{file}</p>
              <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-4"><span className="font-mono text-[11px] text-secondary">{paper.questions} questions · {paper.scorable} official keys</span><div className="flex items-center gap-3"><Link to={`/library/subjects/english?paper_id=${encodeURIComponent(paper.id)}&paper_label=${encodeURIComponent(file)}`} className="rounded-pill bg-ink px-3 py-2 text-[12px] font-semibold text-paper">Browse →</Link>{paper.source_pdf_url && <a href={paper.source_pdf_url} target="_blank" rel="noreferrer" className="text-[12px] font-semibold text-link underline">Source PDF</a>}</div></div>
            </article>
          })}
        </div>
        {!papers.length && !paperError && <div className="mt-4 rounded-[14px] border border-hairline bg-card p-6 text-center text-[14px] text-secondary">No papers match those filters.</div>}
        {paperTotal > paperPageSize && <nav aria-label="General English paper pages" className="mt-5 flex items-center justify-between border-t border-hairline pt-4"><button disabled={paperOffset === 0} onClick={() => setPaperOffset((n) => Math.max(0, n - paperPageSize))} className="min-h-11 rounded-pill border border-hairline px-4 text-[13px] disabled:opacity-40">← Previous</button><span className="font-mono text-[11px] text-muted">Page {paperPage} of {paperPages}</span><button disabled={paperOffset + paperPageSize >= paperTotal} onClick={() => setPaperOffset((n) => n + paperPageSize)} className="min-h-11 rounded-pill border border-hairline px-4 text-[13px] disabled:opacity-40">Next →</button></nav>}
      </>}
    </section>

    <MaterialDiscovery subjectId="english" title="English notes from the community"/>
    <section className="mt-8 rounded-[14px] border border-hairline bg-paper p-5">
      <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">Practice format</div><h2 className="mt-1 font-display text-[22px] font-medium">Choose an answer to see the worked result</h2>
      <p className="mt-2 max-w-[760px] text-[14px] leading-relaxed text-secondary">English MCQs use the Aptitude Hub pattern: select an option, see the correct answer and explanation immediately, and record the attempt in your shared progress. Questions without a checkable key remain available to read.</p>
      <div className="mt-3 flex flex-wrap gap-2">{topics.map((f) => <Link key={f.topic_id} to={`/library/subjects/english?topic_id=${encodeURIComponent(f.topic_id!)}`} className="rounded-pill border border-hairline bg-card px-3 py-2 text-[12px] text-secondary">{f.topic} · {f.questions.toLocaleString('en-IN')}</Link>)}</div>
    </section>
    {error && <p className="mt-5 text-[14px] text-mypick">English topic totals could not load: {error}</p>}
    <Link to="/exams" className="mt-6 inline-block text-[13px] text-secondary underline">← Exams &amp; tools</Link>
  </div>
}
