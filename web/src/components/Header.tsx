import {currentExamScope, changeExamScope, useExamScope, type ExamScope} from '../lib/examScope'
import {reviewRequest} from '../lib/review'
import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { getAccountSession, getProgressSummary, type AccountSession, type Progress } from '../lib/api'
import { Avatar, CountBadge, GroupTitle, PillButton } from './ui'

/** App shell header, ported from markup line 34.
 *
 *  Note for anyone comparing against an earlier version: the six coloured
 *  area dots are NOT in the header. They appear in the landing hero and the
 *  footer mark. They were invented here once; don't put them back. */

const QUICK_NAV = [
  { to: '/exams', label: 'Exams' },
  { to: '/feed', label: 'Community' },
  { to: '/desk', label: 'Study desk' },
  { to: '/games', label: 'Games' },
]

const LIBRARY_NAV = [
  { to: '/library', label: 'All subjects & tools', detail: 'Open the study library' },
  { to: '/atlas', label: 'Interactive Atlas', detail: 'Explore places, rivers and historical maps' },
  { to: '/library/topics/geography', label: 'Geography', detail: 'India, the world and physical geography' },
  { to: '/library/topics/history', label: 'History', detail: 'Indian and world history' },
  { to: '/library/topics/polity', label: 'Polity', detail: 'Constitution and government' },
  { to: '/arithmetic', label: 'Arithmetic', detail: 'Methods, practice and papers' },
  { to: '/arithmetic?subject=reasoning-and-aptitude&view=practice', label: 'Reasoning', detail: 'Logic and aptitude practice' },
  { to: '/library/subjects/general-knowledge', label: 'General Knowledge', detail: 'Topics from past papers' },
  { to: '/mizo', label: 'Mizo', detail: 'Language, literature and culture' },
  { to: '/english', label: 'English', detail: 'Grammar, comprehension and writing' },
  { to: '/vocabulary', label: 'Vocabulary helper', detail: 'Recall and spaced review' },
  { to: '/essay', label: 'Essay writing', detail: 'Past-paper prompts and saved drafts' },
]

/** The mega-menu's columns. Items carry an optional badge and a one-line
 *  description, per markup line 61. Routes that do not exist yet fall
 *  through to the Placeholder screen, which is honest about it. */
const MENU: {
  title: string
  items: { to: string; title: string; tag: string; badge?: string; badgeBg?: string }[]
}[] = [
  {
    title: 'Study library',
    items: [
      { to: '/library', title: 'All subjects & tools', tag: 'Learn and practise within each module' },
      { to: '/arithmetic', title: 'Arithmetic & Reasoning', tag: 'Concepts · questions · papers' },
      { to: '/english', title: 'English', tag: 'Grammar · comprehension · writing' },
      { to: '/library/subjects/general-knowledge', title: 'General Knowledge', tag: 'Topic practice from past papers' },
      { to: '/mizo', title: 'Mizo', tag: 'Language, literature and culture practice' },
      { to: '/vocabulary', title: 'Vocabulary helper', tag: 'Recall and spaced review' },
      { to: '/essay', title: 'Essay writing', tag: 'Past-paper prompts and private drafts' },
      { to: '/atlas', title: 'Interactive Atlas', tag: 'Geography, history and polity maps' },
      { to: '/bank', title: 'Question source archive', tag: 'Full bank and paper provenance' },
    ],
  },
  {
    title: 'Exams & review',
    items: [
      { to: '/exams', title: 'Exams', tag: 'Papers, timed mocks and saved exams' },
      { to: '/revision', title: 'Daily revision', tag: 'Mistakes, saved questions and due vocabulary' },
      { to: '/mistakes', title: 'Mistakes', tag: 'What you got wrong, grouped' },
    ],
  },
  {
    title: 'Compete',
    items: [
      { to: '/games', title: 'Games', tag: 'Gauntlet, speed, duels & weekly cups' },
      { to: '/duel', title: 'Duel', tag: 'Private or random 1v1 games' },
      { to: '/rewards', title: 'My rewards', tag: 'XP, points and earned benefits' },
      { to: '/board', title: 'Leaderboard', tag: 'Learning XP · weekly and monthly' },
    ],
  },
  {
    title: 'Community',
    items: [
      { to: '/feed', title: 'Feed', tag: 'Doubts, materials, challenges' },
      { to: '/contribute', title: 'Contribute', tag: 'Improve questions and follow reviews' },
      { to: '/community/questions', title: 'Community questions', tag: 'Reviewed original MCQ practice' },
      { to: '/community/contributors', title: 'Contributors', tag: 'Published improvements and credit' },
      { to: '/desk', title: 'Study desk', tag: 'Your goals, revision, and weekly plan' },
      { to: '/studio', title: 'Creator studio', tag: 'Write and manage your publications' },
      { to: '/materials', title: 'Materials', tag: 'Read and save shared study resources' },
    ],
  },
  {
    title: 'You',
    items: [
      {to: '/search', title: 'Search everything', tag: 'Questions, people, notes, desks & listings'},
      { to: '/avatar', title: 'Avatar & inventory', tag: 'Customize your saved look' },
      { to: '/profile', title: 'Profile', tag: 'Your materials and progress' },
      { to: '/admin/bank', title: 'Bank administration', tag: 'Assigned reviewers and administrators' },
      { to: '/calendar', title: 'Exam calendar', tag: 'Official notices, dates & reminders' },
      { to: '/scoring', title: 'How scoring works', tag: 'XP, negative marking' },
    ],
  },
]

