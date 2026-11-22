import {ContributorName,type ContributorTier} from './ContributorStanding'
import BlockAuthor,{CommunityFeedback} from './BlockAuthor'
import PostEditing,{EditMarker,type EditablePost} from './PostEditing'
import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {useComposerDraft} from '../lib/useComposerDraft'
import CommunityText,{ComposerFormatting} from './CommunityText'
import DraftNotice from './DraftNotice'
import StudyReplies from './StudyReplies'
import {UserAvatar} from './AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import {reviewRequest} from '../lib/review'
import {parseStudyReference,type StudyReference} from '../lib/communityPosts'

const BTN='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline px-4 py-2 text-sm font-semibold disabled:opacity-50'
const INPUT='mt-2 w-full rounded-[6px] border border-hairline bg-paper p-3 text-sm'
interface Policy {sanctioned?:boolean;registered:boolean;can_create:boolean;scored_attempts:number;old_enough:boolean;weighted_helpful:number;needs_approval:boolean;post_limit:number;posts_remaining:number;reply_limit:number;replies_remaining:number;subjects:{id:string;label:string}[]}
interface StudyPost extends EditablePost {id:number;author_id:string;author_tier?:ContributorTier|null;author_profile_id?:string|null;parent_id?:number|null;kind?:'study'|'material-share';body:string;author:string;avatar?:AvatarLook|null;created_at:string;is_author:boolean;needs_approval:boolean;topic_label:string|null;reference:StudyReference|null;registered:boolean;helpful:number;voted:boolean}
function useAccountVersion(){
 const generation=useRef(0),[version,setVersion]=useState(0)
 useEffect(()=>{const update=()=>{++generation.current;setVersion(n=>n+1)};window.addEventListener('ism-auth-change',update);window.addEventListener('ism-auth-expired',update);window.addEventListener('ism-community-change',update);return()=>{++generation.current;window.removeEventListener('ism-auth-change',update);window.removeEventListener('ism-auth-expired',update);window.removeEventListener('ism-community-change',update)}},[])
 return {generation,version}
}

