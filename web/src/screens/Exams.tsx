import { useEffect, useMemo, useState } from 'react'
import { Link,useSearchParams } from 'react-router-dom'
import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
import {
  getCollection, getExamBookmarks, getExamProgress, isLaterExamCollection,
  listCollections, removeExamBookmark, saveExamBookmark,
  type Collection, type CollectionDetail, type ExamProgressSummary,
} from '../lib/api'

type Filter = 'all' | 'saved'
const PAGE_SIZE = 8
const ALIASES: Record<string, string[]> = {
  ldc: ['ldc', 'lower division clerk'], udc: ['udc', 'upper division clerk'],
  prelims: ['prelims', 'preliminary', 'combined prelims'], mpsc: ['mpsc', 'mizoram public service commission'],
  gazetted: ['gazetted', 'gazette', 'group b'], gazette: ['gazetted', 'gazette', 'group b'],
  nongazetted: ['non gazetted', 'non-gazetted', 'ldc', 'udc'],
  assistant: ['assistant', 'assistant grade', 'assistant audit'],
}
const PHRASES: Record<string, string[]> = {
  'non gazetted': ['non gazetted', 'ldc', 'udc'], 'group b': ['group b', 'gazetted'],
  'combined prelims': ['combined prelims', 'preliminary'],
  'lower division clerk': ['lower division clerk', 'ldc'], 'upper division clerk': ['upper division clerk', 'udc'],
}
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
function matches(text: string, query: string) {
  const terms = norm(query).split(' ').filter(Boolean)
  const target = norm(text)
  const groups: string[][] = []
  for (let i = 0; i < terms.length;) {
    const phrase = Object.keys(PHRASES).sort((a, b) => b.length - a.length).find((p) => terms.slice(i, i + p.split(' ').length).join(' ') === p)
    if (phrase) { groups.push(PHRASES[phrase]); i += phrase.split(' ').length }
    else { groups.push(ALIASES[terms[i]] ?? [terms[i]]); i++ }
  }
  return groups.every((g) => g.some((alias) => target.includes(norm(alias))))
}

