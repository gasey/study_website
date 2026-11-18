import {lazy,Suspense,useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {listLibraryShelves,type LibraryShelf,listTaxonomy,type TaxonomyFacet} from '../lib/api'
import MaterialDiscovery from '../components/MaterialDiscovery'
const Materials=lazy(()=>import('./Materials'))
const VIEWS=[['subjects','Subjects'],['practice','Practice sets'],['reading','Reading'],['saved','Saved'],['tools','Modules']] as const
const TOOLS=[
 {title:'Atlas',href:'/atlas',label:'Interactive chapters and map layers'},
 {title:'Chronicle',href:'/chronicle',label:'Dates, events and linked questions'},
 {title:'Stats',href:'/stats',label:'India, global rankings and the Economic Survey'},
 {title:'Arithmetic',href:'/arithmetic',label:'Concepts, worked methods and practice'},
 {title:'English',href:'/english',label:'Grammar, comprehension and writing'},
 {title:'Reasoning',href:'/arithmetic?subject=reasoning-and-aptitude&view=practice',label:'Patterns, logic and aptitude'},
 {title:'Mizo',href:'/mizo',label:'Language, literature and culture'},
 {title:'Essay writing',href:'/essay',label:'Real prompts and private drafts'},
]
const PRACTICE=[
 {to:'/bank?origin=paper&exam_scope=mizoram-recruitment',title:'MPSC question bank',text:'Original papers, questions and clearly labelled answer sources.'},
 {to:'/website-bank',title:'Website question bank',text:'Published questions contributed by learners.'},
 {to:'/practice-sets',title:'Practice sets',text:'Reviewed collections for one focused study session.'},
 {to:'/tests',title:'Mock tests',text:'Shared tests, or build your own timed practice.'},
 {to:'/revise',title:'Revisit & remember',text:'Scheduled questions, mistakes and vocabulary.'},
]
export default function Library(){
 const [params,setParams]=useSearchParams(),[shelves,setShelves]=useState<LibraryShelf[]>([]),[facets,setFacets]=useState<TaxonomyFacet[]>([])
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[query,setQuery]=useState(''),[retry,setRetry]=useState(0)
 const tab=VIEWS.some(([id])=>id===params.get('library_view'))?params.get('library_view')!:'subjects'
 function setTab(value:string){setParams(p=>{const next=new URLSearchParams(p);next.set('library_view',value);for(const key of ['offset','q','access','sort','saved','collection_id','subject_id'])next.delete(key);return next})}
 useEffect(()=>{if(tab!=='subjects')return;let live=true;setLoading(true);setError('')
  Promise.allSettled([listLibraryShelves().then(rows=>{if(live)setShelves(rows)}),listTaxonomy('all',true).then(rows=>{if(live)setFacets(rows)})]).then(results=>{if(live){setLoading(false);if(results.some(r=>r.status==='rejected'))setError('Some subjects could not load. Please try again.')}})
  return()=>{live=false}
 },[tab,retry])
 const subjects=useMemo(()=>{const grouped=new Map<string,{id:string;title:string;questions:number}>();for(const f of facets){const old=grouped.get(f.subject_id);if(old)old.questions=f.subject_questions??old.questions+f.questions;else grouped.set(f.subject_id,{id:f.subject_id,title:f.subject,questions:f.subject_questions??f.questions})}return [...grouped.values()].sort((a,b)=>a.title.localeCompare(b.title)).filter(f=>f.title.toLowerCase().includes(query.toLowerCase()))},[facets,query])
 return <div className="finna-page" data-screen="library">
  <header className="finna-page-heading"><div><p className="finna-eyebrow text-learn-dark">Library</p><h1>{tab==='subjects'?'Study by subject':tab==='tools'?'Guided modules':tab==='reading'?'A good place to read':tab==='saved'?'Your saved library':'Focused practice'}</h1></div><nav aria-label="Library views" className="finna-segments">{VIEWS.map(([id,label])=><button key={id} type="button" aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</nav></header>
  {tab==='subjects'&&<>
   {loading&&<p role="status" className="mb-4 text-sm text-secondary">Loading subjects…</p>}
   {error&&<p role="alert" className="mb-4 rounded-xl border border-mypick bg-mypick-soft p-4 text-sm text-mypick">{error} <button onClick={()=>setRetry(n=>n+1)} className="min-h-11 font-bold underline">Try again</button></p>}
   <section aria-label="Subject library" className="finna-library-grid">{shelves.map(s=><Link key={s.id} to={'/library/topics/'+s.id}><h2>{s.title}</h2><p>{s.description}</p><strong>{s.questions.toLocaleString('en-IN')} questions →</strong></Link>)}</section>
   {!loading&&!error&&!shelves.length&&<section className="finna-card"><h2>Your subject library is getting ready</h2><p className="mt-2 text-sm text-secondary">Explore the modules below or browse all subject categories.</p></section>}
  </>}
  {(tab==='subjects'||tab==='tools')&&<section className="finna-tools" aria-labelledby="guided-tools"><h2 id="guided-tools">Guided modules and tools</h2><div>{TOOLS.map(t=><Link key={t.href} to={t.href}><h3>{t.title}</h3><p>{t.label}</p></Link>)}</div></section>}
  {tab==='subjects'&&<><div className="mt-5 grid items-start gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(250px,1fr)]"><MaterialDiscovery title="Reading" compact/><section className="finna-card mt-6"><div className="finna-section-top"><h2>Saved collections</h2><Link to="/library?library_view=saved">Open</Link></div><Link to="/revise" className="finna-plan-item"><span className="text-sm font-semibold">Revise questions & mistakes →</span></Link><Link to="/library?library_view=saved" className="finna-plan-item"><span className="text-sm font-semibold">Saved reading →</span></Link><Link to="/exams?exam_filter=saved" className="finna-plan-item"><span className="text-sm font-semibold">My exams →</span></Link></section></div>
   <details className="finna-card mt-5"><summary className="min-h-11 cursor-pointer py-2 text-base font-extrabold">Browse all subject categories</summary><label className="mt-3 block"><span className="sr-only">Find a library subject</span><input type="search" aria-label="Find a library subject" placeholder="Find a subject" value={query} onChange={e=>setQuery(e.target.value)} className="min-h-11 w-full rounded-xl border border-hairline bg-paper px-4 text-sm"/></label><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{subjects.map(s=><Link key={s.id} to={'/library/subjects/'+encodeURIComponent(s.id)} className="rounded-xl border border-hairline p-4 hover:border-learn"><h3 className="text-base font-extrabold">{s.title}</h3><p className="mt-1 text-xs text-secondary">{s.questions.toLocaleString('en-IN')} questions</p></Link>)}</div>{!loading&&!subjects.length&&<p className="py-4 text-sm text-secondary">No subjects match this search.</p>}</details>
  </>}
  {tab==='practice'&&<div className="finna-library-grid">{PRACTICE.map(item=><Link key={item.to} to={item.to}><h2>{item.title}</h2><p>{item.text}</p><strong>Explore →</strong></Link>)}</div>}
  {tab==='reading'&&<Suspense fallback={<p role="status">Loading reading…</p>}><Materials embedded/></Suspense>}
  {tab==='saved'&&<><section className="finna-card mb-5 flex flex-wrap items-center justify-between gap-4"><div><h2>Your saved questions</h2><p className="mt-2 text-sm text-secondary">Bookmarks are kept in your personal Desk.</p></div><Link className="finna-btn" to="/desk">Open saved questions →</Link></section><Suspense fallback={<p role="status">Loading saved materials…</p>}><Materials key="saved" embedded savedOnly/></Suspense></>}
 </div>
}
