import type {ContentDocument,CuratedWordCard} from './materials'
const key=(s:string)=>s.normalize('NFKC').trim().toLowerCase().replace(/\s+/g,' ')
export function wordCardIssues(card:CuratedWordCard|undefined|null){
 if(!card)return ['Add the vocabulary card fields.']
 const issues:string[]=[]
 if([card.word,card.meaning,card.usage,card.source_note].some(x=>!x.trim()))issues.push('Finish the word, meaning, usage and source/editorial note.')
 if(card.language==='mizo-english'&&!card.mizo_gloss.trim())issues.push('Add the Mizo gloss for this pair.')
 for(const [name,choices,answer] of [['Recall',card.recognition_options,card.meaning],['Cloze',card.cloze_options,card.word]] as const){const keys=choices.map(key);if(keys.length<2||keys.length>6||keys.some(x=>!x)||new Set(keys).size!==keys.length||keys.filter(x=>x===key(answer)).length!==1)issues.push(name+' needs two to six distinct choices, including its correct meaning/word once.')}
 if(card.mizo_options?.length){const keys=card.mizo_options.map(key);if(card.language!=='mizo-english'||keys.length<2||keys.length>6||keys.some(x=>!x)||new Set(keys).size!==keys.length||keys.filter(x=>x===key(card.mizo_gloss)).length!==1)issues.push('Mizo choices need two to six distinct glosses including the correct gloss once.')}
 if(card.cloze_sentence.split('{{word}}').length!==2||!card.cloze_sentence.replace('{{word}}','').trim())issues.push('Write a cloze sentence with exactly one {{word}} gap.')
 return issues
}
export function vocabularyDocumentIssues(doc:ContentDocument){
 const cards=doc.blocks.filter(b=>b.type==='vocabulary'),issues:string[]=[]
 if(cards.length&&doc.kind!=='vocabulary-deck')issues.push('Choose Vocabulary deck as the material type.')
 if(doc.kind==='vocabulary-deck'){
  if(!cards.length)issues.push('Add a vocabulary card.')
  if(!doc.collection_id||!doc.subject_id)issues.push('Choose the reviewed exam and subject for this vocabulary deck.')
  const keys=cards.filter(b=>b.vocabulary).map(b=>b.vocabulary!.language+':'+key(b.vocabulary!.word))
  if(new Set(keys).size!==keys.length)issues.push('Use each word/language pair once in this deck.')
 }
 cards.forEach(b=>issues.push(...wordCardIssues(b.vocabulary).map(x=>'Vocabulary card: '+x)))
 return issues
}
