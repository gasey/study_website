import {reviewRequest} from './review'
export type DiscoveryExam='udc'|'combined-prelims'
export interface DiscoveryQuestion {id:string;appearance_id:string;question:string;paper_id:string;qnum:string|null;exam_name:string;year:number|null;url:string;participants:number;score:number}
export interface DiscoverySource {url:string;title:string;published_on:string;checked_on:string}
export interface HotPick {id:string;collection_id:DiscoveryExam;taxonomy_id:string;title:string;why_now:string;sources:DiscoverySource[];fact_revision_id:number|null;state:string;expires_at:string;version:number;url:string;topic:string;published_at:string|null}
export interface Discovery {collection_id:DiscoveryExam;popular:DiscoveryQuestion[];recommended:DiscoveryQuestion[];hot:HotPick[];generated_at:string|null;withheld:boolean;message?:string}
export const getDiscovery=(exam:DiscoveryExam,limit=3)=>reviewRequest<Discovery>('/discovery?collection_id='+exam+'&limit='+limit)
