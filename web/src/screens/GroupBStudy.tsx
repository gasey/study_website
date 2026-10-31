import Pagination from '../components/Pagination'
import {pageNumber} from '../lib/pagination'
import {useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import ExamStudyTopics from '../components/ExamStudyTopics'
import {ModuleQuestionBrowser} from './ModuleStudy'
import {getCollection,getGroupBStudyConfig,type CollectionDetail,type GroupBStudyArea} from '../lib/api'

const COLLECTIONS=['group-b-gazetted','group-b-non-gazetted']
const AREAS:[GroupBStudyArea,string][]=[['common','English & GK/GS'],['english','English'],['gk-gs','General Knowledge & Studies'],['technical','Technical papers']]
export default function GroupBStudy(){
  const [params,setParams]=useSearchParams()
  const requested=params.get('study_area')||'common'
  const area:GroupBStudyArea=AREAS.some(([id])=>id===requested)?requested as GroupBStudyArea:'common'
  const collection=COLLECTIONS.includes(params.get('collection')||'')?params.get('collection')!:'group-b'
  const view=params.get('view')==='practice'?'practice':params.get('view')==='browse'?'browse':'topics'
  const [collections,setCollections]=useState<CollectionDetail[]>([])
  const [roles,setRoles]=useState<Awaited<ReturnType<typeof getGroupBStudyConfig>>|null>(null)
  const [error,setError]=useState('')
  useEffect(()=>{let live=true;Promise.all([Promise.all(COLLECTIONS.map(getCollection)),getGroupBStudyConfig()]).then(([values,config])=>{if(live){setCollections(values);setRoles(config)}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[])
  const selected=collections.filter(c=>collection==='group-b'||c.id===collection)
  const sourceCollections=useMemo(()=>Object.fromEntries(selected.flatMap(c=>c.paper_list.map(p=>[p.id,c.id]))),[collections,collection])
  const papers=selected.flatMap(c=>c.paper_list).filter((p,i,all)=>all.findIndex(other=>other.id===p.id)===i)
  const technicalPapers=papers.filter(p=>roles?.rules.some(r=>r.paper_id===p.id&&r.role==='technical'&&selected.some(c=>c.id===r.collection_id)))
  const paperSearch=params.get('technical_q')||''
  const matchedTechnical=technicalPapers.filter(p=>`${p.title} ${p.id}`.toLowerCase().includes(paperSearch.toLowerCase()))
  const technicalPage=Math.min(pageNumber(params.get('technical_page')),Math.max(1,Math.ceil(matchedTechnical.length/8)))
  const visibleTechnical=matchedTechnical.slice((technicalPage-1)*8,technicalPage*8)
  function select(key:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);next.set(key,value);if(key==='technical_q')next.delete('technical_page');if(key!=='view'&&key!=='technical_q'&&key!=='technical_page'){for(const field of ['paper','section','subject_id','topic_id','subtopic_id','offset','q','answer_status'])next.delete(field);next.set('view','topics')}return next})}
  return <div className="mx-auto max-w-shell px-5 pb-24 pt-8 sm:px-6">
    <Link to="/exams" className="text-[13px] text-secondary">← Exams</Link>
    <div className="mt-4 rounded-[18px] bg-exams-soft p-6 sm:p-8"><div className="font-mono text-[11px] uppercase tracking-[.1em] text-exams-dark">Group B preparation</div><h1 className="mt-3 font-display text-[clamp(32px,5vw,48px)] leading-tight">{area==='technical'?'Group B — Technical papers':'Group B — English & GK/GS'}</h1><p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-secondary">Common-subject preparation for gazetted and non-gazetted recruitments. Study English and General Knowledge & Studies together, or choose a separate technical paper for your discipline.</p><p className="mt-3 text-[13px] text-secondary">Check the syllabus for your recruitment and year. These study areas cover the available papers; they do not represent every Group B syllabus.</p></div>
    <nav className="mt-5 flex flex-wrap gap-2" aria-label="Group B learning areas">{AREAS.map(([id,label])=><button key={id} type="button" onClick={()=>select('study_area',id)} aria-pressed={area===id} className={`min-h-11 rounded-pill border px-4 text-[13px] font-semibold ${area===id?'border-ink bg-ink text-paper':'border-hairline bg-card'}`}>{label}</button>)}</nav>
    <div className="mt-4 flex flex-wrap items-end gap-4"><label className="text-[12px] font-semibold">Source recruitment group<select value={collection} onChange={e=>select('collection',e.target.value)} className="mt-1 block min-h-11 rounded-[8px] border border-hairline bg-card px-3 text-[14px]"><option value="group-b">Gazetted & non-gazetted</option><option value="group-b-non-gazetted">Non-gazetted</option><option value="group-b-gazetted">Gazetted</option></select></label><nav className="flex flex-wrap gap-2" aria-label="Study mode">{(['topics','browse','practice'] as const).map(mode=><button key={mode} type="button" onClick={()=>select('view',mode)} aria-pressed={view===mode} className={`min-h-11 rounded-pill border px-4 text-[13px] ${view===mode?'border-ink font-semibold':'border-hairline'}`}>{mode==='topics'?'Subjects & topics':mode==='browse'?'Browse questions':'Practise answers'}</button>)}</nav></div>
    <p className="mt-4 rounded-[12px] border border-hairline bg-card p-4 text-[13px] leading-relaxed text-secondary">Gazetted coverage currently contains historical departmental Inspector papers. Direct-recruitment common papers are being added as sources become available. Original paper names, years and recruitment details remain visible with each question.</p>
    {error&&<p role="alert" className="mt-4 text-mypick">Could not load Group B papers: {error}</p>}
    {area==='technical'&&view==='topics'&&<section className="mt-6" aria-labelledby="group-b-technical-heading"><h2 id="group-b-technical-heading" className="font-display text-[28px]">Choose a technical paper</h2><p className="mt-2 text-[13px] text-secondary">Choose a paper for your discipline, or practise its subjects and topics below. Full departmental papers are also available in the exam archives.</p><label className="mt-4 block text-[12px] font-semibold">Find your discipline or paper<input type="search" value={paperSearch} onChange={e=>select('technical_q',e.target.value)} placeholder="Electrical, surveyor, laboratory…" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-card px-3 text-[14px]"/></label><div className="mt-4 grid gap-3 md:grid-cols-2">{visibleTechnical.map(p=><Link key={p.id} to={`/exams/${sourceCollections[p.id]}/paper?paper=${encodeURIComponent(p.id)}`} className="min-w-0 rounded-[12px] border border-hairline bg-card p-4 hover:border-ink"><strong className="block break-words text-[14px]">{p.id.split('/').pop()?.replace(/\.pdf$/i,'')}</strong><span className="mt-2 block text-[12px] text-secondary">{p.year||'Year unavailable'} · {p.questions} questions · Open original paper →</span></Link>)}</div><Pagination page={technicalPage} pages={Math.ceil(matchedTechnical.length/8)} onPageChange={page=>select('technical_page',String(page))} label="Technical paper pages"/>{roles&&!matchedTechnical.length&&<p className="mt-4 text-[13px] text-secondary">No technical paper has been assigned for this source group yet.</p>}</section>}
    {view==='topics'?<ExamStudyTopics key={collection+area} examId={collection} area={area} basePath="/group-b"/>:collections.length>0&&<ModuleQuestionBrowser key={collection+area+view} collectionId={collection} studyArea={area} sourceCollections={sourceCollections} papers={area==='technical'?technicalPapers:papers} sections={[]} initialPool={view==='practice'?'practice':'all'}/>}
    <section className="mt-8 border-t border-hairline pt-5"><h2 className="font-display text-[24px]">Complete exam archives</h2><p className="mt-2 text-[13px] text-secondary">Find full mixed papers, other subjects and papers awaiting a study-area assignment.</p><div className="mt-3 flex flex-wrap gap-3">{selected.map(c=><Link key={c.id} className="inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 text-[13px] font-semibold" to={`/exams/${c.id}?view=papers`}>{c.title} · all papers →</Link>)}</div></section>
  </div>
}
