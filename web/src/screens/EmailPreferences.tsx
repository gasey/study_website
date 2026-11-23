import {useState} from 'react'
import {Link} from 'react-router-dom'
import ReviewDigestPreference from '../components/ReviewDigestPreference'

export default function EmailPreferences(){
 const [token]=useState(()=>new URLSearchParams(location.hash.slice(1)).get('unsubscribe'))
 const [busy,setBusy]=useState(false),[done,setDone]=useState(false),[error,setError]=useState('')
 async function unsubscribe(){
  if(busy||done)return;setBusy(true);setError('')
  try{
   const response=await fetch('/api/review-digest/unsubscribe',{method:'POST',credentials:'omit',headers:{'content-type':'application/json'},body:JSON.stringify({token})})
   if(!response.ok)throw new Error('This unsubscribe link could not be used. Try again or manage reminders from your profile.')
   history.replaceState(null,'','/account/email-preferences');setDone(true)
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 return <main className="at-sub-page at-sub-page--narrow">
  <header className="av-hero">
   <div className="av-hero-copy">
    <span className="cr-eyebrow">Notifications</span>
    <h1>Email preferences</h1>
    <p>Control evening review reminder digests. Security and recovery emails remain active.</p>
   </div>
   <div className="av-hero-actions">
    <Link to="/profile" className="cr-glass-btn">← Profile</Link>
   </div>
  </header>
  {token?<section className="at-card"><div className="at-card-head"><div><h2>Stop review reminders</h2><p>Account security emails are unaffected. You do not need to sign in.</p></div></div>{done?<p role="status" className="finna-st-notice">Review reminders are off.</p>:<button onClick={()=>void unsubscribe()} disabled={busy} className="cr-primary-btn">{busy?'Saving…':'Unsubscribe'}</button>}{error&&<p role="alert" className="at-inline-err">{error}</p>}</section>:<ReviewDigestPreference/>}
  <div className="at-btn-row"><Link to="/profile" className="at-link">← Back to your profile</Link></div>
 </main>
}
