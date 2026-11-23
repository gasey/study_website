import {useEffect,useState,type FormEvent} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import {accountContext} from '../lib/accountContext'

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

 return <main className="at-sub-page at-sub-page--narrow">
  <section className="at-card">
   <span className="cr-eyebrow">Account recovery</span>
   <h1 className="font-display text-2xl font-bold">{title}</h1>
   <p className="text-sm leading-relaxed text-secondary">{description}</p>
   {error&&<p role="alert" className="at-inline-err">{error}</p>}
   {notice?<div role="status" className="finna-st-notice">{notice} <Link to="/login" className="ml-2 underline">Sign in →</Link></div>:<>
    {!hasToken&&available===false?<p className="text-sm text-secondary">Email recovery is awaiting mail-service setup. Contact site support for access help.</p>:<form onSubmit={e=>void submit(e)} className="space-y-4">
     {!hasToken&&<label className="at-field"><span>Account email</span><input required type="email" autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label>}
     {(reset||reopen)&&<><label className="at-field"><span>New password</span><input required type="password" minLength={12} maxLength={200} autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)}/><small className="text-xs text-secondary">At least 12 characters, including a letter and a number.</small></label>{reset&&<label className="at-field"><span>Authenticator or recovery code, if enabled</span><input autoComplete="one-time-code" maxLength={64} value={code} onChange={e=>setCode(e.target.value)}/></label>}</>}
     {hasToken&&<p className="finna-st-notice">This link expires after 30 minutes and can be used once.</p>}
     <button disabled={busy||(!hasToken&&available!==true)} className="cr-primary-btn">{busy?'Please wait…':verify?'Verify email':reset||reopen?'Save password':'Send recovery link'}</button>
    </form>}
   </>}
   <div className="at-card-foot"><Link to="/login" className="at-link">← Back to sign in</Link></div>
  </section>
 </main>
}