export function StudyComposer({onSaved,onClose,kind='study'}:{kind?:'study'|'material-share';onSaved:(id:number)=>void;onClose:()=>void}) {
 const sharing=kind==='material-share'
 const [policy,setPolicy]=useState<Policy|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('')
 const {generation,version}=useAccountVersion()
 const draft=useComposerDraft('post:'+kind,!!policy?.registered),{body,subject,link}=draft.fields
 const setBody=(body:string)=>draft.update({body}),setSubject=(subject:string)=>draft.update({subject}),setLink=(link:string)=>draft.update({link})
 useEffect(()=>{let active=true;const run=++generation.current;setPolicy(null);setError('');setBusy(false);reviewRequest<Policy>('/community/study-posts/status').then(r=>{if(active&&generation.current===run)setPolicy(r)}).catch(e=>{if(active&&generation.current===run)setError(e.message)});return()=>{active=false}},[version,kind])
 async function submit(e:React.FormEvent){
  e.preventDefault();const run=generation.current;setBusy(true);setError('')
  try{
   const reference=parseStudyReference(link,window.location.origin)
   if(sharing&&reference?.kind!=='material')throw Error('Use a link to an already-published Finna material.')
   const payload={body,topic_tag:subject||null,reference,...(sharing?{kind}: {})},serialized=JSON.stringify(payload)
   const saved=await reviewRequest<{id:number}>('/community/study-posts',payload,draft.requestKey(serialized))
   if(run!==generation.current)return
   draft.clear();onSaved(saved.id)
  }catch(e){if(run===generation.current)setError((e as Error).message)}finally{if(run===generation.current)setBusy(false)}
 }
 return <section aria-label={sharing?"Share a reviewed material":"Write a study note"} className="mt-4 rounded-panel border border-hairline bg-card p-5">
  <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-display text-xl">{sharing?'Share a reviewed material':'Share a study note'}</h2><button type="button" className={BTN} onClick={onClose}>Close composer</button></div>
  <p className="mt-2 text-sm text-secondary">{sharing?'Link an already-reviewed publication and explain why it is useful. Its full content stays on the material page.':'A short tip, strategy or progress note. Share only what you want public.'} Helpful votes earn no points.</p>
  {!policy&&!error&&<p role="status" className="mt-3 text-secondary">Checking posting access…</p>}
  {error&&<p role="alert" className="mt-3 break-words text-sm text-mypick">{error}</p>}
  {policy&&!policy.registered&&<Link className={BTN+' mt-4'} to={'/login?next='+encodeURIComponent('/community?compose='+kind)}>{sharing?'Sign in to share a material':'Sign in to write a note'}</Link>}
  {policy?.registered&&<>
   <p className="mt-3 text-sm text-secondary">{policy.posts_remaining} of {policy.post_limit} posts remaining today · {policy.replies_remaining} of {policy.reply_limit} replies remaining · resets at midnight IST.</p>
   {!policy.can_create&&<p role="status" className="mt-3 rounded-[8px] bg-community-soft p-3 text-sm">{policy.sanctioned?'Posting is restricted while your account is under moderation.':<>Study notes open after 3 days and 50 scored attempts, or Helper standing without a moderation restriction. You have {policy.scored_attempts>=50?'50+':policy.scored_attempts} scored attempts. You can still ask a doubt on a question you have unlocked.</>}</p>}
   <form onSubmit={e=>void submit(e)} className="mt-4" aria-busy={busy}>
    <label className="block text-sm font-semibold">{sharing?'Why this material is useful':'Your study note'}<textarea required minLength={10} maxLength={5000} rows={5} disabled={busy} value={body} onChange={e=>setBody(e.target.value)} className={INPUT}/></label>
    <p className="mt-1 text-xs text-muted">{body.length}/5000 · Bold, lists and inline code · Use the linked item below for a Finna link. External links and uploads are unavailable.</p>
    <ComposerFormatting body={body}/><DraftNotice status={draft.status} onDiscard={draft.clear} hasDraft={!!(body||subject||link)}/>
    <label className="mt-3 block text-sm font-semibold">Subject · optional<select disabled={busy} value={subject} onChange={e=>setSubject(e.target.value)} className={INPUT}><option value="">General study</option>{policy.subjects.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select></label>
    <label className="mt-3 block text-sm font-semibold">{sharing?'Published material link · required':'Finna item link · optional'}<input required={sharing} disabled={busy} maxLength={2000} value={link} onChange={e=>setLink(e.target.value)} className={INPUT} placeholder={sharing?'/materials/…':'Question, material, original paper or exam link'}/></label>
    <p className="mt-2 text-xs text-secondary">{sharing?<>Only published materials can be shared. Blocks, withdrawal and content access still apply. <Link to="/materials" className="font-semibold text-link">Find a reviewed material →</Link></>:'A linked question keeps this note hidden until the reader checks or shows its answer. Active tests and games stay protected.'}{policy.needs_approval?' Your note will wait for review and be visible only to you.':''}</p>
    <div className="mt-4 flex flex-wrap gap-3"><button disabled={busy||!policy.can_create||policy.posts_remaining===0} className={BTN+' bg-ink text-paper'}>{busy?'Saving…':sharing?'Share material':'Post study note'}</button><Link className={BTN} to="/bank">{policy.sanctioned?'Browse questions':'Ask a doubt on a question'}</Link></div>
   </form>
  </>}
 </section>
}

export function StudyPostDetail({id,onClose}:{id:number;onClose:()=>void}) {
 const [post,setPost]=useState<StudyPost|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[reload,setReload]=useState(0),[report,setReport]=useState(false),[reason,setReason]=useState('spam'),[note,setNote]=useState(''),[notice,setNotice]=useState('')
 const {generation,version}=useAccountVersion()
 const sharing=post?.kind==='material-share'
 useEffect(()=>{let active=true;const run=++generation.current;setPost(null);setError('');setNotice('');setReport(false);setNote('');setBusy(false);reviewRequest<StudyPost>('/community/study-posts/'+id).then(r=>{if(active&&generation.current===run)setPost(r)}).catch(e=>{if(active&&generation.current===run)setError(e.message)});return()=>{active=false;++generation.current}},[id,version,reload])
 async function change(action:string,body:unknown){
  const run=generation.current;setBusy(true);setError('')
  try{await reviewRequest('/community/study-posts/'+id+'/'+action,body);if(run!==generation.current)return;if(action==='helpful')window.dispatchEvent(new Event('ism-community-standing-change'));if(action==='withdraw'){onClose();return}if(action==='report'){setNotice('Report saved for moderation.');setReport(false);setNote('')}else setReload(n=>n+1)}catch(e){if(run===generation.current){setPost(null);setError((e as Error).message)}}finally{if(run===generation.current)setBusy(false)}
 }
 return <section aria-label="Study note" className="mt-4 min-w-0 rounded-panel border border-hairline bg-card p-5">
  <button type="button" className={BTN} onClick={onClose}>Back to community</button>
  <CommunityFeedback/>
  {!post&&!error&&<p role="status" className="mt-4 text-secondary">Loading study note…</p>}
  {error&&<p role="alert" className="mt-3 break-words text-sm text-mypick">{error}</p>}
  {post&&<article className="mt-4 min-w-0"><div className="flex flex-wrap items-center gap-2 text-sm"><UserAvatar look={post.avatar} initials={post.author}/><ContributorName {...post}/><span className="rounded-pill bg-community-soft px-3 py-1 text-community-dark">{sharing?'Material share':'Study note'}</span><span className="text-muted">{new Date(post.created_at).toLocaleDateString('en-IN')}</span></div>
   {post.needs_approval&&<p role="status" className="mt-3 rounded-[8px] bg-community-soft p-3 text-sm">Awaiting moderation · only you can see this post.</p>}
   {post.topic_label&&<p className="mt-3 font-mono text-xs text-secondary">{post.topic_label}</p>}
   <EditMarker post={post}/><CommunityText body={post.body} className="mt-4 text-base leading-relaxed"/>
   {post.is_author&&<PostEditing key={'edit:'+post.id+':'+(post.content_version||0)} post={post} onSaved={()=>setReload(n=>n+1)}/>}
   {post.reference?.url&&<Link reloadDocument={post.reference.kind==='paper'} to={post.reference.url} className="mt-4 block min-w-0 break-words rounded-[8px] border border-hairline bg-paper p-4 text-sm font-semibold text-link">{post.reference.label} →{sharing&&<span className="mt-2 block text-xs font-normal text-secondary">Reviewed material · Open the material page for access and reading</span>}</Link>}
   <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-hairline pt-3"><span className="text-sm text-secondary">{post.helpful} helpful</span>
    {post.registered&&!post.is_author&&!post.needs_approval&&<><button disabled={busy} aria-pressed={post.voted} className={BTN} onClick={()=>void change('helpful',{enabled:!post.voted})}>Helpful</button><button disabled={busy} className={BTN} onClick={()=>setReport(!report)}>{sharing?'Report share':'Report note'}</button></>}
    {post.registered&&!post.is_author&&<BlockAuthor authorId={post.author_id} disabled={busy}/>}
    {post.is_author&&<button disabled={busy} className={BTN} onClick={()=>void change('withdraw',{})}>{sharing?'Withdraw share':'Withdraw note'}</button>}
    {!post.registered&&<Link to="/login" className={BTN}>Sign in to vote or report</Link>}
   </div>
   {report&&<form className="mt-4" onSubmit={e=>{e.preventDefault();void change('report',{reason,note})}}><label className="block text-sm">Conduct issue<select value={reason} onChange={e=>setReason(e.target.value)} className={INPUT}>{['spam','harassment','answer_leak','copyright','other'].map(r=><option key={r} value={r}>{r.replace('_',' ')}</option>)}</select></label><label className="mt-3 block text-sm">Details<textarea required minLength={10} maxLength={2000} value={note} onChange={e=>setNote(e.target.value)} className={INPUT}/></label><button disabled={busy} className={BTN+' mt-3'}>Send conduct report</button></form>}
   {!post.needs_approval&&!post.parent_id&&<StudyReplies key={id+':'+version} id={id} onUnavailable={message=>{setPost(null);setError(message)}}/>}
  </article>}
  {notice&&<p role="status" className="mt-3 text-sm text-correct-dark">{notice}</p>}
 </section>
}
