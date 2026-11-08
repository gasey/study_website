import {linkRegisteredPaper,type PaperPayload,type RegisteredPaperSource} from '../lib/paperWorkbench'

export default function PaperSourceTarget({payload,sources,editable,published=false,onChange}:{payload:PaperPayload;sources:RegisteredPaperSource[];editable:boolean;published?:boolean;onChange:(payload:PaperPayload)=>void}){
 if(!sources.length&&!payload.target_paper_id)return null
 const linked=sources.find(source=>source.paper_id===payload.target_paper_id)
 const stale=!!payload.target_paper_id&&(!linked||linked.source_version!==payload.target_source_version||!published&&linked.question_count>0)
 return <section aria-label="Existing original paper" className="mt-4 rounded-[14px] border border-hairline bg-paper p-4">
  <h2 className="text-[14px] font-semibold">Existing original paper</h2>
  <p className="mt-2 text-[13px] leading-relaxed text-secondary">This PDF is already registered. Link its empty original to publish reviewed questions under the same paper identity. Existing paper details and source registration are preserved.</p>
  {stale&&<p role="alert" className="mt-2 text-[13px] text-mypick">{published?'The original registration changed after publication. This saved review link records the earlier source identity.':'The linked original changed or now has questions. Refresh its link and review again; publication will stop until this is resolved.'}</p>}
  {sources.map(source=><div key={source.paper_id} className="mt-3 border-t border-hairline pt-3 text-[13px]">
   <p className="font-semibold">{source.exam_name||'Exam name not registered'} · {source.year||'Year not registered'}{source.paper_subject?' · '+source.paper_subject:''}</p>
   <p className="mt-1 break-words text-[12px] text-secondary">{source.paper_id}</p>
   <p className="mt-1 text-[12px] text-secondary">{source.question_count?`${source.question_count} existing questions · use their correction workflow`:!source.unambiguous?'This PDF matches multiple original identities; resolve the registration first.':'No extracted questions yet.'}</p>
   {payload.target_paper_id===source.paper_id&&!stale?<p className="mt-2 font-semibold">{published?'Published into this original · source identity preserved':'Linked to this original · owner decision or independent review required'}</p>:editable&&<button type="button" disabled={!!source.question_count||!source.unambiguous||!source.exam_name||!source.year} onClick={()=>onChange(linkRegisteredPaper(payload,source))} className="mt-2 min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold disabled:opacity-40">{payload.target_paper_id===source.paper_id?'Refresh original link':'Use this empty original'}</button>}
  </div>)}
  {payload.target_paper_id&&editable&&<button type="button" onClick={()=>onChange({...payload,target_paper_id:null,target_source_version:null})} className="mt-2 min-h-11 text-[12px] font-semibold text-link underline">Remove original link</button>}
  <p className="mt-2 text-[12px] text-secondary">{published?'The original paper details and registration were retained. Existing questions use their correction workflow.':'Save after linking. Changing the link invalidates an earlier approval. A registered paper with questions cannot receive another whole-paper import.'}</p>
 </section>
}
