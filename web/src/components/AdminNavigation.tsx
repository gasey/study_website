import {Link} from 'react-router-dom'
import QuickFind from './QuickFind'
import {ADMIN_GROUPS,ADMIN_SECTIONS,adminTabHref,canOpenAdminTab,type AdminGrant} from '../lib/adminNavigation'

/** Admin sidebar. Everything here is derived from `ADMIN_SECTIONS` (§VIII.6): this file
 *  used to keep its own group list, which silently hid eleven sections — including the
 *  authoring console — from anyone who did not already know the URL. */
export default function AdminNavigation({tab,grants,onNavigate}:{tab:string;grants:AdminGrant[];onNavigate:(tab:string)=>void}){
 const available=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],grants))
 const start=available.filter(s=>s[2]==='start')
 const groups=ADMIN_GROUPS.map(([id,title])=>[id,title,available.filter(s=>s[2]===id)] as const).filter(([,,rows])=>rows.length)
 return <>
  <div className="px-3 pt-3"><QuickFind access={{grants,assigned:false}} admin/></div>
  <div className="p-3 lg:hidden"><label className="text-xs text-[#A9B0D0]" htmlFor="admin-section">Admin section</label><select id="admin-section" value={available.length?tab:''} disabled={!available.length} onChange={e=>onNavigate(e.target.value)} className="mt-2 min-h-12 w-full rounded-xl border border-[#28315D] bg-[#151B3A] px-3 text-sm text-white">{!available.length&&<option value="">Sign in with admin access</option>}{start.map(s=><option key={s[0]} value={s[0]}>{s[1]}</option>)}{groups.map(([id,title,rows])=><optgroup key={id} label={title}>{rows.map(s=><option key={s[0]} value={s[0]}>{s[1]}</option>)}</optgroup>)}</select></div>
  <nav aria-label="Bank administration" className="hidden px-3 pb-6 lg:block">
   {start.length>0&&<div className="mt-4 space-y-0.5">{start.map(s=><Link key={s[0]} to={adminTabHref(s[0])} aria-current={tab===s[0]?'page':undefined} className="flex min-h-10 items-center rounded-[10px] px-3 py-2 text-sm font-bold">{s[1]}</Link>)}</div>}
   {groups.map(([id,title,rows])=><section key={id} className="mt-5"><h2 className="px-3 pb-2 text-xs font-bold uppercase tracking-[.08em] text-[#A9B0D0]">{title}</h2><div className="space-y-0.5">{rows.map(s=><Link key={s[0]} to={adminTabHref(s[0])} aria-current={tab===s[0]?'page':undefined} className="flex min-h-10 items-center rounded-[10px] px-3 py-2 text-sm font-semibold">{s[1]}</Link>)}</div></section>)}
  </nav>
  {available.length>0&&<nav aria-label="Review shortcuts" className="space-y-1 border-t border-[#28315D] p-3"><Link to={adminTabHref('edit')} className="flex min-h-11 items-center rounded-xl px-3 text-sm font-bold text-white">Authoring console →</Link><Link to={adminTabHref('editorial')} className="flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold">Review workspace →</Link><Link to="/admin/bank?tab=editorial&workspace=attention&queue=tags" className="flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold">Find &amp; fix tags →</Link></nav>}
 </>
}
