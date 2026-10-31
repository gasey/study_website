import {Component,useLayoutEffect,type ReactNode} from 'react'
import {useLocation,useNavigationType} from 'react-router-dom'
const positions=new Map<string,number>()
let previousPath:string|null=null
export function RouteNavigation(){
  const {key,pathname,hash}=useLocation(),navigation=useNavigationType()
  useLayoutEffect(()=>{
    const previous=history.scrollRestoration;history.scrollRestoration='manual'
    const wanted=positions.get(key)||0
    let restoring=navigation==='POP',observer:ResizeObserver|MutationObserver|null=null,timer:number|undefined
    const save=()=>{if(restoring)return;positions.set(key,window.scrollY);while(positions.size>100)positions.delete(positions.keys().next().value!)}
    const stop=()=>{observer?.disconnect();observer=null;if(timer!==undefined)clearTimeout(timer);restoring=false}
    const cancel=()=>{stop();save()}
    const restore=()=>{
      if(hash){
        let id='';try{id=decodeURIComponent(hash.slice(1))}catch{/* malformed hash */}
        const find=()=>{const target=document.getElementById(id);if(!target)return false;target.scrollIntoView();stop();save();return true}
        if(id&&!find()){restoring=true;observer=new MutationObserver(find);observer.observe(document.body,{subtree:true,childList:true});timer=window.setTimeout(cancel,8000)}else restoring=false
      }else if(navigation==='POP'){
        const attempt=()=>{if(Math.max(0,document.documentElement.scrollHeight-window.innerHeight)<wanted)return;window.scrollTo(0,wanted);stop();save()}
        if(Math.max(0,document.documentElement.scrollHeight-window.innerHeight)>=wanted){window.scrollTo(0,wanted);stop()}
        else{restoring=true;observer=new ResizeObserver(attempt);observer.observe(document.body);timer=window.setTimeout(cancel,8000)}
      }else{restoring=false;if(previousPath!==pathname)window.scrollTo(0,0)}
      previousPath=pathname;save()
    }
    const frame=requestAnimationFrame(restore)
    window.addEventListener('scroll',save,{passive:true});window.addEventListener('pagehide',save)
    for(const event of ['wheel','touchstart','keydown'])window.addEventListener(event,cancel,{passive:true})
    return()=>{cancelAnimationFrame(frame);stop();window.removeEventListener('scroll',save);window.removeEventListener('pagehide',save);for(const event of ['wheel','touchstart','keydown'])window.removeEventListener(event,cancel);history.scrollRestoration=previous}
  },[key,pathname,hash,navigation])
  return null
}

export function WorkspaceLoading(){return <div role="status" aria-live="polite" className="mx-auto min-h-[60vh] max-w-shell px-6 py-10"><p className="text-[14px] text-secondary">Opening workspace…</p><div aria-hidden="true" className="mt-5 space-y-4 motion-safe:animate-pulse"><div className="h-8 max-w-sm rounded bg-paper"/><div className="h-4 max-w-xl rounded bg-paper"/><div className="h-44 rounded-[14px] border border-hairline bg-card"/></div></div>}
export class RouteErrorBoundary extends Component<{children:ReactNode},{failed:boolean}>{
  state={failed:false}
  static getDerivedStateFromError(){return {failed:true}}
  render(){return this.state.failed?<section role="alert" className="mx-auto min-h-[50vh] max-w-shell p-8"><h1 className="font-display text-[30px]">This workspace couldn’t open</h1><p className="mt-3 text-secondary">Check your connection, then reload this page. Previously saved progress is kept.</p><button className="mt-5 min-h-[44px] rounded-pill bg-ink px-5 text-paper" onClick={()=>window.location.reload()}>Reload this page</button><a className="ml-4 text-link underline" href="/">Home</a></section>:this.props.children}
}
