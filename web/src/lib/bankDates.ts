import {reviewRequest} from './review'
export type BankDate={year:number|null;month:number|null;day:number|null;precision:'date'|'month'|'year';era?:'BCE'}
export type DateEvidence='answer'|'question'|'unresolved'
export type DateEvent={id:string;title:string;category:'observance'|'history'|'event';dates:BankDate[];question_count:number;evidence:DateEvidence[];subjects:string[];preview:string;first_question_id:string}
export type DateQuestion={id:string;question:string;evidence:DateEvidence;subject:string|null;origin:'paper'|'community';answer_source:string|null}
export type DateIndex={items:DateEvent[];total:number;question_count:number;dated_count:number;offset:number;limit:number;today:string;subjects:{id:string;title:string}[];calendar_days:{day:number;events:number}[];month_only_count:number}
export type DateDetail={entry:DateEvent;questions:DateQuestion[];total:number;offset:number;limit:number;today:string;subjects:{id:string;title:string}[]}
export const bankDates=(query:string)=>reviewRequest<DateIndex|DateDetail>('/learning-catalog/bank-dates?'+query)
export const dateMonths=['January','February','March','April','May','June','July','August','September','October','November','December']
export function formatBankDate(value:BankDate):string{
 const year=value.year?`${value.year}${value.era?' BCE':''}`:''
 return [value.day,value.month?dateMonths[value.month-1]:null,year].filter(Boolean).join(' ')
}
export const dateEvidenceLabel=(evidence:DateEvidence)=>({answer:'From bank answer',question:'Mentioned in question',unresolved:'Date to check'}[evidence])

export function dateYearGroup(entry:DateEvent):string{
 const value=entry.dates[0]
 if(!value)return 'Dates to check'
 if(value.year)return `${value.year}${value.era?' BCE':''}`
 return 'Dates without a recorded year'
}
