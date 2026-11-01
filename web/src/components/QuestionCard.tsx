import PracticeAnswerPanel from './PracticeAnswerPanel'
import {questionTopicLabel} from '../lib/questionLabels'
import {savePracticePosition} from '../lib/learning'
import AnswerProvenance from './AnswerProvenance'
import {scopeLink} from '../lib/examScope'
import {QuestionActions} from './QuestionDiscussion'
import {AnswerOptions} from './AnswerLayout'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { submitAnswer, type AnswerResult, type Question } from '../lib/api'
import { SourceQuestionContext, SourceQuestionText } from './SourceQuestionText'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

/** Bank question card, ported from `India Study Map v3.dc.html` line 407.
 *  Exact values and the README-vs-markup disagreements are recorded in
 *  docs/DESIGN-FIDELITY.md — read that before changing anything here. */
export default function QuestionCard({ q, onAnswered, onNext }: { q: Question; onAnswered?: () => void; onNext?:()=>void }) {
  const [picked, setPicked] = useState<number | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [answerError, setAnswerError] = useState('')

  const [viewed,setViewed]=useState(false)
  async function pick(i: number) {
    if (result || busy || viewed) return
    setAnswerError('')
    setPicked(i)
    setBusy(true)
    try {
      setResult(await submitAnswer(q.id, i))
      void savePracticePosition(q.id).catch(()=>{})
      onAnswered?.()
    } catch (error) {
      setAnswerError(error instanceof Error ? error.message : 'Answer could not be checked. Please try again.')
      setPicked(null) // let them try again rather than stranding a selection
    } finally {
      setBusy(false)
    }
  }

  const years = [q.first_year, q.last_year].filter(Boolean)
  const source = q.source_appearance
  const answerable = !q.held && q.answer_source !== 'none' && !['duplicate-options','unresolved-source'].includes(q.source_defect||'')
  const yearLabel = years.length === 2 && years[0] !== years[1]
    ? `${years[0]}, ${years[1]}`
    : String(years[0] ?? '—')
  const sourceNote = q.source_defect === 'correct-option-added'
    ? 'Source correction · none of the printed choices is correct. A clearly labelled practice answer was added; it is not an option from the original paper.'
    : q.source_defect === 'diagram-not-embedded'
      ? 'Diagram note · the figure artwork is in the original PDF, not embedded here. Open the source PDF below before answering.'
      : null


  return (
    <article id={'question-'+q.id} className="mb-3 rounded-[14px] border border-hairline bg-card px-[22px] py-5 shadow-[0_1px_2px_rgba(29,27,24,.05)]">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        {(q.taxonomy_topic || q.taxonomy_subject) && (
          <span className="rounded-pill bg-practice-soft px-[9px] py-[3px] font-mono text-[10px] uppercase tracking-[0.06em] text-practice-dark">
            {questionTopicLabel(q)}
          </span>
        )}
        {q.taxonomy_paths?.filter(p=>!p.is_primary).map(p=><Link key={p.subtopic_id||p.topic_id||p.subject_id} to={'/library/subjects/'+encodeURIComponent(p.subject_id)+(p.topic_id?'?topic_id='+encodeURIComponent(p.topic_id):'')} className="rounded-pill border border-hairline px-2 py-1 text-[10px] text-link">{p.subtopic_label||p.topic_label||p.subject_label}</Link>)}
        <span className="font-mono text-[11px] text-muted">
          {q.last_year ?? q.first_year ?? '—'} · {q.type === 'mcq' ? 'MCQ' : 'Descriptive'}
        </span>

        <AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.type==='mcq'?q.id:undefined} outlined />

        {q.times_asked > 1 && (
          <span
            title={yearLabel}
            className="rounded-pill bg-ink px-[9px] py-[3px] font-mono text-[10px] uppercase tracking-[0.06em] text-paper"
          >
            Asked {q.times_asked}× · {yearLabel}
          </span>
        )}

        <Link
          to={scopeLink(`/bank/${q.id}`)}
          className="ml-auto inline-flex min-h-11 items-center rounded-pill px-2 font-mono text-[11px] text-secondary hover:text-link hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-link"
        >
          Open question →
        </Link>
      </div>

      <div className="max-w-[75ch] my-[10px] mb-[14px] font-display text-[21px] leading-[1.35] [text-wrap:pretty]">
        <SourceQuestionContext direction={q.direction} passage={q.passage} />
        <SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup ?? q.question} />
      </div>

      {q.figure_image_url && <a href={q.figure_image_url} target="_blank" rel="noreferrer" className="mb-3 block max-w-2xl overflow-hidden rounded-[9px] border border-hairline bg-paper" aria-label="Open original question figure"><img src={q.figure_image_url} loading="lazy" decoding="async" alt="Original scanned figure or chart for this question" className="max-h-[360px] w-full object-contain" /><span className="block border-t border-hairline px-3 py-2 font-mono text-[10px] uppercase tracking-wide text-muted">Original source figure · open full image ↗</span></a>}

      {q.key_disputed && <p className="mb-3 rounded-[8px] border border-[#D8B56D] bg-[#FFF4DF] px-3 py-2 text-[12px] leading-relaxed text-[#684919]">Key discrepancy · the official answer key conflicts with this reviewed derived answer. It is shown for practice and is excluded from official-key scoring.{q.dispute_note ? ` ${q.dispute_note}` : ''}</p>}

      {sourceNote && <p className="mb-3 rounded-[8px] border border-[#D8B56D] bg-[#FFF4DF] px-3 py-2 text-[12px] leading-relaxed text-[#684919]">{sourceNote}</p>}


      {q.options.length > 0 && (
        <AnswerOptions>
          {q.options.map((text, i) => {
            const isCorrect = result?.answer_index === i
            const isPick = picked === i
            let cls = 'bg-opt-bg border-opt-border text-ink'
            let mark = ''
            if (result) {
              if (isCorrect) {
                cls = 'bg-keyed-soft border-keyed text-ink'
                mark = isPick ? (result.verified||q.reviewed_derived?'Correct':'Matches stored answer') : (result.verified||q.reviewed_derived?'Answer':'Stored answer')
              } else if (isPick) {
                cls = 'bg-mypick-soft border-mypick text-ink'
                mark = 'Your pick'
              } else {
                cls = 'bg-opt-bg border-opt-border text-opt-muted'
              }
            }
            return (
              <button
                key={i}
                onClick={() => setPicked(i)}
                disabled={text === null || !answerable || !!result || busy || viewed}
                aria-pressed={isPick}
                data-answer-state={isCorrect?'correct':result&&isPick?'wrong':isPick?'selected':'neutral'}
                className={`answer-option flex min-h-[44px] items-center gap-3 rounded-[6px] border px-[14px] py-[11px] text-left text-[15px] ${cls} ${
                  result || !answerable || text === null ? 'cursor-default opacity-70' : 'cursor-pointer'
                }`}
              >
                <span className="w-4 shrink-0 font-mono text-[12px]">{LETTERS[i]}</span>
                <span className="flex-1">{text === null ? 'Option text unavailable' : <SourceQuestionText text={q.options_markup?.[i] ?? text} />}</span>
                {/* The prototype marks state with a WORD, not a symbol. */}
                {mark && <span className="shrink-0 font-mono text-[11px]">{mark}</span>}
              </button>
            )
          })}
        </AnswerOptions>
      )}

      {answerError && <p role="alert" className="mt-3 text-[13px] text-mypick">{answerError}</p>}
      {!answerable && q.options.length > 0 && (
        <p className="mt-3 text-[13px] text-muted">This question is held for review or has no usable answer yet. Browse its source, compare the evidence or suggest a correction.</p>
      )}

      {!result&&!viewed&&answerable&&q.type==='mcq'&&<button type="button" disabled={picked===null||busy} onClick={()=>picked!==null&&void pick(picked)} className="mt-3 min-h-11 rounded-pill bg-ink px-4 py-2 text-[13px] text-paper disabled:opacity-40">{busy?'Checking…':'Check answer'}</button>}
      {q.type==='mcq'&&<PracticeAnswerPanel qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={source?.paper_id} year={source?.year ?? q.first_year ?? q.last_year} available={answerable} disabled={busy} onBusy={setBusy} onViewed={setViewed} onRetry={()=>{setPicked(null);setResult(null)}} onNext={onNext}/>}
      <QuestionActions questionType={q.type} qid={q.id} context={{paper_id:q.source_appearance?.paper_id}} answeredSignal={result}/>
      {source && <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-hairline pt-3 text-[12px] text-secondary"><span><strong className="font-semibold text-ink">Source:</strong> {source.exam || source.paper_id.split('/').pop()}{source.year ? ` · ${source.year}` : ''}{source.paper_label ? ` · ${source.paper_label}` : source.paper ? ` · Paper ${source.paper}` : ''}{source.section_label ? ` · Section: ${source.section_label}` : ''}{source.series ? ` · Series ${source.series}` : ''}{source.qnum ? ` · Q${source.qnum}` : ''}{source.page ? ` · p. ${source.page}` : ''}</span>{source.source_pdf_url && <a href={`${source.source_pdf_url}${source.page ? `#page=${source.page}` : ''}`} target="_blank" rel="noreferrer" className="font-semibold text-link underline">Source PDF ↗</a>}{q.times_asked > 1 && <Link to={scopeLink(`/bank/${q.id}`)} className="font-semibold text-link underline">All {q.times_asked} appearances ↗</Link>}</div>}
    </article>
  )
}
