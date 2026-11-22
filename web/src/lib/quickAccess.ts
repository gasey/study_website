import type {Collection} from './api'
import {EXAM_GUIDES} from './examGuideCatalog'
import {ADMIN_SECTIONS,adminTabHref,canOpenAdminTab} from './adminNavigation'
import {reviewDestinations,type ReviewAccess} from './reviewNavigation'
import {destinationsForSurface} from './siteMap'

export type QuickDestination={to:string;label:string;detail:string;group:string;keywords?:string}
export type QuickTask='mixed'|'unseen'|'ever_wrong'|'papers'|'overview'|'topics'|'practice'
export type QuickExam=Pick<Collection,'id'|'title'>
export function quickExams(exams:QuickExam[]):QuickExam[]{
 return [...exams,...EXAM_GUIDES.filter(guide=>!exams.some(exam=>exam.id===guide.id))]
}
export function quickStudyTasks(id:string){
 if(EXAM_GUIDES.some(guide=>guide.id===id))return [
  {id:'overview',label:'Choose branch & scheme',action:'Open exam',description:'Choose your engineering branch and exam regulations, then explore its syllabus and papers.'},
  {id:'mixed',label:'Browse past questions',action:'Browse questions',description:'Read MCQs and written questions from a source paper in your selected branch.'},
  {id:'topics',label:'Syllabus & revision',action:'Open syllabus',description:'Study the source-linked syllabus and update your personal revision checklist.'},
  {id:'practice',label:'Past-paper MCQs',action:'Start practice',description:'Practise eligible MCQs one at a time. Choose your branch and regulations in the exam.'},
  {id:'papers',label:'Original papers',action:'Read papers',description:'Read original exam papers and choose a year, branch and exam scheme.'},
 ] as const
 return [
  {id:'mixed',label:'Mixed practice',action:'Start practice',description:'Untimed questions with an available answer. Choose an option to check it.'},
  {id:'unseen',label:'Never attempted',action:'Try new questions',description:'Start with answerable questions you have not attempted before.'},
  {id:'ever_wrong',label:'Previously wrong',action:'Review mistakes',description:'Includes questions you got wrong, even if you later answered them correctly.'},
  {id:'papers',label:'Original papers',action:'Read papers',description:'Read the original source papers and choose a specific sitting.'},
 ] as const
}
export function quickStudyHref(id:string,task:QuickTask){
 if(EXAM_GUIDES.some(guide=>guide.id===id)){
  const view=task==='papers'?'papers':task==='topics'?'topics':task==='practice'?'practice':task==='mixed'?'browse':'overview'
  return `/exams/${encodeURIComponent(id)}?view=${view}${view==='practice'||view==='browse'?'#exam-question-browser':''}`
 }
 if(task==='papers')return `/exams/${encodeURIComponent(id)}?view=papers#past-paper-results`
 const params=new URLSearchParams({exam:id,autostart:'1',...(task==='unseen'||task==='ever_wrong'?{status:task}:{})})
 return `/practice?${params}`
}
const SECTION_GROUP:Record<string,string>={study:'Study',practice:'Practice',guides:'Guides',community:'Community',you:'You'}
export function quickDestinations(exams:Pick<Collection,'id'|'title'>[],access:ReviewAccess):QuickDestination[]{
 const manifest=destinationsForSurface('quickfind').map(d=>({to:d.path,label:d.label,detail:d.blurb,group:SECTION_GROUP[d.section]||'Study',keywords:d.keywords}))
 const work=reviewDestinations(access).map(x=>({...x,detail:x.description,group:'Your workspaces'}))
 const admin=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],access.grants)).map(s=>({to:adminTabHref(s[0]),label:s[1],detail:s[4],group:'Admin tools'}))
 return [...manifest,...quickExams(exams).map(e=>({to:'/exams/'+encodeURIComponent(e.id),label:e.title,detail:EXAM_GUIDES.some(guide=>guide.id===e.id)?'Choose a branch · syllabus, questions and original papers':e.id+' · subjects, questions and original papers',keywords:EXAM_GUIDES.find(guide=>guide.id===e.id)?.search,group:'Exams'})),...work,...admin]
}
export function matchDestinations(items:QuickDestination[],query:string){
 const words=query.toLowerCase().trim().split(/\s+/).filter(Boolean)
 return items.filter(item=>words.every(word=>`${item.label} ${item.detail} ${item.group} ${item.keywords||''}`.toLowerCase().includes(word)))
}
