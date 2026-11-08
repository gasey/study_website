/** Dated facts share entities, but measurements need a fixed comparison identity. */
export const FACT_KINDS=[
 ['general','General changing fact'],['officeholder','Appointments and officeholders'],
 ['trade-ranking','Trade: exporters / importers'],['production-ranking','Production and resource rankings'],
 ['statistic','Statistics, rates and quantities'],['report-ranking','Reports, indices and rankings'],
 ['scheme','Schemes, rules and policies'],['award','Awards and sporting editions'],
 ['record','Records, firsts, largest / longest'],['event','Events, summits and discoveries'],
] as const
export type FactKind=typeof FACT_KINDS[number][0]
export interface Comparison {kind:FactKind;subject:string|null;metric:string|null;basis:'value'|'volume'|'rate'|'count'|'index-score'|'qualitative'|'other'|null;unit:string|null;population:string|null;source_series:string|null;methodology:string|null}
export const blankComparison=(kind:FactKind='general'):Comparison=>({kind,subject:null,metric:null,basis:null,unit:null,population:null,source_series:null,methodology:null})
export const measuredKind=(kind:FactKind)=>['trade-ranking','production-ranking','statistic','report-ranking'].includes(kind)
export const factKindLabel=(kind:FactKind)=>FACT_KINDS.find(k=>k[0]===kind)?.[1]||'General changing fact'
export const SERIES_FIELDS=[
 ['subject','Exact subject / commodity','Iron ore; not iron and steel'],
 ['metric','What is being measured?','Largest exporter; not largest producer'],
 ['unit','Units / currency / price basis','Tonnes; USD at current prices; percentage'],
 ['population','Which places / group are compared?','Countries worldwide; Indian states'],
 ['source_series','Report / dataset series','Named trade dataset or index series'],
 ['methodology','Definition and comparison limits','Commodity classification/code, re-exports, calendar versus financial years, methodology changes'],
] as const
