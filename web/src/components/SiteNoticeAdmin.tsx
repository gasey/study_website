import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {accountGeneration} from '../lib/accountContext'
import {reviewRequest} from '../lib/review'
type Setting={message:string;expires_at:string|null;version:number;updated_at:string}
function istTime(value:string|null){return value?new Date(new Date(value).getTime()+19800000).toISOString().slice(0,16):''}
const CARD='min-w-0 rounded-[18px] border border-hairline bg-card p-5'
export default function SiteNoticeAdmin(){
 const [setting,setSetting]=useState<Setting|null>(null),[message,setMessage]=useState(''),[expiry,setExpiry]=useState(''),[error,setError]=useState(''),[saved,setSaved]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[refresh,setRefresh]=useState(0)
 const sequence=useRef(0),mounted=useRef(true)
 const editExpiry=(value:string)=>{setExpiry(value);setSaved('')}
 useEffect(()=>{mounted.current=true;const clear=()=>{sequence.current++;setSetting(null);setMessage('');setExpiry('');setError('');setSaved('');setBusy(false);setRefresh(n=>n+1)};for(const e of ['ism-auth-change','ism-auth-expired'])window.addEventListener(e,clear);return()=>{mounted.current=false;sequence.current++;for(const e of ['ism-auth-change','ism-auth-expired'])window.removeEventListener(e,clear)}},[])
 useEffect(()=>{let live=true;const request=++sequence.current,epoch=accountGeneration();setSetting(null);setMessage('');setExpiry('');setError('');setSaved('');setLoading(true)
  reviewRequest<Setting>('/admin/ops/notice').then(data=>{if(live&&request===sequence.current&&epoch===accountGeneration()){setSetting(data);setMessage(data.message);setExpiry(istTime(data.expires_at))}}).catch(e=>{if(live&&request===sequence.current&&epoch===accountGeneration())setError(e.message)}).finally(()=>{if(live&&request===sequence.current&&epoch===accountGeneration())setLoading(false)})
  return()=>{live=false}
 },[refresh])
 async function save(clear=false){if(!setting||busy)return;const request=++sequence.current,epoch=accountGeneration();setBusy(true);setError('');setSaved('')
  try{const data=await reviewRequest<Setting>('/admin/ops/notice',{message:clear?'':message,expires_at:clear||!expiry?null:new Date(expiry+'+05:30').toISOString(),expected_version:setting.version})
   if(mounted.current&&request===sequence.current&&epoch===accountGeneration()){setSetting(data);setMessage(data.message);setExpiry(istTime(data.expires_at));setSaved(data.message?'Site notice saved.':'Site notice cleared.');window.dispatchEvent(new Event('ism-site-notice-change'))}
  }catch(e){if(mounted.current&&request===sequence.current&&epoch===accountGeneration())setError((e as Error).message)}finally{if(mounted.current&&request===sequence.current&&epoch===accountGeneration())setBusy(false)}
 }
 return <section className={CARD} aria-busy={loading||busy}><h2 className="text-base font-bold">Site notice</h2><p className="mt-1 text-sm text-secondary">Publish a short announcement across the website. The notice does not pause study or account changes.</p>
  {loading&&<p className="mt-3 text-sm" role="status">Loading notice setting…</p>}
  {error&&<p className="mt-3 break-words text-sm text-mypick" role="alert">Notice unavailable: {error} <Link to="/account/security" className="underline">Account security →</Link></p>}
  {saved&&<p role="status" className="mt-3 text-sm text-correct">{saved}</p>}
  {setting&&<form className="mt-4 space-y-4" onSubmit={event=>{event.preventDefault();void save()}}><label className="block text-xs font-semibold">Announcement<textarea value={message} onChange={event=>{setMessage(event.target.value);setSaved('')}} maxLength={500} disabled={busy} rows={3} className="mt-2 w-full rounded-[10px] border border-hairline bg-paper p-3 text-sm"/></label><p className="text-xs text-secondary">{message.length}/500 characters · plain text</p><label className="block min-w-0 text-xs font-semibold">Expires at (IST, optional)<input type="datetime-local" value={expiry} onChange={event=>editExpiry(event.target.value)} onInput={event=>editExpiry(event.currentTarget.value)} disabled={busy} className="mt-2 min-h-11 w-full min-w-0 max-w-full rounded-[10px] border border-hairline bg-paper px-3 text-sm"/></label><p className="text-xs text-secondary">Version {setting.version}. Changes are recorded in the owner’s account event history. Other open pages check for announcements every minute.</p><div className="flex flex-wrap gap-3"><button disabled={busy} className="min-h-11 rounded-[10px] bg-ink px-4 text-sm font-bold text-paper disabled:opacity-50">{busy?'Saving…':'Save site notice'}</button>{setting.message&&<button type="button" disabled={busy} onClick={()=>void save(true)} className="min-h-11 rounded-[10px] border border-hairline px-4 text-sm font-bold disabled:opacity-50">Clear notice</button>}</div></form>}
  <div className="mt-3 flex flex-wrap gap-4"><button disabled={loading||busy} onClick={()=>setRefresh(n=>n+1)} className="min-h-11 text-xs font-bold text-link underline disabled:opacity-50">Reload notice setting</button><a href="/ops-runbook.html#site-notice" className="inline-flex min-h-11 items-center text-xs font-bold text-link underline">Notice runbook →</a></div>
 </section>
}
