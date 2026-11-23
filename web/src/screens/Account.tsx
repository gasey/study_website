import {SignupReferral} from '../components/ReferralPanel'
import GroupRateClaim from '../components/GroupRateClaim'
import AgeCategoryCheck from '../components/AgeCategoryCheck'
import {mobileReturn} from '../lib/mobileReturn'
import GoogleSignIn from '../components/GoogleSignIn'
import {safeReturnPath,resetAccountContext} from '../lib/accountContext'
import {reviewRequest,reviewSession} from '../lib/review'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { cancelBilling, createCheckout, getAccountSession, getBilling, getBillingConfig, loginAccount, logoutAccount, registerAccount, verifyCheckout, type AccountSession, type BillingConfig } from '../lib/api'

const shell = 'mx-auto max-w-shell px-6 pb-24 pt-10'
const panel = 'rounded-[16px] border border-hairline bg-card p-6 shadow-[0_1px_2px_rgba(29,27,24,.05)]'
const input = 'mt-1.5 h-12 w-full rounded-[9px] border border-hairline bg-paper px-3 text-base outline-none focus:border-ink'
const button = 'rounded-pill bg-ink px-5 py-3 text-sm font-semibold text-white disabled:opacity-50'

export function AccountForm({ mode }: { mode: 'login' | 'join' }) {
  const [ageReady,setAgeReady]=useState(false)
  const [googleBusy,setGoogleBusy]=useState(false);const [code,setCode]=useState('');const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false)
  const location=useLocation();const mobileNext=mobileReturn(new URLSearchParams(location.search).get('next'));const next=mobileNext||safeReturnPath(new URLSearchParams(location.search).get('next'));const [saveGuest,setSaveGuest]=useState(false);const [guestCount,setGuestCount]=useState(0)
  useEffect(()=>{fetch('/api/auth/guest-progress',{credentials:'include',cache:'no-store'}).then(r=>r.json()).then(r=>setGuestCount(r.attempts||0)).catch(()=>{})},[])
  const nav=useNavigate(); const joining=mode==='join'
  const rawReferral=new URLSearchParams(location.search).get('ref');const referralCode=joining&&rawReferral&&/^[A-Za-z0-9_-]{24}$/.test(rawReferral)?rawReferral:undefined
  function removeReferral(){const params=new URLSearchParams(location.search);params.delete('ref');nav({pathname:location.pathname,search:params.toString()},{replace:true})}
  async function submit(e:FormEvent){ e.preventDefault();if(googleBusy||busy||joining&&!ageReady)return; setBusy(true);setError('');try{ if(joining) await registerAccount(email,password,referralCode); else await loginAccount(email,password,code); resetAccountContext();let transferError='';if(saveGuest){try{await reviewSession(true);await reviewRequest('/auth/guest-progress/save',{})}catch(e){transferError=(e as Error).message}}window.dispatchEvent(new Event('ism-auth-change'));if(mobileNext)window.location.assign(mobileNext);else nav(next);if(transferError)window.dispatchEvent(new CustomEvent('ism-account-notice',{detail:'Signed in. Guest progress could not be saved: '+transferError})) }catch(err){setError(err instanceof Error?err.message:'Could not sign in.')}finally{setBusy(false)} }
  return <main className={shell+' finna-account-page'}><div className="mx-auto max-w-[480px]">
    <div className="mb-5 font-mono text-xs uppercase tracking-[.12em] text-muted">Finna · Account</div>
    <section className={panel}><h1 className="font-display text-2xl font-medium">{joining?'Join free':'Welcome back'}</h1>
      <p className="mt-2 text-sm leading-relaxed text-secondary">{joining?'Finna is for people aged 18 or over. Save your progress across devices. New accounts include a seven-day Pro trial with no card required.':'Finna is for people aged 18 or over. Sign in to continue, or manage your existing account and data.'}</p>
      {new URLSearchParams(location.search).has('recovered')&&<p role="status" className="mt-4 text-sm">Your password was saved. Sign in to continue.</p>}
      {new URLSearchParams(location.search).has('reopened')&&<p role="status" className="mt-4 text-sm">Your account is reopened. Sign in with your new password; reconnect Google and set up MFA again if you used them.</p>}
      {new URLSearchParams(location.search).has('closed')&&<p role="status" className="mt-4 text-sm">Your account is closed and all devices have been signed out. If your email was verified, you can request a reopening link within 30 days.</p>}
      {error&&<p role="alert" className="mt-4 rounded-[9px] bg-wrong-soft p-3 text-sm text-wrong-dark">{error}</p>}
      <AgeCategoryCheck onReady={setAgeReady}/>{referralCode&&<SignupReferral key={referralCode} code={referralCode} onRemove={removeReferral} disabled={busy||googleBusy}/>}<GoogleSignIn referralCode={referralCode} disabled={busy||!ageReady} onBusyChange={setGoogleBusy}/>{new URLSearchParams(location.search).has("google_error")&&<p role="status">Google sign-in was cancelled. You can try again.</p>}<form onSubmit={submit} className="mt-5 space-y-4"><label className="block text-sm font-semibold">Email address<input className={input} type="email" autoComplete="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label>
        <label className="block text-sm font-semibold">Password<input className={input} type="password" autoComplete={joining?'new-password':'current-password'} minLength={joining?12:1} maxLength={200} required value={password} onChange={e=>setPassword(e.target.value)}/>{joining&&<span className="mt-1 block text-xs font-normal text-muted">At least 12 characters, including a letter and a number.</span>}</label>
        {!joining&&<label className="block text-sm font-semibold">Authenticator or recovery code <span className="font-normal text-muted">(if enabled)</span><input value={code} onChange={e=>setCode(e.target.value)} autoComplete="one-time-code" maxLength={64} className={input}/></label>}
        {guestCount>0&&<label className="flex gap-3 text-sm leading-relaxed"><input type="checkbox" checked={saveGuest} onChange={e=>setSaveGuest(e.target.checked)}/><span>Save this browser’s {guestCount} practice answers and study progress to my account. Past guest answers earn no XP.</span></label>}
        <button className={`${button} w-full`} disabled={busy||googleBusy||joining&&!ageReady}>{busy?'Please wait…':joining?'Create account':'Log in'}</button>
      </form>
      <p className="mt-5 text-center text-sm text-secondary">{joining?'Already have an account?':'New to India Study Map?'} <Link className="font-semibold text-link underline" to={(joining?'/login':'/join')+'?next='+encodeURIComponent(next)}>{joining?'Log in':'Join free'}</Link></p>
      {!joining&&<Link to="/account/recovery" className="mt-4 inline-flex min-h-11 items-center text-sm text-link underline">Forgot your password?</Link>}
      <p className="mt-4 border-t border-hairline pt-4 text-xs leading-relaxed text-muted">Use an email address you can access. Check Account recovery for current recovery availability.</p>
    </section>
  </div></main>
}

