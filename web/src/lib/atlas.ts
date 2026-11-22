import {deviceId} from './device'
import {accountGeneration} from './accountContext'
import {scopeLink} from './examScope'
export type AtlasLink={subject?:string;chapter_id:string;layer_id:string|null;event_id:string|null;title:string}
export function atlasUrl(link:AtlasLink){const q=new URLSearchParams({chapter:link.chapter_id});if(link.layer_id)q.set('layer',link.layer_id);if(link.event_id)q.set('event',link.event_id);return scopeLink('/atlas?'+q)}
export async function atlasRead<T>(path:string):Promise<T>{const generation=accountGeneration();const r=await fetch('/api'+path,{credentials:'include',headers:{'x-device-id':deviceId()}});if(!r.ok){let message='Atlas could not load';try{message=(await r.json()).detail||message}catch{}throw Error(message)}const data=await r.json();if(generation!==accountGeneration())throw Error('Your account changed. Reload Atlas.');return data}

export async function atlasAccount<T>(path:string,body?:unknown):Promise<T>{
 const epoch=accountGeneration();const {reviewSession}=await import('./review');const session=await reviewSession();
 const r=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'include',cache:'no-store',headers:{'content-type':'application/json','x-device-id':deviceId(),'x-learning-user':session.user_id,...(body===undefined?{}:{'x-review-csrf':session.csrf})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 if(epoch!==accountGeneration())throw Error('Your account changed. Reload Atlas.');
 if(!r.ok){if(r.status===401){const {accountContext,checkSessionRejected}=await import('./accountContext');await checkSessionRejected(await accountContext())}let message='Map activity could not be saved';try{const e=await r.json();message=typeof e.detail==='string'?e.detail:message}catch{}throw Error(message)}return r.json()
}
