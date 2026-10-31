import {useSyncExternalStore,type ReactNode} from 'react'
const KEY='ism:answer-layout:v1',EVENT='ism-answer-layout'
type Layout='grid'|'list'
let fallback:Layout='grid'
function snapshot():Layout{try{const stored=localStorage.getItem(KEY);return stored==='list'?'list':stored==='grid'?'grid':fallback}catch{return fallback}}
function subscribe(callback:()=>void){window.addEventListener(EVENT,callback);window.addEventListener('storage',callback);return()=>{window.removeEventListener(EVENT,callback);window.removeEventListener('storage',callback)}}
function useLayout(){return useSyncExternalStore(subscribe,snapshot,()=> 'grid' as Layout)}
export function AnswerLayoutControl(){const layout=useLayout();return <div role="group" aria-label="Answer layout" className="my-3 flex flex-wrap items-center gap-2 text-[12px]"><span className="mr-1 text-secondary">Answer layout</span>{([['grid','2×2'],['list','List']] as const).map(([value,label])=><button key={value} type="button" aria-pressed={layout===value} onClick={()=>{fallback=value;try{localStorage.setItem(KEY,value)}catch{/* Keep the choice in this session when persistent storage is blocked. */}window.dispatchEvent(new Event(EVENT))}} className={'min-h-11 rounded-[8px] border px-3 py-2 font-semibold '+(layout===value?'border-ink bg-ink text-paper':'border-hairline bg-card text-ink')}>{label}</button>)}<span className="text-[11px] text-muted">Single column on small screens</span></div>}
export function AnswerOptions({children,className='',as='div'}:{children:ReactNode;className?:string;as?:'div'|'ol'}){const layout=useLayout();const Tag=as;return <Tag className={'answer-options '+className} data-layout={layout}>{children}</Tag>}
