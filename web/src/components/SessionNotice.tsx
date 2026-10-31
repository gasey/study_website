import {logoutAccount} from '../lib/api'
import {useEffect,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
export default function SessionNotice(){
 const [notice,setNotice]=useState('');const [expired,setExpired]=useState(false);const location=useLocation()
 useEffect(()=>{const inform=(e:Event)=>setNotice((e as CustomEvent<string>).detail);const expire=()=>setExpired(true),clear=()=>{setExpired(false);setNotice('')};window.addEventListener('ism-account-notice',inform);window.addEventListener('ism-auth-expired',expire);window.addEventListener('ism-auth-change',clear);return()=>{window.removeEventListener('ism-account-notice',inform);window.removeEventListener('ism-auth-expired',expire);window.removeEventListener('ism-auth-change',clear)}},[])
 if(notice)return <div role="status" className="border-b border-hairline bg-attention-soft px-4 py-3 text-[14px]">{notice}</div>
 if(!expired)return null
 return <div role="alert" className="border-b border-hairline bg-attention-soft px-4 py-3 text-[14px]">Your session expired. Sign in again before saving. <Link to={'/login?next='+encodeURIComponent(location.pathname+location.search+location.hash)} className="font-semibold text-link underline">Sign in →</Link> <button className="ml-3 min-h-11 underline" onClick={async()=>{try{await logoutAccount();window.dispatchEvent(new Event('ism-auth-change'))}catch(e){setNotice((e as Error).message)}}}>Continue as guest</button></div>
}
