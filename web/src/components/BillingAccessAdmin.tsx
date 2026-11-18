import {useRef,useState} from 'react'
import BulkRatesAdmin from './BulkRatesAdmin'
import {reviewRequest} from '../lib/review'

type Grant={days:number;starts_at:string;ends_at:string}
type Account={id:string;email:string;handle:string;amount_paise:number;granted_access:Grant[];subscription:{amount_paise:number;status:string}|null}
const input='min-h-11 rounded-[10px] border border-hairline bg-card px-3 text-[14px]'
const button='min-h-11 rounded-pill bg-ink px-5 py-2 text-[14px] font-semibold text-paper disabled:opacity-50'
export default function BillingAccessAdmin(){
 const [email,setEmail]=useState(''),[account,setAccount]=useState<Account|null>(null),[days,setDays]=useState(7),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('')
 const operation=useRef<string|null>(null)
 async function load(value=email){const data=await reviewRequest<Account>('/billing/admin/account?'+new URLSearchParams({email:value.trim()}));setAccount(data);return data}
 async function find(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');setMessage('');setAccount(null);operation.current=null;try{await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function rate(amount:number){if(!account)return;setBusy(true);setError('');setMessage('');try{await reviewRequest('/billing/admin/account/'+encodeURIComponent(account.id)+'/rate',{amount_paise:amount,expected_amount_paise:account.amount_paise});await load(account.email);setMessage(`Next new subscription: ₹${amount/100}/month.`)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function grant(e:React.FormEvent){e.preventDefault();if(!account)return;setBusy(true);setError('');setMessage('');operation.current??=crypto.randomUUID();try{await reviewRequest('/billing/admin/account/'+encodeURIComponent(account.id)+'/days',{days,idempotency_key:operation.current});await load(account.email);operation.current=null;setMessage(`${days} extra Pro days granted.`)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <><section className="mt-5 rounded-[18px] border border-hairline bg-card p-5">
  <h2 className="font-display text-[24px]">Monthly price & extra Pro days</h2>
  <p className="mt-2 text-[14px] text-secondary">Standard price is ₹100/month. Select an existing account to offer ₹50/month or grant extra Pro days.</p>
  <form onSubmit={e=>void find(e)} className="mt-4 flex flex-wrap gap-3"><input type="email" required disabled={busy} value={email} onChange={e=>{setEmail(e.target.value);setAccount(null);setMessage('');operation.current=null}} placeholder="Account email" aria-label="Find billing account by email" className={input+' min-w-0 flex-1'}/><button disabled={busy} className={button}>Find account</button></form>
  {error&&<p role="alert" className="mt-3 text-wrong-dark">{error}</p>}{message&&<p role="status" className="mt-3 text-correct-dark">{message}</p>}
  {account&&<div className="mt-5 border-t border-hairline pt-4"><p className="font-semibold">{account.email} · @{account.handle}</p><p className="mt-2 text-[14px]">Next new subscription: <b>₹{account.amount_paise/100}/month</b></p>
   {account.subscription&&<p className="mt-2 text-[13px] text-secondary">Existing subscription: ₹{account.subscription.amount_paise/100} · {account.subscription.status}</p>}
   <p className="mt-2 text-[13px] text-secondary">The selected price repeats monthly on a new subscription. Changing it here does not change an existing Razorpay renewal.</p>
   <div className="mt-3 flex flex-wrap gap-3"><button type="button" disabled={busy||account.amount_paise===5000} onClick={()=>void rate(5000)} className={button}>Set ₹50/month</button><button type="button" disabled={busy||account.amount_paise===10000} onClick={()=>void rate(10000)} className={button}>Set ₹100/month</button></div>
   <form onSubmit={e=>void grant(e)} className="mt-5 flex flex-wrap items-end gap-3"><label className="text-[14px]">Extra days<input type="number" required disabled={busy} min={1} max={3650} value={days} onChange={e=>{setDays(Number(e.target.value));operation.current=null}} className={input+' ml-3 w-24'} /></label><button disabled={busy} className={button}>Grant extra Pro days</button></form>
   <p className="mt-2 text-[13px] text-secondary">Days extend existing trial, paid or granted access. They do not charge money or move Razorpay’s renewal date. Cancel renewal separately if payments should stop.</p>
   <div className="mt-3 space-y-2">{account.granted_access.map((g,i)=><p key={i} className="text-[13px]">{g.days} days · {new Date(g.starts_at).toLocaleDateString('en-IN')} – {new Date(g.ends_at).toLocaleDateString('en-IN')}</p>)}</div>
  </div>}
 </section><BulkRatesAdmin/></>
}
