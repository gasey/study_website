import {lazy,Suspense} from 'react'
const Materials=lazy(()=>import('./Materials'))
import LearningOverview from '../components/LearningOverview'
import { useEffect, useMemo, useState } from 'react'
import { Link,useSearchParams } from 'react-router-dom'
import { listLibraryShelves, type LibraryShelf, listTaxonomy, type TaxonomyFacet } from '../lib/api'

const FEATURED = [
  { title: 'Interactive Atlas', href: '/atlas', label: 'Maps · places · layers', description: 'Explore Mizoram, India and world geography, historical routes and polity maps.', color: 'bg-[#E3F1EF] text-[#176F72]' },
  { title: 'Arithmetic', href: '/arithmetic', label: 'Learn · practise · papers', description: 'Build a method, then use real arithmetic questions and source papers.', color: 'bg-[#E7EDF9] text-[#28468B]' },
  { title: 'Reasoning', href: '/arithmetic?subject=reasoning-and-aptitude&view=practice', label: 'Patterns · logic · aptitude', description: 'Work through reasoning concepts and practise with tagged questions.', color: 'bg-[#E7EDF9] text-[#28468B]' },
  { title: 'English', href: '/english', label: 'Grammar · comprehension · writing', description: 'Learn, practise and browse English papers from one module.', color: 'bg-[#E9F1E5] text-[#315D39]' },
  { title: 'Vocabulary helper', href: '/vocabulary', label: 'Recall · spaced review', description: 'Test words from real questions and revisit them when due.', color: 'bg-[#F1EBF7] text-[#62418B]' },
  { title: 'Mizo', href: '/mizo', label: 'Language · literature · culture', description: 'Read and practise Mizo questions by topic and source paper.', color: 'bg-[#E3F1EF] text-[#176F72]' },
  { title: 'Essay writing', href: '/essay', label: 'Prompts · private drafts', description: 'Write from real paper prompts and save drafts for later revision.', color: 'bg-[#F3EAD9] text-[#8C5C16]' },
]

const HIGHLIGHTS = ['gk-gs', 'mizo', 'science', 'mathematics', 'reasoning-and-aptitude', 'english']

