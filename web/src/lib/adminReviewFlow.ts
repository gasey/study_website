/** Navigation only: never modifies review, publication or scoring state. */
export function nextReviewTarget<T extends {id:string}>(items:T[],total:number,offset:number,selected:string){
 const index=items.findIndex(q=>q.id===selected)
 if(index<0)return null
 if(index+1<items.length)return {kind:'question' as const,question:items[index+1]}
 if(offset+items.length<total)return {kind:'page' as const,offset:offset+items.length}
 return null
}
export function adminReadCanCoalesce(path:string){
 return path.startsWith('/admin/bank/')||path==='/review/taxonomy'||path==='/review/session'
}
export const ADMIN_TAXONOMY_TABS=['questions','retag','review','people','taxonomy']
