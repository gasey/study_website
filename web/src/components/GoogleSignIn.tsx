import {accountContext} from '../lib/accountContext'
import {useEffect,useState} from 'react'
export async function googleRequest<T>(path:string,body?:unknown):Promise<T>{
 const identity=await accountContext()
 const response=await fetch('/api/auth/google/'+path,{method:body===undefined?'GET':'POST',credentials:'include',headers:{'Content-Type':'application/json',...(body===undefined?{}:{'x-review-csrf':identity.csrf||''})},cache:'no-store',...(body===undefined?{}:{body:JSON.stringify(body)})})
 const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Google sign-in failed');return data
}
export default function GoogleSignIn({link=false}:{link?:boolean}){
 const [enabled,setEnabled]=useState(false);const [error,setError]=useState('');const [busy,setBusy]=useState(false)
 useEffect(()=>{let live=true;googleRequest<{enabled:boolean}>('config').then(x=>{if(live)setEnabled(x.enabled)}).catch(()=>{});return()=>{live=false}},[])
 async function start(){setBusy(true);setError('');try{const r=await googleRequest<{url:string}>('start',{action:link?'link':'login'});window.location.assign(r.url)}catch(e){setError((e as Error).message);setBusy(false)}}
 if(!enabled)return null
 return <div className="my-5"><button type="button" disabled={busy} onClick={()=>void start()} className="min-h-11 w-full rounded-pill border border-hairline bg-white px-5 py-3 text-sm font-semibold disabled:opacity-50">{busy?'Opening Google…':link?'Link Google to this account':'Continue with Google'}</button>{link&&<p className="mt-2 text-xs text-secondary">Requires a recent sign-in and your authenticator if enabled. Existing progress stays with this account.</p>}{error&&<p role="alert" className="mt-3 text-sm text-mypick">{error}</p>}</div>
}
