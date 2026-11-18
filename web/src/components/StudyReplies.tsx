import {ContributorName,type ContributorTier} from './ContributorStanding'
import BlockAuthor from './BlockAuthor'
import PostEditing,{EditMarker,type EditablePost} from './PostEditing'
import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {useComposerDraft} from '../lib/useComposerDraft'
import CommunityText,{ComposerFormatting} from './CommunityText'
import DraftNotice from './DraftNotice'
import {UserAvatar} from './AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import {reviewRequest} from '../lib/review'
const BTN='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold disabled:opacity-50'
const INPUT='mt-2 w-full rounded-[6px] border border-hairline bg-paper p-3 text-[14px]'
interface Reply extends EditablePost {id:number;author_id:string;author_tier?:ContributorTier|null;author_profile_id?:string|null;body:string;author:string;avatar?:AvatarLook|null;created_at:string;is_author:boolean;needs_approval:boolean;helpful:number;voted:boolean}
interface Page {items:Reply[];has_more:boolean;registered:boolean;can_reply:boolean;replies_remaining:number;reply_limit:number}
export default function StudyReplies({id,onUnavailable}:{id:number;onUnavailable:(message:string)=>void}){
 const [open,setOpen]=useState(false),[page,setPage]=useState<Page|null>(null),[offset,setOffset]=useState(0),[reload,setReload]=useState(0),[version,setVersion]=useState(0),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[reporting,setReporting]=useState<number|null>(null),[reason,setReason]=useState('spam'),[reportNote,setReportNote]=useState('')
 const generation=useRef(0)
 const draft=useComposerDraft('reply:'+id,!!page?.registered),{body}=draft.fields
 const setBody=(body:string)=>draft.update({body})
 useEffect(()=>{const change=()=>{++generation.current;setOpen(false);setPage(null);setOffset(0);setBusy(false);setError('');setNotice('');setReporting(null);setReportNote('');setVersion(n=>n+1)};window.addEventListener('ism-auth-change',change);window.addEventListener('ism-auth-expired',change);window.addEventListener('ism-community-change',change);return()=>{++generation.current;window.removeEventListener('ism-auth-change',change);window.removeEventListener('ism-auth-expired',change);window.removeEventListener('ism-community-change',change)}},[])
 useEffect(()=>{if(!open)return;let active=true;const run=++generation.current;setLoading(true);if(offset===0)setPage(null)
  reviewRequest<Page>('/community/study-posts/'+id+'/replies?offset='+offset).then(result=>{if(active&&generation.current===run)setPage(previous=>offset===0||!previous?result:{...result,items:[...previous.items,...result.items.filter(item=>!previous.items.some(old=>old.id===item.id))]})}).catch(e=>{if(active&&generation.current===run){setPage(null);onUnavailable(e.message)}}).finally(()=>{if(active&&generation.current===run)setLoading(false)})
  return()=>{active=false;++generation.current}
 },[id,open,offset,reload,version])
 async function submit(e:React.FormEvent){e.preventDefault();const run=generation.current;setBusy(true);setError('');setNotice('')
  try{const serialized=JSON.stringify({body})
   const saved=await reviewRequest<{needs_approval:boolean}>('/community/study-posts/'+id+'/replies',{body},draft.requestKey(serialized))
   if(run!==generation.current)return
   draft.clear();setNotice(saved.needs_approval?'Reply saved · awaiting moderation, visible only to you.':'Reply posted.');setOffset(0);setReload(n=>n+1)
  }catch(e){if(run===generation.current){setError((e as Error).message);setOffset(0);setReload(n=>n+1)}}finally{if(run===generation.current)setBusy(false)}
 }
 async function action(rid:number,name:string,payload:unknown){const run=generation.current;setBusy(true);setError('');setNotice('')
  try{await reviewRequest('/community/study-posts/'+rid+'/'+name,payload);if(run!==generation.current)return;if(name==='helpful')window.dispatchEvent(new Event('ism-community-standing-change'));setReporting(null);setReportNote('');if(name==='report')setNotice('Reply report saved for moderation.');setOffset(0);setReload(n=>n+1)}catch(e){if(run===generation.current){setPage(null);onUnavailable((e as Error).message)}}finally{if(run===generation.current)setBusy(false)}
 }
 return <section aria-label="Conversation replies" className="mt-5 border-t border-hairline pt-4">
  {!open?<button className={BTN} onClick={()=>setOpen(true)}>Show replies</button>:<>
   <h3 className="font-display text-[23px]">Replies</h3>
   {loading&&<p role="status" className="mt-3 text-[13px] text-secondary">Loading replies…</p>}
   {error&&<p role="alert" className="mt-3 break-words text-[13px] text-mypick">{error}</p>}
   {notice&&<p role="status" className="mt-3 text-[13px] text-secondary">{notice}</p>}
   {page&&<>
    {!page.items.length&&<p className="mt-3 text-[14px] text-secondary">No visible replies yet. Share a helpful response.</p>}
    <div className="mt-3 grid gap-3">{page.items.map(reply=><article key={reply.id} className="min-w-0 rounded-panel border border-hairline bg-paper p-4">
     <div className="flex flex-wrap items-center gap-2 text-[13px]"><UserAvatar look={reply.avatar} initials={reply.author}/><ContributorName {...reply}/><span className="text-muted">{new Date(reply.created_at).toLocaleDateString('en-IN')}</span></div>
     {reply.needs_approval&&<p className="mt-2 text-[12px] text-secondary">Awaiting moderation · only you can see this reply.</p>}
     <EditMarker post={reply}/>{reply.is_author&&<PostEditing key={'edit:'+reply.id+':'+(reply.content_version||0)} post={reply} onSaved={()=>setReload(n=>n+1)}/>}<CommunityText body={reply.body} className="mt-3 text-[14px] leading-relaxed"/>
     <div className="mt-3 flex flex-wrap items-center gap-2 text-[13px]"><span>{reply.helpful} helpful</span>
      {page.registered&&!reply.is_author&&!reply.needs_approval&&<><button disabled={busy||loading} aria-pressed={reply.voted} className={BTN} onClick={()=>void action(reply.id,'helpful',{enabled:!reply.voted})}>Helpful reply</button><button disabled={busy||loading} className={BTN} onClick={()=>{setReporting(reply.id);setReportNote('')}}>Report reply</button></>}
      {page.registered&&!reply.is_author&&<BlockAuthor authorId={reply.author_id} disabled={busy||loading}/>}
      {reply.is_author&&<button disabled={busy||loading} className={BTN} onClick={()=>void action(reply.id,'withdraw',{})}>Withdraw reply</button>}
     </div>
     {reporting===reply.id&&<form className="mt-3" onSubmit={e=>{e.preventDefault();void action(reply.id,'report',{reason,note:reportNote})}}><label className="block text-[13px]">Reply conduct issue<select className={INPUT} value={reason} onChange={e=>setReason(e.target.value)}>{['spam','harassment','answer_leak','copyright','other'].map(r=><option key={r} value={r}>{r.replace('_',' ')}</option>)}</select></label><label className="mt-3 block text-[13px]">Reply report details<textarea required minLength={10} maxLength={2000} disabled={busy} className={INPUT} value={reportNote} onChange={e=>setReportNote(e.target.value)}/></label><button className={BTN+' mt-3'} disabled={busy||loading}>Send reply report</button></form>}
    </article>)}</div>
    {page.has_more&&<button disabled={busy||loading} className={BTN+' mt-3'} onClick={()=>setOffset(n=>n+20)}>Load more replies</button>}
    {page.registered?<><p className="mt-4 text-[12px] text-secondary">{page.replies_remaining} of {page.reply_limit} replies remaining today · resets at midnight IST. Replies follow the same moderation rules as posts.</p>
     {!page.can_reply&&<p className="mt-2 text-[13px] text-secondary">Replying is restricted while your account is under moderation.</p>}
     <form onSubmit={e=>void submit(e)} className="mt-3" aria-busy={busy}><label className="block text-[13px] font-semibold">Your reply<textarea required minLength={10} maxLength={5000} rows={3} className={INPUT} value={body} disabled={busy||loading} onChange={e=>setBody(e.target.value)}/></label><p className="mt-1 text-[12px] text-muted">{body.length}/5000 · Bold, lists and inline code · External links and uploads are unavailable.</p><ComposerFormatting body={body}/><DraftNotice status={draft.status} onDiscard={draft.clear} hasDraft={!!body}/><button disabled={busy||loading||!page.can_reply||page.replies_remaining===0} className={BTN+' mt-3 bg-ink text-paper'}>{busy?'Saving reply…':'Post reply'}</button></form>
    </>:<Link to="/login" className={BTN+' mt-4'}>Sign in to reply</Link>}
   </>}
  </>}
 </section>
}
