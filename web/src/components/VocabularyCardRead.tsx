import type {CuratedWordCard} from '../lib/materials'
export default function VocabularyCardRead({card}:{card:CuratedWordCard}){
 return <section aria-label="Editorial vocabulary card" className="rounded-xl border border-hairline bg-paper p-4 sm:p-5">
  <p className="text-xs text-muted">Editorial vocabulary · {card.language==='mizo-english'?'Mizo–English pair':'English'}</p>
  <h3 className="mt-2 whitespace-pre-wrap font-display text-2xl">{card.word||'Word not entered'}</h3>
  <p className="mt-3 whitespace-pre-wrap text-base text-secondary">{card.meaning||'Meaning not entered'}</p>
  {card.mizo_gloss&&<p className="mt-3 whitespace-pre-wrap text-sm"><strong>Mizo:</strong> {card.mizo_gloss}</p>}
  <p className="mt-3 whitespace-pre-wrap text-sm"><strong>Usage:</strong> {card.usage||'Add a usage example.'}</p>
  <p className="mt-3 whitespace-pre-wrap text-xs text-muted"><strong>Source/editorial note:</strong> {card.source_note||'Not entered'}</p>
  <details className="mt-4 border-t border-hairline pt-3"><summary className="min-h-11 cursor-pointer text-sm font-semibold">Review the practice prompts</summary>
   <p className="mt-2 text-sm">Recall: Which meaning matches “{card.word}”?</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{card.recognition_options.map((x,i)=><li key={i} className="whitespace-pre-wrap">{x}</li>)}</ul>
   <p className="mt-3 whitespace-pre-wrap text-sm">Cloze: {card.cloze_sentence.replace('{{word}}','_____')}</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{card.cloze_options.map((x,i)=><li key={i} className="whitespace-pre-wrap">{x}</li>)}</ul>
   {!!card.mizo_options?.length&&<><p className="mt-3 text-sm">English → Mizo choices:</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{card.mizo_options.map((x,i)=><li key={i} className="whitespace-pre-wrap">{x}</li>)}</ul></>}
  </details>
 </section>
}
