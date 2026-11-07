import {UserAvatar} from '../components/AvatarArt'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useState } from 'react'
import { Link, useNavigate,useSearchParams } from 'react-router-dom'
import { lazy, Suspense } from 'react'
const Materials=lazy(()=>import('./Materials'))
const FollowingMaterials=lazy(()=>import('./Creators').then(m=>({default:m.FollowingMaterials})))
const CommunityQuestions=lazy(()=>import('./CommunityQuestions'))
import { Card } from '../components/ui'
import { getCommunityFeed, type CommunityFeedItem, type CommunityFeedResponse } from '../lib/api'

const TABS: { id: CommunityFeedResponse['tab']; label: string }[] = [
  { id: 'for-you', label: 'Discover' }, { id: 'following', label: 'Following' },
  { id: 'mcqs', label: 'Practice MCQs' }, { id: 'questions', label: 'Questions & Doubts' }, { id: 'materials', label: 'Materials' },
]
const COMPOSE = ['Doubt', 'Note', 'MCQ']

export default function Feed() {
  const nav=useNavigate()
  const [feedParams,setFeedParams]=useSearchParams()
  useEffect(()=>{if(feedParams.get('section')==='community')document.getElementById('community-section')?.scrollIntoView({block:'start'})},[feedParams])
  const rawTab=feedParams.get('tab')==='doubts'?'questions':feedParams.get('tab')
  const tab:CommunityFeedResponse['tab']=TABS.some(t=>t.id===rawTab)?rawTab as CommunityFeedResponse['tab']:'for-you'
  const rawDiscussion=feedParams.get('discussion') ?? (feedParams.get('tab')==='doubts'?'doubts':'all')
  const discussion: 'all' | 'doubts' | 'unanswered' = rawDiscussion==='doubts'||rawDiscussion==='unanswered'?rawDiscussion:'all'
  const setTab=(value:CommunityFeedResponse['tab'])=>{setOffset(0);setFeedParams(previous=>{const next=new URLSearchParams();if(previous.has('exam_scope'))next.set('exam_scope',previous.get('exam_scope')!);next.set('tab',value);return next},{replace:true})}
  const [feed, setFeed] = useState<CommunityFeedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [reload, setReload] = useState(0)
  const [offset, setOffset] = useState(0)
  const [composeType, setComposeType] = useState<string | null>(null)

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

  const startCompose = (type: string) => type === 'MCQ' ? nav('/contribute/new?kind=new_question') : ['Note','Material','Post'].includes(type)?nav('/studio/new'):setComposeType(type)

  return <div className="mx-auto max-w-shell px-4 pb-24 pt-6 sm:px-6 sm:pt-6">
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="font-mono text-[10px] uppercase tracking-widest text-community-dark">Learn together</p><h1 className="mt-2 font-display text-[40px]">Community</h1><p className="mt-2 text-[14px] text-secondary">Questions, shared reading and conversations.</p></div><Link to="/create" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-5 text-[13px] font-semibold text-paper">Create & contribute →</Link></header>
    <div className="mx-auto min-w-0 max-w-4xl">
      <section className="min-w-0">
        <div id="community-section" className="mb-2 mt-8 scroll-mt-32 flex flex-wrap items-end justify-end gap-3"><h2 className="sr-only">Community feed</h2><details className="relative"><summary className="min-h-11 cursor-pointer rounded-pill border border-hairline bg-card px-4 py-3 text-[13px] font-semibold">Share or ask</summary><div className="absolute right-0 z-10 mt-2 grid min-w-[180px] gap-1 rounded-panel border border-hairline bg-card p-2 shadow-lg">{COMPOSE.map(type=><button key={type} type="button" onClick={()=>startCompose(type)} className="min-h-11 rounded-lg px-4 text-left text-[13px] hover:bg-canvas">{type==='Doubt'?'Ask a doubt':type==='Note'?'Share study material':'Contribute an MCQ'}</button>)}</div></details></div>
        <div className="mt-4 flex gap-1 overflow-x-auto rounded-pill border border-hairline bg-card p-1 shadow-[0_1px_2px_rgba(29,27,24,.05)]" role="tablist" aria-label="Community feed filters">{TABS.map((item) => <button key={item.id} type="button" id={`community-tab-${item.id}`} role="tab" aria-controls="community-tab-panel" tabIndex={tab===item.id?0:-1} aria-selected={tab === item.id} onKeyDown={event=>{const index=TABS.findIndex(t=>t.id===tab);const next=event.key==='Home'?0:event.key==='End'?TABS.length-1:event.key==='ArrowRight'?(index+1)%TABS.length:event.key==='ArrowLeft'?(index+TABS.length-1)%TABS.length:-1;if(next>=0){event.preventDefault();setTab(TABS[next].id);document.getElementById(`community-tab-${TABS[next].id}`)?.focus()}}} onClick={() => { setOffset(0); setTab(item.id) }} className={`min-h-10 shrink-0 rounded-pill px-4 py-2 text-[14px] font-semibold transition ${tab === item.id ? 'bg-ink text-white' : 'text-secondary hover:bg-[#F7F3EA] hover:text-ink'}`}>{item.label}</button>)}</div>

        <div id="community-tab-panel" role="tabpanel" aria-labelledby={`community-tab-${tab}`} tabIndex={0} className="min-w-0">
        {tab==='following'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading following feed…</p>}><FollowingMaterials embedded/></Suspense>:tab==='materials'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading materials…</p>}><Materials embedded/></Suspense>:tab==='mcqs'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading community practice…</p>}><CommunityQuestions embedded/></Suspense>:<>
        {tab==='questions'&&<div className="mt-3 rounded-panel border border-hairline bg-card p-4"><h2 className="font-display text-[23px]">Questions & Doubts</h2><p className="mt-1 text-[13px] leading-relaxed text-secondary">Discuss a question, explain your reasoning or help with a doubt. These are the same conversations shown on each question. Answer it first to reveal discussion; active mocks stay protected.</p><div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Question discussion filters">{([['all','All discussions'],['doubts','Doubts'],['unanswered','Unanswered doubts']] as const).map(([value,label])=><button key={value} type="button" aria-pressed={discussion===value} onClick={()=>{setOffset(0);setFeedParams(previous=>{const next=new URLSearchParams(previous);next.set('tab','questions');next.set('discussion',value);return next})}} className={`min-h-11 rounded-pill border px-3 py-2 text-[12px] font-semibold ${discussion===value?'border-ink bg-ink text-paper':'border-hairline text-secondary'}`}>{label}</button>)}<Link to="/bank" className="inline-flex min-h-11 items-center px-3 text-[12px] font-semibold text-link">Find a question to discuss →</Link></div><p className="mt-2 text-[12px] text-muted">Unanswered means no published reply visible to you. For an incorrect question or key, use Suggest correction on the question.</p></div>}

        {tab==='for-you'&&<MaterialDiscovery title="Reading for your next study break" compact/>}
        <div aria-live="polite" className="mt-3 space-y-3">
          {loading && offset === 0 ? <Card className="p-8 text-center text-[13px] text-muted">Loading discussions…</Card> : error && offset === 0 ? <Card className="p-8 text-center"><p className="text-[14px]">The community feed couldn’t load.</p><button type="button" className="mt-2 min-h-10 px-3 text-[12px] font-semibold text-link" onClick={() => setReload((n) => n + 1)}>Try again</button></Card> : !feed?.available ? <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">···</div><p className="mt-3 font-display text-[19px]">This space is not open yet</p><p className="mx-auto mt-1 max-w-md text-[13px] leading-relaxed text-secondary">{feed?.message}</p></Card> : feed.items.length === 0 ? <EmptyFeed title={tab==='questions'&&discussion==='unanswered'?'No unanswered doubts to show':'No discussions to show yet'} message={feed?.message ?? 'Answer a question first; its published explanation or doubt will then appear here.'} /> : <>{feed.items.map((item) => <Discussion key={item.id} item={item} />)}{(feed.has_more || error && offset > 0) && <div className="p-4 text-center"><button type="button" disabled={loading} onClick={() => error ? setReload((n) => n + 1) : setOffset((value) => value + 20)} className="min-h-11 rounded-pill border border-hairline bg-card px-4 py-2 text-[12px] font-semibold disabled:opacity-50">{loading ? 'Loading…' : error ? 'Retry loading discussions' : 'Load more discussions'}</button></div>}</>}
        </div>
        </>}
        </div>
      </section>


    </div>

    {composeType && <div className="fixed inset-0 z-[70] grid place-items-center bg-ink/55 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setComposeType(null) }}><section role="dialog" aria-modal="true" aria-labelledby="compose-preview-title" className="w-full max-w-md rounded-panel border border-hairline bg-card p-6 shadow-[0_20px_60px_rgba(0,0,0,.25)]"><div className="label text-community-dark">Community contribution</div><h2 id="compose-preview-title" className="mt-2 font-display text-[26px] font-medium">{composeType === 'Post' ? 'Share with the community' : `Create a ${composeType.toLowerCase()}`}</h2><p className="mt-2 text-[14px] leading-relaxed text-secondary">Choose a question in the bank or an exam, then use Discuss / Ask a doubt. The question and its source stay linked; published topics also appear in this feed.</p><div className="mt-5 flex flex-wrap justify-end gap-2"><button type="button" onClick={() => setComposeType(null)} className="min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold">Close</button><Link to="/bank" onClick={() => setComposeType(null)} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-[13px] font-semibold text-paper">Browse questions →</Link></div></section></div>}
  </div>
}

