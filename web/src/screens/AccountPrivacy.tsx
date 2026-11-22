import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import AgeCategoryCheck from '../components/AgeCategoryCheck'
import {privacyStatus} from '../lib/privacy'
import {reviewRequest} from '../lib/review'

type Item={id:string;user_id?:string;kind:string;state:string;version:number;created_at:string}
type List={user_id?:string;items:Item[]}
const button='min-h-11 rounded-pill border border-hairline px-4 text-sm disabled:opacity-50'
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
 return <main className="mx-auto max-w-[760px] px-4 pb-24 pt-10"><Link to="/profile" className="inline-flex min-h-11 items-center text-sm text-link underline">← Profile</Link><h1 className="font-display text-2xl">{admin?'Privacy request queue':'Privacy and account help'}</h1>
  {!admin&&<><p className="mt-3 text-sm leading-relaxed text-secondary">Manage your age declaration, download your data or send a request to Finna’s operator, Hruaitluanga. Support: <a className="break-all text-link underline" href="mailto:hruaitluangasailo20@gmail.com">hruaitluangasailo20@gmail.com</a>.</p><AgeCategoryCheck/><Link to="/policies/about" className="mt-4 inline-flex min-h-11 items-center text-sm text-link underline">Review launch policy previews</Link><div className="mt-5 flex flex-wrap gap-4 text-sm"><Link to="/account/security" className="min-h-11 py-3 text-link underline">Account security, export and closure</Link><Link to="/account/email-preferences" className="min-h-11 py-3 text-link underline">Email preferences</Link></div></>}
  {!user?<p className="mt-5 text-sm"><Link to="/login?next=%2Faccount%2Fprivacy" className="inline-flex min-h-11 items-center text-link underline">Sign in to view your requests</Link>. You can also contact support by email.</p>:<section className="mt-5 rounded-panel border border-hairline bg-card p-5"><h2 className="font-display text-lg">{admin?'Open requests':'Your requests'}</h2>
   {!admin&&<form className="mt-4" onSubmit={event=>{event.preventDefault();void action()}}><label className="block text-sm" htmlFor="privacy-kind">Request type</label><select id="privacy-kind" value={kind} disabled={busy} onChange={e=>{setKind(e.target.value);requestKey.current=null}} className="mt-2 min-h-12 w-full rounded-[9px] border border-hairline bg-paper px-3 text-sm"><option value="access">Access to my data</option><option value="correction">Correct personal information</option><option value="erasure">Review data erasure</option></select><p className="mt-2 text-sm leading-relaxed text-secondary">This sends a request for operator review. It does not close your account or change age eligibility. Contact support with the request reference for further details; do not send passwords or one-time codes.</p><button disabled={busy||!data} className={button+' mt-3'}>Submit request</button></form>}
   {data?.items.length===0&&<p className="mt-4 text-sm text-secondary">No requests to show.</p>}
   <ul className="mt-4 space-y-3">{data?.items.map(item=><li key={item.id} className="rounded-[12px] border border-hairline p-4"><h3 className="text-sm font-semibold capitalize">{item.kind==='guardian'?'Previous guardian request':item.kind} · {item.state.replace('_',' ')}</h3><p className="mt-1 break-all font-mono text-xs text-muted">Reference: {item.id}</p>{admin&&<p className="mt-1 break-all text-xs text-secondary">Account: {item.user_id}</p>}<p className="mt-2 text-xs text-muted">{new Date(item.created_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})}</p>{['received','in_review'].includes(item.state)&&<div className="mt-3 flex flex-wrap gap-2">{admin?<>{item.state==='received'&&<button disabled={busy} className={button} onClick={()=>void action(item,'in_review')}>Start review</button>}<button disabled={busy} className={button} onClick={()=>void action(item,'completed')}>Mark handled</button><button disabled={busy} className={button} onClick={()=>void action(item,'declined')}>Mark declined</button></>:<button disabled={busy} className={button} onClick={()=>void action(item,'withdrawn')}>Withdraw request</button>}</div>}</li>)}</ul>
   {admin&&<p className="mt-4 text-sm leading-relaxed text-secondary">Record a final status only after the actual work and communication are complete. These controls do not erase data, change age eligibility or send email.</p>}
  </section>}
  {notice&&<p role="status" className="mt-4 text-sm">{notice}</p>}{error&&<p role="alert" className="mt-4 text-sm text-wrong-dark">{error}</p>}<button disabled={busy} className={button+' mt-4'} onClick={()=>setRetry(n=>n+1)}>Reload requests</button>
 </main>
}
