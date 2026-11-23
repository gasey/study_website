import PasswordSettings from '../components/PasswordSettings'
import GoogleSignIn from '../components/GoogleSignIn'
import EmailVerification from '../components/EmailVerification'
import AccountSessions from '../components/AccountSessions'
import {useEffect,useState,type FormEvent} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest,reviewSession} from '../lib/review'
interface Status{configured:boolean;enabled:boolean;verified:boolean;staff_required:boolean;recovery_codes_remaining:number}
const INPUT='mt-2 min-h-12 w-full rounded-[8px] border border-hairline bg-paper px-3 text-base'
export default function AccountSecurity(){
 const [status,setStatus]=useState<Status|null>(null);const [password,setPassword]=useState('');const [code,setCode]=useState('')
 const [setup,setSetup]=useState<{setup_key:string;qr_data_url:string}|null>(null);const [recovery,setRecovery]=useState<string[]>([])
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [notice,setNotice]=useState('')
 async function load(){setStatus(await reviewRequest<Status>('/auth/mfa/status'))}
 useEffect(()=>{let live=true;reviewSession(true).then(()=>reviewRequest<Status>('/auth/mfa/status')).then(s=>{if(live)setStatus(s)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[])
 async function action(type:'setup'|'confirm'|'verify'|'recovery-codes'|'disable',event?:FormEvent){event?.preventDefault();setBusy(true);setError('');setNotice('');try{
   if(type==='setup'){const result=await reviewRequest<{setup_key:string;qr_data_url:string}>('/auth/mfa/setup',{password});setSetup(result);setCode('');setRecovery([]);setPassword('')}
   else if(type==='confirm'){const result=await reviewRequest<{recovery_codes:string[]}>('/auth/mfa/confirm',{code});setRecovery(result.recovery_codes);setSetup(null);setCode('');setNotice('Authenticator enabled. Save the recovery codes below.')}
   else if(type==='verify'){await reviewRequest('/auth/mfa/verify',{code});setCode('');setNotice('This session is verified for staff changes for 15 minutes.')}
   else if(type==='recovery-codes'){const result=await reviewRequest<{recovery_codes:string[]}>('/auth/mfa/recovery-codes',{password,code});setRecovery(result.recovery_codes);setPassword('');setCode('');setNotice('Previous recovery codes are invalid. Save the new codes below.')}
   else{await reviewRequest('/auth/mfa/disable',{password,code});setRecovery([]);setPassword('');setCode('');setNotice('Authenticator disabled. Other signed-in sessions were revoked.')}
   window.dispatchEvent(new Event('ism-auth-change'));await reviewSession(true);await load()
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <main className="at-sub-page">
  <header className="av-hero">
   <div className="av-hero-copy">
    <span className="cr-eyebrow">Account security</span>
    <h1>Protect your account</h1>
    <p>Use an authenticator app for a six-digit code at sign-in, manage recovery codes, and review active sessions.</p>
   </div>
   <div className="av-hero-actions">
    <Link to="/profile" className="cr-glass-btn">← Profile</Link>
    <Link to="/account/privacy" className="cr-glass-btn">Privacy requests</Link>
   </div>
  </header>
  <GoogleSignIn link/>
  {error&&<p role="alert" className="at-inline-err">{error} <Link to="/login" className="underline">Sign in again</Link></p>}
  {notice&&<p role="status" className="finna-st-notice">{notice}</p>}
  {status&&<><section className="at-card"><div className="at-card-head"><div><h2>Authenticator</h2><p>{status.staff_required?'Admin and reviewer changes require an enrolled authenticator and a recently verified session.':'Authenticator protection is optional for this account. You can continue using your account without setting it up.'}</p></div><span className={`finna-st-pill ${status.enabled?'finna-st-pill--green':'finna-st-pill--gray'}`}>{status.enabled?'Enabled':'Not enabled'}</span></div>{status.enabled&&<p className="text-sm">{status.verified?'This session is verified.':'Verify a code to unlock sensitive staff actions.'} {status.recovery_codes_remaining} recovery codes remain.</p>}
  {!status.configured?<p className="text-sm text-secondary">Authenticator setup is temporarily unavailable. Please try again later.</p>:setup?<form onSubmit={e=>void action('confirm',e)} className="mt-2"><h3 className="font-semibold">Add this account to your authenticator app</h3><img src={setup.qr_data_url} alt="Authenticator enrollment QR code" className="mt-4 h-[230px] w-[230px] max-w-full rounded-[12px] bg-white p-3"/><details className="mt-3 text-sm"><summary className="cursor-pointer">Enter a setup key instead</summary><code className="mt-2 block break-all rounded-[8px] bg-paper p-3">{setup.setup_key}</code></details><p className="mt-3 text-xs text-muted">Setup expires after ten minutes. Your existing authenticator stays active until confirmation.</p><label className="mt-4 block text-sm">Six-digit authenticator code<input required autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" value={code} onChange={e=>setCode(e.target.value)} className={INPUT}/></label><div className="mt-4 flex flex-wrap gap-3"><button disabled={busy} className="cr-primary-btn">Confirm authenticator</button><button type="button" onClick={()=>{setSetup(null);setCode('')}} className="finna-st-btn">Cancel setup</button></div></form>:<>
  {status.enabled&&!status.verified&&<form onSubmit={e=>void action('verify',e)} className="mt-2"><label className="block text-sm">Authenticator or unused recovery code<input required autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} className={INPUT}/></label><button disabled={busy} className="cr-primary-btn mt-3">Verify session</button></form>}
  {(!status.enabled||status.verified)&&<form onSubmit={e=>void action('setup',e)} className="mt-2"><label className="block text-sm">Current password<input type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} className={INPUT}/></label><button disabled={busy} className="cr-primary-btn mt-3">{status.enabled?'Replace authenticator':'Set up authenticator'}</button></form>}
  {status.enabled&&<details className="at-saved-details"><summary>Recovery codes and authenticator removal</summary><div className="mt-3 space-y-3"><label className="block text-sm">Current password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} className={INPUT}/></label><label className="block text-sm">Authenticator or unused recovery code<input autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} className={INPUT}/></label><div className="flex flex-wrap gap-3"><button disabled={busy||!password||!code} onClick={()=>void action('recovery-codes')} className="finna-st-btn">Generate new recovery codes</button>{!status.staff_required&&<button disabled={busy||!password||!code} onClick={()=>void action('disable')} className="at-danger-btn">Disable authenticator</button>}</div></div></details>}</>}
  </section>{recovery.length>0&&<section className="at-card at-card--pro"><div className="at-card-head"><div><h2>Save your recovery codes</h2><p>Each code works once. Shown only now and never saved in this browser.</p></div></div><ul className="grid gap-2 font-mono text-sm sm:grid-cols-2">{recovery.map(c=><li key={c} className="rounded-[8px] border border-hairline bg-paper px-3 py-2">{c}</li>)}</ul><div className="at-btn-row"><button onClick={()=>setRecovery([])} className="cr-primary-btn">I have saved these codes</button></div></section>}</>}
  <EmailVerification/>
  <PasswordSettings/>
  <section className="at-card"><AccountSessions/></section>
  <Link to="/admin/bank" className="at-link">Return to admin console →</Link>
 </main>
}