function EmptyFeed({ message, title }: { message: string; title: string }) { return <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">✳</div><p className="mt-3 font-display text-[20px]">{title}</p><p className="mx-auto mt-2 max-w-md text-[13px] leading-relaxed text-secondary">{message}</p><Link to="/bank" className="mt-4 inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-[12px] font-semibold text-paper">Explore the question bank →</Link></Card> }
function Discussion({ item }: { item: CommunityFeedItem }) { return <article className="rounded-panel border border-hairline bg-card p-[18px] pb-[14px] shadow-[0_1px_2px_rgba(29,27,24,.05)]"><div className="flex items-center gap-3"><UserAvatar look={item.avatar} initials={item.author}/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2 text-[14px]"><b>{item.author}</b><span className="rounded-pill bg-[#F1EBDF] px-2 py-0.5 text-[11px] text-secondary">{item.author_role}</span></div><div className="mt-0.5 text-[12px] text-muted">{item.source_context ?? 'Question bank discussion'} · {new Date(item.created_at).toLocaleDateString('en-IN')}</div></div><span className="rounded-pill bg-community-soft px-2.5 py-1 text-[12px] font-semibold text-community-dark">{item.kind === 'doubt' ? 'Doubt' : 'Explanation'}</span></div><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="mt-3 block font-display text-[20px] leading-snug hover:text-link">{item.question}</Link><p className="mt-3 whitespace-pre-wrap text-[15px] leading-relaxed">{item.body}</p>{item.accepted_answer && <div className="mt-3 rounded-[10px] bg-[#DCEFE1] px-4 py-3.5"><div className="text-[12px] font-semibold text-[#1F6234]">✓ Accepted reply · community feedback</div><p className="mt-2 whitespace-pre-wrap text-[14px] leading-relaxed">{item.accepted_answer}</p></div>}<div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-[#F1EBDF] pt-3 text-[13px] text-secondary"><span className="font-semibold">▲ {item.helpful} helpful</span><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="font-semibold">Open discussion →</Link></div></article> }
