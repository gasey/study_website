import {useEffect,useRef,useState} from 'react'
import {createPortal} from 'react-dom'
import {Link,useLocation,useNavigate} from 'react-router-dom'
import {isLaterExamCollection,listCollections,type Collection} from '../lib/api'
import {matchDestinations,quickDestinations} from '../lib/quickAccess'
import type {ReviewAccess} from '../lib/reviewNavigation'
import {useExamScope} from '../lib/examScope'
import NavIcon from './NavIcon'

export default function QuickFind({access,admin=false}:{access:ReviewAccess;admin?:boolean}){
 const dialog=useRef<HTMLDialogElement>(null),input=useRef<HTMLInputElement>(null)
 const [open,setOpen]=useState(false),[query,setQuery]=useState(''),[exams,setExams]=useState<Collection[]>([]),[loading,setLoading]=useState(false),[error,setError]=useState(false),[retry,setRetry]=useState(0)
 const location=useLocation(),navigate=useNavigate(),scope=useExamScope()
 useEffect(()=>{const key=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'&&!e.repeat){e.preventDefault();setOpen(value=>!value)}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key)},[])
 useEffect(()=>{setOpen(false);setQuery('')},[location.key])
 useEffect(()=>{if(!open)return;let live=true;setLoading(true);setError(false);setExams([]);listCollections().then(rows=>{if(live)setExams(rows.filter(e=>e.kind==='exam'&&!isLaterExamCollection(e)))}).catch(()=>{if(live)setError(true)}).finally(()=>{if(live)setLoading(false)});return()=>{live=false}},[open,scope,retry])
 useEffect(()=>{if(!open){dialog.current?.close();return}dialog.current?.showModal();input.current?.focus();const previous=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=previous}},[open])
 const results=matchDestinations(quickDestinations(exams,access),query)
 function close(){setOpen(false);setQuery('')}
 return <>
  <button type="button" onClick={()=>setOpen(true)} aria-label="Quick find" aria-haspopup="dialog" className={'inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-lg px-2 text-[13px] '+(admin?'w-full bg-[#3A3631] text-white':'hover:bg-canvas')}><NavIcon name="search"/><span className={admin?undefined:"hidden min-[360px]:inline"}>Find</span><kbd className="hidden rounded border border-current/20 px-1 text-[10px] opacity-60 xl:inline">Ctrl K</kbd></button>
  {createPortal(<dialog ref={dialog} aria-labelledby="quick-find-title" onCancel={close} onClose={close} onClick={e=>{if(e.target===dialog.current)close()}} className="quick-find-dialog rounded-[14px] border border-hairline bg-card p-0 text-ink shadow-xl">
   <div className="flex max-h-[min(640px,85dvh)] flex-col" onKeyDown={e=>{
    if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return
    const links=Array.from(dialog.current?.querySelectorAll<HTMLAnchorElement>('[data-quick-result]')||[])
    if(!links.length)return;e.preventDefault();const index=links.indexOf(document.activeElement as HTMLAnchorElement)
    if(e.key==='ArrowUp'&&index===0){input.current?.focus();return}
    links[e.key==='ArrowDown'?(index+1)%links.length:index<0?links.length-1:index-1]?.focus()
   }}>
    <div className="flex items-center justify-between border-b border-hairline px-4 py-2"><h2 id="quick-find-title" className="font-display text-[24px]">Quick find</h2><button type="button" onClick={close} className="min-h-11 px-2 text-sm text-secondary">Close</button></div>
    <form className="flex gap-2 p-4" onSubmit={e=>{e.preventDefault();if(query.trim()){navigate('/search?'+new URLSearchParams({q:query.trim()}));close()}}}>
     <input ref={input} type="search" aria-label="Find an exam or tool" placeholder="Exam, practice, PDF, revision…" maxLength={120} value={query} onChange={e=>setQuery(e.target.value)} className="min-h-12 min-w-0 flex-1 rounded-lg border border-hairline bg-canvas px-3 text-base"/>
     {query.trim()&&<button type="submit" className="min-h-12 rounded-lg bg-ink px-3 text-[13px] font-semibold text-paper">Search all</button>}
    </form>
    <div className="min-h-0 overflow-y-auto overscroll-contain px-2 pb-3">
     <p role="status" className="px-3 pb-2 text-xs text-secondary">{results.length} shortcuts{loading?' · Loading exams…':''}</p>
     {error&&<p className="px-3 text-xs text-secondary">Exams couldn’t load. <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 underline">Retry</button></p>}
     {!results.length&&<p className="px-3 py-4 text-sm text-secondary">No matching shortcut. Use Search all to look for questions and resources.</p>}
     {results.map((item,index)=><div key={item.to}>{item.group!==results[index-1]?.group&&<p className="px-3 pb-1 pt-3 font-mono text-[10px] uppercase tracking-widest text-muted">{item.group}</p>}<Link data-quick-result to={item.to} onClick={close} className="flex min-h-11 items-center justify-between gap-3 rounded-lg px-3 py-2 hover:bg-canvas focus:bg-canvas"><span className="min-w-0"><span className="block text-[14px] font-semibold">{item.label}</span><span className="block text-[12px] text-secondary">{item.detail}</span></span><span aria-hidden="true">→</span></Link></div>)}
    </div>
   </div>
  </dialog>,document.body)}
 </>
}
