import {Link} from 'react-router-dom'
import QuickFind from './QuickFind'
import {ADMIN_SECTIONS,adminTabHref,canOpenAdminTab,type AdminGrant} from '../lib/adminNavigation'
const GROUPS:[string,string,string[]][]=[
 ['daily','Daily',['overview','questions','organization']],
 ['sources','Papers & coverage',['pdf-library','intake','quality','exams','papers']],
 ['review','Review & publication',['workflow','retag','review','reports','publications','current-affairs']],
 ['community','Content & community',['content','discussions','desks','calendar']],
 ['system','Accounts & settings',['ops','users','rewards','people','audit']],
 ['reference','References',['modules','taxonomy','database']],
]
export default function AdminNavigation({tab,grants,onNavigate}:{tab:string;grants:AdminGrant[];onNavigate:(tab:string)=>void}){
 const available=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],grants)),owner=grants.some(g=>g.role==='owner'&&g.subject_id===null)
 return <>
  <div className="px-3 pt-3"><QuickFind access={{grants,assigned:false}} admin/></div>
  <div className="p-3 lg:hidden"><label className="text-xs text-[#A9B0D0]" htmlFor="admin-section">Admin section</label><select id="admin-section" value={available.length?tab:''} disabled={!available.length} onChange={e=>onNavigate(e.target.value)} className="mt-2 min-h-12 w-full rounded-xl border border-[#28315D] bg-[#151B3A] px-3 text-sm text-white">{!available.length&&<option value="">Sign in with admin access</option>}{GROUPS.map(([id,title,ids])=>{const rows=available.filter(s=>ids.includes(s[0]));return rows.length?<optgroup key={id} label={title}>{rows.map(s=><option key={s[0]} value={s[0]}>{s[1]}</option>)}</optgroup>:null})}</select></div>
  <nav aria-label="Bank administration" className="hidden px-3 pb-6 lg:block">{GROUPS.map(([id,title,ids])=>{const rows=ids.flatMap(key=>available.filter(s=>s[0]===key));if(!rows.length)return null;return <section key={id} className="mt-5"><h2 className="px-3 pb-2 text-xs font-bold uppercase tracking-[.08em] text-[#A9B0D0]">{title}</h2><div className="space-y-0.5">{rows.map(s=><Link key={s[0]} to={adminTabHref(s[0])} aria-current={tab===s[0]?'page':undefined} className="flex min-h-10 items-center rounded-[10px] px-3 py-2 text-sm font-semibold">{s[1]}</Link>)}</div></section>})}</nav>
  {available.length>0&&<nav aria-label="Review shortcuts" className="space-y-1 border-t border-[#28315D] p-3"><Link to="/admin/bank?tab=editorial" className="flex min-h-11 items-center rounded-xl px-3 text-sm font-bold text-white">Review workspace →</Link><Link to="/admin/bank?tab=editorial&workspace=attention&queue=tags" className="flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold">Find & fix tags →</Link>{owner&&<Link to="/admin/atlas" className="flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold">Atlas topics →</Link>}{owner&&<Link to="/admin/bank?tab=workbench" className="flex min-h-11 items-center rounded-xl px-3 text-sm font-semibold">PDF workbench →</Link>}</nav>}
 </>
}
