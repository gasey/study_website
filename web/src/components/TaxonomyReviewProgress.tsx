import {useEffect,useState} from 'react'
import {reviewRequest} from '../lib/review'

type Progress={total:number;published:number;confirmed:number;blocked:number;stale:number;remaining:number;updated_at:string|null}

export default function TaxonomyReviewProgress({refresh}:{refresh:number}){
 const [data,setData]=useState<Progress|null>(null)
 useEffect(()=>{let live=true;reviewRequest<Progress>('/admin/bank/retag/progress').then(p=>{if(live)setData(p)}).catch(()=>{if(live)setData(null)});return()=>{live=false}},[refresh])
 if(!data?.updated_at)return null
 return <section aria-label="Tagging review progress" className="mt-4 rounded-xl border border-hairline bg-card p-4">
  <h3 className="text-[15px] font-semibold">Tagging review progress</h3>
  <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">{[['Published corrections',data.published],['Reviewed · unchanged',data.confirmed],['Blocked',data.blocked],['Remaining',data.remaining]].map(([label,count])=><div key={label}><dt className="text-[12px] text-secondary">{label}</dt><dd className="mt-1 font-mono text-[20px]">{Number(count).toLocaleString()}</dd></div>)}</dl>
  <p className="mt-3 text-[12px] text-secondary">Owner accepted AI tagging reviews. Remaining includes blocked{data.stale?' and '+data.stale.toLocaleString()+' changed since review':''} questions. Answer, explanation and source checks are tracked separately.</p>
 </section>
}
