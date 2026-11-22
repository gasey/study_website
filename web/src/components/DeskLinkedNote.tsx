import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {deskRead} from '../lib/desk';
import {accountGeneration} from '../lib/accountContext';
type Note={id:string;title:string;body:string;question_id:string|null;author:string};
export default function DeskLinkedNote({deskId,noteId}:{deskId:string;noteId:string}) {
 const [note,setNote]=useState<Note|null>(null),[error,setError]=useState('');
 useEffect(()=>{
  let active=true,sequence=0;const generation=accountGeneration();
  const valid=()=>active&&generation===accountGeneration();
  async function load(){const run=++sequence;try{const n=await deskRead<Note>(`/rooms/${deskId}/notes/${encodeURIComponent(noteId)}`);if(valid()&&run===sequence){setNote(n);setError('')}}catch(e){if(valid()&&run===sequence){setNote(null);setError((e as Error).message)}}}
  const reset=()=>{active=false;++sequence;setNote(null);setError('')};
  setNote(null);setError('');void load();
  const visible=()=>{if(document.visibilityState==='visible')void load()};
  const timer=window.setInterval(visible,10000);window.addEventListener('focus',visible);
  window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-auth-expired',reset);
  return()=>{reset();window.clearInterval(timer);window.removeEventListener('focus',visible);window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-auth-expired',reset)};
 },[deskId,noteId]);
 return <section aria-label="Linked shared note" className="my-4 min-w-0 rounded-panel border border-hairline bg-card p-4 sm:p-5">
  <h2 className="text-lg font-bold">{note?.title || 'Shared note'}</h2>
  {error?<p role="alert" className="mt-3 text-sm text-secondary">{error}</p>:note?<><p className="mt-1 text-xs text-secondary">Shared by {note.author}</p><p className="mt-3 whitespace-pre-wrap break-words">{note.body}</p>{note.question_id&&<Link className="mt-3 block min-h-11 break-all text-sm text-link underline" to={'/bank/'+encodeURIComponent(note.question_id)}>Open linked question</Link>}</>:<p role="status" className="mt-3 text-sm text-secondary">Opening note…</p>}
 </section>;
}
