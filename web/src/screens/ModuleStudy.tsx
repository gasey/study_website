import {useBrowsePosition} from '../hooks/useBrowsePosition'
import {collectionBooklets} from '../lib/examOverview'
import {sortArchivePapers} from '../lib/paperArchive'
import {representativeBooklet} from '../lib/sourceBooklets'
import {paperIdentity} from '../lib/paperIdentity'
import {readStudyStatus,readQuestionOrder,newQuestionSeed,nextBrowseOffset} from '../lib/questionBrowse'
import {learningSubjectTitle} from '../lib/groupBStudy'
import StudyQuestionCard from '../components/StudyQuestionCard'
import {questionQueryString} from '../lib/requestCache'
import {savePracticePosition} from '../lib/learning'
import Pagination from '../components/Pagination'
import {scrollToResults} from '../lib/pagination'
import {AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams,Link } from 'react-router-dom'
import {reviewRequest} from '../lib/review'
import { getAccountSession,getMistakes, getProgress, getQuestionFacets, listQuestions, prefetchQuestionPage, submitAnswer, type GroupBStudyArea, type AnswerResult, type CollectionPaper, type CollectionSection, type Mistake, type Progress, type Question, type QuestionFacets } from '../lib/api'


export function ModuleQuestionBrowser({ collectionId, papers, sections, initialSectionPath = '', initialPool = 'all', studyArea, sourceCollections, metadataLoading=false, collectionTitle }: { metadataLoading?:boolean;collectionTitle?:string;studyArea?: GroupBStudyArea; sourceCollections?:Record<string,string>; collectionId: string; papers: CollectionPaper[]; sections: CollectionSection[]; initialSectionPath?: string; initialPool?: 'all'|'scorable'|'practice' }) {
  const [urlParams,setURLParams]=useSearchParams()
  const combined = collectionId === 'combined-prelims'
  const practice=urlParams.get('view')==='practice',PAGE_SIZE=practice?1:25
  const [reload,setReload]=useState(0),[loading,setLoading]=useState(true)
  const search=urlParams.get('q')||'',paperId=urlParams.get('paper')||'',sectionPath=urlParams.get('section')||initialSectionPath
  const subjectId=urlParams.get('subject_id')||'',topicId=urlParams.get('topic_id')||'',subtopicId=urlParams.get('subtopic_id')||''
  const yearParam=urlParams.get('year')||''
  const selectedYear=/^\d{4}$/.test(yearParam)?Number(yearParam):undefined
  const pool:'all'|'scorable'|'practice'=['all','scorable','practice'].includes(urlParams.get('pool')||'')?urlParams.get('pool') as 'all'|'scorable'|'practice':initialPool
  const studyStatus=readStudyStatus(urlParams.get('status')),order=paperId&&!practice?'paper':readQuestionOrder(urlParams.get('order')),seed=urlParams.get('seed')||''
  function shuffle(){setURLParams(previous=>{const next=new URLSearchParams(previous);next.set('order','mixed');next.set('seed',newQuestionSeed());next.delete('offset');return next},{replace:true});setResults({});setPicks({})}
  const answerStatus=(['official','verified','needs-review','unsolved','written'].includes(urlParams.get('answer_status')||'')?urlParams.get('answer_status'):undefined) as 'official'|'verified'|'needs-review'|'unsolved'|'written'|undefined
  const offset=Math.floor(Math.max(0,Math.min(100000,Number(urlParams.get('offset'))||0)))
  function filter(key:string,value:string){setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);if(key!=='offset')next.delete('offset');return next},{replace:key!=='offset'})}
  const setSearch=(v:string)=>filter('q',v),setOffset=(v:number)=>filter('offset',String(v))
  const [facets,setFacets]=useState<QuestionFacets|null>(null)
  useEffect(()=>{let live=true;getQuestionFacets({collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,study_area:studyArea,pool}).then(value=>{if(live)setFacets(value)}).catch(()=>{});return()=>{live=false}},[collectionId,sectionPath,paperId,subjectId,studyArea,pool])
  const selectedSubject=facets?.subjects.find(subject=>subject.id===subjectId)
  const selectedTopic=selectedSubject?.topics.find(topic=>topic.id===topicId)
  function taxonomyFilter(key:'subject_id'|'topic_id'|'subtopic_id',value:string){
    setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);if(key==='subject_id'){next.delete('topic_id');next.delete('subtopic_id')}if(key==='topic_id')next.delete('subtopic_id');next.delete('offset');return next},{replace:true})
    setResults({});setPicks({})
  }
  const requestKey=questionQueryString({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,year_from:selectedYear,year_to:selectedYear,q:search.trim()||undefined,answer_status:answerStatus,pool,order,seed,study_status:studyStatus,limit:PAGE_SIZE,offset})
  const [resolvedKey,setResolvedKey]=useState('')
  const pending=loading||resolvedKey!==requestKey||(order==='mixed'&&!seed)
  function resetFilters(){
    setURLParams(previous=>{const next=new URLSearchParams(previous);for(const key of ['subject_id','topic_id','subtopic_id','section','paper','year','pool','status','answer_status','q','offset','order','seed'])next.delete(key);return next},{replace:true})
    setResults({});setPicks({})
  }
  const [page, setPage] = useState<{items: Question[];total: number}|null>(null)
  const [browseMode, setBrowseMode] = useState<'pages' | 'scroll'>(() => {
    try {
      return localStorage.getItem('finna:browse-mode:v1') === 'scroll' ? 'scroll' : 'pages'
    } catch {
      return 'pages'
    }
  })
  const isScrollMode = !practice && browseMode === 'scroll'
  const MAX_STREAM_ITEMS = 125
  const [stream, setStream] = useState<{ key: string; start: number; items: Question[]; total: number }>({
    key: '',
    start: 0,
    items: [],
    total: 0,
  })
  const [loadingMore, setLoadingMore] = useState(false)
  const [loadingPrev, setLoadingPrev] = useState(false)
  const [returnAnchor, setReturnAnchor] = useState<{ offset: number; index: number } | null>(null)
  const [jumpInput, setJumpInput] = useState('')
  const streamSentinelRef = useRef<HTMLDivElement | null>(null)
  const streamBusyRef = useRef(false)
  const [picks, setPicks] = useState<Record<string,number>>({})
  const [checkingAnswers,setCheckingAnswers]=useState<Record<string,boolean>>({})
  const [viewed,setViewed]=useState<Record<string,boolean>>({})
  const [answerBusy,setAnswerBusy]=useState<Record<string,boolean>>({})
  const checking=useRef(new Set<string>())
  const [results, setResults] = useState<Record<string,AnswerResult>>({})
  const [error, setError] = useState<string|null>(null)
  const [account,setAccount]=useState(false);const [checkpointError,setCheckpointError]=useState('');const saveQueue=useRef(Promise.resolve())
  useEffect(()=>{let live=true;const refresh=()=>{getAccountSession().then(s=>{if(live)setAccount(s.authenticated)}).catch(()=>{});setPage(null);setResults({});setPicks({});setViewed({});setReload(n=>n+1)};refresh();window.addEventListener('ism-auth-change',refresh);return()=>{live=false;window.removeEventListener('ism-auth-change',refresh)}},[])
  useEffect(()=>{if(!account||!page||pending)return;const timer=window.setTimeout(()=>{saveQueue.current=saveQueue.current.then(async()=>{try{if(studyArea){if(page.items[0])await savePracticePosition(page.items[0].id)}else await reviewRequest('/me/exam-checkpoint/'+collectionId,{section:sectionPath,paper:paperId,q:search,pool,order:order==='paper'?'repeated':order,seed,status:studyStatus,subject_id:subjectId,topic_id:topicId,subtopic_id:subtopicId,offset});setCheckpointError('');window.dispatchEvent(new Event('ism-study-checkpoint'))}catch(e){setCheckpointError((e as Error).message)}})},700);return()=>window.clearTimeout(timer)},[account,page,pending,studyArea,collectionId,sectionPath,paperId,search,pool,order,seed,studyStatus,subjectId,topicId,subtopicId,offset])

  const renderedItems = useMemo(
    () => (isScrollMode && stream.key === requestKey ? stream.items : page?.items || []),
    [isScrollMode, stream.key, stream.items, requestKey, page?.items],
  )
  const renderedStart = isScrollMode && stream.key === requestKey ? stream.start : offset
  const renderedIds = useMemo(() => renderedItems.map(q => q.id), [renderedItems])

  const reading=useBrowsePosition(collectionId,!practice,pending,renderedIds,renderedStart)
  useEffect(()=>{if(!reading.initializing&&order==='mixed'&&!seed)setURLParams(previous=>{const next=new URLSearchParams(previous);next.set('seed',newQuestionSeed());return next},{replace:true})},[reading.initializing,order,seed,setURLParams])

  function changeBrowseMode(next: 'pages' | 'scroll') {
    setBrowseMode(next)
    try { localStorage.setItem('finna:browse-mode:v1', next) } catch { /* ignore */ }
    if (next === 'scroll' && page && resolvedKey === requestKey) {
      setStream({ key: requestKey, start: offset, items: page.items, total: page.total })
    }
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    if(reading.initializing||order==='mixed'&&!seed)return
    let prefetchTimer:number|undefined
    const timer = window.setTimeout(() => {
      if(search.trim().length===1){setPage({items:[],total:0});setStream({key:requestKey,start:0,items:[],total:0});setResolvedKey(requestKey);setError('Enter at least two characters to search.');setLoading(false);return}
      setError(null)
      listQuestions({study_area:studyArea,collection_id: collectionId,section_path: sectionPath || undefined,paper_id: paperId || undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,year_from:selectedYear,year_to:selectedYear,q: search.trim() || undefined,answer_status:answerStatus,pool,order,seed,study_status: studyStatus,limit: PAGE_SIZE,offset})
        .then((value) => { if (!cancelled) {
          const last=Math.max(0,value.total-1)
          if(offset>last){setURLParams(previous=>{const next=new URLSearchParams(previous);if(last)next.set('offset',String(Math.floor(last/PAGE_SIZE)*PAGE_SIZE));else next.delete('offset');return next},{replace:true});return}
          setPage(value);setStream({key:requestKey,start:offset,items:value.items,total:value.total});setResolvedKey(requestKey);setError(null)
          if(offset+PAGE_SIZE<value.total)prefetchTimer=window.setTimeout(()=>prefetchQuestionPage({study_area:studyArea,collection_id:collectionId,section_path:sectionPath||undefined,paper_id:paperId||undefined,subject_id:subjectId||undefined,topic_id:topicId||undefined,subtopic_id:subtopicId||undefined,year_from:selectedYear,year_to:selectedYear,q:search.trim()||undefined,answer_status:answerStatus,pool,order,seed,study_status:studyStatus,limit:PAGE_SIZE,offset:offset+PAGE_SIZE}),250)
        } })
        .catch((e) => { if (!cancelled) setError(e.message) })
        .finally(()=>{if(!cancelled)setLoading(false)})
    }, search.trim() ? 250 : 0)
    return () => { cancelled = true; window.clearTimeout(timer);if(prefetchTimer!==undefined)window.clearTimeout(prefetchTimer) }
  }, [studyArea,collectionId,sectionPath,paperId,subjectId,topicId,subtopicId,selectedYear,search,pool,order,seed,studyStatus,answerStatus,offset,PAGE_SIZE,reload,reading.initializing])

  const hasMoreStream = isScrollMode && stream.key === requestKey && stream.start + stream.items.length < stream.total
  const hasPrevStream = isScrollMode && stream.key === requestKey && stream.start > 0

  async function loadNextChunk() {
    if (!isScrollMode || pending || streamBusyRef.current || !hasMoreStream) return
    const nextOffset = stream.start + stream.items.length
    const activeKey = requestKey
    streamBusyRef.current = true
    setLoadingMore(true)
    try {
      const value = await listQuestions({
        study_area: studyArea,
        collection_id: collectionId,
        section_path: sectionPath || undefined,
        paper_id: paperId || undefined,
        subject_id: subjectId || undefined,
        topic_id: topicId || undefined,
        subtopic_id: subtopicId || undefined,
        year_from: selectedYear,
        year_to: selectedYear,
        q: search.trim() || undefined,
        answer_status: answerStatus,
        pool,
        order,
        seed,
        study_status: studyStatus,
        limit: PAGE_SIZE,
        offset: nextOffset,
      })
      setStream(old => {
        if (old.key !== activeKey) return old
        const seen = new Set(old.items.map(q => q.id))
        const fresh = value.items.filter(q => !seen.has(q.id))
        if (!fresh.length) return { ...old, total: value.total }
        let combinedItems = [...old.items, ...fresh]
        let nextStart = old.start
        // Keep DOM memory flat even across thousands of questions using a sliding window.
        if (combinedItems.length > MAX_STREAM_ITEMS) {
          const drop = combinedItems.length - MAX_STREAM_ITEMS
          combinedItems = combinedItems.slice(drop)
          nextStart += drop
        }
        return { key: old.key, start: nextStart, items: combinedItems, total: value.total }
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      streamBusyRef.current = false
      setLoadingMore(false)
    }
  }

  async function loadPrevChunk() {
    if (!isScrollMode || pending || streamBusyRef.current || !hasPrevStream) return
    const prevOffset = Math.max(0, stream.start - PAGE_SIZE)
    const count = stream.start - prevOffset
    if (count <= 0) return
    const activeKey = requestKey
    const prevHeight = document.documentElement.scrollHeight
    streamBusyRef.current = true
    setLoadingPrev(true)
    try {
      const value = await listQuestions({
        study_area: studyArea,
        collection_id: collectionId,
        section_path: sectionPath || undefined,
        paper_id: paperId || undefined,
        subject_id: subjectId || undefined,
        topic_id: topicId || undefined,
        subtopic_id: subtopicId || undefined,
        year_from: selectedYear,
        year_to: selectedYear,
        q: search.trim() || undefined,
        answer_status: answerStatus,
        pool,
        order,
        seed,
        study_status: studyStatus,
        limit: count,
        offset: prevOffset,
      })
      setStream(old => {
        if (old.key !== activeKey) return old
        const seen = new Set(old.items.map(q => q.id))
        const fresh = value.items.filter(q => !seen.has(q.id))
        if (!fresh.length) return old
        const combinedItems = [...fresh, ...old.items].slice(0, MAX_STREAM_ITEMS)
        return { key: old.key, start: prevOffset, items: combinedItems, total: value.total }
      })
      requestAnimationFrame(() => {
        const delta = document.documentElement.scrollHeight - prevHeight
        if (delta > 0) window.scrollBy({ top: delta, behavior: 'auto' })
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      streamBusyRef.current = false
      setLoadingPrev(false)
    }
  }

  useEffect(() => {
    if (!isScrollMode || !hasMoreStream || pending) return
    const el = streamSentinelRef.current
    if (!el || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some(e => e.isIntersecting)) void loadNextChunk()
      },
      { rootMargin: '700px 0px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  })

  const currentPage=Math.floor(offset/PAGE_SIZE)+1,pages=Math.max(currentPage,currentPage+Math.ceil(Math.max(0,(page?.total||0)-offset-PAGE_SIZE)/PAGE_SIZE))
  function goPage(value:number){
    // Answering changes membership of personal queues. Refresh this position so
    // advancing cannot skip the next unseen question after the current one leaves.
    if(value===currentPage+1){
      const next=nextBrowseOffset(offset,PAGE_SIZE,studyStatus,page?.items.map(q=>results[q.id])||[])
      if(next===offset)setReload(n=>n+1);else setOffset(next)
    } else setOffset(Math.max(0,offset+(value-currentPage)*PAGE_SIZE))
    requestAnimationFrame(()=>scrollToResults('exam-question-browser'))
  }

  function jumpToQuestionNumber(targetOneBased: number, rememberCurrent = true) {
    const total = page?.total || 0
    if (total <= 0) return
    const clamped = Math.min(total, Math.max(1, Math.floor(targetOneBased)))
    const targetOffset = Math.floor((clamped - 1) / PAGE_SIZE) * PAGE_SIZE
    const currentIdx = reading.currentIndex || (renderedStart + 1)
    if (rememberCurrent && Math.abs(currentIdx - clamped) >= 2) {
      setReturnAnchor({
        offset: Math.floor(Math.max(0, currentIdx - 1) / PAGE_SIZE) * PAGE_SIZE,
        index: currentIdx,
      })
    }
    // If already rendered on screen, scroll directly to that card!
    const localIdx = clamped - 1 - renderedStart
    if (localIdx >= 0 && localIdx < renderedItems.length) {
      const targetId = renderedItems[localIdx]?.id
      const el = targetId ? document.getElementById('question-' + targetId) : null
      if (el) {
        el.scrollIntoView({
          block: 'start',
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
        })
        return
      }
    }
    setResults({})
    setPicks({})
    setOffset(targetOffset)
    requestAnimationFrame(() => scrollToResults('exam-question-browser'))
  }

  function jumpToStart() {
    const currentIdx = reading.currentIndex || (renderedStart + 1)
    if (currentIdx > 1) {
      setReturnAnchor({
        offset: Math.floor(Math.max(0, currentIdx - 1) / PAGE_SIZE) * PAGE_SIZE,
        index: currentIdx,
      })
    }
    setResults({})
    setPicks({})
    setOffset(0)
    requestAnimationFrame(() => scrollToResults('exam-question-browser'))
  }

  function jumpToLastReturn() {
    if (!returnAnchor) return
    const target = returnAnchor
    setReturnAnchor(null)
    jumpToQuestionNumber(target.index, false)
  }

  function hideAllChecked() {
    setPicks({})
    setResults({})
  }

  const checkedCount = Object.keys(results).length
  function update<T>(setter: (value:T)=>void, value:T) { setter(value); setResults({}); setPicks({}) }
  // One option tap submits through the guarded attempt path.
  async function answer(q: Question, index: number) {
    if (pending || q.held || results[q.id] || viewed[q.id] || answerBusy[q.id] || checking.current.has(q.id) || q.answer_source === 'none' || q.key_disputed || ['duplicate-options','unresolved-source'].includes(q.source_defect||'')) return
    setPicks(old=>({...old,[q.id]:index}));checking.current.add(q.id);setCheckingAnswers(old=>({...old,[q.id]:true}));setAnswerBusy(old=>({...old,[q.id]:true}))
    try {
      const actualPaper=paperId||((studyArea||['udc','ldc','assistant'].includes(collectionId))?q.source_appearance?.paper_id:undefined)
      const actualCollection=sourceCollections?.[actualPaper||'']||collectionId
      const result = await submitAnswer(q.id,index,'practice',actualCollection==='group-b'?undefined:actualCollection,actualPaper,sectionPath || undefined)
      setResults((old) => ({...old,[q.id]:result}))
    } catch (e) {
      setPicks((old) => { const next={...old}; delete next[q.id]; return next })
      setError((e as Error).message)
    } finally {checking.current.delete(q.id);setCheckingAnswers(old=>({...old,[q.id]:false}));setAnswerBusy(old=>({...old,[q.id]:false}))}
  }

  const selectedPaper=papers.find(p=>p.id===paperId)
  const paperGroups=useMemo(()=>collectionBooklets(collectionId,sortArchivePapers(papers,'newest')),[collectionId,papers])
  const paperPosition=paperGroups.findIndex(group=>group.papers.some(p=>p.id===paperId))
  function chooseSection(value:string){setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set('section',value);else next.delete('section');next.delete('paper');next.delete('offset');next.delete('fresh');return next},{replace:true})}
  function chooseStatus(value:string){setURLParams(previous=>{const next=new URLSearchParams(previous);next.delete('status');next.delete('answer_status');next.delete('offset');if(value.startsWith('study:'))next.set('status',value.slice(6));if(value.startsWith('answer:')){next.set('answer_status',value.slice(7));next.set('pool','all')}return next},{replace:true});setResults({});setPicks({})}
  function choosePaper(value:string){setURLParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set('paper',value);else next.delete('paper');if(combined&&value){const source=papers.find(p=>p.id===value);if(source?.section_path)next.set('section',source.section_path);else next.delete('section')}next.delete('offset');next.delete('seed');next.delete('fresh');return next},{replace:false});setResults({});setPicks({})}
  const questionFormat: 'all' | 'mcq' | 'written' =
    answerStatus === 'written' ? 'written' : pool === 'practice' ? 'mcq' : 'all'
  function chooseQuestionFormat(nextFormat: 'all' | 'mcq' | 'written') {
    setURLParams(previous => {
      const next = new URLSearchParams(previous)
      next.delete('offset')
      if (nextFormat === 'written') {
        next.set('pool', 'all')
        next.set('answer_status', 'written')
      } else if (nextFormat === 'mcq') {
        next.set('pool', 'practice')
        if (next.get('answer_status') === 'written') next.delete('answer_status')
      } else {
        next.set('pool', 'all')
        if (next.get('answer_status') === 'written') next.delete('answer_status')
      }
      return next
    }, { replace: true })
    setResults({})
    setPicks({})
  }

  const testViewHref = useMemo(() => {
    const p = new URLSearchParams()
    if (collectionId) p.set('exam', collectionId)
    if (subjectId) p.set('subject', subjectId)
    if (selectedYear) p.set('year', String(selectedYear))
    if (studyStatus !== 'all') p.set('status', studyStatus)
    if (search.trim().length >= 2) p.set('q', search.trim())
    p.set('autostart', '1')
    return '/practice?' + p.toString()
  }, [collectionId, subjectId, selectedYear, studyStatus, search])

  const hasMultipleSections = !studyArea && sections.length > 1
  const hasPapers = paperGroups.length > 0
  const hasMultipleSubjects = (facets?.subjects.length ?? 0) > 1
  const singleSubject = facets?.subjects.length === 1 ? facets.subjects[0] : null
  const activeTopicSource = selectedSubject || singleSubject
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)

  const activeChips: { key: string; label: string; clear: () => void }[] = []
  if (subjectId) {
    activeChips.push({
      key: 'subject',
      label: selectedSubject ? learningSubjectTitle(selectedSubject.id, selectedSubject.title, collectionId) : subjectId,
      clear: () => taxonomyFilter('subject_id', ''),
    })
  }
  if (topicId) {
    activeChips.push({
      key: 'topic',
      label: selectedTopic?.title || topicId,
      clear: () => taxonomyFilter('topic_id', ''),
    })
  }
  if (subtopicId) {
    const subTitle = selectedTopic?.subtopics.find(b => b.id === subtopicId)?.title || subtopicId
    activeChips.push({
      key: 'subtopic',
      label: subTitle,
      clear: () => taxonomyFilter('subtopic_id', ''),
    })
  }
  if (selectedYear) {
    activeChips.push({
      key: 'year',
      label: String(selectedYear),
      clear: () => filter('year', ''),
    })
  }
  if (sectionPath) {
    const secLabel = combined
      ? sectionPath === 'gs' ? 'Paper I' : sectionPath === 'aptitude' ? 'Paper II' : sectionPath
      : sections.find(s => s.path === sectionPath)?.title || sectionPath
    activeChips.push({
      key: 'section',
      label: secLabel,
      clear: () => chooseSection(''),
    })
  }
  if (paperId) {
    activeChips.push({
      key: 'paper',
      label: selectedPaper ? paperIdentity(selectedPaper).title : 'Selected paper',
      clear: () => choosePaper(''),
    })
  }
  if (studyStatus !== 'all') {
    const statusMap: Record<string, string> = { ever_wrong: 'Previously wrong', unseen: 'Never attempted', answered: 'Attempted', wrong: 'Previously wrong' }
    activeChips.push({
      key: 'status',
      label: statusMap[studyStatus] || studyStatus,
      clear: () => chooseStatus(''),
    })
  }
  if (search.trim()) {
    activeChips.push({
      key: 'q',
      label: `“${search.trim()}”`,
      clear: () => update(setSearch, ''),
    })
  }
  if (!practice && questionFormat !== 'all') {
    activeChips.push({
      key: 'format',
      label: questionFormat === 'written' ? '✎ Written only' : '◉ MCQs only',
      clear: () => chooseQuestionFormat('all'),
    })
  }
  const activeFilterCount = activeChips.length

  const rangeText = !pending && page
    ? page.total > 0
      ? `${(renderedStart + 1).toLocaleString('en-IN')}–${Math.min(renderedStart + renderedItems.length, page.total).toLocaleString('en-IN')} of ${page.total.toLocaleString('en-IN')}`
      : '0 questions'
    : page ? 'Updating…' : 'Loading…'

  return <section id="exam-question-browser" tabIndex={-1} aria-busy={pending} className="mb-shell scroll-mt-28 focus:outline-none">
    <div className="mb-layout">
      {/* Main reading column: slim top strip + Checkpoint Dock + Question #1 immediately above the fold */}
      <div className="mb-main">
        <div className="mb-reading-bar">
          <div className="mb-reading-left">
            <span className="mb-count-pill" role="status">{rangeText}</span>
            {activeChips.length > 0 ? (
              <div className="mb-chip-list" aria-label="Active filters">
                {activeChips.map(chip => (
                  <button key={chip.key} type="button" className="mb-active-chip" onClick={chip.clear} title={`Remove ${chip.label} filter`}>
                    <span>{chip.label}</span>
                    <span aria-hidden="true" className="mb-chip-x">×</span>
                  </button>
                ))}
              </div>
            ) : (
              <span className="mb-scope-hint">{practice ? 'Study practice' : (collectionTitle || 'All questions')}</span>
            )}
          </div>
          <div className="mb-reading-right">
            {!practice && (
              <div className="mb-format-seg" role="group" aria-label="Question format">
                <button
                  type="button"
                  aria-pressed={questionFormat === 'all'}
                  className={questionFormat === 'all' ? 'is-on' : ''}
                  onClick={() => chooseQuestionFormat('all')}
                >
                  All
                </button>
                <button
                  type="button"
                  aria-pressed={questionFormat === 'mcq'}
                  className={questionFormat === 'mcq' ? 'is-on is-mcq' : ''}
                  onClick={() => chooseQuestionFormat('mcq')}
                  title="Show multiple-choice questions only"
                >
                  ◉ MCQs
                </button>
                <button
                  type="button"
                  aria-pressed={questionFormat === 'written'}
                  className={questionFormat === 'written' ? 'is-on is-written' : ''}
                  onClick={() => chooseQuestionFormat('written')}
                  title="Show written / descriptive prompts only"
                >
                  ✎ Written
                </button>
              </div>
            )}
            {!practice && page && page.total > PAGE_SIZE && (
              <div className="mb-mode-seg" role="group" aria-label="Reading mode">
                <button
                  type="button"
                  aria-pressed={!isScrollMode}
                  className={!isScrollMode ? 'is-on' : ''}
                  onClick={() => changeBrowseMode('pages')}
                  title="25 questions per page"
                >
                  Pages
                </button>
                <button
                  type="button"
                  aria-pressed={isScrollMode}
                  className={isScrollMode ? 'is-on' : ''}
                  onClick={() => changeBrowseMode('scroll')}
                  title="Optimized continuous scroll stream"
                >
                  Scroll
                </button>
              </div>
            )}
            <AnswerLayoutControl compact />
            {!isScrollMode && page && pages > 1 && (
              <div className="mb-mini-pager" role="navigation" aria-label="Quick page step">
                <button type="button" disabled={pending || currentPage <= 1} onClick={() => goPage(currentPage - 1)} aria-label="Previous page">‹</button>
                <span>{currentPage}/{pages}</span>
                <button type="button" disabled={pending || currentPage >= pages} onClick={() => goPage(currentPage + 1)} aria-label="Next page">›</button>
              </div>
            )}
            <button
              type="button"
              className={`mb-mobile-filter-btn${mobileFiltersOpen ? ' is-open' : ''}`}
              aria-expanded={mobileFiltersOpen}
              onClick={() => setMobileFiltersOpen(v => !v)}
            >
              Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}
            </button>
          </div>
        </div>

        {/* Reading Checkpoints & Quick-Jump Bar: Auto-resume, Start, Last Spot, Pinned Checkpoint, Jump #, Hide Checked */}
        {!practice && page && page.total > 0 && (
          <nav aria-label="Reading checkpoints and quick jump" className="mb-checkpoint-bar">
            <div className="mb-cp-group">
              <span className="mb-cp-pos" title="Your place is saved automatically; answers reset hidden when you return">
                {reading.resumedIndex && reading.currentIndex === reading.resumedIndex
                  ? `Resumed #${reading.currentIndex.toLocaleString('en-IN')}`
                  : `At #${(reading.currentIndex || renderedStart + 1).toLocaleString('en-IN')}`}
              </span>
              {(reading.currentIndex > 1 || renderedStart > 0) && (
                <button type="button" className="mb-cp-btn" onClick={jumpToStart} title="Jump to question #1 (answers kept)">
                  ⏮ Start
                </button>
              )}
              {returnAnchor && (
                <button type="button" className="mb-cp-btn is-accent" onClick={jumpToLastReturn} title="Return to where you were before jumping">
                  ↩ Last (#{returnAnchor.index.toLocaleString('en-IN')})
                </button>
              )}
              {reading.checkpoint ? (
                <span className="mb-cp-pin-wrap">
                  <button type="button" className="mb-cp-btn is-pin" onClick={reading.jumpToCheckpoint} title="Jump to your pinned checkpoint">
                    ⚑ #{reading.checkpoint.questionIndex.toLocaleString('en-IN')}
                  </button>
                  <button type="button" className="mb-cp-icon-btn" onClick={reading.pinCheckpoint} title="Move checkpoint pin to current question" aria-label="Move checkpoint pin here">
                    ↻
                  </button>
                  <button type="button" className="mb-cp-icon-btn" onClick={reading.clearPinnedCheckpoint} title="Remove checkpoint pin" aria-label="Remove checkpoint pin">
                    ×
                  </button>
                </span>
              ) : (
                <button type="button" className="mb-cp-btn" onClick={reading.pinCheckpoint} title="Drop a reading checkpoint at this question">
                  ⚑ Pin #{(reading.currentIndex || renderedStart + 1).toLocaleString('en-IN')}
                </button>
              )}
              {page.total > PAGE_SIZE && (reading.currentIndex < page.total - PAGE_SIZE + 1) && (
                <button
                  type="button"
                  className="mb-cp-btn"
                  onClick={() => jumpToQuestionNumber(page.total)}
                  title={`Jump to the last question (#${page.total.toLocaleString('en-IN')})`}
                >
                  ⏭ End
                </button>
              )}
            </div>

            <div className="mb-cp-group mb-cp-right">
              {checkedCount > 0 && (
                <button type="button" className="mb-cp-btn is-hide" onClick={hideAllChecked} title="Hide all revealed answers on screen so you can test yourself again">
                  ↺ Hide checked ({checkedCount})
                </button>
              )}
              {page.total > PAGE_SIZE && (
                <form
                  className="mb-cp-jump-form"
                  onSubmit={(e) => {
                    e.preventDefault()
                    const n = Number(jumpInput)
                    if (Number.isFinite(n) && n >= 1) {
                      jumpToQuestionNumber(n)
                      setJumpInput('')
                    }
                  }}
                >
                  <input
                    type="number"
                    min={1}
                    max={page.total}
                    inputMode="numeric"
                    value={jumpInput}
                    onChange={(e) => setJumpInput(e.target.value)}
                    placeholder="# Go…"
                    aria-label="Jump to question number"
                  />
                  <button type="submit" disabled={!jumpInput.trim()}>Go</button>
                </form>
              )}
            </div>
          </nav>
        )}

        {paperId && <nav aria-label="Paper navigation" className="browse-paper-navigation mb-3">
          <button type="button" disabled={paperPosition <= 0} onClick={() => choosePaper(representativeBooklet(paperGroups[paperPosition - 1]).id)} className="min-h-10 text-link disabled:opacity-40">← Prev paper</button>
          <span className="min-w-0 flex-1 truncate text-center font-semibold text-ink" title={selectedPaper ? paperIdentity(selectedPaper).title : 'Selected paper'}>{selectedPaper ? paperIdentity(selectedPaper).title : 'Selected paper'}</span>
          <button type="button" disabled={paperPosition < 0 || paperPosition >= paperGroups.length - 1} onClick={() => choosePaper(representativeBooklet(paperGroups[paperPosition + 1]).id)} className="min-h-10 text-link disabled:opacity-40">Next paper →</button>
          <Link to={sourceCollections ? '/exams/group-b-gazetted?' + new URLSearchParams({ collection: collectionId, view: 'papers' }) : `/exams/${collectionId}?view=papers`} className="inline-flex min-h-10 items-center text-link">All papers</Link>
          {selectedPaper?.source_pdf_url && <a href={selectedPaper.source_pdf_url} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center text-link underline">PDF ↗</a>}
        </nav>}

        {subjectId === 'gk-gs' && topicId === 'gk-gs:science' && selectedTopic && <nav aria-label="Science branches" className="mb-3 flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-bold uppercase tracking-wider text-secondary">Science:</span>
          {[{ id: '', title: 'All Science' }, ...selectedTopic.subtopics].map(branch => <button key={branch.id} type="button" aria-pressed={subtopicId === branch.id} onClick={() => taxonomyFilter('subtopic_id', branch.id)} className={`min-h-9 rounded-pill border px-3 text-xs font-semibold ${subtopicId === branch.id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card'}`}>{branch.title}</button>)}
        </nav>}

        {error && <p role="alert" className="mb-3 rounded-[12px] border border-mypick bg-mypick-soft p-3 text-sm text-mypick">{error} <button type="button" onClick={() => setReload(n => n + 1)} className="underline">Retry</button></p>}
        {metadataLoading && <p role="status" className="mb-2 text-xs text-muted">Paper details are loading. You can start with the available questions.</p>}
        {checkpointError && <p role="status" className="mb-2 text-xs text-mypick">Could not save your place: {checkpointError}</p>}
        {practice && <p className="mb-2 text-xs text-secondary">Tap an option to submit your answer. Show answer opens reading mode.</p>}

        {hasPrevStream && (
          <div className="mb-stream-top">
            <button
              type="button"
              className="mb-stream-load-btn"
              disabled={loadingPrev}
              onClick={() => void loadPrevChunk()}
            >
              {loadingPrev
                ? 'Loading earlier questions…'
                : `↑ Load earlier ${Math.min(PAGE_SIZE, renderedStart)} (#${Math.max(1, renderedStart - PAGE_SIZE + 1).toLocaleString('en-IN')}–#${renderedStart.toLocaleString('en-IN')})`}
            </button>
          </div>
        )}

        {pending && !page && !error && <p role="status" className="min-h-[320px] py-10 text-center text-secondary">Loading questions…</p>}
        <div className={`exam-reading-area mb-question-list ${pending && page ? 'opacity-50' : ''}`} data-results-current={!pending}>
          {renderedItems.map((q, index) => {
            const result = results[q.id]
            const posNum = renderedStart + index + 1
            return <StudyQuestionCard showPanelNext={false} key={q.id} q={q} positionNumber={posNum} collectionId={collectionId} paperId={paperId} sourceCollections={sourceCollections}
              result={result} pick={picks[q.id]} viewed={viewed[q.id]} busy={answerBusy[q.id]} checking={checkingAnswers[q.id]} disabled={pending}
              onPick={i => void answer(q, i)}
              onViewed={value => setViewed(old => ({ ...old, [q.id]: value }))} onBusy={v => setAnswerBusy(old => ({ ...old, [q.id]: v }))}
              onRetry={() => { setPicks(old => { const next = { ...old }; delete next[q.id]; return next }); setResults(old => { const next = { ...old }; delete next[q.id]; return next }) }}
              onNext={() => { const next = renderedItems[index + 1]; if (next) document.getElementById('question-' + next.id)?.scrollIntoView({ block: 'start', behavior: 'smooth' }); else if (!isScrollMode && currentPage < pages) goPage(currentPage + 1); else if (isScrollMode && hasMoreStream) void loadNextChunk(); else setError('You reached the end of these results. Change filters to continue.') }} />
          })}
          {!pending && page && !renderedItems.length && <div className="rounded-2xl border border-hairline bg-card py-10 text-center text-sm text-secondary">No questions match these filters. <button type="button" onClick={resetFilters} className="min-h-11 font-semibold underline">Reset filters</button></div>}
        </div>
        {isScrollMode ? (
          <div ref={streamSentinelRef} className="mb-stream-foot">
            {hasMoreStream ? (
              <button
                type="button"
                className="mb-stream-load-btn"
                disabled={loadingMore}
                onClick={() => void loadNextChunk()}
              >
                {loadingMore
                  ? 'Loading next 25 questions…'
                  : `Load more (#${(renderedStart + renderedItems.length + 1).toLocaleString('en-IN')}–#${Math.min(page?.total || 0, renderedStart + renderedItems.length + PAGE_SIZE).toLocaleString('en-IN')})`}
              </button>
            ) : page && page.total > 0 ? (
              <p className="mb-stream-end">
                Reached the end ({page.total.toLocaleString('en-IN')} questions).{' '}
                <button type="button" className="underline font-semibold" onClick={jumpToStart}>Back to #1</button>
              </p>
            ) : null}
          </div>
        ) : (
          page && <Pagination page={currentPage} pages={pages} disabled={pending} onPageChange={goPage} label={practice ? 'Practice question navigator' : 'Exam question pages'} />
        )}
      </div>

      {/* Sticky Study Controls Sidebar: uses right desktop gutter cleanly; drawer on <1040px */}
      <aside className={`mb-rail${mobileFiltersOpen ? ' is-open' : ''}`} aria-label="Question filters and study controls">
        <div className="mb-rail-card">
          <div className="mb-rail-actions">
            {!pending && page && page.total > 0 && (
              <Link to={testViewHref} className="mb-cta-primary">Test this view →</Link>
            )}
            <button
              type="button"
              onClick={() => chooseStatus(studyStatus === 'ever_wrong' ? '' : 'study:ever_wrong')}
              aria-pressed={studyStatus === 'ever_wrong'}
              className={`mb-cta-mistake${studyStatus === 'ever_wrong' ? ' is-on' : ''}`}
            >
              Revise mistakes
            </button>
          </div>

          <div className="mb-rail-head">
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <button type="button" onClick={resetFilters} className="mb-reset-link">Reset ({activeFilterCount})</button>
            )}
          </div>

          <div className="mb-filter-stack" aria-label="Question filters">
            <label className="mb-field">
              <span>Search</span>
              <input maxLength={120} value={search} onChange={e => update(setSearch, e.target.value)} placeholder="Keyword or phrase…" />
            </label>

            {hasMultipleSubjects ? (
              <label className="mb-field">
                <span>Subject</span>
                <select value={subjectId} onChange={e => taxonomyFilter('subject_id', e.target.value)}>
                  <option value="">All subjects</option>
                  {subjectId && !selectedSubject && <option value={subjectId}>Selected subject</option>}
                  {facets?.subjects.map(subject => <option key={subject.id} value={subject.id}>{learningSubjectTitle(subject.id, subject.title, collectionId)} ({subject.questions})</option>)}
                </select>
              </label>
            ) : activeTopicSource && activeTopicSource.topics.length > 0 ? (
              <label className="mb-field">
                <span>Topic</span>
                <select value={topicId} onChange={e => taxonomyFilter('topic_id', e.target.value)}>
                  <option value="">All topics</option>
                  {activeTopicSource.topics.map(topic => <option key={topic.id} value={topic.id}>{topic.title} ({topic.questions})</option>)}
                </select>
              </label>
            ) : null}

            {hasMultipleSubjects && selectedSubject && selectedSubject.topics.length > 0 && (
              <label className="mb-field">
                <span>Topic</span>
                <select value={topicId} onChange={e => taxonomyFilter('topic_id', e.target.value)}>
                  <option value="">All topics</option>
                  {selectedSubject.topics.map(topic => <option key={topic.id} value={topic.id}>{topic.title} ({topic.questions})</option>)}
                </select>
              </label>
            )}

            <div className="mb-field-pair">
              {(facets?.years.length ?? 0) > 0 && (
                <label className="mb-field">
                  <span>Year</span>
                  <select aria-label="Exam year" value={yearParam} onChange={e => filter('year', e.target.value)}>
                    <option value="">All years</option>
                    {facets?.years.map(y => <option key={y.year} value={String(y.year)}>{y.year} ({y.questions})</option>)}
                  </select>
                </label>
              )}
              <label className="mb-field">
                <span>Status</span>
                <select aria-label="Your study status" value={studyStatus !== 'all' ? 'study:' + studyStatus : ''} onChange={e => chooseStatus(e.target.value)}>
                  <option value="">All</option>
                  <option value="study:unseen">Unseen</option>
                  <option value="study:ever_wrong">Wrong</option>
                  <option value="study:answered">Attempted</option>
                </select>
              </label>
            </div>

            {hasMultipleSections && (
              <label className="mb-field">
                <span>{combined ? 'Paper type' : 'Section'}</span>
                <select aria-label={combined ? 'Paper type' : 'Section'} disabled={metadataLoading} value={sectionPath} onChange={e => chooseSection(e.target.value)}>
                  <option value="">{combined ? 'Both papers' : 'All sections'}</option>
                  {sections.map(s => <option key={s.path} value={s.path}>{combined ? (s.path === 'gs' ? 'Paper I only' : s.path === 'aptitude' ? 'Paper II only' : s.title) : s.title}</option>)}
                </select>
              </label>
            )}

            {hasPapers && (
              <label className="mb-field">
                <span>Paper</span>
                <select aria-label="Specific paper" disabled={metadataLoading} value={paperId} onChange={e => choosePaper(e.target.value)}>
                  <option value="">All papers</option>
                  {paperGroups.filter(group => !sectionPath || group.papers.some(p => p.section_path === sectionPath)).map(group => { const p = group.papers.find(p => p.id === paperId) || representativeBooklet(group); return <option key={p.id} value={p.id}>{p.year ? `${p.year} · ` : ''}{group.papers.length > 1 ? group.title : paperIdentity(p).title}</option> })}
                  {paperId && paperPosition < 0 && <option value={paperId}>Selected paper</option>}
                </select>
              </label>
            )}
          </div>

          {!practice && (
            <div className="mb-rail-foot">
              <p role="status" className="mb-save-note">
                {reading.initializing ? 'Restoring reading position…' : reading.message || 'Place saved automatically on this device.'}
              </p>
              <div className="mb-foot-btns">
                {order === 'mixed' && <button type="button" onClick={shuffle} className="mb-foot-btn">↻ Shuffle</button>}
                <button type="button" onClick={reading.startAgain} title="Reset this reading position; your answers and scores are kept." className="mb-foot-btn">Start again</button>
              </div>
              {(combined || collectionId === 'udc') && !paperId && (
                <p className="mb-dedup-note">Identical booklet-series copies are grouped; figures &amp; source differences stay separate.</p>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  </section>
}

export function ModuleProgressPanel({ collectionId, collectionTitle, totalScorable, totalQuestions = totalScorable, practiceAvailable=true, practiceHref, papersHref }: { collectionId: string; collectionTitle: string; totalScorable: number; totalQuestions?: number; practiceAvailable?:boolean; practiceHref?:string; papersHref?:string }) {
  const practiceLink=practiceHref||`/exams/${collectionId}?view=practice`,paperLink=papersHref||`/exams/${collectionId}?view=papers`
  const [progress, setProgress] = useState<Progress | null>(null)
  const [mistakes, setMistakes] = useState<Mistake[]>([])
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    Promise.all([getProgress(collectionId), getMistakes(collectionId)])
      .then(([p, m]) => { if (!cancelled) { setProgress(p); setMistakes(m) } })
      .catch((e) => { if (!cancelled) setError(e.message) })
    return () => { cancelled = true }
  }, [collectionId])

  if (error) return <p role="alert" className="mt-5 rounded-[10px] border border-mypick bg-mypick-soft p-4 text-mypick">Couldn’t load this progress yet. {error}</p>
  if (!progress) return <div className="learning-dashboard" aria-live="polite"><p className="label">Loading your {collectionTitle} progress…</p></div>
  if (!practiceAvailable && progress.answered === 0 && mistakes.length === 0) return <section className="learning-dashboard">
    <header className="learning-header"><div><p className="learning-eyebrow">Your study map · {collectionTitle}</p><h2>Reading & written preparation</h2><p className="learning-intro">This collection currently has source papers to study. Answer-ready MCQ practice is not available yet.</p></div></header>
    <section className="learning-start-panel"><div className="learning-start-icon" aria-hidden="true">↗</div><div className="learning-start-copy"><h3>Build your preparation from an original paper.</h3><p>Keep your written answers in your own notes. Reading and written work are not automatically graded or recorded as answer attempts, accuracy or completion.</p></div><div className="learning-start-actions"><Link to={paperLink} className="learning-primary-button">Choose a paper →</Link></div></section>
  </section>

  const started = progress.answered > 0
  const coverage = totalQuestions > 0 ? Math.min(100, Math.round(progress.unique_questions / totalQuestions * 100)) : 0
  const activity = Array.from({ length: 28 }, (_, i) => {
    const day = new Date()
    day.setHours(12, 0, 0, 0)
    day.setDate(day.getDate() - (27 - i))
    const key = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`
    return { day: key, count: progress.daily_activity.find((item) => item.day === key)?.answered ?? 0 }
  })

  return <section className="learning-dashboard">
    <header className="learning-header">
      <div><p className="learning-eyebrow">Your study map · {collectionTitle}</p><h2>Your progress</h2><p className="learning-intro">{practiceAvailable?'A clear record of what you’ve practised in this exam, what’s going well, and where to focus next.':'Your previous answer activity is preserved here. Current preparation uses source papers; reading and written work do not add automatic scores.'}</p></div>
      <div className="learning-storage"><span className="learning-storage-dot"/><div><strong>{practiceAvailable?'Progress saved automatically':'Recorded answer activity'}</strong><small>{progress.last_active_at ? `Last practice ${new Date(progress.last_active_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}` : 'No practice recorded yet.'}</small></div></div>
    </header>

    {!started ? <section className="learning-start-panel"><div className="learning-start-icon" aria-hidden="true">↗</div><div className="learning-start-copy"><p className="learning-eyebrow">A fresh start</p><h3>Your {collectionTitle} progress starts with one question.</h3><p>{practiceAvailable?'Try a short practice set. Your answers, accuracy, section coverage and review list will build here automatically.':'This collection currently offers source reading and written preparation. Written work is not automatically graded or counted as answer attempts.'}</p></div><div className="learning-start-actions">{practiceAvailable&&<Link to={practiceLink} className="learning-primary-button">Start practice →</Link>}<Link to={paperLink} className="learning-secondary-button">Choose a paper</Link></div></section> : <section className="learning-overall"><div className="learning-overall-copy"><span>Question coverage</span><strong>{progress.unique_questions.toLocaleString('en-IN')} <small>of {totalQuestions.toLocaleString('en-IN')}</small></strong></div><div className="learning-overall-meter" role="progressbar" aria-label={`${collectionTitle} question coverage`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={coverage}><span style={{ width: `${coverage}%` }} /></div><div className="learning-overall-foot"><span>{coverage}% of the question set explored</span><Link to={practiceAvailable?practiceLink:paperLink}>{practiceAvailable?'Keep practising →':'Read source papers →'}</Link></div></section>}

    <div className="learning-summary-grid">{[
      ['Answer attempts', progress.answered.toLocaleString('en-IN'), `${progress.unique_questions.toLocaleString('en-IN')} distinct questions`, true],
      ['Accuracy', started ? `${progress.accuracy}%` : '—', started ? `${progress.correct.toLocaleString('en-IN')} correct answers` : 'Appears after your first answer', false],
      [progress.streak_basis==='device activity'?'Device activity':'Current streak', started ? `${progress.current_streak} days` : '—', started ? progress.streak_basis==='device activity'?'Consecutive days on this device':'Your account learning streak across exams' : 'Build a streak with regular practice', false],
      ['Active days', `${progress.active_days_30} / 30`, 'Days with practice in the last month', false],
    ].map(([label, value, foot, primary]) => <article key={String(label)} className={`learning-summary-card ${primary ? 'learning-summary-primary' : ''}`}><span>{label}</span><strong>{value}</strong><div className="learning-summary-foot">{foot}</div></article>)}</div>

    <div className="learning-dashboard-columns">
      <section className="learning-panel">
        <div className="learning-panel-heading"><div><p className="learning-eyebrow">Progress by section</p><h3>{started ? 'Your exam sections' : 'Sections are ready to explore'}</h3><p>Practice is grouped by the sections in this exam.</p></div></div>
        {progress.sections.length ? <div className="learning-area-list">{progress.sections.map((s) => {
          const accuracy = s.accuracy
          const status = accuracy < 50 ? 'Needs review' : accuracy < 75 ? 'Building' : 'Strong'
          const sectionUrl = `/exams/${collectionId}?view=browse${s.scope_id === 'unsectioned' ? '' : `&section=${encodeURIComponent(s.scope_id)}`}`
          return <article className="learning-area-row" key={s.scope_id}><div className="learning-area-main"><div className="learning-area-title"><strong>{s.label}</strong><span className={`learning-status ${accuracy < 50 ? 'is-weak' : accuracy < 75 ? 'is-developing' : 'is-strong'}`}>{status}</span></div><div className="learning-area-meta"><span>{s.unique_questions} distinct</span><span>{s.answered} attempts</span><span>{accuracy}% accuracy</span></div><div className="learning-meter"><span style={{ width: `${accuracy}%` }} /></div></div><div className="learning-area-numbers"><span><b>{s.correct}</b><small>correct</small></span></div><Link className="learning-link-button" to={sectionUrl}>Review →</Link></article>
        })}</div> : <div className="learning-empty-state"><span aria-hidden="true">◎</span><p>{!practiceAvailable?'Reading and written preparation do not produce automatic section scores.':started ? 'Section details will appear as you practise questions from this exam.' : 'Answer a few questions and this view will show your activity in each section.'}</p><Link to={practiceAvailable?practiceLink:paperLink}>{practiceAvailable?'Choose a practice set →':'Choose a source paper →'}</Link></div>}
      </section>

      <div className="learning-side-column">
        <section className="learning-panel"><div className="learning-panel-heading"><div><p className="learning-eyebrow">Last 28 days</p><h3>Practice activity</h3></div><span className="learning-status is-developing">{progress.active_days_30} active</span></div><div className="learning-activity-grid" aria-label="Daily answers over the last 28 days">{activity.map((item) => <div key={item.day} title={`${item.day}: ${item.count} answers`} aria-label={`${item.day}, ${item.count} answers`} className={`learning-activity-day ${item.count ? 'has-activity' : ''}`}><span>{item.count || ''}</span></div>)}</div><div className="learning-activity-legend"><span>Less</span>{[0, 1, 3, 6].map((level) => <i key={level} className={level ? 'has-activity' : ''} style={level ? { opacity: .25 + level * .1 } : undefined} />)}<span>More</span></div><p className="learning-panel-note">{started ? `${progress.answered.toLocaleString('en-IN')} answers recorded in this exam.` : 'Your daily activity will appear here after your first practice.'}</p></section>

        <section className="learning-panel"><div className="learning-panel-heading compact"><div><p className="learning-eyebrow">Review queue</p><h3>Questions to revisit</h3></div><span className={`learning-status ${mistakes.length ? 'is-weak' : 'is-developing'}`}>{mistakes.length} due</span></div>
          {collectionId==='udc'&&mistakes.length>0&&<Link to="/exams/udc?view=practice&status=wrong#exam-question-browser" className="mb-3 inline-flex min-h-11 items-center rounded-pill border border-ink px-4 text-sm font-semibold">Practise UDC mistakes →</Link>}
          {mistakes.length ? <div className="learning-queue-list">{mistakes.slice(0, 8).map((m) => <Link className="learning-queue-row" key={m.id} to={`/bank/${m.id}`}><span><strong>{m.question}</strong><small>Missed {m.times_wrong} times · Review question</small></span><b>{m.times_wrong}</b><span className="learning-queue-arrow">›</span></Link>)}</div> : <div className="learning-queue-empty"><span aria-hidden="true">✓</span><p>{started ? 'Nothing is waiting for review right now.' : 'Missed questions will be collected here so you can revisit them later.'}</p>{!started&&practiceAvailable && <Link to={practiceLink}>Start a practice set →</Link>}</div>}
        </section>
      </div>
    </div>
  </section>
}
