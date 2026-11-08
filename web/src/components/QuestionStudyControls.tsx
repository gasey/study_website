import {studyStatusOptions,type StudyStatus,type QuestionOrder} from '../lib/questionBrowse'
const select='min-h-11 min-w-0 rounded-lg border border-hairline bg-card px-3 text-[13px]'
export default function QuestionStudyControls({status,order,disabled=false,onStatus,onOrder,onShuffle}:{status:StudyStatus;order:QuestionOrder;disabled?:boolean;onStatus:(v:StudyStatus)=>void;onOrder:(v:QuestionOrder)=>void;onShuffle:()=>void}){
 return <div className="my-3">
  <div className="flex flex-wrap items-center gap-2">
   <select aria-label="My questions" className={select} value={status} disabled={disabled} onChange={e=>onStatus(e.target.value as StudyStatus)}>{studyStatusOptions.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select>
   <select aria-label="Question order" className={select} value={order} disabled={disabled} onChange={e=>onOrder(e.target.value as QuestionOrder)}><option value="mixed">Mixed order</option><option value="repeated">Most repeated first</option></select>
   {order==='mixed'&&<button type="button" disabled={disabled} className="min-h-11 px-2 text-[13px] font-semibold text-link disabled:opacity-40" onClick={onShuffle}>Shuffle again</button>}
  </div>
  {status==='ever_wrong'&&<p className="mt-1 text-[12px] text-secondary">Includes questions you later answered correctly.</p>}
 </div>
}
