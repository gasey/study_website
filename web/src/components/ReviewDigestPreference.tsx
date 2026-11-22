import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
type Preference={user_id:string;enabled:boolean;verified:boolean;available:boolean;version:number}

export default function ReviewDigestPreference(){
 const [data,setData]=useState<Preference|null>(null),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),saving=useRef(false)
 useEffect(()=>{
  let live=true;const epoch=++generation.current;setData(null);setError('');setNotice('');setBusy(false);saving.current=false
  reviewRequest<Preference>('/review-digest/preferences').then(value=>{if(live&&epoch===generation.current)setData(value)}).catch(e=>{if(live&&epoch===generation.current)setError((e as Error).message)})
  const refresh=()=>{generation.current++;setData(null);setNotice('');setRetry(n=>n+1)}
  window.addEventListener('ism-auth-change',refresh)
  return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',refresh)}
 },[retry])
 async function save(){
  if(!data||saving.current)return;saving.current=true;setBusy(true);setError('');setNotice('');const epoch=generation.current
  try{const next=await reviewRequest<Preference>('/review-digest/preferences',{user_id:data.user_id,expected_version:data.version,enabled:!data.enabled});if(epoch===generation.current){setData(next);setNotice(next.enabled?'Evening reminders are on.':'Review reminders are off.')}}
  catch(e){if(epoch===generation.current)setError((e as Error).message)}
  finally{if(epoch===generation.current){saving.current=false;setBusy(false)}}
 }
 return <section className="mt-6 rounded-panel border border-hairline bg-card p-5" aria-labelledby="review-email-title">
  <h2 id="review-email-title" className="font-display text-lg">Evening review email</h2>
  <p className="mt-2 text-sm leading-relaxed text-secondary">Choose one reminder at most per day, between 6 and 10 pm IST, with your due-review count, study streak and a Smart Review link. Empty queues stay quiet. Unsubscribe from any reminder without signing in.</p>
  {error&&<div role="alert" className="mt-3 text-sm text-wrong-dark">{error}<button onClick={()=>setRetry(n=>n+1)} className="ml-3 min-h-11 text-link underline">Reload preferences</button></div>}
  {!data&&!error&&<p role="status" className="mt-3 text-sm text-secondary">Loading email preferences…</p>}
  {data&&<><p className="mt-3 text-sm">Reminders: <strong>{data.enabled?'On':'Off'}</strong></p>
   {!data.verified&&<p className="mt-2 text-sm text-secondary">Verify your email in <Link to="/account/security" className="text-link underline">Account security</Link> before subscribing.</p>}
   {!data.available&&<p className="mt-2 text-sm text-secondary">Evening reminders are not available yet. You can still turn an existing subscription off.</p>}
   <button onClick={()=>void save()} disabled={busy||(!data.enabled&&(!data.verified||!data.available))} className="mt-3 min-h-11 rounded-pill border border-ink px-4 text-sm font-semibold disabled:opacity-50">{busy?'Saving…':data.enabled?'Turn reminders off':'Turn evening reminders on'}</button></>}
  {notice&&<p role="status" className="mt-3 text-sm">{notice}</p>}
 </section>
}
