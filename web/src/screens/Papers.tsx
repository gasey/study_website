import {useEffect,useMemo,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {getCollection,listCollections,type Collection,type CollectionDetail} from '../lib/api'
import {useExamScope} from '../lib/examScope'
import {choosePreferredExam,usePreferredExam} from '../lib/preferredExam'
import {sortArchivePapers} from '../lib/paperArchive'
import {groupSourceBooklets} from '../lib/sourceBooklets'
import ExamPaperList from '../components/ExamPaperList'
import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
const SIZE=20
/** /papers is reserved for original PDF assets; this directory is /past-papers. */
export default function Papers(){
 const [params,setParams]=useSearchParams(),scope=useExamScope(),[exams,setExams]=useState<Collection[]>([])
 const [data,setData]=useState<CollectionDetail|null>(null),[catalogLoading,setCatalogLoading]=useState(true),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 const preferred=usePreferredExam(exams),exam=exams.find(e=>e.id===params.get('exam'))||preferred
 const query=params.get('q')||'',page=pageNumber(params.get('page')),year=params.get('year')||''
 function filter(key:string,value:string){setParams(old=>{const next=new URLSearchParams(old);value?next.set(key,value):next.delete(key);if(key!=='page')next.delete('page');return next},{replace:key!=='page'})}
 useEffect(()=>{let live=true;setExams([]);setCatalogLoading(true);setError('');listCollections().then(rows=>{if(live)setExams(rows.filter(c=>c.kind==='exam'))}).catch(()=>{if(live)setError('The exam directory could not load. Please try again.')}).finally(()=>{if(live)setCatalogLoading(false)});return()=>{live=false}},[scope,retry])
 useEffect(()=>{if(!exam)return;let live=true;setData(null);setError('');getCollection(exam.id).then(result=>{if(live)setData(result)}).catch(e=>{if(live)setError(e instanceof Error?e.message:'The paper archive could not load.')});return()=>{live=false}},[exam?.id,retry])
 const current=data?.id===exam?.id?data:null
 const papers=useMemo(()=>sortArchivePapers((current?.paper_list||[]).filter(p=>p.allow_browse&&(!year||String(p.year)===year)&&(!query||[p.title,p.exam,p.subject,p.paper_number,p.source_file].filter(Boolean).join(' ').toLowerCase().includes(query.toLowerCase()))),'newest'),[current,year,query])
 const groups=groupSourceBooklets(papers),pages=Math.max(1,Math.ceil(groups.length/SIZE)),visible=groups.slice((page-1)*SIZE,page*SIZE)
 useEffect(()=>{if(current&&page>pages)setParams(old=>{const next=new URLSearchParams(old);if(pages>1)next.set('page',String(pages));else next.delete('page');return next},{replace:true})},[current,page,pages,setParams])
 const years=[...new Set(current?.paper_list.flatMap(p=>p.year?[p.year]:[])||[])].sort((a,b)=>b-a)
 return <div className="finna-page" data-screen="papers"><header className="finna-page-heading"><div><p className="finna-eyebrow text-exams-dark">From the original source</p><h1>Past papers</h1></div><Link className="finna-btn finna-btn-quiet" to="/exams">Browse by exam →</Link></header>
  <form onSubmit={e=>e.preventDefault()} className="mb-5 flex flex-wrap gap-3 rounded-[20px] border border-hairline bg-card p-4"><label className="min-w-0 flex-1 basis-64"><span className="sr-only">Search past papers</span><input type="search" aria-label="Search past papers" placeholder="Search exam, paper or subject" value={query} onChange={e=>filter('q',e.target.value)} className="min-h-12 w-full min-w-0 rounded-xl border border-hairline bg-paper px-4 text-sm"/></label><label className="min-w-0 max-w-full"><span className="sr-only">Exam papers</span><select aria-label="Exam papers" disabled={catalogLoading} value={exam?.id||''} onChange={e=>{choosePreferredExam(e.target.value);setParams(old=>{const next=new URLSearchParams(old);next.set('exam',e.target.value);next.delete('page');next.delete('year');return next})}} className="min-h-12 w-full max-w-72 rounded-xl border border-hairline bg-paper px-3 text-sm">{!exams.length&&<option value="">{catalogLoading?'Loading exams…':'Choose an exam'}</option>}{exams.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label><label><span className="sr-only">Paper year</span><select aria-label="Paper year" value={year} onChange={e=>filter('year',e.target.value)} className="min-h-12 rounded-xl border border-hairline bg-paper px-3 text-sm"><option value="">Any year</option>{years.map(y=><option key={y} value={y}>{y}</option>)}</select></label></form>
  <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3"><h2 id="paper-results" tabIndex={-1} className="scroll-mt-44 text-xl font-bold">{exam?exam.title+' · original papers':'Original papers'}</h2><span role="status" className="text-xs text-secondary">{current?groups.length.toLocaleString('en-IN')+' papers':error?'Unavailable':'Loading…'}</span></div>
  {error&&<section className="finna-card" role="alert"><h2>The paper archive couldn’t load</h2><p className="mt-2 text-sm text-secondary">{error}</p><button className="finna-btn mt-4" onClick={()=>setRetry(n=>n+1)}>Try again</button></section>}
  {!current&&!error&&<div role="status" className="finna-card">Loading source papers…</div>}
  {current&&!visible.length&&<section className="finna-card"><h2>No papers match these filters</h2><p className="mt-2 text-sm text-secondary">Try another search or year.</p><button className="finna-btn finna-btn-quiet mt-4" onClick={()=>setParams(exam?{exam:exam.id}:{})}>Clear filters</button></section>}
  {current&&exam&&visible.length>0&&<ExamPaperList papers={papers} groups={visible} examId={exam.id}/>}
  {current&&groups.length>SIZE&&<div className="mt-6"><Pagination page={page} pages={pages} onPageChange={n=>{filter('page',String(n));requestAnimationFrame(()=>scrollToResults('paper-results'))}} label="Past paper pages"/></div>}
 </div>
}
