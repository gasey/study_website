import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useIsStaff } from '../hooks/useIsStaff'
import AtlasQuestionLinks from './AtlasQuestionLinks'
import PracticeAnswerPanel from './PracticeAnswerPanel'
import { questionTopicLabel } from '../lib/questionLabels'
import { formatQuestionSource, resolveQuestionGuide } from '../lib/questionGuideLink'
import AnswerProvenance from './AnswerProvenance'
import { scopeLink } from '../lib/examScope'
import { QuestionActions } from './QuestionDiscussion'
import { AnswerOptions } from './AnswerLayout'
import { SourceQuestionContext, SourceQuestionText } from './SourceQuestionText'
import type { Question, AnswerResult } from '../lib/api'

const LETTERS = ['A','B','C','D','E','F','G','H','I','J']

export default function StudyQuestionCard({q,collectionId,paperId='',positionNumber,sourceCollections,contextCollectionId,result,pick,viewed=false,busy=false,checking=false,disabled=false,onPick,onViewed,onBusy,onRetry,onNext,nextLabel,showPanelNext=true}:{
  q:Question;collectionId:string;paperId?:string;positionNumber?:number;sourceCollections?:Record<string,string>;
  /** Source-only guides can use shared cards without claiming membership in a published collection. */
  contextCollectionId?:string|null;
  result?:AnswerResult;pick?:number;viewed?:boolean;busy?:boolean;checking?:boolean;disabled?:boolean;
  onPick:(index:number)=>void;onViewed:(value:boolean)=>void;onBusy:(value:boolean)=>void;
  onRetry:()=>void;onNext:()=>void|Promise<void>;nextLabel?:string;showPanelNext?:boolean;
}) {
  const combined=collectionId==='combined-prelims'
  const isStaff = useIsStaff()
  const isWritten = q.type !== 'mcq'
  const adminFixHref = useMemo(() => {
    const p = new URLSearchParams({ tab: 'retag', tag_q: q.id, tag_issue: 'all', tag_selected: q.id })
    if (q.source_appearance?.paper_id) p.set('tag_paper', q.source_appearance.paper_id)
    return '/admin/bank?' + p.toString()
  }, [q.id, q.source_appearance?.paper_id])
  const blocked=q.held||q.key_disputed||['duplicate-options','unresolved-source'].includes(q.source_defect||'')
  const sourceInfo = useMemo(
    () => formatQuestionSource(q),
    [q.source_appearance, q.first_year, q.last_year],
  )
  const guideMatch = useMemo(
    () => resolveQuestionGuide(q),
    [q.taxonomy_subject_id, q.taxonomy_topic_id, q.taxonomy_subtopic_id, q.subject, q.topic, q.question],
  )
  const actions = <QuestionActions questionType={q.type} qid={q.id} context={{paper_id:q.source_appearance?.paper_id,collection_id:q.source_appearance?.paper_id?(contextCollectionId!==undefined?contextCollectionId:sourceCollections?.[q.source_appearance.paper_id]||(collectionId==='group-b'?null:collectionId)):null}} answeredSignal={result}/>
  return <article id={'question-'+q.id} key={q.id} data-question-type={isWritten ? 'written' : 'mcq'} className={`${combined?'cp-question':'udc-question-card'} compact-question sq-card${isWritten ? ' sq-card--written' : ' sq-card--mcq'}`}>
          <div className="sq-meta">{positionNumber!=null&&<span className="sq-meta-pos">#{positionNumber.toLocaleString('en-IN')}</span>}<span className={isWritten ? 'sq-kind-badge is-written' : 'sq-kind-badge is-mcq'}>{isWritten ? '✎ Written' : '◉ MCQ'}</span>{paperId&&q.source_appearance?.paper_id===paperId&&q.source_appearance.qnum&&<span className="sq-meta-qnum">Q{q.source_appearance.qnum}</span>}<span className="sq-meta-year">{q.source_appearance?.year ?? q.first_year ?? q.last_year ?? 'Year unknown'}</span><span className="sq-meta-topic">{questionTopicLabel(q,collectionId)}</span>{!isWritten && <AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.id}/>}</div>
          <AtlasQuestionLinks qid={q.id} context={q.type==='mcq'&&['official','verified'].includes(q.answer_status||'')}/>
          <SourceQuestionContext direction={q.direction} passage={q.passage}/><h3 className="sq-stem"><SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup||q.question}/></h3>
          {blocked&&<p className="mt-3 rounded-[10px] bg-mypick-soft p-3 text-sm text-mypick">Under review. See answer details below.</p>}
          {q.figure_image_url&&<img src={q.figure_image_url} loading="lazy" alt="Printed question figure" className="mt-3 max-h-[360px] max-w-full rounded-[10px] border border-hairline object-contain"/>}
          {!!q.options.length && <AnswerOptions className="mt-3.5">{q.options.map((option,i)=>{
            const correct=result?.answer_index===i
            const wrong=!!result && pick===i && !result.correct
            return <button key={i} type="button" disabled={disabled || busy || !!result || viewed || option==null || blocked || q.answer_source==='none'} onClick={()=>onPick(i)} aria-pressed={pick===i} data-answer-state={correct?'correct':wrong?'wrong':pick===i?'selected':'neutral'} className={`answer-option ${combined?'cp-option':'udc-option-label'} sq-option flex min-h-12 items-start gap-2.5 rounded-[12px] border px-3.5 py-2.5 text-left disabled:cursor-default ${correct?'is-right border-correct bg-correct-soft':wrong?'is-wrong border-wrong bg-wrong-soft':pick===i?'is-chosen border-ink bg-paper':'border-hairline bg-card'}`}><span className={`${combined?'cp-option-letter':'font-mono'} sq-opt-letter`}>{LETTERS[i]}</span><span className="sq-opt-text"><SourceQuestionText text={q.options_markup?.[i]||option||'Option unavailable'}/></span></button>
          })}</AnswerOptions>}
          {checking&&<p role="status" aria-live="polite" aria-atomic="true" className="mt-2 text-xs font-medium text-secondary">Checking your answer…</p>}
          {!isWritten && q.answer_source==='none'&&<p className="mt-3 text-xs text-muted">Answer not available yet.</p>}
          {!isWritten && <PracticeAnswerPanel secondaryActions={actions} options={q.options} qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={paperId||q.source_appearance?.paper_id} year={q.source_appearance?.year ?? q.first_year ?? q.last_year} available={!blocked&&q.answer_source!=='none'} disabled={disabled||busy} onBusy={onBusy} onViewed={onViewed} onRetry={onRetry} onNext={onNext} nextLabel={nextLabel} showNext={showPanelNext}/>}
          {isWritten && <div className="sq-written-box">
            <div className="sq-written-copy">
              <strong>Descriptive / written prompt</strong>
              <span>Draft your answer on paper or open the writing workspace to save notes &amp; compare structure.</span>
            </div>
            <Link to={scopeLink(`/bank/${q.id}`)} className="sq-written-cta">Write answer →</Link>
          </div>}
          {isWritten && actions}
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
                  {q.times_asked}× papers ↗
                </Link>
              )}
              {isStaff && (
                <Link
                  to={adminFixHref}
                  target="_blank"
                  rel="noreferrer"
                  title="Open this exact question in Admin Cross-Check & Fix"
                  className="sq-source-pdf"
                >
                  ✎ Fix ↗
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
}
