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
 return <main className="mx-auto max-w-[620px] px-4 pb-24 pt-10"><h1 className="font-display text-2xl">Email preferences</h1>
  {token?<section className="mt-5 rounded-panel border border-hairline bg-card p-5"><h2 className="font-display text-lg">Stop review reminders</h2><p className="mt-2 text-sm text-secondary">Account security emails are unaffected. You do not need to sign in.</p>{done?<p role="status" className="mt-4 text-sm">Review reminders are off.</p>:<button onClick={()=>void unsubscribe()} disabled={busy} className="mt-4 min-h-11 rounded-pill bg-ink px-5 text-sm font-semibold text-paper disabled:opacity-50">{busy?'Saving…':'Unsubscribe'}</button>}{error&&<p role="alert" className="mt-3 text-sm text-wrong-dark">{error}</p>}</section>:<ReviewDigestPreference/>}
  <Link to="/profile" className="mt-5 inline-flex min-h-11 items-center text-sm text-link underline">Back to your profile</Link>
 </main>
}
