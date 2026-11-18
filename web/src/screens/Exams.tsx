import '../styles/exam-experience.css'
import {choosePreferredExam} from '../lib/preferredExam'
import {MES_GUIDE} from '../lib/examGuideCatalog'
import {examPresentation,examCatalogLayout} from '../lib/examPresentation'
import { useEffect, useMemo, useState } from 'react'
import { Link,useSearchParams } from 'react-router-dom'
import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults} from '../lib/pagination'
import {
  getExamBookmarks, getExamProgress, isLaterExamCollection,
  listCollections, removeExamBookmark, saveExamBookmark,
  type Collection, type ExamProgressSummary,
} from '../lib/api'

type Filter = 'all' | 'saved'
type CatalogEntry = { type: 'collection'; collection: Collection } | { type: 'guide'; id: 'mes' }
const PAGE_SIZE = 8
const ALIASES: Record<string, string[]> = {
  ldc: ['ldc', 'lower division clerk'], udc: ['udc', 'upper division clerk'],
  prelims: ['prelims', 'preliminary', 'combined prelims'], mpsc: ['mpsc', 'mizoram public service commission'],
  gazetted: ['gazetted', 'gazette', 'group b'], gazette: ['gazetted', 'gazette', 'group b'],
  nongazetted: ['non gazetted', 'non-gazetted', 'ldc', 'udc'],
  assistant: ['assistant', 'assistant grade', 'assistant audit'],
}
const PHRASES: Record<string, string[]> = {
  'non gazetted': ['non gazetted', 'ldc', 'udc'], 'group b': ['group b', 'gazetted'],
  'combined prelims': ['combined prelims', 'preliminary'],
  'lower division clerk': ['lower division clerk', 'ldc'], 'upper division clerk': ['upper division clerk', 'udc'],
}
const examShort=(id:string,fallback:string)=>({udc:'UDC',ldc:'LDC',assistant:'Assistant','combined-prelims':'Combined Prelims','group-b-gazetted':'Group B Gazetted','group-b-non-gazetted':'Group B Non-Gazetted','iti-instructor-2026':'ITI Instructor'}[id]||fallback)
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
function matches(text: string, query: string) {
  const terms = norm(query).split(' ').filter(Boolean)
  const target = norm(text)
  const groups: string[][] = []
  for (let i = 0; i < terms.length;) {
    const phrase = Object.keys(PHRASES).sort((a, b) => b.length - a.length).find((p) => terms.slice(i, i + p.split(' ').length).join(' ') === p)
    if (phrase) { groups.push(PHRASES[phrase]); i += phrase.split(' ').length }
    else { groups.push(ALIASES[terms[i]] ?? [terms[i]]); i++ }
  }
  return groups.every((g) => g.some((alias) => target.includes(norm(alias))))
}

