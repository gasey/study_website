import {useEffect,useState} from 'react'
import type {StatsObservation} from './stats-types'

export function statsNumber(value:number|null|undefined,compact=true):string {
 if(value==null||!Number.isFinite(value))return 'Not available'
 return new Intl.NumberFormat(compact?'en-GB':'en-IN',{maximumFractionDigits:compact?3:6,...(compact&&Math.abs(value)>=1000000?{notation:'compact' as const}:{})}).format(value)
}
export function statsDate(value?:string|null){
 if(!value)return 'Not checked yet'
 const date=new Date(value)
 return Number.isNaN(date.getTime())?'Date unavailable':date.toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})
}
export function statsPlaces(value:string|null,fallback='IND'){
 return [...new Set([fallback,...(value||'').split(',').filter(p=>/^[A-Z]{3}$|^IN-[A-Z]{2}$/.test(p)&&p!==fallback)])].slice(0,4)
}
export function statsRankingPath(id:string,releaseId:string,period:string|null,group:string,q:string,page:number){
 const params=new URLSearchParams({release_id:releaseId,limit:'25',offset:String((page-1)*25)})
 if(period)params.set('period',period)
 if(group)params.set('group',group)
 if(q)params.set('q',q)
 return `/metrics/${encodeURIComponent(id)}/rankings?${params}`
}
// A gap in a source series ends the line; missing years are never interpolated.
export function statsSegments(rows:StatsObservation[],periods:string[],place:string){
 const byPeriod=new Map(rows.filter(r=>r.place===place).map(r=>[r.period,r.value]))
 const segments:{period:string;value:number}[][]=[]
 let run:{period:string;value:number}[]=[]
 for(const period of periods){const value=byPeriod.get(period);if(value==null||!Number.isFinite(value)){if(run.length)segments.push(run);run=[]}else run.push({period,value})}
 if(run.length)segments.push(run)
 return segments
}

type Snapshot<T>={savedAt:number;data:T}
const CACHE_KEY='finna.stats.public.v1',MAX_AGE=24*60*60*1000,MAX_ITEMS=24
// This cache is restricted to public Stats GETs and never stores account responses.
export function readStatsSnapshot<T>(path:string,now=Date.now()):Snapshot<T>|null{
 try{const item=JSON.parse(localStorage.getItem(CACHE_KEY)||'{}')[path];return item&&typeof item.savedAt==='number'&&now>=item.savedAt&&now-item.savedAt<MAX_AGE&&'data'in item?item:null}catch{return null}
}
export function saveStatsSnapshot<T>(path:string,data:T,now=Date.now()){
 try{const cache=JSON.parse(localStorage.getItem(CACHE_KEY)||'{}');cache[path]={savedAt:now,data};const entries=Object.entries(cache).filter(([,v])=>now-(v as Snapshot<unknown>).savedAt<MAX_AGE).sort((a,b)=>(b[1] as Snapshot<unknown>).savedAt-(a[1] as Snapshot<unknown>).savedAt).slice(0,MAX_ITEMS);localStorage.setItem(CACHE_KEY,JSON.stringify(Object.fromEntries(entries)))}catch{/* Storage may be disabled or full. Live reads still work. */}
}
export function useStatsRead<T>(path:string|null){
 const [retry,setRetry]=useState(0)
 const [state,setState]=useState<{path:string|null;data:T|null;error:string;offlineAt:number|null}>({path:null,data:null,error:'',offlineAt:null})
 useEffect(()=>{
  if(!path)return
  const controller=new AbortController();let active=true
  setState({path,data:null,error:'',offlineAt:null})
  const timer=setTimeout(()=>controller.abort(),20000)
  void (async()=>{
   let allowFallback=true
   try{
    if(!/^\/(overview(?:\?|$)|sources$|surveys(?:\/|$)|metrics\/)/.test(path)||path.includes('..')){allowFallback=false;throw Error('Unsupported Stats request')}
    const response=await fetch('/api/stats'+path,{signal:controller.signal,credentials:'omit',headers:{Accept:'application/json'}})
    allowFallback=response.status>=500
    if(!response.ok)throw Error(response.status===404?'This statistical release is not available.':'Stats could not load. Please try again.')
    const data=await response.json() as T
    if(active){saveStatsSnapshot(path,data);setState({path,data,error:'',offlineAt:null})}
   }catch(error){
    if(!active)return
    const cached=allowFallback?readStatsSnapshot<T>(path):null
    setState({path,data:cached?.data??null,error:cached?'':controller.signal.aborted?'The Stats request timed out. Please try again.':error instanceof Error?error.message:'Stats could not load.',offlineAt:cached?.savedAt??null})
   }finally{clearTimeout(timer)}
  })()
  return()=>{active=false;clearTimeout(timer);controller.abort()}
 },[path,retry])
 return {data:state.path===path?state.data:null,error:state.path===path?state.error:'',offlineAt:state.path===path?state.offlineAt:null,retry:()=>setRetry(n=>n+1)}
}
