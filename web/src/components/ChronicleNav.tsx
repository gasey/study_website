import {useEffect,useRef,useState,type ReactNode} from 'react'
import {Link} from 'react-router-dom'

export type ChronicleTab='timeline'|'chronology'|'list'|'calendar'

interface ChronicleNavProps{
 active:ChronicleTab
 onSelectMode?:(mode:'list'|'chronology'|'calendar')=>void
}

const ICONS:Record<ChronicleTab,ReactNode>={
 timeline:<svg className="finna-chrono-nav-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M2 9h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/><circle cx="5" cy="9" r="2.2" fill="currentColor"/><circle cx="13" cy="9" r="2.2" fill="currentColor"/><path d="M5 6.8V4.2M13 11.2v2.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
 chronology:<svg className="finna-chrono-nav-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M5 3.5v11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/><circle cx="5" cy="4.5" r="1.8" fill="currentColor"/><circle cx="5" cy="9" r="1.8" fill="currentColor"/><circle cx="5" cy="13.5" r="1.8" fill="currentColor"/><path d="M8.5 4.5h6M8.5 9h5M8.5 13.5h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>,
 list:<svg className="finna-chrono-nav-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3 5h12M3 9h12M3 13h8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>,
 calendar:<svg className="finna-chrono-nav-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true"><rect x="2.5" y="3.5" width="13" height="12" rx="2.5" stroke="currentColor" strokeWidth="1.5"/><path d="M2.5 7.5h13M6 2v2.5M12 2v2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
}

const ITEMS:{id:ChronicleTab;label:string;to:string}[]=[
 {id:'timeline',label:'Timeline',to:'/chronicle'},
 {id:'chronology',label:'Chronology',to:'/chronicle?view=chronology'},
 {id:'list',label:'List',to:'/chronicle?view=list'},
 {id:'calendar',label:'Calendar',to:'/chronicle?view=calendar'},
]

export default function ChronicleNav({active,onSelectMode}:ChronicleNavProps){
 const railRef=useRef<HTMLDivElement>(null)
 const [pill,setPill]=useState<{left:number;width:number;height:number;top:number;ready:boolean}>({left:0,width:0,height:0,top:0,ready:false})
 const [hover,setHover]=useState<{left:number;width:number;height:number;top:number;visible:boolean}>({left:0,width:0,height:0,top:0,visible:false})
 const [animate,setAnimate]=useState(false)

 function measure(id:ChronicleTab){
  const rail=railRef.current
  if(!rail||typeof rail.querySelector!=='function')return null
  const el=rail.querySelector<HTMLElement>(`[data-chrono-tab="${id}"]`)
  if(!el||typeof el.offsetWidth!=='number'||el.offsetWidth===0)return null
  return {left:el.offsetLeft,top:el.offsetTop,width:el.offsetWidth,height:el.offsetHeight}
 }

 useEffect(()=>{
  const sync=()=>{
   const rect=measure(active)
   if(!rect)return
   setPill(prev=>{
    if(prev.ready)setAnimate(true)
    return {...rect,ready:true}
   })
  }
  sync()
  if(typeof window==='undefined')return
  window.addEventListener('resize',sync)
  let ro:ResizeObserver|null=null
  if(typeof ResizeObserver!=='undefined'&&railRef.current){
   ro=new ResizeObserver(sync)
   ro.observe(railRef.current)
  }
  return()=>{
   window.removeEventListener('resize',sync)
   ro?.disconnect()
  }
 },[active])

 function onEnter(id:ChronicleTab){
  const rect=measure(id)
  if(rect)setHover({...rect,visible:true})
 }

 return <nav aria-label="Chronicle views" className="finna-chrono-nav-wrap">
  <div ref={railRef} className={'finna-chrono-nav'+(pill.ready?' has-slider':'')+(animate?' is-animated':'')} onMouseLeave={()=>setHover(h=>({...h,visible:false}))}>
   <span aria-hidden="true" className={'finna-chrono-nav-hover'+(hover.visible?' is-visible':'')} style={{transform:`translate3d(${hover.left}px,${hover.top}px,0)`,width:hover.width,height:hover.height}}/>
   {pill.ready&&<span aria-hidden="true" className="finna-chrono-nav-slider" style={{transform:`translate3d(${pill.left}px,${pill.top}px,0)`,width:pill.width,height:pill.height}}/>}
   {ITEMS.map(item=>{
    const isActive=active===item.id
    const cls='finna-chrono-nav-item'+(isActive?' is-active':'')
    if(onSelectMode&&item.id!=='timeline'){
     const mode=item.id
     return <button key={item.id} data-chrono-tab={item.id} type="button" aria-pressed={isActive} onClick={()=>onSelectMode(mode)} onMouseEnter={()=>onEnter(item.id)} onFocus={()=>onEnter(item.id)} className={cls}>{ICONS[item.id]}<span>{item.label}</span></button>
    }
    return <Link key={item.id} data-chrono-tab={item.id} to={item.to} aria-current={isActive?'page':undefined} onMouseEnter={()=>onEnter(item.id)} onFocus={()=>onEnter(item.id)} className={cls}>{ICONS[item.id]}<span>{item.label}</span></Link>
   })}
  </div>
 </nav>
}
