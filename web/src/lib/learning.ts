import {reviewSession} from './review'
import {deviceId} from './device'
import {currentExamScope} from './examScope'
export async function learningRequest<T>(path:string,user:string,body?:unknown):Promise<T>{
 const session=await reviewSession()
 if(session.user_id!==user)throw new Error('Your signed-in account changed. Reload before continuing.')
 const response=await fetch('/api/learning'+path,{method:body===undefined?'GET':'POST',credentials:'include',cache:'no-store',headers:{'content-type':'application/json','x-device-id':deviceId(),'x-learning-user':user,...body===undefined?{}:{'x-review-csrf':session.csrf}},...body===undefined?{}:{body:JSON.stringify(body)}})
 if(!response.ok){const error=await response.json().catch(()=>({}));throw new Error(typeof error.detail==='string'?error.detail:'The study request could not be completed. Please retry.')}
 return response.json()
}
export interface ResumeItem{kind:string;title:string;detail:string;url:string;updated_at:string|null}
export interface ResumePage{items:ResumeItem[];checkpoint_version:number}
export interface RevisionOverview{day:string;available:number;mistakes:number;saved:number;vocabulary:number;session_id:string|null;daily_limit:number}
export interface RevisionSession{id:string;day:string;exam_scope:string;items:{id:string;question:string|null;subject:string|null;reasons:string[];state:'ready'|'completed'|'unavailable'}[]}
let writes=Promise.resolve()
export function savePracticePosition(qid:string,appearanceId?:string|null):Promise<void>{
 const routeParams=new URLSearchParams(window.location.search);for(const key of ['resume_question','update','post'])routeParams.delete(key);
 const route=window.location.pathname+(routeParams.size?'?'+routeParams:'')
 if(!/^\/(bank|group-b|english|mizo|arithmetic|essay|desk|library|exams)(\/|$)/.test(route.split('?')[0]))return Promise.resolve()
 const scope=currentExamScope()
 const captured=reviewSession()
 const task=writes.catch(()=>{}).then(async()=>{
  const session=await captured
  const latest=await learningRequest<ResumePage>('/resume?exam_scope='+scope,session.user_id)
  await learningRequest('/checkpoint',session.user_id,{route,question_id:qid,appearance_id:appearanceId||null,expected_version:latest.checkpoint_version})
 })
 writes=task.catch(()=>{})
 return task
}
