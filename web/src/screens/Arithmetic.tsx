import {AnswerOptions,AnswerLayoutControl} from '../components/AnswerLayout'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import content from '../data/arithmetic-content.json'
import reasoningContent from '../data/reasoning-content.json'
import { getLearningProgress, listQuestionPapers, listQuestions, listTaxonomy, saveLearningProgress, type LearningProgressItem, type QuestionPage, type QuestionPaperSummary, type TaxonomyFacet } from '../lib/api'
import { SourceQuestionText } from '../components/SourceQuestionText'
import QuestionCard from '../components/QuestionCard'

type Concept = { id: string; name: string; analogy: string; explain: string; formulas: string[]; variant: { q: string; options: string[]; answer: number; solution: string } }
type Progress = Record<string, { visited: boolean; correct: boolean | null }>
const CONCEPTS = [...content as Concept[], ...reasoningContent as Concept[]]
const PROGRESS_KEY = 'ism-arithmetic-progress-v1'
const PAGE_SIZE = 10

function readProgress(): Progress {
  try { return JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}') as Progress } catch { return {} }
}

export default function Arithmetic() {
  const [params, setParams] = useSearchParams()
  const [section, setSection] = useState<'learn' | 'practice' | 'papers'>(() => {
    const view = params.get('view')
    return view === 'practice' || view === 'papers' ? view : 'learn'
  })
  const [subject, setSubject] = useState<'mathematics' | 'reasoning-and-aptitude'>(() =>
    params.get('subject') === 'reasoning-and-aptitude' || (reasoningContent as Concept[]).some((c) => c.id === params.get('topic')) ? 'reasoning-and-aptitude' : 'mathematics',
  )
  const [facets, setFacets] = useState<TaxonomyFacet[]>([])
  const [taxonomyError, setTaxonomyError] = useState('')
  const [topicId, setTopicId] = useState('')
  const [topicName, setTopicName] = useState('All topics')
  const [conceptId, setConceptId] = useState(() => CONCEPTS.some((c) => c.id === params.get('topic')) ? params.get('topic')! : CONCEPTS[0].id)
  const [progress, setProgress] = useState<Progress>(readProgress)
  const progressRef = useRef(progress)
  const locallyTouched = useRef(new Set<string>())
  const syncSequence = useRef(0)
  const [progressSync, setProgressSync] = useState<'loading' | 'saved' | 'device-only'>('loading')
  const [choice, setChoice] = useState<number | null>(null)
  const [page, setPage] = useState<QuestionPage | null>(null)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [papers, setPapers] = useState<QuestionPaperSummary[]>([])
  const [paperTotal, setPaperTotal] = useState(0)
  const [paperOffset, setPaperOffset] = useState(0)
  const [paperQuery, setPaperQuery] = useState('')
  const [paperLoading, setPaperLoading] = useState(false)
  const [paperError, setPaperError] = useState('')
  const concepts = useMemo(() => CONCEPTS.filter((c) => (subject === 'mathematics' ? !('cat' in c) || (c as Concept & {cat?: string}).cat !== 'reas' : (c as Concept & {cat?: string}).cat === 'reas')), [subject])
  const active = concepts.find((c) => c.id === conceptId) ?? concepts[0]
  const subjectFacets = facets.filter((f) => f.subject_id === subject && f.topic_id)
  const subjectCount = facets.find(f=>f.subject_id===subject)?.subject_questions ?? facets.filter((f) => f.subject_id === subject).reduce((n, f) => n + f.questions, 0)
  const selectedCount = topicId ? (subjectFacets.find((f) => f.topic_id === topicId)?.questions ?? 0) : subjectCount
  const paperPages = Math.max(1, Math.ceil(paperTotal / 20))

  useEffect(() => {
    if (section !== 'practice') return
    let cancelled = false
    getLearningProgress('arithmetic').then(({ items }) => {
      if (cancelled) return
      const remote = new Map(items.map((item) => [item.item_id, item]))
      const merged: Progress = { ...progressRef.current }
      for (const item of items) {
        if (!locallyTouched.current.has(item.item_id)) {
          merged[item.item_id] = { visited: item.visited, correct: item.correct }
        }
      }
      progressRef.current = merged
      setProgress(merged)
      try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(merged)) } catch { /* API remains the durable copy. */ }
      const localOnly: LearningProgressItem[] = Object.entries(merged)
        .filter(([id]) => !remote.has(id))
        .map(([item_id, value]) => ({ item_id, ...value }))
      if (localOnly.length) return saveLearningProgress('arithmetic', localOnly)
    }).then(() => { if (!cancelled) setProgressSync('saved') })
      .catch(() => { if (!cancelled) setProgressSync('device-only') })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    listTaxonomy('all').then((all) => { if (!cancelled) { setFacets(all); setTaxonomyError('') } }).catch((e) => { if (!cancelled) setTaxonomyError(e.message || 'Topic list is temporarily unavailable.') })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true); setError('')
    listQuestions({ pool: 'all', subject_id: subject, topic_id: topicId || undefined, limit: PAGE_SIZE, offset })
      .then((result) => { if (!cancelled) setPage(result) })
      .catch((e) => { if (!cancelled) { setError(e.message || 'Questions could not be loaded.'); setPage(null) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [section, subject, topicId, offset, reloadKey])

  useEffect(() => {
    if (section !== 'papers') return
    let cancelled = false
    setPaperLoading(true); setPaperError('')
    const timer = window.setTimeout(() => {
      listQuestionPapers({ subject_id: subject, q: paperQuery.trim().length >= 2 ? paperQuery.trim() : undefined, limit: 20, offset: paperOffset })
        .then((result) => { if (!cancelled) { setPapers(result.items); setPaperTotal(result.total) } })
        .catch((e) => { if (!cancelled) setPaperError(e.message || 'Source papers could not be loaded.') })
        .finally(() => { if (!cancelled) setPaperLoading(false) })
    }, 180)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [section, subject, paperQuery, paperOffset])

  function changeSubject(value: 'mathematics' | 'reasoning-and-aptitude') {
    setSubject(value); setTopicId(''); setTopicName('All topics'); setOffset(0)
    const first = CONCEPTS.find((c) => value === 'mathematics' ? !('cat' in c) || (c as Concept & {cat?: string}).cat !== 'reas' : (c as Concept & {cat?: string}).cat === 'reas')
    if (first) { setConceptId(first.id); setChoice(null); const next = new URLSearchParams(params); next.set('topic', first.id); setParams(next, { replace: true }) }
  }
  function chooseTopic(id: string, label: string) { setTopicId(id); setTopicName(label); setOffset(0) }
  function changeSection(value: 'learn' | 'practice' | 'papers') {
    setSection(value)
    const next = new URLSearchParams(params)
    if (value === 'learn') next.delete('view')
    else next.set('view', value)
    setParams(next, { replace: true })
  }
  function saveCheck(itemId: string, correct: boolean | null) {
    locallyTouched.current.add(itemId)
    const next = { ...progressRef.current, [itemId]: { visited: true, correct } }
    progressRef.current = next
    setProgress(next)
    try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(next)) } catch { /* Keep the current session usable without storage. */ }
    const sequence = ++syncSequence.current
    saveLearningProgress('arithmetic', [{ item_id: itemId, visited: true, correct }])
      .then(() => { if (sequence === syncSequence.current) setProgressSync('saved') })
      .catch(() => { if (sequence === syncSequence.current) setProgressSync('device-only') })
  }
  function answer(index: number) {
    if (choice !== null || !active) return
    setChoice(index); saveCheck(active.id, index === active.variant.answer)
  }

  return <main className="mx-auto max-w-shell px-6 pb-24 pt-9">
    <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-practice-dark">MPSC aptitude · shared question bank</div>
    <header className="mt-2 grid gap-5 border-b border-hairline pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
      <div><h1 className="font-display text-[clamp(36px,5vw,52px)] font-medium leading-[1.05] -tracking-[0.02em]">Arithmetic &amp; Reasoning</h1>
        <p className="mt-3 max-w-[760px] text-[17px] leading-relaxed text-secondary">Learn a method, practise tagged questions from the single bank, or browse the original MPSC papers. Source directions, emphasis and available figures travel with each question.</p></div>
      <div className="rounded-[12px] border border-hairline bg-card px-4 py-3"><div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">Topic questions</div><div className="mt-1 font-display text-[25px]">{subjectCount.toLocaleString('en-IN')}</div><div className="text-[12px] text-secondary">{subject === 'mathematics' ? 'Mathematics' : 'Reasoning & aptitude'}</div></div>
    </header>

    <nav aria-label="Study mode" className="mt-6 flex flex-wrap gap-2">
      {([['learn','Learn ideas'],['practice','Topic practice'],['papers','Exams & papers']] as const).map(([key,label]) => <button key={key} onClick={() => changeSection(key)} aria-pressed={section === key} className={`min-h-11 rounded-pill border px-4 py-2 text-[13px] font-semibold ${section === key ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card text-secondary'}`}>{label}</button>)}
      <Link to="/exams" className="ml-auto inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 py-2 text-[13px] font-semibold">All exam tracks →</Link>
    </nav>
    <div className="mt-5 flex flex-wrap gap-2" aria-label="Choose subject">
      {([['mathematics','Arithmetic & Mathematics'],['reasoning-and-aptitude','Reasoning']] as const).map(([id,label]) => <button key={id} onClick={() => changeSubject(id)} aria-pressed={subject === id} className={`min-h-10 rounded-[8px] px-3 py-2 text-[13px] font-semibold ${subject === id ? 'bg-[#E2EEE8] text-[#245F45]' : 'bg-paper text-secondary'}`}>{label}</button>)}
    </div>

    {section === 'learn' && <MaterialDiscovery subjectId={subject} title={subject==='mathematics'?'Arithmetic study notes':'Reasoning study notes'}/>}
    {section === 'learn' && active && <div className="mt-6 grid gap-6 lg:grid-cols-[270px_minmax(0,1fr)]">
      <nav aria-label={`${subject} concepts`} className="grid h-fit grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-1">{concepts.map((c,i) => <button key={c.id} onClick={() => { setConceptId(c.id); setChoice(null); saveCheck(c.id, progress[c.id]?.correct ?? null); const next = new URLSearchParams(params); next.set('topic', c.id); setParams(next, { replace: true }) }} aria-current={c.id === active.id ? 'step' : undefined} className={`flex min-h-12 items-center gap-2 rounded-[9px] border px-3 py-2 text-left text-[12px] ${c.id === active.id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card'}`}><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[#EFE8D8] font-mono text-[10px] text-ink">{progress[c.id]?.correct ? '✓' : i+1}</span><span>{c.name}</span></button>)}</nav>
      <section className="min-w-0 rounded-[14px] border border-hairline bg-card p-5 sm:p-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">{subject === 'mathematics' ? 'Arithmetic concept' : 'Reasoning concept'}</div><h2 className="mt-2 font-display text-[30px] font-medium leading-tight">{active.name}</h2>
        <div className="mt-5 rounded-[10px] border-l-[3px] border-[#D9842F] bg-[#FFF6EA] px-4 py-3 text-[14px] leading-relaxed"><SourceQuestionText text={active.analogy} /></div>
        <p className="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-secondary"><SourceQuestionText text={active.explain} /></p>
        <h3 className="mt-6 font-display text-[20px] font-medium">Method and reminders</h3><ul className="mt-3 grid gap-2 sm:grid-cols-2">{active.formulas.map((f,i)=><li key={i} className="rounded-[9px] border border-hairline bg-paper px-3 py-2.5 text-[13px] leading-relaxed"><SourceQuestionText text={f}/></li>)}</ul>
        <div className="mt-7 rounded-[12px] border border-hairline p-4 sm:p-5"><div className="font-mono text-[10px] uppercase tracking-[0.1em] text-practice-dark">Worked concept check · teaching example</div><p className="mt-2 text-[15px] font-semibold leading-relaxed"><SourceQuestionText text={active.variant.q}/></p><AnswerLayoutControl/><AnswerOptions className="mt-3">{active.variant.options.map((option,i)=>{const correct=choice!==null&&i===active.variant.answer;const wrong=choice===i&&!correct;return <button key={i} disabled={choice!==null} onClick={()=>answer(i)} data-answer-state={correct?'correct':wrong?'wrong':'neutral'} className={`answer-option flex min-h-11 items-start gap-2 rounded-[8px] border px-3 py-2.5 text-left text-[13px] ${correct?'border-[#2F8559] bg-[#E0F0E6]':wrong?'border-[#C2503A] bg-[#F7E2DC]':'border-hairline bg-card'}`}><span className="font-mono">{String.fromCharCode(65+i)}.</span><SourceQuestionText text={option}/></button>})}</AnswerOptions>{choice!==null&&<p className="mt-3 rounded-[8px] bg-[#EFF6F3] p-3 text-[13px] leading-relaxed"><strong>{choice===active.variant.answer?'Correct. ':'Review the method. '}</strong><SourceQuestionText text={active.variant.solution}/></p>}{choice!==null&&<button onClick={()=>setChoice(null)} className="mt-3 rounded-pill border border-ink px-3 py-2 text-[12px] font-semibold">Try again</button>}</div>
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4"><p className="text-[11px] text-muted">{progressSync === 'loading' ? 'Syncing lesson progress…' : progressSync === 'saved' ? 'Lesson progress saved to your study profile.' : 'Lesson progress is saved on this device; reconnect to sync it to your profile.'} Lesson notes adapted from the India Study Map MPSC Maths &amp; Reasoning hub. Scored practice below uses only canonical bank questions.</p><button onClick={()=>changeSection('practice')} className="rounded-pill bg-ink px-4 py-2 text-[12px] font-semibold text-paper">Practise bank questions →</button></div>
      </section>
    </div>}

    {section === 'practice' && <section className="mt-6" aria-labelledby="topic-practice-title">
      <div className="rounded-[12px] border border-[#D7E5E0] bg-[#EFF6F3] p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 id="topic-practice-title" className="font-display text-[24px]">Practise by topic</h2><p className="mt-1 text-[13px] text-secondary">{topicName} · {selectedCount.toLocaleString('en-IN')} approved questions tagged here. Each card keeps its source, answer status and any available scan figure.</p></div><Link to={`/bank?subject_id=${encodeURIComponent(subject)}${topicId?`&topic_id=${encodeURIComponent(topicId)}`:''}`} className="rounded-pill bg-ink px-4 py-2.5 text-[12px] font-semibold text-paper">Open bank filters →</Link></div></div>
      <div className="mt-4 flex flex-wrap gap-2"><button onClick={()=>chooseTopic('','All topics')} aria-pressed={!topicId} className={`min-h-10 rounded-pill border px-3 py-2 text-[12px] ${!topicId?'border-ink bg-ink text-paper':'border-hairline bg-card'}`}>All topics · {subjectCount}</button>{subjectFacets.map(f=><button key={f.topic_id} onClick={()=>chooseTopic(f.topic_id!,f.topic!)} aria-pressed={topicId===f.topic_id} className={`min-h-10 rounded-pill border px-3 py-2 text-[12px] ${topicId===f.topic_id?'border-ink bg-ink text-paper':'border-hairline bg-card'}`}>{f.topic} · {f.questions.toLocaleString('en-IN')}</button>)}</div>
      {taxonomyError&&<p role="status" className="mt-3 text-[12px] text-muted">Topic counts could not be refreshed: {taxonomyError}. You can still load the shared bank questions.</p>}
      {error&&<div role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-[13px] text-mypick">{error}<button onClick={()=>setReloadKey((v)=>v+1)} className="ml-2 font-semibold underline">Retry</button></div>}
      {loading&&<p role="status" className="mt-5 text-[13px] text-muted">Loading {subject === 'mathematics'?'mathematics':'reasoning'} questions…</p>}
      {page&&<><AnswerLayoutControl/><div className="mt-5 flex items-center justify-between border-b border-hairline pb-2 text-[12px] text-secondary"><span>{page.total.toLocaleString('en-IN')} questions · newest repeated items first</span><span>{page.total?offset+1:0}–{Math.min(offset+PAGE_SIZE,page.total)}</span></div><div className="mt-3 grid gap-3">{page.items.map((q)=><QuestionCard key={q.id} q={q}/>)}</div><div className="mt-4 flex items-center justify-between"><button disabled={offset===0||loading} onClick={()=>setOffset(Math.max(0,offset-PAGE_SIZE))} className="rounded-pill border border-ink px-4 py-2 text-[13px] disabled:opacity-40">Previous</button><span className="font-mono text-[11px] text-muted">{Math.floor(offset/PAGE_SIZE)+1} / {Math.max(1,Math.ceil(page.total/PAGE_SIZE))}</span><button disabled={offset+PAGE_SIZE>=page.total||loading} onClick={()=>setOffset(offset+PAGE_SIZE)} className="rounded-pill border border-ink px-4 py-2 text-[13px] disabled:opacity-40">Next</button></div></>}
    </section>}

    {section === 'papers' && <section className="mt-6" aria-labelledby="papers-title">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">Original source papers</div><h2 id="papers-title" className="mt-1 font-display text-[28px]">Browse {subject === 'mathematics'?'maths':'reasoning'} in exam context</h2><p className="mt-1 text-[13px] text-secondary">Search past papers, inspect the source PDF, and follow its page reference back to the same bank questions.</p></div><label className="w-full max-w-sm"><span className="sr-only">Search exam and paper</span><input value={paperQuery} onChange={(e)=>{setPaperQuery(e.target.value);setPaperOffset(0)}} placeholder="Exam, post, year, or paper…" className="min-h-11 w-full rounded-[8px] border border-hairline bg-card px-3 text-[13px]"/></label></div>
      <div className="mt-5"><div className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">Open a full exam workspace</div><div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{[['ldc','LDC'],['udc','UDC'],['assistant','Assistant'],['combined-prelims','Combined Prelims'],['group-b-gazetted','Group B · Gazetted'],['group-b-non-gazetted','Group B · Non-gazetted']].map(([id,label])=><Link key={id} to={`/exams/${id}`} className="flex min-h-11 items-center justify-between rounded-[9px] border border-hairline bg-card px-3 py-2 text-[13px] font-semibold hover:bg-exams-soft"><span>{label}</span><span aria-hidden="true">→</span></Link>)}</div><p className="mt-2 text-[11px] text-muted">Exam workspaces include paper-wise question views, topic practice, progress and timed tests where source rules allow.</p></div>
      {paperError&&<p role="alert" className="mt-4 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{paperError}</p>}{paperLoading&&<p className="mt-4 text-[13px] text-muted">Loading source papers…</p>}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">{papers.map(p=><article key={p.id} className="rounded-[12px] border border-hairline bg-card p-4"><div className="font-mono text-[10px] uppercase tracking-wide text-practice-dark">{p.year??'Year not listed'} · {p.exam_type.replace('_',' ')}</div><h3 className="mt-1 font-display text-[20px] leading-snug">{p.exam||p.source_file?.split('/').pop()||'MPSC paper'}{p.paper_number?` · Paper ${p.paper_number}`:''}</h3><p className="mt-2 text-[12px] text-secondary">{p.questions.toLocaleString('en-IN')} printed questions · {p.scorable.toLocaleString('en-IN')} verified-key · {p.answered.toLocaleString('en-IN')} with an answer</p><div className="mt-3 flex flex-wrap gap-3">{p.source_pdf_url?<a target="_blank" rel="noreferrer" href={p.source_pdf_url} className="text-[12px] font-semibold text-link underline underline-offset-2">Open source paper ↗</a>:<span className="text-[12px] text-muted">Source PDF unavailable</span>}<Link to={`/bank?subject_id=${encodeURIComponent(subject)}&paper_id=${encodeURIComponent(p.id)}`} className="text-[12px] font-semibold text-link underline underline-offset-2">Browse this paper’s questions →</Link></div></article>)}</div>
      {!paperLoading&&!papers.length&&!paperError&&<p className="mt-4 rounded-[10px] border border-hairline bg-card p-4 text-[13px] text-secondary">No source papers matched. Try a shorter exam or year search.</p>}
      <div className="mt-4 flex items-center justify-between"><button disabled={paperOffset===0||paperLoading} onClick={()=>setPaperOffset(Math.max(0,paperOffset-20))} className="rounded-pill border border-ink px-4 py-2 text-[13px] disabled:opacity-40">Previous</button><span className="font-mono text-[11px] text-muted">{Math.floor(paperOffset/20)+1} / {paperPages} · {paperTotal.toLocaleString('en-IN')} papers</span><button disabled={paperOffset+20>=paperTotal||paperLoading} onClick={()=>setPaperOffset(paperOffset+20)} className="rounded-pill border border-ink px-4 py-2 text-[13px] disabled:opacity-40">Next</button></div>
    </section>}
  </main>
}
