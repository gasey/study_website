import {ReputationSummary,useCommunityEpoch,type CommunityReputation} from '../components/ContributorStanding'
import BioModeration from '../components/BioModeration'
import AvatarArt, {DEFAULT_HERO_LOOK, UserAvatar} from '../components/AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import {useEffect,useState,type FormEvent} from 'react'
import {Link,useLocation,useNavigate,useParams,useSearchParams} from 'react-router-dom'
import {contentRequest,type MaterialItem} from '../lib/materials'
import {MaterialCard} from '../components/MaterialDiscovery'
const BUTTON='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold disabled:opacity-40'
const INPUT='min-h-11 w-full min-w-0 rounded-[8px] border border-hairline bg-card px-3 py-2 text-sm'
const SHELL='mx-auto max-w-[1180px] px-5 pb-24 pt-8 sm:px-6'
interface TargetExam{id:string;title:string;is_primary?:boolean}
interface LearnerScores{weekly_xp:number;league:string;lifetime_xp:number;streak_days:number;daily_five_plays:number;daily_five_best:number;cup_plays:number;cup_best:number;duel_wins:number;blocks_best?:number;blocks_runs?:number}
interface LearnerActivitySummary{questions_answered:number;questions_correct:number|null;saved_questions:number;posts_count:number;doubts_count:number;answers_count:number;shared_packs_count:number;shared_tests_count:number}
interface Creator{avatar?:AvatarLook|null;id:string;handle:string;bio:string;materials:number;level?:number;target_exams?:TargetExam[]}
interface PublicCreator extends Creator{scholar_title?:string;district?:string|null;board_public?:boolean;scores?:LearnerScores|null;activity?:LearnerActivitySummary;community:CommunityReputation;public:boolean;following:boolean;followers:number;is_self:boolean;contributions:{id:string;title:string;kind:string;canonical_id:string|null;updated_at:string}[];has_more_contributions:boolean}
type ProfileTab='posts'|'doubts'|'saved'|'answered'|'materials'|'contributions'
interface ActivityPostItem{id:number;kind:string;body:string;topic_tag?:string|null;topic_label?:string|null;reference?:{kind:string;id:string}|null;helpful:number;reply_count:number;created_at:string}
interface ActivityDoubtItem{id:number;kind:'doubt'|'explanation'|'reply';canonical_id:string;question:string;subject?:string|null;topic?:string|null;accepted:boolean;pinned:boolean;helpful:number;created_at:string;body:string|null;spoiler_locked:boolean}
interface ActivitySavedQuestion{canonical_id:string;question:string;subject?:string|null;topic?:string|null;saved_at:string}
interface ActivitySharedPack{token:string;title:string;description:string;mode:string;duration_minutes:number;item_count:number;clones_count:number;created_at:string}
interface ActivitySharedTest{entry_id:string;title:string;description:string;question_count:number;duration_minutes:number;published_at:string}
interface ActivityAnsweredItem{canonical_id:string;question:string;subject?:string|null;topic?:string|null;answered_at:string;outcome:'correct'|'wrong'|null}
interface ActivityPayload{tab:'posts'|'doubts'|'saved'|'answered';items:unknown[];has_more:boolean;shared_packs?:ActivitySharedPack[];shared_tests?:ActivitySharedTest[]}
function refHref(ref?:{kind:string;id:string}|null){
 if(!ref||!ref.id)return null
 if(ref.kind==='question')return '/bank/'+encodeURIComponent(ref.id)
 if(ref.kind==='material')return '/materials/'+encodeURIComponent(ref.id)
 if(ref.kind==='exam')return '/exams/'+encodeURIComponent(ref.id)
 return null
}
function CreatorActivityFeed({uid,tab}:{uid:string;tab:'posts'|'doubts'|'saved'|'answered'}){
 const [offset,setOffset]=useState(0)
 const [data,setData]=useState<ActivityPayload|null>(null)
 const [error,setError]=useState('')
 const [retry,setRetry]=useState(0)
 useEffect(()=>{setOffset(0)},[uid,tab])
 useEffect(()=>{
  let live=true;setData(null);setError('')
  contentRequest<ActivityPayload>(`/creators/${encodeURIComponent(uid)}/activity?tab=${tab}&offset=${offset}`)
   .then(r=>{if(live)setData(r)})
   .catch(e=>{if(live)setError(e.message)})
  return()=>{live=false}
 },[uid,tab,offset,retry])

 if(error)return <div className="mt-5"><ErrorNotice error={error}/><button onClick={()=>setRetry(n=>n+1)} className={BUTTON+' mt-3'}>Retry</button></div>
 if(!data)return <p role="status" className="mt-5 text-sm text-muted">Loading activity…</p>

 if(tab==='posts'){
  const items=data.items as ActivityPostItem[]
  return <section aria-label="Study posts and notes" className="mt-5 space-y-3">
   {items.map(p=>{
    const href=refHref(p.reference)
    return <article key={p.id} className="lp-feed-card">
     <div className="lp-feed-head">
      <span className={`lp-kind-pill ${p.kind==='material-share'?'is-teal':'is-cobalt'}`}>{p.kind==='material-share'?'Material share':'Study post'}</span>
      {p.topic_label&&<span className="lp-topic-pill">{p.topic_label}</span>}
      <span className="lp-feed-date">{new Date(p.created_at).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</span>
     </div>
     <p className="lp-feed-body">{p.body}</p>
     <div className="lp-feed-foot">
      <span>👍 {p.helpful} helpful · 💬 {p.reply_count} {p.reply_count===1?'reply':'replies'}</span>
      <div className="flex flex-wrap gap-3">
       {href&&<Link to={href} className="font-semibold text-link hover:underline">Open linked item →</Link>}
       <Link to={`/community?post=${p.id}`} className="font-semibold text-link hover:underline">View in Community →</Link>
      </div>
     </div>
    </article>
   })}
   {!items.length&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-sm text-secondary">No public study posts or notes yet.</p>}
   <PageButtons offset={offset} more={data.has_more} onPage={setOffset}/>
  </section>
 }

 if(tab==='doubts'){
  const items=data.items as ActivityDoubtItem[]
  return <section aria-label="Doubts and discussion answers" className="mt-5 space-y-3">
   {items.map(d=><article key={d.id} className="lp-feed-card">
    <div className="lp-feed-head">
     <span className={`lp-kind-pill ${d.kind==='doubt'?'is-amber':d.kind==='explanation'?'is-emerald':'is-violet'}`}>
      {d.kind==='doubt'?'Doubt asked':d.kind==='explanation'?'Explanation':'Discussion reply'}
     </span>
     {d.accepted&&<span className="lp-kind-pill is-emerald">✓ Accepted</span>}
     {d.pinned&&<span className="lp-kind-pill is-cobalt">📌 Pinned</span>}
     {d.subject&&<span className="lp-topic-pill">{d.subject}</span>}
     <span className="lp-feed-date">{new Date(d.created_at).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</span>
    </div>
    <Link to={'/bank/'+encodeURIComponent(d.canonical_id)} className="lp-feed-q">{d.question}</Link>
    {d.spoiler_locked?(
     <p className="lp-spoiler-note">🔒 Answer or reveal this question first to read their discussion without spoilers.</p>
    ):(
     d.body&&<p className="lp-feed-body">{d.body}</p>
    )}
    <div className="lp-feed-foot">
     <span>👍 {d.helpful} helpful</span>
     <Link to={'/bank/'+encodeURIComponent(d.canonical_id)} className="font-semibold text-link hover:underline">
      {d.spoiler_locked?'Attempt question to unlock →':'Open question thread →'}
     </Link>
    </div>
   </article>)}
   {!items.length&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-sm text-secondary">No public doubts or question answers yet.</p>}
   <PageButtons offset={offset} more={data.has_more} onPage={setOffset}/>
  </section>
 }

 if(tab==='saved'){
  const items=data.items as ActivitySavedQuestion[]
  const packs=data.shared_packs||[]
  const tests=data.shared_tests||[]
  return <section aria-label="Saved questions, shared packs and tests" className="mt-5 space-y-5">
   {!!packs.length&&(
    <div>
     <h2 className="mb-2.5 font-mono text-xs font-bold uppercase tracking-wider text-secondary">Shared Vault Study Packs ({packs.length})</h2>
     <div className="grid gap-3 md:grid-cols-2">
      {packs.map(pk=><Link key={pk.token} to={'/vault/share/'+encodeURIComponent(pk.token)} className="lp-feed-card transition hover:border-ink">
       <div className="lp-feed-head">
        <span className="lp-kind-pill is-violet">📦 Vault Pack · {pk.mode}</span>
        <span className="lp-feed-date">{pk.item_count} Qs · {pk.clones_count} clones</span>
       </div>
       <strong className="mt-1 block font-display text-lg text-ink">{pk.title}</strong>
       {pk.description&&<p className="mt-1 line-clamp-2 text-xs text-secondary">{pk.description}</p>}
      </Link>)}
     </div>
    </div>
   )}
   {!!tests.length&&(
    <div>
     <h2 className="mb-2.5 font-mono text-xs font-bold uppercase tracking-wider text-secondary">Published Shared Mock Tests ({tests.length})</h2>
     <div className="grid gap-3 md:grid-cols-2">
      {tests.map(t=><Link key={t.entry_id} to={'/tests/'+encodeURIComponent(t.entry_id)} className="lp-feed-card transition hover:border-ink">
       <div className="lp-feed-head">
        <span className="lp-kind-pill is-teal">⏱ Shared Test</span>
        <span className="lp-feed-date">{t.question_count} Qs{t.duration_minutes?` · ${t.duration_minutes}m`:''}</span>
       </div>
       <strong className="mt-1 block font-display text-lg text-ink">{t.title}</strong>
       {t.description&&<p className="mt-1 line-clamp-2 text-xs text-secondary">{t.description}</p>}
      </Link>)}
     </div>
    </div>
   )}
   <div>
    <h2 className="mb-2.5 font-mono text-xs font-bold uppercase tracking-wider text-secondary">Saved Bank Questions</h2>
    <div className="space-y-2.5">
     {items.map(sq=><Link key={sq.canonical_id} to={'/bank/'+encodeURIComponent(sq.canonical_id)} className="lp-feed-card block transition hover:border-ink">
      <div className="lp-feed-head">
       <span className="lp-kind-pill is-amber">★ Saved</span>
       {sq.subject&&<span className="lp-topic-pill">{sq.subject}</span>}
       {sq.topic&&<span className="lp-topic-pill">{sq.topic}</span>}
       <span className="lp-feed-date">{new Date(sq.saved_at).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</span>
      </div>
      <p className="lp-feed-q">{sq.question}</p>
      <div className="lp-feed-foot">
       <span className="text-muted">From Finna Question Bank</span>
       <span className="font-semibold text-link">Practice question →</span>
      </div>
     </Link>)}
     {!items.length&&!packs.length&&!tests.length&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-sm text-secondary">No saved bank questions, vault packs, or shared tests yet.</p>}
    </div>
    <PageButtons offset={offset} more={data.has_more} onPage={setOffset}/>
   </div>
  </section>
 }

 const items=data.items as ActivityAnsweredItem[]
 return <section aria-label="Recently practiced questions" className="mt-5 space-y-2.5">
  {items.map(aq=><Link key={aq.canonical_id} to={'/bank/'+encodeURIComponent(aq.canonical_id)} className="lp-feed-card block transition hover:border-ink">
   <div className="lp-feed-head">
    {aq.outcome==='correct'?<span className="lp-kind-pill is-emerald">✓ Solved</span>:aq.outcome==='wrong'?<span className="lp-kind-pill is-amber">Reviewed</span>:<span className="lp-kind-pill is-cobalt">Practiced</span>}
    {aq.subject&&<span className="lp-topic-pill">{aq.subject}</span>}
    {aq.topic&&<span className="lp-topic-pill">{aq.topic}</span>}
    <span className="lp-feed-date">{new Date(aq.answered_at).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</span>
   </div>
   <p className="lp-feed-q">{aq.question}</p>
   <div className="lp-feed-foot">
    <span className="text-muted">Official MPSC Bank Question</span>
    <span className="font-semibold text-link">Try this question →</span>
   </div>
  </Link>)}
  {!items.length&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-sm text-secondary">No practiced bank questions recorded yet.</p>}
  <PageButtons offset={offset} more={data.has_more} onPage={setOffset}/>
 </section>
}
function ErrorNotice({error}:{error:string}){return error?<p role="alert" className="mt-4 rounded-[10px] border border-hairline bg-card p-4 text-sm text-mypick">{error} <Link to="/login" className="text-link underline">Sign in</Link></p>:null}
function PageButtons({offset,more,onPage}:{offset:number;more:boolean;onPage:(n:number)=>void}){return <nav aria-label="Creator pages" className="mt-5 flex justify-between gap-3"><button disabled={!offset} className={BUTTON} onClick={()=>onPage(Math.max(0,offset-12))}>← Previous</button><button disabled={!more} className={BUTTON} onClick={()=>onPage(offset+12)}>Next →</button></nav>}
export function CreatorDirectory(){const [params,setParams]=useSearchParams();const q=params.get('q')||'',offset=Math.max(0,Number(params.get('offset'))||0);const sort=params.get('sort')==='alpha'?'alpha':'discover';const [seed,setSeed]=useState('');const [data,setData]=useState<{items:Creator[];total:number}|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{let live=true;setData(null);setError('');const timer=setTimeout(()=>contentRequest<{items:Creator[];total:number}>('/creators?'+new URLSearchParams({q,sort,...(seed?{seed}:{}),offset:String(offset)})).then(r=>{if(live)setData(r)}).catch(e=>{if(live)setError(e.message)}),250);return()=>{live=false;clearTimeout(timer)}},[q,sort,seed,offset,retry])
 return <main className={SHELL}><div className="font-mono text-xs uppercase tracking-widest text-[#5E2F98]">Community learners &amp; creators</div><h1 className="mt-2 font-display text-3xl">Find learners &amp; profiles</h1><p className="mt-3 max-w-[700px] text-base leading-relaxed text-secondary">Discover peers matched to your exams or search any public @handle to inspect their pixel hero, target exams, scores, and published notes.</p><div className="mt-5 flex flex-wrap items-center gap-2.5"><Link to="/creators/settings" className={BUTTON}>My visibility &amp; follows</Link><Link to="/community?tab=following" className={BUTTON}>Following feed →</Link><div className="ml-auto flex items-center gap-2"><button type="button" aria-pressed={sort==='discover'} onClick={()=>{const next=new URLSearchParams(params);next.set('sort','discover');next.delete('offset');setParams(next,{replace:true})}} className={BUTTON+(sort==='discover'?' !border-ink !bg-ink !text-paper':'')}>For you</button><button type="button" aria-pressed={sort==='alpha'} onClick={()=>{const next=new URLSearchParams(params);next.set('sort','alpha');next.delete('offset');setParams(next,{replace:true})}} className={BUTTON+(sort==='alpha'?' !border-ink !bg-ink !text-paper':'')}>A–Z</button>{sort==='discover'&&<button type="button" onClick={()=>setSeed(Date.now().toString(36))} className={BUTTON} title="Shuffle fresh learners">↻ Shuffle</button>}</div></div><input aria-label="Search learner handles" maxLength={100} value={q} onChange={e=>{const next=new URLSearchParams(params);if(e.target.value)next.set('q',e.target.value);else next.delete('q');next.delete('offset');setParams(next)}} type="search" placeholder="Search public handles" className={INPUT+' mt-5'}/><ErrorNotice error={error}/>{error&&<button className={BUTTON+' mt-3'} onClick={()=>setRetry(n=>n+1)}>Retry</button>}{!data&&!error&&<p role="status" className="mt-5 text-muted">Loading learners…</p>}{data&&<><div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.items.map(c=><Link key={c.id} to={'/creators/'+encodeURIComponent(c.id)} className="flex min-w-0 flex-col justify-between rounded-[16px] border border-hairline bg-card p-5 transition hover:border-ink"><div><div className="flex items-center gap-3"><UserAvatar look={c.avatar} initials={c.handle} size={50}/><div className="min-w-0"><h2 className="truncate font-display text-xl">{c.handle}</h2>{c.level!=null&&<span className="inline-flex rounded-full bg-canvas px-2 py-0.5 font-mono text-[11px] font-bold text-secondary">Lv {c.level}</span>}</div></div><p className="mt-3 line-clamp-3 break-words text-sm text-secondary">{c.bio||'Learning and sharing study materials on Finna.'}</p>{!!c.target_exams?.length&&<div className="mt-3 flex flex-wrap gap-1.5">{c.target_exams.map(ex=><span key={ex.id} className="rounded-full border border-hairline bg-canvas px-2.5 py-0.5 text-[11px] font-semibold text-ink">{ex.title}</span>)}</div>}</div><p className="mt-4 font-mono text-xs text-muted">{c.materials} published materials</p></Link>)}</div>{!data.items.length&&<p className="mt-5 rounded-[14px] border border-hairline bg-card p-6 text-secondary">No public profiles match yet. You can choose to publish your own profile in visibility settings.</p>}<PageButtons offset={offset} more={offset+12<data.total} onPage={n=>{const next=new URLSearchParams(params);next.set('offset',String(n));setParams(next)}}/></>}</main>
}
export function FollowingMaterials({embedded=false}:{embedded?:boolean}={}){const Heading=embedded?'h2':'h1';return <div className={embedded?'mt-4 min-w-0':SHELL}><Heading className={embedded?'font-display text-xl':'font-display text-3xl'}>From creators you follow</Heading><p className="mt-3 text-sm text-secondary">New approved materials, most recent first. Private profiles and blocked creators do not appear.</p><Link to="/creators" className={BUTTON+' mt-4'}>Find creators →</Link><CreatorMaterials following embedded={embedded}/></div>}
function CreatorMaterials({uid,following=false,embedded=false}:{uid?:string;following?:boolean;embedded?:boolean}){const [offset,setOffset]=useState(0),[data,setData]=useState<{items:MaterialItem[];total:number}|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 useEffect(()=>{setOffset(0)},[uid,following])
 useEffect(()=>{let live=true;setData(null);setError('');contentRequest<{items:MaterialItem[];total:number}>('/materials?'+new URLSearchParams({...(uid?{creator_id:uid}:{}),following:String(following),sort:'recent',limit:'12',offset:String(offset)})).then(r=>{if(live)setData(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[uid,following,offset,retry])
 return <section aria-label="Published materials" className="mt-6"><ErrorNotice error={error}/>{error&&<button onClick={()=>setRetry(n=>n+1)} className={BUTTON+' mt-3'}>Retry</button>}{!data&&!error&&<p role="status" className="text-muted">Loading publications…</p>}{data&&<><div className={embedded?"grid gap-4":"grid gap-4 md:grid-cols-2 lg:grid-cols-3"}>{data.items.map(m=><MaterialCard key={m.id} item={m}/>)}</div>{!data.items.length&&<p className="rounded-[14px] border border-hairline bg-card p-6 text-secondary">{following?'No publications to show yet. Follow a public creator, then their approved materials will appear here.':'No published materials yet.'}</p>}<PageButtons offset={offset} more={offset+12<data.total} onPage={setOffset}/></>}</section>
}
export default function CreatorProfile(){const {generation,version}=useCommunityEpoch();const {id=''}=useParams();const nav=useNavigate();const [data,setData]=useState<PublicCreator|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0),[offset,setOffset]=useState(0),[tab,setTab]=useState<ProfileTab>('posts'),[tabChosen,setTabChosen]=useState(false),[notice,setNotice]=useState(''),[reportOpen,setReportOpen]=useState(false),[blockConfirm,setBlockConfirm]=useState(false),[report,setReport]=useState({reason:'spam',note:''})
 useEffect(()=>{setOffset(0);setTab('posts');setTabChosen(false);setReportOpen(false);setBlockConfirm(false);setNotice('');setReport({reason:'spam',note:''})},[id,version])
 useEffect(()=>{let live=true;const run=++generation.current;setData(null);setError('');contentRequest<PublicCreator>('/creators/'+encodeURIComponent(id)+'?offset='+offset).then(r=>{if(live&&run===generation.current){setData(r);if(!tabChosen){const act=r.activity;if(act?.posts_count)setTab('posts');else if((act?.doubts_count||0)+(act?.answers_count||0)>0)setTab('doubts');else if(r.materials>0)setTab('materials');else if((act?.saved_questions||0)+(act?.shared_packs_count||0)+(act?.shared_tests_count||0)>0)setTab('saved');else if(act?.questions_answered)setTab('answered');else if(r.contributions.length)setTab('contributions')}}}).catch(e=>{if(live&&run===generation.current)setError(e.message)});return()=>{live=false;++generation.current}},[id,offset,refresh,version,tabChosen])
 const pickTab=(next:ProfileTab)=>{setTabChosen(true);setTab(next)}
 async function act(kind:string,body:unknown){setBusy(true);setError('');try{await contentRequest('/creators/'+encodeURIComponent(id)+'/'+kind,body);if(kind==='block'){nav('/creators/settings');return}if(kind==='report'){setNotice('Report sent to the owner for review.');setReportOpen(false)}else setRefresh(n=>n+1)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <main className={SHELL}>
  <div className="flex flex-wrap items-center justify-between gap-3">
   <Link to="/creators" className="text-sm font-semibold text-link">← All learners &amp; creators</Link>
   <Link to="/profile/rewards" className="text-sm font-semibold text-link">Weekly standings →</Link>
  </div>
  <ErrorNotice error={error}/>
  {!data&&!error&&<p role="status" className="mt-5 text-muted">Loading learner profile…</p>}
  {notice&&<p role="status" className="mt-4 text-sm text-practice-dark">{notice}</p>}
  {data&&<>
   {/* Sleek Learner Hero Card with animated 16-bit Pixel RPG Sprite */}
   <header className="lp-hero mt-5">
    <div className="lp-sprite-stage" aria-hidden="true">
     <AvatarArt look={data.avatar || DEFAULT_HERO_LOOK} variant="sprite" size={114} animate label={`${data.handle} pixel hero`}/>
     <span className="lp-level-tag">Lv {data.level ?? 1}</span>
    </div>
    <div className="lp-hero-body">
     <div className="lp-eyebrow-row">
      <span className="lp-eyebrow">{data.public ? 'Public learner profile' : 'Your private profile preview'}</span>
      {data.scholar_title && <span className="lp-chip">{data.scholar_title}</span>}
      {data.district && <span className="lp-chip">📍 {data.district}</span>}
     </div>
     <h1 className="lp-handle">@{data.handle}</h1>
     <p className="lp-bio">{data.bio || 'Preparing for Mizoram & MPSC exams on Finna.'}</p>
     {!!data.target_exams?.length && (
      <div className="lp-exams" aria-label="Target exams">
       <span className="lp-exams-label">Preparing for</span>
       {data.target_exams.map(ex => (
        <Link key={ex.id} to={`/exams/${encodeURIComponent(ex.id)}`} className={`lp-exam-pill${ex.is_primary ? ' is-primary' : ''}`}>
         {ex.is_primary ? '★ ' : ''}{ex.title}
        </Link>
       ))}
      </div>
     )}
    </div>
    <div className="lp-actions">
     {data.is_self ? (
      <>
       <Link to="/profile/avatar" className="lp-btn lp-btn--gold">Edit Pixel Hero</Link>
       <Link to="/creators/settings" className="lp-btn">Visibility &amp; Bio</Link>
      </>
     ) : (
      <>
       <button disabled={busy} aria-pressed={data.following} onClick={()=>void act('follow',{enabled:!data.following})} className={`lp-btn ${data.following ? 'lp-btn--following' : 'lp-btn--gold'}`}>
        {data.following ? '✓ Following' : '+ Follow'}
       </button>
       <button disabled={busy} onClick={()=>setBlockConfirm(v=>!v)} className="lp-btn">Block</button>
       <button disabled={busy} onClick={()=>setReportOpen(v=>!v)} className="lp-btn">Report</button>
      </>
     )}
    </div>
   </header>

   {/* Opted-in Weekly XP, Daily Five, Cup & Streak Score Tiles */}
   {data.scores ? (
    <section aria-label="Learner scores and activity" className="lp-score-grid mt-4">
     <article className="lp-score-tile is-gold">
      <span>Weekly XP · {data.scores.league}</span>
      <strong>{data.scores.weekly_xp.toLocaleString('en-IN')} <small>XP</small></strong>
      <p>{data.scores.lifetime_xp.toLocaleString('en-IN')} lifetime XP</p>
     </article>
     <article className="lp-score-tile is-teal">
      <span>Daily Five</span>
      <strong>{data.scores.daily_five_best.toLocaleString('en-IN')} <small>best</small></strong>
      <p>{data.scores.daily_five_plays} completed runs</p>
     </article>
     <article className="lp-score-tile is-cobalt">
      <span>Weekly Cup</span>
      <strong>{data.scores.cup_best.toLocaleString('en-IN')} <small>best</small></strong>
      <p>{data.scores.cup_plays} cup entries</p>
     </article>
     <article className="lp-score-tile is-violet">
      <span>Streak &amp; Arcade</span>
      <strong>{data.scores.streak_days}d <small>streak</small></strong>
      <p>
       {data.scores.duel_wins} duel {data.scores.duel_wins === 1 ? 'win' : 'wins'}
       {data.scores.blocks_best ? ` · 🧱 ${data.scores.blocks_best.toLocaleString('en-IN')} Blocks` : ''}
      </p>
     </article>
    </section>
   ) : (
    <p className="mt-4 rounded-[12px] border border-hairline bg-card px-4 py-3 text-xs text-secondary">
     {data.is_self
      ? 'Your scores are currently hidden from others. Opt into leaderboard visibility in Profile → Rewards to display your Weekly XP, Daily Five, Cup & Blocks tiles here.'
      : 'This learner keeps their competitive scores private.'}
    </p>
   )}

   {data.community&&<ReputationSummary value={data.community}/>}
   {blockConfirm&&<section aria-label="Confirm creator block" className="mt-4 rounded-[12px] border border-hairline bg-card p-5"><h2 className="font-display text-xl">Block this learner?</h2><p className="mt-2 text-sm text-secondary">Follows in both directions will be removed. Their materials, profile, discussions and desk messages will be hidden while signed in, and pending desk invitations will be cancelled. You can unblock them anytime in visibility settings.</p><div className="mt-3 flex gap-3"><button disabled={busy} className={BUTTON+' text-mypick'} onClick={()=>void act('block',{enabled:true})}>Confirm block</button><button disabled={busy} className={BUTTON} onClick={()=>setBlockConfirm(false)}>Cancel</button></div></section>}

   {/* Public Study & Community Activity Strip */}
   <section aria-label="Learner study and community summary" className="lp-activity-grid mt-4">
    <button type="button" onClick={()=>pickTab('answered')} className={`lp-act-tile${tab==='answered'?' is-active':''}`}>
     <span className="lp-act-lbl">Questions Answered</span>
     <strong>{(data.activity?.questions_answered??0).toLocaleString('en-IN')}</strong>
     <small>
      {data.activity?.questions_correct!=null&&data.activity.questions_answered>0
       ? `${Math.round((data.activity.questions_correct/data.activity.questions_answered)*100)}% accuracy`
       : 'Bank practice'}
     </small>
    </button>
    <button type="button" onClick={()=>pickTab('saved')} className={`lp-act-tile${tab==='saved'?' is-active':''}`}>
     <span className="lp-act-lbl">Saved &amp; Packs</span>
     <strong>{(data.activity?.saved_questions??0).toLocaleString('en-IN')}</strong>
     <small>
      {(data.activity?.shared_packs_count??0)+(data.activity?.shared_tests_count??0)} shared packs &amp; tests
     </small>
    </button>
    <button type="button" onClick={()=>pickTab('doubts')} className={`lp-act-tile${tab==='doubts'?' is-active':''}`}>
     <span className="lp-act-lbl">Doubts &amp; Q&amp;A</span>
     <strong>{((data.activity?.doubts_count??0)+(data.activity?.answers_count??0)).toLocaleString('en-IN')}</strong>
     <small>{data.activity?.doubts_count??0} doubts · {data.activity?.answers_count??0} answers</small>
    </button>
    <button type="button" onClick={()=>pickTab('posts')} className={`lp-act-tile${tab==='posts'?' is-active':''}`}>
     <span className="lp-act-lbl">Community Posts</span>
     <strong>{(data.activity?.posts_count??0).toLocaleString('en-IN')}</strong>
     <small>Study notes &amp; shares</small>
    </button>
    <button type="button" onClick={()=>pickTab('materials')} className={`lp-act-tile${tab==='materials'?' is-active':''}`}>
     <span className="lp-act-lbl">Materials · Followers</span>
     <strong>{data.materials}</strong>
     <small>{data.followers} {data.followers===1?'follower':'followers'}</small>
    </button>
   </section>

   {reportOpen&&<form onSubmit={(e:FormEvent)=>{e.preventDefault();void act('report',report)}} className="mt-4 rounded-[14px] border border-hairline bg-card p-5"><label className="block text-sm">Reason<select className={INPUT+' mt-2'} value={report.reason} onChange={e=>setReport({...report,reason:e.target.value})}>{['spam','harassment','impersonation','other'].map(r=><option key={r}>{r}</option>)}</select></label><label className="mt-3 block text-sm">What should be reviewed?<textarea required minLength={10} maxLength={2000} value={report.note} onChange={e=>setReport({...report,note:e.target.value})} className={INPUT+' mt-2'}/></label><button disabled={busy} className={BUTTON+' mt-3'}>Send report</button></form>}

   <div className="lp-tab-bar mt-5" role="tablist" aria-label="Learner profile sections">
    {([
     {id:'posts',label:'Posts',count:data.activity?.posts_count??0},
     {id:'doubts',label:'Doubts & Q&A',count:(data.activity?.doubts_count??0)+(data.activity?.answers_count??0)},
     {id:'saved',label:'Saved & Packs',count:(data.activity?.saved_questions??0)+(data.activity?.shared_packs_count??0)+(data.activity?.shared_tests_count??0)},
     {id:'answered',label:'Answered',count:data.activity?.questions_answered??0},
     {id:'materials',label:'Materials',count:data.materials},
     {id:'contributions',label:'Contributions',count:data.contributions.length},
    ] as const).map(item=>(
     <button
      key={item.id}
      type="button"
      role="tab"
      aria-selected={tab===item.id}
      onClick={()=>pickTab(item.id)}
      className={`lp-tab-pill${tab===item.id?' is-active':''}`}
     >
      <span>{item.label}</span>
      <span className="lp-tab-count">{item.count}</span>
     </button>
    ))}
   </div>

   {tab==='materials' ? (
    <CreatorMaterials uid={id}/>
   ) : tab==='contributions' ? (
    <section className="mt-5 space-y-3">
     {data.contributions.map(c=><Link key={c.id} to={c.canonical_id?'/bank/'+encodeURIComponent(c.canonical_id):'/community/questions'} className="block rounded-[12px] border border-hairline bg-card p-5 transition hover:border-ink"><div className="font-mono text-xs uppercase text-muted">Published · {c.kind.replace(/_/g,' ')}</div><h2 className="mt-2 break-words font-display text-xl">{c.title}</h2><p className="mt-2 text-xs text-muted">{new Date(c.updated_at).toLocaleDateString('en-IN')}</p></Link>)}
     {!data.contributions.length&&<p className="rounded-[12px] border border-hairline bg-card p-5 text-secondary">No publicly attributed published bank contributions yet.</p>}
     <PageButtons offset={offset} more={data.has_more_contributions} onPage={setOffset}/>
     <p className="text-xs text-muted">Contribution attribution follows the creator’s separate contribution-visibility setting.</p>
    </section>
   ) : (
    <CreatorActivityFeed uid={id} tab={tab}/>
   )}
  </>}
 </main>
}
interface CreatorSettingsData{bio_version:number;bio_needs_approval:boolean;bio_hidden:boolean;id:string;handle:string;public:boolean;bio:string;following:{id:string;handle:string;public:boolean}[];blocked:{id:string;handle:string}[]}
type CreatorTab='visibility'|'following'|'blocked'
export function CreatorSettings(){
 const location=useLocation()
 const [data,setData]=useState<CreatorSettingsData|null>(null),[publicProfile,setPublic]=useState(false),[bio,setBio]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0),[copied,setCopied]=useState(false),[filter,setFilter]=useState('')
 const [tab,setTab]=useState<CreatorTab>(()=>location.hash==='#blocked-users'?'blocked':'visibility')
 useEffect(()=>{if(location.hash==='#blocked-users')setTab('blocked')},[location.hash])
 useEffect(()=>{let live=true;setError('');contentRequest<CreatorSettingsData>('/creators/settings').then(r=>{if(live){setData(r);setPublic(r.public);setBio(r.bio)}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[refresh])
 async function mutate(path:string,body:unknown){setBusy(true);setError('');setNotice('');try{await contentRequest(path,body);setNotice('Changes saved.');setRefresh(n=>n+1);window.dispatchEvent(new Event('ism-community-standing-change'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 function copyProfileUrl(){
  if(!data||typeof navigator==='undefined'||!navigator.clipboard)return
  const url=window.location.origin+'/creators/'+encodeURIComponent(data.id)
  void navigator.clipboard.writeText(url).then(()=>{setCopied(true);window.setTimeout(()=>setCopied(false),1800)}).catch(()=>{})
 }
 const bioStatus=data?.bio_hidden?{label:'Hidden by moderation',cls:'finna-st-pill finna-st-pill--warn'}:data?.bio_needs_approval?{label:'Waiting for review',cls:'finna-st-pill finna-st-pill--amber'}:{label:publicProfile?'Live when public':'Only visible to you',cls:'finna-st-pill finna-st-pill--teal'}
 const dirty=!!data&&(publicProfile!==data.public||bio!==data.bio)
 const bioPct=Math.min(100,Math.round((bio.length/140)*100))
 const filteredFollowing=(data?.following||[]).filter(c=>!filter.trim()||c.handle.toLowerCase().includes(filter.trim().toLowerCase()))
 const filteredBlocked=(data?.blocked||[]).filter(c=>!filter.trim()||c.handle.toLowerCase().includes(filter.trim().toLowerCase()))
 const initials=data?data.handle.replace(/^@/,'').slice(0,2).toUpperCase():'CR'

 return <main className="finna-page cr-page">
  <div className="cr-shell">
   <header className="cr-hero">
    <div className="cr-hero-top">
     <div className="cr-hero-id">
      <div className={'cr-hero-av'+(publicProfile?' is-live':'')} aria-hidden="true">{initials}</div>
      <div className="cr-hero-copy">
       <span className="cr-eyebrow">Community · Creator Studio</span>
       <div className="cr-hero-title-row">
        <h1>Creator visibility &amp; community</h1>
        {data&&<span className={'cr-status-pill'+(data.public?' is-public':'')}><i aria-hidden="true"/>{data.public?'Public profile':'Private profile'}</span>}
       </div>
       <p className="cr-hero-sub">{data?`@${data.handle} · Shape how learners discover your published notes and manage who you follow`:'Shape how learners discover your published notes and manage who you follow'}</p>
      </div>
     </div>
     <div className="cr-hero-actions">
      <Link to="/profile" className="cr-glass-btn">← Profile</Link>
      <Link to="/creators" className="cr-glass-btn">Find creators</Link>
      {data&&<Link to={'/creators/'+encodeURIComponent(data.id)} className="cr-glass-btn cr-glass-btn--accent">Open page ↗</Link>}
     </div>
    </div>

    <div className="cr-hero-metrics">
     <div className="cr-metric">
      <span>Directory status</span>
      <strong>{data?(data.public?'Discoverable':'Hidden'):'—'}</strong>
     </div>
     <div className="cr-metric">
      <span>Following</span>
      <strong>{data?data.following.length:'—'}</strong>
     </div>
     <div className="cr-metric">
      <span>Blocked</span>
      <strong>{data?data.blocked.length:'—'}</strong>
     </div>
    </div>
   </header>

   <div className="cr-body">
    <nav aria-label="Creator settings sections" className="cr-side">
     <div className="cr-side-group-wrap">
      <div className="cr-side-group">Workspace</div>
      <button type="button" onClick={()=>{setTab('visibility');setFilter('')}} aria-current={tab==='visibility'?'page':undefined} className={'cr-navitem'+(tab==='visibility'?' is-on':'')}>
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="currentColor" strokeWidth="1.6"/><path d="M4.5 16.5c.8-2.8 3-4 5.5-4s4.7 1.2 5.5 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg></span>
       <span className="cr-nav-lbl">Public profile</span>
      </button>
      <button type="button" onClick={()=>{setTab('following');setFilter('')}} aria-current={tab==='following'?'page':undefined} className={'cr-navitem'+(tab==='following'?' is-on':'')}>
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><path d="M10 4.5v11M4.5 10h11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg></span>
       <span className="cr-nav-lbl">Following</span>
       {data&&<span className="cr-nav-count">{data.following.length}</span>}
      </button>
      <button type="button" onClick={()=>{setTab('blocked');setFilter('')}} aria-current={tab==='blocked'?'page':undefined} className={'cr-navitem'+(tab==='blocked'?' is-on':'')}>
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="6.5" stroke="currentColor" strokeWidth="1.6"/><path d="m5.6 5.6 8.8 8.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg></span>
       <span className="cr-nav-lbl">Blocked</span>
       {data&&<span className="cr-nav-count">{data.blocked.length}</span>}
      </button>
     </div>
     <div className="cr-side-group-wrap">
      <div className="cr-side-group">Shortcuts</div>
      <Link to="/studio" className="cr-navitem">
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><path d="M4 15.5h12M6 12l6.5-6.5a1.5 1.5 0 0 1 2.1 2.1L8.1 14H6v-2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg></span>
       <span className="cr-nav-lbl">Content studio</span>
      </Link>
      <Link to="/community?tab=following" className="cr-navitem">
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><path d="M4 6h12M4 10h9M4 14h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg></span>
       <span className="cr-nav-lbl">Following feed</span>
      </Link>
      <Link to="/account/security" className="cr-navitem">
       <span className="cr-nav-ico" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><path d="M10 2.5 4 5v4.6c0 3.7 2.5 6.8 6 7.9 3.5-1.1 6-4.2 6-7.9V5l-6-2.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg></span>
       <span className="cr-nav-lbl">Account &amp; security</span>
      </Link>
     </div>
    </nav>

    <div className="cr-pane">
     <ErrorNotice error={error}/>
     {notice&&<div role="status" className="cr-toast"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.6"/><path d="m6 9.2 2 2 4-4.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg><span>{notice}</span></div>}
     {!data&&!error&&<div role="status" className="cr-skeleton"><span/><span/><span/></div>}

     {data&&tab==='visibility'&&<div className="cr-vis-layout">
      <form className="cr-vis-form" onSubmit={e=>{e.preventDefault();void mutate('/creators/settings',{public:publicProfile,bio,expected_bio_version:data.bio_version})}}>
       <div className="cr-sec-head">
        <h2>Public visibility</h2>
        <p>Toggle discovery anytime. Hiding your profile pauses discovery without unpublishing existing materials.</p>
       </div>

       <div className={'cr-vis-switch-card'+(publicProfile?' is-on':'')}>
        <div className="cr-vis-switch-ico" aria-hidden="true">
         {publicProfile?<svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.6"/><path d="M3.5 10h13M10 3a11 11 0 0 1 0 14M10 3a11 11 0 0 0 0 14" stroke="currentColor" strokeWidth="1.4"/></svg>:<svg viewBox="0 0 20 20" fill="none"><rect x="4" y="9" width="12" height="8" rx="2" stroke="currentColor" strokeWidth="1.6"/><path d="M7 9V6.5a3 3 0 0 1 6 0V9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>}
        </div>
        <div className="cr-vis-switch-copy">
         <strong>Show my creator profile publicly</strong>
         <span>{publicProfile?'Learners can find your handle and follow new published materials.':'Only you can preview your creator page right now.'}</span>
        </div>
        <button type="button" role="switch" aria-checked={publicProfile} aria-label="Show my creator profile publicly" onClick={()=>setPublic(v=>!v)} className={'finna-st-toggle'+(publicProfile?' is-on':'')}>
         <span className="finna-st-toggle-dot"/>
        </button>
       </div>

       <div className="cr-privacy-grid">
        <div className="cr-privacy-tile is-shared">
         <span className="cr-privacy-ico" aria-hidden="true">✓</span>
         <div>
          <strong>Shared when public</strong>
          <p>Your @{data.handle} handle, short bio, and approved materials.</p>
         </div>
        </div>
        <div className="cr-privacy-tile is-locked">
         <span className="cr-privacy-ico" aria-hidden="true">🔒</span>
         <div>
          <strong>Always stays private</strong>
          <p>Email, practice scores, mocks, streaks, and billing.</p>
         </div>
        </div>
       </div>

       <div className="cr-bio-block">
        <div className="finna-st-field-top">
         <label htmlFor="creator-bio-input" className="cr-field-label">Short bio</label>
         <span className={bioStatus.cls}>{bioStatus.label}</span>
        </div>
        <div className="cr-bio-box">
         <textarea id="creator-bio-input" maxLength={140} rows={3} value={bio} onChange={e=>setBio(e.target.value)} placeholder="e.g. Sharing MPSC Polity summaries, Mizoram GK notes & past-paper breakdowns." className="cr-bio-input"/>
         <div className="cr-bio-meter" aria-hidden="true"><span style={{width:`${bioPct}%`}}/></div>
        </div>
        <div className="finna-st-hint-row">
         <span>{bio.length} / 140 characters</span>
         <span>Follows &amp; upvotes never affect XP or points</span>
        </div>
       </div>

       <div className={'cr-save-bar'+(dirty?' is-dirty':'')}>
        <span className="cr-save-status">{dirty?'You have unsaved changes':'All changes saved'}</span>
        <div className="cr-save-btns">
         {dirty&&<button type="button" disabled={busy} onClick={()=>{setPublic(data.public);setBio(data.bio)}} className="finna-st-btn finna-st-btn--quiet">Reset</button>}
         <button type="submit" disabled={busy||!dirty} className="cr-primary-btn">{busy?'Saving…':'Save visibility'}</button>
        </div>
       </div>
      </form>

      <aside className="cr-preview-col" aria-label="Live creator card preview">
       <div className="cr-preview-shell">
        <div className="cr-preview-bar">
         <span className="cr-preview-label">Live preview</span>
         <span className={'cr-preview-tag'+(publicProfile?' is-on':'')}>{publicProfile?'Discoverable':'Hidden'}</span>
        </div>
        <div className={'cr-preview-card'+(publicProfile?'':' is-dim')}>
         <div className="cr-preview-banner"/>
         <div className="cr-preview-body">
          <div className="cr-preview-av" aria-hidden="true">{initials}</div>
          <div className="cr-preview-handle">@{data.handle}</div>
          <p className={'cr-preview-bio'+(bio.trim()?'':' is-placeholder')}>
           {bio.trim()||'Add a short bio to tell learners which exams or subjects you share notes for.'}
          </p>
          <div className="cr-preview-foot">
           <span>Private scores stay hidden</span>
          </div>
         </div>
         {!publicProfile&&<div className="cr-preview-mask"><span>Private · Only you can see this</span></div>}
        </div>
        <div className="cr-preview-actions">
         <button type="button" onClick={copyProfileUrl} className="finna-st-btn cr-preview-copy">{copied?'Copied link ✓':'Copy profile link'}</button>
         <Link to={'/creators/'+encodeURIComponent(data.id)} className="finna-st-btn">View full page →</Link>
        </div>
       </div>
      </aside>
     </div>}

     {data&&tab==='following'&&<div className="cr-list-pane">
      <div className="cr-list-top">
       <div className="cr-sec-head">
        <h2>Following <span className="cr-count-pill">{data.following.length}</span></h2>
        <p>Approved study materials from creators you follow appear automatically in your Following feed.</p>
       </div>
       {data.following.length>3&&<input type="search" value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Filter by handle…" aria-label="Filter followed creators" className="cr-filter-input"/>}
      </div>
      {data.following.length?filteredFollowing.length?<div className="cr-cards-grid">
       {filteredFollowing.map(c=><div key={c.id} className="cr-person-card">
        <span className="cr-person-av" aria-hidden="true">{c.handle.slice(0,2).toUpperCase()}</span>
        <div className="cr-person-meta">
         {c.public?<Link to={'/creators/'+encodeURIComponent(c.id)} className="cr-person-name">@{c.handle}</Link>:<span className="cr-person-name">@{c.handle}</span>}
         <span className="cr-person-sub">{c.public?'Public creator · active in feed':'Profile currently hidden'}</span>
        </div>
        <button type="button" disabled={busy} onClick={()=>void mutate('/creators/'+encodeURIComponent(c.id)+'/follow',{enabled:false})} className="finna-st-btn">Unfollow</button>
       </div>)}
      </div>:<div className="cr-empty-card"><p>No followed creators match “{filter}”.</p></div>:<div className="cr-empty-card">
       <div className="cr-empty-halo" aria-hidden="true">✦</div>
       <strong>Not following any creators yet</strong>
       <p>Follow public contributors to see their newly approved notes and study sheets in one calm feed.</p>
       <Link to="/creators" className="cr-primary-btn mt-4">Explore creators →</Link>
      </div>}
     </div>}

     {data&&tab==='blocked'&&<div id="blocked-users" className="cr-list-pane">
      <div className="cr-list-top">
       <div className="cr-sec-head">
        <h2>Blocked creators <span className="cr-count-pill">{data.blocked.length}</span></h2>
        <p>Blocking removes mutual follows and hides their profile, materials, and discussions while you’re signed in. Unblocking does not re-follow.</p>
       </div>
       {data.blocked.length>3&&<input type="search" value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Filter blocked handles…" aria-label="Filter blocked creators" className="cr-filter-input"/>}
      </div>
      {data.blocked.length?filteredBlocked.length?<div className="cr-cards-grid">
       {filteredBlocked.map(c=><div key={c.id} className="cr-person-card">
        <span className="cr-person-av is-muted" aria-hidden="true">{c.handle.slice(0,2).toUpperCase()}</span>
        <div className="cr-person-meta">
         <span className="cr-person-name">@{c.handle}</span>
         <span className="cr-person-sub">Hidden across profiles, materials &amp; discussions</span>
        </div>
        <button type="button" disabled={busy} onClick={()=>void mutate('/creators/'+encodeURIComponent(c.id)+'/block',{enabled:false})} className="finna-st-btn">Unblock</button>
       </div>)}
      </div>:<div className="cr-empty-card"><p>No blocked creators match “{filter}”.</p></div>:<div className="cr-empty-card">
       <div className="cr-empty-halo" aria-hidden="true">✓</div>
       <strong>Your block list is clear</strong>
       <p>Anyone you block from a creator page or discussion will show up here so you can manage or unblock them anytime.</p>
      </div>}
     </div>}
    </div>
   </div>
  </div>
 </main>
}
export function CreatorReportAdmin(){const [params,setParams]=useSearchParams();const reportId=params.get('creator_report')||'';const [data,setData]=useState<{items:{id:number;creator_id:string;handle:string;reason:string;note:string}[];has_more:boolean}|null>(null),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0),[error,setError]=useState(''),[busy,setBusy]=useState(false),[reasons,setReasons]=useState<Record<number,string>>({})
 useEffect(()=>{let live=true;setData(null);setError('');contentRequest<typeof data>('/admin/bank/creator-reports?'+new URLSearchParams({offset:String(offset),...(reportId?{report_id:reportId}:{})})).then(r=>{if(live)setData(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[offset,refresh,reportId])
 async function resolve(id:number){setBusy(true);try{await contentRequest('/admin/bank/creator-reports/'+id+'/resolve',{reason:reasons[id]||''});setRefresh(n=>n+1)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section id="creator-reports" className="mt-6 rounded-[14px] border border-hairline bg-card p-5"><h2 className="font-display text-xl">Creator reports</h2><BioModeration/>{reportId&&<button onClick={()=>setParams(p=>{const n=new URLSearchParams(p);n.delete('creator_report');return n})} className={BUTTON+' mt-3'}>Show all open creator reports</button>}<p className="mt-2 text-sm text-secondary">Review reports here. Resolving records your decision; it does not silently unpublish materials or change account permissions.</p><ErrorNotice error={error}/>{!data&&!error&&<p className="mt-3 text-muted">Loading reports…</p>}{data?.items.map(r=><form key={r.id} onSubmit={e=>{e.preventDefault();void resolve(r.id)}} className="mt-4 border-t border-hairline pt-4"><p className="text-sm font-semibold">{r.handle} · {r.reason}</p><p className="mt-2 whitespace-pre-wrap break-words text-sm">{r.note}</p><Link to={'/creators/'+encodeURIComponent(r.creator_id)} className="inline-flex min-h-11 items-center text-sm text-link">Inspect public profile →</Link><label className="block text-sm">Decision and action taken<textarea required minLength={10} maxLength={2000} value={reasons[r.id]||''} onChange={e=>setReasons({...reasons,[r.id]:e.target.value})} className={INPUT+' mt-2'}/></label><button disabled={busy} className={BUTTON+' mt-3'}>Resolve report</button></form>)}{data&&!data.items.length&&<p className="mt-4 text-sm text-muted">No open creator reports.</p>}<div className="mt-4 flex justify-between gap-3"><button disabled={!offset||busy} onClick={()=>setOffset(Math.max(0,offset-20))} className={BUTTON}>Previous</button><button disabled={!data?.has_more||busy} onClick={()=>setOffset(offset+20)} className={BUTTON}>Next</button></div></section>
}
