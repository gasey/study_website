import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../components/ui'
import { getModerationQueue, reviewModerationPost, decideModerationAppeal, undoModerationAction, type ModerationAction, type ModerationItem, type ModerationQueue, type ModerationTab } from '../lib/api'

const TABS: { id: ModerationTab; label: string; count: (q: ModerationQueue) => number }[] = [
  { id: 'Reported', label: 'Reported', count: (q) => q.counts.open_reports },
  { id: 'New users', label: 'New users', count: (q) => q.counts.pending_posts },
  { id: 'Appeals', label: 'Appeals', count: (q) => q.counts.open_appeals },
  { id: 'My actions', label: 'My actions', count: (q) => q.counts.handled_today },
]

export default function Moderation() {
  const [token, setToken] = useState(() => sessionStorage.getItem('ism-admin-token') ?? '')
  const [candidate, setCandidate] = useState('')
  const [tab, setTab] = useState<ModerationTab>('Reported')
  const [queue, setQueue] = useState<ModerationQueue | null>(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [reload, setReload] = useState(0)

  const load = useCallback(async (auth: string, selected: ModerationTab) => {
    setLoading(true); setError(''); setMessage('')
    try { setQueue(await getModerationQueue(auth, selected)) }
    catch (err) {
      const status = (err as { status?: number })?.status
      if (status === 401) { sessionStorage.removeItem('ism-admin-token'); setToken('') }
      setError(status === 503 ? 'Admin access is not configured on the API server.' : status === 401 ? 'That admin token was not accepted.' : 'Could not load the moderation queue. Try again.')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { if (token) void load(token, tab) }, [token, tab, reload, load])

  const unlock = async (event: FormEvent) => {
    event.preventDefault()
    const next = candidate.trim()
    if (!next) return
    sessionStorage.setItem('ism-admin-token', next)
    setToken(next)
    setCandidate('')
  }

  const act = async (item: ModerationItem, action: ModerationAction) => {
    const note = notes[item.id]?.trim() ?? ''
    if (['reject', 'hide', 'deny_appeal'].includes(action) && !note) {
      setError('Add a short reason before rejecting, hiding, or denying an appeal.')
      return
    }
    if (!token || busy) return
    setBusy(item.id); setError(''); setMessage('')
    try {
      if (item.item_type === 'appeal' && item.appeal_id !== null) await decideModerationAppeal(token, item.appeal_id, action, note)
      else if (item.item_type !== 'action' && item.post_id !== null) await reviewModerationPost(token, item.post_id, action, note)
      else return
      setMessage(actionMessage(action)); setReload((n) => n + 1)
    } catch (err) { setError(err instanceof Error ? err.message : 'Action could not be saved.') }
    finally { setBusy(null) }
  }

  const undo = async (item: ModerationItem) => {
    if (!token || item.action_id === null || busy) return
    setBusy(item.id); setError(''); setMessage('')
    try { await undoModerationAction(token, item.action_id); setMessage('Action undone and logged.'); setReload((n) => n + 1) }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not undo that action.') }
    finally { setBusy(null) }
  }

  return <main className="mx-auto max-w-shell px-4 pb-24 pt-7 sm:px-6 sm:pt-8">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl"><div className="flex items-center gap-2 text-[13px] font-semibold text-community-dark"><i className="h-2 w-2 rounded-full bg-community"/>Community · Moderator</div><h1 className="mt-1 font-display text-[clamp(34px,5vw,48px)] font-medium leading-tight -tracking-[.02em]">Moderation</h1><p className="mt-2 text-[15px] leading-relaxed text-secondary">Review conduct reports and first posts. Question errors belong in the bank review flow. Actions are logged and can be undone; appeals require a different moderator.</p></div>
      <div className="flex flex-wrap gap-1.5"><span className="rounded-pill bg-community-soft px-3 py-1.5 text-[12px] font-semibold text-community-dark">Site-wide moderation</span><span className="rounded-pill bg-[#F1EBDF] px-3 py-1.5 text-[12px] font-semibold text-secondary">Owner access</span></div>
    </div>

    {!token ? <Card className="mt-6 max-w-xl p-5 sm:p-6"><div className="label text-community-dark">Private admin access</div><h2 className="mt-2 font-display text-[22px] font-medium">Enter the site admin token</h2><p className="mt-1 text-[13px] leading-relaxed text-secondary">This is separate from your study-device ID. The token stays in this browser tab session and is sent only to the India Study Map API.</p><form className="mt-4 flex flex-wrap gap-2" onSubmit={unlock}><label className="sr-only" htmlFor="admin-token">Admin token</label><input id="admin-token" autoComplete="current-password" type="password" value={candidate} onChange={(e) => setCandidate(e.target.value)} className="h-11 min-w-0 flex-1 rounded-panel border border-hairline bg-paper px-3 text-[14px]" placeholder="Admin token"/><button className="min-h-11 rounded-pill bg-ink px-4 py-2 text-[13px] font-semibold text-paper">Unlock queue</button></form>{error && <p role="alert" className="mt-3 text-[13px] text-wrong-dark">{error}</p>}</Card> : <>
      {queue && <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-4">{[
        { value: queue.counts.open_reports, label: 'open reports' }, { value: queue.counts.pending_posts, label: 'posts awaiting review' }, { value: queue.counts.open_appeals, label: 'open appeals' }, { value: queue.counts.handled_today, label: 'handled by you today' },
      ].map((item) => <Card key={item.label} className="p-3.5 sm:px-4"><div className="font-display text-[28px] leading-none">{item.value}</div><div className="mt-1.5 text-[12px] text-secondary">{item.label}</div></Card>)}</div>}

      <div className="mt-4 flex gap-1 overflow-x-auto rounded-pill border border-hairline bg-card p-1" role="tablist" aria-label="Moderation queues">{TABS.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => setTab(item.id)} className={`flex min-h-10 shrink-0 items-center gap-2 rounded-pill px-4 py-2 text-[14px] font-semibold ${tab === item.id ? 'bg-ink text-white' : 'text-secondary hover:bg-[#F7F3EA]'}`}>{item.label}<span className={`rounded-pill px-2 py-0.5 font-mono text-[11px] ${tab === item.id ? 'bg-[#3A3631] text-white' : 'bg-[#F1EBDF] text-secondary'}`}>{queue ? TABS.find((x) => x.id === item.id)?.count(queue) ?? 0 : '—'}</span></button>)}</div>

      {error && <div role="alert" className="mt-3 rounded-panel border border-wrong/30 bg-wrong-soft px-4 py-3 text-[13px] text-wrong-dark">{error}<button type="button" onClick={() => setReload((n) => n + 1)} className="ml-2 font-semibold underline">Retry</button></div>}
      {message && <div role="status" className="mt-3 rounded-panel border border-correct/30 bg-correct-soft px-4 py-3 text-[13px] text-correct-dark">{message}</div>}

      <div className="mt-3 flex flex-wrap items-start gap-6">
        <section className="grid min-w-0 flex-[999_1_560px] content-start gap-3" aria-label={`${tab} queue`}>
          {loading && <Card className="p-8 text-center text-[13px] text-muted">Loading moderation queue…</Card>}
          {!loading && queue?.items.length === 0 && <Card className="p-8 text-center text-[15px] text-secondary">{tab === 'My actions' ? 'No moderation actions yet.' : 'Queue clear. Nice work.'}</Card>}
          {!loading && queue?.items.map((item) => <ModerationCard key={item.id} item={item} tab={tab} note={notes[item.id] ?? ''} onNote={(value) => setNotes((old) => ({ ...old, [item.id]: value }))} onAction={(action) => void act(item, action)} onUndo={() => void undo(item)} busy={busy === item.id}/>)}
        </section>
        <aside className="grid min-w-0 flex-[1_1_280px] content-start gap-3 lg:max-w-[360px]">
          <Card className="p-4 sm:px-[18px]"><div className="text-[14px] font-semibold">Steps for a repeat problem</div><div className="mt-0.5 text-[12px] text-secondary">Use the least restrictive response that fits.</div>{[['1','Warning','Explain the rule and what to change.','bg-[#B26B00]'],['2','Mute 24 hours','Read and practise remain available.','bg-[#B26B00]'],['3','Mute 7 days','No posting, duels, or cups during the mute.','bg-[#9E2A1F]'],['4','Suspension','Staff-only; review before applying.','bg-[#9E2A1F]']].map(([n,title,detail,color]) => <div key={n} className="mt-2 grid grid-cols-[22px_minmax(0,1fr)] gap-2.5 border-t border-[#F1EBDF] pt-2 text-[13px]"><span className={`grid h-[22px] w-[22px] place-items-center rounded-full text-[11px] font-semibold text-white ${color}`}>{n}</span><span><b>{title}</b> · {detail}</span></div>)}</Card>
          <Card className="p-4 sm:px-[18px]"><div className="text-[14px] font-semibold">Moderators cannot</div>{['Change question answers, keys, or explanations','Suspend or delete accounts','Read private messages','Act on their own posts','Decide their own appeal'].map((item) => <div key={item} className="flex gap-2 py-1.5 text-[13px] leading-relaxed"><span className="font-semibold text-[#9E2A1F]">×</span><span>{item}</span></div>)}</Card>
          <div className="rounded-panel bg-community-soft p-4 text-[13px] leading-relaxed text-[#4A1540]"><b>Keep queues separate.</b> This page handles conduct and approval only. Wrong keys, OCR, and duplicate questions go to question review; moderation never changes scoring.</div>
        </aside>
      </div>
    </>}
  </main>
}

