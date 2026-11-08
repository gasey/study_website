import {reviewRequest} from './review'
import type {MockSession} from './api'
export type TestConfig={duration_minutes:number;marks_correct:number;marks_wrong:number;answer_mode:'official'|'derived-practice'}
export type SharedTest={id:string;revision:number;title:string;description:string;subject_id:string;question_count:number;config:TestConfig;published_at:string;path:string;share_path:string}
export type TestQuestion={id:string;question:string;options:(string|null)[];answer_source:string;total?:number}
export type TestStats={editions:{revision:number;starts:number;completions:number;late_completions:number}[];basis:string}
export const getSharedTest=(id:string)=>reviewRequest<SharedTest>('/tests/'+encodeURIComponent(id))
export const sharedTestUrl=(id:string,origin=window.location.origin)=>origin+'/api/tests/'+encodeURIComponent(id)+'/share'
export const testInvitation=(id:string,title:string,origin=window.location.origin)=>title+'\nTake this mock test on India Study Map:\n'+sharedTestUrl(id,origin)
export const testWhatsAppUrl=(id:string,title:string,origin=window.location.origin)=>'https://wa.me/?text='+encodeURIComponent(testInvitation(id,title,origin))
export function mockResumePath(m:Pick<MockSession,'collection_id'|'paper_id'|'section_path'|'answer_mode'|'paper_mode'|'learning_test_id'>){
 if(m.learning_test_id)return '/tests/'+encodeURIComponent(m.learning_test_id)+'/take'
 const p=new URLSearchParams();if(m.paper_id)p.set('paper',m.paper_id);else if(m.section_path)p.set('section',m.section_path);if(m.paper_mode==='full')p.set('simulation','full');if(m.answer_mode==='derived-practice')p.set('mode','derived');return '/exams/'+encodeURIComponent(m.collection_id)+'/mock'+(p.size?'?'+p:'')
}
