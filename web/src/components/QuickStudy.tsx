import {useEffect,useState} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import {isLaterExamCollection,listCollections,type Collection} from '../lib/api'
import {useExamScope} from '../lib/examScope'
import {quickExams,quickStudyHref,quickStudyTasks,type QuickTask} from '../lib/quickAccess'
import {choosePreferredExam} from '../lib/preferredExam'

const SHORTCUTS=[['udc','UDC'],['ldc','LDC'],['combined-prelims','Prelims'],['mes','MES']] as const
export default function QuickStudy({compact=false,initialExam=''}:{compact?:boolean;initialExam?:string}){
 const [expanded,setExpanded]=useState(false)
 const [exams,setExams]=useState<Collection[]>([]),[selected,setSelected]=useState(''),[task,setTask]=useState<QuickTask>('mixed'),[error,setError]=useState(false),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0)
 const navigate=useNavigate(),scope=useExamScope()
 useEffect(()=>{let live=true;setLoading(true);setError(false);listCollections().then(rows=>{if(live){const available=rows.filter(c=>c.kind==='exam'&&!isLaterExamCollection(c));setExams(available);setSelected(current=>quickExams(available).some(exam=>exam.id===current)?current:quickExams(available).some(exam=>exam.id===initialExam)?initialExam:'')}}).catch(()=>{if(live)setError(true)}).finally(()=>{if(live)setLoading(false)});return()=>{live=false}},[scope,retry,initialExam])
 useEffect(()=>{if(initialExam)setSelected(initialExam)},[initialExam])
 const choices=quickExams(exams),tasks=quickStudyTasks(selected),choice=choices.find(exam=>exam.id===selected)
 const currentTask=tasks.find(item=>item.id===task)||tasks[0]
 function choose(id:string){setSelected(id);setTask(task==='papers'?'papers':quickStudyTasks(id)[0].id);if(compact)choosePreferredExam(id)}
 if(compact&&!expanded)return <section className="finna-quick-launch" aria-labelledby="quick-study-title"><div className="finna-quick-launch-icon" aria-hidden="true">{selected==='udc'?'UDC':selected==='ldc'?'LDC':selected==='mes'?'MES':'→'}</div><div className="min-w-0 flex-1"><p className="finna-eyebrow text-exams-dark">Quick start</p><h2 id="quick-study-title" className="mt-1">{choice?.title||'Choose your exam'}</h2><p className="mt-1 text-sm">{choice?currentTask.label+' · '+(selected==='mes'?'choose your branch':'at your own pace'):'Questions, original papers and practice'}</p><button type="button" onClick={()=>setExpanded(true)} className="mt-1 min-h-9 text-left text-xs font-bold underline underline-offset-4">Change exam or practice mode</button></div><Link className="finna-btn" to={choice?quickStudyHref(choice.id,currentTask.id):'/exams'}>{choice?'Start':'Explore'}</Link></section>
 return <section aria-labelledby="quick-study-title" className="finna-quick-start overflow-hidden rounded-panel border border-hairline bg-card shadow-[0_2px_8px_rgba(29,27,24,.04)]">
  <div className="border-b border-hairline bg-gradient-to-br from-exams-soft to-card p-5 sm:p-6"><div className="flex flex-wrap items-center justify-between gap-2"><h2 id="quick-study-title" className="font-display text-xl leading-tight">Quick start</h2>{compact?<button type="button" onClick={()=>setExpanded(false)} className="min-h-11 text-xs font-bold text-link">Done</button>:<Link to="/exams" className="inline-flex min-h-11 items-center text-xs font-semibold text-link underline-offset-4 hover:underline">Browse all exams →</Link>}</div><p className="mt-1 text-sm leading-relaxed text-secondary">Pick your exam. Choose a focus. Start studying.</p></div>
  <div className="p-5 sm:p-6">
   <div role="group" aria-label="Exam shortcuts" className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">{SHORTCUTS.filter(([id])=>choices.some(exam=>exam.id===id)).map(([id,label])=><button key={id} type="button" aria-label={`Choose ${choices.find(exam=>exam.id===id)!.title}`} aria-pressed={selected===id} onClick={()=>choose(id)} className={'min-h-11 rounded-lg border px-3 text-sm font-semibold transition-colors '+(selected===id?'border-exams bg-exams-soft text-exams-dark':'border-hairline bg-paper text-secondary hover:border-exams hover:text-ink')}>{label}</button>)}</div>
   <form onSubmit={e=>{e.preventDefault();if(choice)navigate(quickStudyHref(choice.id,currentTask.id))}} className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
    <label className="text-xs font-semibold text-secondary">Exam<select required aria-label="Quick start exam" value={selected} onChange={e=>choose(e.target.value)} className="mt-1.5 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-canvas px-3 text-sm font-normal text-ink"><option value="">{loading?'Loading exams…':'Choose your exam'}</option>{choices.map(exam=><option key={exam.id} value={exam.id}>{exam.title}</option>)}</select></label>
    <label className="text-xs font-semibold text-secondary">What next?<select aria-label="Quick start task" value={currentTask.id} onChange={e=>setTask(e.target.value as QuickTask)} className="mt-1.5 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-canvas px-3 text-sm font-normal text-ink">{tasks.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
    <div className="mt-1 flex min-w-0 flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4 sm:col-span-2"><p aria-live="polite" className="min-w-0 flex-1 basis-48 text-sm leading-relaxed text-secondary">{choice?currentTask.description:'Choose an exam above, or browse the full exam library.'}</p><button type="submit" disabled={!choice} className="inline-flex min-h-11 w-full items-center justify-center gap-3 rounded-pill bg-ink px-5 py-3 text-sm font-semibold text-paper disabled:opacity-40 sm:w-auto">{choice?currentTask.action:'Choose an exam'} <span aria-hidden="true">→</span></button></div>
   </form>
   {error&&<p role="status" className="mt-3 text-sm text-secondary">The exam list couldn’t load. MES is still available. <button onClick={()=>setRetry(n=>n+1)} className="min-h-11 font-semibold text-link underline">Try again</button></p>}
  </div>
 </section>
}
