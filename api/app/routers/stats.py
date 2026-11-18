"""Public statistical reading and cookie/MFA protected owner review."""
import hashlib
import json
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from ..db import cursor
from ..services import stats as store
from ..services.stats_catalog import METRICS, SOURCES, SURVEYS
from ..services.review_identity import Actor, identity, require_role

router=APIRouter(prefix='/api/stats',tags=['Stats'])
Owner=Annotated[Actor,Depends(identity)]

def cached(request,data):
 encoded=json.dumps(jsonable_encoder(data),sort_keys=True,separators=(',',':'))
 etag='"'+hashlib.sha256(encoded.encode()).hexdigest()+'"'
 headers={'ETag':etag,'Cache-Control':'public, max-age=300'}
 if request.headers.get('if-none-match')==etag:return Response(status_code=304,headers=headers)
 return Response(encoded,media_type='application/json',headers=headers)

def source(m):return SOURCES[m['source_id']]

@router.get('/overview')
async def overview(request:Request,country:str=Query('IND',pattern=r'^[A-Z]{3}$')):
 items=[]
 for m in METRICS.values():
  r=await store.release(m['id'],place='IN-MZ' if m['scope']=='states' else country);row=None
  if r:
   candidates=[x for x in r['payload']['rows'] if x['place']==('IN-MZ' if m['scope']=='states' else country) and x['value'] is not None]
   row=max(candidates,key=lambda x:x['period']) if candidates else None
  items.append({**m,'source':source(m),'release':store.metadata(r) if r else None,'observation':row,'freshness':await store.freshness(m['id'])})
 return cached(request,{'country':country,'items':items,'surveys':await survey_catalog()})

@router.get('/sources')
async def sources(request:Request):
 return cached(request,{'items':[{**s,'metrics':[{'id':m['id'],'title':m['title'],'freshness':await store.freshness(m['id'])} for m in METRICS.values() if m['source_id']==s['id']]} for s in SOURCES.values()]})

@router.get('/metrics/{metric_id}/releases')
async def releases(metric_id:str):
 if metric_id not in METRICS:raise HTTPException(404,'Metric not found')
 async with cursor() as cur:
  await cur.execute("SELECT id,edition,reference_period,published_at FROM stats_releases WHERE metric_id=%s AND status='published' ORDER BY published_at DESC LIMIT 50",(metric_id,));return {'items':await cur.fetchall()}

@router.get('/metrics/{metric_id}')
async def detail(request:Request,metric_id:str,places:str=Query('IND',max_length=100),period:str|None=Query(None,pattern=r'^\d{4}(?:-\d{2})?$'),release_id:str|None=Query(None,max_length=80)):
 m=METRICS.get(metric_id)
 if not m:raise HTTPException(404,'Metric not found')
 ids=list(dict.fromkeys(places.split(',')))
 if not 1<=len(ids)<=4 or any(not __import__('re').fullmatch(r'[A-Z0-9-]{2,20}',p) for p in ids):raise HTTPException(422,'Choose up to four places')
 r=await store.release(metric_id,release_id)
 if not r:
  if release_id:raise HTTPException(404,'Published release not found')
  return cached(request,{'metric':m,'source':source(m),'release':None,'places':[],'history':[],'observations':[],'period':None,'periods':[],'freshness':await store.freshness(metric_id)})
 allrows=r['payload']['rows'];hist=[x for x in allrows if x['place'] in ids]
 available=[{x['period'] for x in hist if x['place']==p and x['value'] is not None} for p in ids]
 common=set.intersection(*available) if available else set()
 period=period or (max(common) if common else max((x['period'] for x in hist),default=r['reference_period']))
 observations=[]
 for p in ids:
  entry=next((x for x in hist if x['place']==p and x['period']==period),None)
  observations.append(entry or {'place':p,'name':next((x['name'] for x in allrows if x['place']==p),p),'period':period,'value':None,'rank':None,'group':'countries','status':'reported'})
 return cached(request,{'metric':m,'source':source(m),'release':store.metadata(r),'places':sorted({x['place']: {'id':x['place'],'title':x['name']} for x in allrows}.values(),key=lambda x:x['title']),'periods':sorted({x['period'] for x in hist},reverse=True),'period':period,'observations':observations,'history':sorted(hist,key=lambda x:(x['period'],x['place'])),'freshness':await store.freshness(metric_id)})

