/** Tag search scope is independent of the paper currently open in My work. */
export function tagPaperScope(params:URLSearchParams){return params.get('tag_paper')||(params.get('tab')==='retag'?params.get('paper')||'':'')}
export function updateTagFilter(previous:URLSearchParams,key:string,value:string){
 const p=new URLSearchParams(previous)
 if(key==='tag_paper'&&p.get('tab')==='retag')p.delete('paper')
 if(key==='tag_q'&&p.get('tab')==='retag')p.delete('q')
 value?p.set(key,value):p.delete(key)
 p.delete('tag_offset')
 return p
}

export function tagReviewHref(question:string,appearance:string,paper:string,returnTo:string){
 const p=new URLSearchParams({tab:'retag',tag_q:question,tag_issue:'all',tag_selected:question,tag_appearance:appearance,tag_paper:paper,tag_return:returnTo})
 return '/admin/bank?'+p
}
export function tagQuery(params:URLSearchParams){return params.get('tag_q')||(params.get('tab')==='retag'?params.get('q')||'':'')}
export function tagReturn(params:URLSearchParams){const value=params.get('tag_return')||'';return value.startsWith('/admin/bank?')||value.startsWith('/editorial?')?value:''}
