import {useEffect,useRef,useState} from 'react'
import {getFocusSubjects,getOnboardingSummary,saveFocusSubjects,type FocusSubjects,type OnboardingSummary} from '../lib/api'
import {accountGeneration} from '../lib/accountContext'

export default function OnboardingSuggestions({sid}:{sid:string}){
 const [summary,setSummary]=useState<OnboardingSummary|null>(null),[focus,setFocus]=useState<FocusSubjects|null>(null),[selected,setSelected]=useState<string[]>([]),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),inFlight=useRef(false)
 useEffect(()=>{let live=true;const run=++generation.current;setSummary(null);setFocus(null);setSelected([]);setError('');setNotice('');setBusy(false);inFlight.current=false
  Promise.all([getOnboardingSummary(sid),getFocusSubjects()]).then(([s,f])=>{if(live&&run===generation.current){setSummary(s);setFocus(f);setSelected(f.items.map(i=>i.subject_id))}}).catch(e=>{if(live&&run===generation.current)setError(e.message)})
  const clear=()=>{generation.current++;setSummary(null);setFocus(null);setSelected([]);setRetry(n=>n+1)}
  for(const event of ['ism-auth-change','ism-auth-expired','finna-exam-change'])window.addEventListener(event,clear)
  return()=>{live=false;generation.current++;for(const event of ['ism-auth-change','ism-auth-expired','finna-exam-change'])window.removeEventListener(event,clear)}
 },[sid,retry])
 const epoch=accountGeneration(),renderGeneration=generation.current
 const options=focus?[...(focus.available||[]),...focus.items.filter(i=>!focus.available?.some(a=>a.id===i.subject_id)).map(i=>({id:i.subject_id,label:i.label,selected:true}))]:[]
 async function save(){if(!focus||inFlight.current||epoch!==accountGeneration()||renderGeneration!==generation.current)return;const run=generation.current;inFlight.current=true;setBusy(true);setError('');setNotice('')
  try{await saveFocusSubjects(selected);if(run===generation.current&&epoch===accountGeneration()){setNotice('Your selected focus subjects are saved.');window.dispatchEvent(new Event('ism-focus-change'))}}
  catch(e){if(run===generation.current&&epoch===accountGeneration())setError((e as Error).message)}
  finally{if(run===generation.current){inFlight.current=false;setBusy(false)}}
 }
 return <section aria-labelledby="checkin-suggestions-title" className="mt-5 rounded-panel border border-hairline bg-card p-5"><h3 id="checkin-suggestions-title" className="text-xl font-bold">What to work on next</h3>
  {error&&<p role="alert" className="mt-3 text-sm text-wrong">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button></p>}
  {!summary&&!error&&<p role="status" className="mt-3 text-sm">Reading your checked answers…</p>}
  {summary?.finished&&<><p className="mt-3 text-sm text-secondary">{summary.basis}</p>{summary.subjects.length?<ul className="mt-3 space-y-2 text-sm">{summary.subjects.map(s=><li key={s.subject_id}><strong>{s.label}</strong> · {s.correct} correct of {s.checked} checked{summary.suggested_subject_ids.includes(s.subject_id)?' · Suggested focus':''}</li>)}</ul>:<p className="mt-3 text-sm text-secondary">No currently eligible checked answers are available for suggestions.</p>}
   {!summary.suggested_subject_ids.length&&summary.subjects.length>0&&<p className="mt-3 text-sm text-secondary">No weaker subject appeared in these checked answers. You can still choose what to practise next.</p>}
   {focus&&<fieldset className="mt-4 border-t border-hairline pt-4"><legend className="text-sm font-bold">Choose up to five focus subjects</legend><p className="mt-2 text-xs text-secondary">Your existing selection is kept. Suggestions are optional; nothing is applied until you save.</p><div className="mt-3 grid gap-1 sm:grid-cols-2">{options.map(s=><label key={s.id} className="flex min-h-11 items-center gap-3 text-sm"><input type="checkbox" checked={selected.includes(s.id)} disabled={busy||selected.length>=5&&!selected.includes(s.id)} onChange={e=>{if(epoch!==accountGeneration()||renderGeneration!==generation.current)return;setNotice('');setSelected(old=>e.target.checked?[...old,s.id]:old.filter(id=>id!==s.id))}}/>{s.label}{summary.suggested_subject_ids.includes(s.id)&&<span className="text-xs text-link">Suggested</span>}</label>)}</div><button disabled={busy||!options.length} className="finna-btn mt-4" onClick={()=>void save()}>{busy?'Saving…':'Save selected focus subjects'}</button></fieldset>}
   {notice&&<p role="status" className="mt-3 text-sm text-secondary">{notice}</p>}
  </>}
 </section>
}
