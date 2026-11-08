import {learnerExplanation} from '../lib/answerStatus'
import {useEffect, useState, type ReactNode} from 'react'
import {getAnswerComparison, type AnswerComparisonData, type ComparedAnswer, type AnswerResult} from '../lib/api'
import {SourceQuestionText} from './SourceQuestionText'

function AnswerEvidence({label,answer,explanation,options}: {label:string;answer:ComparedAnswer|null;explanation?:string|null;options?:readonly (string|null)[]}) {
  if(!answer)return null
  return <section className="min-w-0">
    <h4 className="font-semibold text-ink">{label} · {optionLabel(answer,options)}</h4>
    <div className="mt-1 break-words"><SourceQuestionText text={answer.answer_text}/></div>
    {answer.explanation&&learnerExplanation(answer.explanation)!==learnerExplanation(explanation)&&<div className="mt-2 whitespace-pre-wrap break-words"><SourceQuestionText text={learnerExplanation(answer.explanation)}/></div>}
    {answer.document&&<p className="mt-2 text-[12px]">{answer.document.title} · {answer.document.key_status||'Key'} · p. {answer.document.page}</p>}
    {answer.imported&&<p className="mt-2 text-[12px]">Transcribed from the official key; the key document is not linked here yet.</p>}
  </section>
}

function optionLabel(answer:Pick<ComparedAnswer,'answer_index'|'answer_text'>, options?:readonly (string|null)[]) {
  if(!options)return String.fromCharCode(65+answer.answer_index)
  const matches=options.flatMap((text,index)=>text===answer.answer_text?[index]:[])
  return matches.length===1?String.fromCharCode(65+matches[0]):answer.answer_text
}

type Props={answer?:Pick<AnswerResult,'answer_text'|'answer_source'|'answer_index'>;answerReviewed?:boolean;qid:string;paperId?:string|null;revealed?:boolean;options?:readonly (string|null)[];children?:ReactNode;explanation?:string|null;actions?:ReactNode;tools?:ReactNode}
export default function AnswerComparison(props:Props) {
  return <Comparison key={props.qid+':'+(props.paperId||'')} {...props}/>
}
function Comparison({qid,paperId,revealed=false,options,children,explanation,actions,tools,answer,answerReviewed=false}:Props) {
  const [open,setOpen]=useState(revealed),[busy,setBusy]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0)
  const [data,setData]=useState<AnswerComparisonData|null>(null)
  useEffect(()=>{if(revealed)setOpen(true)},[revealed])
  useEffect(()=>{
    if(!open)return
    const controller=new AbortController()
    setBusy(true);setError('');setData(null)
    getAnswerComparison(qid,paperId,controller.signal,revealed).then(value=>{if(!controller.signal.aborted)setData(value)})
      .catch(e=>{if(!controller.signal.aborted)setError((e as Error).message)})
      .finally(()=>{if(!controller.signal.aborted)setBusy(false)})
    return()=>controller.abort()
  },[qid,paperId,open,retry,revealed])
  const official=data?.official
  const candidate=answer&&['derived','inferred'].includes(answer.answer_source)&&(!options||options.filter(option=>option===answer.answer_text).length===1)?answer:null
  const reviewedConflict=!!(official&&data?.solution&&official.answer_text!==data.solution.answer_text)
  const candidateConflict=!!(official&&candidate&&official.answer_text!==candidate.answer_text)
  const alternative=reviewedConflict?data!.solution:candidateConflict?candidate:data?.solution||candidate
  const reviewed=!!(alternative&&alternative===data?.solution)||!!(alternative&&alternative===candidate&&answerReviewed&&candidate?.answer_source==='derived')
  const conflict=!!(official&&alternative&&official.answer_text!==alternative.answer_text)
  const alternativeLabel=reviewed?'Verified answer':'Suggested answer'
  const choice=(value:Pick<ComparedAnswer,'answer_index'|'answer_text'>)=>{
    const label=optionLabel(value,options)
    return label===value.answer_text?value.answer_text:label+' · '+value.answer_text
  }
  return <div className="mt-1">
    {!revealed&&<button type="button" aria-expanded={open} onClick={()=>setOpen(!open)} className="min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold text-link">{open?'Hide answer sources':'View answer sources'}</button>}
    {open&&<section aria-label="Answer sources" className="text-[13px]">
      {busy&&<p role="status" className="text-secondary">Loading answer comparison…</p>}
      {error&&<p role="alert" className="text-secondary">{error} <button type="button" onClick={()=>setRetry(n=>n+1)} className="min-h-11 text-link underline">Retry</button></p>}
      {conflict&&official&&alternative&&<aside aria-label="Answer conflict" className="mt-2 rounded-[8px] border border-[#D9B76B] bg-[#FFF4D9] p-3 text-[13px] text-[#705015]">
        <p className="font-semibold">{reviewed?'Answer conflict':'Answer under review'}</p>
        <dl className="mt-2 space-y-1">
          <div className="flex flex-wrap gap-x-1"><dt className="font-semibold">Official key:</dt><dd className="break-words"><SourceQuestionText text={choice(official)}/></dd></div>
          <div className="flex flex-wrap gap-x-1"><dt className="font-semibold">{alternativeLabel}:</dt><dd className="break-words"><SourceQuestionText text={choice(alternative)}/></dd></div>
        </dl>
        <p className="mt-2 text-[12px]">{data?.held?'Excluded from scored tests pending review.':!reviewed?'The suggested answer is awaiting verification.':'The official key is preserved. See the explanation and source details.'}</p>
      </aside>}
      {data?.held&&!conflict&&<p role="note" className="mt-1 text-[12px] text-secondary">Excluded from scored tests pending review.</p>}
      {data?.official?.document?.key_status==='provisional'&&<p className="mt-1 text-[12px] text-secondary">Provisional official key · final key awaited.</p>}
      {children}
      <div className="flex flex-wrap items-start gap-x-4">
      {actions}
      {(data||tools)&&<details className="min-w-0 open:basis-full">
        <summary className="min-h-11 cursor-pointer py-3 font-semibold text-link">Sources & study tools</summary>
        <div className="space-y-3 border-t border-hairline py-3 text-secondary">
          {data&&<>
            {data.relation==='agree'&&data.official&&data.solution&&<p>Official key and verified answer agree.</p>}

            <AnswerEvidence label="Verified answer" answer={data.solution} explanation={explanation} options={options}/>
            <AnswerEvidence label="Official answer key" answer={data.official} explanation={explanation} options={options}/>
            {data.review_note&&<p className="whitespace-pre-wrap">{data.review_note}</p>}
          </>}
          {tools}
        </div>
      </details>}
      </div>
    </section>}
  </div>
}
