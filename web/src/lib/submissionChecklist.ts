import {vocabularyDocumentIssues} from './curatedWordCards'
import type {ContentDocument} from './materials'
import type {CatalogContent} from './learningCatalog'
import type {Proposal} from './review'
export const SUBMISSION_BODY_LIMIT=65536
export function submissionBytes(value:unknown){return new TextEncoder().encode(JSON.stringify(value)).length}
export function materialIssues(doc:ContentDocument){
 const issues:string[]=vocabularyDocumentIssues(doc)
 if(doc.title.trim().length<5)issues.push('Add a title with at least 5 characters.')
 if(doc.summary.trim().length<20)issues.push('Add a useful summary with at least 20 characters.')
 if(!doc.blocks.length)issues.push('Add at least one content block.')
 if(doc.access!=='free'&&doc.preview.trim().length<40)issues.push('Add a public excerpt with at least 40 characters.')
 if(new Set(doc.blocks.map(b=>b.id)).size!==doc.blocks.length)issues.push('Each block needs its own ID.')
 for(let i=0;i<doc.blocks.length;i++){
  const b=doc.blocks[i],label='Block '+(i+1)+': '
  if(['heading','paragraph','callout','quote'].includes(b.type)&&!b.text?.trim())issues.push(label+'finish or remove the empty text.')
  if(b.type==='list'&&(!b.items?.length||b.items.some(x=>!x.trim())))issues.push(label+'finish every list item.')
  if(b.type==='table'&&(!b.rows?.length||b.rows.some(r=>!r.length)||new Set(b.rows.map(r=>r.length)).size!==1))issues.push(label+'use nonempty rows with matching column counts.')
  if(['image','link'].includes(b.type)){
   try{const u=new URL(b.url||'');if(u.protocol!=='https:'||u.username||u.password)throw Error()}catch{issues.push(label+'use an HTTPS source URL without embedded credentials.')}
   if(b.type==='image'&&!b.alt?.trim())issues.push(label+'add an image description.')
   if(b.type==='link'&&!b.text?.trim())issues.push(label+'name the linked source.')
  }
  if(b.type==='question'&&!b.question_id)issues.push(label+'choose a bank question.')
 }
 return issues
}
export function proposalIssues(p:Proposal){
 const issues:string[]=[]
 if(!p.evidence.length||p.evidence.some(e=>e.note.trim().length<5))issues.push('Name the source or describe your own worked reasoning in Evidence.')
 if(p.rationale.trim().length<20)issues.push('Explain the change and its evidence in at least 20 characters.')
 return issues
}
export function collectionIssues(c:CatalogContent){
 const issues:string[]=[]
 if(c.title.trim().length<3)issues.push('Add a title with at least 3 characters.')
 if(c.description.trim().length<20)issues.push('Add a description with at least 20 characters.')
 if(!c.subject_id)issues.push('Choose an approved subject.')
 if(c.kind==='practice'&&!c.question_ids.filter(q=>q.trim()).length)issues.push('Link at least one reviewed bank question.')
 if(c.kind==='day'&&!c.sources.length)issues.push('Name a verified source for the date or observance.')
 return issues
}
