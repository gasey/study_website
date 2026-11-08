import PracticeAnswerPanel from './PracticeAnswerPanel'
import { questionTopicLabel } from '../lib/questionLabels'
import AnswerProvenance from './AnswerProvenance'
import { QuestionActions } from './QuestionDiscussion'
import { AnswerOptions } from './AnswerLayout'
import { SourceQuestionContext, SourceQuestionText } from './SourceQuestionText'
import type { Question, AnswerResult } from '../lib/api'

const LETTERS = ['A','B','C','D','E','F','G','H','I','J']

export default function StudyQuestionCard({q,collectionId,paperId='',sourceCollections,result,pick,viewed=false,busy=false,disabled=false,onPick,onViewed,onBusy,onRetry,onNext,nextLabel,showPanelNext=true}:{
  q:Question;collectionId:string;paperId?:string;sourceCollections?:Record<string,string>;
  result?:AnswerResult;pick?:number;viewed?:boolean;busy?:boolean;disabled?:boolean;
  onPick:(index:number)=>void;onViewed:(value:boolean)=>void;onBusy:(value:boolean)=>void;
  onRetry:()=>void;onNext:()=>void|Promise<void>;nextLabel?:string;showPanelNext?:boolean;
}) {
  const combined=collectionId==='combined-prelims'
  const blocked=q.held||q.key_disputed||['duplicate-options','unresolved-source'].includes(q.source_defect||'')
  const sourceDetails=q.source_appearance&&<p className="mt-2 text-[12px] text-secondary">{q.source_appearance.exam||'Source paper'}{q.source_appearance.paper_label ? ' · '+q.source_appearance.paper_label : ''}{q.source_appearance.section_label ? ' · Section: '+q.source_appearance.section_label : ''} · Q{q.source_appearance.qnum||'?'}{q.source_appearance.page?' · p. '+q.source_appearance.page:''} {q.source_appearance.source_pdf_url&&<a href={q.source_appearance.source_pdf_url+(q.source_appearance.page?'#page='+q.source_appearance.page:'')} target="_blank" rel="noreferrer" className="text-link underline">Source PDF ↗</a>}</p>
  const actions = <QuestionActions sourceDetails={sourceDetails} questionType={q.type} qid={q.id} context={{paper_id:q.source_appearance?.paper_id,collection_id:q.source_appearance?.paper_id?(sourceCollections?.[q.source_appearance.paper_id]||(collectionId==='group-b'?null:collectionId)):null}} answeredSignal={result}/>
  return <article id={'question-'+q.id} key={q.id} className={`${combined?'cp-question':'udc-question-card'} compact-question py-3`}>
          <div className="flex flex-wrap gap-x-3 text-[11px] text-muted"><span>{q.source_appearance?.year ?? q.first_year ?? q.last_year ?? 'Year unknown'}</span><span>{q.type==='mcq'?'MCQ':'Written question'}</span><span>{questionTopicLabel(q,collectionId)}</span><AnswerProvenance source={q.answer_source} reviewed={q.reviewed_derived} disputed={q.key_disputed} defect={q.source_defect} questionType={q.type} statusOverride={q.answer_status} questionId={q.id}/></div>
          <SourceQuestionContext direction={q.direction} passage={q.passage}/><h3 className="mt-1 font-display text-[19px] leading-snug"><SourceQuestionText formatEnumerations instruction={[q.direction,q.question].filter(Boolean).join(' ')} text={q.question_markup||q.question}/></h3>
          {blocked&&<p className="mt-3 rounded-[8px] bg-mypick-soft p-3 text-[13px] text-mypick">Excluded from scoring. See answer details below.</p>}
          {q.figure_image_url&&<img src={q.figure_image_url} loading="lazy" alt="Printed question figure" className="mt-3 max-h-[360px] max-w-full rounded-[8px] border border-hairline object-contain"/>}
          {!!q.options.length && <AnswerOptions className="mt-3">{q.options.map((option,i)=>{
            const correct=result?.answer_index===i
            const wrong=!!result && pick===i && !result.correct
            return <button key={i} type="button" disabled={disabled || busy || !!result || viewed || option==null || blocked || q.answer_source==='none'} onClick={()=>onPick(i)} aria-pressed={pick===i} data-answer-state={correct?'correct':wrong?'wrong':pick===i?'selected':'neutral'} className={`answer-option ${combined?'cp-option':'udc-option-label'} flex min-h-11 gap-2 rounded-[8px] border p-3 text-left text-[13px] disabled:cursor-default ${correct?'is-right border-correct bg-correct-soft':wrong?'is-wrong border-wrong bg-wrong-soft':pick===i?'is-chosen border-ink bg-paper':'border-hairline bg-card'}`}><span className={`${combined?'cp-option-letter':'font-mono'}`}>{LETTERS[i]}.</span><span><SourceQuestionText text={q.options_markup?.[i]||option||'Option unavailable'}/></span></button>
          })}</AnswerOptions>}
          {q.answer_source==='none'&&<p className="mt-3 text-[12px] text-muted">Answer not available yet.</p>}
          {q.type==='mcq'&&<PracticeAnswerPanel secondaryActions={actions} options={q.options} qid={q.id} question={q.question} context={{reviewed:q.reviewed_derived,disputed:q.key_disputed,defect:q.source_defect,statusOverride:q.answer_status}} result={result} topic={[q.taxonomy_subject,q.taxonomy_topic].filter(Boolean).join(" / ")} paperId={paperId||q.source_appearance?.paper_id} year={q.source_appearance?.year ?? q.first_year ?? q.last_year} available={!blocked&&q.answer_source!=='none'} disabled={disabled||busy} onBusy={onBusy} onViewed={onViewed} onRetry={onRetry} onNext={onNext} nextLabel={nextLabel} showNext={showPanelNext}/>}
          {q.type!=='mcq'&&actions}
        </article>
}
