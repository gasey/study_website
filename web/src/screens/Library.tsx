import {lazy,Suspense} from 'react'
const Materials=lazy(()=>import('./Materials'))
import { useEffect, useMemo, useState } from 'react'
import { Link,useSearchParams } from 'react-router-dom'
import { listLibraryShelves, type LibraryShelf, listTaxonomy, type TaxonomyFacet } from '../lib/api'

const FEATURED = [
  { title: 'Interactive Atlas', href: '/atlas', label: 'Maps · places · layers', description: 'Explore Mizoram, India and world geography, historical routes and polity maps.', color: 'bg-map-soft text-map-dark' },
  { title: 'Arithmetic', href: '/arithmetic', label: 'Learn · practise · papers', description: 'Build a method, then use real arithmetic questions and source papers.', color: 'bg-practice-soft text-practice-dark' },
  { title: 'Reasoning', href: '/arithmetic?subject=reasoning-and-aptitude&view=practice', label: 'Patterns · logic · aptitude', description: 'Work through reasoning concepts and practise with tagged questions.', color: 'bg-practice-soft text-practice-dark' },
  { title: 'English', href: '/english', label: 'Grammar · comprehension · writing', description: 'Learn, practise and browse English papers from one module.', color: 'bg-correct-soft text-correct-dark' },
  { title: 'Vocabulary helper', href: '/vocabulary', label: 'Recall · spaced review', description: 'Test words from real questions and revisit them when due.', color: 'bg-learn-soft text-learn-dark' },
  { title: 'Mizo', href: '/mizo', label: 'Language · literature · culture', description: 'Read and practise Mizo questions by topic and source paper.', color: 'bg-map-soft text-map-dark' },
  { title: 'Essay writing', href: '/essay', label: 'Prompts · private drafts', description: 'Write from real paper prompts and save drafts for later revision.', color: 'bg-exams-soft text-exams-dark' },
]

const VIEWS=[['subjects','Subjects'],['practice','Practice'],['reading','Reading'],['saved','Saved'],['tools','Tools']] as const
const HIGHLIGHTS = ['gk-gs', 'mizo', 'science', 'mathematics', 'reasoning-and-aptitude', 'english']

