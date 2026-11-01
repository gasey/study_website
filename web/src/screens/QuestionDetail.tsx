import PracticeAnswerPanel from '../components/PracticeAnswerPanel'
import QuestionUpdate from '../components/QuestionUpdate'
import {savePracticePosition} from '../lib/learning'
import {QuestionActions} from '../components/QuestionDiscussion'
import {AnswerOptions,AnswerLayoutControl} from '../components/AnswerLayout'
import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { RepeatBadge } from '../components/ProvenanceTag'
import AnswerProvenance, {evidenceLink} from '../components/AnswerProvenance'
import {
  getQuestion,
  submitAnswer,
  type AnswerResult,
  type QuestionDetail as QD,
} from '../lib/api'
import { getDesk, getDeskSync, saveDesk, subscribeDesk, trackRecentQuestion } from '../lib/desk'
import { SourceQuestionContext, SourceQuestionText } from '../components/SourceQuestionText'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

export default function QuestionDetail() {
  const { id = '' } = useParams()
  const [params]=useSearchParams()
  const [q, setQ] = useState<QD | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [picked, setPicked] = useState<number | null>(null)
  const [answerError,setAnswerError]=useState('')
  const [viewed,setViewed]=useState(false)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [deskLoading, setDeskLoading] = useState(() => getDeskSync().loading)
  const [saved, setSaved] = useState(() => getDesk().saved.includes(id))

  useEffect(() => {
    setQ(null)
    setPicked(null)
    setResult(null)
    setViewed(false)
    setAnswerError('')
    setError(null)
    setSaved(getDesk().saved.includes(id))
    getQuestion(id)
      .then((question) => { setQ(question); trackRecentQuestion(id); void savePracticePosition(id).catch(()=>{}) })
      .catch((e) => setError(e.message))
  }, [id])

  useEffect(() => subscribeDesk(() => { setSaved(getDesk().saved.includes(id)); setDeskLoading(getDeskSync().loading) }), [id])

  function toggleSaved() {
    if (getDeskSync().loading) return
    const data = getDesk()
    const next = saved ? data.saved.filter((qid) => qid !== id) : [id, ...data.saved.filter((qid) => qid !== id)]
    saveDesk({ ...data, saved: next })
    setSaved(!saved)
  }

  async function reveal() {
    if (picked === null || result || viewed || submitting) return
    setSubmitting(true)
    setAnswerError('')
    try {
      // The client does not know the answer until this returns — the server
      // never sent it with the question.
      setResult(await submitAnswer(id, picked, 'practice',undefined,params.get('paper')||undefined))
    } catch (e) {
      setAnswerError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-card border border-wrong bg-wrong-soft p-5 text-wrong-dark">
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">× Error</span>
          <p className="mt-1">{error}</p>
        </div>
        <Link to="/bank" className="label mt-4 inline-block underline">
          ← Back to the bank
        </Link>
      </div>
    )
  }

  if (!q) return <div className="mx-auto max-w-3xl px-6 py-10 label">Loading…</div>

  const sourceNote = q.source_defect === 'correct-option-added'
    ? 'Source correction · none of the printed choices is correct. A clearly labelled practice answer was added; it is not an option from the original paper.'
    : q.source_defect === 'diagram-not-embedded'
      ? 'Diagram note · the figure artwork is in the original PDF below. Open the source paper before answering.'
      : null

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <Link to="/bank" className="label underline">
        ← Bank
      </Link>

      <QuestionUpdate questionId={id}/>
      <div id={'question-'+id} className="mt-4 rounded-card border border-hairline bg-card p-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="label text-practice-dark">
            {q.last_year ?? q.first_year ?? '—'}
          </span>
          <span className="text-hairline2">·</span>
          <span className="label">{q.type === 'mcq' ? 'MCQ' : 'Descriptive'}</span>
          <span className="grow" />
          <RepeatBadge times={q.times_asked} />
          <AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.type==='mcq'?q.id:undefined} />
          <button type="button" onClick={toggleSaved} disabled={deskLoading} aria-pressed={saved} className={`min-h-11 rounded-pill border px-3 py-2 text-[12px] font-semibold ${saved ? 'border-learn-dark bg-learn-soft text-learn-dark' : 'border-hairline text-secondary'}`}>
            {deskLoading ? 'Loading saved questions…' : saved ? '★ Saved' : '☆ Save for revision'}
          </button>
        </div>

        <SourceQuestionContext direction={q.direction} passage={q.passage} />
        <h1 className="font-display text-[24px] font-medium leading-snug"><SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup ?? q.question} /></h1>

        {q.appearances.some((a) => a.figure_image_url) && <div className="mt-4 grid gap-3">{q.appearances.filter((a) => a.figure_image_url).map((a) => <figure key={`${a.paper_id}-${a.page}`} className="max-w-2xl overflow-hidden rounded-[9px] border border-hairline bg-paper"><a href={a.figure_image_url!} target="_blank" rel="noreferrer"><img src={a.figure_image_url!} loading="lazy" decoding="async" alt="Original scanned figure or chart from the source paper" className="max-h-[360px] w-full object-contain" /></a><figcaption className="border-t border-hairline px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-muted">Original source figure · {a.exam ?? 'MPSC paper'} · p. {a.page ?? '—'}</figcaption></figure>)}</div>}

        {!q.verified&&q.type==='mcq'&&<p className="mt-3 text-[13px] text-secondary"><Link to={evidenceLink(q.id)} className="inline-flex min-h-[44px] items-center font-semibold text-link underline">{q.reviewed_derived?'Improve this solution · submit evidence →':'Help verify this answer · submit evidence →'}</Link></p>}
        {q.key_disputed && <p className="mt-4 rounded-panel border border-[#D8B56D] bg-[#FFF4DF] p-4 text-[13px] leading-relaxed text-[#684919]">Key discrepancy · the Commission’s official key conflicts with this reviewed derived answer. It is available for practice but excluded from official-key scoring.{q.dispute_note ? ` ${q.dispute_note}` : ''}</p>}

        {sourceNote && <p className="mt-4 rounded-panel border border-[#D8B56D] bg-[#FFF4DF] p-4 text-[13px] leading-relaxed text-[#684919]">{sourceNote}</p>}

        {q.options.length > 0 && (
          <> <AnswerLayoutControl/><AnswerOptions as="ol" className="mt-3">
            {q.options.map((o, i) => {
              const isPicked = picked === i
              const isAnswer = result?.answer_index === i
              const wrongPick = !!result && isPicked && !result.correct

              let cls = 'border-hairline bg-card hover:border-ink'
              if (result) {
                if (isAnswer) cls = 'border-correct bg-correct-soft'
                else if (wrongPick) cls = 'border-wrong bg-wrong-soft'
                else cls = 'border-hairline bg-card opacity-60'
              } else if (isPicked) {
                cls = 'border-ink bg-paper'
              }

              return (
                <li key={i}>
                  <button
                    disabled={!!result || viewed || submitting || o === null}
                    onClick={() => o !== null && setPicked(i)}
                    aria-pressed={isPicked}
                    data-answer-state={isAnswer?'correct':wrongPick?'wrong':isPicked?'selected':'neutral'}
                    className={`answer-option flex w-full items-start gap-3 rounded-panel border p-3 text-left text-[15px] transition-colors ${cls}`}
                  >
                    <span className="label mt-[2px] shrink-0">{LETTERS[i]}</span>
                    <span className="grow">{o === null ? 'Option text unavailable' : <SourceQuestionText text={q.options_markup?.[i] ?? o} />}</span>
                    {/* States always carry a symbol, never colour alone. */}
                    {result && isAnswer && <span className="text-correct-dark">✓</span>}
                    {wrongPick && <span className="text-wrong-dark">×</span>}
                  </button>
                </li>
              )
            })}
          </AnswerOptions></>
        )}

        {!result && !viewed && q.options.length > 0 && q.answer_source!=='none' && !q.held && (
          <button
            disabled={picked === null || submitting}
            onClick={reveal}
            className="mt-5 rounded-pill bg-ink px-5 py-2 text-[14px] text-paper disabled:opacity-40"
          >
            {submitting ? 'Checking…' : 'Check answer'}
          </button>
        )}

        {answerError&&<p role="alert" className="mt-3 text-[13px] text-mypick">{answerError}</p>}
        {q.held&&<p className="mt-4 rounded-panel border border-[#D9B76B] bg-[#FFF4D9] p-3 text-[13px] text-[#705015]">This question is held for review and cannot be checked or scored. Compare the official key and reviewed evidence below.</p>}
        {q.answer_source==='none'&&<p className="mt-4 text-[13px] text-secondary">No checkable answer is available yet. You can submit a worked solution with evidence even when no official key is available.</p>}
        {q.type==='mcq'&&<PracticeAnswerPanel key={id+':'+(params.get('paper')||'')} qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={params.get('paper')} year={q.appearances.find(a=>a.paper_id===params.get('paper'))?.year ?? (new Set(q.appearances.map(a=>a.year)).size===1?q.appearances[0]?.year:null)} available={!q.held&&q.answer_source!=='none'&&!['duplicate-options','unresolved-source'].includes(q.source_defect||'')} disabled={submitting} onBusy={setSubmitting} onViewed={setViewed} onRetry={()=>{setPicked(null);setResult(null);setAnswerError('')}}/>}

      </div>

      <div id="discussion"><QuestionActions questionType={q.type} key={id} qid={id} context={{paper_id:q.appearances.find(a=>a.paper_id===params.get('paper'))?.paper_id,collection_id:params.get('exam')}} answeredSignal={result} initialOpen={true}/></div>
      <section className="mt-6">
        <h2 className="label text-exams-dark">
          Appeared in {q.appearances.length} paper{q.appearances.length === 1 ? '' : 's'}
        </h2>
        <ul className="mt-2 grid gap-2">
          {q.appearances.map((a, i) => (
            <li
              key={i}
              className="rounded-panel border border-hairline bg-card px-4 py-3 text-[14px]"
            >
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="label text-exams-dark">{a.year ?? '—'}</span>
                <span className="text-secondary">{a.exam ?? a.paper_id}</span>
                {(a.paper_label || a.paper) && <span className="label">{a.paper_label || `Paper ${a.paper}`}</span>}
                {a.section_label && <span className="label">Section: {a.section_label}</span>}
                {a.qnum && <span className="label">Q{a.qnum}</span>}
                {a.page && <span className="label">p.{a.page}</span>}
                {a.source_pdf_url && (
                  <a
                    href={`${a.source_pdf_url}${a.page ? `#page=${a.page}` : ''}`}
                    target="_blank"
                    rel="noreferrer"
                    className="ml-auto font-semibold text-exams-dark underline underline-offset-2"
                  >
                    View source PDF ↗
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
