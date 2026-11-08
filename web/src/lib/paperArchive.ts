import type {CollectionPaper} from './api'
export type PaperOrder='newest'|'oldest'|'exam-asc'|'exam-desc'
export function paperOrder(value:string|null):PaperOrder {
 return value==='oldest'||value==='exam-asc'||value==='exam-desc'?value:'newest'
}
/** Sort before pagination; unknown years stay last in either date direction. */
export function sortArchivePapers(papers:CollectionPaper[],order:PaperOrder){
 const name=(p:CollectionPaper)=>p.exam?.trim()||p.title
 const compareName=(a:CollectionPaper,b:CollectionPaper)=>name(a).localeCompare(name(b),undefined,{numeric:true,sensitivity:'base'})
 const compareYear=(a:CollectionPaper,b:CollectionPaper,direction:number)=>a.year==null?(b.year==null?0:1):b.year==null?-1:direction*(a.year-b.year)
 return [...papers].sort((a,b)=>{
  const primary=order==='exam-asc'?compareName(a,b):order==='exam-desc'?-compareName(a,b):compareYear(a,b,order==='oldest'?1:-1)
  return primary||(order.startsWith('exam-')?compareYear(a,b,-1):compareName(a,b))||a.id.localeCompare(b.id,undefined,{numeric:true})
 })
}