const planCards=[{period:'monthly',label:'Monthly',price:'₹100',note:'Billed monthly'}]
declare global { interface Window { Razorpay?: new (options:any)=>{open:()=>void}; } }
function loadCheckout():Promise<void>{return new Promise((resolve,reject)=>{if(window.Razorpay)return resolve();const s=document.createElement('script');s.src='https://checkout.razorpay.com/v1/checkout.js';s.onload=()=>resolve();s.onerror=()=>reject(new Error('Could not load secure checkout.'));document.body.append(s)})}

export function Plans(){
  const [config,setConfig]=useState<BillingConfig|null>(null);const [account,setAccount]=useState<AccountSession|null>(null);const [busy,setBusy]=useState('');const [msg,setMsg]=useState('');const [error,setError]=useState('');const nav=useNavigate()
  useEffect(()=>{getBillingConfig().then(setConfig);getAccountSession().then(setAccount)},[])
  async function checkout(period:string){if(!account?.authenticated){nav(`/join?next=${encodeURIComponent('/plans')}`);return}setBusy(period);setError('');setMsg('');try{const checkout=await createCheckout(period);await loadCheckout();const razor=new window.Razorpay!({key:checkout.key_id,subscription_id:checkout.subscription_id,name:checkout.name,description:checkout.description,prefill:{email:checkout.email},theme:{color:'#0A7D8C'},modal:{ondismiss:()=>setBusy('')},handler:async(result:any)=>{await verifyCheckout(result);setMsg('Payment verified. Your Pro plan is being activated.');setBusy('');window.dispatchEvent(new Event('ism-auth-change'))}});razor.open()}catch(e){setError(e instanceof Error?e.message:'Checkout could not start.');setBusy('')}}
  return <main className="finna-page at-plan-page">
    <header className="av-hero">
      <div className="av-hero-copy">
        <span className="cr-eyebrow">Plans · Razorpay Secure Checkout</span>
        <h1>Make room to focus</h1>
        <p>The question bank, exams, and community stay free. Pro adds unlimited practice, timed mocks, and smart mistakes review.</p>
      </div>
      <div className="av-hero-actions">
        <Link to="/profile" className="cr-glass-btn">← Profile</Link>
        <Link to="/profile/rewards" className="cr-glass-btn">Earn free Pro days →</Link>
      </div>
    </header>
    <div className="at-trial-banner"><strong>7 days of Pro included</strong> with every new account — no card required, no automatic charge.</div>
    {error&&<p role="alert" className="at-inline-err">{error}</p>}
    {msg&&<p role="status" className="finna-st-notice">{msg}</p>}
    <div className="at-plans-grid">
      <section className="at-card">
        <div className="at-card-head"><div><h3>Free forever</h3><p>Everything you need to start studying</p></div><span className="finna-st-pill finna-st-pill--gray">₹0</span></div>
        <ul className="at-plan-list"><li>✓ Full MPSC question bank &amp; source papers</li><li>✓ Exam guides, Chronicle &amp; Atlas</li><li>✓ Community discussions &amp; private study desk</li></ul>
      </section>
      {planCards.map(p=><section key={p.period} className="at-card at-card--pro">
        <div className="at-card-head"><div><h3>Pro · {p.label}</h3><p>{p.note}</p></div><span className="finna-st-pill finna-st-pill--teal">Popular</span></div>
        <div className="at-plan-price">{config?.plans.find(plan=>plan.period===p.period)?.amount_paise!=null?new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(config.plans.find(plan=>plan.period===p.period)!.amount_paise/100):p.price}<span>/mo</span></div>
        <ul className="at-plan-list"><li>✓ Unlimited timed mock papers &amp; analytics</li><li>✓ Smart Review spaced-repetition queue</li><li>✓ Cancel anytime — zero lock-in</li></ul>
        <button disabled={!config?.enabled||busy!==''} onClick={()=>void checkout(p.period)} className="cr-primary-btn mt-4 w-full">{!config?.enabled?'Payments setting up':busy===p.period?'Opening checkout…':'Choose Pro'}</button>
      </section>)}
    </div>
    {!config?.enabled&&<p className="text-xs text-secondary">Paid plans are not available yet. You can continue using all free features.</p>}
    <section className="at-card"><div className="at-card-head"><div><h3>Class plan</h3><p>Designed for teacher-led cohorts — currently in development and not open for purchase yet.</p></div><span className="finna-st-pill finna-st-pill--gray">Coming later</span></div></section>
  </main>
}

