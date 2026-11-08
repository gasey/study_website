import {useEffect,useState,type ReactNode} from 'react'
import {Link} from 'react-router-dom'
import {getExamStudyTopics,type CollectionDetail,type ExamStudyTopics} from '../lib/api'
import {groupBLink,groupBTitle} from '../lib/groupBStudy'
import ExamPaperList from './ExamPaperList'
import {sortArchivePapers} from '../lib/paperArchive'
import GroupBBookmark from './GroupBBookmark'
import GroupBNonGazettedIntro from './GroupBNonGazettedIntro'

const ACTION='inline-flex min-h-11 items-center justify-center rounded-pill px-4 py-2 text-[13px] font-semibold'
export default function GroupBStudyHome({collection,sources,technicalCount}:{collection:string;sources:CollectionDetail[];technicalCount:number}){
 const [topics,setTopics]=useState<ExamStudyTopics|null>(null),[failed,setFailed]=useState(false),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;setTopics(null);setFailed(false);getExamStudyTopics(collection,'common').then(t=>{if(live)setTopics(t)}).catch(()=>{if(live)setFailed(true)});return()=>{live=false}},[collection,retry])
 const ng=collection==='group-b-non-gazetted',combined=collection==='group-b',ready=sources.length>0
 const hasAnswers=sources.some(c=>c.answerable_count>0),paperCount=new Set(sources.flatMap(c=>c.paper_list.map(p=>p.id))).size
 const departmentalOnly=ready&&sources.every(c=>c.paper_list.length>0&&c.paper_list.every(p=>/departmental/i.test(p.exam||p.title)))
 const current=topics?.subjects.find(s=>s.id==='gk-gs')?.topics.find(t=>/current affairs|current events/i.test(t.title))
 const english=topics?.subjects.find(s=>s.id==='english'),knowledge=topics?.subjects.find(s=>s.id==='gk-gs')
 const study=(area:string)=>groupBLink(collection,'topics',{study_area:area})
 return <>
  <section aria-label="Start your Group B preparation" className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
   <div className="min-w-0 rounded-[16px] border border-hairline bg-card p-5 sm:p-6">
    <p className="font-mono text-[10px] uppercase tracking-widest text-exams-dark">Your starting point</p>
    <h2 className="mt-2 font-display text-[28px] leading-tight sm:text-[32px]">{!ready?'Find your study route':hasAnswers?'Choose a subject. Build from there.':'Start with an original paper.'}</h2>
    <p className="mt-3 max-w-2xl text-[14px] leading-relaxed text-secondary">{ng?'Build your common English and GK foundation, then add the papers required by your post.':combined?'Explore the common preparation available in both collections. Choose a single group whenever your recruitment needs a specific scheme.':'Read the available departmental papers, work through written prompts and compare your response with the original source. Your post’s syllabus determines what to prepare.'}</p>
    <div className="mt-5 flex flex-wrap gap-2"><Link className={ACTION+' bg-ink text-paper'} to={groupBLink(collection,ready&&!hasAnswers?'papers':'topics',{study_area:'common'})}>{ready&&!hasAnswers?'Choose a paper':'Choose a subject'} →</Link><Link className={ACTION+' border border-hairline text-link'} to={groupBLink(collection,'progress')}>My progress →</Link></div>
    {ready&&!hasAnswers&&<p className="mt-4 rounded-lg bg-paper p-3 text-[12px] leading-relaxed text-secondary">No answer-ready MCQ practice is available in this collection yet. Reading and written preparation are available through the paper library; written responses are not automatically graded.</p>}
   </div>
   <aside className="min-w-0 rounded-[16px] border border-hairline bg-paper p-5 sm:p-6"><div className="flex flex-wrap items-start justify-between gap-2"><h2 className="font-display text-[24px]">Available to study</h2>{!combined&&<GroupBBookmark key={collection} collection={collection}/>}</div>{ready?<><dl className="mt-4 grid grid-cols-2 gap-x-3 gap-y-4"><div><dt className="text-[12px] text-secondary">Original papers</dt><dd className="mt-1 font-display text-[30px]">{paperCount}</dd></div>{!combined&&<div><dt className="text-[12px] text-secondary">Questions in this bank</dt><dd className="mt-1 font-display text-[30px]">{sources[0].questions.toLocaleString('en-IN')}</dd></div>}</dl><p className="mt-4 text-[12px] leading-relaxed text-secondary">These are available sources, not a measure of syllabus completion. Original exam names, years and answer labels stay visible.</p><Link className={ACTION+' mt-3 border border-hairline bg-card text-link'} to={groupBLink(collection,'papers')}>Browse paper library →</Link></>:<p role="status" className="mt-4 text-[13px] text-secondary">Loading available papers…</p>}</aside>
  </section>
  {ready&&!hasAnswers&&!combined&&<section className="mt-6"><div className="flex flex-wrap items-baseline justify-between gap-2"><h2 className="font-display text-[28px]">Start with a source paper</h2><Link className={ACTION+' text-link'} to={groupBLink(collection,'papers')}>All papers →</Link></div><ExamPaperList papers={sortArchivePapers(sources[0].paper_list,'newest').slice(0,3)} examId={collection}/></section>}
  <OptionalDisclosure collapsed={ready&&!hasAnswers&&!combined}><section aria-labelledby="group-b-subject-choices" className="mt-7"><div className="flex flex-wrap items-baseline justify-between gap-2"><h2 id="group-b-subject-choices" className="font-display text-[28px]">Common-subject preparation</h2><Link className={ACTION+' text-link'} to={study('common')}>All available topics →</Link></div>
   <p className="mt-1 text-[13px] text-secondary">Choose only the subjects you need. Specialist and departmental papers stay in their own source library.</p>
   {failed?<p role="alert" className="mt-4 rounded-xl border border-hairline bg-card p-4 text-[13px]">Subject availability could not load. <button className={ACTION+' text-link underline'} onClick={()=>setRetry(n=>n+1)}>Retry subjects</button></p>:!topics?<p role="status" className="mt-4 text-[13px] text-secondary">Loading subject availability…</p>:<div className="mt-4 grid gap-3 md:grid-cols-3">
    <Subject title="General English" detail="Grammar, vocabulary and comprehension. Check your paper for written English requirements." count={english?.questions||0} to={study('english')} empty="No English questions are currently mapped to this group."/>
    <Subject title={ng?'General Knowledge':'General Knowledge & Studies'} detail="Browse the approved topics available within these source papers." count={knowledge?.questions||0} to={study('gk-gs')} empty="No common knowledge questions are currently mapped to this group."/>
    <Subject title="Current Affairs" detail="Historical questions belong to their exam date. Compare time-sensitive facts with dated source updates." count={current?.questions||0} to={current?groupBLink(collection,'browse',{study_area:'gk-gs',subject_id:'gk-gs',topic_id:current.id}):''} empty="No Current Affairs topic is currently mapped to this group."/>
   </div>}
  </section>
  </OptionalDisclosure>
  <section aria-label="Preparation beyond common subjects" className={"mt-6 grid gap-3 "+(technicalCount>0?"md:grid-cols-2":"")}>
   <Link to={groupBLink(collection,'papers',{paper_kind:'written'})} className="min-w-0 rounded-xl border border-hairline bg-card p-5 hover:border-ink"><h2 className="font-display text-[24px]">Written & departmental papers</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">Open the full question, plan your answer and compare the original PDF. Keep your written work in your own notes.</p><span className={ACTION+' mt-2 px-0 text-link'}>Find written papers →</span></Link>
   {technicalCount>0&&<div className="min-w-0 rounded-xl border border-hairline bg-card p-5"><h2 className="font-display text-[24px]">Technical preparation</h2><p className="mt-2 text-[13px] leading-relaxed text-secondary">Choose papers for your discipline. Technical questions are kept separate from common English and GK preparation.</p><Link className={ACTION+' mt-2 px-0 text-link'} to={study('technical')}>Explore {technicalCount} technical papers →</Link></div>}
  </section>
  {ng?<GroupBNonGazettedIntro guidanceOnly/>:<details className="mt-5 rounded-xl border border-hairline bg-card px-5"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Scope of this preparation hub</summary><div className="pb-5 text-[13px] leading-relaxed text-secondary"><p>{combined?'This optional shared view brings both source collections together. It does not combine their recruitment rules or imply that their syllabuses are identical.':departmentalOnly?'The current archive contains departmental source papers. Their subjects and requirements do not define a universal direct-recruitment Gazetted syllabus.':'This hub groups available source papers. Their subjects and requirements do not define a universal Gazetted syllabus.'}</p><p className="mt-3">Follow the official notice for your post and year. Practice scores and topic counts do not establish exam readiness or complete syllabus coverage.</p></div></details>}
  {combined&&<div className="mt-4 flex flex-wrap gap-3">{sources.map(c=><Link key={c.id} to={groupBLink(c.id)} className={ACTION+' border border-hairline'}>{groupBTitle(c.id)} →</Link>)}</div>}
 </>
}
function Subject({title,detail,count,to,empty}:{title:string;detail:string;count:number;to:string;empty:string}){
 return <article className="min-w-0 rounded-xl border border-hairline bg-card p-5"><h3 className="font-display text-[24px] leading-tight">{title}</h3><p className="mt-3 text-[13px] leading-relaxed text-secondary">{detail}</p>{count>0&&to?<><p className="mt-3 font-mono text-[11px] text-secondary">{count.toLocaleString('en-IN')} available {count===1?'question':'questions'}</p><Link className={ACTION+' mt-2 px-0 text-link'} to={to}>Open subject →</Link></>:<p className="mt-4 text-[12px] text-muted">{empty}</p>}</article>
}

function OptionalDisclosure({collapsed,children}:{collapsed:boolean;children:ReactNode}){
 return collapsed?<details className="mt-6 rounded-xl border border-hairline bg-card px-5 pb-3"><summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Common-subject availability · limited coverage</summary>{children}</details>:<>{children}</>
}
