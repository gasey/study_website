import {useEffect,useRef,useState} from 'react'
import {getDocument,GlobalWorkerOptions,version,type PDFDocumentProxy} from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
GlobalWorkerOptions.workerSrc=workerUrl
const CONTROL='min-h-11 rounded-[6px] border border-hairline bg-card px-3 py-2 text-[12px] disabled:opacity-40'

/** Lazy, same-origin PDF rendering; no browser PDF plug-in or third-party upload. */
export default function PaperPdf({url,questionPage,questionId}:{url:string;questionPage:number|null;questionId:string}){
 const [document,setDocument]=useState<PDFDocumentProxy|null>(null)
 const [page,setPage]=useState(questionPage||1),[draft,setDraft]=useState(String(questionPage||1))
 const [zoom,setZoom]=useState(1),[width,setWidth]=useState(500)
 const [error,setError]=useState(''),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0)
 const host=useRef<HTMLDivElement>(null),frame=useRef<HTMLDivElement>(null)
 useEffect(()=>{setPage(questionPage||1);setDraft(String(questionPage||1))},[questionPage,questionId])
 useEffect(()=>{
  let live=true;setDocument(null);setError('');setLoading(true)
  const base='/vendor/pdfjs/'+version+'/'
  const task=getDocument({url:url.split('#')[0],cMapUrl:base+'cmaps/',cMapPacked:true,standardFontDataUrl:base+'standard_fonts/',wasmUrl:base+'wasm/',isEvalSupported:false})
  task.promise.then(doc=>{if(live)setDocument(doc)}).catch(e=>{if(live){setError(e.message||'The PDF could not load.');setLoading(false)}})
  return()=>{live=false;void task.destroy()}
 },[url,retry])
 useEffect(()=>{
  if(!frame.current)return
  const observer=new ResizeObserver(entries=>setWidth(Math.max(180,Math.floor(entries[0].contentRect.width)-16)))
  observer.observe(frame.current);return()=>observer.disconnect()
 },[])
 useEffect(()=>{
  if(!document||!host.current)return
  let live=true;let cancel:(()=>void)|undefined
  host.current.replaceChildren();setError('');setLoading(true)
  const actual=Math.max(1,Math.min(page,document.numPages))
  document.getPage(actual).then(async pdfPage=>{
   if(!live)return
   const natural=pdfPage.getViewport({scale:1}),viewport=pdfPage.getViewport({scale:width/natural.width*zoom})
   const output=Math.min(window.devicePixelRatio||1,2,4096/viewport.width,Math.sqrt(12000000/(viewport.width*viewport.height)))
   const canvas=window.document.createElement('canvas'),context=canvas.getContext('2d')
   if(!context)throw new Error('Canvas rendering is unavailable in this browser.')
   canvas.width=Math.floor(viewport.width*output);canvas.height=Math.floor(viewport.height*output)
   canvas.style.width=Math.floor(viewport.width)+'px';canvas.style.height=Math.floor(viewport.height)+'px'
   canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Original PDF page '+actual+'. The question transcript is alongside this preview.')
   const task=pdfPage.render({canvas,canvasContext:context,viewport,transform:output===1?undefined:[output,0,0,output,0,0]})
   cancel=()=>task.cancel();await task.promise
   if(live){host.current?.replaceChildren(canvas);setLoading(false)}
  }).catch(e=>{if(live&&e.name!=='RenderingCancelledException'){setError(e.message||'This page could not render.');setLoading(false)}})
  return()=>{live=false;cancel?.()}
 },[document,page,zoom,width])
 const actual=document?Math.max(1,Math.min(page,document.numPages)):page
 function turn(next:number){setPage(next);setDraft(String(next))}
 return <div>
  <div className="mb-2 flex flex-wrap items-center gap-2"><button type="button" aria-label="Previous PDF page" disabled={!document||actual<=1} onClick={()=>turn(actual-1)} className={CONTROL}>←</button><form onSubmit={e=>{e.preventDefault();const next=Number(draft);if(document&&Number.isInteger(next)&&next>=1&&next<=document.numPages)turn(next)}} className="flex items-center gap-2"><label className="text-[12px]">Page <input aria-label="PDF page number" type="number" min={1} max={document?.numPages||1} required value={draft} onChange={e=>setDraft(e.target.value)} className={CONTROL+' w-16'}/></label><span className="text-[12px]">/ {document?.numPages||'…'}</span><button disabled={!document} className={CONTROL}>Go</button></form><button type="button" aria-label="Next PDF page" disabled={!document||actual>=document.numPages} onClick={()=>turn(actual+1)} className={CONTROL}>→</button><label className="text-[12px]">Zoom <select aria-label="PDF zoom" value={zoom} onChange={e=>setZoom(Number(e.target.value))} className={CONTROL}><option value={1}>Fit width</option><option value={1.5}>150%</option><option value={2}>200%</option></select></label></div>
  {questionPage&&actual!==questionPage&&<button type="button" onClick={()=>turn(questionPage)} className="mb-2 min-h-11 text-[12px] text-link underline">Return to question page {questionPage}</button>}
  {document&&page>document.numPages&&<p role="alert" className="mb-2 text-[12px] text-mypick">The recorded page is beyond this PDF’s {document.numPages} pages. Showing its last page; check the source mapping.</p>}
  {error&&<p role="alert" className="mb-2 text-[12px] text-mypick">{error} <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 underline">Retry PDF</button></p>}
  <div ref={frame} aria-busy={loading} className="max-h-[65vh] min-h-40 overflow-auto rounded-[8px] border border-hairline bg-[#dedbd4] p-2">
   {loading&&<p role="status" className="p-4 text-[13px]">Rendering original PDF page…</p>}
   <div ref={host}/>
  </div>
 </div>
}
