import {groupSourceBooklets,representativeBooklet} from '../lib/sourceBooklets'
import {useSearchParams} from 'react-router-dom'
import type {CollectionDetail} from '../lib/api'
import {groupBNavigate,groupBTitle} from '../lib/groupBStudy'
import {paperOrder,sortArchivePapers} from '../lib/paperArchive'
import {pageNumber} from '../lib/pagination'
import ExamPaperList from './ExamPaperList'
import Pagination from './Pagination'

const INPUT='mt-1 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-card px-3 text-[16px]'
export default function GroupBPaperArchive({sources}:{sources:CollectionDetail[]}){
 const [params,setParams]=useSearchParams(),q=params.get('paper_q')||'',year=params.get('paper_year')||'',written=params.get('paper_kind')==='written',sort=paperOrder(params.get('paper_sort'))
 const sourceByPaper=Object.fromEntries(sources.flatMap(c=>c.paper_list.map(p=>[p.id,c.id])))
 const papers=[...new Map(sources.flatMap(c=>c.paper_list.map(p=>[p.id,p] as const))).values()]
 const tokens=q.toLowerCase().trim().split(/\s+/).filter(Boolean)
 const filtered=sortArchivePapers(papers.filter(p=>(!year||String(p.year)===year)&&(!written||p.descriptive>0)&&tokens.every(t=>`${p.title} ${p.exam||''} ${p.paper_label||''} ${p.subject||''} ${p.year||''}`.toLowerCase().includes(t))),sort)
 const groups=groupSourceBooklets(filtered)
 const pages=Math.max(1,Math.ceil(groups.length/10)),page=Math.min(pageNumber(params.get('paper_page')),pages),visibleGroups=groups.slice((page-1)*10,page*10),visible=visibleGroups.map(representativeBooklet)
 function update(key:string,value:string){setParams(old=>groupBNavigate(old,key,value),{replace:key!=='paper_page'})}
 return <section aria-labelledby="group-b-paper-heading" className="mt-6"><h2 id="group-b-paper-heading" className="font-display text-[30px]">Original paper library</h2><p className="mt-2 text-[14px] text-secondary">Find the exact recruitment, year and paper. Read written prompts or open the source PDF.</p>
  <div className="mt-4 grid gap-3 rounded-xl border border-hairline bg-paper p-4 sm:grid-cols-2 lg:grid-cols-4"><label className="min-w-0 text-[12px] font-semibold">Search papers<input className={INPUT} type="search" value={q} onChange={e=>update('paper_q',e.target.value)} placeholder="Post, department or subject"/></label><label className="min-w-0 text-[12px] font-semibold">Year<select className={INPUT} value={year} onChange={e=>update('paper_year',e.target.value)}><option value="">All years</option>{[...new Set(papers.map(p=>p.year).filter((v):v is number=>v!==null))].sort((a,b)=>b-a).map(y=><option key={y}>{y}</option>)}</select></label><label className="min-w-0 text-[12px] font-semibold">Paper content<select className={INPUT} value={written?'written':'all'} onChange={e=>update('paper_kind',e.target.value)}><option value="all">All papers</option><option value="written">Contains written questions</option></select></label><label className="min-w-0 text-[12px] font-semibold">Order<select className={INPUT} value={sort} onChange={e=>update('paper_sort',e.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="exam-asc">Exam A–Z</option><option value="exam-desc">Exam Z–A</option></select></label></div>
  <p role="status" className="mt-4 text-[12px] text-secondary">{groups.length} matching papers</p>
  {sources.map(c=>{const rows=visible.filter(p=>sourceByPaper[p.id]===c.id);return rows.length?<div key={c.id} className="mt-4">{sources.length>1&&<h3 className="font-display text-[24px]">{groupBTitle(c.id)}</h3>}<ExamPaperList papers={rows} groups={visibleGroups.filter(group=>rows.some(p=>p.id===representativeBooklet(group).id))} examId={c.id}/></div>:null})}
  {!filtered.length&&<p className="mt-4 rounded-xl border border-hairline bg-card p-5 text-[14px]">No papers match. Try a different year or clear your search.</p>}
  <Pagination page={page} pages={pages} onPageChange={value=>update('paper_page',String(value))} label="Group B paper library pages"/>
 </section>
}
