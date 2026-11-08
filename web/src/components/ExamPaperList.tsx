import {groupSourceBooklets,representativeBooklet,withoutBooklet} from '../lib/sourceBooklets'
import {bookletLabel,type BookletGroup} from '../lib/mcsBooklets'
import {Link} from 'react-router-dom'
import type {CollectionPaper} from '../lib/api'
import {paperIdentity} from '../lib/paperIdentity'

export default function ExamPaperList({papers,examId,groups=groupSourceBooklets(papers)}:{papers:CollectionPaper[];examId:string;groups?:BookletGroup[]}){
 return <div className="mt-3 overflow-hidden rounded-[12px] border border-hairline bg-card" aria-label="Exam and year list">
  <div aria-hidden="true" className="hidden gap-4 border-b border-hairline bg-canvas px-4 py-3 text-[12px] font-semibold md:grid md:grid-cols-[72px_minmax(0,2fr)_minmax(0,1fr)_180px]"><span>Year</span><span>Examination</span><span>Paper</span><span>Open</span></div>
  <ul className="divide-y divide-hairline">{groups.map(group=>{const p=representativeBooklet(group);const identity=paperIdentity(p);return <li key={p.id} className="grid min-w-0 gap-2 p-4 md:grid-cols-[72px_minmax(0,2fr)_minmax(0,1fr)_180px] md:gap-4">
   <span className="font-mono text-[13px]">{p.year??'Unknown year'}</span>
   <div className="min-w-0"><h3 className="break-words text-[14px] font-semibold leading-relaxed">{group.papers.length>1?withoutBooklet(identity.exam||p.title):identity.exam||p.title}</h3><p className="mt-1 text-[12px] text-secondary">{p.questions.toLocaleString('en-IN')} questions{p.descriptive?` · ${p.descriptive} written`:''}</p></div>
   <div className="min-w-0"><p className="break-words text-[13px] text-secondary">{group.papers.length>1?group.title:identity.title}</p>{group.papers.length>1&&<details className="mt-1"><summary className="min-h-11 cursor-pointer py-3 text-[12px] font-semibold text-link">Other booklet originals</summary><ul className="space-y-1 text-[12px]">{group.papers.map(source=><li key={source.id}><Link className="inline-flex min-h-11 items-center text-link underline" to={`/exams/${examId}/paper?paper=${encodeURIComponent(source.id)}`}>{bookletLabel(source)} →</Link></li>)}</ul></details>}</div>
   <div className="flex flex-wrap items-start gap-x-4 text-[13px] font-semibold text-link">{p.questions>0&&<Link className="inline-flex min-h-11 items-center" to={`/exams/${examId}/paper?paper=${encodeURIComponent(p.id)}`}>Browse paper →</Link>}{p.source_pdf_url&&<a className="inline-flex min-h-11 items-center" href={p.source_pdf_url} target="_blank" rel="noreferrer">PDF ↗</a>}</div>
  </li>})}</ul>
 </div>
}