export default function Exams() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [progress, setProgress] = useState<Record<string, ExamProgressSummary>>({})
  const [bookmarks, setBookmarks] = useState<string[]>([])
  const [busyBookmark, setBusyBookmark] = useState<string | null>(null)
  const [params,setParams]=useSearchParams()
  const filter:Filter=params.get('exam_filter')==='saved'?'saved':'all',query=params.get('q')||'',page=pageNumber(params.get('page'))-1
  function filterURL(key:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);next.delete('page');return next},{replace:true})}
  const setFilter=(value:Filter)=>filterURL('exam_filter',value==='all'?'':value),setQuery=(value:string)=>filterURL('q',value)
  const goPage=(value:number)=>{setParams(previous=>{const next=new URLSearchParams(previous);if(value>1)next.set('page',String(value));else next.delete('page');return next});requestAnimationFrame(()=>scrollToResults('exam-library-heading'))}
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [catalogError,setCatalogError]=useState(false),[retry,setRetry]=useState(0)

  useEffect(() => {
    let live = true
    setLoading(true);setCatalogError(false);setError(null)
    listCollections().then((all) => {
      if (!live) return
      const order=['udc','ldc','combined-prelims','group-b-gazetted','group-b-non-gazetted','assistant'];const rank=(id:string)=>{const i=order.indexOf(id);return i<0?99:i}
      const available = all.filter((c) => c.kind === 'exam' && !isLaterExamCollection(c)).sort((a,b)=>rank(a.id)-rank(b.id))
      setCollections(available)
      setLoading(false)
    }).catch((e) => { if (live) { setError(e.message);setCatalogError(true); setLoading(false) } })
    Promise.all([getExamBookmarks(), getExamProgress()]).then(([saved, rows]) => {
      if (!live) return
      setBookmarks(saved.collection_ids)
      setProgress(Object.fromEntries(rows.map((row) => [row.collection_id, row])))
    }).catch(() => {})
    return () => { live = false }
  }, [retry])

  const mesVisible=filter==='all'&&!collections.some(c=>c.id==='mes')&&matches(MES_GUIDE.title+' '+MES_GUIDE.search,query)
  const shown = useMemo<CatalogEntry[]>(() => {
    const entries: CatalogEntry[] = collections.filter((c) => {
      const isSaved = bookmarks.includes(c.id)
      const typeMatch = filter === 'all' || isSaved
      return typeMatch && matches(`${c.title} ${c.id} ${c.kind}`, query)
    }).map(collection => ({ type: 'collection', collection }))
    return mesVisible ? [{ type: 'guide', id: 'mes' }, ...entries] : entries
  }, [collections, bookmarks, filter, query, mesVisible])
  const pages = Math.ceil(shown.length / PAGE_SIZE)
  const visible = shown.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  useEffect(()=>{if(!loading&&page>=Math.max(1,pages))setParams(previous=>{const next=new URLSearchParams(previous);if(pages>1)next.set('page',String(pages));else next.delete('page');return next},{replace:true})},[loading,page,pages,setParams])

  async function toggleBookmark(c: Collection) {
    const wasSaved = bookmarks.includes(c.id)
    setBusyBookmark(c.id)
    // Optimistic UI keeps browsing responsive; restore the saved state if the API fails.
    setBookmarks((old) => wasSaved ? old.filter((id) => id !== c.id) : [c.id, ...old])
    try {
      if (wasSaved) await removeExamBookmark(c.id)
      else await saveExamBookmark(c.id)
    } catch (e) {
      setBookmarks((old) => wasSaved ? [...old, c.id] : old.filter((id) => id !== c.id))
      setError(e instanceof Error ? `Could not update saved exams: ${e.message}` : 'Could not update saved exams.')
    } finally { setBusyBookmark(null) }
  }

  const layout=examCatalogLayout(params.get('exam_layout')),expanded=params.get('exam_open')||''
  function expand(id:string){setParams(previous=>{const next=new URLSearchParams(previous);if(next.get('exam_open')===id)next.delete('exam_open');else next.set('exam_open',id);return next},{replace:true})}
  const compared=(params.get('compare')||'').split(',').filter(id=>collections.some(c=>c.id===id)).slice(0,3)
  const comparison=collections.filter(c=>compared.includes(c.id))
  function toggleCompare(id:string){setParams(previous=>{const next=new URLSearchParams(previous);const ids=compared.includes(id)?compared.filter(x=>x!==id):[...compared,id].slice(0,3);if(ids.length)next.set('compare',ids.join(','));else next.delete('compare');return next},{replace:true})}
  const savedCount = bookmarks.filter((id) => collections.some((c) => c.id === id)).length

  return <div className="exam-experience"><div className="exam-catalog">
    <header className="exam-catalog-heading">
      <div><div className="exam-catalog-kicker">Exams</div><h1>Choose your exam</h1><p>Subjects, practice and original papers, all in one place.</p></div>
      <Link to="/desk">My study desk ↗</Link>
    </header>
    <section aria-labelledby="exam-library-heading">
      <div className="exam-catalog-toolbar">
        <label className="exam-catalog-search"><span className="sr-only">Search exam collections</span><input id="exam-search" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Find MES, UDC, LDC, Assistant, Prelims…"/></label>
        <div className="exam-segment" role="group" aria-label="Filter exams">{([['all','All exams'],['saved','Saved']] as const).map(([key,label])=><button key={key} type="button" onClick={()=>setFilter(key)} aria-pressed={filter===key}>{label}{key==='saved'?` (${savedCount})`:''}</button>)}</div>
        <div className="exam-segment" role="group" aria-label="Exam display">{(['cards','list'] as const).map(value=><button key={value} type="button" aria-pressed={layout===value} onClick={()=>filterURL('exam_layout',value)}>{value==='cards'?'Cards':'List'}</button>)}</div>
      </div>
      <div className="mt-5 flex items-baseline justify-between gap-3"><h2 id="exam-library-heading" tabIndex={-1} className="scroll-mt-28 font-display text-[25px]">{filter==='saved'?'Your saved exams':'Explore exams'}</h2><span role="status" className="text-xs text-secondary">{loading?'Loading…':`${shown.length} available`}</span></div>
      {error && <div role="status" className="mt-3 rounded-[10px] border border-mypick bg-mypick-soft p-3 text-[13px] text-mypick">{error}{catalogError?<button type="button" onClick={()=>setRetry(n=>n+1)} className="ml-2 min-h-11 underline">Retry exams</button>:<button type="button" onClick={() => setError(null)} className="ml-2 min-h-11 underline">Dismiss</button>}</div>}
      {loading && <div className="mt-4 grid gap-3 md:grid-cols-2" aria-label="Loading exams">{[1,2,3].map((i) => <div key={i} className="h-48 animate-pulse rounded-[14px] border border-hairline bg-card" />)}</div>}
      {!loading&&visible.length>0&&<div className="exam-catalog-results" data-layout={layout}>{visible.map(entry=>{
        if(entry.type==='guide')return <MesExamCard key={entry.id} open={expanded===entry.id} onExpand={()=>expand(entry.id)}/>
        const c=entry.collection
        const p=progress[c.id],saved=bookmarks.includes(c.id),identity=examPresentation(c.id),open=expanded===c.id
        const completion=p&&c.questions?Math.min(100,Math.round(100*p.unique_questions/c.questions)):0
        return <article key={c.id} className="finna-exam-card" data-exam-tone={identity.tone}>
          <Link className="finna-exam-title" onClick={()=>choosePreferredExam(c.id)} to={`/exams/${c.id}`}><h3>{examShort(c.id,c.title)}</h3><p>{c.title}</p></Link>
          <div className="finna-exam-pills"><span>{c.sections} {c.sections===1?'section':'sections'}</span><span>{c.questions.toLocaleString('en-IN')} questions</span></div>
          <div className="finna-exam-progress"><div className="finna-progress" role="progressbar" aria-label={`${c.title} coverage`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={completion}><span style={{width:completion+'%',background:'rgb(var(--ism-exams-rgb))'}}/></div><p>{p?`${p.unique_questions.toLocaleString('en-IN')} answered · ${completion}% covered`:'Your progress will appear here'}</p></div>
          <div className="finna-exam-actions"><Link className="finna-btn finna-btn-dark" onClick={()=>choosePreferredExam(c.id)} to={`/exams/${c.id}`}>Open</Link><button type="button" className="finna-btn finna-btn-quiet" disabled={busyBookmark!==null} onClick={()=>void toggleBookmark(c)} aria-pressed={saved} aria-label={`${saved?'Remove':'Save'} ${c.title} ${saved?'from':'to'} saved exams`}>{saved?'Saved':'Save'}</button><button type="button" className="finna-btn finna-btn-quiet" aria-pressed={compared.includes(c.id)} disabled={compared.length>=3&&!compared.includes(c.id)} onClick={()=>toggleCompare(c.id)} aria-label={`Compare ${c.title}`}>{compared.includes(c.id)?'Added':'Compare'}</button></div>
          <button type="button" className="self-start text-xs font-bold text-link" aria-expanded={open} aria-controls={'exam-options-'+c.id} aria-label={`${open?'Hide':'Show'} study options for ${c.title}`} onClick={()=>expand(c.id)}>Study options {open?'⌃':'⌄'}</button>
          <div id={'exam-options-'+c.id} hidden={!open} className="finna-exam-options"><nav aria-label={`${c.title} study options`}><Link to={`/exams/${c.id}?view=browse#exam-question-browser`}>Questions</Link><Link to={`/exams/${c.id}?view=topics#exam-study-heading`}>Subjects &amp; topics</Link><Link to={`/exams/${c.id}?view=papers#past-paper-results`}>Original papers</Link><Link to={`/exams/${c.id}?view=practice#exam-question-browser`}>Open practice →</Link></nav><p className="mt-2 text-xs text-secondary">{c.scorable.toLocaleString('en-IN')} official-key questions</p></div>
        </article>
      })}</div>}
      {!loading && !catalogError && !visible.length && <div className="mt-4 rounded-[14px] border border-dashed border-hairline bg-card p-8 text-center"><div className="font-display text-[22px]">{filter === 'saved' ? 'No saved exams match' : 'No matching exams'}</div><p className="mt-1 text-[13px] text-secondary">{filter === 'saved' ? 'Save an exam with the Save button, or clear your search to see all saved exams.' : 'Try a shorter search or clear the selected filter.'}</p>{(filter === 'saved'||query) && <button type="button" onClick={() => {setParams(previous=>{const next=new URLSearchParams(previous);next.delete('q');next.delete('exam_filter');next.delete('page');return next})}} className="mt-3 min-h-11 rounded-pill bg-ink px-4 py-2 text-[12px] font-semibold text-paper">Clear filters</button>}</div>}
      <Pagination page={page+1} pages={pages} disabled={loading} onPageChange={goPage} label="Exam collection pages"/>
    </section>
    {comparison.length>0&&<section className="finna-card mt-6 overflow-x-auto" aria-labelledby="compare-exams"><div className="finna-section-top"><h2 id="compare-exams" className="text-xl">Compare exams</h2><span className="text-xs text-secondary">{comparison.length} of 3 selected · live bank inventory</span></div><table className="w-full min-w-[500px] text-left text-sm"><thead><tr><th className="py-3 pr-4">In the bank</th>{comparison.map(c=><th key={c.id} className="px-4 py-3 text-exams-dark">{examShort(c.id,c.title)}<button type="button" onClick={()=>toggleCompare(c.id)} aria-label={'Remove '+c.title+' from comparison'} className="ml-2 inline-grid min-h-9 min-w-9 place-items-center text-secondary">×</button></th>)}</tr></thead><tbody>{[['Sections',(c:Collection)=>c.sections],['Questions',(c:Collection)=>c.questions],['Official-key questions',(c:Collection)=>c.scorable],['Questions attempted',(c:Collection)=>progress[c.id]?.unique_questions??'—']].map(([label,value])=><tr key={String(label)} className="border-t border-hairline"><th className="py-3 pr-4 font-semibold text-secondary">{String(label)}</th>{comparison.map(c=><td key={c.id} className="px-4 py-3">{typeof value==='function'?value(c).toLocaleString('en-IN'):''}</td>)}</tr>)}</tbody></table></section>}
    <section aria-label="Group B common subjects" className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-hairline bg-exams-soft px-4 py-3"><div><h2 className="font-display text-[23px]">Study across Group B exams</h2><p className="text-xs text-secondary">Common subjects or technical papers.</p></div><div className="flex flex-wrap gap-4"><Link className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link" to="/group-b">English &amp; GK/GS →</Link><Link className="inline-flex min-h-11 items-center text-[13px] text-link" to="/group-b?study_area=technical">Technical papers →</Link></div></section>
  </div></div>
}


