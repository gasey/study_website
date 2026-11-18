import {Link} from 'react-router-dom'
import type {CuratedWordCard} from '../lib/materials'
import type {CuratedResult} from '../lib/vocabulary'
import VocabularyCardRead from './VocabularyCardRead'
export const wordModeLabel:Record<string,string>={recognition:'Meaning',cloze:'Usage cloze','mizo-to-english':'Mizo → English','english-to-mizo':'English → Mizo'}
type Feedback={correct:boolean|null;answer_text?:string|null;answer_index?:number|null;card?:CuratedWordCard|null;next_due?:string|null;graduated?:boolean;outcome?:string}
export default function CuratedWordQuestion({prompt,options,meta,result,pick,disabled,onPick,onReveal}:{prompt:string;options:(string|null)[];meta:{deck_id:string;deck_title:string;mode?:string;source_changed?:boolean;revealed_result?:CuratedResult|null;practice_enabled?:boolean};result?:Feedback|null;pick?:number|null;disabled?:boolean;onPick:(index:number)=>void;onReveal:()=>void}){
 const feedback=result||meta.revealed_result,locked=disabled||!!feedback||meta.source_changed||meta.practice_enabled===false
 return <article aria-label="Reviewed word practice" className="mt-5 min-w-0 rounded-panel border border-hairline bg-card p-5">
  <p className="text-xs text-secondary">Reviewed editorial card · {wordModeLabel[meta.mode||'recognition']||'Word practice'}</p>
  <p className="mt-2 break-words text-sm text-muted">{meta.deck_title}</p>
  {meta.practice_enabled===false&&<p role="status" className="mt-3 text-sm text-secondary">Word-card practice is temporarily paused. Saved grades and bank reviews remain available.</p>}
  {meta.source_changed&&<p role="alert" className="mt-3 text-sm text-secondary">The reviewed card has changed. This saved prompt keeps its earlier content; skip it and use a fresh review for the current version.</p>}
  <h3 className="mt-4 whitespace-pre-wrap break-words font-display text-2xl leading-snug">{prompt}</h3>
  <div role="group" aria-label="Word choices" className="mt-5 grid gap-3 sm:grid-cols-2">{options.map((value,i)=><button key={i} disabled={locked} aria-pressed={pick===i} onClick={()=>onPick(i)} className={'min-h-11 min-w-0 whitespace-pre-wrap break-words rounded-xl border p-3 text-left text-sm leading-relaxed disabled:cursor-default '+(feedback?.answer_index===i?'border-green-700 bg-correct-soft':feedback&&pick===i&&!feedback.correct?'border-hairline bg-mypick-soft':'border-hairline bg-paper')}>{String.fromCharCode(65+i)}. {value}</button>)}</div>
  {!feedback&&<button disabled={disabled||meta.source_changed||meta.practice_enabled===false} onClick={onReveal} className="mt-4 min-h-11 rounded-pill border border-hairline px-4 text-sm font-semibold">Show word-card answer</button>}
  {feedback&&<div role="status" className="mt-5 rounded-xl border border-hairline bg-paper p-4 text-sm"><strong>{feedback.correct===true?'Correct.':feedback.correct===false?'Not quite.':feedback.outcome==='defer'?'Skipped for now.':'Answer shown.'}</strong>{feedback.answer_text&&<p className="mt-2 whitespace-pre-wrap break-words">Answer: {feedback.answer_text}</p>}{feedback.graduated?<p className="mt-2">Graduated from the shared review queue.</p>:feedback.next_due?<p className="mt-2">Next review: {new Date(feedback.next_due).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',dateStyle:'medium',timeStyle:'short'})} IST</p>:null}</div>}
  {feedback?.card&&<div className="mt-4"><VocabularyCardRead card={feedback.card}/></div>}
  <Link to={'/materials/'+encodeURIComponent(meta.deck_id)} className="mt-4 inline-flex min-h-11 items-center text-sm font-bold text-link underline">Read the reviewed deck →</Link>
 </article>
}
