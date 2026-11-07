import {Link,useLocation} from 'react-router-dom'
import {PRIMARY_NAV,primarySection,focusedSession} from '../lib/navigation'
import NavIcon from './NavIcon'
export default function BottomBar(){
 const {pathname}=useLocation()
 if(pathname==='/'||focusedSession(pathname))return null
 return <nav aria-label="Primary navigation" className="sticky bottom-0 z-40 border-t border-hairline bg-card pb-[env(safe-area-inset-bottom)] lg:hidden"><div className="mx-auto flex max-w-shell">{PRIMARY_NAV.map(t=><Link key={t.to} to={t.to} aria-current={primarySection(pathname)===t.to?'page':undefined} className={'flex min-h-[60px] min-w-0 flex-1 flex-col items-center justify-center gap-1 text-[11px] '+(primarySection(pathname)===t.to?'font-semibold text-ink':'text-secondary')}><span className={'rounded-lg px-4 py-1 '+(primarySection(pathname)===t.to?'bg-[#EDE7DA]':'')}><NavIcon name={t.icon}/></span>{t.label}</Link>)}</div></nav>
}
