import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewRequest } from '../lib/review'
import { practiceJourneyLink, type Journey } from '../lib/examJourney'

export default function ExamJourney({ id, focused = false }: { id: string; focused?: boolean }) {
  const [data, setData] = useState<Journey | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let live = true
    setError('')
    reviewRequest<Journey>('/me/exam-journey/' + encodeURIComponent(id))
      .then(value => { if (live) setData(value) }).catch(e => { if (live) setError(e.message) })
    return () => { live = false }
  }, [id, retry])
  useEffect(() => {
    const refresh = () => setRetry(n => n + 1)
    window.addEventListener('ism-study-checkpoint', refresh)
    return () => window.removeEventListener('ism-study-checkpoint', refresh)
  }, [])
  const active = data?.active_mock && (!focused || data.active_mock.collection_id === id) ? data.active_mock : null
  const qs = new URLSearchParams()
  if (active?.paper_id) qs.set('paper', active.paper_id)
  else if (active?.section_path) qs.set('section', active.section_path)
  if (active?.answer_mode === 'derived-practice') qs.set('mode', 'derived')
  const primary = 'inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-3 text-[13px] font-semibold text-paper'
  const secondary = 'inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 py-3 text-[13px] font-semibold'
  return <section aria-label="Your exam journey" className="mt-5 rounded-[14px] border border-hairline bg-card p-5">
    <div className="flex flex-wrap items-baseline justify-between gap-3">
      <h2 className="font-display text-[25px]">{focused ? 'Your next UDC study step' : 'Your next step'}</h2>
      {!focused && <Link to="/rewards" className="text-[13px] font-semibold text-link">XP &amp; reward points →</Link>}
    </div>
    {!data && !error && <p role="status" className="mt-3 text-[13px] text-muted">Loading saved progress…</p>}
    {error && <p role="alert" className="mt-3 text-[13px]">Could not load your saved place. <button onClick={() => setRetry(n => n + 1)} className="min-h-11 underline">Retry</button></p>}
    <div className="mt-3 flex flex-wrap gap-3">
      {active && <Link to={'/exams/' + active.collection_id + '/mock?' + qs} className={primary}>Resume saved {focused ? 'UDC timed practice' : 'mock'}{active.collection_id !== id ? ' · another exam' : ''} →</Link>}
      <Link to={practiceJourneyLink(id, data)} className={focused && !active ? primary : secondary}>{data?.active_study_session?'Continue practice':focused&&data?.recent_study_sessions?.length?'Start another set':data?.last_practice||data?.checkpoint?'Continue practice':'Start practice'} →</Link>
      <Link to={`/exams/${id}?view=progress`} className={secondary}>Review progress &amp; mistakes</Link>
    </div>
    {data?.last_practice && <p className="mt-3 text-[12px] text-muted">Last practice {new Date(data.last_practice.at).toLocaleString('en-IN')} · answers are saved to your account when signed in.</p>}
    {focused&&!!data?.recent_study_sessions?.length&&<div className="mt-4 border-t border-hairline pt-3"><h3 className="text-[12px] font-semibold">Recent study sets</h3>{data.recent_study_sessions.map(set=><Link key={set.id} to={'/exams/udc?view=practice&session='+encodeURIComponent(set.id)+'#exam-question-browser'} className="mt-2 flex min-h-11 flex-wrap items-center justify-between gap-2 text-[13px] text-link"><span>{set.total} questions · {set.summary?.correct||0} correct · {set.summary?.wrong||0} wrong</span><span>View summary →</span></Link>)}</div>}
    {!!data?.recent_results.length && <div className="mt-4 border-t border-hairline pt-3">
      <h3 className="text-[12px] font-semibold">Recent saved results</h3>
      {data.recent_results.map(mock => <Link key={mock.id} to={'/results/' + mock.id} className="mt-2 flex flex-wrap justify-between gap-2 text-[13px] text-link"><span>{new Date(mock.submitted_at).toLocaleDateString('en-IN')} · Original {mock.score} marks</span><span>{mock.n_correct} correct · {mock.n_wrong} wrong · Review →</span></Link>)}
    </div>}
  </section>
}
