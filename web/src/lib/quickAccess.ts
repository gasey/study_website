import type {Collection} from './api'
import {ADMIN_SECTIONS,adminTabHref,canOpenAdminTab} from './adminNavigation'
import {reviewDestinations,type ReviewAccess} from './reviewNavigation'

export type QuickDestination={to:string;label:string;detail:string;group:string}
export type QuickTask='mixed'|'unseen'|'ever_wrong'|'papers'
export function quickStudyHref(id:string,task:QuickTask){
 const params=new URLSearchParams(task==='papers'?{view:'papers'}:{view:'browse',pool:'practice',order:'mixed',...(task==='mixed'?{}:{status:task})})
 return `/exams/${encodeURIComponent(id)}?${params}#${task==='papers'?'past-paper-results':'exam-question-browser'}`
}
export function quickDestinations(exams:Pick<Collection,'id'|'title'>[],access:ReviewAccess):QuickDestination[]{
 const study=[
  ['/feed','Study home','Continue your learning'],['/exams','Exams','UDC, LDC, Assistant and more'],
  ['/revision','Daily revision','Saved questions and words due for review'],['/mistakes','My mistakes','Return to questions you got wrong'],
  ['/desk','Study desk','Your saved work'],['/library','Subject library','Topics, reading and questions'],
  ['/search','Search everything','Questions, notes and people'],['/calendar','Exam calendar','Dates and notices'],
  ['/community','Community','Discussions and shared notes'],['/more','All tools','Learning, account and community'],
 ].map(([to,label,detail])=>({to,label,detail,group:'Study'}))
 const work=reviewDestinations(access).map(x=>({...x,detail:x.description,group:'Your workspaces'}))
 const admin=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],access.grants)).map(s=>({to:adminTabHref(s[0]),label:s[1],detail:s[4],group:'Admin tools'}))
 return [...study,...exams.map(e=>({to:'/exams/'+encodeURIComponent(e.id),label:e.title,detail:e.id+' · subjects, questions and original papers',group:'Exams'})),...work,...admin]
}
export function matchDestinations(items:QuickDestination[],query:string){
 const words=query.toLowerCase().trim().split(/\s+/).filter(Boolean)
 return items.filter(item=>words.every(word=>`${item.label} ${item.detail} ${item.group}`.toLowerCase().includes(word)))
}
