import {useEffect,useRef,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {getAccountSession,getProgressSummary,listCollections,isLaterExamCollection,type AccountSession,type Collection} from '../lib/api'
import {reviewRequest,reviewSession} from '../lib/review'
import {reviewDestinations,type ReviewAccess} from '../lib/reviewNavigation'
import {useExamScope} from '../lib/examScope'
import {focusedSession,mobileTitle} from '../lib/navigation'
import {useStudyTheme} from '../lib/theme'
import {usePreferredExam} from '../lib/preferredExam'
import {Avatar} from './ui'
import QuickFind from './QuickFind'
import NavIcon from './NavIcon'
import BrowseAllowance from './BrowseAllowance'

const NAV=[{to:'/feed',label:'Home'},{to:'/exams',label:'Exams'},{to:'/library',label:'Subjects'},{to:'/past-papers',label:'Papers'},{to:'/bank?pool=practice',label:'Practice'},{to:'/community',label:'Community'}]
const MENUS:Record<string,{title:string;links:[string,string,string][]}[]>={
 Exams:[{title:'Your next exam',links:[['/exams/udc','UDC','Upper Division Clerk'],['/exams/ldc','LDC','Lower Division Clerk'],['/exams/combined-prelims','Combined Prelims','Civil services preparation']]},{title:'Explore',links:[['/exams/group-b-gazetted','Group B Gazetted','Subjects and past papers'],['/exams/group-b-non-gazetted','Group B Non-Gazetted','Common and technical subjects'],['/exams/mes','Engineering Services','Branch, syllabus and paper guides']]},{title:'Plan your study',links:[['/exams','All exams','Find an exam and save it'],['/calendar','Exam calendar','Published dates and notices'],['/tests','Mock tests','Shared tests and your test builder']]}],
 Subjects:[{title:'Study by subject',links:[['/arithmetic','Arithmetic & reasoning','Concepts, worked methods and questions'],['/english','English','Grammar, comprehension and writing'],['/mizo','Mizo','Language, literature and culture']]},{title:'Learning tools',links:[['/atlas','Atlas','Geography, places and layers'],['/chronicle','Chronicle','Dates and events from the bank'],['/stats','Stats','India, global rankings and the Economic Survey']]},{title:'Your library',links:[['/library','All subjects','Browse the subject library'],['/library?library_view=reading','Reading','Notes and study materials'],['/library?library_view=saved','Saved collections','Return to what you saved']]}],
 Practice:[{title:'Question banks',links:[['/bank?origin=paper','MPSC question bank','Original papers and answer sources'],['/website-bank','Website question bank','Reviewed learner contributions'],['/practice-sets','Practice sets','Focused collections of questions']]},{title:'Keep learning',links:[['/revise','Revise','Scheduled questions, mistakes and vocabulary'],['/games','Play','All learning games in one place']]},{title:'Test yourself',links:[['/tests','Mock tests','Browse available shared tests'],['/tests/make','Build a mock test','Choose questions and a timer'],['/exams','Past papers','Find the paper for your exam']]}],
 Community:[{title:'Learn together',links:[['/community','Community feed','Shared reading and conversations'],['/community?tab=questions','Questions & doubts','Work through a question together'],['/creators','Creators','Find people and published work']]},{title:'Share what you know',links:[['/create','Create','Questions, notes and practice sets'],['/studio','My materials','Continue your drafts'],['/contribute','My contributions','Corrections and submissions']]},{title:'Your space',links:[['/desk','Study desk','Focus and keep your study work'],['/profile','Your profile','Activity, progress and rewards']]}],
}
export default function Header(){
 const {pathname,search}=useLocation(),scope=useExamScope()
 const [theme,setTheme]=useStudyTheme(),[access,setAccess]=useState<ReviewAccess>({grants:[],assigned:false})
 const [account,setAccount]=useState<AccountSession>({authenticated:false}),[unread,setUnread]=useState<number|null>(null),[streak,setStreak]=useState<number|null>(null)
 const [exams,setExams]=useState<Collection[]>([]),[menu,setMenu]=useState<string|null>(null)
 const selected=usePreferredExam(exams),shell=useRef<HTMLElement>(null)
 useEffect(()=>{let live=true,version=0
  const load=()=>{const run=++version;setUnread(null);setStreak(null);setAccess({grants:[],assigned:false});setAccount({authenticated:false})
   getProgressSummary().then(p=>{if(live&&run===version)setStreak(p.current_streak)}).catch(()=>{})
   getAccountSession().then(a=>{if(!live||run!==version)return;setAccount(a)
    if(a.authenticated){void reviewSession(true).then(async s=>{const assigned=s.grants.length?false:(await reviewRequest<{items:{state:string}[]}>('/editorial/assignments')).items.some(x=>x.state==='active'||x.state==='pending');if(live&&run===version)setAccess({grants:s.grants,assigned})}).catch(()=>{})
     reviewRequest<{unread:number}>('/inbox/unread').then(r=>{if(live&&run===version)setUnread(r.unread)}).catch(()=>{})}
   }).catch(()=>{})}
  load();const events=['ism-auth-change','ism-avatar-change','ism-notifications-change','focus'];events.forEach(e=>window.addEventListener(e,load));return()=>{live=false;events.forEach(e=>window.removeEventListener(e,load))}
 },[])
 useEffect(()=>{let live=true;setExams([]);listCollections().then(rows=>{if(live)setExams(rows.filter(c=>c.kind==='exam'&&!isLaterExamCollection(c)))}).catch(()=>{});return()=>{live=false}},[scope])
 useEffect(()=>{setMenu(null)},[pathname,search])

 useEffect(()=>{if(!menu)return;const outside=(e:PointerEvent)=>{if(!shell.current?.contains(e.target as Node))setMenu(null)};document.addEventListener('pointerdown',outside);return()=>document.removeEventListener('pointerdown',outside)},[menu])
 const focused=focusedSession(pathname,search)
 const openFind=()=>window.dispatchEvent(new Event('finna-open-find'))
 const active=(label:string)=>label==='Home'?pathname==='/feed':label==='Exams'?/^\/(exams|group-b)/.test(pathname):label==='Subjects'?/^\/(library|english|arithmetic|mizo|atlas|chronicle|stats|vocabulary|important-days)/.test(pathname):label==='Papers'?pathname==='/past-papers':label==='Practice'?/^\/(bank|website-bank|tests|revise|revision|mistakes)/.test(pathname)&&new URLSearchParams(search).get('view')!=='papers':/^\/(community|creators)/.test(pathname)
 const staff=reviewDestinations(access)
 return <header ref={shell} data-app-header className={'finna-shell'+(focused?' finna-focused':'')} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))setMenu(null)}}>
  <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-[80] focus:rounded-lg focus:bg-card focus:p-3 focus:text-ink">Skip to content</a>
  {!focused&&<div className="finna-top"><div className="finna-wrap finna-top-inner"><span className="finna-top-tag">Study</span><span className="finna-top-note">Past papers. Clear sources. Your next step.</span><div className="finna-top-actions">{streak!==null&&streak>0&&<Link to="/profile" className="text-[#FFC83D]">{streak} day streak</Link>}{account.authenticated&&<Link to="/inbox">Inbox {unread!==null&&<span className="ml-1 rounded-full bg-white px-1.5 text-[11px] font-extrabold text-[#0E1330]">{unread}</span>}</Link>}<button type="button" className="finna-theme" onClick={()=>setTheme(theme==='night'?'paper':'night')} aria-label={`Switch to ${theme==='night'?'light':'dark'} theme`}>{theme==='night'?'Light':'Dark'}</button>{staff.length>0&&<nav aria-label="Workspaces" className="flex items-center gap-4">{staff.slice(0,2).map(link=><Link key={link.to} to={link.to}>{link.label}</Link>)}</nav>}</div></div></div>}
  {!focused&&<div className="finna-phone-header"><div className="finna-phone-heading">{pathname!=='/feed'&&<Link to={/^\/(bank|exams)\//.test(pathname)?'/exams':pathname.startsWith('/library/')?'/library':'/feed'} aria-label="Back to study home" className="finna-phone-back">‹</Link>}<h1>{mobileTitle(pathname)}</h1></div><nav aria-label="Phone quick actions">{pathname==='/feed'&&streak!==null&&<Link to="/profile" className="finna-phone-streak">{streak} day streak</Link>}<button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/></button><Link to="/create" aria-label="Create"><NavIcon name="create"/></Link><Link to="/inbox" aria-label={unread?'Inbox, '+unread+' unread':'Inbox'}><span aria-hidden="true">✉</span>{unread!==null&&unread>0&&<span className="finna-phone-unread">{unread>99?'99+':unread}</span>}</Link><Link to="/more" aria-label="More tools and appearance"><NavIcon name="more"/></Link></nav></div>}
  <div className="finna-brand-row"><div className="finna-wrap finna-brand-inner">
   <Link to="/feed" className="finna-brand" aria-label="Finna home">Finna<span>.</span></Link>
   {!focused&&<button type="button" className="finna-search-trigger" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/><span>Find an exam, question or tool</span><kbd>Ctrl K</kbd></button>}
   <div className="finna-mobile-tools">{!focused&&<><button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/></button><button type="button" aria-label={`Switch to ${theme==='night'?'light':'dark'} theme`} onClick={()=>setTheme(theme==='night'?'paper':'night')}>{theme==='night'?'☀':'☾'}</button></>}</div>
   {!focused&&<Link to="/create" className="finna-create">Create</Link>}
   {focused&&<Link to="/feed" className="ml-auto text-sm font-semibold text-link">Study home →</Link>}
   {account.authenticated?<Link to="/profile" className="finna-account" aria-label="Your profile"><Avatar look={account.avatar} initials={account.email?.slice(0,2).toUpperCase()||'Me'}/></Link>:<Link to={'/login?next='+encodeURIComponent(pathname+search)} className="finna-account">Sign in</Link>}
  </div></div>
  {!focused&&<div className="finna-nav" onMouseLeave={()=>setMenu(null)}><div className="finna-wrap finna-nav-inner"><nav aria-label="Primary navigation" className="flex items-center gap-0.5">{NAV.map(item=><div key={item.label} className="flex items-center" onMouseEnter={()=>setMenu(MENUS[item.label]?item.label:null)}><Link to={item.to} className="finna-nav-link" aria-current={active(item.label)?'page':undefined}>{item.label}</Link>{MENUS[item.label]&&<button type="button" className="-ml-1.5 mr-1 grid h-9 w-5 place-items-center rounded-md text-[10px] text-secondary" aria-label={`${item.label} menu`} aria-expanded={menu===item.label} aria-controls="finna-mega-menu" onClick={()=>setMenu(menu===item.label?null:item.label)}>⌄</button>}</div>)}</nav><div className="finna-quick"><Link to="/revise">Revise</Link><Link to="/desk" className="finna-secondary-tool">Study desk</Link><Link to="/games" className="finna-secondary-tool">Play</Link><Link to="/atlas" className="finna-secondary-tool">Atlas</Link><Link to="/chronicle" className="finna-secondary-tool">Chronicle</Link><Link to={selected?'/exams/'+selected.id:'/exams'} className="finna-exam-chip">{selected?'My exam: '+selected.title.replace(/\s*[·(].*$/,'').slice(0,24):'Choose your exam'}</Link></div></div>
   {menu&&MENUS[menu]&&<div id="finna-mega-menu" className="finna-menu"><div className="finna-wrap finna-menu-inner">{MENUS[menu].map(col=><div key={col.title}><h2 className="finna-menu-title">{col.title}</h2>{col.links.map(([to,label,note])=><Link key={to} to={to}>{label}<small>{note}</small></Link>)}</div>)}</div></div>}
  </div>}
  {!focused&&<QuickFind access={access} trigger={false}/>}
  {!focused&&(/^\/(?:bank|exams|library|english|arithmetic|group-b|past-papers)(?:\/|$)/.test(pathname)||(scope==='all'&&/^\/desk(?:\/|$)/.test(pathname)))&&<BrowseAllowance/>}
 </header>
}
