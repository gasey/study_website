import {ContributorName,GuideStrip} from '../components/ContributorStanding'
import {CommunityFeedback} from '../components/BlockAuthor'
import {EditMarker} from '../components/PostEditing'
import CommunityText from '../components/CommunityText'
import {UserAvatar} from '../components/AvatarArt'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate,useSearchParams } from 'react-router-dom'
import { lazy, Suspense } from 'react'
const Materials=lazy(()=>import('./Materials'))
const FollowingMaterials=lazy(()=>import('./Creators').then(m=>({default:m.FollowingMaterials})))
const CommunityQuestions=lazy(()=>import('./CommunityQuestions'))
const StudyComposer=lazy(()=>import('../components/StudyPosts').then(m=>({default:m.StudyComposer})))
const StudyPostDetail=lazy(()=>import('../components/StudyPosts').then(m=>({default:m.StudyPostDetail})))
import { Card } from '../components/ui'
import { getCommunityFeed, type CommunityFeedItem, type CommunityFeedResponse } from '../lib/api'

const TABS: { id: CommunityFeedResponse['tab']; label: string }[] = [
  { id: 'for-you', label: 'For you' }, { id: 'following', label: 'Following' },
  { id: 'questions', label: 'Doubts' }, { id: 'mcqs', label: 'MCQs' }, { id: 'materials', label: 'Materials' },
]
const COMPOSE = ['Doubt', 'Note', 'Share material', 'MCQ']

