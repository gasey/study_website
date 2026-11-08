import {useMemo,useState} from 'react'
import type {TaxonomyNode} from '../lib/review'
import {learningChoices,learningPathLabel,type Classification} from '../lib/learningTaxonomy'
const BUTTON='min-h-11 rounded-lg border border-hairline px-3 py-2 text-left text-[13px] disabled:opacity-40'
export function taxonomyPath(node:TaxonomyNode,nodes:TaxonomyNode[]):Classification{
 const parent=nodes.find(n=>n.id===node.parent_id)
 return node.level==='subject'?{subject_id:node.id,topic_id:null,subtopic_id:null}:node.level==='topic'?{subject_id:node.parent_id!,topic_id:node.id,subtopic_id:null}:{subject_id:parent?.parent_id||'',topic_id:parent?.id,subtopic_id:node.id}
}
export function pathLabel(path:Classification,nodes:TaxonomyNode[]){return learningPathLabel(path,nodes)||'No subject'}
export default function SearchableTaxonomyPicker({value,nodes,onChange,label='Choose learning tags'}:{value:Classification;nodes:TaxonomyNode[];onChange:(p:Classification)=>void;label?:string}){
 const [search,setSearch]=useState(''),[open,setOpen]=useState(!value.subject_id),[page,setPage]=useState(0)
 const choices=useMemo(()=>learningChoices(nodes,value.subject_id),[nodes,value.subject_id])
 const matches=choices.filter(n=>search.trim()?search.toLowerCase().split(/\s+/).every(word=>n.search.includes(word)):!n.path.topic_id)
 const pages=Math.ceil(matches.length/12),current=Math.min(page,Math.max(0,pages-1))
 return <div className="min-w-0"><p className="text-[13px] font-semibold">{label}</p><button type="button" className={BUTTON+' mt-2 w-full break-words bg-paper'} aria-expanded={open} onClick={()=>setOpen(v=>!v)}>{pathLabel(value,nodes)} · Change</button>{open&&<div className="mt-2 rounded-lg border border-hairline p-3"><label className="block text-[12px]">Search subjects, topics or subtopics<input type="search" value={search} onChange={e=>{setSearch(e.target.value);setPage(0)}} className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-card px-3 text-[16px]" placeholder="For example: Geography rivers"/></label><div className="mt-2 grid gap-1">{matches.slice(current*12,current*12+12).map(n=><button key={n.id} type="button" className={BUTTON+' break-words hover:bg-paper'} onClick={()=>{onChange(n.path);setOpen(false);setSearch('');setPage(0)}}>{n.label}{!n.path.topic_id?' · Subject only':''}</button>)}</div>{!matches.length&&<p className="py-3 text-[13px]">No matching registered path.</p>}{pages>1&&<div className="mt-2 flex flex-wrap items-center justify-between gap-2"><button type="button" disabled={!current} className={BUTTON} onClick={()=>setPage(current-1)}>Previous</button><span className="text-[12px]">{current+1} / {pages}</span><button type="button" disabled={current+1>=pages} className={BUTTON} onClick={()=>setPage(current+1)}>More paths</button></div>}<p className="mt-2 text-[12px] text-secondary">GK/GS combines shared learning areas while keeping each stored path. Choose a subject alone when a narrower topic is not supported by the question.</p></div>}</div>
}
