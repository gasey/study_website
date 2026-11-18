import {useEffect,useState} from 'react'
import {reviewRequest} from '../lib/review'
import {calendarRead,indiaToday,type CalendarFeed,type OwnedEntry,type OwnedKind,ownedKindLabel} from '../lib/calendar'
import type {HomeData} from '../lib/api'
const B='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold disabled:opacity-40'
const I='mt-1 min-h-11 w-full min-w-0 rounded-lg border border-hairline bg-paper px-3 py-2 text-base'
const blank=():OwnedEntry=>({id:crypto.randomUUID(),date:indiaToday(),title:'',note:'',kind:'personal',recurrence:null,collection_id:null,version:0})
export default function OwnedCalendar({entries,exams}:{entries:OwnedEntry[];exams:HomeData['collections']}){
 const [form,setForm]=useState<OwnedEntry>(blank),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[feed,setFeed]=useState<CalendarFeed|null>(null),[url,setUrl]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;calendarRead<CalendarFeed>('/me/calendar/feed').then(r=>{if(live)setFeed(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[retry])
 useEffect(()=>{const target=(event:Event)=>{const e=(event as CustomEvent<{date:string;title:string;collection_id:string|null}>).detail;setForm({...blank(),...e,kind:'exam-target'});setOpen(true);setError('');document.getElementById('private-calendar')?.scrollIntoView({behavior:'smooth',block:'start'})};window.addEventListener('ism-calendar-target',target);return()=>window.removeEventListener('ism-calendar-target',target)},[])
 // Parent unmounts this component on account changes: secrets and edits stay in memory.
 function update<K extends keyof OwnedEntry>(key:K,value:OwnedEntry[K]){setForm(f=>({...f,[key]:value}))}
 async function mutate(action:'save'|'delete'|'rotate'|'revoke'){
  setBusy(true);setError('');setNotice('')
  try{
   if(action==='save'){
    const {id,version,date,title,note,kind,recurrence,collection_id}=form
    const body={date,title,note,kind,recurrence:kind==='progress-test'?recurrence:null,collection_id:kind==='personal'?null:collection_id}
    await reviewRequest('/me/calendar/entries/'+id,{...body,expected_version:version})
    setOpen(false);setForm(blank());setNotice('Entry saved.')
   }else if(action==='delete'){
    await reviewRequest('/me/calendar/entries/'+form.id+'/delete',{expected_version:form.version})
    setOpen(false);setForm(blank());setNotice('Entry deleted.')
   }else{
    if(!feed)throw new Error('Reload subscription status first.')
    const r=await reviewRequest<CalendarFeed>('/me/calendar/feed/'+action,{expected_version:feed.version})
    setFeed(r);setUrl(r.url||'');setNotice(action==='rotate'?'New subscription link ready. Any previous link is now revoked.':'Subscription revoked. Calendar apps may retain copies already downloaded.')
   }
   if(action==='save'||action==='delete')window.dispatchEvent(new Event('ism-calendar-change'))
  }catch(e){setError((e as Error).message);setRetry(n=>n+1)}finally{setBusy(false)}
 }
 return <div id="private-calendar" className="mt-4 border-t border-hairline pt-4">
  <div className="flex flex-wrap gap-2"><button className={B} onClick={()=>{setForm(blank());setOpen(true);setError('')}}>Add private entry</button><label className="min-w-0 flex-1 text-sm">Edit an entry<select aria-label="Edit calendar entry" className={I} value={open&&form.version?form.id:''} onChange={e=>{const r=entries.find(r=>r.id===e.target.value);if(r){setForm(r);setOpen(true);setError('')}}}><option value="">Choose an entry…</option>{entries.map(e=><option key={e.id} value={e.id}>{e.title} · {e.date}</option>)}</select></label></div>
  {open&&<form className="mt-4 min-w-0 rounded-xl border border-hairline bg-card p-3 sm:p-4" onSubmit={e=>{e.preventDefault();void mutate('save')}}>
   <h3 className="font-display text-xl">{form.version?'Edit private entry':'New private entry'}</h3>
   <fieldset disabled={busy} className="mt-3 grid min-w-0 gap-3 sm:grid-cols-2">
    <label className="text-sm">Layer<select className={I} value={form.kind} onChange={e=>{const kind=e.target.value as OwnedKind;setForm(f=>({...f,kind,recurrence:kind==='progress-test'?7:null}))}}>{Object.entries(ownedKindLabel).map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label>
    <label className="text-sm">{form.kind==='progress-test'?'First slot · repeats on this weekday':'Date'}<input className={I} type="date" min="2000-01-01" max="2100-12-31" required value={form.date} onChange={e=>update('date',e.target.value)}/></label>
    <label className="text-sm sm:col-span-2">Title<input className={I} required maxLength={180} value={form.title} onChange={e=>update('title',e.target.value)}/></label>
    {form.kind!=='personal'&&<label className="text-sm">Exam{form.kind==='progress-test'?' (required)':' (optional)'}<select className={I} required={form.kind==='progress-test'} value={form.collection_id||''} onChange={e=>update('collection_id',e.target.value||null)}><option value="">Choose exam…</option>{exams.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></label>}
    {form.kind==='progress-test'&&<label className="text-sm">Repeat<select className={I} value={form.recurrence||7} onChange={e=>update('recurrence',Number(e.target.value) as 7|14)}><option value={7}>Weekly</option><option value={14}>Fortnightly</option></select></label>}
    <label className="text-sm sm:col-span-2">Note or goal · plain text<textarea className={I} rows={3} maxLength={3000} value={form.note} onChange={e=>update('note',e.target.value)}/></label>
   </fieldset>
   {form.kind==='progress-test'&&<p className="mt-2 text-xs text-secondary">Choose the first date for your weekday. Upcoming slots open normal 20-minute mocks for this exam. Missed slots simply move on; no calendar rewards or penalties.</p>}
   <div className="mt-3 flex flex-wrap gap-2"><button disabled={busy} className={B+' bg-ink text-paper'} type="submit">Save entry</button><button type="button" disabled={busy} className={B} onClick={()=>setOpen(false)}>Cancel</button>{form.version>0&&<button type="button" disabled={busy} className={B} onClick={()=>void mutate('delete')}>Delete entry</button>}</div>
  </form>}
  <details className="mt-3"><summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">Subscribe in your calendar app</summary><p className="text-xs leading-relaxed text-secondary">The secret link includes your personal entries, exam targets, upcoming test slots, projected review counts and past verified activity. Recurring slots and learning counts cover one year; forecasts shift as you answer. Anyone with the link can read these entries. Revoking stops future access; downloaded copies may remain.</p><div className="mt-3 flex flex-wrap gap-2"><button disabled={busy||!feed} className={B} onClick={()=>void mutate('rotate')}>{feed?.active?'Replace secret link':'Create secret link'}</button>{feed?.active&&<button disabled={busy} className={B} onClick={()=>void mutate('revoke')}>Revoke link</button>}</div>{!feed&&<button className={B+' mt-2'} onClick={()=>setRetry(n=>n+1)}>Reload subscription status</button>}{url&&<label className="mt-3 block text-sm">Copy this URL into your calendar app’s subscription field<input aria-label="Secret calendar URL" readOnly className={I} value={url} onFocus={e=>e.target.select()}/><span className="mt-1 block text-xs text-secondary">Shown once here. Create a replacement if you lose it. Calendar apps choose their own refresh schedule.</span></label>}</details>
  {notice&&<p role="status" className="mt-2 text-sm text-learn-dark">{notice}</p>}{error&&<p role="alert" className="mt-2 break-words text-sm text-mypick">{error}</p>}
 </div>
}
