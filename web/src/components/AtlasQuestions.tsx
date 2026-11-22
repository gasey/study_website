import {useEffect,useState} from 'react'
import {listQuestions,listCollections,type QuestionPage,type Collection} from '../lib/api'
import {atlasRead} from '../lib/atlas'
import {accountGeneration} from '../lib/accountContext'
import {useExamScope} from '../lib/examScope'
import type {Chapter} from '../atlas/types'
import QuestionCard from './QuestionCard'
const input='min-h-11 w-full rounded-lg border border-hairline bg-card px-3 text-sm'
export default function AtlasQuestions({chapter,initialLayer=''}:{chapter:Chapter;initialLayer?:string}){
 const scope=useExamScope(),[layer,setLayer]=useState(initialLayer),[exam,setExam]=useState(''),[exams,setExams]=useState<Collection[]>([]),[page,setPage]=useState(0),[data,setData]=useState<QuestionPage|null>(null),[bound,setBound]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;listCollections().then(r=>{if(live)setExams(r.filter(c=>c.kind==='exam'&&c.id!=='group-b'))}).catch(()=>{});return()=>{live=false}},[scope])
 useEffect(()=>{let live=true,sequence=0;const generation=accountGeneration(),valid=()=>live&&generation===accountGeneration();setData(null);setError('');setBound(false)
  async function load(){const run=++sequence;try{
   const binding=await atlasRead<{items:unknown[]}>('/atlas/chapters/'+encodeURIComponent(chapter.id)+'/bindings');if(!valid()||run!==sequence)return
   if(!binding.items.length){setBound(false);setData({items:[],total:0,limit:5,offset:0});setError('');return}
   const result=await listQuestions({atlas_chapter:chapter.id,atlas_layer:layer||undefined,collection_id:exam||undefined,exam_scope:scope,pool:'all',limit:5,offset:page*5});if(valid()&&run===sequence){setBound(true);setData(result);setError('')}
  }catch(e){if(valid()&&run===sequence){setData(null);setError((e as Error).message)}}}
  const refresh=()=>{if(document.visibilityState==='visible')void load()},reset=()=>{live=false;++sequence;setData(null);setError('Your account changed. Refresh this panel to continue.')}
  void load();const timer=window.setInterval(refresh,30000);window.addEventListener('focus',refresh);window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-auth-expired',reset)
  return()=>{live=false;++sequence;window.clearInterval(timer);window.removeEventListener('focus',refresh);window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-auth-expired',reset)}
 },[chapter.id,layer,exam,scope,page,retry])
 return <section aria-label="Asked from this map" className="mt-6 min-w-0 rounded-xl border border-hairline bg-canvas p-3 sm:p-5"><h3 className="font-display text-2xl">Asked from this map</h3><p className="mt-2 text-xs text-secondary">Real bank questions linked through editor-curated approved topics. Source: {scope==='all'?'all exam sources':'Mizoram recruitment papers'}. Questions in active assessments are omitted.</p><div className="my-3 grid gap-3 sm:grid-cols-2"><label className="text-sm">Map layer<select className={input} value={layer} onChange={e=>{setLayer(e.target.value);setPage(0)}}><option value="">Whole chapter</option>{chapter.layers.map(l=><option key={l.id} value={l.id}>{l.name}</option>)}</select></label><label className="text-sm">Exam<select className={input} value={exam} onChange={e=>{setExam(e.target.value);setPage(0)}}><option value="">All available papers</option>{exams.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label></div>
  {error?<p role="alert" className="break-words text-sm">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>:!data?<p role="status">Loading linked questions…</p>:!bound?<p className="text-sm text-secondary">No editor-curated topics are linked to this chapter yet.</p>:<><p className="mb-3 text-sm">{data.total} tagged questions available in this selection.</p>{data.items.length?data.items.map(q=><QuestionCard key={q.id} q={q}/>):<p className="text-sm text-secondary">No tagged questions are available for this selection. Choose another layer or exam, or return after your assessment.</p>}{data.total>5&&<nav aria-label="Atlas question pages" className="flex min-h-11 items-center justify-between gap-3"><button disabled={!page} className="min-h-11 underline disabled:opacity-40" onClick={()=>setPage(n=>n-1)}>Previous</button><span>{page+1} / {Math.ceil(data.total/5)}</span><button disabled={(page+1)*5>=data.total} className="min-h-11 underline disabled:opacity-40" onClick={()=>setPage(n=>n+1)}>Next</button></nav>}</>}
 </section>
}
