import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
import {UserAvatar} from './AvatarArt'
import type {AvatarLook} from '../lib/avatar'

export type ContributorTier='Helper'|'Regular'|'Mentor'|'Guide'
export interface CommunityReputation {display_tier:ContributorTier|null;helpful_count:number;accepted_answers:number;weekly_helpful:number;counts_scope:string}
const BUTTON='inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold'
const EVENTS=['ism-auth-change','ism-auth-expired','ism-community-change','ism-community-standing-change']

export function useCommunityEpoch(){
 const generation=useRef(0),[version,setVersion]=useState(0)
 useEffect(()=>{const update=()=>{++generation.current;setVersion(n=>n+1)};for(const name of EVENTS)window.addEventListener(name,update);return()=>{++generation.current;for(const name of EVENTS)window.removeEventListener(name,update)}},[])
 return {generation,version}
}
function useStandingRead<T>(path:string){
 const {generation,version}=useCommunityEpoch(),[data,setData]=useState<T|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{const run=++generation.current;setData(null);setError('');reviewRequest<T>(path).then(result=>{if(run===generation.current)setData(result)}).catch(e=>{if(run===generation.current)setError(e.message)});return()=>{++generation.current}},[path,version,retry])
 return {data,error,retry:()=>setRetry(n=>n+1)}
}
export function TierFlair({tier,post=false}:{tier?:ContributorTier|null;post?:boolean}){
 if(!tier||post&&tier==='Helper')return null
 return <span className="inline-flex rounded-pill bg-community-soft px-2.5 py-1 text-xs font-semibold text-community-dark" title="Highest earned community tier">{tier}</span>
}
export function ContributorName({author,author_tier,author_profile_id}:{author:string;author_tier?:ContributorTier|null;author_profile_id?:string|null}){
 return <>{author_profile_id?<Link className="break-words font-semibold text-link" to={'/creators/'+encodeURIComponent(author_profile_id)}>{author}</Link>:<b className="break-words">{author}</b>}<TierFlair tier={author_tier} post/></>
}
export function ReputationSummary({value}:{value:CommunityReputation}){
 return <section aria-label="Community reputation" className="mt-4 rounded-panel border border-hairline bg-card p-4">
  <div className="flex flex-wrap items-center gap-2"><h2 className="font-display text-xl">Community reputation</h2><TierFlair tier={value.display_tier}/></div>
  <div className="mt-3 flex flex-wrap gap-6"><p><strong className="font-display text-xl">{value.helpful_count}</strong><span className="ml-2 text-sm text-secondary">Helpful votes</span></p><p><strong className="font-display text-xl">{value.accepted_answers}</strong><span className="ml-2 text-sm text-secondary">Accepted replies</span></p></div>
  <p className="mt-2 text-xs text-secondary">Lifetime counts on published posts visible to you. Hidden, blocked and locked conversations are excluded. The highest earned tier stays visible.</p>
 </section>
}
interface OwnStanding extends CommunityReputation {weighted_helpful:number;tier:ContributorTier|null;privileges_restricted:boolean;mentor_eligible:boolean;can_create:boolean;post_limit:number;reply_limit:number;creator_public:boolean;board_public:boolean}
export function OwnCommunityStanding(){
 const {data,error,retry}=useStandingRead<OwnStanding>('/community/standing')
 return <section aria-label="Your community standing" className="mt-4 rounded-panel border border-hairline bg-card p-5">
  <h2 className="font-display text-xl">Your community standing</h2>
  {error?<p role="alert" className="mt-3 text-sm text-mypick">{error} <button className={BUTTON} onClick={retry}>Retry standing</button></p>:!data?<p role="status" className="mt-3 text-sm text-secondary">Loading standing…</p>:<>
   <div className="mt-3 flex flex-wrap items-center gap-3"><TierFlair tier={data.display_tier}/><p className="text-sm">{data.weighted_helpful} weighted Helpful · no points or XP</p></div>
   <p className="mt-2 text-sm text-secondary">{data.helpful_count} visible Helpful votes · {data.accepted_answers} visible accepted {data.accepted_answers===1?'reply':'replies'}</p>
   <p className="mt-2 text-sm text-secondary">Highest earned tiers stay on display. Posting access uses current eligible votes and moderation: {data.post_limit} posts / {data.reply_limit} replies per day.</p>
   {data.privileges_restricted&&<p role="status" className="mt-3 rounded-[8px] bg-attention-soft p-3 text-sm text-attention-dark">Ladder privileges are paused while your posts or account need moderation.</p>}
   {data.mentor_eligible&&<p className="mt-3 text-sm">You are eligible for a reviewer or editorial invitation. Mentor standing does not grant access automatically.</p>}
   <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">{[['10 · Helper','Study notes open without the new-account wait'],['25 · Regular','10 posts / 60 replies daily, plus post flair'],['50 · Mentor','Eligibility for reviewer or editorial invitations'],['150 · Guide','Eligibility for the weekly helpful strip']].map(([title,description])=><div key={title}><dt className="font-semibold">{title}</dt><dd className="mt-1 text-secondary">{description}</dd></div>)}</dl>
   <p className="mt-4 text-xs text-secondary">Guide features require a public creator profile, weekly-board visibility and visible Helpful activity this week. {data.creator_public&&data.board_public?'Your visibility settings allow featuring.':'You control whether you appear.'}</p>
   <div className="mt-2 flex flex-wrap gap-3"><Link className={BUTTON} to="/creators/settings">Creator visibility</Link><Link className={BUTTON} to="/profile#account-tools-title">Weekly-board visibility</Link></div>
  </>}
 </section>
}
interface Guide extends CommunityReputation {id:string;handle:string;avatar?:AvatarLook|null}
interface GuideWeek {week_start:string;week_end:string;as_of:string;items:Guide[]}
export function GuideStrip(){
 const {data,error,retry}=useStandingRead<GuideWeek>('/community/guides')
 const date=(value:string)=>new Date(value+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',timeZone:'Asia/Kolkata'})
 return <section aria-label="Helpful Guides this week" className="my-4 rounded-panel border border-hairline bg-card p-4">
  <div className="flex flex-wrap items-baseline justify-between gap-2"><h2 className="font-display text-xl">Helpful Guides this week</h2>{data&&<p className="text-xs text-secondary">{date(data.week_start)} – {date(data.week_end)} · IST</p>}</div>
  <p className="mt-1 text-xs text-secondary">Current Guides with Helpful activity on posts you can view. Public profile and weekly-board choices apply.</p>
  {error?<p role="alert" className="mt-3 text-sm text-mypick">Could not load Guides. <button className={BUTTON} onClick={retry}>Retry Guides</button></p>:!data?<p role="status" className="mt-3 text-sm text-secondary">Loading Guides…</p>:<>
   {!data.items.length?<p className="mt-3 text-sm text-secondary">No eligible Guides with visible Helpful activity this week.</p>:<div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{data.items.map(author=><Link key={author.id} to={'/creators/'+encodeURIComponent(author.id)} className="min-w-0 rounded-[10px] border border-hairline bg-paper p-3"><div className="flex flex-wrap items-center gap-2"><UserAvatar look={author.avatar} initials={author.handle} size={32}/><strong className="break-words text-sm">{author.handle}</strong><TierFlair tier="Guide"/></div><p className="mt-2 text-xs text-secondary">{author.weekly_helpful} Helpful this week</p></Link>)}</div>}
   <p className="mt-2 text-xs text-muted">Updated {new Date(data.as_of).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})} IST · ranks update with votes and visibility.</p>
  </>}
 </section>
}
