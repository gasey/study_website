#!/usr/bin/env python3
"""Build private district starting proposals from frozen attributed inputs; no DB writes.

The boundary subset is ODbL 1.0; GeoNames points retain CC BY 4.0 separately.
Run --check to check generated output without rewriting it.
"""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'web/public/maps'
BOUNDARY=DATA/'mizoram-district-boundaries-2021.geojson'
POINTS=DATA/'mizoram-gazetteer-points.json'

def build():
    boundaries=json.loads(BOUNDARY.read_text());points=json.loads(POINTS.read_text());chapters=[]
    def ring_inside(x,y,ring):
        inside=False
        for a,b in zip(ring,ring[1:]):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        return inside
    def contains(g,p):
        polygons=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        return any(ring_inside(*p,rings[0]) and not any(ring_inside(*p,h) for h in rings[1:]) for rings in polygons)
    source=lambda id,title,url,attr,note,**kw:dict(id=id,title=title,url=url,attribution=attr,note=note,checked_on='2026-11-18',reuse='reference',**kw)
    base=[source('boundaries','geoBoundaries IND ADM2 · represented year 2021','https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/','Pathways Data Pvt. Ltd., lgdirectory.gov.in; distributed by geoBoundaries.','2021 simplified dataset, not a current legal boundary survey. This subset retains original geometry and source properties; Finna adds display names only. Download is provided under ODbL 1.0.',license='ODbL 1.0',license_url='https://opendatacommons.org/licenses/odbl/1-0/',download_path='/maps/mizoram-district-boundaries-2021.geojson'),source('geonames','GeoNames gazetteer · approximate feature points','https://download.geonames.org/export/dump/readme.txt','GeoNames contributors, CC BY 4.0.','Extracted from IN.zip on 18 November 2026. Names and coordinates are approximate reference points, not river courses or an official district assignment. Points are spatially selected against the dated boundary; no elevations/population or present-day jurisdiction inferred.',license='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/',download_path='/maps/mizoram-gazetteer-points.json'),source('district-list','Mizoram Legislative Assembly · district/headquarters directory','https://www.mizoramassembly.in/page/about-us','Mizoram Legislative Assembly.','Directory consulted for district/headquarters names only; no prose, maps or images copied. Saiha is displayed as Siaha, matching the existing profile district list.',license_url='https://www.mizoramassembly.in/page/copyright-policy')]
    base[0]['reuse']=base[1]['reuse']='licensed'
    for f in sorted(boundaries['features'],key=lambda f:f['properties']['shapeName']):
        name=f['properties']['shapeName'];district='Siaha' if name=='Saiha' else name;geometry=f['geometry'];selected=[p for p in points['features'] if contains(geometry,p['geometry']['coordinates'])]
        hq=next(p for p in points['features'] if p['properties'].get('headquarters')==district)
        coords=hq['geometry']['coordinates'];layers=[]
        b=json.loads(json.dumps(f));b['properties']['name']=district+' · 2021 illustrative boundary'
        def layer(id,name,features,refs,color):return {'id':id,'name':name,'description':('Reference points only; not a traced river course.' if id=='rivers' else 'Dated, approximate study data; inspect the sources before publication.'),'kind':'vector','data':{'type':'FeatureCollection','features':features},'source_ids':refs,'defaultOn':True,'style':{'color':color,'fillColor':color,'fillOpacity':.10,'weight':2,'markerRadius':6}}
        layers.append(layer('boundary','District boundary · 2021',[b],['boundaries'],'#176f72'))
        layers.append(layer('headquarters','Headquarters · approximate location',[hq],['champhai-reference'] if district=='Champhai' else ['geonames','district-list'],'#b45309'))
        for id,title,codes,color in [('rivers','River reference points',('STM',),'#0e7490'),('peaks','Peak and hill reference points',('MT','PK','HLL'),'#6366f1')]:
            layers.append(layer(id,title,[p for p in selected if p['properties'].get('feature_code') in codes],['geonames'],color))
        sources=json.loads(json.dumps(base))
        if district=='Champhai':sources.append(source('champhai-reference','Champhai district · location reference','https://champhai.nic.in/','Champhai District Administration, Government of Mizoram.','Approximate locator converted from the published 23°28′28″N, 93°19′32″E. A coordinate fact only; no site prose or map reproduced.'))
        chapters.append({'id':'mizoram-district-'+district.lower(),'district':district,'subject':'geography','unit':'Mizoram districts','title':district+' district','summary':'Dated district boundary, headquarters and available river/peak reference points. A source proposal for owner review.','focus':'Read '+district+' through the 2021 illustrative boundary and attributed reference points. These do not certify current legal boundaries or complete district geography.','view':{'center':[coords[1],coords[0]],'zoom':10},'layers':layers,'facts':[{'id':'hq','text':'District headquarters: '+district+(' (also recorded as Saiha in the Assembly directory).' if district=='Siaha' else '.')},{'id':'scope','text':'Boundary source represents 2021. River and peak points are a partial gazetteer selection; absence is not evidence that a district has no such feature.'}],'sources':sources,'quiz':[],'drills':[],'events':[]})
    return {'status':'private-starting-proposals','attribution':'AI-assisted source preparation; not independent human review or owner publication.','chapters':chapters}

if __name__=='__main__':
    payload=build();encoded=json.dumps(payload,ensure_ascii=False,indent=2)+'\n';target=ROOT/'api/app/data/atlas-district-proposals.json'
    if sys.argv[1:]==['--check']:assert target.read_text()==encoded,'District proposals differ from frozen source data'
    else:
        assert not sys.argv[1:];target.write_text(encoded)
    print('11 private district proposals prepared; no publication, inferred taxonomy bindings or database writes.')
