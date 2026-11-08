import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewSession,reviewRequest} from '../lib/review'
export default function ReviewModuleLink({collection}:{collection:string}){
 const [allowed,setAllowed]=useState(false)
 useEffect(()=>{let live=true;let generation=0;function update(){const version=++generation;setAllowed(false);reviewSession(true).then(async s=>{const assigned=s.grants.length?false:(await reviewRequest<{items:{state:string}[]}>('/editorial/assignments')).items.some(a=>a.state==='active');if(live&&version===generation)setAllowed(s.grants.length>0||assigned)}).catch(()=>{})}update();window.addEventListener('ism-auth-change',update);return()=>{live=false;generation++;window.removeEventListener('ism-auth-change',update)}},[])
 return allowed?<Link to={'/editorial?'+new URLSearchParams({scope:'module:'+collection})} className="inline-flex min-h-11 items-center rounded-pill border border-hairline bg-card px-4 text-[13px] font-semibold text-link">Review this module →</Link>:null
}
