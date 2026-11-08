import type {TestConfig} from './sharedTests'
import {reviewRequest} from './review'
export type CatalogSource={title:string;url:string;checked_on:string}
export type CatalogContent={test_config?:TestConfig|null;kind:'day'|'practice';title:string;description:string;subject_id:string;question_ids:string[];sources:CatalogSource[];month:number|null;day:number|null;occurrences:string[];themes:{year:number;text:string;source:CatalogSource}[];suggested_minutes:number|null}
export type CatalogEntry={id:string;content:CatalogContent;next_date:string|null;available:number}
export type CatalogPage={items:CatalogEntry[];today:string}
export type CatalogDraft={id:string;version:number;state:string;author_id:string;payload:CatalogContent;live_payload:CatalogContent|null;history:{version:number;action:string;reason:string;created_at:string}[]}
export const catalog=(kind:'day'|'practice',month='',q='')=>reviewRequest<CatalogPage>('/learning-catalog?'+new URLSearchParams({kind,...month?{month}:{},...q?{q}:{}}))
