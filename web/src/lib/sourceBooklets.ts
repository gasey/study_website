import type {CollectionPaper} from './api'
import type {BookletGroup} from './mcsBooklets'

// Only explicit booklet markers qualify. “Paper I/II” and unknown sittings stay separate.
const marker=/\b(?:series|booklet(?:\s+series)?|set)(?:\s+(?:no\.?|number|code))?[\s_:'"()\-]*([A-D]|[1-4])(?=$|[\s.\-_'"()])/i
export function sourceBookletIdentity(paper:Pick<CollectionPaper,'id'|'year'|'paper_number'>){
 const match=marker.exec(paper.id.split('/').pop()||'')
 if(!match||paper.year==null)return null
 const at=paper.id.lastIndexOf('/')
 const stem=(paper.id.slice(0,at+1)+paper.id.slice(at+1).replace(marker,'[booklet]')).replace(/[.\s]+(?=\.pdf$)/i,'').toLowerCase()
 return {key:`${paper.year}:${paper.paper_number||''}:${stem}`,series:match[1].toUpperCase()}
}
export function withoutBooklet(title:string){return title.replace(marker,'').replace(/\s*[-·]\s*$/,'').replace(/[.\s]+$/,'').replace(/\s+/g,' ').trim()}
export function representativeBooklet(group:BookletGroup){
 return [...group.papers].sort((a,b)=>(b.questions||0)-(a.questions||0)||(sourceBookletIdentity(a)?.series||'').localeCompare(sourceBookletIdentity(b)?.series||'',undefined,{numeric:true})||a.id.localeCompare(b.id))[0]
}
/** Navigation grouping only: variants keep exact PDF, question and answer mappings. */
export function groupSourceBooklets(papers:CollectionPaper[]):BookletGroup[]{
 const groups=new Map<string,BookletGroup>()
 for(const paper of papers){const identity=sourceBookletIdentity(paper),key=identity?.key||paper.id
  if(!groups.has(key))groups.set(key,{id:key,title:identity?withoutBooklet(paper.paper_label||paper.id.split('/').pop()?.replace(/\.pdf$/i,'')||paper.title):paper.paper_label||paper.title,papers:[]})
  groups.get(key)!.papers.push(paper)
 }
 return [...groups.values()]
}