@router.get('/metrics/{metric_id}/rankings')
async def rankings(request:Request,metric_id:str,period:str|None=Query(None,pattern=r'^\d{4}(?:-\d{2})?$'),release_id:str|None=Query(None,max_length=80),group:str|None=Query(None,max_length=80),q:str=Query('',max_length=100),offset:int=Query(0,ge=0,le=25000),limit:int=Query(25,ge=1,le=100)):
 m=METRICS.get(metric_id)
 if not m:raise HTTPException(404,'Metric not found')
 if m['scope']=='states' and not group:group='Smaller states'
 r=await store.release(metric_id,release_id)
 if not r:
  if release_id:raise HTTPException(404,'Published release not found')
  return cached(request,{'items':[],'total':0,'coverage':0,'india':None,'release':None,'derived':m['kind']=='indicator','group':group,'period':None})
 if not period and m['scope']=='world':
  india=[x['period'] for x in r['payload']['rows'] if x['place']=='IND' and x['value'] is not None]
  if india:period=max(india)
 rows,period=store.select_rows(r,period,group)
 rows=[x for x in rows if x['value'] is not None]
 derived=m['kind']=='indicator'
 if derived:
  # Deterministic competition ranks on raw values; equal values share a rank.
  reverse=m['direction']!='lower'
  rows.sort(key=lambda x:((-x['value'] if reverse else x['value']),x['name']))
  for i,x in enumerate(rows):x['rank']=rows[i-1]['rank'] if i and x['value']==rows[i-1]['value'] else i+1
 else:rows.sort(key=lambda x:(x['rank'] if x['rank'] is not None else 99999,x['name']))
 coverage=len(rows);india=next((x for x in rows if x['place']==('IN-MZ' if m['scope']=='states' else 'IND')),None)
 rows=[x for x in rows if q.casefold() in x['name'].casefold() or q.upper()==x['place']]
 return cached(request,{'items':rows[offset:offset+limit],'total':len(rows),'offset':offset,'coverage':coverage,'india':india,'release':store.metadata(r),'derived':derived,'group':group,'period':period,'groups':sorted({x['group'] for x in r['payload']['rows']}),'periods':sorted({x['period'] for x in r['payload']['rows']},reverse=True)})

@router.get('/surveys')
async def surveys(request:Request):return cached(request,{'items':await survey_catalog()})

@router.get('/surveys/{edition}')
async def survey(edition:str):
 s=next((s for s in await survey_catalog() if s['id']==edition),None)
 if not s:raise HTTPException(404,'Survey edition not found')
 return s

@router.get('/admin/releases')
async def pending(actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute("SELECT id,metric_id,edition,reference_period,source_url,content_hash,fetched_at,status FROM stats_releases ORDER BY fetched_at DESC LIMIT 100");items=await cur.fetchall()
  await cur.execute('SELECT * FROM stats_source_watches ORDER BY source_id');return {'items':items,'sources':await cur.fetchall()}

@router.get('/admin/releases/{release_id}')
async def inspect(release_id:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('SELECT * FROM stats_releases WHERE id=%s',(release_id,));r=await cur.fetchone()
  if not r:raise HTTPException(404,'Release not found')
  return r

@router.post('/admin/releases')
async def stage(body:store.ReleaseInput,actor:Owner):
 async with cursor() as cur:await require_role(cur,actor.id,roles=('owner',))
 i,created=await store.stage(body)
 async with cursor() as cur:
  await cur.execute('SELECT status FROM stats_releases WHERE id=%s',(i,));state=(await cur.fetchone())['status']
 return {'id':i,'created':created,'status':state}

class Decision(BaseModel):
 decision:Literal['publish','reject']
 note:str=Field(min_length=10,max_length=2000)

@router.post('/admin/releases/{release_id}/decision')
async def decision(release_id:str,body:Decision,actor:Owner):
 await store.decide(release_id,actor.id,body.decision,body.note)
 return {'id':release_id,'decision':body.decision}


class StatsBodyLimit:
 """Bound statistical import JSON before FastAPI parses it (including chunks)."""
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  if not (scope.get('type')=='http' and scope.get('method')=='POST' and scope.get('path','').startswith('/api/stats/admin/')):
   return await self.app(scope,receive,send)
  size=0;messages=[]
  while True:
   message=await receive()
   if message['type']=='http.disconnect':return
   size+=len(message.get('body',b''))
   if size>4*1024*1024:return await JSONResponse({'detail':'Stats import exceeds 4 MiB'},status_code=413)(scope,receive,send)
   messages.append(message)
   if not message.get('more_body',False):break
  async def replay():return messages.pop(0) if messages else await receive()
  await self.app(scope,replay,send)


async def survey_catalog():
 import copy
 async with cursor() as cur:
  await cur.execute("SELECT checked_at,needs_review,error FROM stats_source_watches WHERE source_id='survey'");watch=await cur.fetchone()
 result=copy.deepcopy(SURVEYS)
 for s in result:s['catalogue_status']={'changed':bool(watch and watch['needs_review']),'delayed':bool(watch and watch['error']),'last_checked_at':watch['checked_at'] if watch else None}
 return result
