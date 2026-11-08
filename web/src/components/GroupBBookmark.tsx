import {useEffect,useState,useRef} from 'react'
import {getExamBookmarks,saveExamBookmark,removeExamBookmark} from '../lib/api'

export default function GroupBBookmark({collection}:{collection:string}){
 const generation=useRef(0)
 const [saved,setSaved]=useState(false),[ready,setReady]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[refresh,setRefresh]=useState(0)
 useEffect(()=>{let live=true;generation.current++;setReady(false);setBusy(false);setSaved(false);setError('');getExamBookmarks().then(data=>{if(live){setSaved(data.collection_ids.includes(collection));setReady(true)}}).catch(()=>{if(live)setError('Saved exams could not load.')});const update=()=>setRefresh(n=>n+1);window.addEventListener('ism-auth-change',update);return()=>{live=false;generation.current++;window.removeEventListener('ism-auth-change',update)}},[collection,refresh])
 async function toggle(){const version=generation.current;setBusy(true);setError('');try{if(saved)await removeExamBookmark(collection);else await saveExamBookmark(collection);if(version===generation.current)setSaved(!saved)}catch(e){if(version===generation.current)setError((e as Error).message)}finally{if(version===generation.current)setBusy(false)}}
 return <div className="max-w-full"><button type="button" disabled={!ready||busy} aria-pressed={saved} onClick={()=>void toggle()} className="min-h-11 rounded-pill border border-hairline bg-card px-3 text-[12px] font-semibold disabled:opacity-50">{busy?'Saving…':saved?'Saved exam':'Save exam'}</button>{error&&<p role="alert" className="mt-1 max-w-xs text-[12px] text-mypick">{error}{!ready&&<button className="min-h-11 px-2 underline" onClick={()=>setRefresh(n=>n+1)}>Retry</button>}</p>}</div>
}
