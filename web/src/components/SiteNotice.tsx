import {useEffect,useState} from 'react'
type Notice={message:string;expires_at:string|null;version:number}

/** Public plain-text announcement, shared by every web route. */
export default function SiteNotice(){
 const [notice,setNotice]=useState<Notice|null>(null)
 useEffect(()=>{let live=true,sequence=0,controller:AbortController|null=null
  async function load(){const request=++sequence;controller?.abort();const current=new AbortController();controller=current;const timer=window.setTimeout(()=>current.abort(),8000)
   try{const response=await fetch('/api/site-notice',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('Notice unavailable');const data=await response.json() as Notice
    if(live&&request===sequence)setNotice(typeof data.message==='string'&&data.message.length<=500&&data.message.trim()&&(!data.expires_at||Date.parse(data.expires_at)>Date.now())?data:null)
   }catch{if(live&&request===sequence)setNotice(null)}finally{window.clearTimeout(timer)}
  }
  const visible=()=>{if(document.visibilityState==='visible')void load()},changed=()=>void load()
  void load();const timer=window.setInterval(visible,60000);document.addEventListener('visibilitychange',visible);window.addEventListener('ism-site-notice-change',changed)
  return()=>{live=false;sequence++;controller?.abort();window.clearInterval(timer);document.removeEventListener('visibilitychange',visible);window.removeEventListener('ism-site-notice-change',changed)}
 },[])
 useEffect(()=>{if(!notice?.expires_at)return;let timer:number;const expiry=Date.parse(notice.expires_at)
  const expire=()=>{const remaining=expiry-Date.now();if(remaining<=0)setNotice(null);else timer=window.setTimeout(expire,Math.min(remaining,2147483647))};expire();return()=>window.clearTimeout(timer)
 },[notice?.expires_at])
 if(!notice)return null
 return <aside aria-label="Site announcement" className="border-b border-hairline bg-attention-soft text-attention"><div role="status" className="mx-auto flex max-w-[1320px] flex-wrap gap-x-3 gap-y-1 px-4 py-3 text-sm sm:px-7"><strong>Site notice</strong><span className="min-w-0 flex-1 whitespace-pre-wrap break-words">{notice.message}</span></div></aside>
}
