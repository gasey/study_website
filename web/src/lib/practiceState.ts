import {loadPracticeStates,type PracticeState} from './api'
import {currentExamScope} from './examScope'
import {accountGeneration} from './accountContext'

type Pending={question_id:string;paper_id?:string|null;scope:string;generation:number;resolve:(state:PracticeState)=>void;reject:(error:unknown)=>void}
let pending:Pending[]=[],scheduled=false
/** One bounded private read per visible batch; no answer-bearing persistent cache. */
export function getPracticeState(question_id:string,paper_id?:string|null):Promise<PracticeState>{
 return new Promise((resolve,reject)=>{
  pending.push({question_id,paper_id,scope:currentExamScope(),generation:accountGeneration(),resolve,reject})
  if(!scheduled){scheduled=true;queueMicrotask(()=>void flush())}
 })
}
async function flush(){
 scheduled=false;const work=pending.splice(0)
 for(let offset=0;offset<work.length;offset+=100){
  const batch=work.slice(offset,offset+100),current=batch.filter(p=>p.scope===currentExamScope()&&p.generation===accountGeneration())
  for(const p of batch)if(!current.includes(p))p.reject(new Error('Your exam focus or account changed. Reload before continuing.'))
  if(!current.length)continue
  try{
   const response=await loadPracticeStates(current.map(({question_id,paper_id})=>({question_id,paper_id})))
   current.forEach((p,i)=>{if(p.scope!==currentExamScope()||p.generation!==accountGeneration())p.reject(new Error('Your account or exam focus changed. Reload before continuing.'));else p.resolve(response.items[i])})
  }catch(e){current.forEach(p=>p.reject(e))}
 }
}
