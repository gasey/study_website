import {useEffect,useState} from 'react'
import {reviewRequest} from '../lib/review'
export default function EmailVerification(){
 const [state,setState]=useState<{available:boolean;verified:boolean}|null>(null),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false)
 useEffect(()=>{Promise.all([fetch('/api/auth/recovery/status',{credentials:'include',cache:'no-store'}).then(r=>r.json()),fetch('/api/auth/session',{credentials:'include',cache:'no-store'}).then(r=>r.json())]).then(([r,s])=>setState({available:r.available,verified:!!s.email_verified_at})).catch(()=>setNotice('Email status could not load. Refresh to retry.'))},[])
 async function send(){setBusy(true);try{const r=await reviewRequest<{message:string}>('/auth/email/request',{});setNotice(r.message)}catch(e){setNotice((e as Error).message)}finally{setBusy(false)}}
 return <section className="mt-5 rounded-[12px] border border-hairline bg-card p-5"><h2 className="font-display text-[24px]">Email address</h2><p className="mt-2 text-[13px] text-secondary">{state?.verified?'Your email is verified.':state?.available?'Verify your email to confirm that you can receive account messages.':'Email verification and recovery are awaiting mail-service setup.'}</p>{notice&&<p role="status" className="mt-3 text-[13px]">{notice}</p>}{state?.available&&!state.verified&&<button disabled={busy} onClick={()=>void send()} className="mt-3 min-h-11 rounded-pill border border-hairline px-4 text-[13px]">{busy?'Please wait…':'Send verification email'}</button>}</section>
}
