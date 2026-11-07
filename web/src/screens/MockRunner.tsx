import {getSharedTest,mockResumePath} from '../lib/sharedTests'
import {AnswerOptions,AnswerLayoutControl} from '../components/AnswerLayout'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import MockResultView, { mmss } from '../components/MockResultView'
import { SourceQuestionContext, SourceQuestionText } from '../components/SourceQuestionText'
import {
  currentMock,
  getMockResult,
  getCollection,
  isLaterExamCollection,
  startMock,
  saveMockAnswer,
  submitMock,
  type MockResult,
  type MockSession,
} from '../lib/api'

/** The timed paper — the prototype's `exam` screen, line 579.
 *  Named MockRunner because `exam` is ambiguous here; see
 *  docs/DESIGN-FIDELITY.md.
 *
 *  The countdown below is DISPLAY ONLY. The server recorded started_at and
 *  recomputes elapsed time on submit, so stopping this timer in a debugger
 *  buys nothing. */

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

export default function MockRunner() {
  const { id: collectionId = '',testId } = useParams()
  const backTo=testId?'/tests/'+encodeURIComponent(testId):'/exams/'+collectionId
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sectionPath = searchParams.get('section') || undefined
  const paperId = searchParams.get('paper') || undefined
  const paperMode=searchParams.get('simulation')==='full'?'full':'practice'
  const answerMode = searchParams.get('mode') === 'derived' ? 'derived-practice' : 'official'
  const [mock, setMock] = useState<MockSession | null>(null)
  const [paperTitle, setPaperTitle] = useState('Preparing your paper')
  const [result, setResult] = useState<MockResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [at, setAt] = useState(0)
  const [picks, setPicks] = useState<Record<string, number>>({})
  const [marked, setMarked] = useState<Record<string, boolean>>({})
  const [left, setLeft] = useState(0)
  const [busy, setBusy] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [loadingSlow, setLoadingSlow] = useState(false)
  const submitted = useRef(false)
  const saveQueue = useRef(Promise.resolve())

  // Reuse one server-owned session. Shared tests carry an immutable edition.
  useEffect(() => {
    let dead = false
    const slowTimer=window.setTimeout(()=>{if(!dead)setLoadingSlow(true)},12000)
    const matches=(m:MockSession)=>testId?m.learning_test_id===testId:!m.learning_test_id&&m.collection_id===collectionId&&(m.paper_id??undefined)===paperId&&(paperId||(m.section_path??undefined)===sectionPath)&&m.answer_mode===answerMode&&(m.paper_mode||'practice')===paperMode
    ;(async()=>{
      try {
        const existing=await currentMock()
        if(existing&&!matches(existing)){navigate(mockResumePath(existing),{replace:true});return}
        const shared=testId&&!existing?await getSharedTest(testId):null
        const collection=!testId?await getCollection(collectionId):null
        if(collection&&isLaterExamCollection(collection))throw new Error('LDE exam practice will be added as the exam library grows.')
        const m=existing??await startMock(shared?{
          collection_id:'shared-tests',learning_test_id:shared.id,learning_test_version:shared.revision,
        }:{collection_id:collectionId,section_path:sectionPath,paper_id:paperId,answer_mode:answerMode,paper_mode:paperMode,count:20,duration_minutes:20}).catch(async error=>{const resumed=await currentMock();if(resumed)return resumed;throw error})
        if(!matches(m)){navigate(mockResumePath(m),{replace:true});return}
        const section=collection?.section_list.find(s=>s.path===m.section_path),paper=collection?.paper_list.find(p=>p.id===m.paper_id)
        if(!dead){
          setLoadingSlow(false);setError(null);setMock(m);setLeft(m.seconds_remaining);setPicks(m.saved_answers||{});setMarked(Object.fromEntries((m.marked_questions||[]).map(id=>[id,true])));setAt(m.current_position||0)
          setPaperTitle(m.learning_test_title?m.learning_test_title+' · edition '+m.learning_test_version:`${collection?.title}${paper?' · '+paper.title:section?' · '+section.title:''} · ${answerMode==='derived-practice'?'Practice estimate':paper?(paper.rule_source==='platform-default'?'Timed practice':'Paper test'):'Mock'}`)
        }
      }catch(e){if(!dead)setError((e as Error).message)}finally{window.clearTimeout(slowTimer)}
    })()
    return()=>{dead=true;window.clearTimeout(slowTimer)}
  },[collectionId,testId,sectionPath,paperId,answerMode,paperMode,navigate])

  const persistAnswer = (question_id: string, chosen_index: number | null, isMarked: boolean, position: number) => {
    if (!mock) return
    saveQueue.current = saveQueue.current.then(async () => {
      try {
        await saveMockAnswer(mock.id,{question_id,chosen_index,marked:isMarked,position})
        setSaveError(null)
      } catch (e) { setSaveError(`Could not save this answer yet: ${(e as Error).message}`) }
    })
  }

  const send = useCallback(async () => {
    if (!mock || submitted.current) return
    submitted.current = true
    setBusy(true)
    try {
      await saveQueue.current
      const saved=await submitMock(mock.id,Object.entries(picks).map(([question_id,chosen_index])=>({question_id,chosen_index}))).catch(async error=>{try{return await getMockResult(mock.id)}catch{throw error}})
      setResult(saved)
      navigate('/results/'+saved.id,{replace:true})
    } catch (e) {
      setError((e as Error).message)
      submitted.current = false
    } finally {
      setBusy(false)
    }
  }, [mock, picks,navigate])

  // Tick for display, and auto-submit at zero so an abandoned tab still
  // produces a result rather than an orphaned open session.
  useEffect(() => {
    if (!mock || result) return
    const t = setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          clearInterval(t)
          void send()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [mock, result, send])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="rounded-[14px] border border-mypick bg-mypick-soft p-5 text-mypick">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to={backTo} className="label mt-4 inline-block underline">
          ← Back to {testId?'test':'exam'}
        </Link>
      </div>
    )
  }
  if (result)
    return <MockResultView result={result} backTo={backTo} />
  if (!mock) return <div className="mx-auto max-w-shell px-6 py-12 label">{loadingSlow ? <><p>This paper is taking longer than expected. Check your connection, then reload to resume.</p><button onClick={() => window.location.reload()} className="mt-4 rounded-pill border border-ink px-4 py-2 text-[13px] font-semibold">Reload paper</button></> : 'Preparing your paper…'}</div>

  const q = mock.questions[at]
  const answered = Object.keys(picks).length
  const nMarked = Object.values(marked).filter(Boolean).length
  const low = left <= 60

  return (
    <div className="exam-session">
      {/* Sticky dark bar, markup line 579. */}
      <div className="exam-session-bar sticky top-0 z-40 bg-ink text-paper">
        <div className="mx-auto flex max-w-shell flex-wrap items-center gap-x-5 gap-y-2.5 px-6 py-2.5">
          <Link to={backTo} className="text-[14px] font-medium text-[#D9D0BF]">
            ← Exit
          </Link>
          <div className="min-w-0 flex-[1_1_280px]">
            <div className="font-display text-[19px] font-medium">{paperTitle}</div>
            <div className="font-mono text-[11px] text-[#BDB3A0]">
              {mock.questions.length} questions · timed practice
            </div>
          </div>
          <div
            className={`exam-clock font-mono text-[22px] font-medium tracking-[0.02em] ${low ? 'text-mypick-soft' : ''}`}
            aria-live="off"
          >
            <span className="exam-clock-label">Time remaining</span>{mmss(left)}
          </div>
          <button
            onClick={send}
            disabled={busy}
            className="rounded-pill bg-paper px-[18px] py-[9px] text-[14px] font-semibold text-ink disabled:opacity-50"
          >
            {busy ? 'Submitting…' : 'Submit paper'}
          </button>
        </div>
      </div>

      {saveError && <p role="status" className="mx-auto mt-3 max-w-shell rounded-[8px] border border-mypick bg-mypick-soft px-4 py-2 text-[13px] text-mypick">{saveError} Keep this page open and try again before submitting.</p>}

      {!!mock.excluded_presentations&&<p className="mx-auto mt-3 max-w-shell rounded-[8px] border border-hairline bg-paper px-4 py-2 text-[13px]">{mock.excluded_presentations} source appearances were excluded because their options or context could not be safely mapped. This test scores only the displayed questions.</p>}
      {mock.answer_mode === 'derived-practice' && <p className="mx-auto mt-3 max-w-shell rounded-[8px] border border-[#D8B56D] bg-[#FFF4DF] px-4 py-2 text-[13px] text-[#684919]">Practice estimate · includes reviewed worked solutions. This is not an official-key test score.</p>}

      <main className="exam-session-layout mx-auto flex max-w-shell flex-wrap items-start gap-10 px-6 pb-24 pt-8">
        <section className="exam-sheet exam-active-sheet min-w-0 flex-[999_1_560px]" aria-label="Current question">
          <div className="flex justify-between gap-2.5 border-b border-ink pb-2.5 font-mono text-[12px] text-muted">
            <span>Question {at + 1} of {mock.questions.length}</span>
            <span>{marked[q.id] ? 'Marked for review' : ''}</span>
          </div>

          <div className="my-6 font-display text-[clamp(22px,2.6vw,28px)] leading-[1.35] [text-wrap:pretty]">
            <SourceQuestionContext direction={q.direction} passage={q.passage} />
            <SourceQuestionText instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup ?? q.question} />
          </div>
          {q.figure_image_url && <a href={q.figure_image_url} target="_blank" rel="noreferrer" className="mb-5 block max-w-2xl overflow-hidden rounded-[9px] border border-hairline bg-paper" aria-label="Open original question figure"><img src={q.figure_image_url} alt="Original figure for this question" decoding="async" className="max-h-[420px] w-full object-contain"/><span className="block border-t border-hairline px-3 py-2 text-[11px] text-secondary">Original source figure · open full image ↗</span></a>}
          {q.source_pdf_url && <a href={`${q.source_pdf_url}${q.page ? `#page=${q.page}` : ''}`} target="_blank" rel="noreferrer" className="-mt-3 mb-5 inline-block text-[12px] font-semibold text-[#486B62] underline underline-offset-2">Open original question · page {q.page ?? 'not listed'} ↗</a>}

          <AnswerLayoutControl/><AnswerOptions>
            {q.options.map((text, i) => {
              const on = picks[q.id] === i
              return (
                <button
                  key={i}
                  onClick={() => { setPicks((p) => ({ ...p, [q.id]: i })); persistAnswer(q.id,i,!!marked[q.id],at) }}
                  aria-pressed={on}
                  data-answer-state={on?'selected':'neutral'}
                  className={`answer-option flex items-center gap-3.5 rounded-[6px] border p-4 text-left text-[16px] ${
                    on ? 'border-ink bg-[#EDE5D4]' : 'border-opt-border bg-opt-bg hover:border-ink'
                  }`}
                >
                  <span
                    className={`flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border border-ink font-mono text-[12px] ${
                      on ? 'bg-ink text-paper' : 'bg-transparent text-ink'
                    }`}
                  >
                    {LETTERS[i]}
                  </span>
                  <span>{text === null ? 'Option unavailable in source' : <SourceQuestionText text={q.options_markup?.[i] ?? text} />}</span>
                </button>
              )
            })}
          </AnswerOptions>

          <div className="exam-sheet-navigation mt-7 flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => { const next=Math.max(0,at-1); setAt(next); persistAnswer(q.id,picks[q.id]??null,!!marked[q.id],next) }}
              disabled={at === 0}
              className="rounded-pill border border-ink px-[18px] py-[11px] text-[14px] font-semibold disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => { const next=!marked[q.id]; setMarked((m) => ({ ...m, [q.id]: next })); persistAnswer(q.id,picks[q.id]??null,next,at) }}
              className="rounded-pill border border-prov px-[18px] py-[11px] text-[14px] font-semibold text-prov"
            >
              {marked[q.id] ? 'Unmark' : 'Mark for review'}
            </button>
            <button
              onClick={() => {
                setPicks((p) => {
                  const { [q.id]: _drop, ...rest } = p
                  return rest
                })
                persistAnswer(q.id,null,!!marked[q.id],at)
              }}
              className="px-[18px] py-[11px] text-[14px] text-secondary"
            >
              Clear
            </button>
            <div className="flex-1" />
            <button
              onClick={() => { const next=Math.min(mock.questions.length-1,at+1); setAt(next); persistAnswer(q.id,picks[q.id]??null,!!marked[q.id],next) }}
              disabled={at === mock.questions.length - 1}
              className="rounded-pill bg-ink px-[22px] py-[11px] text-[14px] font-semibold text-paper disabled:opacity-40"
            >
              Save &amp; next
            </button>
          </div>
        </section>

        <aside className="exam-answer-sheet min-w-0 max-w-[380px] flex-[1_1_300px]" aria-label="Answer sheet">
          <div className="answer-sheet-title">Your answer sheet</div>
          <p className="answer-sheet-hint">Select a number to revisit a question.</p>
          <progress className="exam-completion" aria-label="Questions answered" value={answered} max={mock.questions.length}/>
          <div className="flex justify-between border-b border-ink pb-2 font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
            <span>Progress</span>
            <span>{answered} answered · {nMarked} marked</span>
          </div>
          <div className="exam-question-map mt-3.5 grid grid-cols-6 gap-[5px] sm:grid-cols-10">
            {mock.questions.map((mq, i) => {
              const isAns = picks[mq.id] !== undefined
              const isMark = !!marked[mq.id]
              const cur = i === at
              const cls = isMark
                ? 'bg-[#DCE5EE] text-prov'
                : isAns
                  ? 'bg-ink text-paper'
                  : 'bg-transparent text-secondary'
              const border = cur
                ? 'border-mypick'
                : isMark
                  ? 'border-prov'
                  : isAns
                    ? 'border-ink'
                    : 'border-[#CFC5B2]'
              return (
                <button
                  key={mq.id}
                  aria-label={`Question ${i + 1}, ${isAns ? 'answered' : 'unanswered'}${isMark ? ', marked for review' : ''}`}
                  aria-current={cur ? 'step' : undefined}
                  onClick={() => { setAt(i); persistAnswer(mq.id,picks[mq.id]??null,!!marked[mq.id],i) }}
                  className={`flex aspect-square items-center justify-center rounded-[4px] border font-mono text-[11px] ${cls} ${border}`}
                >
                  {i + 1}
                </button>
              )
            })}
          </div>
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-[12px] text-secondary">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] bg-ink" />Answered
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] bg-[#DCE5EE]" />Marked
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-[3px] border border-[#CFC5B2]" />Unanswered
            </span>
          </div>
        </aside>
      </main>
    </div>
  )
}
