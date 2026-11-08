import {useEffect,useState} from 'react'
import {Link,useLocation,useNavigate} from 'react-router-dom'
import {getAccountSession,type AccountSession} from '../lib/api'
import {reviewRequest,reviewSession} from '../lib/review'
import {reviewDestinations,type ReviewAccess} from '../lib/reviewNavigation'
import {useExamScope,changeExamScope,type ExamScope} from '../lib/examScope'
import {PRIMARY_NAV,primarySection,focusedSession} from '../lib/navigation'
import {STUDY_THEMES,useStudyTheme} from '../lib/theme'
import {Avatar} from './ui'
import QuickFind from './QuickFind'

export default function Header(){
 const {pathname,search}=useLocation(),nav=useNavigate(),scope=useExamScope()
 const [theme,,cycleTheme]=useStudyTheme()
 const activeTheme=STUDY_THEMES.find(t=>t.id===theme)||STUDY_THEMES[0]
 const [access,setAccess]=useState<ReviewAccess>({grants:[],assigned:false})
 const [account,setAccount]=useState<AccountSession>({authenticated:false}),[unread,setUnread]=useState<number|null>(null)
 useEffect(()=>{let live=true,version=0;const load=()=>{const run=++version;setUnread(null);setAccess({grants:[],assigned:false});getAccountSession().then(a=>{if(!live||run!==version)return;setAccount(a);if(a.authenticated)void reviewSession(true).then(async s=>{const assigned=s.grants.length?false:(await reviewRequest<{items:{state:string}[]}>('/editorial/assignments')).items.some(x=>x.state==='active'||x.state==='pending');if(live&&run===version)setAccess({grants:s.grants,assigned})}).catch(()=>{});if(a.authenticated)reviewRequest<{unread:number}>('/inbox/unread').then(r=>{if(live&&run===version)setUnread(r.unread)}).catch(()=>{})}).catch(()=>{})};load();window.addEventListener('ism-auth-change',load);window.addEventListener('ism-avatar-change',load);window.addEventListener('ism-notifications-change',load);window.addEventListener('focus',load);return()=>{live=false;window.removeEventListener('ism-auth-change',load);window.removeEventListener('ism-avatar-change',load);window.removeEventListener('ism-notifications-change',load);window.removeEventListener('focus',load)}},[])
 const focused=focusedSession(pathname)
 const showScope=!focused&&/^\/(bank|exams|library|english|mizo|arithmetic|vocabulary|essay|search)(\/|$)/.test(pathname)
 const udc=/^\/exams\/udc(?:\/|$)/.test(pathname)
 return <><header data-app-header className="sticky top-0 z-50 border-b border-hairline bg-card/90 backdrop-blur-md transition-colors">
  <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-[80] focus:rounded-lg focus:bg-ink focus:p-3 focus:text-paper">Skip to content</a>
  <div className="mx-auto flex min-h-[64px] max-w-shell items-center gap-2 px-4 sm:gap-5 sm:px-6">
   <Link to="/feed" aria-label="India Study Map home" className="group shrink-0 font-display text-[19px] font-semibold leading-none tracking-tight sm:text-[24px]">India Study Map<span className="ml-1 inline-block text-[#C0462C] transition-transform duration-200 group-hover:scale-125">.</span></Link>
   {!focused&&<nav aria-label="Primary navigation" className="hidden items-center gap-1 lg:flex">{PRIMARY_NAV.map(t=>{const active=primarySection(pathname)===t.to;return <Link key={t.to} to={t.to} aria-current={active?'page':undefined} className={'inline-flex min-h-11 items-center rounded-pill px-3.5 text-[13px] transition-all duration-150 '+(active?'bg-canvas font-semibold text-ink shadow-[inset_0_0_0_1px_rgb(var(--ism-hairline2-rgb))]':'text-secondary hover:bg-canvas/70 hover:text-ink')}>{t.label}</Link>})}</nav>}
   <div className="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
    <button
     type="button"
     onClick={cycleTheme}
     aria-label={`Study theme: ${activeTheme.label}. Activate to switch theme.`}
     title={`Theme: ${activeTheme.label} (${activeTheme.description}) — tap to switch`}
     className="ism-tactile-btn inline-flex min-h-11 items-center gap-1.5 rounded-pill border border-hairline bg-paper px-2.5 text-[12px] font-medium text-secondary hover:border-hairline2 hover:text-ink sm:px-3"
    >
     <span aria-hidden="true" className="text-[13px] leading-none">{activeTheme.icon}</span>
     <span className="hidden font-mono text-[11px] uppercase tracking-wider sm:inline">{activeTheme.shortLabel}</span>
    </button>
    {!focused&&<QuickFind access={access}/>}
    {account.authenticated?<><Link to="/inbox" aria-label={unread?`Inbox, ${unread} unread`:'Inbox'} className="relative hidden min-h-11 items-center rounded-pill px-2.5 text-[13px] transition-colors hover:bg-canvas sm:inline-flex">Inbox{unread? <span className="ml-1.5 rounded-pill bg-ink px-1.5 text-[10px] text-paper">{unread>99?'99+':unread}</span>:null}</Link><Link to="/profile" aria-label="Your profile" className="relative flex min-h-11 min-w-11 items-center justify-center transition-transform hover:scale-105"><Avatar look={account.avatar} initials={account.email?.slice(0,2).toUpperCase()||'Me'}/>{!!unread&&<span className="absolute right-0 top-1 h-2 w-2 rounded-full bg-community sm:hidden"/>}</Link></>:<Link to={'/login?next='+encodeURIComponent(pathname+search)} className="ism-tactile-btn inline-flex min-h-11 items-center rounded-pill bg-ink px-3.5 text-[12px] font-semibold text-paper shadow-sm sm:px-4 sm:text-[13px]">Sign in</Link>}
   </div>
  </div>

  {showScope&&<div className="border-t border-hairline bg-canvas/65 transition-colors"><div className="mx-auto flex max-w-shell items-center justify-between gap-2 px-4 py-1 sm:px-6">{udc?<p className="py-2 text-[12px] text-secondary"><strong className="text-ink">UDC</strong> · Questions and papers for your exam</p>:<label className="flex min-h-9 min-w-0 items-center gap-2 text-[12px] text-secondary"><span className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted">Study focus</span><select aria-label="Question and exam focus" className="min-h-9 min-w-0 max-w-full cursor-pointer rounded-md bg-transparent pr-2 font-semibold text-ink" value={scope} onChange={e=>nav(changeExamScope(e.target.value as ExamScope),{replace:true,preventScrollReset:true})}><option value="mizoram-recruitment">MPSC & Mizoram</option><option value="all">All exams & questions</option></select></label>}</div></div>}
 </header>
  {!focused&&reviewDestinations(access).length>0&&<nav aria-label="Workspaces" className="border-b border-hairline bg-paper"><div className="mx-auto flex max-w-shell flex-wrap items-center gap-x-5 px-4 sm:px-6">{reviewDestinations(access).slice(0,2).map(link=><Link key={link.to} to={link.to} aria-current={pathname===link.to?'page':undefined} className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link hover:underline">{link.label} →</Link>)}</div></nav>}
 </>
}
