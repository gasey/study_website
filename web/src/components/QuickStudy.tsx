import {useEffect,useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {isLaterExamCollection,listCollections,type Collection} from '../lib/api'
import {quickStudyHref,type QuickTask} from '../lib/quickAccess'

export default function QuickStudy(){
 const [exams,setExams]=useState<Collection[]>([]),[selected,setSelected]=useState(''),[task,setTask]=useState<QuickTask>('mixed'),[error,setError]=useState(false),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0)
 const navigate=useNavigate()
 useEffect(()=>{let live=true;setLoading(true);setError(false);listCollections().then(rows=>{if(live)setExams(rows.filter(c=>c.kind==='exam'&&!isLaterExamCollection(c)))}).catch(()=>{if(live)setError(true)}).finally(()=>{if(live)setLoading(false)});return()=>{live=false}},[retry])
 return <section aria-labelledby="quick-study-title" className="rounded-panel border border-hairline bg-card p-4 sm:p-5">
  <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2"><h2 id="quick-study-title" className="font-display text-[25px]">Quick start</h2><p className="text-xs text-secondary">Your exam. Your next step.</p></div>
  <form onSubmit={e=>{e.preventDefault();if(exams.some(c=>c.id===selected))navigate(quickStudyHref(selected,task))}} className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
   <label className="text-xs text-secondary">Exam<select required aria-label="Quick start exam" value={selected} onChange={e=>setSelected(e.target.value)} disabled={loading||error} className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-canvas px-2 text-sm text-ink"><option value="">{loading?'Loading exams…':'Choose your exam'}</option>{exams.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label>
   <label className="text-xs text-secondary">What next?<select aria-label="Quick start task" value={task} onChange={e=>setTask(e.target.value as QuickTask)} className="mt-1 min-h-11 w-full rounded-lg border border-hairline bg-canvas px-2 text-sm text-ink"><option value="mixed">Mixed practice</option><option value="unseen">Never attempted</option><option value="ever_wrong">Previously wrong</option><option value="papers">Original papers</option></select></label>
   <button type="submit" disabled={!selected||loading||error} className="min-h-11 self-end rounded-lg bg-ink px-4 text-sm font-semibold text-paper disabled:opacity-40">Open →</button>
  </form>
  {task==='ever_wrong'&&<p className="mt-2 text-xs text-secondary">Includes questions you later answered correctly.</p>}
  {error&&<p role="status" className="mt-2 text-sm text-secondary">Exams couldn’t load. <button onClick={()=>setRetry(n=>n+1)} className="min-h-11 underline">Try again</button></p>}
 </section>
}
