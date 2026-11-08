import type {GroupBStudyArea} from './api'

export const GROUP_B_COLLECTIONS=['group-b-non-gazetted','group-b-gazetted'] as const
export const GROUP_B_AREAS:GroupBStudyArea[]=['common','english','gk-gs','technical']
export function groupBState(params:URLSearchParams){
 const requested=params.get('collection')
 const collection=requested==='group-b'||GROUP_B_COLLECTIONS.some(id=>id===requested)?requested!:'group-b-non-gazetted'
 const area=GROUP_B_AREAS.includes(params.get('study_area') as GroupBStudyArea)?params.get('study_area') as GroupBStudyArea:'common'
 const requestedView=params.get('view')
 const view=requestedView==='home'||requestedView==='practice'||requestedView==='browse'||requestedView==='topics'||requestedView==='papers'||requestedView==='progress'?requestedView:area==='common'?'home':'topics'
 return {collection,area,view,nonGazetted:collection==='group-b-non-gazetted'}
}
export function groupBAreaLabel(area:GroupBStudyArea,collection:string){
 const ng=collection==='group-b-non-gazetted'
 return {common:ng?'English & GK':'English & GK/GS',english:'General English','gk-gs':ng?'General Knowledge':'General Knowledge & Studies',technical:'Technical papers'}[area]
}
/** Changing scope discards incompatible filters; mode changes retain the topic. */
export function groupBNavigate(previous:URLSearchParams,key:string,value:string){
 const next=new URLSearchParams(previous)
 next.set('collection',groupBState(previous).collection)
 next.set(key,value)
 if(key==='collection'||key==='study_area'||(key==='view'&&value==='home')){
  for(const field of ['paper','section','subject_id','topic_id','subtopic_id','offset','q','answer_status','pool','status','technical_q','technical_page','resume_question','session','paper_q','paper_year','paper_sort','paper_page','paper_kind'])next.delete(field)
  if(key==='collection'||value==='home')next.set('study_area','common')
  next.set('view',key==='study_area'&&value!=='common'?'topics':'home')
 }else if(key==='view'){
  next.delete('offset');next.delete('answer_status')
  if(value==='practice'||value==='browse')next.set('pool',value==='practice'?'practice':'all')
 }else if(key==='technical_q')next.delete('technical_page')
 else if(['paper_q','paper_year','paper_sort','paper_kind'].includes(key))next.delete('paper_page')
 return next
}
export function learningSubjectTitle(id:string,title:string,collection:string){
 return collection==='group-b-non-gazetted'&&id==='gk-gs'?'General Knowledge':title
}

export function groupBTitle(collection:string){
 return collection==='group-b-non-gazetted'?'Group B Non-Gazetted':collection==='group-b-gazetted'?'Group B Gazetted':'Group B shared study'
}
export function groupBLink(collection:string,view:string='home',extra:Record<string,string>={}){
 return '/group-b?'+new URLSearchParams({...extra,collection,view})
}

/** Only landing pages move; existing paper/question/practice deep links keep their scope. */
export function groupBOverviewDestination(id:string,params:URLSearchParams){
 return GROUP_B_COLLECTIONS.some(value=>value===id)&&(!params.get('view')||params.get('view')==='overview')?groupBLink(id):null
}
