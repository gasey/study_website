export function pageNumber(value:string|null,maximum=4001){
  if(!value||!/^\d{1,6}$/.test(value))return 1
  return Math.min(maximum,Math.max(1,Number(value)))
}
export function scrollToResults(id:string){
  const target=document.getElementById(id)
  if(!target)return
  if(!target.hasAttribute('tabindex'))target.setAttribute('tabindex','-1')
  target.focus({preventScroll:true})
  const header=document.querySelector('header')
  const box=header?.getBoundingClientRect()
  const sticky=header&&['sticky','fixed'].includes(getComputedStyle(header).position)
  const inset=sticky&&box&&box.top<=0?box.bottom:0
  window.scrollTo({top:Math.max(0,window.scrollY+target.getBoundingClientRect().top-inset-16),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})
}

/** Hash targets may arrive after a lazy view or exam header. */
export function focusWhenAvailable(id:string){
  let frame=0
  const focus=()=>{if(!document.getElementById(id))return false;frame=requestAnimationFrame(()=>scrollToResults(id));return true}
  if(focus())return()=>cancelAnimationFrame(frame)
  const observer=new MutationObserver(()=>{if(focus())observer.disconnect()})
  observer.observe(document.body,{childList:true,subtree:true})
  const timer=window.setTimeout(()=>observer.disconnect(),10000)
  return()=>{observer.disconnect();window.clearTimeout(timer);cancelAnimationFrame(frame)}
}
