import {useEffect,useRef,useState} from 'react'
import {Link,useNavigate,useSearchParams} from 'react-router-dom'
import UdcStudySessions from '../components/UdcStudySessions'
import {getOnboarding,startOnboarding,type OnboardingStatus} from '../lib/api'
import {accountGeneration} from '../lib/accountContext'

export default function Onboarding(){
 const [params]=useSearchParams(),navigate=useNavigate(),sid=params.get('session')||''
 const [data,setData]=useState<OnboardingStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),key=useRef<{exam:string;value:string}|null>(null),inFlight=useRef(false)
 useEffect(()=>{let live=true;const run=++generation.current;setData(null);setError('');setBusy(false);inFlight.current=false;key.current=null
  getOnboarding().then(value=>{if(live&&run===generation.current)setData(value)}).catch(e=>{if(live&&run===generation.current)setError(e.message)})
  const refresh=()=>{generation.current++;setData(null);setError('');setRetry(n=>n+1)}
  for(const event of ['ism-auth-change','ism-auth-expired','finna-exam-change'])window.addEventListener(event,refresh)
  return()=>{live=false;generation.current++;for(const event of ['ism-auth-change','ism-auth-expired','finna-exam-change'])window.removeEventListener(event,refresh)}
 },[retry,sid])
 const epoch=accountGeneration(),renderGeneration=generation.current
 async function start(){
  if(!data?.exam||!data.available||inFlight.current||epoch!==accountGeneration()||renderGeneration!==generation.current)return
  const run=generation.current,exam=data.exam.id
  if(key.current?.exam!==exam)key.current={exam,value:crypto.randomUUID()}
  inFlight.current=true;setBusy(true);setError('')
  try{const value=await startOnboarding(exam,key.current.value);if(run===generation.current&&epoch===accountGeneration())navigate('/onboarding?'+new URLSearchParams({session:value.id}))}
  catch(e){if(run===generation.current&&epoch===accountGeneration())setError((e as Error).message)}
  finally{if(run===generation.current){inFlight.current=false;setBusy(false)}}
 }
 return <main className="mx-auto max-w-4xl px-4 py-6 pb-24 sm:px-6"><header><p className="text-xs font-bold uppercase tracking-widest text-secondary">Study setup · optional</p><h1 className="mt-2 text-3xl font-bold">Your exam check-in</h1><p className="mt-3 text-sm leading-relaxed text-secondary">Ten questions from your primary exam’s eligible official-key pool, mixed across the subjects available. Checked answers update your usual mastery. This small sample is not an exam-readiness estimate.</p></header>
  {sid?<UdcStudySessions key={sid} papers={[]} onboarding/>:<section className="mt-5 rounded-panel border border-hairline bg-card p-5">
   {error&&<p role="alert" className="text-sm text-wrong">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button> <Link to="/login?next=%2Fonboarding" className="inline-flex min-h-11 items-center underline">Sign in</Link></p>}
   {!data&&!error&&<p role="status">Loading your study setup…</p>}
   {data&&<><h2 className="text-xl font-bold">{data.exam?.title||'Choose your primary exam'}</h2><p className="mt-3 text-sm text-secondary">{data.session?'Your check-in is saved. Resume where you left off, or revisit its summary.':data.available?'You can skip any question or leave and resume later. Reading an answer does not count as checking it. Normal practice rules apply; there is no check-in bonus.':data.reason}</p>
    <div className="mt-4 flex flex-wrap gap-2">{data.session?<Link className="finna-btn" to={'/onboarding?'+new URLSearchParams({session:data.session.id})}>{data.session.finished_at?'View saved summary':'Resume check-in'} →</Link>:data.available&&<button disabled={busy} className="finna-btn" onClick={()=>void start()}>{busy?'Preparing…':'Start 10 questions →'}</button>}<Link className="finna-btn finna-btn-quiet" to="/profile">Study setup</Link></div>
   </>}
  </section>}
  <div className="mt-5 flex flex-wrap gap-3"><Link className="inline-flex min-h-11 items-center text-sm font-semibold text-link" to="/feed">Back to today’s plan →</Link><Link className="inline-flex min-h-11 items-center text-sm font-semibold text-link" to="/revise">Your due reviews →</Link></div>
 </main>
}