export default function Feed({embedded=false}:{embedded?:boolean}) {
  const nav=useNavigate()
  const [feedParams,setFeedParams]=useSearchParams()
  useEffect(()=>{if(feedParams.get('section')==='community')document.getElementById('community-section')?.scrollIntoView({block:'start'})},[feedParams])
  const [localTab,setLocalTab]=useState<CommunityFeedResponse['tab']>('for-you')
  const [localDiscussion,setLocalDiscussion]=useState<'all'|'doubts'|'unanswered'>('all')
  const rawTab=embedded?localTab:feedParams.get('tab')==='doubts'?'questions':feedParams.get('tab')
  const tab:CommunityFeedResponse['tab']=TABS.some(t=>t.id===rawTab)?rawTab as CommunityFeedResponse['tab']:'for-you'
  const rawDiscussion=embedded?localDiscussion:feedParams.get('discussion') ?? (feedParams.get('tab')==='doubts'?'doubts':'all')
  const discussion: 'all' | 'doubts' | 'unanswered' = rawDiscussion==='doubts'||rawDiscussion==='unanswered'?rawDiscussion:'all'
  const setTab=(value:CommunityFeedResponse['tab'])=>{setOffset(0);if(embedded){setLocalTab(value);return}setFeedParams(previous=>{const next=new URLSearchParams();if(previous.has('exam_scope'))next.set('exam_scope',previous.get('exam_scope')!);next.set('tab',value);return next},{replace:true})}
  const [result, setFeed] = useState<CommunityFeedResponse | null>(null)
  const feed = result?.tab === tab ? result : null
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [reload, setReload] = useState(0)
  const [offset, setOffset] = useState(0)
  const [composeType, setComposeType] = useState<string | null>(null)
  const studyId=/^\d+$/.test(feedParams.get('study')||'')?Number(feedParams.get('study')):null
  const composeKind=feedParams.get('compose')==='material-share'?'material-share':'study'
  const composingStudy=['study','material-share'].includes(feedParams.get('compose')||'')
  const closeStudy=()=>{setFeedParams(previous=>{const next=new URLSearchParams(previous);next.delete('study');next.delete('compose');return next},{replace:true});setReload(n=>n+1)}
  const generation = useRef(0)

  useEffect(() => {
    const update = () => {++generation.current;setFeed(null);setLoading(true);setComposeType(null);setOffset(0);setReload(n=>n+1)}
    window.addEventListener('ism-auth-change',update);window.addEventListener('ism-auth-expired',update);window.addEventListener('ism-community-change',update)
    return () => {++generation.current;window.removeEventListener('ism-auth-change',update);window.removeEventListener('ism-auth-expired',update);window.removeEventListener('ism-community-change',update)}
  }, [])

  useEffect(() => {
    if(tab==='materials'||tab==='mcqs')return
    let active = true
    const run = ++generation.current
    if(offset===0)setFeed(null)
    setLoading(true)
    setError(false)
    getCommunityFeed(tab, offset, tab==='questions'?discussion:'all').then((result) => {
      if (active && run===generation.current) setFeed((previous) => offset === 0 || previous?.tab!==result.tab ? result : { ...result, items: [...previous.items, ...result.items.filter(item=>!previous.items.some(old=>old.id===item.id))] })
    }).catch(() => { if (active && run===generation.current) setError(true) }).finally(() => { if (active && run===generation.current) setLoading(false) })
    return () => { active = false }
  }, [tab, discussion, offset, reload])

  const startCompose = (type: string) => type === 'MCQ' ? nav('/create/new?kind=new_question') : type==='Note'?nav('/community?compose=study'):type==='Share material'?nav('/community?compose=material-share'):['Material','Post'].includes(type)?nav('/studio/new'):setComposeType(type)

  return <div className={embedded?'finna-embedded-community':'mx-auto max-w-shell px-4 pb-24 pt-6 sm:px-6 sm:pt-6'}>
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="font-mono text-xs uppercase tracking-widest text-community-dark">Learn together</p><h1 className="mt-2 font-display text-3xl">Community</h1><p className="mt-2 text-sm text-secondary">Questions, shared reading and conversations.</p></div><Link to="/create" className="inline-flex min-h-11 items-center rounded-pill bg-ink px-5 text-sm font-semibold text-paper">Create & contribute →</Link></header>
    <div className="mx-auto min-w-0 max-w-4xl">
      {!studyId&&<><CommunityFeedback/><GuideStrip/></>}{composingStudy&&<Suspense fallback={<p role="status">Opening note composer…</p>}><StudyComposer key={composeKind} kind={composeKind} onClose={closeStudy} onSaved={id=>{setFeedParams(previous=>{const next=new URLSearchParams(previous);next.delete('compose');next.set('study',String(id));return next},{replace:true});setReload(n=>n+1)}}/></Suspense>}
      {studyId&&<Suspense fallback={<p role="status">Opening study note…</p>}><StudyPostDetail id={studyId} onClose={closeStudy}/></Suspense>}
      <section className="min-w-0">
        <div id="community-section" className="mb-2 mt-8 scroll-mt-32 flex flex-wrap items-end justify-end gap-3"><h2 className="sr-only">Community feed</h2><details className="relative"><summary className="min-h-11 cursor-pointer rounded-pill border border-hairline bg-card px-4 py-3 text-sm font-semibold">Share or ask</summary><div className="absolute right-0 z-10 mt-2 grid min-w-[180px] gap-1 rounded-panel border border-hairline bg-card p-2 shadow-lg">{COMPOSE.map(type=><button key={type} type="button" onClick={()=>startCompose(type)} className="min-h-11 rounded-lg px-4 text-left text-sm hover:bg-canvas">{type==='Doubt'?'Ask a doubt':type==='Note'?'Share a study note':type==='Share material'?'Share a reviewed material':'Contribute an MCQ'}</button>)}</div></details></div>
        <div className="mt-4 flex gap-1 overflow-x-auto rounded-pill border border-hairline bg-card p-1 shadow-[0_1px_2px_rgba(29,27,24,.05)]" role="tablist" aria-label="Community feed filters">{TABS.map((item) => <button key={item.id} type="button" id={`community-tab-${item.id}`} role="tab" aria-controls="community-tab-panel" tabIndex={tab===item.id?0:-1} aria-selected={tab === item.id} onKeyDown={event=>{const index=TABS.findIndex(t=>t.id===tab);const next=event.key==='Home'?0:event.key==='End'?TABS.length-1:event.key==='ArrowRight'?(index+1)%TABS.length:event.key==='ArrowLeft'?(index+TABS.length-1)%TABS.length:-1;if(next>=0){event.preventDefault();setTab(TABS[next].id);document.getElementById(`community-tab-${TABS[next].id}`)?.focus()}}} onClick={() => { setOffset(0); setTab(item.id) }} className={`min-h-10 shrink-0 rounded-pill px-4 py-2 text-sm font-semibold transition ${tab === item.id ? 'bg-ink text-white' : 'text-secondary hover:bg-[#F7F3EA] hover:text-ink'}`}>{item.label}</button>)}</div>

        <div id="community-tab-panel" role="tabpanel" aria-labelledby={`community-tab-${tab}`} tabIndex={0} className="min-w-0">
        {tab==='materials'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading materials…</p>}><Materials embedded/></Suspense>:tab==='mcqs'?<Suspense fallback={<p role="status" className="p-6 text-muted">Loading community practice…</p>}><CommunityQuestions embedded/></Suspense>:<>
        {tab==='following'&&<section className="mt-3 rounded-panel border border-hairline bg-card p-4"><h2 className="font-display text-lg">From people you follow</h2><p className="mt-1 text-sm text-secondary">Study notes, material shares and published discussions, newest first. Linked question content unlocks after you check or show its answer.</p><Link to="/creators" className="inline-flex min-h-11 items-center text-sm font-semibold text-link">Find creators →</Link><details><summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">Materials from followed creators</summary><Suspense fallback={<p>Loading followed materials…</p>}><FollowingMaterials key={reload} embedded/></Suspense></details></section>}
        {tab==='questions'&&<div className="mt-3 rounded-panel border border-hairline bg-card p-4"><h2 className="font-display text-lg">Questions & Doubts</h2><p className="mt-1 text-sm leading-relaxed text-secondary">Discuss a question, explain your reasoning or help with a doubt. These are the same conversations shown on each question. Answer it first to reveal discussion; active mocks stay protected.</p><div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Question discussion filters">{([['all','All discussions'],['doubts','Doubts'],['unanswered','Unanswered doubts']] as const).map(([value,label])=><button key={value} type="button" aria-pressed={discussion===value} onClick={()=>{setOffset(0);if(embedded){setLocalDiscussion(value);return}setFeedParams(previous=>{const next=new URLSearchParams(previous);next.set('tab','questions');next.set('discussion',value);return next})}} className={`min-h-11 rounded-pill border px-3 py-2 text-xs font-semibold ${discussion===value?'border-ink bg-ink text-paper':'border-hairline text-secondary'}`}>{label}</button>)}<Link to="/bank" className="inline-flex min-h-11 items-center px-3 text-xs font-semibold text-link">Find a question to discuss →</Link></div><p className="mt-2 text-xs text-muted">Unanswered means no published reply visible to you. For an incorrect question or key, use Suggest correction on the question.</p></div>}

        {tab==='for-you'&&<MaterialDiscovery title="Reading for your next study break" compact/>}
        <div aria-live="polite" className="mt-3 space-y-3">
          {loading && offset === 0 ? <Card className="p-8 text-center text-sm text-muted">Loading discussions…</Card> : error && offset === 0 ? <Card className="p-8 text-center"><p className="text-sm">The community feed couldn’t load.</p><button type="button" className="mt-2 min-h-10 px-3 text-xs font-semibold text-link" onClick={() => setReload((n) => n + 1)}>Try again</button></Card> : !feed?.available ? <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">···</div><p className="mt-3 font-display text-md">This space is not open yet</p><p className="mx-auto mt-1 max-w-md text-sm leading-relaxed text-secondary">{feed?.message}</p></Card> : feed.items.length === 0 ? <EmptyFeed title={tab==='questions'&&discussion==='unanswered'?'No unanswered doubts to show':'No posts to show yet'} message={feed?.message ?? 'Answer a question first; its published explanation or doubt will then appear here.'} /> : <>{feed.items.map((item) => ['study','material-share'].includes(item.kind)?<StudyCard key={item.id} item={item}/>:<Discussion key={item.id} item={item} />)}{(feed.has_more || error && offset > 0) && <div className="p-4 text-center"><button type="button" disabled={loading} onClick={() => error ? setReload((n) => n + 1) : setOffset((value) => value + 20)} className="min-h-11 rounded-pill border border-hairline bg-card px-4 py-2 text-xs font-semibold disabled:opacity-50">{loading ? 'Loading…' : error ? 'Retry loading discussions' : 'Load more discussions'}</button></div>}</>}
        </div>
        </>}
        </div>
      </section>


    </div>

    {composeType && <div className="fixed inset-0 z-[70] grid place-items-center bg-ink/55 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setComposeType(null) }}><section role="dialog" aria-modal="true" aria-labelledby="compose-preview-title" className="w-full max-w-md rounded-panel border border-hairline bg-card p-6 shadow-[0_20px_60px_rgba(0,0,0,.25)]"><div className="label text-community-dark">Community contribution</div><h2 id="compose-preview-title" className="mt-2 font-display text-xl font-medium">{composeType === 'Post' ? 'Share with the community' : `Create a ${composeType.toLowerCase()}`}</h2><p className="mt-2 text-sm leading-relaxed text-secondary">Choose a question in the bank or an exam, then use Discuss / Ask a doubt. The question and its source stay linked; published topics also appear in this feed.</p><div className="mt-5 flex flex-wrap justify-end gap-2"><button type="button" onClick={() => setComposeType(null)} className="min-h-11 rounded-pill border border-hairline px-4 py-2 text-sm font-semibold">Close</button><Link to="/bank" onClick={() => setComposeType(null)} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-sm font-semibold text-paper">Browse questions →</Link></div></section></div>}
  </div>
}

function EmptyFeed({ message, title }: { message: string; title: string }) { return <Card className="p-8 text-center"><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-community-soft text-community-dark">✳</div><p className="mt-3 font-display text-lg">{title}</p><p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-secondary">{message}</p><Link to="/bank" className="mt-4 inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-xs font-semibold text-paper">Explore the question bank →</Link></Card> }
function StudyCard({item}:{item:CommunityFeedItem}) {return <article className="min-w-0 rounded-panel border border-hairline bg-card p-[18px]"><div className="flex flex-wrap items-center gap-2 text-sm"><UserAvatar look={item.avatar} initials={item.author}/><ContributorName {...item}/><span className="rounded-pill bg-community-soft px-3 py-1 text-community-dark">{item.kind==='material-share'?'Material share':'Study note'}</span><span className="text-muted">{new Date(item.created_at).toLocaleDateString('en-IN')}</span></div>{item.topic_label&&<p className="mt-3 font-mono text-xs text-secondary">{item.topic_label}</p>}<EditMarker post={item}/><CommunityText body={item.body} className="mt-3 text-base leading-relaxed"/>{item.material&&<Link to={'/materials/'+encodeURIComponent(item.material.id)} className="mt-4 block break-words rounded-[8px] border border-hairline bg-paper p-4 text-sm font-semibold text-link">{item.material.label}<span className="mt-2 block text-xs font-normal text-secondary">Reviewed {item.material.format} · {item.material.access==='pro'?'Pro access':item.material.access==='paid-preview'?'Preview available':'Free to read'} →</span></Link>}<div className="mt-4 flex flex-wrap items-center gap-3 border-t border-hairline pt-3 text-sm"><span>{item.helpful} helpful</span>{item.study_reference&&<span className="text-secondary">Linked {item.study_reference.kind}</span>}<Link to={'/community?study='+item.id} className="inline-flex min-h-11 items-center font-semibold text-link">{item.kind==='material-share'?'Open material share →':'Open study note →'}</Link></div></article>}
function Discussion({ item }: { item: CommunityFeedItem }) { return <article className="rounded-panel border border-hairline bg-card p-[18px] pb-[14px] shadow-[0_1px_2px_rgba(29,27,24,.05)]"><div className="flex items-center gap-3"><UserAvatar look={item.avatar} initials={item.author}/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2 text-sm"><ContributorName {...item}/><span className="rounded-pill bg-[#F1EBDF] px-2 py-0.5 text-xs text-secondary">{item.author_role}</span></div><div className="mt-0.5 text-xs text-muted">{item.source_context ?? 'Question bank discussion'} · {new Date(item.created_at).toLocaleDateString('en-IN')}</div></div><span className="rounded-pill bg-community-soft px-2.5 py-1 text-xs font-semibold text-community-dark">{item.kind === 'doubt' ? 'Doubt' : 'Explanation'}</span></div><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="mt-3 block break-words font-display text-lg leading-snug hover:text-link">{item.question}</Link><EditMarker post={item}/><CommunityText body={item.body} className="mt-3 text-base leading-relaxed"/>{item.accepted_answer && <div className="mt-3 rounded-[10px] bg-correct-soft px-4 py-3.5"><div className="text-xs font-semibold text-correct-dark">✓ Accepted reply · community feedback</div>{item.accepted_answer_edited_at&&<p className="mt-2 text-xs text-secondary">Edited · {new Date(item.accepted_answer_edited_at).toLocaleDateString('en-IN')}</p>}<CommunityText body={item.accepted_answer} className="mt-2 text-sm leading-relaxed"/></div>}<div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-[#F1EBDF] pt-3 text-sm text-secondary"><span className="font-semibold">▲ {item.helpful} helpful</span><Link to={`/bank/${item.question_id}?post=${item.id}#discussion`} className="font-semibold">Open discussion →</Link></div></article> }
