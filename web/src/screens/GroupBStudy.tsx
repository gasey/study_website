import '../styles/exam-experience.css'
import ExamOverview from '../components/ExamOverview'
import ReviewModuleLink from '../components/ReviewModuleLink'
import {paperIdentity} from '../lib/paperIdentity'
import {GROUP_B_COLLECTIONS,GROUP_B_AREAS,groupBState,groupBAreaLabel,groupBNavigate,groupBTitle,groupBLink} from '../lib/groupBStudy'
import GroupBStudyHome from '../components/GroupBStudyHome'
import GroupBPaperArchive from '../components/GroupBPaperArchive'
import '../styles/legacy-learning-dashboard.css'
import Pagination from '../components/Pagination'
import {pageNumber} from '../lib/pagination'
import {useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import ExamStudyTopics from '../components/ExamStudyTopics'
import {ModuleQuestionBrowser,ModuleProgressPanel} from './ModuleStudy'
import {getCollection,getGroupBStudyConfig,type CollectionDetail} from '../lib/api'

export default function GroupBStudy(){
  const [params,setParams]=useSearchParams()
  const {collection,area,view}=groupBState(params)
  const [collections,setCollections]=useState<CollectionDetail[]>([])
  const [roles,setRoles]=useState<Awaited<ReturnType<typeof getGroupBStudyConfig>>|null>(null)
  const [error,setError]=useState('')
  const [retry,setRetry]=useState(0)
  const [loadedCollection,setLoadedCollection]=useState('')
  useEffect(()=>{
    let live=true;setError('');setLoadedCollection('')
    const ids=collection==='group-b'?[...GROUP_B_COLLECTIONS]:[collection]
    Promise.all([Promise.all(ids.map(getCollection)),getGroupBStudyConfig()])
      .then(([values,config])=>{if(live){setCollections(values);setRoles(config);setLoadedCollection(collection)}})
      .catch(e=>{if(live)setError(e.message)})
    return()=>{live=false}
  },[collection,retry])
  const selected=(loadedCollection===collection?collections:[]).filter(c=>collection==='group-b'||c.id===collection)
  const sourceCollections=useMemo(()=>Object.fromEntries(selected.flatMap(c=>c.paper_list.map(p=>[p.id,c.id]))),[collections,collection,loadedCollection])
  const papers=selected.flatMap(c=>c.paper_list).filter((p,i,all)=>all.findIndex(other=>other.id===p.id)===i)
  const technicalPapers=papers.filter(p=>roles?.rules.some(r=>r.paper_id===p.id&&r.role==='technical'&&selected.some(c=>c.id===r.collection_id)))
  const paperSearch=params.get('technical_q')||''
  const matchedTechnical=technicalPapers.filter(p=>`${p.exam||''} ${p.paper_label||''} ${p.title} ${p.id}`.toLowerCase().includes(paperSearch.toLowerCase()))
  const technicalPage=Math.min(pageNumber(params.get('technical_page')),Math.max(1,Math.ceil(matchedTechnical.length/8)))
  const visibleTechnical=matchedTechnical.slice((technicalPage-1)*8,technicalPage*8)
  const hasAnswers=selected.some(c=>c.answerable_count>0)
  const studyView=['topics','browse','practice'].includes(view)
  function select(key:string,value:string){setParams(previous=>groupBNavigate(previous,key,value))}
  const recruitmentNavigation = <nav aria-label="Group B recruitment group" className="mt-4 flex flex-wrap gap-2">{[...GROUP_B_COLLECTIONS].map(id=><button key={id} type="button" aria-pressed={collection===id} onClick={()=>select('collection',id)} className={'min-h-11 rounded-pill border px-4 text-sm font-semibold '+(collection===id?'border-ink bg-ink text-paper':'border-hairline bg-card')}>{id==='group-b-non-gazetted'?'Non-Gazetted':'Gazetted'}</button>)}<button type="button" aria-pressed={collection==='group-b'} onClick={()=>select('collection','group-b')} className="min-h-11 px-3 text-xs text-link underline">Shared study</button></nav>
  const viewNavigation = <nav aria-label="Group B study navigation" className="module-view-nav">{[['browse','Browse'],['topics','Subjects'],['papers','Papers'],...(hasAnswers||view==='practice'?[['practice','Practice']]:[]),['progress','Progress'],['home','Overview']].map(([value,label])=><button key={value} type="button" onClick={()=>select('view',value)} aria-current={view===value?'page':undefined} className={'min-h-11 min-w-0 rounded-pill border px-1 text-xs font-semibold sm:px-4 sm:text-sm '+(view===value?'border-ink bg-ink text-paper':'border-hairline bg-card')}>{label}</button>)}</nav>
  const existingViews = <div className="exam-module-content">
    {studyView&&<><nav className="mt-4 flex flex-wrap gap-2" aria-label="Group B learning areas">{GROUP_B_AREAS.map(id=><button key={id} type="button" onClick={()=>select('study_area',id)} aria-pressed={area===id} className={'min-h-11 rounded-pill border px-4 text-sm '+(area===id?'border-ink bg-ink text-paper':'border-hairline bg-card')}>{groupBAreaLabel(id,collection)}</button>)}</nav><nav className="mt-3 flex flex-wrap gap-2" aria-label="Study mode">{(['topics','browse',...(hasAnswers||view==='practice'?['practice']:[])] as string[]).map(mode=><button key={mode} type="button" onClick={()=>select('view',mode)} aria-pressed={view===mode} className={'min-h-11 rounded-lg px-3 text-sm '+(view===mode?'bg-paper font-semibold underline':'text-link')}>{mode==='topics'?'Choose a topic':mode==='browse'?'Read questions':'Practise answers'}</button>)}</nav></>}
    {loadedCollection!==collection&&!error&&<p role="status" className="mt-4 text-sm text-secondary">Loading your study sources…</p>}
    {error&&<p role="alert" className="mt-4 text-mypick">Could not load Group B papers: {error} <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 px-3 underline">Retry</button></p>}
    {area==='technical'&&view==='topics'&&<section className="mt-6" aria-labelledby="group-b-technical-heading"><h2 id="group-b-technical-heading" className="font-display text-xl">Choose a technical paper</h2><p className="mt-2 text-sm text-secondary">Choose a paper for your discipline, or practise its subjects and topics below. Full departmental papers are also available in the exam archives.</p><label className="mt-4 block text-xs font-semibold">Find your discipline or paper<input type="search" value={paperSearch} onChange={e=>select('technical_q',e.target.value)} placeholder="Electrical, surveyor, laboratory…" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-card px-3 text-sm"/></label><div className="mt-4 grid gap-3 md:grid-cols-2">{visibleTechnical.map(p=><Link key={p.id} to={`/exams/${sourceCollections[p.id]}/paper?paper=${encodeURIComponent(p.id)}`} className="min-w-0 rounded-[12px] border border-hairline bg-card p-4 hover:border-ink"><strong className="block break-words text-sm">{paperIdentity(p).title}</strong>{paperIdentity(p).exam&&<span className="mt-2 block break-words text-sm text-secondary">{paperIdentity(p).exam}</span>}<span className="mt-2 block text-xs text-secondary">{p.year||'Year unavailable'} · {p.questions} questions · Open original paper →</span></Link>)}</div><Pagination page={technicalPage} pages={Math.ceil(matchedTechnical.length/8)} onPageChange={page=>select('technical_page',String(page))} label="Technical paper pages"/>{loadedCollection===collection&&roles&&!matchedTechnical.length&&<p className="mt-4 text-sm text-secondary">No technical paper has been assigned for this source group yet.</p>}</section>}
    {view==='home'&&<GroupBStudyHome key={collection} collection={collection} sources={selected} technicalCount={technicalPapers.length}/>}
    {view==='topics'&&<ExamStudyTopics key={collection+area} examId={collection} area={area} basePath="/group-b" allowPractice={hasAnswers}/>}
    {(view==='browse'||view==='practice')&&loadedCollection===collection&&(view==='practice'&&!hasAnswers?<section className="mt-5 rounded-xl border border-hairline bg-card p-5"><h2 className="font-display text-xl">Start with the available source papers</h2><p className="mt-2 text-sm text-secondary">This collection does not currently have answer-ready MCQ practice. You can read the original questions and prepare written responses.</p><Link className="mt-3 inline-flex min-h-11 items-center text-sm font-semibold text-link" to={groupBLink(collection,'papers')}>Open paper library →</Link></section>:<ModuleQuestionBrowser key={collection+area+view} collectionId={collection} collectionTitle={groupBTitle(collection)} studyArea={params.has('paper')?undefined:area} sourceCollections={sourceCollections} papers={area==='technical'?technicalPapers:papers} sections={[]} initialPool={view==='practice'?'practice':'all'}/>)}
    {view==='papers'&&loadedCollection===collection&&<GroupBPaperArchive key={collection} sources={selected}/>}
    {view==='progress'&&loadedCollection===collection&&(collection==='group-b'?<section className="mt-5 rounded-xl border border-hairline bg-card p-5"><h2 className="font-display text-xl">Choose a group for progress</h2><p className="mt-2 text-sm text-secondary">Keep your preparation goals separate. Shared questions retain their existing attempt history.</p><div className="mt-3 flex flex-wrap gap-3">{selected.map(c=><Link key={c.id} className="inline-flex min-h-11 items-center text-sm font-semibold text-link" to={groupBLink(c.id,'progress')}>{groupBTitle(c.id)} →</Link>)}</div></section>:<><p className="mt-5 text-sm text-secondary">Progress reflects recorded question attempts. Reading papers and writing offline answers do not create automatic scores or syllabus completion.</p><ModuleProgressPanel key={collection} collectionId={collection} collectionTitle={groupBTitle(collection)} totalScorable={selected[0].scorable} totalQuestions={selected[0].questions} practiceAvailable={hasAnswers} practiceHref={groupBLink(collection,'practice')} papersHref={groupBLink(collection,'papers')}/></>)}
    {studyView&&<div className="mt-8 border-t border-hairline pt-4"><Link className="inline-flex min-h-11 items-center text-sm font-semibold text-link" to={groupBLink(collection,'papers')}>Looking for written or mixed papers? Open the full paper library →</Link></div>}

  </div>
  return <ExamOverview title={groupBTitle(collection)} collections={selected} loading={loadedCollection!==collection&&!error} error={error} onRetry={()=>setRetry(n=>n+1)} viewKey={view} navigation={<><ReviewModuleLink collection={collection}/>{recruitmentNavigation}{viewNavigation}</>}>{view!=='home'?existingViews:undefined}</ExamOverview>
}
