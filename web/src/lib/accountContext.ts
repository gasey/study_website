/** Cookie credentials stay HttpOnly; only public session metadata lives here. */
export interface AccountContext {authenticated:boolean;state?:string;csrf?:string|null;expires_at?:string|null}
let pending:Promise<AccountContext>|null=null
let generation=0
export function resetAccountContext(){generation++;pending=null}
export function accountGeneration(){return generation}
export function accountContext():Promise<AccountContext>{
 if(pending)return pending
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),8000)
 return pending??(pending=fetch('/api/auth/session',{credentials:'include',cache:'no-store',signal:controller.signal}).then(async r=>{
  if(!r.ok)throw new Error('Account status could not load. Please retry.')
  return r.json()
 }).catch(e=>{pending=null;throw e}).finally(()=>clearTimeout(timer)))
}
window.addEventListener('ism-auth-change',resetAccountContext)
// Force a fresh account boundary in other tabs; never broadcast credentials.
window.addEventListener('ism-auth-change',()=>localStorage.setItem('ism.account-change',crypto.randomUUID()))
window.addEventListener('storage',e=>{if(e.key==='ism.account-change')window.location.reload()})
export function safeReturnPath(raw:string|null):string{
 if(!raw||!raw.startsWith('/')||raw.startsWith('//')||/[\\\u0000-\u0020]/.test(raw))return '/profile'
 try{const decoded=decodeURIComponent(raw);if(decoded.startsWith('//')||/[\\\u0000-\u0020]/.test(decoded)||/^\/(login|join|logout)(\/|\?|#|$)/.test(decoded))return '/profile';const url=new URL(raw,location.origin);if(url.origin!==location.origin||/^\/(login|join|logout)(\/|$)/.test(url.pathname))return '/profile';return url.pathname+url.search+url.hash}catch{return '/profile'}
}

export async function checkSessionRejected(identity:AccountContext){
 if(!identity.authenticated&&identity.state!=='expired')return
 try{const r=await fetch('/api/auth/session',{credentials:'include',cache:'no-store'});if(r.ok&&!(await r.json()).authenticated)window.dispatchEvent(new Event('ism-auth-expired'))}catch{/* An outage is not an expired session. */}
}
