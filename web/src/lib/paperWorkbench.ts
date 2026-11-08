export interface DraftQuestion {id:string;number:string;page:number;type:'mcq'|'descriptive';question:string;options:string[];direction:string;passage:string;explanation:string;answer_index:number|null;answer_source:'none'|'derived'|'key';key_page:number|null;subject_id:string;topic_id:string|null;subtopic_id:string|null;figure_job:string|null}
export interface PaperPayload {title:string;exam_name:string;year:number|null;paper_subject:string;booklet:string;source_reference:string;identity_page:number|null;identity_note:string;expected_questions:number|null;target_paper_id?:string|null;target_source_version?:string|null;key_sha256:string|null;key_status?:'provisional'|'final'|null;key_title:string;key_series:string;questions:DraftQuestion[]}
export interface RegisteredPaperSource {paper_id:string;exam_name:string|null;year:number|null;paper_subject:string|null;source_version:string;question_count:number;unambiguous:boolean}
export function linkRegisteredPaper(payload:PaperPayload,source:RegisteredPaperSource):PaperPayload {
 if(source.question_count||!source.unambiguous||!source.exam_name||!source.year)throw new Error('Choose an unambiguous empty original with a registered exam name and year.')
 return {...payload,target_paper_id:source.paper_id,target_source_version:source.source_version,exam_name:source.exam_name,year:source.year,paper_subject:source.paper_subject||''}
}
export function questionFromText(text:string,page:number,number:string,subject=''):DraftQuestion {
 const parts=text.split(/(?:^|\n)\s*\(?([A-Fa-f])[.)]\s+/)
 const letters=parts.filter((_,i)=>i%2===1).map(s=>s.toUpperCase())
 const parsed=letters.length>=2&&letters.length<=6&&letters.every((s,i)=>s===String.fromCharCode(65+i))
 return {id:crypto.randomUUID(),number,page,type:'mcq',question:(parsed?parts[0]:text).replace(/^\s*\d+[.)]\s*/,''),options:parsed?parts.filter((_,i)=>i>0&&i%2===0).map(s=>s.trim()):[],direction:'',passage:'',explanation:'',answer_index:null,answer_source:'none',key_page:null,subject_id:subject,topic_id:null,subtopic_id:null,figure_job:null}
}
export function splitNumberedPage(text:string):{number:string;text:string}[]{
 const matches=[...text.matchAll(/^\s*(\d{1,3})[.)]\s+/gm)]
 if(matches.length<2)return []
 return matches.map((m,i)=>({number:m[1],text:text.slice(m.index!,matches[i+1]?.index||text.length).trim()}))
}
