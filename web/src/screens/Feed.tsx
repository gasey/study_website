import {UserAvatar} from '../components/AvatarArt'
import CalendarCountdown from '../components/CalendarCountdown'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useState } from 'react'
import { Link, useNavigate,useSearchParams } from 'react-router-dom'
import PublishedImprovements from '../components/PublishedImprovements'
import { lazy, Suspense } from 'react'
const Materials=lazy(()=>import('./Materials'))
const FollowingMaterials=lazy(()=>import('./Creators').then(m=>({default:m.FollowingMaterials})))
const CommunityQuestions=lazy(()=>import('./CommunityQuestions'))
import { Card } from '../components/ui'
import { currentMock, getCommunityFeed, getHome, getMistakes, getProgressSummary, listMocks, type CommunityFeedItem, type CommunityFeedResponse, type HomeData, type MockSession, type MockSummary, type Progress } from '../lib/api'

const TABS: { id: CommunityFeedResponse['tab']; label: string }[] = [
  { id: 'for-you', label: 'For you' }, { id: 'following', label: 'Following' },
  { id: 'mcqs', label: 'MCQs' }, { id: 'questions', label: 'Questions & Doubts' }, { id: 'materials', label: 'Materials' },
]
const COMPOSE = ['MCQ', 'Doubt', 'Note', 'Material']