function ModerationCard({ item, tab, note, onNote, onAction, onUndo, busy }: { item: ModerationItem; tab: ModerationTab; note: string; onNote: (value: string) => void; onAction: (action: ModerationAction) => void; onUndo: () => void; busy: boolean }) {
  const reason = item.reasons.map(pretty).join(' · ') || pretty(item.action ?? item.item_type)
  const age = relative(item.created_at)
  return <article className="flex flex-col gap-3 rounded-panel border border-hairline bg-card p-[18px] shadow-[0_1px_2px_rgba(29,27,24,.05)] sm:px-5">
    <div className="flex flex-wrap items-center gap-2"><span className={`rounded-pill px-2.5 py-1 text-[12px] font-semibold ${item.item_type === 'reported' ? 'bg-wrong-soft text-wrong-dark' : item.item_type === 'new_user' ? 'bg-[#E3E9F8] text-[#1F44A6]' : item.item_type === 'appeal' ? 'bg-[#EEE6F7] text-[#5E2F98]' : 'bg-correct-soft text-correct-dark'}`}>{reason}</span><span className="text-[12px] text-secondary">{item.item_type === 'appeal' ? 'Appeal' : item.question ? 'Question discussion' : 'Community post'}</span><span className="ml-auto font-mono text-[11px] text-muted">{item.signal ?? age}</span></div>
    <div className="flex gap-3"><span className="grid h-[34px] w-[34px] shrink-0 place-items-center rounded-full bg-[#F1EBDF] font-mono text-[11px]">{item.author.slice(0,2).toUpperCase()}</span><div className="min-w-0 flex-1"><div className="text-[13px] text-secondary"><b className="text-ink">{item.author}</b> · {pretty(item.author_role)} · {age}{item.report_count > 0 ? ` · ${item.report_count} report${item.report_count === 1 ? '' : 's'} · score ${item.report_score}` : ''}</div>{item.question && <Link to={`/bank/${item.canonical_id}`} className="mt-2 block font-display text-[17px] leading-snug hover:text-link">{item.question}</Link>}<div className="mt-2 whitespace-pre-wrap break-words rounded-[8px] bg-[#F7F3EA] px-3 py-2.5 text-[14px] leading-relaxed">{item.body}</div></div></div>
    {item.note && <div className="rounded-[8px] bg-[#F7EAD0] px-3 py-2 text-[13px] leading-relaxed text-[#5B3D08]">{item.note}</div>}
    {tab === 'My actions' ? <div className={`flex flex-wrap items-center gap-2 rounded-[8px] px-3 py-2.5 text-[13px] ${item.undone ? 'bg-[#F1EBDF] text-secondary' : 'bg-correct-soft text-correct-dark'}`}><b>{item.undone ? '↶ Reversed' : `✓ ${pretty(item.action ?? 'Handled')}`}</b>{item.undone ? <span>Undo logged</span> : item.action_id !== null && item.before_state ? <button type="button" disabled={busy} onClick={onUndo} className="ml-auto min-h-9 px-2 font-semibold text-ink underline disabled:opacity-50">{busy ? 'Saving…' : 'Undo'}</button> : <span>Logged in moderation history</span>}</div> : <><label className="sr-only" htmlFor={`note-${item.id}`}>Moderator note</label><input id={`note-${item.id}`} value={note} onChange={(event) => onNote(event.target.value)} maxLength={1000} placeholder={tab === 'Appeals' ? 'Decision note (required to deny)' : 'Note for the moderation log (required to hide or reject)'} className="h-10 rounded-[8px] border border-hairline bg-paper px-3 text-[13px]"/><div className="flex flex-wrap gap-2 border-t border-[#F1EBDF] pt-3">
      {tab === 'Reported' && <><ActionButton label="Hide post" tone="dark" busy={busy} onClick={() => onAction('hide')}/><ActionButton label="Keep post · dismiss reports" tone="light" busy={busy} onClick={() => onAction('dismiss')}/></>}
      {tab === 'New users' && <><ActionButton label="Approve and publish" tone="green" busy={busy} onClick={() => onAction('approve')}/><ActionButton label="Reject post" tone="red" busy={busy} onClick={() => onAction('reject')}/></>}
      {tab === 'Appeals' && <><ActionButton label="Grant appeal" tone="green" busy={busy} onClick={() => onAction('grant_appeal')}/><ActionButton label="Keep decision" tone="light" busy={busy} onClick={() => onAction('deny_appeal')}/></>}
    </div></>}
  </article>
}

