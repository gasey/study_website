import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {getAccountSession} from '../lib/api'
import {reviewRequest,reviewSession,type ReviewSession} from '../lib/review'
import {STUDY_THEMES,useStudyTheme} from '../lib/theme'
import {reviewDestinations} from '../lib/reviewNavigation'

const GROUPS=[
 ['My learning','Keep your own rhythm.',[['Study desk','/desk'],['Daily revision','/revision'],['Mistakes','/mistakes'],['Progress & profile','/profile'],['Rewards','/rewards']]],
 ['Explore','Stay curious beyond the next paper.',[['Shared mock tests','/tests'],['Make a mock test','/tests/make'],['Learning games','/games'],['Topic Trail','/trail'],['Exam calendar','/calendar'],['Exam notices','/news'],['Important Days','/important-days']]],
 ['Community','Learn and contribute together.',[['Community feed','/community'],['Shared reading','/library?library_view=reading'],['Find creators','/creators'],['Contributors','/community/contributors'],['Create & contribute','/create']]],
] as const

export default function More(){
 const [theme,setTheme]=useStudyTheme()
 const [assigned,setAssigned]=useState(false)
 const [authenticated,setAuthenticated]=useState<boolean|null>(null),[session,setSession]=useState<ReviewSession|null>(null)
 useEffect(()=>{let live=true,version=0;const load=()=>{const run=++version;setSession(null);setAssigned(false);getAccountSession().then(async a=>{if(!live||run!==version)return;setAuthenticated(a.authenticated);if(!a.authenticated)return;const s=await reviewSession();const assigned=s.grants.length?false:(await reviewRequest<{items:{state:string}[]}>('/editorial/assignments')).items.some(x=>x.state==='active'||x.state==='pending');if(live&&run===version){setSession(s);setAssigned(assigned)}}).catch(()=>{})};load();window.addEventListener('ism-auth-change',load);return()=>{live=false;window.removeEventListener('ism-auth-change',load)}},[])
 const destinations=reviewDestinations({grants:session?.grants||[],assigned})
 const staff=!!session?.grants.length,owner=session?.grants.some(g=>g.role==='owner')
 return <div className="mx-auto max-w-shell px-4 pb-12 pt-8 sm:px-6"><header className="border-b border-hairline pb-6"><p className="font-mono text-[10px] uppercase tracking-widest text-muted">Everything in its place</p><h1 className="mt-2 font-display text-[40px] sm:text-[48px]">More to explore</h1><p className="mt-3 text-[15px] text-secondary">Your learning tools, community and account.</p></header>
 {destinations.length>0&&<section aria-label="Your workspaces" className="mt-6 rounded-[14px] border border-hairline bg-card p-5 sm:p-6"><h2 className="font-display text-[27px]">Review & administration</h2><p className="mt-2 text-[13px] text-secondary">Start with one module. Use the bank tools for issues across papers.</p><nav className="mt-4 grid gap-3 sm:grid-cols-3">{destinations.map(link=><Link key={link.to} to={link.to} className="ism-card-surface min-w-0 rounded-xl border border-hairline bg-paper p-4 hover:border-ink"><span className="block text-[15px] font-semibold text-link">{link.label} →</span><span className="mt-2 block text-[13px] text-secondary">{link.description}</span></Link>)}</nav></section>}
 <section aria-label="Study theme" className="mt-6 rounded-[14px] border border-hairline bg-card p-5 sm:p-6">
  <div className="flex flex-wrap items-baseline justify-between gap-2">
   <div>
    <p className="font-mono text-[10px] uppercase tracking-widest text-practice-dark">Reading comfort</p>
    <h2 className="mt-1 font-display text-[26px]">Study appearance</h2>
   </div>
   <p className="text-[13px] text-secondary">Choose a surface tuned for daytime focus or late-night revision.</p>
  </div>
  <div className="mt-4 grid gap-3 sm:grid-cols-3" role="group" aria-label="Select study theme">
   {STUDY_THEMES.map(item=>{
    const active=theme===item.id
    return <button key={item.id} type="button" aria-pressed={active} onClick={()=>setTheme(item.id)} className={'ism-tactile-btn flex min-h-11 flex-col items-start rounded-xl border p-4 text-left transition-all '+(active?'border-practice bg-practice-soft/55 shadow-sm':'border-hairline bg-paper hover:border-hairline2')}>
     <div className="flex w-full items-center justify-between gap-2">
      <span className="inline-flex items-center gap-2 font-display text-[20px] font-medium text-ink"><span aria-hidden="true">{item.icon}</span>{item.label}</span>
      {active&&<span className="rounded-pill bg-practice px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-white">Active</span>}
     </div>
     <span className="mt-1.5 text-[12px] leading-relaxed text-secondary">{item.description}</span>
    </button>
   })}
  </div>
 </section>
 <div className="mt-6 grid gap-5 md:grid-cols-3">{GROUPS.map(([name,description,links])=><section key={name} className="ism-card-surface rounded-[14px] border border-hairline bg-card p-5 sm:p-6"><h2 className="font-display text-[27px]">{name}</h2><p className="mt-2 text-[13px] text-secondary">{description}</p><nav aria-label={name} className="mt-5">{links.map(([label,path])=><Link key={path} to={path} className="group flex min-h-11 items-center justify-between gap-2 border-t border-hairline py-3 text-[14px] text-link hover:underline"><span>{label}</span><span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-1">→</span></Link>)}</nav></section>)}</div>
 <section className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-hairline pt-5" aria-label="Account"><h2 className="mr-auto font-display text-[25px]">Account</h2>{authenticated===false?<><Link className="inline-flex min-h-11 items-center text-sm text-link" to="/login?next=%2Fmore">Sign in</Link><Link className="inline-flex min-h-11 items-center text-sm text-link" to="/join?next=%2Fmore">Create an account</Link></>:authenticated&&<>{[['Inbox','/inbox'],['Security & sign-in','/account/security'],['Creator settings','/creators/settings']].map(([label,to])=><Link key={to} className="inline-flex min-h-11 items-center text-[13px] text-link" to={to}>{label}</Link>)}</>}<Link className="inline-flex min-h-11 items-center text-[13px] text-link" to="/plans">Membership</Link></section>
 {staff&&<details className="mt-5 rounded-[14px] border border-hairline bg-card px-5"><summary className="min-h-11 cursor-pointer py-4 text-[13px] font-semibold">More staff tools</summary><nav aria-label="Staff workspaces" className="flex flex-wrap gap-x-6 gap-y-2 pb-4">{[['Learning collections','/learning/manage'],...(owner?[['Paper workbench','/paper-workbench'],['Current affairs','/current-affairs/manage'],['Topic Trail','/admin/topic-trail'],['Practice discovery','/admin/discovery']]:[])].map(([label,to])=><Link key={to} className="inline-flex min-h-11 items-center text-[13px] text-link" to={to}>{label} →</Link>)}</nav></details>}
 </div>
}
