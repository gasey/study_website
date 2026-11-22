import type {FeatureCollection} from 'geojson'
export function validGeoJSON(data:unknown):FeatureCollection{
 const fail=()=>{throw Error('Use finite, bounded point/line/polygon GeoJSON; areas need closed outlines.')}
 let count=0
 function geometry(g:any){const c=g?.coordinates,t=g?.type;let points:any[]=[]
  if(t==='Point')points=[c]
  else if(t==='LineString'){if(!Array.isArray(c)||c.length<2)fail();points=c}
  else if(t==='Polygon'){if(!Array.isArray(c)||!c.length)fail();for(const r of c){if(!Array.isArray(r)||r.length<4||JSON.stringify(r[0])!==JSON.stringify(r.at(-1)))fail();points.push(...r)}}
  else if(['MultiPoint','MultiLineString','MultiPolygon'].includes(t)){if(!Array.isArray(c)||!c.length)fail();for(const part of c)geometry({type:{MultiPoint:'Point',MultiLineString:'LineString',MultiPolygon:'Polygon'}[t as string],coordinates:part});return}
  else fail()
  count+=points.length;if(count>30000)fail();for(const p of points)if(!Array.isArray(p)||p.length!==2||p.some(x=>typeof x!=='number'||!Number.isFinite(x))||p[0]<-180||p[0]>180||p[1]<-90||p[1]>90)fail()
 }
 const d=data as any;if(d?.type!=='FeatureCollection'||!Array.isArray(d.features)||d.features.length>1500)fail();for(const f of d.features){if(f?.type!=='Feature'||f.properties!==null&&typeof f.properties!=='object')fail();geometry(f.geometry)}return d as FeatureCollection
}
