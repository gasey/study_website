import ExamPaperCard from '../components/ExamPaperCard'
import McsBookletGroup from '../components/McsBookletGroup'
import { groupMcsBooklets } from '../lib/mcsBooklets'
import Pagination from '../components/Pagination'
import {pageNumber,scrollToResults,focusWhenAvailable} from '../lib/pagination'
import '../styles/legacy-udc-ldc.css'
import '../styles/legacy-combined-prelims.css'
import '../styles/legacy-learning-dashboard.css'
import {answerStatusAppearance} from '../lib/answerStatus'
import MaterialDiscovery from '../components/MaterialDiscovery'
import { lazy,Suspense,useEffect, useState } from 'react'
import { Link, useParams, useSearchParams, useLocation } from 'react-router-dom'
import { getCollection, getCollectionHeader, getProgress, getExamBookmarks, isLaterExamCollection, prefetchQuestionPage, removeExamBookmark, saveExamBookmark, type CollectionDetail, type CollectionHeader, type ListParams } from '../lib/api'
const ExamJourney=lazy(()=>import('../components/ExamJourney'))
const ExamStudyTopics=lazy(()=>import('../components/ExamStudyTopics'))
import { ModuleProgressPanel, ModuleQuestionBrowser } from './ModuleStudy'

/** One exam's landing page — the prototype's `module` screen, line 1700.
 *  See docs/DESIGN-FIDELITY.md: "module" is the old name, and the
 *  prototype's `exam` screen is the timed paper, not this. */
