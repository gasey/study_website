import {useRef, useState} from 'react'
import {Link} from 'react-router-dom'
import {reviewRequest} from '../lib/review'
import {accountContext} from '../lib/accountContext'

export default function QuestionReport({qid, paperId}: {qid:string; paperId?:string|null}) {
  const [open,setOpen]=useState(false),[note,setNote]=useState(''),[kind,setKind]=useState('wrong_key')
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[sent,setSent]=useState(false),[signIn,setSignIn]=useState(false)
  const sending=useRef(false)
  async function send(e:React.FormEvent) {
    e.preventDefault()
    if(sending.current)return
    sending.current=true;setBusy(true);setError('');setSignIn(false)
    try {
      if(!(await accountContext()).authenticated){setSignIn(true);return}
      await reviewRequest('/review/questions/'+encodeURIComponent(qid)+'/report',{kind,note:note.trim(),paper_id:paperId||null})
      setSent(true)
    } catch(e){setError((e as Error).message)}
    finally{sending.current=false;setBusy(false)}
  }
  const input='mt-1 w-full rounded-[6px] border border-hairline bg-card p-3 text-[16px]'
  return <div className={(open?'basis-full ':'')+'text-[12px] text-secondary'}>
    <button type="button" aria-expanded={open} onClick={()=>setOpen(!open)} className="min-h-11 py-2 underline underline-offset-2">Report an issue</button>
    {open&&<div className="mt-1 rounded-[10px] border border-hairline bg-paper p-4">
      {sent?<p role="status">Thank you. Your report has been sent to our review team.</p>:<form onSubmit={e=>void send(e)} className="space-y-3">
        <p className="text-[13px]">Tell us what needs checking. Reports go privately to our review team.</p>
        <label className="block">Issue<select value={kind} onChange={e=>setKind(e.target.value)} className={input}>
          <option value="wrong_key">Answer or explanation</option><option value="typo_ocr">Question text or options</option><option value="outdated">Outdated information</option><option value="ambiguous">Something else</option>
        </select></label>
        <label className="block">What did you notice?<textarea required minLength={20} maxLength={4000} rows={3} value={note} onChange={e=>setNote(e.target.value)} className={input} placeholder="Describe the issue. Include a source if you have one."/></label>
        {error&&<p role="alert" className="text-mypick">{error}</p>}
        {signIn&&<p role="status"><Link to={'/login?next='+encodeURIComponent(window.location.pathname+window.location.search)} className="text-link underline">Sign in to send your report</Link>. Your note stays here while this page is open.</p>}
        <button type="submit" disabled={busy||note.trim().length<20} className="min-h-11 rounded-pill border border-hairline bg-card px-4 font-semibold disabled:opacity-40">{busy?'Sending…':'Send report'}</button>
      </form>}
    </div>}
  </div>
}