export function Billing(){const [data,setData]=useState<any>(null);const [err,setErr]=useState('');useEffect(()=>{getBilling().then(setData).catch(e=>setErr(e.message))},[]);async function cancel(){try{await cancelBilling();setData(await getBilling())}catch(e){setErr(e instanceof Error?e.message:'Cancellation failed')}}return <main className="finna-page at-plan-page">
  <header className="av-hero">
    <div className="av-hero-copy">
      <span className="cr-eyebrow">Membership &amp; Receipts</span>
      <h1>Plan &amp; billing</h1>
      <p>View your active plan, earned Pro reward windows, and renewal status.</p>
    </div>
    <div className="av-hero-actions">
      <Link to="/profile" className="cr-glass-btn">← Profile</Link>
      <Link to="/plans" className="cr-glass-btn cr-glass-btn--accent">View plans</Link>
    </div>
  </header>
  {err&&<p role="alert" className="at-inline-err">{err}</p>}
  {data?<section className="at-card">
    <div className="at-card-head">
      <div><h2 className="capitalize">{data.plan_code} · {data.plan_status}</h2>{data.email&&<p>{data.email}</p>}</div>
      <span className={data.plan_code==='pro'?'finna-st-pill finna-st-pill--green':'finna-st-pill finna-st-pill--gray'}>{data.plan_status}</span>
    </div>
    <div className="flex flex-col gap-2 text-sm text-secondary">
      {data.trial_ends_at&&data.plan_status==='trial'&&<p>Trial ends {new Date(data.trial_ends_at).toLocaleDateString('en-IN')}</p>}
      {data.plan_code==='pro'&&data.plan_status==='active'&&!data.plan_ends_at&&!data.razorpay_subscription_id&&<p>Unlimited Pro access · no expiry date</p>}
      {data.reward_access?.map((r:any,i:number)=><p key={i}>Earned Pro access: {new Date(r.starts_at).toLocaleDateString('en-IN')} – {new Date(r.ends_at).toLocaleDateString('en-IN')}</p>)}
      {data.granted_access?.map((g:any,i:number)=><p key={'grant-'+i}>{g.source==='referral'?'Invitation Pro access':'Extra Pro access'}: {new Date(g.starts_at).toLocaleDateString('en-IN')} – {new Date(g.ends_at).toLocaleDateString('en-IN')}</p>)}
      {data.subscription&&<p>{data.subscription.billing_period.replace('_',' ')} · {data.subscription.status}{data.subscription.current_end?` · current period ends ${new Date(data.subscription.current_end).toLocaleDateString('en-IN')}`:''}</p>}
    </div>
    <div className="mt-4 flex flex-wrap gap-2">
      <Link to="/plans" className="cr-primary-btn">View plans</Link>
      <Link to="/profile/rewards" className="finna-st-btn">Earned Pro rewards</Link>
      {data.razorpay_subscription_id&&<button onClick={()=>void cancel()} className="at-danger-btn">Cancel renewal</button>}
    </div>
  </section>:<div className="finna-card text-sm text-secondary">Loading billing details…</div>}
  <GroupRateClaim/>
</main>}

export function LogoutButton(){const nav=useNavigate();return <button onClick={async()=>{await logoutAccount();window.dispatchEvent(new Event('ism-auth-change'));nav('/')}} className="rounded-pill border border-ink px-4 py-2 text-sm font-semibold">Sign out</button>}
