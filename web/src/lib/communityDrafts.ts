/** Only the learner's composer input lives here; never fetched post/question bodies. */
export const DRAFT_PREFIX='finna.community-draft.v1:'
const TTL=7*24*60*60*1000,MAX_DRAFTS=32
export interface DiscussionDraftFields {kind:'doubt'|'explanation';sources:{url:string;note:string}[]}
export interface ComposerFields {body:string;subject:string;link:string;discussion?:DiscussionDraftFields}
export interface ComposerDraft {version:1;owner:string;scope:string;updated:number;fields:ComposerFields;retry:{payload:string;key:string}}
export const emptyComposerFields=():ComposerFields=>({body:'',subject:'',link:''})
export function draftKey(owner:string,scope:string){return DRAFT_PREFIX+encodeURIComponent(owner)+':'+encodeURIComponent(scope)}
export function clearComposerDrafts(){try{for(const key of Object.keys(localStorage))if(key.startsWith(DRAFT_PREFIX))localStorage.removeItem(key)}catch{/* Storage may be disabled. */}}
export function hasComposerDraft(fields:ComposerFields){return !!(fields.body||fields.subject||fields.link||fields.discussion?.sources.length||fields.discussion?.kind==='explanation')}
function validDiscussion(value:unknown):boolean {
 if(value===undefined)return true // Preserve existing note/share/reply drafts.
 const d=value as DiscussionDraftFields|null
 return !!d&&(d.kind==='doubt'||d.kind==='explanation')&&Array.isArray(d.sources)&&d.sources.length<=5
  &&d.sources.every(s=>!!s&&typeof s.url==='string'&&s.url.length<=2000&&typeof s.note==='string'&&s.note.length<=1000)
}
function valid(value:unknown,owner:string,scope:string):value is ComposerDraft {
 const v=value as ComposerDraft|undefined,f=v?.fields,r=v?.retry
 return v?.version===1&&v.owner===owner&&v.scope===scope&&typeof v.updated==='number'&&Number.isFinite(v.updated)&&v.updated<=Date.now()+60000&&v.updated>Date.now()-TTL
  &&!!f&&typeof f.body==='string'&&f.body.length<=5000&&typeof f.subject==='string'&&f.subject.length<=200&&typeof f.link==='string'&&f.link.length<=2000
  &&validDiscussion(f.discussion)
  &&!!r&&typeof r.payload==='string'&&r.payload.length<=65536&&typeof r.key==='string'&&/^[a-zA-Z0-9_-]{16,100}$/.test(r.key)
}
export function readComposerDraft(owner:string,scope:string):ComposerDraft|null {
 const key=draftKey(owner,scope),raw=localStorage.getItem(key)
 if(!raw)return null
 try{const saved:unknown=JSON.parse(raw);if(valid(saved,owner,scope))return saved}catch{/* Drop malformed or old records. */}
 localStorage.removeItem(key);return null
}
export function writeComposerDraft(draft:ComposerDraft){
 const key=draftKey(draft.owner,draft.scope)
 if(!hasComposerDraft(draft.fields)){localStorage.removeItem(key);return}
 const records=Object.keys(localStorage).filter(n=>n.startsWith(DRAFT_PREFIX)&&n!==key).map(n=>{try{return {key:n,time:Number(JSON.parse(localStorage.getItem(n)||'{}').updated)||0}}catch{return {key:n,time:0}}}).sort((a,b)=>b.time-a.time)
 for(const row of records.slice(MAX_DRAFTS-1))localStorage.removeItem(row.key)
 localStorage.setItem(key,JSON.stringify(draft))
}
