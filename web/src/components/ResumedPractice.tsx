import {Link,useLocation,useSearchParams} from 'react-router-dom'
import {DeskQuestion} from './DeskPractice'
export default function ResumedPractice(){
 const [params]=useSearchParams(),location=useLocation(),id=params.get('resume_question')||''
 const clean=new URLSearchParams(params);clean.delete('resume_question')
 if(!/^[a-zA-Z0-9_-]{1,100}$/.test(id))return null
 return <section aria-label="Resumed practice question" className="mx-auto max-w-[900px] px-6 pt-6"><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><h2 className="font-display text-[26px]">Continue your saved question</h2><Link to={location.pathname+(clean.size?'?'+clean:'')} replace className="inline-flex min-h-11 items-center text-[13px] text-link underline">Return to the module ↓</Link></div><p className="mb-3 text-[13px] text-secondary">Your module and filters remain below. This opens the current bank question; previously recorded answers remain in your history.</p><DeskQuestion key={id} qid={id}/></section>
}