function ActionButton({ label, tone, busy, onClick }: { label: string; tone: 'dark' | 'light' | 'green' | 'red'; busy: boolean; onClick: () => void }) { const palette = { dark:'border-ink bg-ink text-white', light:'border-hairline bg-white text-ink', green:'border-[#3F8350] bg-[#DCEFE1] text-[#1F6234]', red:'border-[#C0462C] bg-[#F8DEDA] text-[#9E2A1F]' }; return <button type="button" disabled={busy} onClick={onClick} className={`min-h-10 rounded-pill border px-3.5 py-2 text-[13px] font-semibold disabled:cursor-wait disabled:opacity-50 ${palette[tone]}`}>{busy ? 'Saving…' : label}</button> }
function pretty(value: string) { return value.replace(/_/g, ' ').replace(/\b\w/g, (letter: string) => letter.toUpperCase()) }
function relative(value: string) { const minutes = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000)); if (minutes < 1) return 'just now'; if (minutes < 60) return `${minutes}m ago`; const hours = Math.floor(minutes / 60); if (hours < 24) return `${hours}h ago`; const days = Math.floor(hours / 24); return days === 1 ? 'yesterday' : `${days}d ago` }
function actionMessage(action: ModerationAction) { return ({ approve:'Post approved and published. Action logged.', reject:'Post rejected and hidden. Action logged.', hide:'Post hidden. Action logged.', dismiss:'Reports dismissed; post state unchanged. Action logged.', grant_appeal:'Appeal granted. Action logged.', deny_appeal:'Appeal denied. Action logged.' } as Record<string,string>)[action] ?? 'Action saved.' }
