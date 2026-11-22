import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {atlasRead,atlasUrl,type AtlasLink} from '../lib/atlas'
import type {Chapter} from '../atlas/types'
export function AtlasSources({chapter}:{chapter:Chapter}){
 return <details className="mt-4 min-w-0 rounded-xl border border-hairline bg-card p-4"><summary className="min-h-11 cursor-pointer font-semibold">Sources and map provenance · {chapter.sources?.length||0}</summary>{chapter.district&&<p className="my-2 text-sm">Mizoram district · {chapter.district}</p>}{!chapter.sources?.length?<p className="text-sm text-secondary">Current-site chapter content. No separate source or reuse review has been recorded here.</p>:<ul className="space-y-4">{chapter.sources.map(s=><li key={s.id} className="break-words border-t border-hairline pt-3 text-sm"><a className="text-link underline" href={s.url} target="_blank" rel="noreferrer">{s.title} ↗</a><p className="mt-1">{s.attribution}</p><p className="mt-1 text-xs text-secondary">Source checked {s.checked_on} · {s.reuse==='licensed'?'Licensed dataset':'Reference only; no reproduction permission recorded'}</p>{s.license_url&&<a className="inline-flex min-h-11 items-center text-link underline" href={s.license_url} target="_blank" rel="noreferrer">{s.license||'Reuse terms'} ↗</a>}<p className="text-xs text-secondary">{s.note}</p>{s.download_path&&/^\/maps\/[a-z0-9-]+\.(geojson|json)$/.test(s.download_path)&&<a className="inline-flex min-h-11 items-center text-link underline" href={s.download_path} download>Download the attributed data</a>}</li>)}</ul>}</details>
}
export function AtlasChronicleLinks({chapterId,eventId}:{chapterId:string;eventId?:string}){
 const [items,setItems]=useState<{event_id:string;entry_id:string;title:string}[]>([])
 useEffect(()=>{let live=true,serial=0;setItems([]);const load=()=>{const run=++serial;setItems([]);atlasRead<{items:typeof items}>('/atlas/chapters/'+encodeURIComponent(chapterId)+'/chronicle').then(r=>{if(live&&run===serial)setItems(r.items)}).catch(()=>{})};load();window.addEventListener('ism-auth-change',load);window.addEventListener('ism-content-change',load);return()=>{live=false;window.removeEventListener('ism-auth-change',load);window.removeEventListener('ism-content-change',load)}},[chapterId])
 const shown=items.filter(i=>!eventId||i.event_id===eventId)
 return shown.length?<nav aria-label="Related Chronicle entries" className="mt-3">{shown.map(i=><Link key={i.event_id} className="block min-h-11 py-2 text-sm text-link underline" to={'/chronicle?'+new URLSearchParams({view:'chronology',event:i.entry_id})}>Chronicle · {i.title} →</Link>)}</nav>:null
}
export function ChronicleAtlasLinks({entryId}:{entryId:string}){
 const [items,setItems]=useState<AtlasLink[]>([])
 useEffect(()=>{let live=true,serial=0;const load=()=>{const run=++serial;setItems([]);atlasRead<{items:AtlasLink[]}>('/atlas/chronicle/'+encodeURIComponent(entryId)+'/links').then(r=>{if(live&&run===serial)setItems(r.items)}).catch(()=>{})};load();window.addEventListener('ism-auth-change',load);window.addEventListener('ism-content-change',load);return()=>{live=false;window.removeEventListener('ism-auth-change',load);window.removeEventListener('ism-content-change',load)}},[entryId])
 return items.length?<nav aria-label="Related Atlas chapters" className="my-3">{items.map(i=><Link key={i.chapter_id+':'+i.event_id} className="block min-h-11 py-2 text-sm text-link underline" to={atlasUrl(i)}>View on Atlas · {i.title} →</Link>)}</nav>:null
}