export default function ExamPage() {
  const { id = '' } = useParams()
  const [metadata, setC] = useState<CollectionDetail | null>(null)
  const [header,setHeader]=useState<CollectionHeader|null>(null)
  const [headerError,setHeaderError]=useState('')
  const [retry,setRetry]=useState(0)
  const ready=metadata?.id===id?metadata:null
  const head=header?.id===id?header:null
  const c:CollectionDetail|null=ready||(head?{...head,sections:0,questions:0,scorable:0,practice_count:0,answerable_count:0,needs_review:0,unsolved:0,section_list:[],paper_list:[]}:null)
  const location=useLocation()
  const [error, setError] = useState<string | null>(null)
  const [answeredCount, setAnsweredCount] = useState<number | null>(null)
  const [bookmarked, setBookmarked] = useState(false)
  const [bookmarkBusy, setBookmarkBusy] = useState(false)
  const [bookmarkError,setBookmarkError]=useState('')
  const [searchParams, setSearchParams] = useSearchParams()
  const rawView = searchParams.get('view')
  const view: 'overview' | 'topics' | 'papers' | 'browse' | 'practice' | 'progress' = rawView === 'topics' || rawView === 'papers' || rawView === 'browse' || rawView === 'practice' || rawView === 'progress' ? rawView : 'overview'

  useEffect(()=>{
    const target=location.hash.slice(1)
    if(['exam-question-browser','exam-study-heading','past-paper-results'].includes(target))return focusWhenAvailable(target)
  },[id,view,location.hash])

  useEffect(() => {
    setC(previous=>previous?.id===id?previous:null)
    setHeader(previous=>previous?.id===id?previous:null);setHeaderError('')
    setError(null)
    let live=true
    // Begin the first question request alongside the collection metadata.
    // The browser reuses this in-flight result when the question panel mounts.
    const params=new URLSearchParams(window.location.search)
    const initialView=params.get('view')
    const initialStatus=params.get('status')||'all'
    if((initialView==='browse'||initialView==='practice')&&initialStatus==='all'&&(params.get('q')||'').length!==1){
      const pool=params.get('pool')
      const answerStatus=params.get('answer_status')
      const request:ListParams={collection_id:id,section_path:params.get('section')||undefined,paper_id:params.get('paper')||undefined,subject_id:params.get('subject_id')||undefined,topic_id:params.get('topic_id')||undefined,subtopic_id:params.get('subtopic_id')||undefined,q:params.get('q')||undefined,pool:pool==='all'||pool==='scorable'||pool==='practice'?pool:initialView==='practice'?'practice':'all',limit:initialView==='practice'?1:25,offset:Math.floor(Math.max(0,Math.min(100000,Number(params.get('offset'))||0))/(initialView==='practice'?1:25))*(initialView==='practice'?1:25)}
      if(answerStatus==='official'||answerStatus==='verified'||answerStatus==='needs-review'||answerStatus==='unsolved'||answerStatus==='written')request.answer_status=answerStatus
      prefetchQuestionPage(request)
    }
    getCollectionHeader(id).then(value=>{if(live)setHeader(value)}).catch(e=>{if(live)setHeaderError(e.message)})
    getCollection(id).then(c=>{if(live)setC(c)}).catch((e) => {if(live)setError(e.message)})
    getProgress(id).then((p) => {if(live)setAnsweredCount(p.answered)}).catch(() => {if(live)setAnsweredCount(null)})
    getExamBookmarks().then((saved) => {if(live)setBookmarked(saved.collection_ids.includes(id))}).catch(() => {if(live)setBookmarked(false)})
    return()=>{live=false}
  }, [id,retry])

  async function toggleBookmark() {
    if (!c || bookmarkBusy) return
    const wasBookmarked = bookmarked
    setBookmarked(!wasBookmarked)
    setBookmarkBusy(true)
    setBookmarkError('')
    try {
      if (wasBookmarked) await removeExamBookmark(c.id)
      else await saveExamBookmark(c.id)
    } catch(e) {
      setBookmarkError((e as Error).message)
      setBookmarked(wasBookmarked)
    } finally { setBookmarkBusy(false) }
  }

  if (!c && (error||headerError)) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-[14px] border border-mypick bg-mypick-soft p-5 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1">{error||headerError}</p><button type="button" onClick={()=>setRetry(n=>n+1)} className="mt-3 min-h-11 underline">Retry exam details</button>
        </div>
        <Link to="/exams" className="label mt-4 inline-block underline">← Exams</Link>
      </div>
    )
  }
  if (!c) return <main aria-busy="true" className="mx-auto max-w-shell px-6 py-10"><p role="status" className="label">Opening exam…</p><div aria-hidden="true" className="mt-4 h-40 animate-pulse rounded-xl bg-exams-soft"/></main>

  if (isLaterExamCollection(c)) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-[14px] border border-hairline bg-card p-6">
          <div className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted">Planned for later</div>
          <h1 className="mt-2 font-display text-[28px] font-medium">This exam is not open yet</h1>
          <p className="mt-2 text-[14px] text-secondary">We’ll add LDE exam practice as the exam library grows.</p>
        </div>
        <Link to="/exams" className="label mt-4 inline-block underline">← Exams</Link>
      </div>
    )
  }

  const general = c.section_list.filter((s) => s.path.startsWith('general/'))
  const technical = c.section_list.filter((s) => s.path.startsWith('technical/'))
  const subjects = c.section_list.filter((s) => s.path.startsWith('subject/'))
  const papers = c.paper_list.length
  const paperQuery=searchParams.get('paper_q')||''
  const paperYear=searchParams.get('paper_year')||''
  const tokens=paperQuery.toLowerCase().trim().split(/\s+/).filter(Boolean)
  const mcsSection=c.id==='combined-prelims'?searchParams.get('section'):null
  const filteredPapers=c.paper_list.filter(p=>(!mcsSection||!['gs','aptitude'].includes(mcsSection)||p.section_path===mcsSection)&&(!paperYear||String(p.year)===paperYear)&&tokens.every(token=>`${p.paper_label||''} ${p.title} ${p.exam||''} ${p.subject||''} ${p.paper_number||''} ${p.year||''} ${p.id.split('/').pop()}`.toLowerCase().includes(token)))
  const pageSize=9
  const bookletGroups=c.id==='combined-prelims'?groupMcsBooklets(filteredPapers):[]
  const paperResultCount=c.id==='combined-prelims'?bookletGroups.length:filteredPapers.length
  const paperPages=Math.max(1,Math.ceil(paperResultCount/pageSize))
  const paperPage=Math.min(pageNumber(searchParams.get('paper_page')),paperPages)
  const visiblePapers=filteredPapers.slice((paperPage-1)*pageSize,paperPage*pageSize)
  const visibleBookletGroups=bookletGroups.slice((paperPage-1)*pageSize,paperPage*pageSize)
  function paperFilter(key:string,value:string){setSearchParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);if(key!=='paper_page')next.delete('paper_page');return next},{replace:key!=='paper_page'});if(key==='paper_page')requestAnimationFrame(()=>scrollToResults('past-paper-results'))}
  const combined = c.id === 'combined-prelims'

  return (
    <div className={`${combined ? 'cp-page' : 'udc-ldc-page'} min-h-[70vh]`}>
    <div className={`${combined ? 'cp-content' : 'udc-ldc-content mx-auto max-w-shell'} px-6 pb-24 pt-8`}>
      <Link to="/exams" className="text-[13px] text-secondary">← Exams</Link>

      {/* Tinted header block, markup line 1702. Exams area colour. */}
      <div className={`${combined ? 'cp-hero' : 'udc-hero'} mt-3 flex flex-wrap items-end justify-between gap-4 rounded-xl ${view==='overview'?'p-6':'p-4'}`}>
        <div className="min-w-0">
          <div className={combined ? 'cp-eyebrow' : 'font-mono text-[11px] uppercase tracking-[0.1em] text-white/85'}>
            {c.kind} · Exam collection
          </div>
          <h1 className={`mt-2 font-display ${view==='overview'?'text-[clamp(30px,4.6vw,44px)]':'text-[28px]'} font-medium -tracking-[0.02em]`}>
            {c.title}
          </h1>
          {view==='overview'&&<p className="mt-1 text-[14px] text-white/85">Choose a subject, practise questions or open an original paper.</p>}
          <div className="mt-2 flex min-h-5 flex-wrap gap-x-4 gap-y-1 text-[12px] text-white/90">
            {ready?<><span>{papers} listed papers</span><span>{c.questions.toLocaleString('en-IN')} questions</span><span>{c.scorable.toLocaleString('en-IN')} official-key questions</span></>:<span role="status">Loading paper coverage…</span>}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => void toggleBookmark()} disabled={bookmarkBusy} aria-pressed={bookmarked}
            className={`whitespace-nowrap rounded-pill border px-[17px] py-[9px] text-[14px] font-semibold text-ink disabled:opacity-60 ${bookmarked ? 'border-[#E9C46A] bg-[#FFF6DD] text-[#79570A]' : 'border-ink bg-card hover:bg-canvas'}`}>
            {bookmarked ? '★ Saved' : '☆ Save exam'}
          </button>
          {view!=='practice'&&<Link to={`/exams/${c.id}?view=practice${mcsSection?`&section=${encodeURIComponent(mcsSection)}`:''}#exam-question-browser`} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 py-2 text-[13px] font-semibold text-paper">Start practice →</Link>}
          <Link to={`/exams/${c.id}?view=topics${mcsSection?`&section=${encodeURIComponent(mcsSection)}`:''}#exam-study-heading`} className="exam-hero-light-action inline-flex min-h-11 items-center rounded-pill border border-ink bg-card px-4 py-2 text-[13px] font-semibold">Subjects &amp; topics</Link>
          {view==='overview'&&<Link to={`/exams/${c.id}?view=papers${mcsSection?`&section=${encodeURIComponent(mcsSection)}`:''}#past-paper-results`} className="exam-hero-light-action inline-flex min-h-11 items-center rounded-pill border border-ink bg-card px-4 py-2 text-[13px] font-semibold">Past papers</Link>}
        </div>
      </div>

      {combined&&<section className="mt-4 rounded-xl border border-hairline bg-card p-4" aria-label="MCS preliminary papers">
        <h2 className="font-display text-[23px]">Choose your preliminary paper</h2>
        <p className="mt-1 text-[13px] text-secondary">Study General Studies and Aptitude separately. Historical papers keep their own source, booklet and answer status.</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">{[['gs','Paper I · General Studies','History, polity, geography, economy, environment, science and Mizoram'],['aptitude','Paper II · Aptitude Tests','Comprehension, reasoning, numeracy and data interpretation']].map(([role,title,description])=><Link key={role} to={{search:'?'+new URLSearchParams({view:view==='overview'?'papers':view,section:role})}} aria-current={mcsSection===role?'page':undefined} className={'rounded-lg border p-4 '+(mcsSection===role?'border-exams bg-exams-soft':'border-hairline')}><strong className="text-[15px]">{title}</strong><p className="mt-1 text-[12px] text-secondary">{description}</p></Link>)}</div>
        {mcsSection&&<Link to={{search:'?'+new URLSearchParams({view})}} className="mt-2 inline-flex min-h-11 items-center text-[12px] font-semibold underline">Show both papers</Link>}
        <p className="mt-2 text-[12px] text-secondary">Timed sets use eligible questions and the stated practice rules. Partial booklets and recovered copies are study resources; they are not a complete exam simulation.</p>
      </section>}

      {view==='overview'&&['udc','ldc','assistant'].includes(c.id)&&<section aria-label="Clerical exam study" className="mt-4 rounded-[12px] border border-hairline bg-card p-4">
        <nav aria-label="Choose clerical exam" className="flex flex-wrap gap-2">{[['udc','UDC'],['ldc','LDC'],['assistant','Assistant Grade']].map(([exam,label])=><Link key={exam} to={`/exams/${exam}`} aria-current={c.id===exam?'page':undefined} className={'inline-flex min-h-11 items-center rounded-pill border px-4 text-[13px] font-semibold '+(c.id===exam?'border-ink bg-ink text-paper':'border-hairline')}>{label}</Link>)}</nav>
        <p className="mt-3 text-[13px] leading-relaxed text-secondary">Study shared subjects with questions from {c.title} papers. General Knowledge, English and other subjects are grouped for revision; each source paper keeps its printed sections and test rules.</p>
        <div className="mt-3 flex flex-wrap gap-2"><Link to={`/exams/${c.id}?view=topics${mcsSection?`&section=${encodeURIComponent(mcsSection)}`:''}#exam-study-heading`} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">All subjects &amp; topics →</Link><Link to={`/exams/${c.id}?view=browse&subject_id=gk-gs#exam-question-browser`} className="inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 text-[13px] font-semibold">General Knowledge →</Link><Link to={`/exams/${c.id}?view=browse&subject_id=english#exam-question-browser`} className="inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 text-[13px] font-semibold">English →</Link></div>
      </section>}

      {c.section_list.find((s) => s.note)?.note && <div className="mt-4 rounded-[10px] border border-[#E9D8B4] bg-[#FBF4E6] p-4 text-[13px] leading-relaxed text-[#5B3D08]">{c.section_list.find((s) => s.note)?.note}</div>}

      {ready&&(view==='overview'||view==='papers')&&<details aria-label="Answer readiness" className="mt-4 rounded-[12px] border border-hairline bg-card p-4">
        <summary className="cursor-pointer text-[14px] font-semibold">Answer sources &amp; test options</summary>
        <ul aria-label="Answer source legend" className="mt-3 flex flex-wrap gap-3">{['official','verified','needs-review'].map(status=>{const style=answerStatusAppearance(status);return <li key={status} className="flex flex-col items-start gap-1 text-[12px]"><span className={'inline-flex items-center gap-2 rounded-pill border px-3 py-1 font-semibold '+style.badge}><span aria-hidden="true">{style.symbol}</span>{style.shortLabel}</span><span className="text-secondary">{style.meaning}</span></li>})}</ul>
        <p className="mt-2 text-[13px] leading-relaxed text-secondary">{c.needs_review.toLocaleString('en-IN')} MCQs need answer review · {c.unsolved.toLocaleString('en-IN')} have no answer. Browse keeps the available questions visible, including written questions. {c.answerable_count.toLocaleString('en-IN')} questions have usable stored answers for study practice, shown with their review labels; only eligible reviewed answers enter a practice-estimate mock.</p>
        {!c.practice_count&&<p className="mt-2 text-[13px] text-secondary">No reviewed mock set is ready for this exam yet. You can study the papers and help verify answers below each question.</p>}
        <p className="mt-2 text-[12px] text-secondary">Past-paper current affairs belong to their exam date. Date hints help you compare time-sensitive facts with official updates without changing historical answers.</p>
        <div className="mt-3 flex flex-wrap gap-3">{c.scorable>=20&&<Link to={`/exams/${c.id}/mock${mcsSection?`?section=${encodeURIComponent(mcsSection)}`:''}`} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Official-key mock</Link>}{c.practice_count>=20&&<Link to={`/exams/${c.id}/mock?mode=derived${mcsSection?`&section=${encodeURIComponent(mcsSection)}`:''}`} className="inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 text-[13px] font-semibold">Reviewed practice estimate</Link>}</div>
      </details>}

      {view==='overview'&&c.id.startsWith('group-b-')&&<section className="mt-5 rounded-[14px] border border-hairline bg-exams-soft p-5"><h2 className="font-display text-[25px]">Study common subjects first</h2><p className="mt-2 text-[13px] text-secondary">English and GK/GS have a focused study area. Technical papers are available separately.</p><div className="mt-3 flex flex-wrap gap-3"><Link to={`/group-b?collection=${c.id}`} className="inline-flex min-h-11 items-center rounded-pill bg-ink px-4 text-[13px] font-semibold text-paper">English &amp; GK/GS →</Link><Link to={`/group-b?study_area=technical&collection=${c.id}`} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-[13px] font-semibold">Technical papers →</Link></div></section>}

      {bookmarkError&&<p role="alert" className="mt-3 text-[13px] text-mypick">Could not save this exam: {bookmarkError}</p>}
      {view==='overview'&&<Suspense fallback={<p className="mt-4 text-[13px] text-muted">Loading saved journey…</p>}><ExamJourney key={c.id} id={c.id}/></Suspense>}
      <nav aria-label={`${c.title} module views`} className={`${combined ? 'cp-tabs' : 'udc-tabs'} mt-6 flex gap-1 overflow-x-auto`}>
        {([['overview','Overview'],['topics','Subjects & topics'],['papers',c.id.startsWith('group-b-')?'Group B papers':combined?'Papers':'Past papers'],['browse','Browse'],['practice','Practice'],['progress','My progress']] as const).map(([key,label]) =>
          <Link key={key} to={{search:(()=>{const next=new URLSearchParams(searchParams);next.set('view',key);return '?'+next.toString()})(),hash:key==='topics'?'#exam-study-heading':key==='papers'?'#past-paper-results':key==='browse'||key==='practice'?'#exam-question-browser':''}} aria-current={view===key?'page':undefined}
            className={`${combined ? (view===key ? 'is-active' : '') : `udc-tab ${view===key ? 'is-active' : ''}`} inline-flex min-h-11 items-center whitespace-nowrap px-4 py-3 text-[13px] font-semibold`}>{label}</Link>)
        }
        {c.scorable >= 20 && <Link to={`/exams/${c.id}/mock${mcsSection?`?section=${encodeURIComponent(mcsSection)}`:''}`} className={`${combined?'':'udc-tab'} whitespace-nowrap rounded-[9px] border border-hairline bg-card px-4 py-3 text-[13px] font-semibold`}>{combined?'Quick practice':'Exam'}</Link>}
      </nav>

      {error&&<p role="alert" className="mt-3 rounded-[10px] border border-hairline bg-card p-3 text-[13px]">Paper details could not load. Available questions can still be studied. <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 underline">Retry details</button></p>}
      {view==='topics'&&<Suspense fallback={<p className="mt-5 text-[13px] text-muted">Loading subjects and topics…</p>}><ExamStudyTopics examId={c.id}/></Suspense>}
      {(view === 'browse' || view === 'practice') && <ModuleQuestionBrowser key={`${c.id}:${view}`} metadataLoading={!ready} collectionTitle={c.title} collectionId={c.id} papers={c.paper_list} sections={c.section_list} initialSectionPath={searchParams.get('section') || ''} initialPool={view==='practice'?'practice':'all'} />}
      {ready&&view === 'progress' && <ModuleProgressPanel collectionId={c.id} collectionTitle={c.title} totalScorable={c.scorable} totalQuestions={c.questions} />}

      {ready&&view === 'overview' && <><div className="mt-6 flex flex-wrap items-start gap-7">
        {/* "Question coverage" — share of scorable questions per section. The
            prototype charts topics; ours are sections until classification
            gives us topics to chart. */}
        {combined && <div className="cp-stats mt-6">
          <div><strong>{c.paper_list.length}</strong><span>available papers</span></div>
          <div><strong>{c.questions.toLocaleString('en-IN')}</strong><span>questions extracted</span></div>
          <div><strong>{c.scorable.toLocaleString('en-IN')}</strong><span>ready for scored practice</span></div>
          <div><strong>{answeredCount?.toLocaleString('en-IN') ?? '—'}</strong><span>your answers</span></div>
        </div>}
        {!combined && <section className="min-w-0 flex-[2_1_480px]">
          <div className="flex flex-wrap items-baseline justify-between gap-2.5 border-b border-hairline pb-2.5">
            <h2 className="font-display text-[26px] font-medium">Question coverage</h2>
            <span className="text-[13px] text-secondary">Available questions by section</span>
          </div>
          {c.section_list.map((s) => (
            <div
              key={s.path}
              className="grid items-center gap-3.5 border-b border-hairline2 py-2.5 [grid-template-columns:minmax(120px,200px)_minmax(0,1fr)_48px]"
            >
              <span className="text-[14px]">{s.title}</span>
              <div className="h-2 rounded-[4px] bg-[#E8DFCC]">
                <div
                  className="h-2 rounded-[4px] bg-exams"
                  style={{ width: `${c.questions ? Math.round((s.questions / c.questions) * 100) : 0}%` }}
                  role="progressbar"
                  aria-label={`${s.title}: ${s.questions.toLocaleString('en-IN')} available questions`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={c.questions ? Math.round((s.questions / c.questions) * 100) : 0}
                />
              </div>
              <span className="text-right font-mono text-[12px]">{s.questions}</span>
            </div>
          ))}
        </section>}


      </div>

      </>}

      {ready&&(view === 'overview' || view === 'papers') && !!c.paper_list.length && <section className="mt-10">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-hairline pb-2.5">
          <div>
            <h2 className="font-display text-[26px] font-medium">Past papers</h2>
            <p className="mt-1 text-[13px] text-secondary">{combined?'Choose a year and paper, then your booklet series. Each series keeps its own printed question order, PDF and answer key.':'Choose a paper to read or practise. Counts reflect the questions currently available; check the source PDF for the complete paper.'}</p>
          </div>
          <span className="label">{filteredPapers.length} papers</span>
        </div>
        <div className="mt-4 flex flex-wrap gap-3 rounded-[10px] border border-hairline bg-card p-3">
          <label className="min-w-[180px] flex-1 text-[12px] font-semibold">Find a paper<input type="search" value={paperQuery} onChange={e=>paperFilter('paper_q',e.target.value)} placeholder="Department, paper, year or keyword" className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas px-3 text-[14px]"/></label>
          <label className="text-[12px] font-semibold">Year<select value={paperYear} onChange={e=>paperFilter('paper_year',e.target.value)} className="mt-1 block min-h-11 rounded-[8px] border border-hairline bg-canvas px-3 text-[14px]"><option value="">All years</option>{[...new Set(c.paper_list.map(p=>p.year).filter((year):year is number=>year!==null))].sort((a,b)=>b-a).map(year=><option key={year} value={year}>{year}</option>)}</select></label>
          {(paperQuery||paperYear)&&<button type="button" onClick={()=>setSearchParams(previous=>{const next=new URLSearchParams(previous);for(const key of ['paper_q','paper_year','paper_page'])next.delete(key);return next},{replace:true})} className="self-end rounded-pill border border-hairline px-4 py-3 text-[13px]">Clear filters</button>}
        </div>
        <p id="past-paper-results" tabIndex={-1} role="status" className="mt-3 scroll-mt-28 text-[12px] text-secondary focus:outline-none">{filteredPapers.length} matching {combined?'booklets':'papers'}{combined?` in ${bookletGroups.length} paper groups`:''} · page {paperPage} of {paperPages}</p>
        <div className="exam-paper-grid mt-3">
          {combined?visibleBookletGroups.map(group=><McsBookletGroup key={group.id} group={group}/>):visiblePapers.map(p => <ExamPaperCard key={p.id} paper={p} examId={c.id} />)}
        </div>
        {!filteredPapers.length&&<p className="py-8 text-center text-secondary">No papers match. Try a department name or clear the year.</p>}
        <Pagination page={paperPage} pages={paperPages} onPageChange={value=>paperFilter('paper_page',String(value))} label="Past paper pages"/>
      </section>}

      {ready&&view === 'overview' && <MaterialDiscovery collectionId={c.id} title="Read for this exam"/>}
      {ready&&view === 'overview' && <>
        <Group title="General papers" items={general} examId={c.id} />
        <Group title="By trade" items={technical} examId={c.id} />
        <Group title="By subject" items={subjects} examId={c.id} />
      </>}
    </div>
    </div>
  )
}

function Group({
  title,
  items,
  examId,
}: {
  title: string
  items: { path: string; title: string; papers: number; scorable: number; questions: number }[]
  examId: string
}) {
  if (!items.length) return null
  return (
    <section className="mt-9">
      <h2 className="font-display text-[26px] font-medium">{title}</h2>
      <div className="mt-3 grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(260px,1fr))]">
        {items.map((s) => (
          <article key={s.path} className="flex flex-col gap-2 rounded-[14px] border border-hairline bg-card p-5 shadow-[0_1px_2px_rgba(29,27,24,.05)] transition-shadow hover:shadow-[0_8px_24px_rgba(29,27,24,.12)]">
            <span className="flex items-center gap-2 text-[12.5px] font-semibold">
              <span className="h-2 w-2 rounded-full bg-exams" />
              {s.papers} paper{s.papers === 1 ? '' : 's'}
            </span>
            <div className="font-display text-[21px] font-medium leading-tight">{s.title}</div>
            <div className="flex-1 text-[14px] leading-[1.55] text-[#2E2A24]">
              {s.questions.toLocaleString('en-IN')} questions · {s.scorable.toLocaleString('en-IN')} verified keys
            </div>
            <div className="mt-2 flex gap-2">
              <Link to={`/exams/${examId}?view=browse&section=${encodeURIComponent(s.path)}`} className="inline-flex min-h-11 items-center rounded-pill border border-ink px-3 py-2 text-[12px] font-semibold">Browse section</Link>
              {s.scorable >= 20 && <Link to={`/exams/${examId}/mock?section=${encodeURIComponent(s.path)}`} className="rounded-pill bg-ink px-3 py-2 text-[12px] font-semibold text-paper">Practice test</Link>}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
