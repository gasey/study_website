import WeeklyStandings from '../components/WeeklyStandings'
import BillingAccessAdmin from '../components/BillingAccessAdmin'
import RewardDiagnostics from '../components/RewardDiagnostics'
import RewardFeatureGates,{type RewardLaunchGates} from '../components/RewardFeatureGates'
import FlashBanner from '../components/FlashBanner'
import {CatLoader,CatXpBar} from '../components/CatLoader'
import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
interface Offer{id:string;title:string;points:number;pro_days:number;enabled:boolean;version:number}
interface DailyQuest{reward_eligible?:boolean;activity_only?:boolean;key:string;title:string;subtitle:string;progress:number;target:number;completed:boolean;claimed:boolean;xp_reward:number;points_reward:number}
interface WeekDay{date:string;label:string;active:boolean;is_today:boolean}
interface Wallet{
 point_budget?:{earned:number;cap:number;remaining:number;pillars:{key:string;earned:number;cap:number;remaining:number}[]};
 lifetime_xp:number;monthly_xp:number;weekly_xp?:number;level_floor_xp:number;daily_remaining:number;resets_at:string;daily_xp:number;daily_cap:number;points:number;level:number;title?:string;
 league?:{id:string;name:string;floor_xp:number;next_xp:number|null;xp_to_promote:number};
 stream_cohort?:string|null;current_streak_days?:number;longest_streak_days?:number;streak_shields?:number;last_active_ist_date?:string|null;
 daily_quests?:{ist_date:string;quests:DailyQuest[];week_strip:WeekDay[]};
 next_level_xp:number;public:boolean;catalog:Offer[];redemptions:{id:string;starts_at:string;ends_at:string}[]
}
interface Entry{id:number;kind:string;xp:number;points:number;note:string;created_at:string}
const BUTTON='ism-tactile-btn inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 text-sm font-semibold disabled:opacity-40 hover:border-hairline2'
const COHORT_OPTIONS:[string,string][]= [
 ['arts-comfort','Arts & Humanities'],
 ['science-bridge','Science & Engineering'],
 ['commerce-core','Commerce & Accounts'],
 ['balanced-core','Balanced MPSC Core'],
]
const COHORT_NAMES:Record<string,string>=Object.fromEntries(COHORT_OPTIONS)
export default function Rewards(){
 const [wallet,setWallet]=useState<Wallet|null>(null);const [history,setHistory]=useState<Entry[]>([]);const [cursor,setCursor]=useState<number|null>(null);const [error,setError]=useState('');const [notice,setNotice]=useState('');const [busy,setBusy]=useState(false);const [offer,setOffer]=useState<Offer|null>(null);const key=useRef(crypto.randomUUID())
 async function load(){const [w,h]=await Promise.all([reviewRequest<Wallet>('/rewards/me'),reviewRequest<{items:Entry[];next_cursor:number|null}>('/rewards/history')]);setWallet(w);setHistory(h.items);setCursor(h.next_cursor)}
 useEffect(()=>{void load().catch(e=>setError(e.message))},[])
 async function visibility(){if(!wallet)return;setBusy(true);try{await reviewRequest('/rewards/visibility',{public:!wallet.public});window.dispatchEvent(new Event('ism-community-standing-change'));await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function redeem(){if(!offer)return;setBusy(true);setError('');try{const receipt=await reviewRequest<{starts_at:string;ends_at:string}>('/rewards/redeem',{catalog_id:offer.id,version:offer.version},key.current);setOffer(null);setNotice(`Pro reward saved: ${new Date(receipt.starts_at).toLocaleDateString('en-IN')} – ${new Date(receipt.ends_at).toLocaleDateString('en-IN')}.`);await load();window.dispatchEvent(new Event('ism-auth-change'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function claimQuest(questKey:string){setBusy(true);setError('');try{const res=await reviewRequest<{xp_awarded:number;points_awarded:number}>('/rewards/daily-quests/'+encodeURIComponent(questKey)+'/claim',{});setNotice(`Quest chest claimed: +${res.xp_awarded} XP and +${res.points_awarded} reward points.`);await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function buyShield(){setBusy(true);setError('');try{const res=await reviewRequest<{streak_shields:number;points:number}>('/rewards/streak-shield',{});setNotice(`1-Day Streak Shield equipped (${res.streak_shields}/2 active). Your XP and rank are unchanged.`);await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function updateCohort(cohort:string|null){setBusy(true);setError('');try{await reviewRequest('/rewards/stream-cohort',{stream_cohort:cohort});setNotice(cohort?`Comfort stream set to ${COHORT_NAMES[cohort]||cohort}.`:'Stream cohort cleared.');await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function more(){try{const h=await reviewRequest<{items:Entry[];next_cursor:number|null}>('/rewards/history?before='+cursor);setHistory(v=>[...v,...h.items]);setCursor(h.next_cursor)}catch(e){setError((e as Error).message)}}
 return <main className="mx-auto max-w-shell px-5 pb-24 pt-7">
  <header className="av-hero">
   <div className="av-hero-copy">
    <span className="cr-eyebrow">Learning rewards</span>
    <h1>Small steps. Lasting progress.</h1>
    <p>XP tracks your learning activity. Reward points unlock enabled benefits and streak shields while keeping your XP, level, and leaderboard score intact.</p>
   </div>
   <div className="av-hero-actions">
    <Link to="/board" className="cr-glass-btn cr-glass-btn--accent">Full leaderboard →</Link>
    <Link to="/games" className="cr-glass-btn">Play games</Link>
    <Link to="/community/contributors" className="cr-glass-btn">Contributors</Link>
   </div>
  </header>
  {error&&<div className="mt-4"><FlashBanner kind="error" title="Could not load rewards" message={error} onDismiss={()=>setError('')} actionLabel="Retry" onAction={()=>{setError('');void load().catch(e=>setError(e.message))}} extra={<div className="flex flex-wrap gap-2"><Link to="/login" className="finna-st-btn">Sign in</Link><Link to="/board" className="finna-st-btn">View public leaderboard →</Link></div>}/></div>}
  {notice&&<div className="mt-4"><FlashBanner kind="success" title="Reward update" message={notice} onDismiss={()=>setNotice('')}/></div>}
  {!wallet&&!error&&<div className="mt-8 flex justify-center py-10"><CatLoader size="lg" label="Loading your XP, quests & standings…"/></div>}
  {wallet&&<><div className="at-kpi-grid">{[['This month',wallet.monthly_xp.toLocaleString('en-IN')+' XP','is-teal'],['Lifetime',wallet.lifetime_xp.toLocaleString('en-IN')+' XP','is-indigo'],['Reward wallet',wallet.points.toLocaleString('en-IN')+' pts','is-amber'],['Your level','Lvl '+wallet.level+(wallet.title?' · '+wallet.title:''),'is-emerald']].map(([label,value,tone])=><div key={label} className={`at-kpi-tile ${tone}`}><span>{label}</span><strong>{value}</strong></div>)}</div>
  <div className="mt-4 grid gap-4 rounded-[16px] border border-hairline bg-card p-4 sm:grid-cols-2">
   <CatXpBar value={Math.max(0,wallet.lifetime_xp-wallet.level_floor_xp)} max={Math.max(40,wallet.next_level_xp-wallet.level_floor_xp)} tone="xp" label={`Level ${wallet.level} → Level ${wallet.level+1}`} meta={`${wallet.lifetime_xp.toLocaleString('en-IN')} / ${wallet.next_level_xp.toLocaleString('en-IN')} XP`}/>
   <CatXpBar value={wallet.daily_xp} max={Math.max(1,wallet.daily_cap)} tone="teal" label="Today’s study & game XP" meta={`${wallet.daily_xp} / ${wallet.daily_cap} XP · resets midnight IST`}/>
  </div>
 <div className="mt-6 grid gap-4 lg:grid-cols-2">
  <section aria-label="Consistency streak and league" className="ism-card-surface rounded-[14px] border border-hairline bg-card p-5">
   <div className="flex flex-wrap items-start justify-between gap-3">
    <div>
     <div className="font-mono text-xs uppercase tracking-wider text-vermilion">7-Day IST Consistency Streak</div>
     <h2 className="mt-1 font-display text-xl">🔥 {wallet.current_streak_days??0}-day streak <span className="font-mono text-xs font-normal text-muted">(Best: {wallet.longest_streak_days??0}d)</span></h2>
    </div>
    {wallet.league&&<div className="rounded-[10px] border border-exams bg-exams-soft px-3.5 py-2 text-right">
     <div className="font-mono text-xs uppercase text-exams-dark">Weekly Division</div>
     <div className="font-display text-md font-semibold text-ink">{wallet.league.name}</div>
     <div className="font-mono text-xs text-secondary">{wallet.weekly_xp??0} XP this week{wallet.league.next_xp?` · ${wallet.league.xp_to_promote} XP to promote`:''}</div>
    </div>}
   </div>
   {wallet.daily_quests?.week_strip&&<div className="mt-4 grid grid-cols-7 gap-1.5">
    {wallet.daily_quests.week_strip.map(d=><div key={d.date} className={'flex flex-col items-center rounded-[10px] border py-2.5 text-center transition-transform '+(d.active?'border-correct bg-correct-soft text-correct-dark scale-[1.02]':d.is_today?'border-exams bg-exams-soft text-exams-dark':'border-hairline bg-paper text-muted')}>
     <span className="font-mono text-xs font-semibold">{d.label}</span>
     <span className="mt-1 text-sm font-bold">{d.active?'✓':d.is_today?'•':'–'}</span>
    </div>)}
   </div>}
   <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-3 text-sm">
    <span>Streak Shields equipped: <b>{wallet.streak_shields??0} / 2</b> <span className="text-xs text-secondary">(auto-protects 1 missed IST day)</span></span>
    <button type="button" disabled={busy||(wallet.streak_shields??0)>=2||wallet.points<25} onClick={()=>void buyShield()} className={BUTTON}>Equip 1-Day Shield (25 pts)</button>
   </div>
  </section>
  <section aria-label="Today's 3-ring daily quests" className="ism-card-surface rounded-[14px] border border-hairline bg-card p-5">
   <div className="font-mono text-xs uppercase tracking-wider text-correct-dark">Daily Quest Rings · {wallet.daily_quests?.ist_date||'IST Today'}</div>
   <h2 className="mt-1 font-display text-xl">Today’s 3-Ring Quests</h2>
   <div className="mt-3 space-y-3">
    {(wallet.daily_quests?.quests||[]).map(q=>{
     const pct=Math.min(100,Math.round((q.progress/Math.max(1,q.target))*100))
     return <div key={q.key} className="rounded-[12px] border border-hairline bg-paper p-3.5 transition-colors hover:border-hairline2">
      <div className="flex flex-wrap items-center justify-between gap-2">
       <div>
        <strong className="text-sm">{q.title}</strong>
        <p className="text-xs text-secondary">{q.subtitle}</p>
       </div>
       <div className="text-right font-mono text-xs">
        <span className="text-exams-dark">{q.activity_only?'Map activity · no reward':`+${q.xp_reward} XP · +${q.points_reward} pts`}</span>
        <div className="text-muted">{q.progress} / {q.target}</div>
       </div>
      </div>
      <CatXpBar value={q.progress} max={Math.max(1,q.target)} tone={q.completed?'gold':'quest'} showCat={pct>0} className="mt-2.5"/>
      <div className="mt-2.5 flex items-center justify-between">
       <span className="font-mono text-xs text-secondary">{q.claimed?'✓ Chest claimed today':q.activity_only?'Warm-up complete · activity only':q.completed?'Ready to claim!':'In progress'}</span>
       {!q.claimed&&<button type="button" disabled={busy||!q.completed||q.reward_eligible===false} onClick={()=>void claimQuest(q.key)} className={BUTTON+(q.completed?' !bg-ink !text-paper':'')}>Claim chest</button>}
      </div>
     </div>
    })}
   </div>
  </section>
 </div>
 <section aria-label="Academic stream cohort" className="ism-card-surface mt-5 rounded-[14px] border border-hairline bg-card p-5">
  <div className="flex flex-wrap items-center justify-between gap-3">
   <div>
    <h2 className="font-display text-xl">Your Academic Stream Cohort</h2>
    <p className="mt-1 text-sm text-secondary">Declare your background stream to compare scores on cohort leaderboards and earn <b>+25 Cross-Stream Courage ⚡</b> when answering outside your comfort zone in games.</p>
   </div>
   <div className="flex flex-wrap gap-2">
    {COHORT_OPTIONS.map(([id,label])=><button key={id} type="button" disabled={busy} aria-pressed={wallet.stream_cohort===id} onClick={()=>void updateCohort(wallet.stream_cohort===id?null:id)} className={BUTTON+(wallet.stream_cohort===id?' !bg-ink !text-paper':'')}>{label}</button>)}
   </div>
  </div>
 </section>
 <section className="ism-card-surface mt-5 rounded-[14px] border border-hairline bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-display text-xl">Your leaderboard visibility</h2><p className="mt-1 text-sm text-secondary">{wallet.public?'Your handle and XP appear publicly.':'Your XP and wallet stay private. You can join the public board any time.'}</p></div><button disabled={busy} onClick={()=>void visibility()} className={BUTTON}>{wallet.public?'Keep my score private':'Join the public leaderboard'}</button></div></section>
 <section aria-label="Weekly XP standings" className="ism-card-surface mt-5 rounded-[14px] border border-hairline bg-card p-5">
  <div className="flex flex-wrap items-center justify-between gap-3">
   <div>
    <h2 className="font-display text-xl">Weekly XP leaderboard</h2>
    <p className="mt-1 text-sm text-secondary">Live standings within your division this India week.</p>
   </div>
   <Link to="/board" className={BUTTON}>All leaderboards (XP, Daily Five, Cup, Blocks) →</Link>
  </div>
  <WeeklyStandings endpoint="/rewards/leaderboard?contract=2"/>
 </section>
 <section aria-label="Your free month" className="ism-card-surface mt-5 rounded-[18px] border border-exams bg-exams-soft/65 p-5">
  <h2 className="font-display text-xl">Your free month</h2>
  <p className="mt-2 text-sm">{Math.max(0,wallet.points).toLocaleString('en-IN')} / {(wallet.catalog.find(o=>o.id==='pro-month')?.points||1500).toLocaleString('en-IN')} points toward 30 Pro days</p>
  <progress aria-label="Points toward your free month" value={Math.max(0,wallet.points)} max={wallet.catalog.find(o=>o.id==='pro-month')?.points||1500} className="mt-3 h-3 w-full accent-correct"/>
  <p className="mt-2 text-sm text-secondary">Earn through regular study across different activities. Redemption opens after the launch checklist is complete.</p>
 </section>
 {wallet.point_budget&&<section aria-label="Today's study points" className="ism-card-surface mt-5 rounded-[18px] border border-hairline bg-card p-5">
  <h2 className="font-display text-xl">Today’s study points · {wallet.point_budget.earned} / {wallet.point_budget.cap}</h2>
  <p className="mt-2 text-sm text-secondary">{wallet.point_budget.remaining} points remaining today. Activity limits share this total. XP keeps earning up to 300 per India day; reviewed contributions have a separate points budget.</p>
  <div className="mt-3 flex flex-wrap gap-2">{wallet.point_budget.pillars.map(p=><span key={p.key} className="rounded-pill border border-hairline px-3 py-2 text-xs">{({learn:'Discovery',revise:'Smart Review',prove:'Mocks',play:'Games',daily:'Daily Five',habit:'Quest rings'} as Record<string,string>)[p.key]} · {p.earned} / {p.cap}</span>)}</div>
 </section>}
 <section className="mt-7"><h2 className="font-display text-xl">Turn effort into access</h2><p className="mt-2 text-sm text-secondary">One subscription reward every 30 days. Access starts after existing trial or reward access. Active paid subscriptions must finish before redemption, to avoid overlapping renewals. Reward access never starts a paid renewal.</p><div className="mt-4 grid gap-4 sm:grid-cols-2">{wallet.catalog.map(o=><article key={o.id} className="ism-card-surface rounded-[14px] border border-exams bg-exams-soft/65 p-5"><div className="font-mono text-xs uppercase text-exams-dark">Earned benefit</div><h3 className="mt-2 font-display text-xl">{o.title}</h3><p className="mt-2 text-base font-semibold">{o.points.toLocaleString('en-IN')} reward points</p><p className="mt-2 text-sm text-secondary">{o.enabled?'Available with enough earned points.':'Redemption opens after paid checkout launches and the reward checks pass.'}</p><button disabled={busy||!o.enabled||wallet.points<o.points} onClick={()=>{key.current=crypto.randomUUID();setOffer(o)}} className={BUTTON+' mt-4'}>{o.enabled?'Review redemption':'Not open yet'}</button></article>)}</div>{wallet.redemptions.map(r=><p key={r.id} className="mt-3 text-sm">Saved Pro reward · {new Date(r.starts_at).toLocaleDateString('en-IN')} – {new Date(r.ends_at).toLocaleDateString('en-IN')}</p>)}</section>
 {offer&&<section aria-label="Confirm reward redemption" className="mt-5 rounded-[12px] border border-ink bg-card p-5"><h2 className="font-display text-xl">Redeem {offer.title}?</h2><p className="mt-2 text-sm">Spend {offer.points} points from your {wallet.points}-point wallet. Your XP and ranking remain unchanged.</p><div className="mt-4 flex gap-3"><button disabled={busy} onClick={()=>void redeem()} className={BUTTON}>Confirm redemption</button><button disabled={busy} onClick={()=>setOffer(null)} className={BUTTON}>Cancel</button></div></section>}
 <section className="mt-7"><h2 className="font-display text-xl">How you earn</h2><ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-secondary"><li>First correct answer to a unique verified-key question: 10 XP and 1 reward point, up to 12 discovery points per India day. All study points share a 25-point daily limit; XP has its own 300 daily limit.</li><li>Daily rings reward warm-up, clearing 8 due review items and completing your fixed daily plan. Quest rings share a 10-point daily limit. Quest XP shares the 300 XP daily cap.</li><li>Completed Smart Review sets can earn 20 XP and 2 points: at least 8 due items, 60% correct and 3 seconds per checked item, at most twice per India day (4 review points). Daily point limits can reduce the points in a receipt. Review items pay no individual question reward. The same discovery question pays once across exam practice and mocks. Guests, repeated answers, unverified keys and late mocks earn no question rewards.</li><li>Published bank contributions earn 20 XP and 5 points after independent review and live verification. Answer-key or source fixes with two qualifying reviews earn 40 XP and 10 points. At most 3 credits per India day, outside the study-points cap; reversals negate the original reward. Votes and self-publication earn nothing.</li><li>First independently reviewed material publication: 20 XP and 5 points, at most one publication reward per day. Self-published materials and paid demos earn none; archiving reverses the reward.</li><li>Completed games earn 15 XP and up to 2 points at 60% of the frozen eligible question set correct, with at least 3 seconds per answered item. Games share 4 points daily. A timed Daily Five completion earns 10 XP and 1 point, once per day. These completion bonuses are separate from discovery.</li><li>Fully answered, frozen verified mocks submitted on time earn 30 XP and up to 3 points, sharing 3 mock points daily. Server time must allow at least 3 seconds per question on average.</li><li>A topic reaching proficient earns 30 XP and up to 3 points; mastered earns 60 XP and up to 5. Each topic-tier pays once, inside the 25-point study cap. Existing tiers and background corrections earn no retroactive reward.</li></ul></section>
 <section className="mt-7"><h2 className="font-display text-xl">Point history</h2>{history.length?history.map(h=><article key={h.id} className="mt-2 flex flex-wrap justify-between gap-3 rounded-[10px] border border-hairline bg-card p-4 text-sm"><div><strong>{h.note}</strong><p className="mt-1 text-xs text-muted">{new Date(h.created_at).toLocaleString('en-IN')}</p></div><span>{h.xp>0?'+':''}{h.xp} XP · {h.points>0?'+':''}{h.points} points</span></article>):<p className="mt-3 text-sm text-secondary">No rewards earned yet. Start with verified-key practice in an exam.</p>}{cursor&&<button onClick={()=>void more()} className={BUTTON+' mt-3'}>Older activity</button>}</section></>}
 </main>
}
export function LearningBoard(){return <main className="at-sub-page">
 <header className="av-hero">
  <div className="av-hero-copy">
   <span className="cr-eyebrow">Learning together</span>
   <h1>Weekly learning board</h1>
   <p>Weekly XP within your league. See the top ten and learners near your rank. Spending reward points keeps your XP intact.</p>
  </div>
  <div className="av-hero-actions">
   <Link to="/games" className="cr-glass-btn cr-glass-btn--accent">Game boards →</Link>
   <Link to="/profile/rewards" className="cr-glass-btn">My points & visibility</Link>
  </div>
 </header>
 <section className="at-card"><WeeklyStandings endpoint="/rewards/leaderboard?contract=2"/></section>
 </main>}
export function RewardAdmin(){const [offers,setOffers]=useState<Offer[]>([]);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [gates,setGates]=useState<RewardLaunchGates|null>(null);useEffect(()=>{Promise.all([reviewRequest<Offer[]>('/admin/bank/rewards'),reviewRequest<RewardLaunchGates>('/admin/bank/reward-feature-gates')]).then(([o,g])=>{setOffers(o);setGates(g)}).catch(e=>setError(e.message))},[]);async function save(o:Offer){const reason=window.prompt('Explain this reward-policy change (10 characters minimum)');if(!reason)return;setBusy(true);try{await reviewRequest('/admin/bank/rewards/'+o.id,{version:o.version,points:o.points,enabled:o.enabled,reason});setOffers(await reviewRequest<Offer[]>('/admin/bank/rewards'));setError('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}return <section className="mt-5"><p className="text-sm text-secondary">Review earning caps and subscription costs before opening redemption. Changes are versioned and audited. Disabling an offer preserves existing redeemed access.</p>{error&&<p role="alert" className="mt-3 text-mypick">{error}</p>}<RewardFeatureGates gates={gates}/>{offers.map(o=><div key={o.id} className="mt-4 rounded-[8px] border border-hairline bg-card p-5"><h2 className="font-display text-xl">{o.title}</h2><label className="mt-3 block text-sm">Reward-point cost<input type="number" min={1} max={1000000} value={o.points} onChange={e=>setOffers(v=>v.map(x=>x.id===o.id?{...x,points:Number(e.target.value)}:x))} className="ml-3 min-h-11 rounded-[6px] border border-hairline p-2"/></label><label className="mt-3 flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" disabled={!o.enabled&&!gates?.catalog_ready} checked={o.enabled} onChange={e=>setOffers(v=>v.map(x=>x.id===o.id?{...x,enabled:e.target.checked}:x))}/>Enable redemption</label><button disabled={busy} onClick={()=>void save(o)} className={BUTTON+' mt-3'}>Save reviewed policy</button></div>)}<BillingAccessAdmin/><RewardDiagnostics/></section>}