function ProgressPill() {
  const [p,setP]=useState<Progress|null>(null)
  useEffect(()=>{
    let live=true,version=0
    const load=()=>{const run=++version;getProgressSummary().then(data=>{if(live&&run===version)setP(data)}).catch(()=>{if(live&&run===version)setP(null)})}
    const accountChanged=()=>{setP(null);load()}
    load();window.addEventListener('ism-progress-change',load);window.addEventListener('ism-auth-change',accountChanged);window.addEventListener('focus',load)
    return()=>{live=false;window.removeEventListener('ism-progress-change',load);window.removeEventListener('ism-auth-change',accountChanged);window.removeEventListener('focus',load)}
  },[])
  if(!p||p.answered===0)return null
  return <span className="whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.08em] text-muted">{p.answered} answered · {Math.round((p.correct/p.answered)*100)}%</span>
}

export default function Header() {
  const [menu, setMenu] = useState(false)
  const [libraryMenu, setLibraryMenu] = useState(false)
  const [query, setQuery] = useState('')
  const nav = useNavigate()
  const { pathname } = useLocation()
  useExamScope()
  const ref = useRef<HTMLElement>(null)
  const [account,setAccount] = useState<AccountSession>({authenticated:false})
  const [unread,setUnread]=useState<number|null>(null)
  useEffect(()=>{let live=true,version=0;const load=()=>{const run=++version;if(!account.authenticated){setUnread(null);return}reviewRequest<{unread:number}>('/inbox/unread').then(r=>{if(live&&run===version)setUnread(r.unread)}).catch(()=>{if(live&&run===version)setUnread(null)})};load();const timer=window.setInterval(()=>{if(document.visibilityState==='visible')load()},30000);window.addEventListener('focus',load);window.addEventListener('ism-notifications-change',load);return()=>{live=false;clearInterval(timer);window.removeEventListener('focus',load);window.removeEventListener('ism-notifications-change',load)}},[account.authenticated,account.email])


  useEffect(() => { setMenu(false); setLibraryMenu(false) }, [pathname])
  useEffect(() => {
    let active=true,version=0;
    const sync=(event?:Event)=>{const run=++version;if(event?.type==='ism-auth-change')setAccount({authenticated:false});getAccountSession().then(r=>{if(active&&run===version)setAccount(r)}).catch(()=>{/* Retain known identity during a network failure. */})};
    sync();window.addEventListener('ism-auth-change',sync);window.addEventListener('ism-avatar-change',sync);window.addEventListener('focus',sync);
    return()=>{active=false;window.removeEventListener('ism-auth-change',sync);window.removeEventListener('ism-avatar-change',sync);window.removeEventListener('focus',sync)};
  }, [])

  // Dismiss on outside click and on Escape — a full-width overlay that only
  // closes via its own button is a trap.
  useEffect(() => {
    if (!menu && !libraryMenu) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) { setMenu(false); setLibraryMenu(false) }
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { setMenu(false); setLibraryMenu(false) } }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [menu, libraryMenu])

  return (
    <header
      ref={ref}
      className="sticky top-0 z-50 border-b border-hairline bg-card"
    >
      <div className="mx-auto flex min-h-[54px] max-w-shell flex-wrap items-center gap-3 px-6 py-2">
        <NavLink
          to="/feed"
          className="whitespace-nowrap font-display text-[22px] font-semibold -tracking-[0.01em]"
        >
          India Study Map
        </NavLink>

        <nav className="flex flex-wrap items-center gap-0.5">
          <button
            onClick={() => { setLibraryMenu(false); setMenu((m) => !m) }}
            aria-expanded={menu}
            className={`min-h-[44px] whitespace-nowrap rounded-pill border border-ink px-3 py-2 text-[14px] font-semibold ${
              menu ? 'bg-ink text-paper' : 'bg-transparent text-ink'
            }`}
          >
            Sections ▾
          </button>
          <div className="relative hidden sm:block">
            <button type="button" onClick={() => { setMenu(false); setLibraryMenu((open) => !open) }} aria-expanded={libraryMenu} aria-controls="library-nav-menu" className={`min-h-11 whitespace-nowrap rounded-pill px-3 py-2 text-[14px] font-medium ${pathname.startsWith('/library') || pathname==='/atlas' || libraryMenu ? 'text-ink underline decoration-2 underline-offset-[6px]' : 'text-secondary'}`}>Library ▾</button>
            {libraryMenu && <div id="library-nav-menu" className="absolute left-0 top-full z-50 mt-2 w-[305px] max-h-[min(70vh,560px)] overflow-y-auto rounded-[12px] border border-hairline bg-card p-2 shadow-[0_18px_40px_rgba(29,27,24,.14)]" aria-label="Study library navigation">
              {LIBRARY_NAV.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setLibraryMenu(false)} className="block rounded-[8px] px-3 py-2.5 hover:bg-paper focus-visible:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-link"><span className="block font-display text-[17px] font-medium">{item.label}</span><span className="mt-0.5 block text-[11px] text-muted">{item.detail}</span></NavLink>)}
            </div>}
          </div>
          {QUICK_NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                [
                  'hidden whitespace-nowrap px-3 py-2 text-[14px] font-medium sm:block',
                  isActive
                    ? 'text-ink underline decoration-2 underline-offset-[6px]'
                    : 'text-secondary',
                ].join(' ')
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="min-w-0 flex-1" />

        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (query.trim().length >= 2) nav(`/search?q=${encodeURIComponent(query.trim())}`)
          }}
          className="hidden md:block"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search questions, people, notes…"
            aria-label="Search India Study Map"
            className="h-9 w-[260px] min-w-[140px] rounded-pill border border-hairline bg-[#F7F3EA] px-3 text-[13px] text-ink outline-none placeholder:text-placeholder"
          />
        </form>

        <ProgressPill />

        <NavLink to={account.authenticated?'/billing':'/plans'} className="hidden rounded-pill border border-hairline px-2.5 py-1 font-mono text-[10px] uppercase tracking-[.06em] text-secondary sm:block">
          {account.authenticated ? `${account.plan_status==='trial'?'Pro trial':(account.plan_code||'Free')}${account.plan_status==='trial'&&account.trial_ends_at?` · ${Math.max(0,Math.ceil((new Date(account.trial_ends_at).getTime()-Date.now())/86400000))}d`:''}` : 'Free · Plans'}
        </NavLink>

        <NavLink
          to="/inbox"
          className="hidden items-center gap-1.5 px-1.5 py-2 text-[14px] font-medium md:flex"
        >
          Inbox {unread!==null&&<CountBadge>{unread>99?'99+':unread}</CountBadge>}
        </NavLink>

        <PillButton onClick={() => nav('/feed')}>Community</PillButton>

        {!account.authenticated&&<NavLink to="/login" className="hidden rounded-pill px-2 py-2 text-[13px] font-semibold sm:inline">Log in</NavLink>}
        {!account.authenticated&&<NavLink to="/join" className="rounded-pill bg-ink px-3 py-2 text-[13px] font-semibold text-white">Join free</NavLink>}
        <NavLink to={account.authenticated?'/profile':'/login'} className="flex items-center">
          <Avatar look={account.avatar} initials={account.email?.slice(0,2).toUpperCase() || 'VH'} />
          <span className="-ml-3.5 rounded-pill bg-rewards-dark px-1.5 py-px font-mono text-[10px] font-medium text-white">
            L1
          </span>
        </NavLink>
      </div>

      {menu && (
        <div className="absolute inset-x-0 top-full border-b border-hairline bg-card shadow-[0_18px_40px_rgba(29,27,24,.12)]">
          <div className="mx-auto grid max-w-shell gap-x-10 gap-y-7 px-6 pb-8 pt-7 [grid-template-columns:repeat(auto-fit,minmax(240px,1fr))]">
            {MENU.map((col) => (
              <div key={col.title}>
                <GroupTitle>{col.title}</GroupTitle>
                {col.items.map((it) => (
                  <NavLink key={it.to + it.title} to={it.to} className="block py-2">
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1 font-display text-[18px] font-medium">
                      {it.title}
                      {it.badge && (
                        <span
                          className={`shrink-0 whitespace-nowrap rounded-pill px-[7px] py-[2px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-[#FBF8F1] ${it.badgeBg}`}
                        >
                          {it.badge}
                        </span>
                      )}
                    </span>
                    <span className="mt-0.5 block text-[13px] text-muted [text-wrap:pretty]">
                      {it.tag}
                    </span>
                  </NavLink>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    {!pathname.startsWith('/admin')&&<div className="border-t border-hairline bg-[#F6F0E3] px-4 py-2 text-center text-[11px] text-secondary"><label className="inline-flex flex-wrap items-center justify-center gap-2 font-semibold text-ink">Question & exam focus <select aria-label="Question and exam focus" value={currentExamScope()} disabled={pathname.includes('/mock')} onChange={e=>nav(changeExamScope(e.target.value as ExamScope),{replace:true,preventScrollReset:true})} className="min-h-[36px] max-w-full rounded-md border border-hairline bg-card px-3 text-[12px]"><option value="mizoram-recruitment">MPSC & Mizoram recruitment</option><option value="all">All exams · all questions</option></select></label><span className="ml-2 hidden sm:inline">{pathname.startsWith('/games')?'Games currently use MPSC & Mizoram verified keys.':currentExamScope()==='all'?'Includes other exam systems and unassigned sources.':'LDC / UDC · Group B · Combined Prelims · LDE & departmental papers'}</span></div>}</header>
  )
}
