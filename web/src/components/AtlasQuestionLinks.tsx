import {lazy,Suspense,useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {atlasRead,atlasUrl,type AtlasLink} from '../lib/atlas'
import {useExamScope} from '../lib/examScope'
const Context=lazy(()=>import('./QuestionMapContext'))
export default function AtlasQuestionLinks({qid,links,context=false}:{qid:string;links?:AtlasLink[];context?:boolean}){
 const scope=useExamScope(),[items,setItems]=useState<AtlasLink[]>(links||[])
 useEffect(()=>{let active=true;setItems(links||[]);if(links===undefined)atlasRead<{items:AtlasLink[]}>('/atlas/questions/'+encodeURIComponent(qid)+'/links?exam_scope='+scope).then(r=>{if(active)setItems(r.items)}).catch(()=>{if(active)setItems([])});const reset=()=>{active=false;setItems([])};window.addEventListener('ism-auth-change',reset);return()=>{active=false;window.removeEventListener('ism-auth-change',reset)}},[qid,links,scope])
 if(!items.length)return null
 return <><nav aria-label="Related Atlas maps" className="flex flex-wrap gap-2">{items.map(e=><Link key={[e.chapter_id,e.layer_id,e.event_id].join(':')} to={atlasUrl(e)} className="inline-flex min-h-11 items-center break-words text-xs font-semibold text-map-dark underline">View on Atlas · {e.title}</Link>)}</nav>{context&&items.some(l=>l.subject==='geography')&&<Suspense fallback={<p>Loading map tool…</p>}><Context key={qid} qid={qid}/></Suspense>}</>
}
