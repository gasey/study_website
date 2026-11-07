import {UserAvatar} from './AvatarArt'
import {useEffect,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {contentRequest,type MaterialItem} from '../lib/materials'

export function materialLink(id:string){return '/materials/'+encodeURIComponent(id)+(id==='cms-paid-demo'?'?preview=true':'')}
export function MaterialCard({item:m}:{item:MaterialItem}){
 const location=useLocation();const params=new URLSearchParams(location.search);params.set('read_material',m.id);if(m.id==='cms-paid-demo')params.set('material_preview','true');else params.delete('material_preview');const readerURL=location.pathname+'?'+params.toString()+location.hash
 return <article className="flex min-w-0 flex-col rounded-[14px] border border-hairline bg-card p-5 transition hover:border-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-link">
  <div className="flex flex-wrap gap-2 font-mono text-[10px] uppercase text-muted"><span>{m.payload.kind}</span><span>· {m.payload.access==='paid-preview'?'Paid demo':m.payload.access==='pro'?'Pro members':'Free'}</span></div>
  <h3 className="mt-3 break-words font-display text-[25px] leading-tight"><Link to={readerURL} state={{...location.state,materialReaderFrom:location.pathname+location.search+location.hash}} preventScrollReset className="hover:text-link">{m.payload.title}</Link></h3><p className="mt-3 line-clamp-3 break-words text-[14px] leading-relaxed text-secondary">{m.payload.summary}</p>
  <div className="mt-4 flex flex-wrap gap-1.5">{m.payload.tags.map(t=><span key={t} className="max-w-full break-words rounded-pill bg-paper px-2 py-1 text-[10px]">{t}</span>)}</div>
  <div className="mt-auto flex flex-wrap justify-between gap-2 pt-5 text-[11px] text-muted"><span className="inline-flex items-center gap-2"><UserAvatar look={m.avatar} initials={m.author} size={24}/>{m.creator_public?<Link to={'/creators/'+encodeURIComponent(m.author_id)} className="break-words text-link underline">{m.author}</Link>:<span className="break-words">{m.author}</span>}</span><span>▲ {m.helpful} · {m.studied} studied</span></div>
 </article>
}

/** Only approved publication metadata. No lesson bodies or question-bank scans. */
export default function MaterialDiscovery({collectionId,subjectId,title='From the community',compact=false,hideEmpty=false}:{collectionId?:string;subjectId?:string;title?:string;compact?:boolean;hideEmpty?:boolean}){
 const [expanded,setExpanded]=useState(false),[offset,setOffset]=useState(0)
 const [data,setData]=useState<{items:MaterialItem[];total:number}|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 const context=new URLSearchParams();if(collectionId)context.set('collection_id',collectionId);if(subjectId)context.set('subject_id',subjectId)
 const query=context.toString(),key=query+':'+retry+':'+expanded+':'+offset
 const [loadedKey,setLoadedKey]=useState('')
 useEffect(()=>{let live=true;setError('');setData(null);contentRequest<{items:MaterialItem[];total:number}>('/materials?'+query+(query?'&':'')+'sort=helpful&limit='+(expanded?12:3)+'&offset='+offset).then(r=>{if(live){setData(r);setLoadedKey(key)}}).catch(e=>{if(live){setError(e.message);setLoadedKey(key)}});return()=>{live=false}},[query,key])
 const current=loadedKey===key,items=current?data?.items:null

 if(hideEmpty&&(!current&&!error||current&&data?.total===0))return null

 return <section aria-label={title} className="mt-6 min-w-0 rounded-[14px] border border-[#DDD0E8] bg-[#F6F0FA] p-4 sm:p-5">
  <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-widest text-[#5E2F98]">Community materials</div><h2 className="mt-1 font-display text-[27px] leading-tight">{title}</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">Published notes and lessons · helpful votes reflect reader feedback.</p></div><button type="button" onClick={()=>{setExpanded(v=>!v);setOffset(0)}} aria-expanded={expanded} className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link">{expanded?'Show highlights':'View all here'} →</button></div>
  {(!current||!data&&!error)&&<p role="status" className="mt-4 text-[13px] text-muted">Loading study materials…</p>}
  {current&&error&&<p role="alert" className="mt-4 text-[13px] text-secondary">Materials couldn’t load. <button onClick={()=>setRetry(n=>n+1)} className="min-h-11 font-semibold text-link underline">Try again</button></p>}
  {items&&items.length>0&&<div className={'mt-4 grid min-w-0 gap-3 '+(compact?'':'md:grid-cols-3')}>{items.map(m=><MaterialCard key={m.id} item={m}/>)}</div>}
  {expanded&&current&&data&&data.total>12&&<nav aria-label="Related material pages" className="mt-4 flex items-center justify-between gap-3 text-[13px]"><button type="button" disabled={!offset} onClick={()=>setOffset(n=>Math.max(0,n-12))} className="min-h-11 underline disabled:opacity-40">Previous</button><span>{offset+1}–{Math.min(offset+12,data.total)} of {data.total}</span><button type="button" disabled={offset+12>=data.total} onClick={()=>setOffset(n=>n+12)} className="min-h-11 underline disabled:opacity-40">Next</button></nav>}
  {items?.length===0&&<div className="mt-4 rounded-[10px] border border-hairline bg-card p-4"><p className="text-[14px] text-secondary">{collectionId?'No community materials have been published for this exam yet.':subjectId?'No community materials have been published for this subject yet.':'No community materials have been published yet.'}</p><Link to={'/studio/new'+(query?'?'+query:'')} className="mt-2 inline-flex min-h-11 items-center text-[13px] font-semibold text-link">Create a study note →</Link></div>}
 </section>
}
