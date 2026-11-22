import {lazy,Suspense,useEffect,useState} from 'react'
import {Link,Navigate,useSearchParams} from 'react-router-dom'
import {currentMock,listCollections,isLaterExamCollection,getExamProgress,getExamBookmarks,getProgress,setPrimaryExam,type MockSession,type Collection,type ExamProgressSummary,type Progress} from '../lib/api'
import {reviewSession} from '../lib/review'
import {learningRequest,type ResumePage,type ResumeItem} from '../lib/learning'
import {accountContext} from '../lib/accountContext'
import {useExamScope} from '../lib/examScope'
import {choosePreferredExam,usePreferredExam} from '../lib/preferredExam'
import {examPresentation} from '../lib/examPresentation'
import QuickStudy from '../components/QuickStudy'
import TodayCard from '../components/TodayCard'
import {mockResumePath} from '../lib/sharedTests'
const Feed=lazy(()=>import('./Feed'))

type StudyData={exams:Collection[];examProgress:ExamProgressSummary[];saved:string[];progress:Progress|null;resume:ResumeItem|null;mock:MockSession|null;loading:boolean;error:boolean}
const EMPTY:StudyData={exams:[],examProgress:[],saved:[],progress:null,resume:null,mock:null,loading:true,error:false}
export default function StudyHome(){
 const [params]=useSearchParams(),scope=useExamScope(),[retry,setRetry]=useState(0)
 const [data,setData]=useState<StudyData>(EMPTY),[examError,setExamError]=useState(''),[savingExam,setSavingExam]=useState(false)
 async function chooseExam(id:string){setSavingExam(true);setExamError('');try{if((await accountContext()).authenticated)await setPrimaryExam(id);choosePreferredExam(id)}catch(e){setExamError((e as Error).message)}finally{setSavingExam(false)}}
 useEffect(()=>{let live=true;setData(EMPTY)
  const patch=(values:Partial<StudyData>)=>{if(live)setData(previous=>({...previous,...values}))}
  const requests=[
   listCollections().then(rows=>patch({exams:rows.filter(c=>c.kind==='exam'&&!isLaterExamCollection(c))})),
   getProgress().then(progress=>patch({progress})),
   getExamProgress().then(examProgress=>patch({examProgress})),
   getExamBookmarks().then(saved=>{if(live){patch({saved:saved.collection_ids});if(saved.primary_collection_id)choosePreferredExam(saved.primary_collection_id)}}),
   currentMock().then(mock=>patch({mock})),
   accountContext().then(a=>a.authenticated?reviewSession().then(s=>learningRequest<ResumePage>('/resume?exam_scope='+scope,s.user_id)).then(r=>patch({resume:r.items.find(i=>i.kind!=='desk'&&/^\/(bank|exams|group-b|english|mizo|arithmetic|essay|library|desk|tests)([/?#]|$)/.test(i.url))||null})):undefined),
  ]
  Promise.allSettled(requests).then(results=>patch({loading:false,error:results.some(r=>r.status==='rejected')}))
  return()=>{live=false}
 },[scope,retry])
 useEffect(()=>{const refresh=()=>{setData(EMPTY);setRetry(n=>n+1)};window.addEventListener('ism-auth-change',refresh);return()=>window.removeEventListener('ism-auth-change',refresh)},[])
 const exam=usePreferredExam(data.exams),examProgress=data.examProgress.find(p=>p.collection_id===exam?.id)
 const coverage=exam&&examProgress&&exam.questions?Math.min(100,Math.round(examProgress.unique_questions/exam.questions*100)):0
 const p=data.progress
 const subjects=[...(p?.subjects||[])].sort((a,b)=>b.answered-a.answered).slice(0,6)
 const examTitle=exam?exam.id==='udc'?'UDC':exam.id==='ldc'?'LDC':exam.id==='combined-prelims'?'Prelims':exam.title:'Choose your exam'
 const next=data.mock?mockResumePath(data.mock):data.resume?.url
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata'}).format(new Date())
 const week=p?.daily_activity.filter(d=>d.day>=new Date(Date.parse(today+'T12:00:00Z')-6*86400000).toISOString().slice(0,10))||[]
 const weekAnswers=week.reduce((n,d)=>n+d.answered,0),weekCorrect=week.reduce((n,d)=>n+d.correct,0)
 // Previously shared community links retain their original destinations and filters.
 if(params.has('section')||params.has('tab')||params.has('discussion')){const nextParams=new URLSearchParams(params);nextParams.delete('section');return <Navigate replace to={'/community?'+nextParams}/>}
 return <div className="finna-page finna-home" data-screen="home">
  <h1 className="sr-only">Your study home</h1>
  <div className="finna-home-grid">
   <aside className="finna-home-side" aria-label="Your exam and study plan">
    <section className="finna-exam-hero" aria-labelledby="my-exam-title"><div className="finna-hero-head"><div className="min-w-0"><div className="finna-eyebrow">My exam</div><h2 id="my-exam-title" className="mt-1 text-3xl font-bold leading-none tracking-tight">{data.loading&&!exam?'Your exam':examTitle}</h2>{exam&&<p className="finna-exam-description">{exam.id==='udc'?'Upper Division Clerk':exam.id==='ldc'?'Lower Division Clerk':examPresentation(exam.id).category}</p>}</div>{data.exams.length>0?<label className="finna-hero-change relative">Change<select aria-label="Choose my exam" value={exam?.id||''} disabled={savingExam} onChange={e=>void chooseExam(e.target.value)} className="absolute inset-0 w-full cursor-pointer opacity-0">{data.exams.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label>:<Link className="finna-hero-change" to="/exams">Find</Link>}</div>
     <div className="finna-hero-stats"><div><strong>{exam?exam.questions.toLocaleString('en-IN'):'—'}</strong><small>questions in your exam bank</small></div><div><strong>{exam?coverage+'%':'—'}</strong><small>of bank answered</small></div></div><div className="finna-hero-actions"><Link to={exam?'/practice?exam='+encodeURIComponent(exam.id):'/practice'}>Practice</Link><Link to={exam?'/practice?exam='+encodeURIComponent(exam.id)+'&timer=on':'/practice?timer=on'}>Timed run</Link></div>
    </section>
    {examError&&<p role="alert" className="text-sm text-wrong">{examError}</p>}<TodayCard exams={data.exams}/>
    <section className="finna-card finna-subject-card"><div className="finna-section-top"><h2>Subject progress</h2><Link to="/profile">All activity</Link></div>{subjects.length?subjects.map(s=><Link key={s.subject_id} to={'/bank?subject_id='+encodeURIComponent(s.subject_id)} className="finna-subject-row block"><div><span className="font-semibold">{s.subject}</span><span className="text-secondary">{s.answered?Math.round(s.correct/s.answered*100)+'%':'—'}</span></div><div className="finna-progress"><span style={{width:Math.min(100,s.answered?s.correct/s.answered*100:0)+'%'}}/></div></Link>):<p className="text-sm leading-relaxed text-secondary">{data.loading?'Loading your progress…':'Answer a few questions to see which subjects are getting stronger.'}</p>}</section>
   </aside>
   <section className="finna-home-stream" aria-label="Continue learning and community feed"><nav className="finna-home-phone-links" aria-label="Study and community"><Link to="/community">Community feed →</Link><Link to="/create">Create →</Link></nav>
    <div className="finna-card finna-composer"><Link to="/community?tab=questions">Ask a doubt or share what you know</Link><Link to="/studio/new">Note</Link><Link to="/create/new?kind=new_question">MCQ</Link></div>
    {next&&<section className="finna-card finna-resume"><div><span className="finna-eyebrow">{data.mock?'Test in progress':'Continue'}</span><h2 className="mt-1">{data.mock?'Your next question is waiting':data.resume?.title}</h2><p>{data.mock?`${data.mock.questions.length} questions · ${Math.max(0,Math.ceil(data.mock.seconds_remaining/60))} minutes remaining`:data.resume?.detail}</p></div><Link to={next} className="finna-btn">{data.mock?'Resume test':'Resume'}</Link></section>}
    {!data.mock&&<QuickStudy compact initialExam={exam?.id}/>}
    {data.error&&<p role="status" className="text-xs text-secondary">Some study information couldn’t load. <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 font-semibold text-link underline">Try again</button></p>}
    <Suspense fallback={<section className="finna-card" role="status">Loading your feed…</section>}><Feed embedded/></Suspense>
   </section>
   <aside className="finna-home-side finna-home-right" aria-label="Your activity and saved work">
    <section className="finna-card"><div className="finna-section-top"><h2>This week</h2><Link to="/profile">Your progress</Link></div>{p?<><div className="finna-stat-row"><span>Questions answered</span><strong>{weekAnswers.toLocaleString('en-IN')}</strong></div><div className="finna-stat-row"><span>Accuracy</span><strong>{weekAnswers?Math.round(weekCorrect/weekAnswers*100)+'%':'—'}</strong></div><div className="finna-stat-row"><span>{p.streak_basis==='device activity'?'Device activity':'Current streak'}</span><strong>{p.current_streak} <span className="text-xs font-semibold">days</span></strong></div></>:<p className="text-sm text-secondary">{data.loading?'Loading your activity…':'Your activity is unavailable right now.'}</p>}</section>
    <section className="finna-card"><div className="finna-section-top"><h2>Saved collections</h2><Link to="/library?library_view=saved">View all</Link></div>{data.saved.length?data.exams.filter(e=>data.saved.includes(e.id)).slice(0,4).map(e=><Link to={'/exams/'+e.id} key={e.id} className="finna-plan-item"><span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-learn-soft text-xs font-bold text-learn-dark">{examPresentation(e.id).short}</span><span className="text-sm font-semibold">{e.title}</span></Link>):<p className="text-sm leading-relaxed text-secondary">Save an exam or study material to find it here.</p>}<Link to="/revise" className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-link">Revise questions & mistakes →</Link></section>
    <section className="finna-card"><h2>Make room for learning</h2><p className="mt-2 text-sm leading-relaxed text-secondary">One focused session. Your questions, notes and study companions in one place.</p><Link to="/desk" className="finna-btn finna-btn-quiet mt-4 w-full">Open study desk →</Link></section>
    <section className="finna-card"><h2>Today's quests</h2><p className="mt-2 text-sm leading-relaxed text-secondary">See your daily learning goals and earned rewards.</p><Link to="/profile/rewards" className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-rewards-dark">View your quests →</Link></section>
   </aside>
  </div>
 </div>
}
