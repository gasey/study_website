import {Link,useLocation} from 'react-router-dom'
import {PRIMARY_NAV,primarySection,focusedSession} from '../lib/navigation'
import NavIcon from './NavIcon'
export default function BottomBar(){
 const {pathname}=useLocation()
 if(pathname==='/'||focusedSession(pathname))return null
 return <nav aria-label="Primary navigation" className="sticky bottom-0 z-40 border-t border-hairline bg-card/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden"><div className="mx-auto flex max-w-shell">{PRIMARY_NAV.map(t=>{const active=primarySection(pathname)===t.to;return <Link key={t.to} to={t.to} aria-current={active?'page':undefined} className={'flex min-h-[60px] min-w-0 flex-1 flex-col items-center justify-center gap-1 text-[11px] transition-colors '+(active?'font-semibold text-ink':'text-secondary')}><span className={'rounded-pill px-4 py-1 transition-all duration-150 '+(active?'bg-practice-soft text-practice-dark scale-105':'')}><NavIcon name={t.icon}/></span>{t.label}</Link>})}</div></nav>
}
