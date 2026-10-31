import {useEffect,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {reviewSession} from '../lib/review'
import {learningRequest} from '../lib/learning'
interface Update{question_id:string;changed_fields:string[];created_at:string;message:string;mocks:{id:string;title:string}[]}
export default function QuestionUpdate({questionId}:{questionId:string}){
 const [params]=useSearchParams(),id=params.get('update'),[data,setData]=useState<Update|null>(null),[error,setError]=useState('')
 useEffect(()=>{let live=true;setData(null);setError('');if(!id||!/^\d+$/.test(id))return;reviewSession().then(s=>learningRequest<Update>('/changes/'+id,s.user_id)).then(r=>{if(live&&r.question_id===questionId)setData(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[id,questionId])
 if(!id)return null
 return <aside aria-label="Question correction update" className="mt-4 rounded-panel border border-attention bg-attention-soft p-4 text-[13px]">{error?<p role="alert">{error}</p>:data?<><h2 className="font-semibold">Question updated</h2><p className="mt-2">{data.changed_fields.join(' · ')} · {new Date(data.created_at).toLocaleString('en-IN')}</p><p className="mt-2">{data.message}</p>{data.mocks.map(m=><Link key={m.id} to={'/results/'+m.id} className="mt-2 inline-flex min-h-11 items-center pr-4 text-link underline">{m.title}: original & adjusted result →</Link>)}</>:<p>Loading your update…</p>}</aside>
}
