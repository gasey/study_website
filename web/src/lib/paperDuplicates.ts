import type {PaperQuestion} from './api'

// Source audit: docs/sources/group-b-gazetted-source-audit-20261104.json.
// These are presentation relationships, never canonical merges or scoring rules.
const paper='Old_Questions/Departmental_2015-2018/3.Departmental Exam for Inspector under Excise 2016 Paper III.pdf'
const auditedPairs=[
 ['desc-3d4c5f6b168c76b1d4c7','desc-753c3e58a04fcb5ae9c2'],
 ['desc-24fba67d3f50005033e2','desc-e3d98b0270a0a693994f'],
 ['desc-283b42d56fb5f626139d','desc-ab799471f0b8c1ac7b25'],
 ['desc-a80d7e65c38b0676e046','desc-34e715b051cb5aa44c71'],
] as const
const text=(value:string|null|undefined)=>(value||'').replace(/:\s*-/g,':').replace(/\s+/g,' ').trim()

/** Fail open to showing both records if either transcription changes. */
export function paperDuplicateGroups(paperId:string,items:PaperQuestion[]){
 const representative=new Map<string,string>(),byId=new Map(items.map(q=>[q.appearance_id,q]))
 if(paperId===paper)for(const [original,duplicate]of auditedPairs){
  const a=byId.get(original),b=byId.get(duplicate)
  if(!a||!b||a.type!=='descriptive'||b.type!=='descriptive'||!a.qnum||!a.page||a.qnum!==b.qnum||a.page!==b.page||a.series!==b.series)continue
  if(['question','direction','passage','question_markup','figure_image_url','source_defect','dispute_note'].some(key=>text(a[key as keyof PaperQuestion] as string|null)!==text(b[key as keyof PaperQuestion] as string|null)))continue
  if(a.options.length||b.options.length||a.held!==b.held||a.key_disputed!==b.key_disputed||a.answer_source!==b.answer_source||a.answer_status!==b.answer_status||a.taxonomy_subject_id!==b.taxonomy_subject_id||a.taxonomy_topic_id!==b.taxonomy_topic_id||a.marks!==b.marks)continue
  representative.set(duplicate,original)
 }
 return {representative,hidden:representative.size,printedCount:items.length-representative.size}
}

/** A direct record link must always reach that exact stored appearance. */
export function paperPresentationItems(items:PaperQuestion[],groups:ReturnType<typeof paperDuplicateGroups>,showAll:boolean,selected:string){
 return items.filter(q=>showAll||!groups.representative.has(q.appearance_id)||q.appearance_id===selected)
}
