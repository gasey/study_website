import {useEffect,useState} from 'react'
import {MapContainer,TileLayer,GeoJSON,Marker,Polyline,Circle,useMap,useMapEvents} from 'react-leaflet'
import L from 'leaflet'
import type {Feature,FeatureCollection} from 'geojson'
import type {Chapter,Layer} from './types'
import 'leaflet/dist/leaflet.css'
import './atlas.css'

export type AtlasEdit={radiusKm?:number;mode:'none'|'pin'|'line'|'area';vertices:[number,number][];handles:[number,number][];onPoint:(p:[number,number])=>void;onFinish:()=>void;onMove:(index:number,p:[number,number])=>void}
function AuthorEvents({edit,onView,onPick}:{onPick?:(p:[number,number])=>void;edit?:AtlasEdit;onView?:(view:Chapter['view'])=>void}){
 const map=useMapEvents({click:e=>{if(onPick)onPick([e.latlng.lat,e.latlng.lng]);else if(edit?.mode!=='none')edit?.onPoint([e.latlng.lat,e.latlng.lng])},dblclick:()=>{if(edit&&edit.mode!=='none')edit.onFinish()},moveend:()=>{const c=map.getCenter();onView?.({center:[c.lat,c.lng],zoom:map.getZoom()})}})
 useEffect(()=>{if(edit&&edit.mode!=='none')map.doubleClickZoom.disable();else map.doubleClickZoom.enable()},[map,edit?.mode])
 useEffect(()=>{const c=map.getCenter();onView?.({center:[c.lat,c.lng],zoom:map.getZoom()})},[map])
 return <>{edit?.radiusKm&&edit.handles.length===1&&<Circle center={edit.handles[0]} radius={edit.radiusKm*1000} pathOptions={{color:'#176f72',fillOpacity:.08}}/>}{edit&&edit.vertices.length>1&&<Polyline positions={edit.vertices} pathOptions={{color:'#176f72',dashArray:'5 5'}}/>}{edit?.handles.map((p,i)=><Marker key={i} position={p} draggable icon={L.divIcon({className:'',html:'<span style="display:block;width:18px;height:18px;border:3px solid #fff;border-radius:50%;background:#176f72;box-shadow:0 0 0 2px #176f72"></span>',iconSize:[18,18],iconAnchor:[9,9]})} eventHandlers={{dragend:e=>{const ll=(e.target as L.Marker).getLatLng();edit.onMove(i,[ll.lat,ll.lng])}}}/>)}</>
}
function View({view,focus,reset}:{view:Chapter['view'];focus:Feature|null;reset:number}) {
  const map=useMap()
  useEffect(()=>{map.setView(view.center,view.zoom,{animate:false})},[map,view,reset])
  useEffect(()=>{if(focus){const bounds=L.geoJSON(focus).getBounds();if(bounds.isValid())map.fitBounds(bounds,{padding:[40,40],maxZoom:9,animate:false})}},[map,focus])
  useEffect(()=>{const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(map.getContainer());return()=>observer.disconnect()},[map])
  return null
}
export default function AtlasMap({chapter,layers,view,focus,reset,onFeature,edit,onView,onPick}:{onPick?:(p:[number,number])=>void;edit?:AtlasEdit;onView?:(view:Chapter['view'])=>void;chapter:Chapter;layers:Layer[];view:Chapter['view'];focus:Feature|null;reset:number;onFeature:(feature:Feature)=>void}) {
  const [tileError,setTileError]=useState(false)
  const [base,setBase]=useState(true)
  const [retry,setRetry]=useState(0)
  return <div>
    <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-secondary"><span>Drag to explore · use + / − to zoom · select a map feature</span><label className="flex min-h-11 items-center gap-2"><input type="checkbox" checked={base} onChange={e=>setBase(e.target.checked)}/>Show base map</label></div>
    {tileError&&base&&<p role="status" className="mb-2 rounded-lg border border-hairline bg-card p-3 text-sm">Some map tiles could not load. Study layers remain available. <button className="underline" onClick={()=>{setTileError(false);setRetry(x=>x+1)}}>Retry map tiles</button></p>}
    <div className="atlas-map relative isolate overflow-hidden rounded-xl border border-hairline" role="region" aria-label={`${chapter.title} interactive map`}>
      <MapContainer center={view.center} zoom={view.zoom} minZoom={2} maxZoom={18} scrollWheelZoom={false} className="h-full w-full" attributionControl>
        <AuthorEvents edit={edit} onView={onView} onPick={onPick}/><View view={view} focus={focus} reset={reset}/>
        {base&&<TileLayer key={retry} url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' maxZoom={19} eventHandlers={{tileerror:()=>setTileError(true)}}/>}
        {layers.filter((layer):layer is Extract<Layer,{kind:'vector'}>=>layer.kind==='vector'&&typeof layer.data!=='string').map(layer=><GeoJSON key={layer.id+JSON.stringify(layer)} data={layer.data as FeatureCollection}
          style={feature=>({color:feature?.properties?.color||layer.style?.color||'#176f72',weight:layer.style?.weight??2,fillColor:feature?.properties?.color||layer.style?.fillColor||layer.style?.color||'#176f72',fillOpacity:layer.style?.fillOpacity??.2,dashArray:layer.style?.dashArray})}
          pointToLayer={(feature,latlng)=>L.circleMarker(latlng,{radius:layer.style?.markerRadius??6,color:'#293b35',weight:2,fillColor:feature.properties?.color||layer.style?.color||'#176f72',fillOpacity:.95})}
          onEachFeature={(feature,item)=>{const label=String(feature.properties?.[layer.labelKey||'name']||layer.name);const text=document.createElement('span');text.textContent=label;item.bindTooltip(text,{sticky:true});item.on('click',()=>onFeature(feature))}}/>) }
      </MapContainer>
    </div>
    <p className="mt-2 text-xs leading-relaxed text-muted">Study overlays are illustrative; historical extents and routes are approximate. Base-map boundaries follow the map provider.</p>
  </div>
}
