import type {AdminGrant} from './adminNavigation'

// `/editorial` has not been a declared route since the V.14 consolidation; this chip
// 404'd on /index because the dead-link gate only resolves string literals in `to={...}`
// and this one is passed through a variable (§VIII.6).
export const REVIEW_WORKSPACE='/admin/bank?tab=editorial'
export const TAG_CLEANUP='/admin/bank?tab=editorial&workspace=attention&queue=tags'
export type ReviewAccess={grants:AdminGrant[];assigned:boolean}
export function reviewDestinations({grants,assigned}:ReviewAccess){
 const staff=grants.length>0
 if(!staff&&!assigned)return []
 return [
  {to:REVIEW_WORKSPACE,label:'Review workspace',description:'Continue a module or paper and track your progress.'},
  ...(staff?[
   {to:'/admin/bank',label:'Admin dashboard',description:'Bank-wide questions, submissions, papers and administration.'},
   {to:TAG_CLEANUP,label:'Find & fix tags',description:'Find reported tags and classification gaps across both banks.'},
  ]:[]),
 ]
}

/** Keep My work's exact position while opening a clean module-scoped tag list. */
export function moduleTagScope(previous:URLSearchParams,module:string){
 const params=new URLSearchParams(previous)
 for(const key of [...params.keys()])if(key.startsWith('tag_')||key==='retag_batch'||key==='tab')params.delete(key)
 params.set('workspace','attention');params.set('queue','tags');params.set('tag_module',module)
 return params
}
