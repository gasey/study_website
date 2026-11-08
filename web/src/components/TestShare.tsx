import {useState} from 'react'
import {sharedTestUrl,testInvitation,testWhatsAppUrl} from '../lib/sharedTests'
export default function TestShare({id,title}:{id:string;title:string}){
 const [notice,setNotice]=useState(''),[fallback,setFallback]=useState(false)
 const style='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 py-2 text-[13px] font-semibold'
 async function copy(){try{await navigator.clipboard.writeText(sharedTestUrl(id));setNotice('Test link copied.')}catch{setFallback(true);setNotice('Copy the link below.')}}
 async function share(){try{await navigator.share({title,text:testInvitation(id,title).split('\n').slice(0,-1).join('\n'),url:sharedTestUrl(id)})}catch(e){if((e as Error).name!=='AbortError')setNotice('Sharing could not open. Copy the link or use WhatsApp.')}}
 return <section aria-label="Share this test" className="mt-5"><div className="flex flex-wrap gap-2"><button type="button" className={style} onClick={()=>void copy()}>Copy test link</button><a className={style} href={testWhatsAppUrl(id,title)} target="_blank" rel="noreferrer">Share on WhatsApp ↗</a>{typeof navigator.share==='function'&&<button type="button" className={style} onClick={()=>void share()}>More sharing options</button>}</div>{notice&&<p role="status" className="mt-2 text-[13px] text-secondary">{notice}</p>}{fallback&&<label className="mt-2 block text-sm">Test link<input readOnly className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-hairline p-2" value={sharedTestUrl(id)} onFocus={e=>e.target.select()}/></label>}<p className="mt-2 text-[12px] text-secondary">You choose where to send it. Your private answers and result are not included.</p></section>
}
