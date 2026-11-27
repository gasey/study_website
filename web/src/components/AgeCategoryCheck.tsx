import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {declareAge,privacyStatus,type PrivacyStatus} from '../lib/privacy'
const ready=(value:PrivacyStatus)=>!value.age_check_enabled||value.browser_category==='adult'&&(!value.user_id||value.category==='adult')

export default function AgeCategoryCheck({onReady,compact=false}:{onReady?:(ready:boolean)=>void;compact?:boolean}){
 const [data,setData]=useState<PrivacyStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0),[editing,setEditing]=useState(false)
 const generation=useRef(0),saving=useRef(false)
 useEffect(()=>{
  let live=true;const epoch=++generation.current;onReady?.(false);setData(null);setError('');setBusy(false);setEditing(false);saving.current=false
  privacyStatus().then(value=>{if(live&&epoch===generation.current){setData(value);onReady?.(ready(value))}}).catch(e=>{if(live&&epoch===generation.current)setError((e as Error).message)})
  const refresh=()=>{generation.current++;onReady?.(false);setRetry(n=>n+1)}
  window.addEventListener('ism-auth-change',refresh)
  return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',refresh)}
 },[retry,onReady])
 async function save(category:'adult'|'under18'){
  if(!data||saving.current)return;saving.current=true;setBusy(true);setError('');const epoch=generation.current
  try{await declareAge(data,category);const next=await privacyStatus();if(epoch===generation.current){setData(next);setEditing(false);onReady?.(ready(next))}}
  catch(e){if(epoch===generation.current)setError((e as Error).message)}
  finally{if(epoch===generation.current){saving.current=false;setBusy(false)}}
 }
 if(data&&!data.age_check_enabled)return null
 if(compact){
  const isUnder=data?.category==='under18'||data?.browser_category==='under18'
  const isAdultReady=Boolean(data&&ready(data))
  const showChooser=!editing&&!isUnder&&!isAdultReady||editing
  return <div aria-label="Age category" className="cat-age-row">
   {!data?(
    <>
     <span className="cat-age-copy">{error||'Checking age eligibility…'}</span>
     {error&&<button type="button" disabled={busy} onClick={()=>setRetry(n=>n+1)} className="cat-age-link">Reload</button>}
    </>
   ):showChooser?(
    <>
     <span className="cat-age-copy"><b>Finna is for ages 18+.</b> No date of birth needed.</span>
     <span className="cat-age-btns">
      <button type="button" disabled={busy||data.category==='under18'} onClick={()=>void save('adult')} className="cat-age-btn is-primary">{data.user_id&&!data.category?'Confirm 18+':'I am 18 or over'}</button>
      <button type="button" disabled={busy} onClick={()=>void save('under18')} className="cat-age-btn">Under 18</button>
     </span>
    </>
   ):isAdultReady?(
    <>
     <span className="cat-age-ok" role="status">✓ You selected age 18 or over</span>
     <button type="button" onClick={()=>setEditing(true)} className="cat-age-link">Change</button>
    </>
   ):(
    <>
     <span className="cat-age-under" role="status">Under-18 enrollment is not supported. <Link to="/account/privacy" className="cat-age-link">Privacy &amp; account help</Link></span>
     <button type="button" onClick={()=>setEditing(true)} className="cat-age-link">Change</button>
    </>
   )}
   {error&&data&&<p role="alert" className="cat-age-err">{error}</p>}
  </div>
 }
 return <section aria-label="Age category" className="mt-5 rounded-panel border border-hairline bg-paper p-4">
  <h2 className="font-display text-lg">Before saving study progress</h2>
  <p className="mt-2 text-sm leading-relaxed text-secondary">Finna is for people aged 18 or over. Choose your age category. We do not ask for your date of birth here.</p>
  {data?.category==='under18'||data?.browser_category==='under18'?<p role="status" className="mt-3 text-sm leading-relaxed">{data.user_id?'Under-18 study access is not supported. You can still get help with your existing account and data.':'Under-18 enrollment is not supported; no new learner account was created by this choice.'} Contact <a className="break-all text-link underline" href="mailto:hruaitluangasailo20@gmail.com">hruaitluangasailo20@gmail.com</a> for account or privacy help.</p>:data?.browser_category==='adult'?<p role="status" className="mt-3 text-sm">{data.user_id&&!data.category?'This browser selected age 18 or over. Confirm the category for your signed-in account before saving progress.':'You selected age 18 or over.'}</p>:null}
  {data&&<div className="mt-3 flex flex-wrap gap-2"><button disabled={busy||data.category==='under18'} onClick={()=>void save('adult')} className="min-h-11 rounded-pill bg-ink px-4 text-sm text-paper disabled:opacity-50">{data.user_id&&!data.category?'Confirm for this account':'I am 18 or over'}</button><button disabled={busy} onClick={()=>void save('under18')} className="min-h-11 rounded-pill border border-hairline px-4 text-sm disabled:opacity-50">I am under 18</button></div>}
  {error&&<p role="alert" className="mt-3 text-sm text-wrong-dark">{error}</p>}
  {!data&&<button disabled={busy} onClick={()=>setRetry(n=>n+1)} className="mt-2 min-h-11 text-sm text-link underline">Reload age check</button>}
  <Link to="/account/privacy" className="mt-2 inline-flex min-h-11 items-center text-sm text-link underline">Privacy and account help</Link>
 </section>
}

export function AudienceNotice(){
 const [data,setData]=useState<PrivacyStatus|null>(null)
 useEffect(()=>{
  let live=true,version=0
  const refresh=()=>{const current=++version;setData(null);privacyStatus().then(value=>{if(live&&current===version)setData(value)}).catch(()=>{})}
  refresh();window.addEventListener('ism-auth-change',refresh);window.addEventListener('finna-audience-change',refresh)
  return()=>{live=false;window.removeEventListener('ism-auth-change',refresh);window.removeEventListener('finna-audience-change',refresh)}
 },[])
 if(!data?.age_check_enabled||data.user_id&&data.category==='adult'||!data.user_id&&data.browser_category==='adult')return null
 return <p role="status" className="border-b border-hairline bg-paper px-4 py-3 text-center text-sm">{data.category==='under18'||data.browser_category==='under18'?'Finna is for people aged 18 or over. Under-18 study access is not supported.':'Finna is for people aged 18 or over. Choose your age category before saving progress.'} <Link to="/account/privacy" className="text-link underline">Open privacy and account help</Link></p>
}