export default function Feed() {
  const nav=useNavigate()
  const [feedParams,setFeedParams]=useSearchParams()
  const rawTab=feedParams.get('tab')==='doubts'?'questions':feedParams.get('tab')
  const tab:CommunityFeedResponse['tab']=TABS.some(t=>t.id===rawTab)?rawTab as CommunityFeedResponse['tab']:'for-you'
  const rawDiscussion=feedParams.get('discussion') ?? (feedParams.get('tab')==='doubts'?'doubts':'all')
  const discussion: 'all' | 'doubts' | 'unanswered' = rawDiscussion==='doubts'||rawDiscussion==='unanswered'?rawDiscussion:'all'
  const setTab=(value:CommunityFeedResponse['tab'])=>{setOffset(0);setFeedParams(previous=>{const next=new URLSearchParams();if(previous.has('exam_scope'))next.set('exam_scope',previous.get('exam_scope')!);next.set('tab',value);return next},{replace:true})}
  const [feed, setFeed] = useState<CommunityFeedResponse | null>(null)
  const [home, setHome] = useState<HomeData | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [mistakeCount, setMistakeCount] = useState<number | null>(null)
  const [openMock, setOpenMock] = useState<MockSession | null>(null)
  const [mocks, setMocks] = useState<MockSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [reload, setReload] = useState(0)
  const [offset, setOffset] = useState(0)
  const [composeType, setComposeType] = useState<string | null>(null)

  useEffect(() => {
    getHome().then(setHome).catch(() => setHome(null))
    getProgressSummary().then(setProgress).catch(() => setProgress(null))
    getMistakes().then((items) => setMistakeCount(items.length)).catch(() => setMistakeCount(null))
    currentMock().then(setOpenMock).catch(() => setOpenMock(null))
    listMocks().then(setMocks).catch(() => setMocks([]))
  }, [])
  useEffect(() => {
    if(tab==='materials'||tab==='mcqs'||tab==='following')return
    let active = true
    setLoading(true)
    setError(false)
    getCommunityFeed(tab, offset, tab==='questions'?discussion:'all').then((result) => {
      if (active) setFeed((previous) => offset === 0 ? result : previous ? { ...result, items: [...previous.items, ...result.items] } : result)
    }).catch(() => { if (active) setError(true) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [tab, discussion, offset, reload])

  const collections = home?.collections ?? []
  const featuredExam = collections.find((item) => item.kind === 'exam') ?? collections[0]
  const answered = progress?.answered ?? 0
  const accuracy = progress && progress.answered ? Math.round(progress.correct / progress.answered * 100) : 0
  const completedMocks = mocks.filter((item) => item.submitted_at)
  const mockProgress = openMock ? Math.round((1 - openMock.seconds_remaining / Math.max(1, openMock.duration_seconds)) * 100) : 0
  const startCompose = (type: string) => type === 'MCQ' ? nav('/contribute/new?kind=new_question') : ['Note','Material','Post'].includes(type)?nav('/studio/new'):setComposeType(type)

  return <div className="mx-auto max-w-shell px-4 pb-24 pt-6 sm:px-6 sm:pt-6">
    <main className="flex flex-wrap items-start gap-6">
      <aside className="grid min-w-0 flex-[1_1_210px] gap-3 lg:max-w-[260px]">
        <CalendarCountdown/>
        <PublishedImprovements/>
        <Link to={featuredExam ? (featuredExam.route ?? `/exams/${featuredExam.id}`) : '/exams'} className="block rounded-panel bg-[#14130F] p-4 text-paper transition hover:bg-[#25231F]">
          <div className="text-[12px] font-semibold text-[#D8A33A]">Your exam</div>
          {featuredExam ? <><div className="mt-2 flex items-baseline gap-2"><span className="font-display text-[44px] leading-none">{featuredExam.sections}</span><span className="text-[14px]">sections</span></div><div className="mt-2 text-[13px] text-[#D9D0BF]">{featuredExam.title} · Open collection →</div></> : <div className="mt-2 text-[14px]">Browse available collections →</div>}
        </Link>

        <Card className="p-[14px]">
          <div className="flex items-center justify-between gap-2"><span className="flex items-center gap-2 text-[14px] font-semibold"><i className="h-2 w-2 rounded-full bg-rewards"/>Your progress</span><span className="font-mono text-[11px] text-rewards-dark">{progress ? `${accuracy}% accuracy` : '—'}</span></div>
          <div className="mt-2 h-[6px] overflow-hidden rounded-pill bg-[#ECEDCF]"><div className="h-full rounded-pill bg-[#8A8A12] transition-[width]" style={{ width: `${progress?.answered ? accuracy : 0}%` }}/></div>
          <div className="mt-2 text-[12px] text-secondary">{progress ? `${answered.toLocaleString('en-IN')} answers recorded in your practice` : 'Practice progress will appear here.'}</div>
          <Link to="/mistakes" className="mt-2 inline-flex min-h-9 items-center text-[12px] font-semibold text-link">Review mistakes{mistakeCount !== null ? ` · ${mistakeCount} due` : ''} →</Link>
        </Card>

        <Card className="overflow-hidden">
          <div className="px-4 pb-2 pt-[14px]"><span className="flex items-center gap-2 text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#1F44A6]"/>Your desk</span></div>
          <div className="px-4 pb-[14px]">
            <div className="text-[12px] text-muted">{openMock ? 'Continue' : 'Pick up your study'}</div>
            <div className="mt-1 font-display text-[19px] font-medium leading-snug">{openMock ? (mocks.find((m) => m.id === openMock.id)?.collection_title ?? 'Timed mock') : 'Your personal study space'}</div>
            <div className="mt-1 text-[13px] text-secondary">{openMock ? `Timed mock · ${openMock.questions.length} questions` : 'Goals, saved questions and revision'}</div>
            <div className="my-3 h-[6px] rounded-pill bg-[#E3E9F8]"><div className="h-[6px] rounded-pill bg-[#2D5BD0]" style={{ width: `${openMock ? Math.max(0, Math.min(100, mockProgress)) : Math.min(100, answered)}%` }}/></div>
            <div className="flex items-center justify-between font-mono text-[11px] text-muted"><span>{openMock ? openMock.seconds_remaining > 0 ? `${Math.ceil(openMock.seconds_remaining / 60)} min remaining` : 'Time elapsed' : `${answered} answered`}</span><Link to={openMock ? `/exams/${openMock.collection_id}/mock` : '/desk'} className="font-sans text-[13px] font-semibold text-[#1F44A6]">{openMock ? 'Resume →' : 'Open desk →'}</Link></div>
          </div>
          <div className="border-t border-[#EDE5D4]">
            <RailLink to="/bank" label="Question bank" meta={home ? home.total_questions.toLocaleString('en-IN') : 'Browse'} />
            <RailLink to="/mistakes" label="Mistakes review" meta={mistakeCount === null ? 'Review' : `${mistakeCount} due`} />
            <RailLink to="/exams" label="Exams" meta={String(collections.length)} />
            <RailLink to="/exams" label="Mock exams" meta={openMock ? '1 in progress' : `${completedMocks.length} complete`} />
            <RailLink to="/scoring" label="Challenges" meta="Coming later" last />
          </div>
        </Card>

        <Link to="/desk" className="block rounded-panel border border-hairline bg-card p-[14px] transition hover:bg-[#F7F3EA]">
          <div className="flex items-center gap-2.5"><span className="grid h-[34px] w-[34px] place-items-center rounded-full border border-ink bg-community-soft text-[13px] font-semibold text-community-dark">◎</span><span><span className="block text-[12px] font-semibold text-community-dark">Study desk</span><span className="block text-[14px] font-semibold">Study partners · preview</span></span></div>
          <div className="mt-2 text-[12px] text-secondary">Private by default · See the partner preview →</div>
        </Link>

        <Card className="overflow-hidden">
          <div className="px-4 pb-2 pt-[14px]"><span className="flex items-center gap-2 text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#7E4A00]"/>Your exams</span></div>
          {collections.slice(0, 4).map((collection) => <Link key={collection.id} to={collection.route ?? `/exams/${collection.id}`} className="block border-t border-[#F1EBDF] px-4 py-2.5 text-[14px] transition hover:bg-[#F7F3EA]">{collection.title}</Link>)}
          {!collections.length && <Link to="/exams" className="block px-4 pb-3 text-[13px] text-link">Browse exams →</Link>}
        </Card>
      </aside>

      <section className="min-w-0 flex-[999_1_520px]">
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2"><h1 className="font-display text-[34px] font-medium leading-tight -tracking-[.01em]">Community</h1><span className="font-mono text-[12px] text-muted">{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}</span></div>

        {featuredExam && <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-pill bg-[#2D5BD0] px-[18px] py-2 text-white">
          <span className="min-w-0 flex-[1_1_260px] text-[14px]"><b>Start here:</b> {featuredExam.title}, past papers and {featuredExam.sections} live sections</span>
          <Link to={featuredExam.route ?? `/exams/${featuredExam.id}`} className="rounded-pill bg-white px-4 py-[7px] text-[13px] font-semibold text-[#1F44A6]">Open</Link>
        </div>}

        <Card className="flex flex-wrap items-center gap-3 px-4 py-[14px] sm:px-4">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-ink bg-[#F6DDD3] font-mono text-[12px]">?</span>
          <button type="button" onClick={() => startCompose('Post')} className="min-h-10 min-w-[200px] flex-1 py-2 text-left text-[15px] text-placeholder">Post an MCQ, ask a doubt, share notes…</button>
          <div className="flex flex-wrap gap-1.5">{COMPOSE.map((type) => <button key={type} type="button" onClick={() => startCompose(type)} className="min-h-9 rounded-pill border border-[#CFC5B2] px-3 py-1.5 text-[13px] font-medium transition hover:border-ink">{type}</button>)}</div>
        </Card>

        <div className="mt-4 flex gap-1 overflow-x-auto rounded-pill border border-hairline bg-card p-1 shadow-[0_1px_2px_rgba(29,27,24,.05)]" role="tablist" aria-label="Community feed filters">{TABS.map((item) => <button key={item.id} type="button" id={`community-tab-${item.id}`} role="tab" aria-controls="community-tab-panel" tabIndex={tab===item.id?0:-1} aria-selected={tab === item.id} onKeyDown={event=>{const index=TABS.findIndex(t=>t.id===tab);const next=event.key==='Home'?0:event.key==='End'?TABS.length-1:event.key==='ArrowRight'?(index+1)%TABS.length:event.key==='ArrowLeft'?(index+TABS.length-1)%TABS.length:-1;if(next>=0){event.preventDefault();setTab(TABS[next].id);document.getElementById(`community-tab-${TABS[next].id}`)?.focus()}}} onClick={() => { setOffset(0); setTab(item.id) }} className={`min-h-10 shrink-0 rounded-pill px-4 py-2 text-[14px] font-semibold transition ${tab === item.id ? 'bg-ink text-white' : 'text-secondary hover:bg-[#F7F3EA] hover:text-ink'}`}>{item.label}</button>)}</div>

        <div id="community-tab-panel" role="tabpanel" aria-labelledby={`community-tab-${tab}`} tabIndex={0} className="min-w-0">
        {tab==='following'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading following feed…</p>}><FollowingMaterials embedded/></Suspense>:tab==='materials'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading materials…</p>}><Materials embedded/></Suspense>:tab==='mcqs'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading community practice…</p>}><CommunityQuestions embedded/></Suspense>:<>
        {tab==='questions'&&<div className="mt-3 rounded-panel border border-hairline bg-card p-4"><h2 className="font-display text-[23px]">Questions & Doubts</h2><p className="mt-1 text-[13px] leading-relaxed text-secondary">Discuss a question, explain your reasoning or help with a doubt. These are the same conversations shown on each question. Answer it first to reveal discussion; active mocks stay protected.</p><div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Question discussion filters">{([['all','All discussions'],['doubts','Doubts'],['unanswered','Unanswered doubts']] as const).map(([value,label])=><button key={value} type="button" aria-pressed={discussion===value} onClick={()=>{setOffset(0);setFeedParams({tab:'questions',discussion:value})}} className={`min-h-11 rounded-pill border px-3 py-2 text-[12px] font-semibold ${discussion===value?'border-ink bg-ink text-paper':'border-hairline text-secondary'}`}>{label}</button>)}<Link to="/bank" className="inline-flex min-h-11 items-center px-3 text-[12px] font-semibold text-link">Find a question to discuss →</Link></div><p className="mt-2 text-[12px] text-muted">Unanswered means no published reply visible to you. For an incorrect question or key, use Suggest correction on the question.</p></div>}

        {tab==='for-you'&&<MaterialDiscovery title="Community reading" compact/>}
        <div aria-live="polite" className="mt-3">
          {loading && offset === 0 ? <Card className="p-8 text-center text-[13px] text-muted">Loading discussions…</Card> : error && offset === 0 ? <Card className="p-8 text-center"><p className="text-[14px]">The community feed couldn’t load.</p><button type="button" className="mt-2 min-h-10 px-3 text-[12px] font-semibold text-link" onClick={() => setReload((n) => n + 1)}>Try again</button></Card> : !feed?.available ? <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">···</div><p className="mt-3 font-display text-[19px]">This space is not open yet</p><p className="mx-auto mt-1 max-w-md text-[13px] leading-relaxed text-secondary">{feed?.message}</p></Card> : feed.items.length === 0 ? <EmptyFeed title={tab==='questions'&&discussion==='unanswered'?'No unanswered doubts to show':'No discussions to show yet'} message={feed?.message ?? 'Answer a question first; its published explanation or doubt will then appear here.'} /> : <>{feed.items.map((item) => <Discussion key={item.id} item={item} />)}{(feed.has_more || error && offset > 0) && <div className="p-4 text-center"><button type="button" disabled={loading} onClick={() => error ? setReload((n) => n + 1) : setOffset((value) => value + 20)} className="min-h-11 rounded-pill border border-hairline bg-card px-4 py-2 text-[12px] font-semibold disabled:opacity-50">{loading ? 'Loading…' : error ? 'Retry loading discussions' : 'Load more discussions'}</button></div>}</>}
        </div>
        </>}
        </div>
      </section>

      <aside className="grid min-w-0 flex-[1_1_260px] content-start gap-3 lg:max-w-[320px]">
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between gap-2 px-4 pb-2 pt-[14px]"><span className="flex items-center gap-2 text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#7E4A00]"/>Headlines</span><Link to="/news" className="text-[12px] font-semibold">Notices →</Link></div>
          <div className="border-t border-[#F1EBDF] px-4 py-3"><div className="font-display text-[16px] leading-snug">Official MPSC notices</div><p className="mt-1 text-[12px] leading-relaxed text-secondary">Official exam notices and dates are available in the calendar.</p></div>
        </Card>

        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 px-4 pb-2 pt-[14px] text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#1F44A6]"/>Open challenges</div>
          <div className="px-4 pb-3 pt-1"><p className="text-[14px] leading-relaxed">Choose your next game</p><p className="mt-1 text-[12px] text-muted">Gauntlet, speed rounds and private duels.</p></div>
          <div className="border-t border-[#F1EBDF] px-4 py-3"><div className="font-display text-[18px] font-medium">Weekly cup</div><div className="mt-1 font-mono text-[11px] text-muted"><Link to="/games" className="inline-flex min-h-11 items-center font-semibold text-link">Open games & weekly cup →</Link></div></div>
        </Card>

        <Card className="overflow-hidden">
          <div className="flex items-center justify-between gap-2 px-4 pb-2 pt-[14px]"><span className="flex items-center gap-2 text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#545A06]"/>Your week</span><Link to="/mistakes" className="text-[12px] font-semibold">Review →</Link></div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-4 px-4 pb-3 pt-1">
            <Stat value={progress ? answered.toLocaleString('en-IN') : '—'} label="questions answered" />
            <Stat value={progress && answered ? `${accuracy}%` : '—'} label="accuracy" />
            <Stat value={String(completedMocks.length)} label="mocks finished" />
            <Stat value={mistakeCount === null ? '—' : String(mistakeCount)} label="mistakes to review" />
          </div>
          <div className="border-t border-[#F1EBDF] px-4 py-3 text-[12px] text-secondary">Only you see your practice summary.</div>
        </Card>

        <Link to="/bank" className="block rounded-panel border border-hairline bg-card p-4 transition hover:bg-[#F7F3EA]">
          <div className="flex items-center gap-2 text-[13px] font-semibold text-[#7E4A00]"><i className="h-2 w-2 rounded-full bg-[#B26B00]"/>Help the bank</div>
          <div className="mt-2 font-display text-[19px] font-medium">Explore the question bank</div>
          <div className="mt-1 text-[13px] text-secondary">{home ? `${home.total_questions.toLocaleString('en-IN')} questions · ${home.scorable_questions.toLocaleString('en-IN')} with keys for timed practice` : 'Review questions, answer provenance, and report issues.'}</div>
          <span className="mt-2 inline-flex min-h-9 items-center text-[12px] font-semibold text-link">Open bank →</span>
        </Link>

        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 px-4 pb-2 pt-[14px] text-[13px] font-semibold"><i className="h-2 w-2 rounded-full bg-[#7E4A00]"/>Exams to explore</div>
          {collections.slice(0, 3).map((collection) => <div key={collection.id} className="flex items-center gap-3 border-t border-[#F1EBDF] px-4 py-2.5"><div className="min-w-0 flex-1"><div className="truncate text-[14px] font-medium">{collection.title}</div><div className="font-mono text-[11px] text-muted">{collection.sections} sections</div></div><Link to={collection.route ?? `/exams/${collection.id}`} className="rounded-pill border border-ink px-3 py-1.5 text-[12px] font-semibold">Open</Link></div>)}
          {!collections.length && <Link to="/exams" className="block px-4 pb-3 text-[13px] text-link">Browse available exams →</Link>}
        </Card>
      </aside>
    </main>

    {composeType && <div className="fixed inset-0 z-[70] grid place-items-center bg-ink/55 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setComposeType(null) }}><section role="dialog" aria-modal="true" aria-labelledby="compose-preview-title" className="w-full max-w-md rounded-panel border border-hairline bg-card p-6 shadow-[0_20px_60px_rgba(0,0,0,.25)]"><div className="label text-community-dark">Community contribution</div><h2 id="compose-preview-title" className="mt-2 font-display text-[26px] font-medium">{composeType === 'Post' ? 'Share with the community' : `Create a ${composeType.toLowerCase()}`}</h2><p className="mt-2 text-[14px] leading-relaxed text-secondary">Choose a question in the bank or an exam, then use Discuss / Ask a doubt. The question and its source stay linked; published topics also appear in this feed.</p><div className="mt-5 flex flex-wrap justify-end gap-2"><button type="button" onClick={() => setComposeType(null)} className="min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold">Close</button><Link to="/bank" onClick={() => setComposeType(null)} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-[13px] font-semibold text-paper">Browse questions →</Link></div></section></div>}
  </div>
}

function RailLink({ to, label, meta, last = false }: { to: string; label: string; meta: string; last?: boolean }) { return <Link to={to} className={`flex min-h-10 items-center justify-between gap-2 px-4 py-2 text-[14px] font-medium transition hover:bg-[#F7F3EA] ${last ? '' : 'border-b border-[#F1EBDF]'}`}><span>{label}</span><span className="font-mono text-[11px] text-muted">{meta}</span></Link> }
function Stat({ value, label }: { value: string; label: string }) { return <div><div className="font-display text-[28px] leading-none">{value}</div><div className="mt-1 text-[12px] text-secondary">{label}</div></div> }
function EmptyFeed({ message, title }: { message: string; title: string }) { return <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">✳</div><p className="mt-3 font-display text-[20px]">{title}</p><p className="mx-auto mt-2 max-w-md text-[13px] leading-relaxed text-secondary">{message}</p><Link to="/bank" className="mt-4 inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-[12px] font-semibold text-paper">Explore the question bank →</Link></Card> }
function Discussion({ item }: { item: CommunityFeedItem }) { return <article className="rounded-panel border border-hairline bg-card p-[18px] pb-[14px] shadow-[0_1px_2px_rgba(29,27,24,.05)]"><div className="flex items-center gap-3"><UserAvatar look={item.avatar} initials={item.author}/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2 text-[14px]"><b>{item.author}</b><span className="rounded-pill bg-[#F1EBDF] px-2 py-0.5 text-[11px] text-secondary">{item.author_role}</span></div><div className="mt-0.5 text-[12px] text-muted">{item.source_context ?? 'Question bank discussion'} · {new Date(item.created_at).toLocaleDateString('en-IN')}</div></div><span className="rounded-pill bg-community-soft px-2.5 py-1 text-[12px] font-semibold text-community-dark">{item.kind === 'doubt' ? 'Doubt' : 'Explanation'}</span></div><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="mt-3 block font-display text-[20px] leading-snug hover:text-link">{item.question}</Link><p className="mt-3 whitespace-pre-wrap text-[15px] leading-relaxed">{item.body}</p>{item.accepted_answer && <div className="mt-3 rounded-[10px] bg-[#DCEFE1] px-4 py-3.5"><div className="text-[12px] font-semibold text-[#1F6234]">✓ Accepted reply · community feedback</div><p className="mt-2 whitespace-pre-wrap text-[14px] leading-relaxed">{item.accepted_answer}</p></div>}<div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-[#F1EBDF] pt-3 text-[13px] text-secondary"><span className="font-semibold">▲ {item.helpful} helpful</span><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="font-semibold">Open discussion →</Link></div></article> }
