import type {AvatarLook} from './avatar'
import {reviewRequest} from './review'
export type BlockType='heading'|'paragraph'|'callout'|'quote'|'list'|'table'|'image'|'link'|'question'|'vocabulary'
export interface CuratedWordCard{language:'english'|'mizo-english';word:string;meaning:string;usage:string;mizo_gloss:string;recognition_options:string[];cloze_sentence:string;cloze_options:string[];source_note:string;mizo_options?:string[]}
export const emptyWordCard=():CuratedWordCard=>({language:'english',word:'',meaning:'',usage:'',mizo_gloss:'',recognition_options:[],cloze_sentence:'',cloze_options:[],source_note:''})
export interface ContentBlock{id:string;type:BlockType;text?:string;items?:string[];rows?:string[][];url?:string;alt?:string;question_id?:string|null;vocabulary?:CuratedWordCard|null}
export interface ContentDocument{title:string;summary:string;preview:string;kind:'note'|'article'|'guide'|'lesson'|'vocabulary-deck';access:'free'|'pro'|'paid-preview';price_paise:number;tags:string[];blocks:ContentBlock[];collection_id:string|null;subject_id:string|null}
export const EMPTY_DOCUMENT:ContentDocument={title:'',summary:'',preview:'',kind:'note',access:'free',price_paise:0,tags:[],blocks:[],collection_id:null,subject_id:null}
export interface MaterialItem{avatar?:AvatarLook|null;creator_public?:boolean;id:string;author:string;author_id:string;payload:Omit<ContentDocument,'blocks'>;published_at:string;published_revision:number;helpful:number;studied:number}
export interface MaterialRead extends Omit<MaterialItem,'payload'>{document:ContentDocument;can_read:boolean;is_author:boolean;saved:boolean;reaction:{helpful:boolean;studied:boolean};payments_enabled:boolean;preview_mode?:boolean}
export interface MaterialDraft{feedback?:{action:string;detail:{reason?:string;revision?:number};created_at:string}|null;id:string;author_id:string;workflow_state:string;lock_version:number;revision:number;published_revision:number|null;document:ContentDocument;revisions:{revision:number;created_at:string}[];events:{action:string;detail:{reason?:string;revision?:number};created_at:string}[]}
export const contentRequest=reviewRequest
export function newBlock(type:BlockType):ContentBlock{return {id:crypto.randomUUID(),type,text:'',...type==='list'?{items:['']}:type==='table'?{rows:[['Heading','Heading'],['','']]}:type==='image'?{url:'',alt:''}:type==='link'?{url:''}:type==='question'?{question_id:''}:type==='vocabulary'?{vocabulary:emptyWordCard()}:{}}}
export const BLOCK_LABELS:Record<BlockType,string>={heading:'Heading',paragraph:'Paragraph',callout:'Exam tip',quote:'Quote',list:'List / cards',table:'Table / timeline',image:'Image',link:'Reference link',question:'Bank question',vocabulary:'Vocabulary card'}
