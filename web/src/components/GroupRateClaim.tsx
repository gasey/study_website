import {useEffect,useRef,useState} from 'react'
import {useSearchParams,Link} from 'react-router-dom'
import {getGroupPrice,claimGroupPrice} from '../lib/api'
import {accountGeneration} from '../lib/accountContext'
export default function GroupRateClaim(){
 const [params]=useSearchParams(),[code,setCode]=useState(params.get('group_code')||''),[data,setData]=useState<{amount_paise:number;enabled:boolean}|null>(null),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),inFlight=useRef(false)
 useEffect(()=>{let live=true;const run=++generation.current;setData(null);setError('');setNotice('');setBusy(false);inFlight.current=false
  getGroupPrice().then(value=>{if(live&&run===generation.current)setData(value)}).catch(e=>{if(live&&run===generation.current)setError(e.message)})
  const clear=()=>{generation.current++;setCode('');setData(null);setRetry(v=>v+1)}
  for(const event of ['ism-auth-change','ism-auth-expired'])window.addEventListener(event,clear)
  return()=>{live=false;generation.current++;for(const event of ['ism-auth-change','ism-auth-expired'])window.removeEventListener(event,clear)}
 },[retry])
 const epoch=accountGeneration(),renderGeneration=generation.current
 async function claim(){if(!data||inFlight.current||epoch!==accountGeneration()||renderGeneration!==generation.current)return;inFlight.current=true;setBusy(true);setError('');setNotice('')
  try{const value=await claimGroupPrice(code.trim(),data.amount_paise);if(epoch===accountGeneration()&&renderGeneration===generation.current){setData({...data,amount_paise:value.amount_paise});setNotice(value.already_redeemed?`This account already used that code. Current next-subscription price: ₹${value.amount_paise/100}/month.`:'Your next new subscription is ₹50/month. No payment or access change was made.')}}
  catch(e){if(epoch===accountGeneration()&&renderGeneration===generation.current)setError((e as Error).message)}
  finally{if(renderGeneration===generation.current){inFlight.current=false;setBusy(false)}}
 }
 return <section className="mt-5 rounded-panel border border-hairline bg-card p-5"><h2 className="text-xl font-bold">Have a group price code?</h2><p className="mt-3 text-sm text-secondary">Claim a group’s ₹50/month price for a future new subscription. Existing renewals keep their price; claiming charges nothing and grants no access or points.</p>{error&&<p role="alert" className="mt-3 text-sm text-wrong">{error} <button className="min-h-11 underline" onClick={()=>setRetry(v=>v+1)}>Reload price</button> <Link className="underline" to={'/login?next='+encodeURIComponent('/billing'+(code?'?group_code='+encodeURIComponent(code):''))}>Sign in</Link></p>}{!data&&!error&&<p role="status" className="mt-3">Loading your account price…</p>}{data&&<><p className="mt-3 text-sm">Next new subscription: ₹{data.amount_paise/100}/month.</p>{!data.enabled&&<p className="mt-2 text-sm">New group claims are temporarily paused.</p>}<form className="mt-3 flex flex-wrap gap-2" onSubmit={e=>{e.preventDefault();void claim()}}><label className="min-w-0 flex-1 text-sm">Group code<input disabled={busy||!data.enabled} maxLength={24} value={code} onChange={e=>{setCode(e.target.value.toUpperCase());setNotice('')}} autoComplete="off" className="mt-1 min-h-11 w-full rounded-xl border border-hairline bg-card px-3"/></label><button disabled={busy||!data.enabled||!/^[A-Fa-f0-9]{24}$/.test(code.trim())} className="finna-btn self-end">{busy?'Claiming…':'Claim ₹50/month price'}</button></form></>}{notice&&<p role="status" className="mt-3 text-sm">{notice}</p>}</section>
}
