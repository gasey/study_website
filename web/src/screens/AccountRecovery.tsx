import {useEffect,useState,type FormEvent} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import {accountContext} from '../lib/accountContext'

const INPUT='mt-2 min-h-12 w-full rounded-[8px] border border-hairline bg-paper px-3 text-base'

export default function AccountRecovery(){
 const navigate=useNavigate()
 const [available,setAvailable]=useState<boolean|null>(null)
 const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[code,setCode]=useState('')
 const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false)
 const [fragment]=useState(()=>new URLSearchParams(location.hash.slice(1)))
 const reset=fragment.get('reset'),verify=fragment.get('verify'),reopen=fragment.get('reopen')

 useEffect(()=>{
  fetch('/api/auth/recovery/status',{credentials:'include',cache:'no-store'})
   .then(r=>r.json()).then(r=>setAvailable(r.available))
   .catch(()=>setError('Recovery status could not load. Refresh to retry.'))
 },[])

 async function submit(e:FormEvent){
  e.preventDefault();setBusy(true);setError('')
  try{
   const identity=await accountContext()
   const path=verify?'/email/confirm':reopen?'/reopen/complete':reset?'/recovery/complete':'/recovery/request'
   const body=verify?{token:verify}:reset||reopen?{token:reset||reopen,password,...(reset?{code:code||undefined}:{})}:{email}
   const r=await fetch('/api/auth'+path,{method:'POST',credentials:'include',headers:{'content-type':'application/json','x-review-csrf':identity.csrf||''},body:JSON.stringify(body)})
   const data=await r.json()
   if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'Please check your details and retry.')
   setPassword('');setCode('');setNotice(data.message||(verify?'Email verified. You can continue studying.':'Saved.'))
   if(reset||verify||reopen){
    history.replaceState(null,'','/account/recovery');window.dispatchEvent(new Event('ism-auth-change'))
    navigate(reset?'/login?recovered=1':reopen?'/login?reopened=1':'/account/security',{replace:true})
   }
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 const hasToken=Boolean(reset||verify||reopen)
 const title=verify?'Verify your email':reset?'Choose a new password':reopen?'Reopen your account':'Recover your account'
 const description=reopen
  ?'This single-use link reopens your account during the 30-day window. Choose a fresh password, then sign in again. Reconnect Google and set up MFA again if you used them.'
  :reset?'If your account has an authenticator, you will also need an unused authenticator or recovery code.'
  :verify?'Confirm this link to verify your email address.'
  :'Request a link using the email address on your account. If the address belongs to a closed account still within its 30-day window, the link will reopen it.'

 return <main className="mx-auto max-w-[520px] px-4 py-10"><section className="rounded-[16px] border border-hairline bg-card p-6">
  <h1 className="font-display text-2xl">{title}</h1>
  <p className="mt-3 text-sm text-secondary">{description}</p>
  {error&&<p role="alert" className="mt-4 text-sm text-mypick">{error}</p>}
  {notice?<div role="status" className="mt-4 text-sm">{notice}<Link to="/login" className="mt-4 block min-h-11 text-link underline">Sign in →</Link></div>:<>
   {!hasToken&&available===false?<p className="mt-5 text-sm text-secondary">Email recovery is awaiting mail-service setup. Contact site support for access help.</p>:<form onSubmit={e=>void submit(e)} className="mt-5 space-y-4">
    {!hasToken&&<label className="block text-sm">Account email<input required type="email" autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)} className={INPUT}/></label>}
    {(reset||reopen)&&<><label className="block text-sm">New password<input required type="password" minLength={12} maxLength={200} autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)} className={INPUT}/><span className="mt-1 block text-xs text-secondary">At least 12 characters, including a letter and a number.</span></label>{reset&&<label className="block text-sm">Authenticator or recovery code, if enabled<input autoComplete="one-time-code" maxLength={64} value={code} onChange={e=>setCode(e.target.value)} className={INPUT}/></label>}</>}
    {hasToken&&<p className="rounded-lg bg-paper p-3 text-sm">This link expires after 30 minutes and can be used once.</p>}
    <button disabled={busy||(!hasToken&&available!==true)} className="min-h-12 rounded-pill bg-ink px-5 text-sm text-paper disabled:opacity-50">{busy?'Please wait…':verify?'Verify email':reset||reopen?'Save password':'Send recovery link'}</button>
   </form>}
  </>}
  <Link to="/login" className="mt-5 inline-flex min-h-11 items-center text-sm text-link underline">Back to sign in</Link>
 </section></main>
}
