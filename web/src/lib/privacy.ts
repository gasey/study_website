import {accountGeneration} from './accountContext'
import {reviewSession} from './review'

export type PrivacyStatus={user_id:string|null;category:'adult'|'under18'|null;version:number;browser_category:'adult'|'under18'|null;age_check_enabled:boolean;guardian_enrollment_available:false;support_email:string}

async function request<T>(path:string,body?:unknown,signedIn=false):Promise<T>{
 const epoch=accountGeneration(),headers:Record<string,string>={'content-type':'application/json'}
 if(body!==undefined&&signedIn)headers['x-review-csrf']=(await reviewSession()).csrf
 const r=await fetch('/api/account-privacy/'+path,{method:body===undefined?'GET':'POST',credentials:'include',cache:'no-store',headers,...(body===undefined?{}:{body:JSON.stringify(body)})})
 const data=await r.json()
 if(epoch!==accountGeneration())throw new Error('Your account changed. Reload before continuing.')
 if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request could not be saved. Reload and try again.')
 return data as T
}
export const privacyStatus=()=>request<PrivacyStatus>('status')
export async function declareAge(status:PrivacyStatus,category:'adult'|'under18'){
 await request('declare',{category,user_id:status.user_id,expected_version:status.version},!!status.user_id)
 if(category==='adult'&&status.user_id&&status.category!=='adult')await request('confirm-adult',{user_id:status.user_id,expected_version:status.version},true)
 window.dispatchEvent(new Event('finna-audience-change'))
}
