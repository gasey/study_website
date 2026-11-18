import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'

const BUTTON='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold disabled:opacity-50'
const UNCERTAIN='Blocking was not confirmed. Community content is being refreshed; check Blocked users before retrying.'

/** Use the existing account block; never require a conduct report to block. */
export default function BlockAuthor({authorId,disabled=false}:{authorId:string;disabled?:boolean}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('')
 const generation=useRef(0)
 useEffect(()=>{const clear=()=>{++generation.current;setBusy(false);setError('')};window.addEventListener('ism-auth-change',clear);window.addEventListener('ism-auth-expired',clear);return()=>{++generation.current;window.removeEventListener('ism-auth-change',clear);window.removeEventListener('ism-auth-expired',clear)}},[authorId])
 async function block(){
  const run=generation.current;setBusy(true);setError('')
  let message='Author blocked. Their content is hidden while you are signed in. Unblocking is available in Blocked users.'
  try{await reviewRequest('/creators/'+encodeURIComponent(authorId)+'/block',{enabled:true})}
  catch{message=UNCERTAIN;if(run===generation.current)setError(message)}
  if(run!==generation.current)return
  setBusy(false)
  // An uncertain response may have committed. Refresh every mounted community
  // reader on both outcomes, discarding late reads through their generation guards.
  window.dispatchEvent(new CustomEvent('ism-community-change',{detail:{message}}))
 }
 return <span className="inline-flex min-w-0 flex-col items-start gap-2">
  <button type="button" disabled={busy||disabled} className={BUTTON} onClick={()=>void block()}>{busy?'Blocking…':'Block this author'}</button>
  {error&&<span role="alert" className="max-w-md break-words text-[13px] text-mypick">{error}</span>}
 </span>
}

/** Kept outside fetched post trees so feedback survives their privacy refresh. */
export function CommunityFeedback(){
 const [message,setMessage]=useState('')
 useEffect(()=>{
  const change=(event:Event)=>setMessage((event as CustomEvent<{message?:string}>).detail?.message||'')
  const clear=()=>setMessage('')
  window.addEventListener('ism-community-change',change);window.addEventListener('ism-auth-change',clear);window.addEventListener('ism-auth-expired',clear)
  return()=>{window.removeEventListener('ism-community-change',change);window.removeEventListener('ism-auth-change',clear);window.removeEventListener('ism-auth-expired',clear)}
 },[])
 if(!message)return null
 return <p role="status" className="my-3 rounded-[8px] border border-hairline bg-paper p-3 text-[13px] text-secondary">{message} <Link className="inline-flex min-h-11 items-center font-semibold text-link" to="/creators/settings#blocked-users">Blocked users →</Link></p>
}
