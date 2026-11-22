import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
type Status={user_id:string;available:boolean;verified:boolean;code:{code:string;enabled:boolean;version:number}|null;credited_this_rolling_year:number;signup_referral:{state:string;scored_attempts:number}|null}

export default function ReferralPanel(){
 const [data,setData]=useState<Status|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),saving=useRef(false)
 useEffect(()=>{
  let live=true;const epoch=++generation.current;setData(null);setError('');setBusy(false);saving.current=false
  reviewRequest<Status>('/referrals/me').then(v=>{if(live&&epoch===generation.current)setData(v)}).catch(e=>{if(live&&epoch===generation.current)setError((e as Error).message)})
  const refresh=()=>{generation.current++;setData(null);setRetry(n=>n+1)}
  window.addEventListener('ism-auth-change',refresh)
  return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',refresh)}
 },[retry])
 async function save(){
  if(!data||saving.current)return;saving.current=true;setBusy(true);setError('');const epoch=generation.current
  try{const next=await reviewRequest<Status>('/referrals/code',{user_id:data.user_id,expected_version:data.code?.version||0,enabled:!data.code?.enabled});if(epoch===generation.current)setData(next)}
  catch(e){if(epoch===generation.current)setError((e as Error).message)}
  finally{if(epoch===generation.current){saving.current=false;setBusy(false)}}
 }
 return <section className="mt-6 rounded-panel border border-hairline bg-card p-5" aria-labelledby="referral-title">
  <h2 id="referral-title" className="font-display text-lg">Invite a study friend</h2>
  <p className="mt-2 text-sm leading-relaxed text-secondary">When a friend joins through your link, verifies their email and completes 10 scored answers, you each receive 7 Pro days. Up to 5 qualified invitations per rolling year. Both accounts need verified email addresses.</p>
  {!data&&!error&&<p role="status" className="mt-3 text-sm text-secondary">Loading invitations…</p>}
  {error&&<p role="alert" className="mt-3 text-sm text-wrong-dark">{error}<button className="ml-3 min-h-11 text-link underline" onClick={()=>setRetry(n=>n+1)}>Reload invitations</button></p>}
  {data&&<>
   {!data.available&&<p className="mt-3 text-sm text-secondary">Invitation rewards open after paid plans launch. You can still turn an existing link off.</p>}
   {!data.verified&&<p className="mt-3 text-sm text-secondary">Verify your email in <Link to="/account/security" className="text-link underline">Account security</Link> before creating a link.</p>}
   <p className="mt-3 text-sm">Credited invitations in the past year: <strong>{data.credited_this_rolling_year} / 5</strong></p>
   {data.code?.enabled&&<label className="mt-3 block text-sm">Your invitation link<input readOnly aria-label="Your invitation link" value={window.location.origin+'/join?ref='+data.code.code} onFocus={e=>e.currentTarget.select()} className="mt-2 min-h-11 w-full rounded-lg border border-hairline bg-paper px-3 text-sm"/><span className="mt-2 block text-xs text-secondary">Select and copy the link to share it. Turning it off prevents new signups; existing invitations can still qualify.</span></label>}
   <button onClick={()=>void save()} disabled={busy||(!data.code?.enabled&&(!data.available||!data.verified))} className="mt-3 min-h-11 rounded-pill border border-ink px-4 text-sm font-semibold disabled:opacity-50">{busy?'Saving…':data.code?.enabled?'Turn invitation link off':data.code?'Turn invitation link on':'Create invitation link'}</button>
   {data.signup_referral&&<p role="status" className="mt-3 text-sm">{data.signup_referral.state==='pending'?`Your signup invitation: ${data.signup_referral.scored_attempts} / 10 scored answers.`:data.signup_referral.state==='credited'?'Your signup invitation added 7 Pro days.':data.signup_referral.state==='capped'?'Your inviter reached the yearly limit before this invitation qualified.':'Your signup invitation is no longer eligible.'} <Link to="/billing" className="text-link underline">Plan & billing</Link></p>}
  </>}
 </section>
}

export function SignupReferral({code,onRemove,disabled=false}:{code:string;onRemove:()=>void;disabled?:boolean}){
 const [available,setAvailable]=useState<boolean|null>(null)
 useEffect(()=>{let live=true;setAvailable(null);fetch('/api/referrals/invite/'+encodeURIComponent(code),{credentials:'omit',cache:'no-store'}).then(r=>r.ok?r.json():null).then(v=>{if(live)setAvailable(v?.available===true)}).catch(()=>{if(live)setAvailable(false)});return()=>{live=false}},[code])
 return <aside className="mt-4 rounded-lg border border-hairline bg-paper p-3 text-sm"><p>{available===null?'Checking your invitation…':available?'An invitation is attached. After you verify your email and complete 10 scored answers, you and your inviter can each receive 7 Pro days, subject to their 5-per-year limit.':'Invitation rewards are unavailable for this link. You can still create your account.'}</p><button type="button" disabled={disabled} onClick={onRemove} className="mt-1 min-h-11 text-link underline disabled:opacity-50">Remove invitation</button></aside>
}
