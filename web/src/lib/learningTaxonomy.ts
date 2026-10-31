import type {TaxonomyNode} from './review'
export interface Classification {subject_id:string;topic_id?:string|null;subtopic_id?:string|null}
export const learningSubjectId=(id:string)=>['general-knowledge','general-studies'].includes(id)?'gk-gs':id
export const topicKey=(label:string)=>label.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')
export function learningPathLabel(path:Classification,nodes:TaxonomyNode[]) {
  return [learningSubjectId(path.subject_id)==='gk-gs'?'GK/GS':nodes.find(n=>n.id===path.subject_id)?.label||path.subject_id,
    nodes.find(n=>n.id===path.topic_id)?.label||path.topic_id,
    nodes.find(n=>n.id===path.subtopic_id)?.label||path.subtopic_id].filter(Boolean).join(' → ')
}
export function topicChoices(nodes:TaxonomyNode[],subject:string) {
  const parents=new Set(nodes.filter(n=>n.level==='subject'&&learningSubjectId(n.id)===subject).map(n=>n.id))
  const grouped=new Map<string,TaxonomyNode[]>()
  for(const node of nodes.filter(n=>n.level==='topic'&&parents.has(n.parent_id||''))) {
    const key=topicKey(node.label);grouped.set(key,[...grouped.get(key)||[],node])
  }
  return [...grouped.entries()].sort((a,b)=>a[0].localeCompare(b[0]))
}
export function resolveTopic(choices:TaxonomyNode[],previousSubject:string):Classification {
  const topic=choices.find(n=>n.parent_id===previousSubject)||choices.find(n=>n.parent_id==='general-knowledge')||choices[0]
  return {subject_id:topic.parent_id!,topic_id:topic.id,subtopic_id:null}
}
