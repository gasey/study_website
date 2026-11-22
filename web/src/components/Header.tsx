import {useEffect,useRef,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {getAccountSession,getProgressSummary,listCollections,isLaterExamCollection,type AccountSession,type Collection} from '../lib/api'
import {reviewRequest,reviewSession} from '../lib/review'
import {reviewDestinations,type ReviewAccess} from '../lib/reviewNavigation'
import {useExamScope} from '../lib/examScope'
import {focusedSession,mobileTitle} from '../lib/navigation'
import {destinationPath,destinationsForSurface,menuFor,type Destination,type NavMenu} from '../lib/siteMap'
import {useStudyTheme} from '../lib/theme'
import {usePreferredExam} from '../lib/preferredExam'
import {Avatar} from './ui'
import QuickFind from './QuickFind'
import NavIcon from './NavIcon'
import BrowseAllowance from './BrowseAllowance'

const NAV_ITEMS=destinationsForSurface('nav')
const HOME_PATH=destinationPath('home'),INBOX_PATH=destinationPath('inbox'),PROFILE_PATH=destinationPath('profile')
const CREATE_PATH=destinationPath('create'),INDEX_PATH=destinationPath('index')
const EXAMS_PATH=destinationPath('exams'),LIBRARY_PATH=destinationPath('library')
const MENUS:Record<string,Destination[]>=Object.fromEntries(NAV_ITEMS.filter(i=>i.menu).map(i=>[i.id,menuFor(i.menu as NavMenu)]))

/** Desktop nav (§VII.3.3, revised 22 November 2026).
 *  Menus are generated from `siteMap.ts`, so a dropdown can never point at a
 *  route the manifest does not define — the failure mode of the hand-synced
 *  MENUS table this replaces. The nav label stays a real link and the chevron
 *  is a separate button, so clicking "Exams" still goes to /exams. Opening is
 *  by click or ArrowDown, never hover: hover menus are unusable on touch and
 *  trap keyboard users. Escape closes and returns focus to the trigger. */
export default function Header(){
 const {pathname,search}=useLocation(),scope=useExamScope()
 const [theme,setTheme]=useStudyTheme(),[access,setAccess]=useState<ReviewAccess>({grants:[],assigned:false})
 const [account,setAccount]=useState<AccountSession>({authenticated:false}),[unread,setUnread]=useState<number|null>(null),[streak,setStreak]=useState<number|null>(null)
 const [exams,setExams]=useState<Collection[]>([]),[menu,setMenu]=useState<string|null>(null)
 const selected=usePreferredExam(exams),shell=useRef<HTMLElement>(null)
 const triggers=useRef<Record<string,HTMLButtonElement|null>>({})
 useEffect(()=>{let live=true,version=0
  const load=()=>{const run=++version;setUnread(null);setStreak(null);setAccess({grants:[],assigned:false});setAccount({authenticated:false})
   getProgressSummary().then(p=>{if(live&&run===version)setStreak(p.current_streak)}).catch(()=>{})
   getAccountSession().then(async a=>{if(!live||run!==version)return;setAccount(a);if(!a.authenticated)return
    const s=await reviewSession();if(!live||run!==version)return
    setAccess({grants:s.grants,assigned:s.grants.length?false:(await reviewRequest<{items:{state:string}[]}>('/editorial/assignments')).items.some(x=>x.state==='active'||x.state==='pending')})
    reviewRequest<{unread:number}>('/inbox/unread').then(r=>{if(live&&run===version)setUnread(r.unread)}).catch(()=>{})
   }).catch(()=>{})}
  load();const events=['ism-auth-change','ism-avatar-change','ism-notifications-change','focus'];events.forEach(e=>window.addEventListener(e,load));return()=>{live=false;events.forEach(e=>window.removeEventListener(e,load))}
 },[])
 useEffect(()=>{let live=true;setExams([]);listCollections().then(rows=>{if(live)setExams(rows.filter(c=>c.kind==='exam'&&!isLaterExamCollection(c)))}).catch(()=>{});return()=>{live=false}},[scope])
 useEffect(()=>{setMenu(null)},[pathname,search])
 useEffect(()=>{if(!menu)return
  const outside=(e:PointerEvent)=>{if(!shell.current?.contains(e.target as Node))setMenu(null)}
  const escape=(e:KeyboardEvent)=>{if(e.key==='Escape'){setMenu(null);triggers.current[menu]?.focus()}}
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape)
  return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape)}
 },[menu])
 const focused=focusedSession(pathname,search)
 const openFind=()=>window.dispatchEvent(new Event('finna-open-find'))
 const active=(id:string)=>id==='exams'?/^\/(exams|group-b)/.test(pathname):id==='papers'?pathname==='/past-papers':id==='practice'?/^\/(practice|bank|tests|revise|games)/.test(pathname):id==='guides'?/^\/(guides|library|english|arithmetic|mizo|atlas|chronicle|stats)/.test(pathname):id==='community'?/^\/(community|creators|materials|create)/.test(pathname):pathname===INDEX_PATH
 const staff=reviewDestinations(access)
 return <header ref={shell} data-app-header className={'finna-shell'+(focused?' finna-focused':'')} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))setMenu(null)}}>
  <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-[80] focus:rounded-lg focus:bg-card focus:p-3 focus:text-ink">Skip to content</a>
  {!focused&&<div className="finna-top"><div className="finna-wrap finna-top-inner"><span className="finna-top-tag">Study</span><span className="finna-top-note">Past papers. Clear sources. Your next step.</span><div className="finna-top-actions">{streak!==null&&streak>0&&<Link to={PROFILE_PATH} className="text-[#FFC83D]">{streak} day streak</Link>}{account.authenticated&&<Link to={INBOX_PATH}>Inbox {unread!==null&&<span className="ml-1 rounded-full bg-white px-1.5 text-[11px] font-extrabold text-[#0E1330]">{unread}</span>}</Link>}<button type="button" className="finna-theme" onClick={()=>setTheme(theme==='night'?'paper':'night')} aria-label={`Switch to ${theme==='night'?'light':'dark'} theme`}>{theme==='night'?'Light':'Dark'}</button>{staff.length>0&&<nav aria-label="Workspaces" className="flex items-center gap-4">{staff.slice(0,2).map(link=><Link key={link.to} to={link.to}>{link.label}</Link>)}</nav>}</div></div></div>}
  {!focused&&<div className="finna-phone-header"><div className="finna-phone-heading">{pathname!==HOME_PATH&&<Link to={/^\/(bank|exams)\//.test(pathname)?EXAMS_PATH:pathname.startsWith('/library/')?LIBRARY_PATH:HOME_PATH} aria-label="Back to home" className="finna-phone-back">‹</Link>}<h1>{mobileTitle(pathname)}</h1></div><nav aria-label="Phone quick actions">{pathname===HOME_PATH&&streak!==null&&<Link to={PROFILE_PATH} className="finna-phone-streak">{streak} day streak</Link>}<button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/></button><Link to={CREATE_PATH} aria-label="Create"><NavIcon name="create"/></Link><Link to={INBOX_PATH} aria-label={unread?'Inbox, '+unread+' unread':'Inbox'}><span aria-hidden="true">✉</span>{unread!==null&&unread>0&&<span className="finna-phone-unread">{unread>99?'99+':unread}</span>}</Link><Link to={INDEX_PATH} aria-label="Index and appearance"><NavIcon name="more"/></Link></nav></div>}
  <div className="finna-brand-row"><div className="finna-wrap finna-brand-inner">
   <Link to={HOME_PATH} className="finna-brand" aria-label="Finna home">Finna<span>.</span></Link>
   {!focused&&<button type="button" className="finna-search-trigger" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/><span>Find an exam, question or guide</span><kbd>Ctrl K</kbd></button>}
   <div className="finna-mobile-tools">{!focused&&<><button type="button" onClick={openFind} aria-label="Quick find" aria-haspopup="dialog"><NavIcon name="search"/></button><button type="button" aria-label={`Switch to ${theme==='night'?'light':'dark'} theme`} onClick={()=>setTheme(theme==='night'?'paper':'night')}>{theme==='night'?'☀':'☾'}</button></>}</div>
   {!focused&&<Link to={CREATE_PATH} className="finna-create">Create</Link>}
   {focused&&<Link to={HOME_PATH} className="ml-auto text-sm font-semibold text-link">Home →</Link>}
   {account.authenticated?<Link to={PROFILE_PATH} className="finna-account" aria-label="Your profile"><Avatar look={account.avatar} initials={account.email?.slice(0,2).toUpperCase()||'Me'}/></Link>:<Link to={'/login?next='+encodeURIComponent(pathname+search)} className="finna-account">Sign in</Link>}
  </div></div>
  {!focused&&<div className="finna-nav"><div className="finna-wrap finna-nav-inner">
   <nav aria-label="Primary navigation" className="flex items-center gap-0.5">{NAV_ITEMS.map(item=>{const items=MENUS[item.id]||[]
    return <div key={item.id} className="flex items-center">
     <Link to={item.path} className="finna-nav-link" aria-current={active(item.id)?'page':undefined}>{item.label}</Link>
     {items.length>0&&<button type="button" ref={el=>{triggers.current[item.id]=el}} className="-ml-1.5 mr-1 grid h-9 w-5 place-items-center rounded-md text-[10px] text-secondary" aria-label={`${item.label} menu`} aria-expanded={menu===item.id} aria-controls={menu===item.id?'finna-mega-menu':undefined} onClick={()=>setMenu(menu===item.id?null:item.id)} onKeyDown={e=>{if(e.key==='ArrowDown'){e.preventDefault();setMenu(item.id)}}}>⌄</button>}
    </div>})}</nav>
   <div className="finna-quick"><Link to={selected?'/exams/'+selected.id:EXAMS_PATH} className="finna-exam-chip">{selected?'My exam: '+selected.title.replace(/\s*[·(].*$/,'').slice(0,24):'Choose your exam'}</Link></div>
  </div>
   {menu&&(MENUS[menu]||[]).length>0&&<div id="finna-mega-menu" className="finna-menu"><div className="finna-wrap finna-menu-inner"><div>{MENUS[menu].map(d=><Link key={d.id} to={d.path}>{d.label}<small>{d.blurb}</small></Link>)}</div></div></div>}
  </div>}
  {!focused&&<QuickFind access={access} trigger={false}/>}
  {!focused&&(/^\/(?:bank|exams|library|practice|english|arithmetic|group-b|past-papers)(?:\/|$)/.test(pathname)||(scope==='all'&&/^\/desk(?:\/|$)/.test(pathname)))&&<BrowseAllowance/>}
 </header>
}
