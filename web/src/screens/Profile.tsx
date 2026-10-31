import {UserAvatar} from '../components/AvatarArt'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { changePassword, getProfile, logoutAccount, updateProfile, type PrivateProfile } from '../lib/api'

import {getScoreSummary,type ScoreSummary} from '../lib/api'
import {reviewRequest} from '../lib/review'

type Tab = 'Activity' | 'MCQs' | 'Points' | 'Answers' | 'Materials'

function initials(name: string) {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'S'
}

function Stat({ value, label }: { value: string | number; label: string }) {
  return <div className="rounded-[14px] border border-hairline bg-card px-[18px] py-4 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
    <div className="font-display text-[32px] leading-none">{value}</div>
    <div className="mt-1.5 text-[13px] text-secondary">{label}</div>
  </div>
}

export default function Profile() {
  const [profile, setProfile] = useState<PrivateProfile | null>(null)
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [editing, setEditing] = useState(false)
  const [scoreSummary,setScoreSummary]=useState<ScoreSummary|null>(null)
  const [credit,setCredit]=useState<number|null>(null)
  const [creditError,setCreditError]=useState('')
  const [tab, setTab] = useState<Tab>('Activity')
  const [passwords,setPasswords]=useState({current:'',next:''})
  const [passwordNotice,setPasswordNotice]=useState('')

  useEffect(() => {
    let live = true
    getScoreSummary().then(data=>{if(live)setScoreSummary(data)}).catch(()=>{})
    getProfile().then((data) => { if (live) { setProfile(data); setName(data.name ?? '') } })
      .catch((e) => live && setError(e.message || 'Could not load your profile.'))
      .finally(() => live && setLoading(false))
    return () => { live = false }
  }, [])

  useEffect(()=>{if(tab!=='Points'||profile?.account_type!=='account')return;let live=true;reviewRequest<{credit:number}>('/contributions/summary').then(r=>{if(live)setCredit(r.credit)}).catch(e=>{if(live)setCreditError(e.message)});return()=>{live=false}},[tab,profile?.account_type])

  const saveName = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true); setError(''); setSaved(false)
    try { const updated = await updateProfile(name); setProfile(updated); setName(updated.name ?? ''); setSaved(true); setEditing(false) }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not save your profile.') }
    finally { setSaving(false) }
  }
  const savePassword=async(event:FormEvent)=>{event.preventDefault();setPasswordNotice('');try{await changePassword(passwords.current,passwords.next);setPasswords({current:'',next:''});window.dispatchEvent(new Event('ism-auth-change'));window.dispatchEvent(new CustomEvent('ism-account-notice',{detail:'Password updated. Other sessions have been signed out.'}))}catch(e){setPasswordNotice(e instanceof Error?e.message:'Could not update password.')}}

  const activity = useMemo(() => {
    const byDay = new Map(profile?.progress.daily_activity.map((d) => [d.day, d]) ?? [])
    const today = new Date()
    return Array.from({ length: 30 }, (_, i) => {
      const date = new Date(today)
      date.setDate(today.getDate() - i)
      const day = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      return { ...(byDay.get(day) ?? { answered: 0, correct: 0 }), day }
    }).filter((d) => d.answered > 0)
  }, [profile])

  const p = profile?.progress
  const todayKey = new Date().toLocaleDateString('en-CA')
  const todayAnswered = p?.daily_activity.find((day) => day.day === todayKey)?.answered ?? 0
  const subjects = p?.subjects ?? []
  const activeTab: Tab[] = ['Activity', 'MCQs', 'Points', 'Answers', 'Materials']

  return <main className="mx-auto max-w-[1240px] px-6 pb-24 pt-7">
    {error && <div role="alert" className="mb-4 rounded-[10px] border border-wrong bg-wrong-soft p-3 text-[13px] text-wrong-dark">{error}</div>}
    {loading && <div className="rounded-[14px] border border-hairline bg-card p-6 text-[14px] text-secondary">Loading your profile…</div>}
    {!loading && !profile && <div className="rounded-[14px] border border-hairline bg-card p-6 text-[14px] text-secondary">Your profile could not be loaded. Please refresh to try again.</div>}
    {profile && <>
      <Link to="/creators/settings" className="mb-4 inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 text-[13px] font-semibold text-link">Creator profile, following & visibility →</Link>
      <section className="flex flex-wrap items-center gap-6 rounded-[14px] border border-hairline bg-card p-6 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
        <div className="flex flex-col items-center gap-1.5">
          <UserAvatar look={profile.avatar} initials={initials(profile.name || profile.handle)} size={104}/>
          <Link to="/avatar" className="inline-flex min-h-11 items-center text-[12px] font-semibold text-rewards-dark underline">Edit avatar</Link>
        </div>
        <div className="min-w-[260px] flex-1">
          <h1 className="font-display text-[clamp(32px,4vw,44px)] font-medium leading-tight -tracking-[0.02em]">{profile.name || 'Set your display name'}</h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[14px] text-secondary">
            <span className="font-mono text-[13px]">@{profile.handle}</span><span>{profile.account_type==='account'?profile.email:'Guest profile · stored on this browser'}</span>
            <span className="rounded-pill border border-rewards-dark bg-rewards-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.06em] text-rewards-dark">Level {profile.level}</span>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3"><span className="grid h-[38px] w-[38px] place-items-center rounded-[10px] bg-rewards-dark font-display text-[20px] text-white">{profile.level}</span><span><span className="block text-[14px] font-semibold">Level {profile.level} · Learner</span><span className="block font-mono text-[11px] text-muted">Your study progress, kept private</span></span></div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setEditing((v) => !v)} className="rounded-pill border border-ink px-[18px] py-2 text-[14px] font-semibold hover:bg-paper">{editing ? 'Close editor' : 'Edit profile'}</button>
          <Link to="/account/security" className="rounded-pill border border-hairline2 px-[18px] py-2 text-[14px] text-link">Account security</Link>
          <Link to="/contribute" className="rounded-pill border border-hairline2 px-[18px] py-2 text-[14px] text-link">My contributions →</Link>
          {profile.account_type==='account'?<><Link to="/billing" className="rounded-pill border border-ink px-[18px] py-2 text-[14px] font-semibold">Plan & billing</Link><button type="button" onClick={()=>void logoutAccount().then(()=>{window.dispatchEvent(new Event('ism-auth-change'));window.location.assign('/')})} className="rounded-pill border border-hairline2 px-[18px] py-2 text-[14px]">Sign out</button></>:<Link to="/join" className="rounded-pill bg-ink px-[18px] py-2 text-[14px] font-semibold text-white">Join free · sync progress</Link>}
        </div>
      </section>

      {profile.account_type==='account'&&<section className="mt-3 rounded-[14px] border border-hairline bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-[.1em] text-muted">Your plan</div><h2 className="mt-1 font-display text-[21px] capitalize">{profile.plan_code} · {profile.plan_status}</h2>{profile.trial_ends_at&&profile.plan_status==='trial'&&<p className="text-[12px] text-secondary">Trial ends {new Date(profile.trial_ends_at).toLocaleDateString('en-IN')} · no automatic charge</p>}</div><Link to="/plans" className="rounded-pill border border-ink px-4 py-2 text-[13px] font-semibold">View plans</Link></div><form onSubmit={savePassword} className="mt-4 grid gap-3 border-t border-hairline pt-4 sm:grid-cols-[1fr_1fr_auto]"><label className="text-[12px] font-semibold">Current password<input required type="password" autoComplete="current-password" value={passwords.current} onChange={e=>setPasswords({...passwords,current:e.target.value})} className="mt-1 h-10 w-full rounded-[8px] border border-hairline bg-paper px-3"/></label><label className="text-[12px] font-semibold">New password<input required minLength={12} type="password" autoComplete="new-password" value={passwords.next} onChange={e=>setPasswords({...passwords,next:e.target.value})} className="mt-1 h-10 w-full rounded-[8px] border border-hairline bg-paper px-3"/></label><button className="self-end rounded-pill border border-ink px-4 py-2 text-[12px] font-semibold">Change password</button></form>{passwordNotice&&<p role="status" className="mt-2 text-[12px] text-secondary">{passwordNotice}</p>}</section>}

      {editing && <form onSubmit={(event) => void saveName(event)} className="mt-3 flex flex-wrap items-end gap-3 rounded-[14px] border border-hairline bg-card p-4">
        <div className="min-w-[220px] flex-1"><label htmlFor="profile-name" className="text-[13px] font-semibold">Display name</label><input id="profile-name" value={name} onChange={(event) => { setName(event.target.value); setSaved(false) }} maxLength={60} autoComplete="nickname" placeholder="Your display name" className="mt-1.5 h-11 w-full rounded-[8px] border border-hairline bg-paper px-3 text-[14px] outline-none focus:border-ink" /><p className="mt-1 text-[11px] text-muted">Optional · up to 60 characters · saved with your profile</p></div>
        <button disabled={saving || name === (profile.name ?? '')} className="rounded-pill bg-ink px-5 py-2.5 text-[13px] font-semibold text-paper disabled:opacity-50">{saving ? 'Saving…' : 'Save profile'}</button>{saved && <span role="status" className="text-[12px] text-correct-dark">Saved</span>}
      </form>}

      <div className="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
        <Stat value={p?.answered.toLocaleString('en-IN') ?? 0} label="Questions answered" />
        <Stat value={`${p?.accuracy ?? 0}%`} label="Accuracy" />
        <Stat value={p?.unique_questions.toLocaleString('en-IN') ?? 0} label="Unique questions" />
        <Stat value={p?.correct.toLocaleString('en-IN') ?? 0} label="Correct answers" />
        <Stat value={`${p?.active_days_30 ?? 0}`} label="Active days · 30d" />
        <Stat value={`${p?.current_streak ?? 0}`} label="Day streak" />
      </div>

      <nav aria-label="Profile sections" className="mt-4 flex gap-1 overflow-x-auto rounded-pill border border-hairline bg-card p-1">
        {activeTab.map((item) => <button key={item} type="button" onClick={() => setTab(item)} aria-current={tab === item ? 'page' : undefined} className={`shrink-0 rounded-pill px-4 py-2 text-[14px] font-semibold ${tab === item ? 'bg-ink text-white' : 'text-secondary hover:bg-paper'}`}>{item}</button>)}
      </nav>

      <div className="mt-2 flex flex-wrap items-start gap-x-10">
        <section className="min-w-0 flex-[999_1_520px]">
          {tab === 'Activity' ? <>
            <div className="border-b border-ink py-[18px] pb-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2"><h2 className="font-display text-[24px] font-medium">Today</h2><span className="font-mono text-[13px]"><b>{todayAnswered}</b> practice answers recorded</span></div>
              <p className="mt-2 text-[12px] text-muted">Practice history is recorded below. Reviewed publication credit appears in Points and My contributions.</p>
            </div>
            <div className="flex flex-wrap gap-2 border-b border-hairline2 py-3"><span className="rounded-pill bg-practice-soft px-3 py-1 text-[12px] font-semibold text-practice-dark">Question practice</span><span className="rounded-pill bg-paper px-3 py-1 text-[12px] font-semibold text-secondary">Personal progress</span></div>
            {activity.length ? activity.map((d) => <div key={d.day} className="grid grid-cols-[84px_96px_minmax(0,1fr)_56px] items-center gap-3 border-b border-hairline2 py-3">
              <span className="font-mono text-[11px] text-muted">{d.day === new Date().toLocaleDateString('en-CA') ? 'Today' : new Date(`${d.day}T12:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
              <span className="justify-self-start rounded-pill bg-practice-soft px-2 py-1 font-mono text-[10px] uppercase tracking-[.06em] text-practice-dark">Practice</span>
              <span className="text-[14px] leading-relaxed">Answered {d.answered} questions · {d.correct} correct</span><span className="text-right font-mono text-[13px] font-medium text-practice-dark">{d.answered}</span>
            </div>) : <div className="py-8 text-[14px] leading-relaxed text-secondary">No practice activity yet. Answer a question to start building your study history. <Link to="/bank" className="font-semibold text-link underline">Open the question bank</Link></div>}
            {!!p?.collections.length && <section className="mt-8"><div className="flex items-baseline justify-between border-b border-hairline pb-3"><div><h2 className="font-display text-[24px] font-medium">Progress by module</h2><p className="mt-1 text-[12px] text-muted">One answer history, grouped by where you studied.</p></div><span className="label">{p.collections.length} modules</span></div><div className="mt-3 grid gap-3 sm:grid-cols-2">{p.collections.filter((item)=>item.scope_id!=='general').map((item)=><Link key={item.scope_id} to={`/exams/${item.scope_id}?view=progress`} className="rounded-[12px] border border-hairline bg-card p-4 transition-shadow hover:shadow-[0_5px_16px_rgba(29,27,24,.08)]"><div className="flex items-start justify-between gap-3"><h3 className="font-display text-[18px] font-medium">{item.label}</h3><span className="font-mono text-[13px] font-semibold">{item.accuracy}%</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-[#E8DFCC]"><div className="h-full rounded-pill bg-exams" style={{width:`${item.accuracy}%`}} /></div><div className="mt-2 text-[12px] text-secondary">{item.answered} answers · {item.unique_questions} unique · {item.correct} correct</div><span className="mt-2 inline-block text-[12px] font-semibold text-link">Open module progress →</span></Link>)}</div></section>}
          </> : tab==='Points'?<section className="mt-4 rounded-[10px] border border-hairline bg-card p-6"><Link to="/rewards" className="mb-5 block rounded-[8px] bg-[#FFF6DD] p-4 text-[14px] font-semibold text-link">Open learning XP, reward wallet and subscription rewards →</Link><h2 className="font-display text-[24px]">Contribution credit</h2>{profile.account_type!=='account'?<p className="mt-3 text-[14px]">Sign in to contribute and earn publication credit.</p>:creditError?<p role="alert" className="mt-3 text-[14px] text-mypick">{creditError}</p>:credit===null?<p className="mt-3 text-[14px] text-secondary">Loading publication credit…</p>:<div className="mt-3 font-display text-[40px]">{credit.toLocaleString('en-IN')}</div>}<p className="mt-2 text-[13px] text-secondary">25 for a published new MCQ, 10 for a published improvement. Reversals adjust the total. Helpful votes do not award credit.</p><div className="mt-4 flex gap-4 text-[13px] font-semibold text-link"><Link to="/contribute" className="underline">My contributions →</Link><Link to="/community/contributors" className="underline">Contributor leaderboard</Link></div></section>:tab==='Materials'?<section className="mt-4 rounded-[10px] border border-hairline bg-card p-6"><h2 className="font-display text-[24px]">Your content studio</h2><p className="mt-3 text-[14px] text-secondary">Create and revise your materials, track CMS review, and open published lessons.</p><div className="mt-4 flex flex-wrap gap-4 text-[13px] font-semibold text-link"><Link to="/studio" className="min-h-11 underline">My drafts & publications →</Link><Link to="/materials?saved=true" className="min-h-11 underline">Saved materials →</Link></div></section>: <div className="mt-4 rounded-[10px] border border-hairline bg-card p-6"><h2 className="font-display text-[24px] font-medium">{tab}</h2><p className="mt-2 text-[14px] leading-relaxed text-secondary">This part of the v3 profile is mapped for the next build phase. It will show your {tab.toLowerCase()} here when those records are available.</p></div>}
          {scoreSummary&&<section className="mt-5 rounded-[10px] border border-hairline bg-card p-4"><h3 className="font-display text-[21px]">Score history</h3><p className="mt-2 text-[12px] leading-relaxed text-secondary">{scoreSummary.profile_basis}</p><p className="mt-3 text-[13px]">{scoreSummary.mocks_original.completed} completed mocks · {scoreSummary.mocks_original.original_marks} recorded original marks</p><p className="mt-2 text-[13px]">Practice reassessments: {scoreSummary.practice_adjusted.assessed} of {scoreSummary.practice_adjusted.total} attempts · {scoreSummary.practice_adjusted.correct} correct · {scoreSummary.practice_adjusted.wrong} wrong · {scoreSummary.practice_adjusted.excluded} excluded</p><Link to="/exams" className="mt-3 inline-block text-[13px] font-semibold text-link underline">Open saved mock results →</Link></section>}
          <p className="mt-4 text-[11px] leading-relaxed text-muted">{profile.account_type==='account'?'Your account profile and study progress are private. Community visibility is controlled separately.':'Guest progress is stored on this browser. Join free to sync your study history across devices.'}</p>
        </section>

        <aside className="min-w-0 flex-[1_1_280px] lg:max-w-[360px]">
          <section className="mt-[18px] rounded-[8px] bg-map-soft p-4">
            <div className="flex items-center justify-between gap-2"><span className="font-mono text-[11px] uppercase tracking-[.08em] text-map-dark">Study desk</span><span className="rounded-pill bg-paper px-2 py-1 font-mono text-[10px] uppercase tracking-[.06em] text-map-dark">Private until you join</span></div>
            <h2 className="mt-2 font-display text-[20px] font-medium">Study with others</h2>
              <p className="mt-2 text-[13px] leading-relaxed text-[#24494C]">Invite people you know to a private desk, or accept their invitation. Your profile and progress stay private unless you choose to share them.</p>
            <Link to="/desk" className="mt-3 inline-flex rounded-pill bg-map px-4 py-2 text-[13px] font-semibold text-paper">Open your study desk</Link>
          </section>
          <div className="border-b border-ink py-[18px] pb-2 font-mono text-[11px] uppercase tracking-[.1em] text-muted">Accuracy by subject</div>
          {!subjects.length ? <p className="py-3 text-[13px] leading-relaxed text-secondary">Subject results will appear as you practise questions with approved subject tags.</p> : subjects.slice(0, 8).map((s) => { const pct = s.answered ? Math.round(s.correct / s.answered * 100) : 0; return <Link key={s.subject_id} to={`/library/subjects/${encodeURIComponent(s.subject_id)}`} className="block border-b border-hairline2 py-2.5 hover:bg-card"><div className="flex justify-between gap-2 text-[14px]"><span>{s.subject}</span><span className="font-mono text-[12px]">{pct}%</span></div><div className="mt-2 h-1 overflow-hidden bg-[#E2D9C6]"><div className="h-full bg-practice" style={{ width: `${pct}%` }} /></div></Link> })}
          <div className="mt-6 border-b border-ink pb-2 font-mono text-[11px] uppercase tracking-[.1em] text-muted">Your study shortcuts</div>
          <div className="divide-y divide-hairline2">{[['XP & reward points', '/rewards'], ['Learning leaderboard', '/board'], ['Study library', '/library'], ['Study desk', '/desk'], ['Mistakes review', '/mistakes'], ['Exams', '/exams'], ['Question source archive', '/bank']].map(([label, href]) => <Link key={href} to={href} className="flex justify-between py-3 text-[14px] hover:text-link"><span>{label}</span><span aria-hidden="true">↗</span></Link>)}</div>
        </aside>
      </div>
    </>}
  </main>
}
