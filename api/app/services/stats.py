"""Immutable, validated releases. Public reads never fetch third-party services."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from .stats_catalog import METRICS, SOURCES

class Observation(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 place:str=Field(pattern=r'^[A-Z0-9-]{2,20}$')
 name:str=Field(min_length=1,max_length=120)
 period:str=Field(pattern=r'^\d{4}(?:-\d{2})?$')
 value:float|None=None
 rank:int|None=Field(default=None,ge=1,le=10000)
 group:str=Field(default='countries',max_length=80)
 status:Literal['reported','estimate','provisional','revised','advance estimate','forecast']='reported'

class ReleaseInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 metric_id:str
 source_url:str=Field(max_length=500)
 edition:str=Field(min_length=1,max_length=150)
 reference_period:str=Field(pattern=r'^\d{4}(?:-\d{2})?$')
 methodology:str=Field(min_length=8,max_length=500)
 publisher_date:str|None=None
 note:str=Field(default='',max_length=2000)
 upstream_hash:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
 rows:list[Observation]=Field(min_length=1,max_length=25000)
 @model_validator(mode='after')
 def valid(self):
  m=METRICS.get(self.metric_id)
  if not m:raise ValueError('Unknown metric')
  # Exact, allowlisted source origins and paths. Never accept arbitrary URLs.
  from urllib.parse import urlparse
  src=urlparse(self.source_url)
  allowed={'world-bank':('api.worldbank.org','data.worldbank.org'),'undp':('hdr.undp.org',),'niti':('www.niti.gov.in',),'henley':('www.henleyglobal.com',)}[m['source_id']]
  if src.scheme!='https' or src.hostname not in allowed or src.username or src.password:raise ValueError('Use an approved HTTPS publisher source')
  keys=[(r.place,r.period,r.group) for r in self.rows]
  if len(keys)!=len(set(keys)):raise ValueError('Duplicate place, period and group')
  if m['kind']=='indicator' and any(r.rank is not None for r in self.rows):raise ValueError('Indicator ranks are calculated, not publisher ranks')
  if m['scope']=='world' and any(r.group!='countries' for r in self.rows):raise ValueError('World releases require country/economy coverage')
  if m['scope']=='states' and any(r.group not in {'Larger states','Smaller states','Union Territories'} for r in self.rows):raise ValueError('Retain the report comparison group')
  if any(r.rank is not None and r.value is None for r in self.rows):raise ValueError('A ranked entry needs its score')
  if not any(r.value is not None for r in self.rows):raise ValueError('An entirely missing release cannot replace data')
  for period in [self.reference_period]+[r.period for r in self.rows]:
   if '-' in period and int(period[-2:])!=(int(period[:4])+1)%100:raise ValueError('Financial years must be consecutive')
  if any(len(r.period)!=len(self.reference_period) for r in self.rows):raise ValueError('Do not mix calendar and financial-year labels in one release')
  if any(r.period>self.reference_period for r in self.rows):raise ValueError('Observation follows the reference period')
  if self.publisher_date:
   from datetime import date
   if date.fromisoformat(self.publisher_date)>date.today():raise ValueError('Future publication date')
  for r in self.rows:
   if int(r.period[:4])>datetime.now(timezone.utc).year and r.status!='forecast':raise ValueError('Future observations must be labelled forecast')
   if r.value is None:continue
   if self.metric_id=='hdi' and not 0<=r.value<=1:raise ValueError('HDI outside 0–1')
   if self.metric_id in {'population','gdp','gdp-per-capita','life-expectancy','infant-mortality','passport','state-health'} and r.value<0:raise ValueError('Negative value outside this metric domain')
  return self

def canonical(data:ReleaseInput):
 obj=data.model_dump();obj['rows']=sorted(obj['rows'],key=lambda r:(r['group'],r['place'],r['period']))
 return obj

async def stage(data:ReleaseInput, automatic=False, bootstrap=False):
 payload=canonical(data);digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 async with cursor() as cur:
  await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('stats:'+data.metric_id,))
  await cur.execute('SELECT * FROM stats_releases WHERE metric_id=%s AND content_hash=%s',(data.metric_id,digest));old=await cur.fetchone()
  if old:return old['id'],False
  # A connector may not silently replace methodology or erase a large share of coverage.
  if automatic:
   if METRICS[data.metric_id]['source_id']!='world-bank':raise ValueError('This source requires review')
   await cur.execute("SELECT * FROM stats_releases WHERE metric_id=%s AND status='published' ORDER BY published_at DESC LIMIT 1",(data.metric_id,));prior=await cur.fetchone()
   if prior:
    before=prior['payload'];old_rows={(r['place'],r['period']):r['value'] for r in before['rows'] if r['value'] is not None}
    new_rows={(r['place'],r['period']):r['value'] for r in payload['rows'] if r['value'] is not None}
    if before['methodology']!=data.methodology or data.reference_period<prior['reference_period'] or len(new_rows)<len(old_rows)*.9:automatic=False
    for k,v in new_rows.items():
     p=old_rows.get(k)
     if p is not None and abs(v-p)>max(abs(p)*.25,1):automatic=False;break
  if bootstrap:
   from .stats_bootstrap import accepted
   if not accepted(data):raise ValueError('Release does not match the source-checked bootstrap contract')
  publish=automatic or bootstrap
  i='stat_'+uuid4().hex
  await cur.execute('''INSERT INTO stats_releases(id,metric_id,content_hash,source_url,edition,reference_period,methodology,payload,status,published_at,published_by)
   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,CASE WHEN %s THEN now() END,%s)''',
   (i,data.metric_id,digest,data.source_url,data.edition,data.reference_period,data.methodology,Jsonb(payload),'published' if publish else 'pending',publish,'source-checked-bootstrap' if bootstrap else 'validated-connector' if automatic else None))
 return i,True

async def decide(i,actor,decision,note):
 async with cursor() as cur:
  from .review_identity import require_role
  await require_role(cur,actor,roles=('owner',))
  await cur.execute('SELECT * FROM stats_releases WHERE id=%s FOR UPDATE',(i,));r=await cur.fetchone()
  if not r:raise HTTPException(404,'Release not found')
  if r['status']!='pending':raise HTTPException(409,'This release already has a decision')
  await cur.execute('UPDATE stats_releases SET status=%s,published_at=CASE WHEN %s THEN now() END,published_by=%s WHERE id=%s',('published' if decision=='publish' else 'rejected',decision=='publish',actor,i))
  await cur.execute('INSERT INTO stats_decisions(release_id,actor_id,decision,note) VALUES(%s,%s,%s,%s)',(i,actor,decision,note))

async def release(metric_id,release_id=None,place=None):
 if metric_id not in METRICS:raise HTTPException(404,'Metric not found')
 projection='*';params=(metric_id,release_id,release_id)
 if place:
  # The overview reads only its selected place, not every global time series.
  projection="""id,metric_id,source_url,edition,reference_period,methodology,fetched_at,published_at,
   jsonb_build_object('note',payload->'note','publisher_date',payload->'publisher_date',
    'rows',jsonb_path_query_array(payload,'$.rows[*] ? (@.place == $place)',jsonb_build_object('place',%s::text))) AS payload"""
  params=(place,)+params
 async with cursor() as cur:
  await cur.execute("SELECT "+projection+" FROM stats_releases WHERE metric_id=%s AND status='published' AND (%s::text IS NULL OR id=%s) ORDER BY published_at DESC,id DESC LIMIT 1",params)
  return await cur.fetchone()

async def freshness(metric_id):
 async with cursor() as cur:
  await cur.execute('SELECT succeeded_at,attempted_at,error FROM stats_checks WHERE metric_id=%s',(metric_id,));r=await cur.fetchone()
  await cur.execute('SELECT checked_at,error,needs_review FROM stats_source_watches WHERE source_id=%s',(METRICS[metric_id]['source_id'],));watch=await cur.fetchone()
 source=SOURCES[METRICS[metric_id]['source_id']]
 checked=r['succeeded_at'] if r else None
 delayed=bool((watch and watch['error']) or (r and (r['error'] or checked and (datetime.now(timezone.utc)-checked).days>source['max_age_days'])))
 return {'last_checked_at':checked,'delayed':delayed,'message':'Update check delayed. Showing the last published release.' if delayed else None}

def metadata(r):
 return {k:r[k] for k in ('id','edition','reference_period','source_url','methodology','fetched_at','published_at')} | {'publisher_date':r['payload'].get('publisher_date'),'note':r['payload'].get('note','')}

def select_rows(r,period=None,group=None):
 rows=r['payload']['rows'];period=period or max(x['period'] for x in rows)
 return [x.copy() for x in rows if x['period']==period and (not group or x['group']==group)],period
