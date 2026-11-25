import {useState} from 'react'
import {Link} from 'react-router-dom'
import QuickFind from './QuickFind'
import {ADMIN_GROUPS,ADMIN_SECTIONS,adminTabHref,canOpenAdminTab,type AdminGrant} from '../lib/adminNavigation'

/** Admin sidebar. Everything here is derived from `ADMIN_SECTIONS` (§VIII.6): this file
 *  used to keep its own group list, which silently hid eleven sections — including the
 *  authoring console — from anyone who did not already know the URL. */
export default function AdminNavigation({tab,grants,onNavigate}:{tab:string;grants:AdminGrant[];onNavigate:(tab:string)=>void}){
 const [filter,setFilter]=useState('')
 const q=filter.trim().toLowerCase()
 const available=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],grants))
 const matching=q?available.filter(s=>`${s[0]} ${s[1]} ${s[4]}`.toLowerCase().includes(q)):available
 const start=matching.filter(s=>s[2]==='start')
 const groups=ADMIN_GROUPS.map(([id,title])=>[id,title,matching.filter(s=>s[2]===id)] as const).filter(([,,rows])=>rows.length)
 const allGroups=ADMIN_GROUPS.map(([id,title])=>[id,title,available.filter(s=>s[2]===id)] as const).filter(([,,rows])=>rows.length)
 return <>
  <div className="px-3 pt-3 space-y-2">
   <QuickFind access={{grants,assigned:false}} admin/>
   {available.length>6&&<input type="search" value={filter} onChange={e=>setFilter(e.target.value)} placeholder={`Filter ${available.length} tools…`} aria-label="Filter admin tools" className="hidden min-h-9 w-full rounded-[9px] border border-[#3A3631] bg-[#141210] px-2.5 text-xs text-[#E9E1D2] placeholder:text-[#8E8577] focus:border-[#FFC83D] focus:outline-none lg:block"/>}
  </div>
  <div className="p-3 lg:hidden"><label className="text-xs text-[#A9B0D0]" htmlFor="admin-section">Admin section</label><select id="admin-section" value={available.length?tab:''} disabled={!available.length} onChange={e=>onNavigate(e.target.value)} className="mt-2 min-h-12 w-full rounded-xl border border-[#28315D] bg-[#151B3A] px-3 text-sm text-white">{!available.length&&<option value="">Sign in with admin access</option>}{available.filter(s=>s[2]==='start').map(s=><option key={s[0]} value={s[0]}>{s[1]}</option>)}{allGroups.map(([id,title,rows])=><optgroup key={id} label={title}>{rows.map(s=><option key={s[0]} value={s[0]}>{s[1]}</option>)}</optgroup>)}</select></div>
  <nav aria-label="Bank administration" className="hidden px-3 pb-6 lg:block">
   {start.length>0&&<div className="mt-4 space-y-0.5">{start.map(s=><Link key={s[0]} to={adminTabHref(s[0])} aria-current={tab===s[0]?'page':undefined} className="flex min-h-10 items-center rounded-[10px] px-3 py-2 text-sm font-bold">{s[1]}</Link>)}</div>}
   {groups.map(([id,title,rows])=><section key={id} className="mt-5"><h2 className="px-3 pb-2 text-xs font-bold uppercase tracking-[.08em] text-[#A9B0D0]">{title}</h2><div className="space-y-0.5">{rows.map(s=><Link key={s[0]} to={adminTabHref(s[0])} aria-current={tab===s[0]?'page':undefined} className="flex min-h-10 items-center rounded-[10px] px-3 py-2 text-sm font-semibold">{s[1]}</Link>)}</div></section>)}
   {q&&!start.length&&!groups.length&&<p className="mt-4 px-3 text-xs text-[#A89F8E]">No admin tool matches “{filter}”.</p>}
  </nav>
  {available.length>0&&<nav aria-label="Daily admin shortcuts" className="space-y-1 border-t border-[#3A3631] p-3">
   <p className="px-3 pb-1 font-mono text-[10px] uppercase tracking-[.1em] text-[#A89F8E]">Daily workflow</p>
   <Link to={adminTabHref('edit')} className="flex min-h-10 items-center rounded-xl px-3 text-sm font-bold text-white">Authoring console →</Link>
   {canOpenAdminTab('conflicts',grants)&&<Link to={adminTabHref('conflicts')} className="flex min-h-10 items-center rounded-xl px-3 text-sm font-semibold">Answer conflicts →</Link>}
   {canOpenAdminTab('guides-studio',grants)&&<Link to={adminTabHref('guides-studio')} className="flex min-h-10 items-center rounded-xl px-3 text-sm font-semibold">Concept guides studio →</Link>}
   <Link to="/admin/bank?tab=editorial&workspace=attention&queue=tags" className="flex min-h-10 items-center rounded-xl px-3 text-sm font-semibold">Find &amp; fix tags →</Link>
  </nav>}
 </>
}
