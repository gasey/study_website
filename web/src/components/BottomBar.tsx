import {Link,useLocation} from 'react-router-dom'
import {PRIMARY_NAV,primarySection,focusedSession} from '../lib/navigation'
import NavIcon from './NavIcon'
const TABS=PRIMARY_NAV
export default function BottomBar(){const {pathname,search}=useLocation();if(pathname==='/'||focusedSession(pathname,search))return null;return <nav aria-label="Mobile navigation" className="finna-bottom"><div className="finna-bottom-inner">{TABS.map(t=><Link key={t.to} to={t.to} aria-current={primarySection(pathname)===t.to?'page':undefined} ><span><NavIcon name={t.icon}/></span><span>{t.label}</span></Link>)}</div></nav>}
