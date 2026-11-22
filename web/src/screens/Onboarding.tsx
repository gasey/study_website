import {useEffect,useRef,useState} from 'react'
import {Link,useNavigate,useSearchParams} from 'react-router-dom'
import UdcStudySessions from '../components/UdcStudySessions'
import {getOnboarding,startOnboarding,type OnboardingStatus} from '../lib/api'
import {accountGeneration} from '../lib/accountContext'

const INTRO_SEEN_KEY='finna-intro-seen-v1'
const INTRO_CARDS=[
 {step:'1 of 3',title:'Browse',body:'Every past paper and every question is free to read, with clear source citations.',cta:'Open Papers',to:'/past-papers'},
 {step:'2 of 3',title:'Practice',body:'Pick what you want, pick how many, and toggle the timer on or off whenever you like.',cta:'Try 10 questions',to:'/practice?count=10&autostart=1'},
 {step:'3 of 3',title:'Guides',body:'Read first-party study guides, then practice that chapter’s linked bank questions.',cta:'Open a guide',to:'/guides/using-finna'},
] as const

export default function Onboarding(){
 const [params]=useSearchParams(),navigate=useNavigate(),sid=params.get('session')||''
 const [introStep,setIntroStep]=useState<number>(()=>{try{return localStorage.getItem(INTRO_SEEN_KEY)?-1:0}catch{return 0}})
 const [data,setData]=useState<OnboardingStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0)
 const generation=useRef(0),key=useRef<{exam:string;value:string}|null>(null),inFlight=useRef(false)
 function finishIntro(){try{localStorage.setItem(INTRO_SEEN_KEY,'1')}catch{};setIntroStep(-1)}
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
 const card=introStep>=0&&introStep<INTRO_CARDS.length?INTRO_CARDS[introStep]:null
 return <main className="mx-auto max-w-[850px] px-4 py-8 pb-24 sm:px-6"><header className="border-b border-hairline pb-5"><p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">Study setup · optional</p><h1 className="mt-1 text-2xl font-bold text-ink">Getting started on Finna</h1><p className="mt-2 text-base text-secondary">Browse past papers, practice with or without a timer, and read guides.</p></header>
  {!sid&&card&&<section aria-label="Quick introduction" className="mt-6 rounded-xl border border-hairline bg-card p-6">
   <div className="flex items-center justify-between gap-2"><span className="font-mono text-xs uppercase tracking-[0.08em] text-muted">{card.step}</span><button type="button" onClick={finishIntro} className="min-h-11 px-2 text-sm font-semibold text-secondary hover:text-ink">Skip intro</button></div>
   <h2 className="mt-2 text-xl font-bold text-ink">{card.title}</h2>
   <p className="mt-2 text-base text-secondary">{card.body}</p>
   <div className="mt-5 flex flex-wrap items-center gap-3">
    <Link to={card.to} onClick={finishIntro} className="inline-flex min-h-11 items-center rounded-lg bg-ink px-4 py-2 text-sm font-bold text-paper">{card.cta} →</Link>
    {introStep<INTRO_CARDS.length-1?<button type="button" onClick={()=>setIntroStep(s=>s+1)} className="min-h-11 rounded-lg border border-hairline px-4 py-2 text-sm font-semibold text-ink">Next</button>:<Link to="/practice?count=10&autostart=1" onClick={finishIntro} className="inline-flex min-h-11 items-center rounded-lg border border-ink px-4 py-2 text-sm font-semibold text-ink">Start 10 untimed questions →</Link>}
   </div>
  </section>}
  {sid?<UdcStudySessions key={sid} papers={[]} onboarding/>:<section className="mt-6 rounded-xl border border-hairline bg-card p-5">
   <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">Exam check-in</p>
   {error&&<p role="alert" className="mt-2 text-sm text-wrong">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Try again</button> <Link to="/login?next=%2Fonboarding" className="inline-flex min-h-11 items-center underline">Sign in</Link></p>}
   {!data&&!error&&<p role="status" className="mt-2 text-sm text-secondary">Loading your study setup…</p>}
   {data&&<><h2 className="mt-1 text-lg font-bold">{data.exam?.title||'Choose your primary exam'}</h2><p className="mt-2 text-sm text-secondary">{data.session?'Your check-in is saved. Resume where you left off, or revisit its summary.':data.available?'Ten questions from your primary exam’s eligible official-key pool, mixed across subjects. Normal practice rules apply; there is no check-in bonus.':data.reason}</p>
    <div className="mt-4 flex flex-wrap gap-2">{data.session?<Link className="finna-btn" to={'/onboarding?'+new URLSearchParams({session:data.session.id})}>{data.session.finished_at?'View saved summary':'Resume check-in'} →</Link>:data.available&&<button disabled={busy} className="finna-btn" onClick={()=>void start()}>{busy?'Preparing…':'Start 10 questions →'}</button>}<Link className="finna-btn finna-btn-quiet" to="/profile">Study setup</Link><Link className="finna-btn finna-btn-quiet" to="/index">Browse full index</Link></div>
   </>}
  </section>}
  <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold text-link"><Link className="inline-flex min-h-11 items-center" to="/home">Back to Home →</Link><Link className="inline-flex min-h-11 items-center" to="/guides/using-finna">Read the Finna guide →</Link></div>
 </main>
}
