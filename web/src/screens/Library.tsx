import {lazy,Suspense,useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {listLibraryShelves,type LibraryShelf,listTaxonomy,type TaxonomyFacet} from '../lib/api'
import {SITE_MAP,destinationPath} from '../lib/siteMap'
import MaterialDiscovery from '../components/MaterialDiscovery'
const Materials=lazy(()=>import('./Materials'))
const VIEWS=[['subjects','Subjects'],['reading','From the community'],['saved','Saved']] as const
const SUBJECT_TOOLS=SITE_MAP.filter(d=>['atlas','chronicle','guides','practice','revise','bank'].includes(d.id))
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
  <header className="finna-page-heading"><div><p className="finna-eyebrow text-learn-dark">Subjects</p><h1>{tab==='subjects'?'Study by subject':tab==='reading'?'From the community':'Your saved library'}</h1></div><nav aria-label="Library views" className="finna-segments">{VIEWS.map(([id,label])=><button key={id} type="button" aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</nav></header>
  {tab==='subjects'&&<>
   {loading&&<p role="status" className="mb-4 text-sm text-secondary">Loading subjects…</p>}
   {error&&<p role="alert" className="mb-4 rounded-xl border border-mypick bg-mypick-soft p-4 text-sm text-mypick">{error} <button onClick={()=>setRetry(n=>n+1)} className="min-h-11 font-bold underline">Try again</button></p>}
   <section aria-label="Subject library" className="finna-library-grid">{shelves.map(s=><Link key={s.id} to={'/library/topics/'+s.id}><h2>{s.title}</h2><p>{s.description}</p><strong>{s.questions.toLocaleString('en-IN')} questions →</strong></Link>)}</section>
   {!loading&&!error&&!shelves.length&&<section className="finna-card"><h2>Your subject library is getting ready</h2><p className="mt-2 text-sm text-secondary">Browse all subject categories below or open the index.</p></section>}
   <section className="finna-tools" aria-labelledby="guided-tools"><h2 id="guided-tools">Related surfaces</h2><div>{SUBJECT_TOOLS.map(t=><Link key={t.id} to={t.path}><h3>{t.label}</h3><p>{t.blurb}</p></Link>)}</div></section>
   <div className="mt-5 grid items-start gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(250px,1fr)]"><MaterialDiscovery title="From the community" compact/><section className="finna-card mt-6"><div className="finna-section-top"><h2>Saved</h2><Link to={destinationPath('desk')}>Desk</Link></div><Link to={destinationPath('revise')} className="finna-plan-item"><span className="text-sm font-semibold">Revise questions &amp; mistakes →</span></Link><Link to={destinationPath('exams')} className="finna-plan-item"><span className="text-sm font-semibold">My exams →</span></Link></section></div>
   <details className="finna-card mt-5"><summary className="min-h-11 cursor-pointer py-2 text-base font-bold">Browse all subject categories</summary><label className="mt-3 block"><span className="sr-only">Find a library subject</span><input type="search" aria-label="Find a library subject" placeholder="Find a subject" value={query} onChange={e=>setQuery(e.target.value)} className="min-h-11 w-full rounded-xl border border-hairline bg-paper px-4 text-sm"/></label><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{subjects.map(s=><Link key={s.id} to={'/library/subjects/'+encodeURIComponent(s.id)} className="rounded-xl border border-hairline p-4 hover:border-learn"><h3 className="text-base font-bold">{s.title}</h3><p className="mt-1 text-xs text-secondary">{s.questions.toLocaleString('en-IN')} questions</p></Link>)}</div>{!loading&&!subjects.length&&<p className="py-4 text-sm text-secondary">No subjects match this search.</p>}</details>
  </>}
  {tab==='reading'&&<Suspense fallback={<p role="status">Loading community materials…</p>}><Materials embedded/></Suspense>}
  {tab==='saved'&&<><section className="finna-card mb-5 flex flex-wrap items-center justify-between gap-4"><div><h2>Your saved questions</h2><p className="mt-2 text-sm text-secondary">Bookmarks are kept in your personal Desk.</p></div><Link className="finna-btn" to={destinationPath('desk')}>Open saved questions →</Link></section><Suspense fallback={<p role="status">Loading saved materials…</p>}><Materials key="saved" embedded savedOnly/></Suspense></>}
 </div>
}
