export type MapColumn={name:string;type:string;required:boolean;primary_key:boolean}
export type MapNode={id:string;title:string;total:number;group:string;description:string;href:string;columns:MapColumn[]}
export type MapForeignKey={id:string;source:string;target:string;source_columns:string[];target_columns:string[];source_unique:boolean;optional:boolean}
export type MapData={tables:MapNode[];coverage:{questions:number;without_topic:number;without_subtopic:number};relationships:[string,string,string][];foreign_keys:MapForeignKey[];observed_at:string;read_only:boolean;scope:string}
export type MapEdge={id:string;source:string;target:string;label:string;fk?:MapForeignKey}
export const MAP_GROUPS=[['bank','Question bank'],['delivery','Modules & tests'],['editing','Editing & publication'],['all','All mapped tables']]
export function mapEdges(data:MapData,mode:'content'|'schema'):MapEdge[]{return mode==='content'?data.relationships.map((r,i)=>({id:'flow-'+i,source:r[0],target:r[1],label:r[2]})):data.foreign_keys.map(f=>({id:f.id,source:f.source,target:f.target,label:f.source_columns.join(', ')+' → '+f.target_columns.join(', '),fk:f}))}
