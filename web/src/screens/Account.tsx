import {SignupReferral} from '../components/ReferralPanel'
import GroupRateClaim from '../components/GroupRateClaim'
import AgeCategoryCheck from '../components/AgeCategoryCheck'
import {mobileReturn} from '../lib/mobileReturn'
import GoogleSignIn from '../components/GoogleSignIn'
import CatLoginMascot, { CAT_MOOD_TEXT, type CatMood } from '../components/CatLoginMascot'
import {safeReturnPath,resetAccountContext} from '../lib/accountContext'
import {reviewRequest,reviewSession} from '../lib/review'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { cancelBilling, createCheckout, getAccountSession, getBilling, getBillingConfig, loginAccount, logoutAccount, registerAccount, verifyCheckout, type AccountSession, type BillingConfig } from '../lib/api'

export function AccountForm({ mode }: { mode: 'login' | 'join' }) {
  const [ageReady,setAgeReady]=useState(false)
  const [googleBusy,setGoogleBusy]=useState(false);const [code,setCode]=useState('');const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false)
  const [focusField,setFocusField]=useState<'none'|'email'|'password'|'code'>('none');const [showPassword,setShowPassword]=useState(false);const [showMfa,setShowMfa]=useState(false);const [petted,setPetted]=useState(false)
  const location=useLocation();const mobileNext=mobileReturn(new URLSearchParams(location.search).get('next'));const next=mobileNext||safeReturnPath(new URLSearchParams(location.search).get('next'));const [saveGuest,setSaveGuest]=useState(false);const [guestCount,setGuestCount]=useState(0)
  useEffect(()=>{fetch('/api/auth/guest-progress',{credentials:'include',cache:'no-store'}).then(r=>r.json()).then(r=>setGuestCount(r.attempts||0)).catch(()=>{})},[])
  const nav=useNavigate(); const joining=mode==='join'
  const rawReferral=new URLSearchParams(location.search).get('ref');const referralCode=joining&&rawReferral&&/^[A-Za-z0-9_-]{24}$/.test(rawReferral)?rawReferral:undefined
  function removeReferral(){const params=new URLSearchParams(location.search);params.delete('ref');nav({pathname:location.pathname,search:params.toString()},{replace:true})}
  async function submit(e:FormEvent){ e.preventDefault();if(googleBusy||busy||joining&&!ageReady)return; setBusy(true);setError('');try{ if(joining) await registerAccount(email,password,referralCode); else await loginAccount(email,password,code); resetAccountContext();let transferError='';if(saveGuest){try{await reviewSession(true);await reviewRequest('/auth/guest-progress/save',{})}catch(e){transferError=(e as Error).message}}window.dispatchEvent(new Event('ism-auth-change'));if(mobileNext)window.location.assign(mobileNext);else nav(next);if(transferError)window.dispatchEvent(new CustomEvent('ism-account-notice',{detail:'Signed in. Guest progress could not be saved: '+transferError})) }catch(err){setError(err instanceof Error?err.message:'Could not sign in.')}finally{setBusy(false)} }
  const catMood: CatMood = petted || busy ? 'happy' : error ? 'error' : focusField === 'password' ? (showPassword ? 'peek' : 'password') : focusField === 'email' || focusField === 'code' ? 'email' : 'idle'
  const cardLift = focusField === 'password'
  const nextQs = '?next=' + encodeURIComponent(next)

  return <main className="cat-auth-scene finna-account-page">
    {/* 1b/1c Split Library Reading-Room Editorial Panel (desktop >= 960px) */}
    <aside className="cat-auth-hero" aria-label="About Finna">
      <img src="/images/discover/guides.jpg" alt="" className="cat-auth-hero-img" loading="eager" />
      <div className="cat-auth-hero-scrim" aria-hidden="true" />
      <div className="cat-auth-hero-inner">
        <Link to="/home" className="cat-auth-brand is-light">
          <span className="cat-auth-brand-word">Finna<i>.</i></span>
          <span className="cat-auth-brand-tag">MPSC Study</span>
        </Link>

        <div className="cat-auth-hero-copy">
          <span className="cat-auth-hero-kicker">FINNA · MPSC &amp; MIZORAM EXAM STUDY</span>
          <h2>Master MPSC &amp; Mizoram exams with real past papers</h2>
          <p>
            82,000+ past-paper questions · 11 free Concept Guides · Full-Paper Mocks &amp;
            16-bit RPG drills — free to start, no sign-in needed.
          </p>
          <ul className="cat-auth-perks">
            <li>Every question keeps its source paper and answer label</li>
            <li>Your Vault, streak and progress sync across devices</li>
            <li>Free to practise; sign in only to save</li>
          </ul>
        </div>

        <span className="cat-auth-hero-foot">India Study Map · Aizawl</span>
      </div>
    </aside>

    {/* Right Auth Canvas (lamp glow + 44px graph lines) */}
    <div className="cat-auth-pane">
      <div className="cat-auth-bg-lamp" aria-hidden="true" />
      <div className="cat-auth-bg-grid" aria-hidden="true" />

      <div className="cat-auth-topbar">
        <Link to="/home" className="cat-auth-brand cat-auth-brand-mobile">
          <span className="cat-auth-brand-word">Finna<i>.</i></span>
          <span className="cat-auth-brand-tag">MPSC Study</span>
        </Link>
        <Link to="/home" className="cat-auth-back">← Back to study home</Link>
      </div>

      <div className="cat-auth-shell">
        <CatLoginMascot
          mood={catMood}
          emailProgress={Math.min(1, email.length / 28)}
          hidePill
          onPet={() => {
            setPetted(true)
            window.setTimeout(() => setPetted(false), 1200)
          }}
        />

        <section className={`cat-auth-card${cardLift ? ' is-up' : ''}${error ? ' is-error' : ''}`}>
          <span className="cat-mood-pill cat-mood-pill--edge" aria-live="polite">
            {CAT_MOOD_TEXT[catMood]}
          </span>

          {/* Segmented Log in / Join free pill switcher */}
          <nav className="cat-mode-tabs" aria-label="Account mode">
            <Link to={'/login' + nextQs} className={`cat-mode-tab${!joining ? ' is-active' : ''}`}>
              Log in
            </Link>
            <Link to={'/join' + nextQs} className={`cat-mode-tab${joining ? ' is-active' : ''}`}>
              Join free
            </Link>
          </nav>

          <header className="cat-card-head">
            <h1>{joining ? 'Create your study safe' : 'Welcome back'}</h1>
            <p>
              {joining
                ? 'Save progress across devices & unlock a 7-day Pro trial — no card required.'
                : 'Sign in to sync your past papers, Personal Question Vault, and study streak.'}
            </p>
          </header>

          {new URLSearchParams(location.search).has('recovered') && (
            <p role="status" className="cat-status-pill">Your password was saved. Sign in to continue.</p>
          )}
          {new URLSearchParams(location.search).has('reopened') && (
            <p role="status" className="cat-status-pill">Your account is reopened. Sign in with your new password; reconnect Google and MFA if used.</p>
          )}
          {new URLSearchParams(location.search).has('closed') && (
            <p role="status" className="cat-status-pill">Your account is closed and signed out. Verified emails can request a reopening link within 30 days.</p>
          )}
          {error && <p role="alert" className="cat-error-banner">{error}</p>}

          <AgeCategoryCheck compact onReady={setAgeReady} />
          {referralCode && <SignupReferral key={referralCode} code={referralCode} onRemove={removeReferral} disabled={busy || googleBusy} />}

          <div className="cat-google-wrap">
            <GoogleSignIn referralCode={referralCode} disabled={busy || !ageReady} onBusyChange={setGoogleBusy} />
            {new URLSearchParams(location.search).has('google_error') && (
              <p role="status" className="cat-status-pill">Google sign-in was cancelled. You can try again.</p>
            )}
          </div>

          <div className="cat-divider" aria-hidden="true">
            <span>or with email</span>
          </div>

          <form onSubmit={submit} className="cat-form">
            <div className={`cat-field${focusField === 'email' ? ' is-focused' : ''}${email ? ' is-filled' : ''}`}>
              <div className="cat-field-inner">
                <input
                  id="finna-auth-email"
                  type="email"
                  autoComplete="email"
                  required
                  maxLength={254}
                  placeholder=" "
                  value={email}
                  onFocus={() => setFocusField('email')}
                  onBlur={() => setFocusField('none')}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <label htmlFor="finna-auth-email">Email address</label>
              </div>
            </div>

            <div className={`cat-field${focusField === 'password' ? ' is-focused' : ''}${password ? ' is-filled' : ''}`}>
              <div className="cat-field-inner">
                <input
                  id="finna-auth-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={joining ? 'new-password' : 'current-password'}
                  minLength={joining ? 12 : 1}
                  maxLength={200}
                  required
                  placeholder=" "
                  value={password}
                  onFocus={() => setFocusField('password')}
                  onBlur={() => setFocusField('none')}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <label htmlFor="finna-auth-password">Password</label>
              </div>
              <button
                type="button"
                className="cat-pw-toggle-inline"
                aria-pressed={showPassword}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  setShowPassword((v) => !v)
                  setFocusField('password')
                }}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {joining && (
              <p className="cat-field-hint">At least 12 characters, including a letter and a number.</p>
            )}

            {!joining && (
              <div className="cat-mfa-row">
                {!showMfa ? (
                  <button type="button" className="cat-mfa-trigger" onClick={() => setShowMfa(true)}>
                    Have an authenticator or recovery code?
                  </button>
                ) : (
                  <div className={`cat-field${focusField === 'code' ? ' is-focused' : ''}${code ? ' is-filled' : ''}`}>
                    <div className="cat-field-inner">
                      <input
                        id="finna-auth-mfa"
                        value={code}
                        onFocus={() => setFocusField('code')}
                        onBlur={() => setFocusField('none')}
                        onChange={(e) => setCode(e.target.value)}
                        autoComplete="one-time-code"
                        maxLength={64}
                        placeholder=" "
                      />
                      <label htmlFor="finna-auth-mfa">Authenticator or recovery code</label>
                    </div>
                  </div>
                )}
              </div>
            )}

            {guestCount > 0 && (
              <label className="cat-guest-check">
                <input type="checkbox" checked={saveGuest} onChange={(e) => setSaveGuest(e.target.checked)} />
                <span>Save this browser’s {guestCount} practice answers to my account (past guest answers earn no XP).</span>
              </label>
            )}

            <button className="cat-submit-btn" disabled={busy || googleBusy || (joining && !ageReady)}>
              <span>{busy ? 'Unlocking…' : joining ? 'Create free account' : 'Log in'}</span>
              <span className="cat-submit-arrow" aria-hidden="true">→</span>
            </button>
          </form>

          <div className="cat-card-foot">
            {!joining ? (
              <Link to="/account/recovery" className="cat-foot-link">Forgot password?</Link>
            ) : (
              <span className="cat-foot-note">No card required</span>
            )}
            <Link to={(joining ? '/login' : '/join') + nextQs} className="cat-foot-link is-strong">
              {joining ? 'Already have an account? Log in' : 'New to Finna? Join free'}
            </Link>
          </div>
        </section>

        <p className="cat-scene-footnote">
          By continuing you agree to the <Link to="/policies/terms">Terms</Link> and{' '}
          <Link to="/policies/privacy">Privacy policy</Link>.
        </p>
      </div>
    </div>
  </main>
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
