/** Bounded in-memory request coalescing. Callers choose the permitted data,
 * cache scope and lifetime; this class never writes browser storage. */
export class ReadRequestCache {
  private entries = new Map<string,{promise:Promise<unknown>;expires:number}>()
  constructor(private limit=64,private now=()=>Date.now()){}
  clear(){this.entries.clear()}
  read<T>(key:string,loader:()=>Promise<T>,ttl=0):Promise<T>{
    const existing=this.entries.get(key)
    if(existing&&existing.expires>this.now())return existing.promise as Promise<T>
    const entry={promise:Promise.resolve().then(loader) as Promise<unknown>,expires:Infinity}
    this.entries.set(key,entry)
    while(this.entries.size>this.limit)this.entries.delete(this.entries.keys().next().value!)
    entry.promise.then(()=>{if(this.entries.get(key)!==entry)return;if(ttl>0)entry.expires=this.now()+ttl;else this.entries.delete(key)},()=>{if(this.entries.get(key)===entry)this.entries.delete(key)})
    return entry.promise as Promise<T>
  }
}
export const catalogTtl=(path:string)=>/^\/(?:questions\/taxonomy|collections|library\/shelves(?:\/[^/?]+)?)(?:\?|$)/.test(path)?30000:0

/** Equivalent default filters must share visible/prefetch requests. */
export function questionQueryString(params:Record<string,unknown>){
  const qs=new URLSearchParams()
  for(const [key,value] of Object.entries(params)){
    if(value===undefined||value===null||value===''||value===false)continue
    if((key==='pool'&&value==='all')||(key==='study_status'&&value==='all')||(key==='origin'&&value==='paper')||(key==='offset'&&value===0))continue
    if(Array.isArray(value))value.forEach(item=>qs.append(key,String(item)))
    else qs.set(key,String(value))
  }
  qs.sort();return qs.toString()
}
