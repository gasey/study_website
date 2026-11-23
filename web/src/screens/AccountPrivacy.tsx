import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import AgeCategoryCheck from '../components/AgeCategoryCheck'
import {privacyStatus} from '../lib/privacy'
import {reviewRequest} from '../lib/review'

type Item={id:string;user_id?:string;kind:string;state:string;version:number;created_at:string}
type List={user_id?:string;items:Item[]}
export default function AccountPrivacy({admin=false}:{admin?:boolean}){
 const [data,setData]=useState<List|null>(null),[user,setUser]=useState<string|null>(null),[kind,setKind]=useState('access'),[error,setError]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[retry,setRetry]=useState(0)
 const generation=useRef(0),saving=useRef(false),requestKey=useRef<string|null>(null)
 const path=admin?'/account-privacy/admin/requests':'/account-privacy/requests'
 useEffect(()=>{
  let live=true;const epoch=++generation.current;setData(null);setUser(null);setError('');setNotice('');setBusy(false);saving.current=false;requestKey.current=null
  privacyStatus().then(async status=>{if(!live||epoch!==generation.current)return;setUser(status.user_id);if(status.user_id){const list=await reviewRequest<List>(path);if(live&&epoch===generation.current)setData(list)}}).catch(e=>{if(live&&epoch===generation.current)setError((e as Error).message)})
  const refresh=()=>{generation.current++;setData(null);setUser(null);setRetry(n=>n+1)}
  window.addEventListener('ism-auth-change',refresh)
  return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',refresh)}
 },[retry,path])
 async function action(item?:Item,state?:string){
  if(!user||saving.current)return;saving.current=true;setBusy(true);setError('');setNotice('');const epoch=generation.current
  try{
   if(item)await reviewRequest(path+'/'+encodeURIComponent(item.id)+(admin?'':'/withdraw'),{user_id:admin?item.user_id:user,expected_version:item.version,state})
   else {requestKey.current??=crypto.randomUUID();await reviewRequest(path,{user_id:user,kind,request_key:requestKey.current});requestKey.current=null}
   const next=await reviewRequest<List>(path)
   if(epoch===generation.current){setData(next);setNotice(item?'Request status updated.':'Request received. This records your request; it does not automatically export or erase data.')}
  }catch(e){if(epoch===generation.current)setError((e as Error).message)}
  finally{if(epoch===generation.current){saving.current=false;setBusy(false)}}
 }
 return <main className="at-sub-page">
  <header className="av-hero">
   <div className="av-hero-copy">
    <span className="cr-eyebrow">{admin?'Privacy queue':'Privacy & data rights'}</span>
    <h1>{admin?'Privacy request queue':'Privacy and account help'}</h1>
    {!admin&&<p>Manage your age declaration, download your data, or send a formal request to Finna’s operator, Hruaitluanga (<a className="underline" href="mailto:hruaitluangasailo20@gmail.com">hruaitluangasailo20@gmail.com</a>).</p>}
   </div>
   <div className="av-hero-actions">
    <Link to="/profile" className="cr-glass-btn">← Profile</Link>
    {!admin&&<Link to="/account/security" className="cr-glass-btn">Security & export</Link>}
   </div>
  </header>
  {!admin&&<><AgeCategoryCheck/><div className="at-btn-row"><Link to="/policies/about" className="finna-st-btn">Review launch policy previews</Link><Link to="/account/email-preferences" className="finna-st-btn">Email preferences</Link></div></>}
  {!user?<section className="at-card"><p className="text-sm"><Link to="/login?next=%2Faccount%2Fprivacy" className="at-link">Sign in to view your requests</Link>. You can also contact support by email.</p></section>:<section className="at-card"><div className="at-card-head"><div><h2>{admin?'Open requests':'Your requests'}</h2></div><button disabled={busy} className="finna-st-btn" onClick={()=>setRetry(n=>n+1)}>Reload</button></div>
   {!admin&&<form className="space-y-3" onSubmit={event=>{event.preventDefault();void action()}}><label className="at-field"><span>Request type</span><select id="privacy-kind" value={kind} disabled={busy} onChange={e=>{setKind(e.target.value);requestKey.current=null}}><option value="access">Access to my data</option><option value="correction">Correct personal information</option><option value="erasure">Review data erasure</option></select></label><p className="text-xs leading-relaxed text-secondary">This sends a request for operator review. It does not close your account or change age eligibility. Contact support with the request reference for further details; do not send passwords or one-time codes.</p><button disabled={busy||!data} className="cr-primary-btn">Submit request</button></form>}
   {data?.items.length===0&&<p className="text-sm text-secondary">No requests to show.</p>}
   <ul className="space-y-3">{data?.items.map(item=><li key={item.id} className="at-session-row"><div className="at-session-meta"><div className="at-session-title"><strong className="capitalize">{item.kind==='guardian'?'Previous guardian request':item.kind}</strong><span className="finna-st-pill finna-st-pill--gray">{item.state.replace('_',' ')}</span></div><span className="font-mono text-xs">Ref: {item.id} · {new Date(item.created_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})}</span>{admin&&<span className="text-xs">Account: {item.user_id}</span>}</div>{['received','in_review'].includes(item.state)&&<div className="flex flex-wrap gap-2">{admin?<>{item.state==='received'&&<button disabled={busy} className="finna-st-btn" onClick={()=>void action(item,'in_review')}>Start review</button>}<button disabled={busy} className="finna-st-btn finna-st-btn--primary" onClick={()=>void action(item,'completed')}>Mark handled</button><button disabled={busy} className="finna-st-btn" onClick={()=>void action(item,'declined')}>Mark declined</button></>:<button disabled={busy} className="finna-st-btn" onClick={()=>void action(item,'withdrawn')}>Withdraw request</button>}</div>}</li>)}</ul>
   {admin&&<p className="text-xs leading-relaxed text-secondary">Record a final status only after the actual work and communication are complete. These controls do not erase data, change age eligibility or send email.</p>}
  </section>}
  {notice&&<p role="status" className="finna-st-notice">{notice}</p>}
  {error&&<p role="alert" className="at-inline-err">{error}</p>}
  <div className="at-btn-row"><button disabled={busy} className="finna-st-btn" onClick={()=>setRetry(n=>n+1)}>Reload requests</button></div>
 </main>
}