export default function Library() {
  const [shelves,setShelves]=useState<LibraryShelf[]>([])
  const [params,setParams]=useSearchParams();const tab=VIEWS.some(([id])=>id===params.get('library_view'))?params.get('library_view')!:'subjects';function setTab(value:string){setParams(p=>{const next=new URLSearchParams(p);next.set('library_view',value);for(const key of ['offset','q','access','sort','saved','collection_id','subject_id'])next.delete(key);return next})}
  const [facets, setFacets] = useState<TaxonomyFacet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    if(tab!=='subjects')return
    setLoading(true);setError('')
    let live = true
    listLibraryShelves().then(rows=>{if(live)setShelves(rows)}).catch(e=>{if(live)setError(e.message)})
    listTaxonomy('all',true).then((rows) => { if (live) setFacets(rows) })
      .catch((e) => { if (live) setError(e.message || 'Subjects could not be loaded.') })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [tab])

  const subjects = useMemo(() => {
    const grouped = new Map<string, TaxonomyFacet>()
    for (const facet of facets) {
      const current = grouped.get(facet.subject_id)
      if (current) current.questions = facet.subject_questions ?? current.questions + facet.questions
      else grouped.set(facet.subject_id, { ...facet, questions:facet.subject_questions??facet.questions, topic_id: null, topic: null })
    }
    const rows = [...grouped.values()]
    return rows.sort((a, b) => {
      const ai = HIGHLIGHTS.indexOf(a.subject_id)
      const bi = HIGHLIGHTS.indexOf(b.subject_id)
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
      return a.subject.localeCompare(b.subject)
    }).filter((f) => `${f.subject} ${f.subject_id}`.toLowerCase().includes(query.trim().toLowerCase()))
  }, [facets, query])

  return <div className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <div className="font-mono text-[11px] uppercase tracking-[.12em] text-practice-dark">Learn · practise · revisit</div>
    <div className="mt-2 flex flex-wrap items-end justify-between gap-4 border-b border-hairline pb-7">
      <div><h1 className="font-display text-[clamp(36px,5vw,54px)] font-medium leading-[1.04]">Study library</h1><p className="mt-3 max-w-[700px] text-[16px] leading-relaxed text-secondary">Find a subject, choose your practice or settle into a good read. Your study resources, organised in one place.</p></div>
      <Link to="/exams" className="ism-tactile-btn rounded-pill border border-hairline bg-card px-4 py-2.5 text-[13px] font-semibold shadow-sm hover:border-practice">Looking for an exam? →</Link>
    </div>

    <nav aria-label="Library views" className="mt-6 flex flex-wrap gap-2">{VIEWS.map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>setTab(id)} className={'ism-tactile-btn min-h-11 rounded-pill px-5 text-[13px] font-semibold '+(tab===id?'bg-ink text-paper shadow-sm':'border border-hairline bg-card hover:border-hairline2')}>{label}</button>)}</nav>
    {tab==='reading'&&<Suspense fallback={<p className="mt-5 text-muted">Loading reading…</p>}><Materials embedded/></Suspense>}
    {tab==='saved'&&<><div className="ism-card-surface mt-6 flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-hairline bg-card p-5"><div><h2 className="font-display text-[25px]">Your saved questions</h2><p className="mt-2 text-[13px] text-secondary">Revisit bookmarks, mistakes and words due for review.</p></div><Link to="/revision" className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link hover:underline">Open revision →</Link></div><Suspense fallback={<p className="mt-5 text-muted">Loading saved materials…</p>}><Materials key="saved" embedded savedOnly/></Suspense></>}
    {tab==='practice'&&<section className="mt-7" aria-labelledby="practice-heading"><h2 id="practice-heading" className="font-display text-[29px]">Choose how you practise</h2><p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-secondary">Past papers and learner contributions have separate banks. Collections can bring related questions together while retaining each question’s source.</p><div className="mt-5 grid gap-4 sm:grid-cols-2">{[
      {to:'/bank?origin=paper&exam_scope=mizoram-recruitment',label:'Past papers',title:'MPSC question bank',text:'Practise questions from source papers, with their original context and answer labels.'},
      {to:'/website-bank',label:'Community contributions',title:'Website question bank',text:'Explore learner-submitted questions that have passed publication review.'},
      {to:'/practice-sets',label:'Focused practice',title:'Practice sets',text:'Work through reviewed collections of related questions at your own pace.'},
      {to:'/exams',label:'Exam preparation',title:'Mock tests & papers',text:'Choose your exam to find its available mock tests, source papers and study plan.'},
      {to:'/important-days',label:'Dates & themes',title:'Important Days',text:'Study verified observances and annual themes alongside relevant questions.'},
      {to:'/revision',label:'Personal revision',title:'Revisit & remember',text:'Return to saved questions, mistakes and vocabulary when they are due.'},
    ].map(c=><Link key={c.to} to={c.to} className="ism-card-surface group rounded-[14px] border border-hairline bg-card p-5 hover:border-practice sm:p-6"><p className="font-mono text-[10px] uppercase tracking-wider text-practice-dark">{c.label}</p><h3 className="mt-3 font-display text-[28px] group-hover:text-link">{c.title}</h3><p className="mt-2 max-w-lg text-[14px] leading-relaxed text-secondary">{c.text}</p><span className="mt-4 inline-flex min-h-11 items-center gap-1 text-[13px] font-semibold text-link">Explore <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>)}</div></section>}
    {tab==='subjects'&&loading&&<p role="status" className="mt-5 text-sm text-muted">Loading subjects…</p>}{tab==='subjects'&&error&&<p role="alert" className="mt-5 text-sm text-mypick">{error}</p>}
    {tab==='subjects'&&<section aria-labelledby="direct-subjects" className="mt-7"><h2 id="direct-subjects" className="font-display text-[29px]">What would you like to study?</h2><p className="mt-2 text-[14px] text-secondary">Open a subject directly. Choose an exam or a narrower topic when you need it.</p><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{shelves.map((s,i)=><Link key={s.id} to={'/library/topics/'+s.id} className="ism-card-surface group min-w-0 rounded-[14px] border border-hairline bg-card p-5 hover:border-practice"><span className={'mb-4 block h-2 w-9 rounded-pill '+['bg-practice','bg-exams','bg-learn','bg-map'][i%4]}/><h3 className="font-display text-[25px] group-hover:text-link">{s.title}</h3><p className="mt-2 text-[13px] leading-relaxed text-secondary">{s.description}</p><p className="mt-4 font-mono text-[11px] text-muted">{s.questions.toLocaleString('en-IN')} questions</p><span className="mt-3 inline-flex items-center gap-1 text-[13px] font-semibold text-link">Practise · Browse <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>)}</div></section>}
    {tab==='tools'&&<>    <section className="mt-8" aria-labelledby="tools-heading"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Learning tools</div><h2 id="tools-heading" className="mt-1 font-display text-[29px]">Start with a module</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{FEATURED.map((item) => <Link key={item.title} to={item.href} className="ism-card-surface group flex min-h-[218px] flex-col rounded-[15px] border border-hairline bg-card p-5 hover:border-practice"><span className={`self-start rounded-pill px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide ${item.color}`}>{item.label}</span><h3 className="mt-4 font-display text-[25px] font-medium group-hover:text-link">{item.title}</h3><p className="mt-2 text-[13px] leading-relaxed text-secondary">{item.description}</p><span className="mt-auto inline-flex items-center gap-1 pt-4 text-[13px] font-semibold text-link">Open module <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></span></Link>)}</div>
    </section>

</>}
    {tab==='subjects'&&<details className="ism-card-surface mt-7 rounded-[14px] border border-hairline bg-card p-5"><summary className="min-h-11 cursor-pointer font-display text-[25px]">Browse all subject categories</summary><section aria-labelledby="subjects-heading"><div className="flex flex-wrap items-end justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Subject shelves</div><h2 id="subjects-heading" className="mt-1 font-display text-[29px]">All subject shelves</h2><p className="mt-1 text-[13px] text-secondary">Each subject opens its own topic browser and inline question practice.</p></div><Link to="/bank" className="text-[12px] font-semibold text-link underline">Full source archive →</Link></div>
      <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find a subject, for example General Knowledge" aria-label="Find a library subject" className="mt-4 h-11 w-full rounded-pill border border-hairline bg-paper px-4 text-[14px] placeholder:text-placeholder focus:border-practice focus:outline-none" />
      {error && <p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}</p>}
      {loading && <p className="mt-5 text-[13px] text-muted">Loading subjects…</p>}
      {!loading && !error && subjects.length === 0 && <p className="mt-5 text-[13px] text-muted">No subjects match that search.</p>}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{subjects.map((subject) => <Link key={subject.subject_id} to={`/library/subjects/${encodeURIComponent(subject.subject_id)}`} className="ism-card-surface group flex items-center justify-between gap-3 rounded-[12px] border border-hairline bg-card p-4 hover:border-practice"><div><h3 className="font-display text-[20px] font-medium group-hover:text-link">{subject.subject}</h3><p className="mt-1 font-mono text-[11px] text-muted">{subject.questions.toLocaleString('en-IN')} tagged questions</p></div><span className="text-[18px] text-link transition-transform duration-150 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden="true">↗</span></Link>)}</div>
    </section></details>}
  </div>
}
