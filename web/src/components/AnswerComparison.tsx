import {useEffect, useRef, useState} from 'react'
import {Link} from 'react-router-dom'
import {getAnswerComparison, type AnswerComparisonData, type ComparedAnswer} from '../lib/api'
import {SourceQuestionText} from './SourceQuestionText'
import {evidenceLink} from './AnswerProvenance'

function Lane({label, answer, official}: {label:string; answer:ComparedAnswer|null; official?:boolean}) {
  return <section className={'min-w-0 rounded-[10px] border p-4 '+(official?'border-[#8CB89A] bg-[#E7F3EA] text-[#214E34]':'border-[#8DAED7] bg-[#EAF1FC] text-[#204F86]')}>
    <h4 className="text-[13px] font-bold">{official?'▣':'✓'} {label}</h4>
    {answer?<><p className="mt-2 text-[15px] font-semibold">{String.fromCharCode(65+answer.answer_index)}. {answer.answer_text}</p>
      {answer.explanation&&<div className="mt-2 whitespace-pre-wrap break-words text-[13px] leading-relaxed"><SourceQuestionText text={answer.explanation}/></div>}
      {answer.document&&<p className="mt-3 text-[11px]">Source: {answer.document.title} · {answer.document.key_status||'version not recorded'} · PDF page {answer.document.page}</p>}
      {answer.imported&&<p className="mt-2 text-[12px]">Imported official-key label. An exact registered key citation has not yet been matched here.</p>}
    </>:<p className="mt-2 text-[13px] leading-relaxed">{official?'No mapped official key is available for this source.':'No separate, source-matched reviewed solution has been published. The official answer is not counted as independent verification.'}</p>}
  </section>
}

export default function AnswerComparison({qid,paperId}: {qid:string;paperId?:string|null}) {
  const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('')
  const [data,setData]=useState<AnswerComparisonData|null>(null)
  const request=useRef<AbortController|null>(null)
  useEffect(()=>{setOpen(false);setData(null);setError('');setBusy(false);return()=>request.current?.abort()},[qid,paperId])
  async function reveal(){
    if(open){request.current?.abort();setOpen(false);setBusy(false);return}
    request.current?.abort();const controller=new AbortController();request.current=controller
    setOpen(true);setBusy(true);setData(null);setError('')
    try{const value=await getAnswerComparison(qid,paperId,controller.signal);if(!controller.signal.aborted)setData(value)}
    catch(e){if(!controller.signal.aborted)setError((e as Error).message)}
    finally{if(!controller.signal.aborted)setBusy(false)}
  }
  return <div className="mt-3">
    <button type="button" aria-expanded={open} title="Reveals answer evidence; unavailable during an active test" onClick={()=>void reveal()} className="min-h-11 rounded-pill border border-hairline px-3 py-2 text-[12px] font-semibold text-link">{open?'Hide answer comparison':'Compare key & solution · reveals answers'}</button>
    {open&&<section aria-label="Official key and reviewed solution comparison" className="mt-3 rounded-[12px] border border-hairline bg-paper p-3 sm:p-4">
      <h3 className="font-display text-[22px] text-ink">Key & solution</h3>
      {busy&&<p role="status" className="mt-2 text-[13px] text-secondary">Loading answer evidence…</p>}
      {error&&<p role="alert" className="mt-2 text-[13px] text-mypick">{error} Close and reopen to retry.</p>}
      {data&&<><p className="mt-2 text-[12px] leading-relaxed text-secondary">{data.notice}</p>
        <p className={'mt-3 rounded-[8px] border p-3 text-[13px] font-semibold '+(data.held||data.relation==='disagree'?'border-[#D9B76B] bg-[#FFF4D9] text-[#705015]':'border-hairline bg-card text-ink')}>
          {data.held?'Needs review · excluded from scored tests.':data.relation==='disagree'?'Answers differ · compare the evidence before relying on either.':data.relation==='agree'?'The official key and published reviewed solution agree.':'Independent comparison is not complete.'}
        </p>
        <div className="mt-3 grid gap-3 md:grid-cols-2"><Lane label="Official key · examiner selection" answer={data.official} official/><Lane label="Reviewed solution · unofficial" answer={data.solution}/></div>
        {data.review_note&&<p className="mt-3 whitespace-pre-wrap text-[13px] leading-relaxed text-secondary">Review note: {data.review_note}</p>}
        <Link to={evidenceLink(qid)} className="mt-3 inline-flex min-h-11 items-center text-[13px] font-semibold text-link underline">Challenge the key or submit a worked solution →</Link>
      </>}
    </section>}
  </div>
}
