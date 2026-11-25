import AtlasQuestionLinks from './AtlasQuestionLinks'
import {answerStatus} from '../lib/answerStatus'
import PracticeAnswerPanel from './PracticeAnswerPanel'
import {questionTopicLabel} from '../lib/questionLabels'
import {formatQuestionSource, resolveQuestionGuide} from '../lib/questionGuideLink'
import {savePracticePosition} from '../lib/learning'
import AnswerProvenance from './AnswerProvenance'
import {scopeLink} from '../lib/examScope'
import {QuestionActions} from './QuestionDiscussion'
import {AnswerOptions} from './AnswerLayout'
import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { submitAnswer, type AnswerResult, type Question } from '../lib/api'
import { SourceQuestionContext, SourceQuestionText } from './SourceQuestionText'
import SaveToVaultButton from './SaveToVaultButton'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

/** Bank question card, ported from `India Study Map v3.dc.html` line 407.
 *  Exact values and the README-vs-markup disagreements are recorded in
 *  docs/DESIGN-FIDELITY.md — read that before changing anything here. */
export default function QuestionCard({ q, onAnswered, onNext }: { q: Question; onAnswered?: () => void; onNext?:()=>void }) {
  const [picked, setPicked] = useState<number | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [answerError, setAnswerError] = useState('')

  const sending=useRef(false)
  const [viewed,setViewed]=useState(false)
  async function pick(i: number) {
    if (result || busy || viewed || sending.current || !answerable) return
    sending.current=true
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
      sending.current=false;setBusy(false)
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

  const sourceInfo = useMemo(
    () => formatQuestionSource(q),
    [q.source_appearance, q.first_year, q.last_year],
  )
  const guideMatch = useMemo(
    () => resolveQuestionGuide(q),
    [q.taxonomy_subject_id, q.taxonomy_topic_id, q.taxonomy_subtopic_id, q.subject, q.topic, q.question],
  )
  const actions = <QuestionActions questionType={q.type} qid={q.id} context={{paper_id:q.source_appearance?.paper_id}} answeredSignal={result}/>

  const isWritten = q.type !== 'mcq'
  return (
    <article id={'question-'+q.id} data-question-type={isWritten ? 'written' : 'mcq'} className={`compact-question q-sheet-card mb-4 rounded-[18px] border border-hairline bg-card px-5 py-5 shadow-[var(--ism-card-shadow)] sm:px-6${isWritten ? ' border-l-4 border-l-amber-600' : ''}`}>
      <AtlasQuestionLinks qid={q.id} links={q.atlas_links||[]} context={q.type==='mcq'&&['official','verified'].includes(q.answer_status||'')}/>
      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-2 border-b border-hairline/70 pb-3">
        <span className={isWritten
          ? 'rounded-pill border border-amber-500/40 bg-amber-500/15 px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.06em] text-amber-800 dark:text-amber-300'
          : 'rounded-pill border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.06em] text-blue-700 dark:text-blue-300'}>
          {isWritten ? '✎ Written' : '◉ MCQ'}
        </span>
        {(q.taxonomy_topic || q.taxonomy_subject) && (
          <span className="rounded-pill bg-practice-soft px-3 py-1 font-mono text-xs font-semibold uppercase tracking-[0.06em] text-practice-dark">
            {questionTopicLabel(q)}
          </span>
        )}
        {q.taxonomy_paths?.filter(p=>!p.is_primary).map(p=><Link key={p.subtopic_id||p.topic_id||p.subject_id} to={'/library/subjects/'+encodeURIComponent(p.subject_id)+(p.topic_id?'?topic_id='+encodeURIComponent(p.topic_id):'')} className="rounded-pill border border-hairline px-2.5 py-1 text-xs font-medium text-link hover:border-practice">{p.subtopic_label||p.topic_label||p.subject_label}</Link>)}
        <span className="font-mono text-xs font-medium text-muted">
          {q.last_year ?? q.first_year ?? '—'}
        </span>

        {!isWritten && <AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.id} outlined />}

        {q.times_asked > 1 && (
          <span
            title={yearLabel}
            className="rounded-pill bg-ink px-3 py-1 font-mono text-xs font-semibold uppercase tracking-[0.06em] text-paper"
          >
            Asked {q.times_asked}× · {yearLabel}
          </span>
        )}

        <span className="ml-auto inline-flex items-center gap-2">
          <SaveToVaultButton question={q} compact />
          <Link
            to={scopeLink(`/bank/${q.id}`)}
            className="inline-flex min-h-10 items-center rounded-pill px-2.5 font-mono text-xs font-semibold text-secondary hover:text-link hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-link"
          >
            Open →
          </Link>
        </span>
      </div>

      <div className="q-stem max-w-[70ch] my-4 font-reading text-[20px] leading-[1.48] text-ink sm:text-[21px] [text-wrap:pretty]">
        <SourceQuestionContext direction={q.direction} passage={q.passage} />
        <SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup ?? q.question} />
      </div>

      {q.figure_image_url && <a href={q.figure_image_url} target="_blank" rel="noreferrer" className="mb-3 block max-w-2xl overflow-hidden rounded-[9px] border border-hairline bg-paper" aria-label="Open original question figure"><img src={q.figure_image_url} loading="lazy" decoding="async" alt="Original scanned figure or chart for this question" className="max-h-[360px] w-full object-contain" /><span className="block border-t border-hairline px-3 py-2 font-mono text-xs uppercase tracking-wide text-muted">Original source figure · open full image ↗</span></a>}

      {q.key_disputed && <p className="mb-3 rounded-[8px] border border-wrong bg-wrong-soft px-3 py-2 text-xs leading-relaxed text-wrong-dark">Answer disputed.{q.dispute_note ? ` ${q.dispute_note}` : ''}</p>}

      {sourceNote && <p className="mb-3 rounded-[8px] border border-exams bg-exams-soft px-3 py-2 text-xs leading-relaxed text-exams-dark">{sourceNote}</p>}


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
                const trusted=answerStatus(result.answer_source,{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}).trusted
                mark = trusted?(isPick?'Correct':'Answer'):'Suggested answer'
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
                onClick={() => void pick(i)}
                disabled={text === null || !answerable || !!result || busy || viewed}
                aria-pressed={isPick}
                data-answer-state={isCorrect?'correct':result&&isPick?'wrong':isPick?'selected':'neutral'}
                className={`answer-option q-opt-btn flex min-h-[50px] items-center gap-3.5 rounded-[13px] border px-4 py-3 text-left text-[15.5px] leading-snug ${cls} ${
                  result || !answerable || text === null ? 'cursor-default opacity-80' : 'cursor-pointer'
                }`}
              >
                <span className="q-opt-letter grid h-7 w-7 shrink-0 place-items-center rounded-lg font-mono text-xs font-bold">{LETTERS[i]}</span>
                <span className="flex-1">{text === null ? 'Option text unavailable' : <SourceQuestionText text={q.options_markup?.[i] ?? text} />}</span>
                {/* The prototype marks state with a WORD, not a symbol. */}
                {mark && <span className="q-opt-mark shrink-0 rounded-pill px-2.5 py-0.5 font-mono text-xs font-bold">{mark}</span>}
              </button>
            )
          })}
        </AnswerOptions>
      )}

      {answerError && <p role="alert" className="mt-3 text-sm text-mypick">{answerError}</p>}
      {!answerable && q.options.length > 0 && (
        <p className="mt-3 text-sm text-muted">This question is held for review or has no usable answer yet. Browse its source, compare the evidence or suggest a correction.</p>
      )}

      {q.type==='mcq'&&<PracticeAnswerPanel secondaryActions={actions} options={q.options} showNext={false} qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={source?.paper_id} year={source?.year ?? q.first_year ?? q.last_year} available={answerable} disabled={busy} onBusy={setBusy} onViewed={setViewed} onRetry={()=>{setPicked(null);setResult(null)}} onNext={onNext}/>}
      {q.type!=='mcq'&&<div className="mt-3 space-y-2">
        <Link to={scopeLink(`/bank/${q.id}`)} className="inline-flex min-h-11 items-center rounded-lg border border-ink px-4 py-2 text-sm font-semibold text-ink hover:bg-canvas">Write a practice answer →</Link>
        {actions}
      </div>}

      <footer className="sq-ref-bar" aria-label="Question source and concept guide">
        <div className="sq-source-block">
          <span className="sq-source-kicker">Source</span>
          <span className="sq-source-text" title={sourceInfo.label}>{sourceInfo.label}</span>
          {sourceInfo.pdfUrl && (
            <a href={sourceInfo.pdfUrl} target="_blank" rel="noreferrer" className="sq-source-pdf">
              PDF ↗
            </a>
          )}
          {q.times_asked > 1 && (
            <Link to={scopeLink(`/bank/${q.id}`)} className="sq-source-repeat">
              All {q.times_asked} appearances ↗
            </Link>
          )}
        </div>
        {guideMatch && (
          <Link to={guideMatch.to} state={{ fromQuestion: true }} className={`sq-guide-pill is-${guideMatch.tone}`}>
            <span className="sq-guide-ico" aria-hidden="true">📖</span>
            <span>{guideMatch.label}</span>
            <span aria-hidden="true">→</span>
          </Link>
        )}
      </footer>
    </article>
  )
}