export default function Library() {
  const [shelves,setShelves]=useState<LibraryShelf[]>([])
  const [params,setParams]=useSearchParams();const tab=params.get('library_view')||'subjects';function setTab(value:string){setParams(p=>{const next=new URLSearchParams(p);next.set('library_view',value);next.delete('offset');return next})}
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
      <div><h1 className="font-display text-[clamp(36px,5vw,54px)] font-medium leading-[1.04]">Study library</h1><p className="mt-3 max-w-[700px] text-[16px] leading-relaxed text-secondary">Choose a subject or tool and stay in its learning flow. Questions come from the shared bank, with sources and answer labels shown where you practise.</p></div>
      <Link to="/exams" className="rounded-pill border border-hairline bg-card px-4 py-2.5 text-[13px] font-semibold hover:border-ink">Looking for an exam? →</Link>
    </div>

    <LearningOverview/>
    <nav aria-label="Library views" className="mt-6 flex flex-wrap gap-2">{(['subjects','tools','saved'] as const).map(t=><button key={t} aria-pressed={tab===t} onClick={()=>setTab(t)} className={'min-h-11 rounded-pill px-5 text-[13px] font-semibold '+(tab===t?'bg-ink text-paper':'border border-hairline bg-card')}>{t==='subjects'?'Subjects':t==='tools'?'Modules & tools':'Saved materials'}</button>)}</nav>
    {tab==='saved'&&<Suspense fallback={<p className="mt-5 text-muted">Loading saved materials…</p>}><Materials embedded savedOnly/></Suspense>}
    {tab==='subjects'&&<section aria-labelledby="direct-subjects" className="mt-7"><h2 id="direct-subjects" className="font-display text-[29px]">What would you like to study?</h2><p className="mt-2 text-[14px] text-secondary">Open a subject directly. Choose an exam or a narrower topic when you need it.</p><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{shelves.map((s,i)=><Link key={s.id} to={'/library/topics/'+s.id} className="group min-w-0 rounded-[14px] border border-hairline bg-card p-5 transition hover:border-ink"><span className={'mb-4 block h-2 w-9 rounded-pill '+['bg-[#7097B6]','bg-[#BA8A59]','bg-[#7C87B7]','bg-[#76986A]'][i%4]}/><h3 className="font-display text-[25px] group-hover:underline">{s.title}</h3><p className="mt-2 text-[13px] leading-relaxed text-secondary">{s.description}</p><p className="mt-4 font-mono text-[11px] text-muted">{s.questions.toLocaleString('en-IN')} questions</p><span className="mt-3 inline-block text-[13px] font-semibold text-link">Practise · Browse →</span></Link>)}</div><div className="mt-4 flex flex-wrap gap-2">{[{id:'gk-gs',label:'General Knowledge & Studies (GK/GS)'},{id:'english',label:'English'},{id:'mizo',label:'Mizo'},{id:'mathematics',label:'Mathematics'},{id:'reasoning-and-aptitude',label:'Reasoning'}].map(s=><Link key={s.id} to={'/library/subjects/'+s.id} className="rounded-pill border border-hairline bg-card px-4 py-3 text-[13px] font-semibold">{s.label} →</Link>)}</div></section>}
    {tab==='tools'&&<>    <section className="mt-8" aria-labelledby="tools-heading"><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Learning tools</div><h2 id="tools-heading" className="mt-1 font-display text-[29px]">Start with a module</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{FEATURED.map((item) => <Link key={item.title} to={item.href} className="group flex min-h-[218px] flex-col rounded-[15px] border border-hairline bg-card p-5 transition hover:-translate-y-0.5 hover:border-ink hover:shadow-[0_10px_24px_rgba(29,27,24,.08)]"><span className={`self-start rounded-pill px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide ${item.color}`}>{item.label}</span><h3 className="mt-4 font-display text-[25px] font-medium group-hover:underline">{item.title}</h3><p className="mt-2 text-[13px] leading-relaxed text-secondary">{item.description}</p><span className="mt-auto pt-4 text-[13px] font-semibold text-link">Open module →</span></Link>)}</div>
    </section>

</>}
    {tab==='subjects'&&<section className="mt-11" aria-labelledby="subjects-heading"><div className="flex flex-wrap items-end justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Subject shelves</div><h2 id="subjects-heading" className="mt-1 font-display text-[29px]">All subject shelves</h2><p className="mt-1 text-[13px] text-secondary">Each subject opens its own topic browser and inline question practice.</p></div><Link to="/bank" className="text-[12px] font-semibold text-link underline">Full source archive →</Link></div>
      <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find a subject, for example General Knowledge" aria-label="Find a library subject" className="mt-4 h-11 w-full rounded-pill border border-hairline bg-card px-4 text-[14px] placeholder:text-placeholder focus:border-ink focus:outline-none" />
      {error && <p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}</p>}
      {loading && <p className="mt-5 text-[13px] text-muted">Loading subjects…</p>}
      {!loading && !error && subjects.length === 0 && <p className="mt-5 text-[13px] text-muted">No subjects match that search.</p>}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{subjects.map((subject) => <Link key={subject.subject_id} to={`/library/subjects/${encodeURIComponent(subject.subject_id)}`} className="group flex items-center justify-between gap-3 rounded-[12px] border border-hairline bg-card p-4 transition hover:border-ink hover:shadow-[0_6px_18px_rgba(29,27,24,.07)]"><div><h3 className="font-display text-[20px] font-medium group-hover:underline">{subject.subject}</h3><p className="mt-1 font-mono text-[11px] text-muted">{subject.questions.toLocaleString('en-IN')} tagged questions</p></div><span className="text-[18px] text-link" aria-hidden="true">↗</span></Link>)}</div>
    </section>}
  </div>
}
