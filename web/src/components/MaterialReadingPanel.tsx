import {lazy,Suspense,useCallback,useEffect,useRef} from 'react'
import {Link,useLocation,useNavigate} from 'react-router-dom'
import {RouteErrorBoundary} from './RouteWorkspace'
const Reader=lazy(()=>import('../screens/Materials').then(m=>({default:m.MaterialReaderContent})))

/** Keep the originating list, filters and scroll mounted while reading. */
export default function MaterialReadingPanel(){
  const location=useLocation(),navigate=useNavigate()
  const params=new URLSearchParams(location.search),id=params.get('read_material')||''
  const preview=params.get('material_preview')==='true'
  const dialog=useRef<HTMLDialogElement>(null)
  const close=useCallback(()=>{
    const remaining=new URLSearchParams(location.search)
    remaining.delete('read_material');remaining.delete('material_preview')
    const target=location.pathname+(remaining.size?'?'+remaining:'')+location.hash
    if(location.state?.materialReaderFrom===target)navigate(-1)
    else navigate(target,{replace:true,state:null,preventScrollReset:true})
  },[location,navigate])
  useEffect(()=>{
    if(!id)return
    const element=dialog.current,previousOverflow=document.body.style.overflow
    const previouslyFocused=document.activeElement instanceof HTMLElement?document.activeElement:null
    element?.showModal();document.body.style.overflow='hidden'
    return()=>{element?.close();document.body.style.overflow=previousOverflow;if(previouslyFocused?.isConnected)previouslyFocused.focus({preventScroll:true})}
  },[id])
  if(!id)return null
  return <dialog ref={dialog} aria-labelledby="material-panel-heading" onCancel={event=>{event.preventDefault();close()}} onClick={event=>{if(event.target===event.currentTarget)close()}} className="fixed inset-0 m-auto h-[92dvh] max-h-[100dvh] w-[min(1100px,100%)] max-w-full overflow-y-auto overscroll-contain rounded-[14px] border border-hairline bg-canvas p-0 text-ink shadow-2xl backdrop:bg-black/40">
    <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-2 border-b border-hairline bg-canvas px-5 py-3">
      <h2 id="material-panel-heading" className="text-[14px] font-semibold">Reading material · your place is kept</h2>
      <div className="flex items-center gap-3"><Link to={'/materials/'+encodeURIComponent(id)+(preview?'?preview=true':'')} className="inline-flex min-h-11 items-center text-[12px] text-link underline">Open full page</Link><button autoFocus type="button" onClick={close} className="min-h-11 rounded-pill border border-ink px-4 text-[13px] font-semibold">Close reader</button></div>
    </header>
    <RouteErrorBoundary key={id+String(preview)}><Suspense fallback={<p role="status" className="p-6 text-secondary">Loading material…</p>}><Reader key={id+String(preview)} id={id} preview={preview} embedded/></Suspense></RouteErrorBoundary>
  </dialog>
}
