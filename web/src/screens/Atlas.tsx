import {useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import type {Feature,FeatureCollection} from 'geojson'
import {chapters} from '../atlas/data'
import type {Chapter,TimelineEvent} from '../atlas/types'
import AtlasMap from '../atlas/AtlasMap'

const subjects=[{id:'geography',title:'Geography'},{id:'history',title:'History'},{id:'polity',title:'Polity'}]
const control='min-h-11 w-full rounded-lg border border-hairline bg-card px-3 text-[14px]'
export default function Atlas() {
  const [params,setParams]=useSearchParams()
  const chapter=chapters.find(c=>c.id===params.get('chapter'))||chapters.find(c=>c.unit==='Mizoram')||chapters.find(c=>c.id.includes('mizoram'))||chapters[0]
  function select(id:string){setParams({chapter:id})}
  return <main className="mx-auto max-w-shell pb-24 pt-6">
    <nav aria-label="Breadcrumb" className="mb-4 text-[12px] text-secondary"><Link className="underline" to="/library?library_view=tools">Study library</Link><span aria-hidden="true"> / </span>Interactive Atlas</nav>
    <div className="flex flex-wrap items-end justify-between gap-4 border-b border-hairline pb-5"><div><p className="font-mono text-[10px] uppercase tracking-widest text-exams-dark">MPSC learning tools</p><h1 className="mt-1 font-display text-[38px]">Interactive Atlas</h1><p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-secondary">Explore places, rivers, historical routes and regions. Choose a chapter, then turn its study layers on or off.</p></div><span className="rounded-pill border border-hairline bg-card px-3 py-2 text-[12px]">{chapters.length} map chapters</span></div>
    <div className="mt-5 grid gap-3 sm:grid-cols-[220px_minmax(0,1fr)]"><label className="text-[12px] font-semibold">Subject<select className={`${control} mt-1`} value={chapter.subject} onChange={e=>select(chapters.find(c=>c.subject===e.target.value)!.id)}>{subjects.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label><label className="text-[12px] font-semibold">Map chapter<select className={`${control} mt-1`} value={chapter.id} onChange={e=>select(e.target.value)}>{chapters.filter(c=>c.subject===chapter.subject).map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label></div>
    <ChapterView key={chapter.id} chapter={chapter}/>
  </main>
}
function ChapterView({chapter}:{chapter:Chapter}) {
  const [featureQuery,setFeatureQuery]=useState('')
  const defaults=()=>chapter.layers.filter(l=>l.defaultOn).map(l=>l.id)
  const [active,setActive]=useState(defaults),[focus,setFocus]=useState<Feature|null>(null),[event,setEvent]=useState<TimelineEvent|null>(null),[reset,setReset]=useState(0)
  const layers=chapter.layers.filter(l=>active.includes(l.id))
  const features=useMemo(()=>layers.flatMap(layer=>layer.kind==='vector'&&typeof layer.data!=='string'?(layer.data as FeatureCollection).features.map((feature,index)=>({id:`${layer.id}-${index}`,feature,label:String(feature.properties?.[layer.labelKey||'name']||layer.name)})):[]),[layers])
  function resetView(){setFeatureQuery('');setActive(defaults());setFocus(null);setEvent(null);setReset(n=>n+1)}
  function timeline(e:TimelineEvent|null){setEvent(e);setFocus(null);setReset(n=>n+1);setActive(()=>{const ids=new Set(defaults());if(e){for(const entry of chapter.events||[]){entry.showLayers?.forEach(id=>ids.add(id));entry.hideLayers?.forEach(id=>ids.delete(id));if(entry.id===e.id)break}}return [...ids]})}
  return <section className="mt-6" aria-labelledby="atlas-chapter-title">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="atlas-chapter-title" className="font-display text-[28px]">{chapter.title}</h2><p className="mt-1 max-w-3xl text-[14px] leading-relaxed text-secondary">{chapter.focus||chapter.summary}</p></div><button type="button" className="min-h-11 rounded-pill border border-hairline bg-card px-4 text-[12px] font-semibold" onClick={resetView}>Reset map & layers</button></div>
    <div className="mt-4 grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div className="min-w-0"><AtlasMap chapter={chapter} layers={layers} view={event?.view||chapter.view} focus={focus} reset={reset} onFeature={setFocus}/>
        {focus&&<div aria-live="polite" className="mt-3 rounded-xl border border-hairline bg-card p-4"><p className="text-[11px] uppercase tracking-wide text-muted">Selected map feature</p><p className="mt-1 text-[15px] font-semibold">{String(focus.properties?.name||focus.properties?.title||'Map feature')}</p>{focus.properties?.description&&<p className="mt-2 text-[13px]">{String(focus.properties.description)}</p>}</div>}
        {!!chapter.events?.length&&<div className="mt-4 rounded-xl border border-hairline bg-card p-4"><label className="text-[13px] font-semibold">Timeline<select className={`${control} mt-2`} value={event?.id||''} onChange={e=>timeline(chapter.events?.find(t=>t.id===e.target.value)||null)}><option value="">Chapter overview</option>{chapter.events.map(e=><option key={e.id} value={e.id}>{e.date} · {e.label}</option>)}</select></label>{event&&<p className="mt-3 text-[14px] leading-relaxed">{event.description}</p>}</div>}
      </div>
      <aside className="min-w-0 rounded-xl border border-hairline bg-card p-4"><h3 className="font-display text-[22px]">Map layers</h3><p className="mt-1 text-[12px] text-secondary">{active.length} of {chapter.layers.length} visible</p><div className="mt-3 space-y-1">{chapter.layers.map(layer=><label key={layer.id} className="flex min-h-11 cursor-pointer items-start gap-3 rounded-lg py-2 text-[13px]"><input className="mt-1" type="checkbox" checked={active.includes(layer.id)} onChange={()=>setActive(ids=>ids.includes(layer.id)?ids.filter(id=>id!==layer.id):[...ids,layer.id])}/><span><span className="font-semibold">{layer.kind==='vector'&&<span aria-hidden="true" className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{backgroundColor:layer.style?.color||'#176f72'}}/>}{layer.name}</span>{layer.description&&<span className="mt-1 block text-[12px] leading-relaxed text-secondary">{layer.description}</span>}</span></label>)}</div>
      <Link className="mt-4 inline-flex min-h-11 items-center text-[13px] font-semibold text-link underline" to={`/library/topics/${chapter.id.includes('mizoram')?'mizoram-gk':chapter.subject}`}>Practise {chapter.id.includes('mizoram')?'Mizoram':chapter.subject} questions →</Link><p className="text-[11px] leading-relaxed text-muted">Opens the subject question bank. Select your MPSC exam there.</p></aside>
    </div>
    <div className="mt-5 grid items-start gap-4 md:grid-cols-2"><details className="rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer font-semibold">Places & features · {features.length}</summary><p className="mb-2 text-[12px] text-secondary">Select a name to focus the map. This list follows your visible layers.</p><input type="search" aria-label="Find a map feature" placeholder="Find a place or feature" value={featureQuery} onChange={e=>setFeatureQuery(e.target.value)} className={`${control} mb-2`}/>{!features.some(item=>item.label.toLocaleLowerCase().includes(featureQuery.toLocaleLowerCase()))&&<p className="py-3 text-[13px] text-secondary">No matching features in the visible layers.</p>}<ul className="max-h-80 overflow-auto">{features.filter(item=>item.label.toLocaleLowerCase().includes(featureQuery.toLocaleLowerCase())).map(item=><li key={item.id}><button className="min-h-11 w-full rounded-lg px-2 py-2 text-left text-[13px] hover:bg-canvas focus-visible:outline focus-visible:outline-2 focus-visible:outline-link" onClick={()=>setFocus(item.feature)}>{item.label}</button></li>)}</ul></details>
    <details className="rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer font-semibold">Chapter notes · {chapter.facts.length}</summary><p className="mb-3 text-[12px] text-muted">Restored study notes from the original atlas; dated figures retain their stated reference year.</p><ul className="space-y-3 text-[14px] leading-relaxed">{chapter.facts.map(f=><li className="border-t border-hairline pt-3" key={f.id}>{f.text}</li>)}</ul></details></div>
  </section>
}