export default function Exams() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [feature, setFeature] = useState<CollectionDetail | null>(null)
  const [progress, setProgress] = useState<Record<string, ExamProgressSummary>>({})
  const [bookmarks, setBookmarks] = useState<string[]>([])
  const [busyBookmark, setBusyBookmark] = useState<string | null>(null)
  const [params,setParams]=useSearchParams()
  const filter:Filter=params.get('exam_filter')==='saved'?'saved':'all',query=params.get('q')||'',page=pageNumber(params.get('page'))-1
  function filterURL(key:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);next.delete('page');return next},{replace:true})}
  const setFilter=(value:Filter)=>filterURL('exam_filter',value==='all'?'':value),setQuery=(value:string)=>filterURL('q',value)
  const goPage=(value:number)=>{setParams(previous=>{const next=new URLSearchParams(previous);if(value>1)next.set('page',String(value));else next.delete('page');return next});requestAnimationFrame(()=>scrollToResults('exam-library-heading'))}
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let live = true
    listCollections().then((all) => {
      if (!live) return
      const available = all.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c))
      setCollections(available)
      setLoading(false)
      // The catalog is visible immediately; the featured detail enriches it in the background.
      const featured = available.find((c) => c.id === 'combined-prelims') ?? available.find((c) => c.kind === 'exam')
      if (featured) getCollection(featured.id).then((detail) => live && setFeature(detail)).catch(() => {})
    }).catch((e) => { if (live) { setError(e.message); setLoading(false) } })
    Promise.all([getExamBookmarks(), getExamProgress()]).then(([saved, rows]) => {
      if (!live) return
      setBookmarks(saved.collection_ids)
      setProgress(Object.fromEntries(rows.map((row) => [row.collection_id, row])))
    }).catch(() => {})
    return () => { live = false }
  }, [])

  const featured = collections.find((c) => c.id === 'combined-prelims') ?? collections.find((c) => c.kind === 'exam') ?? null
  const shown = useMemo(() => collections.filter((c) => {
    const isSaved = bookmarks.includes(c.id)
    const typeMatch = filter === 'all' || isSaved
    return typeMatch && matches(`${c.title} ${c.id} ${c.kind}`, query)
  }), [collections, bookmarks, filter, query])
  const pages = Math.ceil(shown.length / PAGE_SIZE)
  const visible = shown.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  useEffect(()=>{if(!loading&&page>=Math.max(1,pages))setParams(previous=>{const next=new URLSearchParams(previous);if(pages>1)next.set('page',String(pages));else next.delete('page');return next},{replace:true})},[loading,page,pages,setParams])

  async function toggleBookmark(c: Collection) {
    const wasSaved = bookmarks.includes(c.id)
    setBusyBookmark(c.id)
    // Optimistic UI keeps browsing responsive; restore the saved state if the API fails.
    setBookmarks((old) => wasSaved ? old.filter((id) => id !== c.id) : [c.id, ...old])
    try {
      if (wasSaved) await removeExamBookmark(c.id)
      else await saveExamBookmark(c.id)
    } catch (e) {
      setBookmarks((old) => wasSaved ? [...old, c.id] : old.filter((id) => id !== c.id))
      setError(e instanceof Error ? `Could not update saved exams: ${e.message}` : 'Could not update saved exams.')
    } finally { setBusyBookmark(null) }
  }

  const detail = feature?.id === featured?.id ? feature : null
  const general = detail?.section_list.filter((s) => s.path.startsWith('general/')) ?? []
  const subjectSections = detail?.section_list.filter((s) => s.path.startsWith('subject/')) ?? []
  const featuredSections = [...general, ...subjectSections].slice(0, 5)
  const examCount = collections.filter((c) => c.kind === 'exam').length
  const savedCount = bookmarks.filter((id) => collections.some((c) => c.id === id)).length

  return <div className="mx-auto max-w-shell px-5 pb-24 pt-7 sm:px-6 sm:pt-10">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-exams-dark">Your exam room</div>
        <h1 className="mt-2 font-display text-[clamp(36px,5vw,54px)] font-medium leading-[1.02] -tracking-[0.03em]">Exams</h1>
        <p className="mt-3 max-w-[690px] text-[16px] leading-relaxed text-secondary">Find an exam, study its questions by subject and topic, work through past papers, or start a timed mock.</p>
      </div>
      <Link to="/desk" className="rounded-pill border border-hairline bg-card px-4 py-2.5 text-[13px] font-semibold hover:border-ink">Open study desk →</Link>
    </div>

    <section className="mt-6 rounded-[14px] border border-hairline bg-exams-soft p-5" aria-label="Group B common subjects"><h2 className="font-display text-[27px]">Group B — English &amp; GK/GS</h2><p className="mt-2 text-[14px] text-secondary">Focus on common subjects across gazetted and non-gazetted recruitment papers. Technical papers have their own area.</p><div className="mt-4 flex flex-wrap gap-3"><Link to="/group-b" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[13px] font-semibold text-paper">Study English &amp; GK/GS →</Link><Link to="/group-b?study_area=technical" className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Technical papers →</Link></div></section>

    <section className="mt-6 grid gap-3 sm:grid-cols-3" aria-label="Exam overview">
      <div className="rounded-[14px] bg-exams-soft p-4"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-exams-dark">Prepared routes</div><div className="mt-1 font-display text-[25px]">{loading ? '…' : examCount}</div><p className="mt-1 text-[12px] text-[#4A3205]">Exam collections, ordered by paper and subject</p></div>
      <div className="rounded-[14px] border border-hairline bg-card p-4"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Your saved list</div><div className="mt-1 font-display text-[25px]">{savedCount} <span className="text-[15px] text-muted">exam{savedCount === 1 ? '' : 's'}</span></div><p className="mt-1 text-[12px] text-secondary">Bookmarks sync with your account when you sign in</p></div>
      <div className="rounded-[14px] border border-hairline bg-card p-4"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-practice-dark">Past papers</div><div className="mt-1 font-display text-[21px]">Browse &amp; practise</div><p className="mt-1 text-[12px] text-secondary">Open questions within each exam, with its source and answer status</p></div>
    </section>

    {featured && <section className="relative mt-5 overflow-hidden rounded-[18px] bg-[#171713] text-paper shadow-[0_14px_40px_rgba(34,30,20,.15)]">
      <div className="absolute -right-10 -top-16 h-64 w-64 rounded-full border border-white/10" aria-hidden="true"/><div className="absolute -right-2 -top-8 h-48 w-48 rounded-full border border-white/10" aria-hidden="true"/>
      <div className="relative grid lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="p-6 sm:p-8">
          <div className="flex flex-wrap items-center gap-2"><span className="rounded-pill bg-practice px-3 py-1 font-mono text-[10px] uppercase tracking-[.1em] text-white">Featured route</span><span className="font-mono text-[11px] text-[#C5BDAD]">{featured.kind} · MPSC</span></div>
          <h2 className="mt-4 max-w-2xl font-display text-[clamp(32px,4vw,48px)] font-medium leading-[1.04] -tracking-[.025em]">{featured.title}</h2>
          <p className="mt-3 max-w-[590px] text-[14px] leading-relaxed text-[#DDD6C8]">Work through the papers in order, browse every question with its source context, or start a timed set using verified answer keys.</p>
          <div className="mt-4 flex min-h-7 flex-wrap gap-1.5">{featuredSections.map((s) => <span key={s.path} className="rounded-pill border border-white/20 px-2.5 py-1 text-[11px] text-[#EEE7DA]">{s.title}</span>)}{!featuredSections.length && <span className="text-[11px] text-[#BDB3A0]">Past papers · verified-key practice · progress saved</span>}</div>
          <div className="mt-6 flex flex-wrap gap-2.5"><Link to={`/exams/${featured.id}`} className="rounded-pill bg-paper px-5 py-3 text-[14px] font-semibold text-ink">Explore this exam</Link><Link to={`/exams/${featured.id}?view=topics#exam-study-heading`} className="rounded-pill border border-white/50 px-5 py-3 text-[14px] font-semibold text-paper hover:bg-white/10">Study by subject</Link><Link to={`/exams/${featured.id}/mock`} className="rounded-pill border border-white/50 px-5 py-3 text-[14px] font-semibold text-paper hover:bg-white/10">Try a timed set</Link></div>
        </div>
        <div className="grid grid-cols-2 content-center gap-y-5 bg-white/[.06] p-6 sm:px-8 lg:grid-cols-1 lg:gap-y-6">
          <Stat label="Questions" value={featured.questions.toLocaleString('en-IN')} /><Stat label="Verified keys" value={featured.scorable.toLocaleString('en-IN')} /><Stat label="Sections" value={featured.sections.toLocaleString('en-IN')} /><Stat label="Your answers" value={(progress[featured.id]?.answered ?? 0).toLocaleString('en-IN')} />
        </div>
      </div>
    </section>}

    <section className="mt-9" aria-labelledby="exam-library-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><div className="font-mono text-[10px] uppercase tracking-[.12em] text-muted">Find your next session</div><h2 id="exam-library-heading" tabIndex={-1} className="scroll-mt-28 focus:outline-none mt-1 font-display text-[30px] font-medium">Browse exams</h2></div>
        <span className="text-[12px] text-secondary">{loading ? 'Loading collections…' : `${shown.length} ${shown.length === 1 ? 'collection' : 'collections'}`}</span>
      </div>
      <div className="mt-4 rounded-[14px] border border-hairline bg-card p-3.5 sm:p-4">
        <label htmlFor="exam-search" className="sr-only">Search exam collections</label><input id="exam-search" type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search: LDC, UDC, assistant, prelims, gazetted…" className="h-12 w-full rounded-[10px] border border-hairline bg-canvas px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" />
        <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Filter exams">{([['all','All exams'],['saved','★ Saved']] as const).map(([key,label]) => <button key={key} type="button" onClick={() => setFilter(key)} aria-pressed={filter === key} className={`rounded-pill px-3.5 py-2 text-[12px] font-semibold transition ${filter === key ? 'bg-ink text-paper' : 'border border-hairline text-secondary hover:border-ink hover:text-ink'}`}>{label}{key === 'saved' ? ` (${savedCount})` : ''}</button>)}</div>
      </div>

      {error && <div role="status" className="mt-3 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}<button type="button" onClick={() => setError(null)} className="ml-2 underline">Dismiss</button></div>}
      {loading && <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading exams">{[1,2,3].map((i) => <div key={i} className="h-48 animate-pulse rounded-[14px] border border-hairline bg-card" />)}</div>}
      {!loading && visible.length > 0 && <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{visible.map((c) => {
        const p = progress[c.id]
        const isSaved = bookmarks.includes(c.id)
        const completion = p && c.questions ? Math.min(100, Math.round(100 * p.unique_questions / c.questions)) : 0
        return <article key={c.id} className="group flex min-h-[210px] flex-col rounded-[15px] border border-hairline bg-card p-4 shadow-[0_1px_2px_rgba(29,27,24,.04)] transition hover:-translate-y-0.5 hover:border-[#C6B58F] hover:shadow-[0_10px_26px_rgba(29,27,24,.09)] sm:p-5">
          <div className="flex items-start justify-between gap-3"><div className="flex items-center gap-2"><span className={`grid h-8 w-8 place-items-center rounded-[9px] ${c.kind === 'exam' ? 'bg-exams-soft text-exams-dark' : 'bg-practice-soft text-practice-dark'}`} aria-hidden="true">{c.kind === 'exam' ? '✦' : '↗'}</span><span className="font-mono text-[10px] uppercase tracking-[.08em] text-muted">{c.kind} · {c.sections} sections</span></div><button type="button" onClick={() => void toggleBookmark(c)} disabled={busyBookmark === c.id} aria-label={`${isSaved ? 'Remove' : 'Save'} ${c.title} ${isSaved ? 'from' : 'to'} saved exams`} aria-pressed={isSaved} className={`grid h-9 w-9 shrink-0 place-items-center rounded-full border transition ${isSaved ? 'border-[#E9C46A] bg-[#FFF6DD] text-[#79570A]' : 'border-hairline text-muted hover:border-[#C6B58F] hover:text-ink'} disabled:opacity-50`}><span aria-hidden="true">{isSaved ? '★' : '☆'}</span></button></div>
          <Link to={`/exams/${c.id}`} className="mt-3 block rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"><h3 className="font-display text-[22px] font-medium leading-tight group-hover:underline decoration-[#C6B58F] underline-offset-4">{c.title}</h3></Link>
          <p className="mt-2 text-[12px] text-secondary">{c.questions.toLocaleString('en-IN')} questions <span className="px-1 text-[#C8BDA8]">·</span> {c.scorable.toLocaleString('en-IN')} official-key questions</p>
          <Link to={`/exams/${c.id}?view=topics#exam-study-heading`} className="mt-3 inline-flex min-h-11 items-center self-start rounded-pill border border-hairline px-3 text-[12px] font-semibold text-link hover:border-ink">Study subjects &amp; topics →</Link>
          {p && p.answered > 0 ? <div className="mt-auto pt-4"><div className="flex justify-between text-[11px]"><span className="font-medium">{p.unique_questions.toLocaleString('en-IN')} unique questions answered</span><span className="text-muted">{completion}% of questions</span></div><div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#ECE6D9]" role="progressbar" aria-label={`${c.title} coverage`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={completion}><div className="h-full rounded-full bg-exams" style={{ width: `${completion}%` }} /></div><div className="mt-2 flex items-center justify-between text-[11px] text-secondary"><span>{p.accuracy}% accuracy</span><Link to={`/exams/${c.id}?view=practice#exam-question-browser`} className="font-semibold text-ink">Practise →</Link></div></div> : <div className="mt-auto flex items-center justify-between pt-4"><span className="text-[11px] text-muted">{c.scorable ? 'Verified-key practice available' : 'Browse questions and papers'}</span><Link to={`/exams/${c.id}`} className="text-[12px] font-semibold text-ink">Explore →</Link></div>}
        </article>
      })}</div>}
      {!loading && !visible.length && <div className="mt-4 rounded-[14px] border border-dashed border-hairline bg-card p-8 text-center"><div className="font-display text-[22px]">{filter === 'saved' ? 'Your saved exams will be here' : 'No matching exams'}</div><p className="mt-1 text-[13px] text-secondary">{filter === 'saved' ? 'Tap the star on any exam to keep it close.' : 'Try a shorter search or clear the selected filter.'}</p>{filter === 'saved' && <button type="button" onClick={() => setFilter('all')} className="mt-3 rounded-pill bg-ink px-4 py-2 text-[12px] font-semibold text-paper">Browse all exams</button>}</div>}
      <Pagination page={page+1} pages={pages} disabled={loading} onPageChange={goPage} label="Exam collection pages"/>
    </section>
  </div>
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div><div className="font-display text-[30px] leading-none text-paper">{value}</div><div className="mt-1.5 text-[11px] text-[#C5BDAD]">{label}</div></div>
}
