import RewardDiagnostics from '../components/RewardDiagnostics'
import {UserAvatar} from '../components/AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import {useEffect,useRef,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
interface Offer{id:string;title:string;points:number;pro_days:number;enabled:boolean;version:number}
interface DailyQuest{key:string;title:string;subtitle:string;progress:number;target:number;completed:boolean;claimed:boolean;xp_reward:number;points_reward:number}
interface WeekDay{date:string;label:string;active:boolean;is_today:boolean}
interface Wallet{
 lifetime_xp:number;monthly_xp:number;weekly_xp?:number;level_floor_xp:number;daily_remaining:number;resets_at:string;daily_xp:number;daily_cap:number;points:number;level:number;title?:string;
 league?:{id:string;name:string;floor_xp:number;next_xp:number|null;xp_to_promote:number};
 stream_cohort?:string|null;current_streak_days?:number;longest_streak_days?:number;streak_shields?:number;last_active_ist_date?:string|null;
 daily_quests?:{ist_date:string;quests:DailyQuest[];week_strip:WeekDay[]};
 next_level_xp:number;public:boolean;catalog:Offer[];redemptions:{id:string;starts_at:string;ends_at:string}[]
}
interface Entry{id:number;kind:string;xp:number;points:number;note:string;created_at:string}
const BUTTON='inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 text-[13px] font-semibold disabled:opacity-40'
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
 async function visibility(){if(!wallet)return;setBusy(true);try{await reviewRequest('/rewards/visibility',{public:!wallet.public});await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function redeem(){if(!offer)return;setBusy(true);setError('');try{const receipt=await reviewRequest<{starts_at:string;ends_at:string}>('/rewards/redeem',{catalog_id:offer.id,version:offer.version},key.current);setOffer(null);setNotice(`Pro reward saved: ${new Date(receipt.starts_at).toLocaleDateString('en-IN')} – ${new Date(receipt.ends_at).toLocaleDateString('en-IN')}.`);await load();window.dispatchEvent(new Event('ism-auth-change'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function claimQuest(questKey:string){setBusy(true);setError('');try{const res=await reviewRequest<{xp_awarded:number;points_awarded:number}>('/rewards/daily-quests/'+encodeURIComponent(questKey)+'/claim',{});setNotice(`Quest chest claimed: +${res.xp_awarded} XP and +${res.points_awarded} reward points.`);await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function buyShield(){setBusy(true);setError('');try{const res=await reviewRequest<{streak_shields:number;points:number}>('/rewards/streak-shield',{});setNotice(`1-Day Streak Shield equipped (${res.streak_shields}/2 active). Your XP and rank are unchanged.`);await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function updateCohort(cohort:string|null){setBusy(true);setError('');try{await reviewRequest('/rewards/stream-cohort',{stream_cohort:cohort});setNotice(cohort?`Comfort stream set to ${COHORT_NAMES[cohort]||cohort}.`:'Stream cohort cleared.');await load()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function more(){try{const h=await reviewRequest<{items:Entry[];next_cursor:number|null}>('/rewards/history?before='+cursor);setHistory(v=>[...v,...h.items]);setCursor(h.next_cursor)}catch(e){setError((e as Error).message)}}
 return <main className="mx-auto max-w-shell px-6 pb-24 pt-8"><div className="font-mono text-[11px] uppercase tracking-widest text-[#8A8A12]">Learning rewards</div><h1 className="mt-2 font-display text-[42px]">Small steps. Lasting progress.</h1><p className="mt-3 max-w-[720px] text-[15px] leading-relaxed text-secondary">XP tracks your learning activity. Reward points can unlock enabled benefits and streak shields. Spending points keeps your XP, level and leaderboard score intact.</p><div className="mt-4 flex flex-wrap gap-3"><Link to="/games" className={BUTTON}>Play learning games →</Link><Link to="/exams" className={BUTTON}>Choose an exam →</Link><Link to="/board" className={BUTTON}>Learning leaderboard</Link><Link to="/community/contributors" className={BUTTON}>Contribution leaderboard</Link></div>
 {error&&<p role="alert" className="mt-4 rounded-[8px] bg-mypick-soft p-4 text-[14px]">{error} <Link to="/login" className="text-link underline">Sign in</Link> <button onClick={()=>{setError('');void load().catch(e=>setError(e.message))}} className="underline">Retry</button></p>}{notice&&<p role="status" className="mt-4 rounded-[8px] bg-practice-soft p-4">{notice}</p>}
 {wallet&&<><div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['This month',wallet.monthly_xp+' XP'],['Lifetime',wallet.lifetime_xp+' XP'],['Reward wallet',wallet.points+' points'],['Your level','Level '+wallet.level+(wallet.title?' · '+wallet.title:'')]].map(([label,value])=><div key={label} className="rounded-[12px] border border-hairline bg-card p-5"><div className="font-mono text-[10px] uppercase text-muted">{label}</div><div className="mt-2 font-display text-[26px] leading-tight">{value}</div></div>)}</div><p className="mt-3 text-[12px] text-secondary">Today’s study/game XP: {wallet.daily_xp} / {wallet.daily_cap} · resets at midnight in India. Next level at {wallet.next_level_xp} lifetime XP.</p>
 <div className="mt-6 grid gap-4 lg:grid-cols-2">
  <section aria-label="Consistency streak and league" className="rounded-[12px] border border-hairline bg-card p-5">
   <div className="flex flex-wrap items-start justify-between gap-3">
    <div>
     <div className="font-mono text-[10px] uppercase tracking-wider text-[#C0462C]">7-Day IST Consistency Streak</div>
     <h2 className="mt-1 font-display text-[26px]">🔥 {wallet.current_streak_days??0}-day streak <span className="font-mono text-[12px] font-normal text-muted">(Best: {wallet.longest_streak_days??0}d)</span></h2>
    </div>
    {wallet.league&&<div className="rounded-[8px] border border-[#D8A33A] bg-[#FBF4E6] px-3 py-1.5 text-right">
     <div className="font-mono text-[10px] uppercase text-[#9A6410]">Weekly Division</div>
     <div className="font-display text-[17px] font-semibold">{wallet.league.name}</div>
     <div className="font-mono text-[10px] text-secondary">{wallet.weekly_xp??0} XP this week{wallet.league.next_xp?` · ${wallet.league.xp_to_promote} XP to promote`:''}</div>
    </div>}
   </div>
   {wallet.daily_quests?.week_strip&&<div className="mt-4 grid grid-cols-7 gap-1.5">
    {wallet.daily_quests.week_strip.map(d=><div key={d.date} className={'flex flex-col items-center rounded-[8px] border py-2 text-center '+(d.active?'border-[#1F6E43] bg-[#EEF3E8] text-[#1F6E43]':d.is_today?'border-[#D8A33A] bg-[#FBF4E6]':'border-hairline bg-paper text-muted')}>
     <span className="font-mono text-[10px] font-semibold">{d.label}</span>
     <span className="mt-1 text-[14px]">{d.active?'✓':d.is_today?'•':'–'}</span>
    </div>)}
   </div>}
   <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-3 text-[13px]">
    <span>Streak Shields equipped: <b>{wallet.streak_shields??0} / 2</b> <span className="text-[12px] text-secondary">(auto-protects 1 missed IST day)</span></span>
    <button type="button" disabled={busy||(wallet.streak_shields??0)>=2||wallet.points<25} onClick={()=>void buyShield()} className={BUTTON}>Equip 1-Day Shield (25 pts)</button>
   </div>
  </section>
  <section aria-label="Today's 3-ring daily quests" className="rounded-[12px] border border-hairline bg-card p-5">
   <div className="font-mono text-[10px] uppercase tracking-wider text-[#1F6E43]">Daily Quest Rings · {wallet.daily_quests?.ist_date||'IST Today'}</div>
   <h2 className="mt-1 font-display text-[26px]">Today’s 3-Ring Quests</h2>
   <div className="mt-3 space-y-3">
    {(wallet.daily_quests?.quests||[]).map(q=>{
     const pct=Math.min(100,Math.round((q.progress/Math.max(1,q.target))*100))
     return <div key={q.key} className="rounded-[10px] border border-hairline bg-paper p-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
       <div>
        <strong className="text-[14px]">{q.title}</strong>
        <p className="text-[12px] text-secondary">{q.subtitle}</p>
       </div>
       <div className="text-right font-mono text-[11px]">
        <span className="text-[#9A6410]">+{q.xp_reward} XP · +{q.points_reward} pts</span>
        <div className="text-muted">{q.progress} / {q.target}</div>
       </div>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded-pill bg-ink/10">
       <div className="h-full bg-[#1F6E43] transition-all" style={{width:`${pct}%`}}/>
      </div>
      <div className="mt-2.5 flex items-center justify-between">
       <span className="font-mono text-[11px] text-secondary">{q.claimed?'✓ Chest claimed today':q.completed?'Ready to claim!':'In progress'}</span>
       {!q.claimed&&<button type="button" disabled={busy||!q.completed} onClick={()=>void claimQuest(q.key)} className={BUTTON+(q.completed?' !bg-ink !text-paper':'')}>Claim chest</button>}
      </div>
     </div>
    })}
   </div>
  </section>
 </div>
 <section aria-label="Academic stream cohort" className="mt-5 rounded-[12px] border border-hairline bg-card p-5">
  <div className="flex flex-wrap items-center justify-between gap-3">
   <div>
    <h2 className="font-display text-[24px]">Your Academic Stream Cohort</h2>
    <p className="mt-1 text-[13px] text-secondary">Declare your background stream to compare scores on cohort leaderboards and earn <b>+25 Cross-Stream Courage ⚡</b> when answering outside your comfort zone in games.</p>
   </div>
   <div className="flex flex-wrap gap-2">
    {COHORT_OPTIONS.map(([id,label])=><button key={id} type="button" disabled={busy} aria-pressed={wallet.stream_cohort===id} onClick={()=>void updateCohort(wallet.stream_cohort===id?null:id)} className={BUTTON+(wallet.stream_cohort===id?' !bg-ink !text-paper':'')}>{label}</button>)}
   </div>
  </div>
 </section>
 <section className="mt-5 rounded-[12px] border border-hairline bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-display text-[24px]">Your leaderboard visibility</h2><p className="mt-1 text-[13px] text-secondary">{wallet.public?'Your handle and XP appear publicly.':'Your XP and wallet stay private. You can join the public board any time.'}</p></div><button disabled={busy} onClick={()=>void visibility()} className={BUTTON}>{wallet.public?'Keep my score private':'Join the public leaderboard'}</button></div></section>
 <section className="mt-7"><h2 className="font-display text-[28px]">Turn effort into access</h2><p className="mt-2 text-[13px] text-secondary">One subscription reward every 30 days. Access starts after existing trial or reward access. Active paid subscriptions must finish before redemption, to avoid overlapping renewals. Reward access never starts a paid renewal.</p><div className="mt-4 grid gap-4 sm:grid-cols-2">{wallet.catalog.map(o=><article key={o.id} className="rounded-[12px] border border-[#D8A33A] bg-[#FFF6DD] p-5"><div className="font-mono text-[10px] uppercase text-muted">Earned benefit</div><h3 className="mt-2 font-display text-[27px]">{o.title}</h3><p className="mt-2 text-[16px] font-semibold">{o.points.toLocaleString('en-IN')} reward points</p><p className="mt-2 text-[13px] text-secondary">{o.enabled?'Available with enough earned points.':'Redemption is awaiting the site owner’s launch review. This cost is provisional.'}</p><button disabled={busy||!o.enabled||wallet.points<o.points} onClick={()=>{key.current=crypto.randomUUID();setOffer(o)}} className={BUTTON+' mt-4'}>{o.enabled?'Review redemption':'Not open yet'}</button></article>)}</div>{wallet.redemptions.map(r=><p key={r.id} className="mt-3 text-[13px]">Saved Pro reward · {new Date(r.starts_at).toLocaleDateString('en-IN')} – {new Date(r.ends_at).toLocaleDateString('en-IN')}</p>)}</section>
 {offer&&<section aria-label="Confirm reward redemption" className="mt-5 rounded-[12px] border border-ink bg-card p-5"><h2 className="font-display text-[24px]">Redeem {offer.title}?</h2><p className="mt-2 text-[14px]">Spend {offer.points} points from your {wallet.points}-point wallet. Your XP and ranking remain unchanged.</p><div className="mt-4 flex gap-3"><button disabled={busy} onClick={()=>void redeem()} className={BUTTON}>Confirm redemption</button><button disabled={busy} onClick={()=>setOffer(null)} className={BUTTON}>Cancel</button></div></section>}
 <section className="mt-7"><h2 className="font-display text-[27px]">How you earn</h2><ul className="mt-3 list-disc space-y-2 pl-5 text-[14px] leading-relaxed text-secondary"><li>First correct answer to a unique verified-key question: 10 XP and 1 reward point, up to 300 study/game XP per day.</li><li>Daily 3-Ring Quests (Warm-Up Circuit, Cross-Stream Triad, Mastery Closure) award bonus XP (within the 300 XP daily cap) and spendable reward points.</li><li>The same question pays once across exam practice and mocks. Guests, repeated answers, unverified keys and late mocks earn no question rewards.</li><li>Published contributions earn their reviewed credit as XP and reward points. Reversals are recorded too; votes alone earn nothing.</li><li>First independently reviewed material publication: 20 XP and 5 points, at most one publication reward per day. Self-published materials and paid demos earn none; archiving reverses the reward.</li><li>Game rewards follow the same question and daily limits as practice. There are no point wagers, cash withdrawals or bought leaderboard boosts.</li></ul></section>
 <section className="mt-7"><h2 className="font-display text-[27px]">Point history</h2>{history.length?history.map(h=><article key={h.id} className="mt-2 flex flex-wrap justify-between gap-3 rounded-[8px] border border-hairline bg-card p-4 text-[13px]"><div><strong>{h.note}</strong><p className="mt-1 text-[11px] text-muted">{new Date(h.created_at).toLocaleString('en-IN')}</p></div><span>{h.xp>0?'+':''}{h.xp} XP · {h.points>0?'+':''}{h.points} points</span></article>):<p className="mt-3 text-[14px] text-secondary">No rewards earned yet. Start with verified-key practice in an exam.</p>}{cursor&&<button onClick={()=>void more()} className={BUTTON+' mt-3'}>Older activity</button>}</section></>}
 </main>
}
export function LearningBoard(){const [period,setPeriod]=useState('month');const [cohort,setCohort]=useState('all');const [offset,setOffset]=useState(0);const [data,setData]=useState<{items:{handle:string;avatar?:AvatarLook|null;stream_cohort?:string|null;streak?:number;xp:number;rank:number}[];total:number;placement:{rank:number;xp:number}|null;period_start:string|null;period_end:string|null}|null>(null);const [error,setError]=useState('');const [retry,setRetry]=useState(0);useEffect(()=>{let live=true;setData(null);setError('');reviewRequest<typeof data>('/rewards/leaderboard?'+new URLSearchParams({period,cohort,offset:String(offset)})).then(r=>{if(live)setData(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[period,cohort,offset,retry]);return <main className="mx-auto max-w-[1000px] px-6 pb-24 pt-8"><div className="font-mono text-[11px] uppercase tracking-widest text-[#8A8A12]">Learning together</div><h1 className="mt-2 font-display text-[42px]">Leaderboard</h1><p className="mt-3 max-w-[680px] text-[15px] text-secondary">Consistent practice and published contributions, measured in XP. This board measures MPSC learning activity, including reviewed publication XP. Spending reward points does not affect standings.</p><div className="mt-5 flex flex-wrap gap-2">{[['week','This week'],['month','This month'],['all','All time']].map(([v,label])=><button key={v} aria-pressed={period===v} onClick={()=>{setPeriod(v);setOffset(0)}} className={BUTTON+(period===v?' !bg-ink !text-paper':'')}>{label}</button>)}<Link to="/games" className={BUTTON}>Game & Pillar boards →</Link><Link to="/rewards" className={BUTTON}>My points & quests →</Link><Link to="/community/contributors" className={BUTTON}>Contribution board →</Link></div><div className="mt-3 flex flex-wrap items-center gap-2"><span className="font-mono text-[11px] uppercase text-muted">Stream cohort:</span>{[['all','All Streams'],...COHORT_OPTIONS].map(([id,label])=><button key={id} type="button" aria-pressed={cohort===id} onClick={()=>{setCohort(id);setOffset(0)}} className={'min-h-9 rounded-pill border px-3 py-1 text-[12px] font-semibold '+(cohort===id?'border-[#9A6410] bg-[#F6E7C6] text-ink':'border-hairline bg-card text-secondary')}>{label}</button>)}</div>{error&&<p role="alert" className="mt-5">{error} <button onClick={()=>setRetry(n=>n+1)} className="underline">Retry</button></p>}{!data&&!error&&<p className="mt-5 text-muted">Loading standings…</p>}{data&&<><section className="mt-5 rounded-[12px] border border-hairline bg-card p-4 text-[14px]">{data.placement?<span>Your public position: <strong>#{data.placement.rank}</strong> · {data.placement.xp.toLocaleString('en-IN')} XP</span>:<span>Your score appears here after you earn XP and join the public board.</span>}{data.period_start&&data.period_end&&<p className="mt-2 text-[12px] text-secondary">{new Date(data.period_start).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} – {new Date(new Date(data.period_end).getTime()-1).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} · India time</p>}</section><div className="mt-5 overflow-hidden rounded-[12px] border border-hairline bg-card">{data.items.length?data.items.map((r,i)=><div key={r.handle+'-'+i} className="flex items-center gap-4 border-b border-hairline px-5 py-4"><span className="w-10 font-display text-[27px]">{r.rank}</span><UserAvatar look={r.avatar} initials={r.handle}/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="break-words text-[15px] font-semibold">{r.handle}</span>{r.stream_cohort&&COHORT_NAMES[r.stream_cohort]&&<span className="rounded-pill bg-ink/10 px-2 py-0.5 font-mono text-[10px] text-ink">{COHORT_NAMES[r.stream_cohort]}</span>}{(r.streak??0)>0&&<span className="rounded-pill bg-[#F6DDD3] px-2 py-0.5 font-mono text-[10px] text-[#C0462C]">🔥 {r.streak}d</span>}</div></div><span className="font-mono text-[13px]">{r.xp.toLocaleString('en-IN')} XP</span></div>):<p className="p-6 text-[14px] text-secondary">No public scores in this period yet. Earn XP and choose to join the board.</p>}</div><div className="mt-4 flex justify-between"><button disabled={offset===0} onClick={()=>setOffset(n=>Math.max(0,n-20))} className={BUTTON}>Previous</button><button disabled={offset+20>=data.total} onClick={()=>setOffset(n=>n+20)} className={BUTTON}>Next</button></div></>}<p className="mt-4 text-[12px] text-muted">Periods use Asia/Kolkata time. Equal XP shares a rank. Private accounts are excluded.</p></main>}
export function RewardAdmin(){const [offers,setOffers]=useState<Offer[]>([]);const [error,setError]=useState('');const [busy,setBusy]=useState(false);useEffect(()=>{reviewRequest<Offer[]>('/admin/bank/rewards').then(setOffers).catch(e=>setError(e.message))},[]);async function save(o:Offer){const reason=window.prompt('Explain this reward-policy change (10 characters minimum)');if(!reason)return;setBusy(true);try{await reviewRequest('/admin/bank/rewards/'+o.id,{version:o.version,points:o.points,enabled:o.enabled,reason});setOffers(await reviewRequest<Offer[]>('/admin/bank/rewards'));setError('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}return <section className="mt-5"><p className="text-[14px] text-secondary">Review earning caps and subscription costs before opening redemption. Changes are versioned and audited. Disabling an offer preserves existing redeemed access.</p>{error&&<p role="alert" className="mt-3 text-mypick">{error}</p>}{offers.map(o=><div key={o.id} className="mt-4 rounded-[8px] border border-hairline bg-card p-5"><h2 className="font-display text-[24px]">{o.title}</h2><label className="mt-3 block text-[13px]">Reward-point cost<input type="number" min={1} max={1000000} value={o.points} onChange={e=>setOffers(v=>v.map(x=>x.id===o.id?{...x,points:Number(e.target.value)}:x))} className="ml-3 min-h-11 rounded-[6px] border border-hairline p-2"/></label><label className="mt-3 flex min-h-11 items-center gap-2 text-[13px]"><input type="checkbox" checked={o.enabled} onChange={e=>setOffers(v=>v.map(x=>x.id===o.id?{...x,enabled:e.target.checked}:x))}/>Enable redemption</label><button disabled={busy} onClick={()=>void save(o)} className={BUTTON+' mt-3'}>Save reviewed policy</button></div>)}<RewardDiagnostics/></section>}
