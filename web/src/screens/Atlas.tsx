import {useEffect,useState} from 'react'
import {Link,useNavigate,useParams,useSearchParams} from 'react-router-dom'
import {atlasAccount,atlasRead} from '../lib/atlas'
import type {Chapter} from '../atlas/types'
import AtlasChapter from '../atlas/AtlasChapter'

const subjects=[{id:'geography',title:'Geography'},{id:'history',title:'History'},{id:'polity',title:'Polity'}]
const control='min-h-11 w-full rounded-lg border border-hairline bg-card px-3 text-sm'
export default function Atlas() {
  const {chapter:chapterParam}=useParams()
  const navigate=useNavigate()
  const [params,setParams]=useSearchParams()
  const [exam,setExam]=useState<{id:string;title:string}|null>(null),[ordering,setOrdering]=useState('exam')
  const [explored,setExplored]=useState<string[]>([])
  useEffect(()=>{let live=true,serial=0;const load=()=>{const run=++serial;return atlasAccount<{items:{chapter_id:string;explored:boolean}[]}>('/atlas/me/progress').then(r=>{if(live&&run===serial)setExplored(r.items.filter(i=>i.explored).map(i=>i.chapter_id))}).catch(()=>{if(live&&run===serial)setExplored([])})};void load();window.addEventListener('ism-progress-change',load);const reset=()=>{setExplored([]);void load()};window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-auth-expired',reset);return()=>{live=false;window.removeEventListener('ism-progress-change',load);window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-auth-expired',reset)}},[])
  const [chapters,setChapters]=useState<{id:string;title:string;subject:string;unit?:string;source_sha256:string;exam_relevant?:boolean}[]>([]),[chapter,setChapter]=useState<Chapter|null>(null),[error,setError]=useState(''),[catalogError,setCatalogError]=useState(''),[loaded,setLoaded]=useState(false),[retry,setRetry]=useState(0)
  const selected=chapterParam||params.get('chapter')||chapters.find(c=>c.id.includes('mizoram'))?.id||chapters[0]?.id
  useEffect(()=>{let live=true,serial=0;const load=()=>{const run=++serial;return atlasAccount<{items:typeof chapters;exam:{id:string;title:string}|null}>('/atlas/me/index').catch(()=>atlasRead<{items:typeof chapters}>('/atlas/chapters').then(r=>({...r,exam:null}))).then(r=>{if(live&&run===serial){setChapters(r.items);setExam(r.exam);setCatalogError('');setLoaded(true)}}).catch(e=>{if(live&&run===serial){setChapters([]);setChapter(null);setCatalogError(e.message);setLoaded(true)}})};void load();const timer=window.setInterval(()=>{if(document.visibilityState==='visible')void load()},30000);window.addEventListener('focus',load);const reset=()=>{setExam(null);setChapters([]);void load()};window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-content-change',load);return()=>{live=false;clearInterval(timer);window.removeEventListener('focus',load);window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-content-change',load)}},[retry])
  const hash=chapters.find(c=>c.id===selected)?.source_sha256
  useEffect(()=>{let live=true;setChapter(null);if(!selected)return;if(!hash)return;setError('');atlasRead<{body:Chapter}>('/atlas/chapters/'+encodeURIComponent(selected)).then(r=>{if(live){setChapter(r.body);setError('')}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[selected,hash,retry,chapters.length])
  function select(id:string){const next=new URLSearchParams(params);next.set('chapter',id);next.delete('layer');next.delete('event');if(chapterParam){navigate('/atlas?'+next.toString())}else{setParams(next)}}
  const relevant=ordering==='exam'&&!!exam
  const subjectChapters=chapters.filter(c=>c.subject===(chapter?.subject||chapters.find(c=>c.id===selected)?.subject))
  const group=(c:typeof chapters[number])=>relevant&&c.exam_relevant?'For your exam':c.unit||'Chapters'
  const sortedChapters=[...subjectChapters].sort((a,b)=>relevant?Number(!!b.exam_relevant)-Number(!!a.exam_relevant):0)
  const units=[...new Set(sortedChapters.map(group))]
  const issue=catalogError||error||(loaded&&selected&&!hash?'This Atlas chapter is unavailable. Choose another chapter.':'')
  if(!chapter)return <main className="finna-page"><h1>Atlas</h1>{issue?<p role="alert">{issue} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>:<p role="status">{loaded&&!chapters.length?'No published chapters are available yet.':'Loading published chapters…'}</p>}{chapters.map(c=><button key={c.id} className="block min-h-11 text-link underline" onClick={()=>select(c.id)}>{c.title}{explored.includes(c.id)?' · Explored':''}</button>)}</main>
  return <main className="finna-page finna-atlas" data-screen="atlas">
    <header className="finna-page-heading"><div><Link className="text-sm font-bold text-map-dark" to="/library">← Library</Link><h1 className="mt-1.5">Atlas</h1></div><nav className="finna-segments" aria-label="Atlas subjects">{subjects.map(s=><button type="button" key={s.id} aria-pressed={chapter.subject===s.id} onClick={()=>{const first=chapters.find(c=>c.subject===s.id);if(first)select(first.id)}}>{s.title}</button>)}</nav></header>
    {exam&&<div className="mb-4 max-w-xl"><label className="text-sm font-semibold">Chapter order<select className={control+' mt-2'} value={ordering} onChange={e=>setOrdering(e.target.value)}><option value="exam">Relevant to {exam.title} first</option><option value="all">Full chapter order</option></select></label><p className="mt-2 text-xs text-secondary">Uses current published exam sections and owner-curated topic links. Every chapter remains available.</p></div>}
    <div className="finna-atlas-layout"><aside className="finna-card finna-atlas-nav"><label className="block text-xs font-bold lg:hidden">Map chapter<select className={`${control} mt-2`} value={chapter.id} onChange={e=>select(e.target.value)}>{sortedChapters.map(c=><option key={c.id} value={c.id}>{c.title}{explored.includes(c.id)?' · Explored':''}</option>)}</select></label><nav aria-label="Atlas chapters" className="hidden space-y-5 lg:block">{units.map(unit=><section key={unit}><h2 className="mb-2 px-2 text-xs font-bold uppercase tracking-widest text-secondary">{unit}</h2>{sortedChapters.filter(c=>group(c)===unit).map(c=><button type="button" key={c.id} aria-current={c.id===chapter.id?'page':undefined} className={'block min-h-10 w-full rounded-[10px] px-2 py-2 text-left text-sm '+(c.id===chapter.id?'bg-map-soft font-bold text-map-dark':'font-medium hover:bg-canvas')} onClick={()=>select(c.id)}>{c.title}{explored.includes(c.id)?' · Explored':''}</button>)}</section>)}</nav></aside><AtlasChapter key={[chapter.id,params.get('layer'),params.get('event')].join(':')} chapter={chapter}/></div>
  </main>
}
