/** One compact row: direct page jumps on desktop, Previous/Next on mobile. */
export default function Pagination({page,pages,onPageChange,disabled=false,label='Pages'}:{page:number;pages:number;onPageChange:(page:number)=>void;disabled?:boolean;label?:string}){
  const count=Math.max(1,Math.floor(pages)),current=Math.min(count,Math.max(1,Math.floor(page)))
  if(count<2)return null
  const candidates=count<=7?Array.from({length:count},(_,i)=>i+1):current<=4?[1,2,3,4,5,count]:current>=count-3?[1,count-4,count-3,count-2,count-1,count]:[1,current-1,current,current+1,count]
  const numbers=Array.from(new Set(candidates)).sort((a,b)=>a-b)
  const button='inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-pill border border-hairline bg-card px-3 text-[13px] font-semibold text-ink transition-colors hover:border-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-link focus-visible:ring-offset-2 disabled:cursor-default disabled:opacity-40'
  return <nav aria-label={label} className="mt-5 flex min-w-0 items-center justify-between gap-2 border-t border-hairline pt-4">
    <button type="button" className={button} disabled={disabled||current===1} onClick={()=>onPageChange(current-1)} aria-label="Previous page">← <span className="ml-1">Previous</span></button>
    <span className="whitespace-nowrap font-mono text-[11px] text-muted sm:hidden" aria-live="polite">{current.toLocaleString('en-IN')} / {count.toLocaleString('en-IN')}</span>
    <div className="hidden items-center gap-1 sm:flex">{numbers.map((n,i)=><span key={n} className="inline-flex items-center gap-1">{i>0&&n>numbers[i-1]+1&&<span aria-hidden="true" className="px-1 text-muted">…</span>}<button type="button" aria-label={`Page ${n}`} aria-current={n===current?'page':undefined} disabled={disabled||n===current} onClick={()=>onPageChange(n)} className={button+(n===current?' !border-ink !bg-ink !text-paper disabled:!opacity-100':'')}>{n.toLocaleString('en-IN')}</button></span>)}</div>
    <button type="button" className={button} disabled={disabled||current===count} onClick={()=>onPageChange(current+1)} aria-label="Next page"><span className="mr-1">Next</span> →</button>
  </nav>
}
