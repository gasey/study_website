import AtlasDrills from '../components/AtlasDrills'
import {AtlasSources,AtlasChronicleLinks} from '../components/AtlasProvenance'
import AtlasQuestions from '../components/AtlasQuestions'
import {useEffect,useMemo,useRef,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import type {Feature,FeatureCollection} from 'geojson'
import type {Chapter,TimelineEvent} from './types'
import AtlasMap from './AtlasMap'
import type {AtlasEdit} from './AtlasMap'
const control='min-h-11 w-full rounded-lg border border-hairline bg-card px-3 text-sm'
export default function AtlasChapter({chapter,draft=false,edit,onView}:{chapter:Chapter;draft?:boolean;edit?:AtlasEdit;onView?:(view:Chapter['view'],layers:string[])=>void}) {
  const [featureQuery,setFeatureQuery]=useState('')
  const [params,setParams]=useSearchParams()
  const initialEvent=chapter.events?.find(e=>e.id===params.get('event'))||null
  const requestedLayer=chapter.layers.find(l=>l.id===params.get('layer'))?.id
  const defaults=()=>chapter.layers.filter(l=>l.defaultOn).map(l=>l.id)
  const initialLayers=()=>{const ids=new Set(defaults());if(initialEvent){for(const e of chapter.events||[]){e.showLayers?.forEach(id=>ids.add(id));e.hideLayers?.forEach(id=>ids.delete(id));if(e.id===initialEvent.id)break}}if(requestedLayer)ids.add(requestedLayer);return [...ids]}
  const [active,setActive]=useState(initialLayers),[focus,setFocus]=useState<Feature|null>(null),[event,setEvent]=useState<TimelineEvent|null>(initialEvent),[reset,setReset]=useState(0)
  const currentView=useRef(chapter.view),knownLayers=useRef(chapter.layers.map(l=>l.id))
  useEffect(()=>{const known=knownLayers.current;setActive(a=>[...new Set([...a.filter(id=>chapter.layers.some(l=>l.id===id)),...chapter.layers.filter(l=>!known.includes(l.id)&&l.defaultOn).map(l=>l.id)])]);knownLayers.current=chapter.layers.map(l=>l.id)},[chapter.layers])
  useEffect(()=>{onView?.(currentView.current,active)},[active.join(':')])
  const layers=chapter.layers.filter(l=>active.includes(l.id))
  const features=useMemo(()=>layers.flatMap(layer=>layer.kind==='vector'&&typeof layer.data!=='string'?(layer.data as FeatureCollection).features.map((feature,index)=>({id:`${layer.id}-${index}`,feature,label:String(feature.properties?.[layer.labelKey||'name']||layer.name)})):[]),[layers])
  function resetView(){const next=new URLSearchParams(params);next.delete('layer');next.delete('event');setParams(next);setFeatureQuery('');setActive(defaults());setFocus(null);setEvent(null);setReset(n=>n+1)}
  function timeline(e:TimelineEvent|null){setEvent(e);setFocus(null);setReset(n=>n+1);setActive(()=>{const ids=new Set(defaults());if(e){for(const entry of chapter.events||[]){entry.showLayers?.forEach(id=>ids.add(id));entry.hideLayers?.forEach(id=>ids.delete(id));if(entry.id===e.id)break}}return [...ids]})}
  return <section className="finna-atlas-chapter min-w-0" aria-labelledby="atlas-chapter-title">
    {draft&&<p className="mb-3 rounded-lg border border-hairline bg-canvas p-3 font-bold" role="status">DRAFT · Owner preview · Not published</p>}
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="atlas-chapter-title" className="font-display text-xl">{chapter.title}</h2><p className="finna-atlas-intro mt-1 max-w-3xl text-sm leading-relaxed text-secondary">{chapter.focus||chapter.summary}</p></div><button type="button" className="min-h-11 rounded-pill border border-hairline bg-card px-4 text-xs font-semibold" onClick={resetView}><span className="hidden sm:inline">Reset map &amp; layers</span><span className="sm:hidden">Reset</span></button></div>
    <div className="mt-4 grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_250px]">
      <div className="min-w-0"><AtlasMap edit={edit} onView={v=>{currentView.current=v;onView?.(v,active)}} chapter={chapter} layers={layers} view={event?.view||chapter.view} focus={focus} reset={reset} onFeature={setFocus}/>
        {focus&&<div aria-live="polite" className="mt-3 rounded-xl border border-hairline bg-card p-4"><p className="text-xs uppercase tracking-wide text-muted">Selected map feature</p><p className="mt-1 text-base font-semibold">{String(focus.properties?.name||focus.properties?.title||'Map feature')}</p>{focus.properties?.description&&<p className="mt-2 text-sm">{String(focus.properties.description)}</p>}</div>}
        {!!chapter.events?.length&&<div className="mt-4 rounded-xl border border-hairline bg-card p-4"><label className="text-sm font-semibold">Timeline<select className={`${control} mt-2`} value={event?.id||''} onChange={e=>timeline(chapter.events?.find(t=>t.id===e.target.value)||null)}><option value="">Chapter overview</option>{chapter.events.map(e=><option key={e.id} value={e.id}>{e.date} · {e.label}</option>)}</select></label>{event&&<p className="mt-3 text-sm leading-relaxed">{event.description}</p>}</div>}
      </div>
      <aside className="min-w-0 rounded-xl border border-hairline bg-card p-4"><h3 className="font-display text-lg">Map layers</h3><p className="mt-1 text-xs text-secondary">{active.length} of {chapter.layers.length} visible</p><div className="mt-3 space-y-1">{chapter.layers.map(layer=><label key={layer.id} className="flex min-h-11 cursor-pointer items-start gap-3 rounded-lg py-2 text-sm"><input className="mt-1 accent-[var(--finna-primary)]" type="checkbox" checked={active.includes(layer.id)} onChange={()=>setActive(ids=>ids.includes(layer.id)?ids.filter(id=>id!==layer.id):[...ids,layer.id])}/><span><span className="font-semibold">{layer.kind==='vector'&&<span aria-hidden="true" className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{backgroundColor:layer.style?.color||'#176f72'}}/>}{layer.name}</span>{layer.description&&<span className="mt-1 block text-xs leading-relaxed text-secondary">{layer.description}</span>}</span></label>)}</div>
      <Link className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-link underline" to={`/library/topics/${chapter.id.includes('mizoram')?'mizoram-gk':chapter.subject}`}>Practise {chapter.id.includes('mizoram')?'Mizoram':chapter.subject} questions →</Link><p className="text-xs leading-relaxed text-muted">Opens the subject question bank. Select your MPSC exam there.</p></aside>
    </div>
    <AtlasSources chapter={chapter}/>{!draft&&<AtlasChronicleLinks chapterId={chapter.id} eventId={event?.id}/>}
    {!draft&&<AtlasDrills chapter={chapter} layers={active}/>}
    {!draft&&<AtlasQuestions key={chapter.id} chapter={chapter} initialLayer={requestedLayer}/>}
    <div className="mt-5 grid items-start gap-4 md:grid-cols-2"><details className="rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer font-semibold">Places & features · {features.length}</summary><p className="mb-2 text-xs text-secondary">Select a name to focus the map. This list follows your visible layers.</p><input type="search" aria-label="Find a map feature" placeholder="Find a place or feature" value={featureQuery} onChange={e=>setFeatureQuery(e.target.value)} className={`${control} mb-2`}/>{!features.some(item=>item.label.toLocaleLowerCase().includes(featureQuery.toLocaleLowerCase()))&&<p className="py-3 text-sm text-secondary">No matching features in the visible layers.</p>}<ul className="max-h-80 overflow-auto">{features.filter(item=>item.label.toLocaleLowerCase().includes(featureQuery.toLocaleLowerCase())).map(item=><li key={item.id}><button className="min-h-11 w-full rounded-lg px-2 py-2 text-left text-sm hover:bg-canvas focus-visible:outline focus-visible:outline-2 focus-visible:outline-link" onClick={()=>setFocus(item.feature)}>{item.label}</button></li>)}</ul></details>
    <details className="rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer font-semibold">Chapter notes · {chapter.facts.length}</summary><p className="mb-3 text-xs text-muted">Chapter study notes; dated figures retain their stated reference year.</p><ul className="space-y-3 text-sm leading-relaxed">{chapter.facts.map(f=><li className="border-t border-hairline pt-3" key={f.id}>{f.text}</li>)}</ul></details></div>
  </section>
}