function MesExamCard({open,onExpand}:{open:boolean;onExpand:()=>void}){
 return <article className="finna-exam-card" aria-label={MES_GUIDE.title}>
  <Link className="finna-exam-title" to="/exams/mes"><h3>MES</h3><p>{MES_GUIDE.title}</p></Link>
  <div className="finna-exam-pills"><span>{MES_GUIDE.branchCount} branches</span><span>{MES_GUIDE.paperCount} original papers</span></div>
  <p className="text-[13px] text-secondary">Choose your branch and regulations to explore the syllabus and source papers.</p>
  <div className="finna-exam-actions"><Link className="exam-choice-open" to="/exams/mes">Open</Link><button type="button" className="finna-btn finna-btn-quiet" aria-expanded={open} aria-controls="exam-options-mes" aria-label={`${open?'Hide':'Show'} study options for Mizoram Engineering Service (MES)`} onClick={onExpand}>Study options ⌄</button></div>
  <div id="exam-options-mes" hidden={!open} className="finna-exam-options"><nav aria-label="MES study options"><Link to="/exams/mes?view=browse">Questions</Link><Link to="/exams/mes?view=topics">Subjects &amp; syllabus</Link><Link to="/exams/mes?view=papers">Original papers</Link><Link to="/exams/mes?view=practice">Open practice →</Link></nav></div>
 </article>
}
