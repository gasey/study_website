import {useEffect,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {getBrowseAllowance,type BrowseAllowance as Allowance} from '../lib/api'

export default function BrowseAllowance(){
  const {pathname,search}=useLocation()
  const [value,setValue]=useState<Allowance|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0)
  useEffect(()=>{
    let live=true,version=0
    const load=()=>{const run=++version;setError(false);getBrowseAllowance().then(result=>{if(live&&run===version)setValue(result)}).catch(()=>{if(live&&run===version){setValue(null);setError(true)}})}
    const identity=()=>{setValue(null);load()}
    load();window.addEventListener('ism-auth-change',identity);window.addEventListener('ism-browse-allowance-change',load);window.addEventListener('focus',load)
    return()=>{live=false;window.removeEventListener('ism-auth-change',identity);window.removeEventListener('ism-browse-allowance-change',load);window.removeEventListener('focus',load)}
  },[retry])
  return <aside aria-label="Combined-filter allowance" className="border-b border-hairline bg-card"><div className="mx-auto flex max-w-shell flex-wrap items-center gap-x-3 gap-y-1 px-6 py-2 text-[12px] text-secondary" aria-live="polite">
    {error?<><span>Filter allowance couldn’t load.</span><button className="min-h-11 font-semibold text-link" onClick={()=>setRetry(n=>n+1)}>Retry</button></>:!value?<span>Loading filter allowance…</span>:value.unlimited?<span>Pro · Unlimited combined filters</span>:value.tier==='guest'?<><span>Basic exam, year and subject filters are free.</span><Link className="min-h-11 content-center font-semibold text-link" to={'/login?next='+encodeURIComponent(pathname+search)}>Sign in for 3 combined searches a day</Link></>:<><span><strong>{value.used}/{value.limit} combined searches used today</strong> · resets at midnight IST</span><span>Combine topic, year or answer filters in one search. Reusing a combination or changing pages is free.</span></>}
  </div></aside>
}
