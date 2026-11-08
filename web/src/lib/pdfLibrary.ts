export interface PdfScan {id:number;state?:string;finished_at:string|null;created_at?:string;heartbeat_at?:string|null;files_seen:number;files_hashed:number;error?:string|null}
export interface PdfModule {id:string;title:string;version?:number}
export interface PdfLibraryItem {
 key:string;paper_id:string|null;title:string;source_label:string;year:number|null;kind:string;
 questions:number;official:number;verified:number;needs_review:number;unsolved:number;written:number;explained:number;
 registered_documents:number;final_keys:number;provisional_keys:number;modules:PdfModule[];
 asset_count:number;sha256:string|null;file_id:number|null;bytes:number|null;copies:number|null;valid_pdf:boolean|null;
 paths:{root:string;path:string;id:number}[];file_status:'unknown'|'available'|'ambiguous'|'not-found';
 empty_paper:boolean;missing_registration:boolean;unlinked:boolean;
 draft:{id:string;state:string;version:number;updated_at:string;error:string|null;published_paper_id:string|null}|null;
}
export function pdfLibraryAction(item:PdfLibraryItem):'draft'|'review'|'inspect'|'intake' {
 if(item.draft&&item.draft.state!=='published')return 'draft'
 if(item.paper_id&&item.questions>0)return 'review'
 if(item.file_status!=='available'||!item.valid_pdf||item.missing_registration||item.kind!=='paper')return 'inspect'
 return 'intake'
}
export function pdfWorkbenchHref(id:string,returnTo:string){
 return '/paper-workbench?'+new URLSearchParams({draft:id,return_to:returnTo})
}
export function pdfLibraryReturn(value:string|null){
 return value?.startsWith('/admin/bank?tab=pdf-library')?value:'/admin/bank?tab=pdf-library'
}
export function pdfInventoryHref(id:string){return '/admin/bank?'+new URLSearchParams({tab:'exams',inv_view:'papers',inventory_paper:id})}
export function pdfReviewHref(id:string){return '/admin/bank?'+new URLSearchParams({tab:'questions',paper:id})}
