"""Bounded official-source fetches, complete pagination and auditable import runs."""
import asyncio
import csv
import io
import random
import time
import hashlib
from datetime import date
import requests
from ..db import cursor
from .stats_catalog import METRICS, HDI_URL, SOURCES
from .stats import ReleaseInput, stage

class SourceError(ValueError):pass
class SourceUnavailable(SourceError):pass

RETRY_ATTEMPTS = 4
RETRY_BASE_SECONDS = 1.5
SECOND_PASS_DELAY_SECONDS = 8.0

def fetch(url,params=None):
 last=None
 for attempt in range(RETRY_ATTEMPTS):
  if attempt:
   delay = RETRY_BASE_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 1.2)
   time.sleep(delay)
  try:
   r=requests.get(url,params=params,timeout=(10,45),allow_redirects=False)
   if r.status_code in (429,500,502,503,504):
    raise requests.HTTPError(f'Transient provider HTTP {r.status_code}',response=r)
   r.raise_for_status()
   if r.status_code!=200:raise SourceError('Unexpected provider redirect/status')
   if len(r.content)>25_000_000:raise SourceError('Source response exceeds size limit')
   return r
  except requests.RequestException as e:last=e
 raise SourceUnavailable(f'Official source unavailable after {RETRY_ATTEMPTS} attempts') from last

def wb_pages(path,extra=None):
 last=None
 for size in (5000,1000,500):
  try:return _wb_pages_size(path,extra,size)
  except SourceUnavailable as e:
   # Some provider/CDN responses fail for one page size. Restart the complete
   # request with smaller pages; never combine a partial failed fetch.
   last=e
 raise last

def _wb_pages_size(path,extra,size):
 rows=[];expected=None;edition=None
 for page in range(1,21):
  body=fetch('https://api.worldbank.org/v2/'+path,{'format':'json','per_page':size,'page':page,**(extra or {})}).json()
  if not isinstance(body,list) or len(body)!=2 or not isinstance(body[0],dict) or not isinstance(body[1],list):raise SourceError('World Bank schema changed')
  meta=body[0]
  if expected is None:expected=int(meta['total']);edition=meta.get('lastupdated')
  if meta.get('lastupdated')!=edition:raise SourceError('World Bank edition changed mid-fetch')
  if int(meta['total'])!=expected or int(meta['page'])!=page:raise SourceError('World Bank pagination changed mid-fetch')
  rows.extend(body[1])
  if page>=int(meta['pages']):
   if len(rows)!=expected:raise SourceError('World Bank pagination incomplete')
   return rows,meta
 raise SourceError('World Bank pagination exceeds import limit')

def world_bank(metric_id,countries):
 m=METRICS[metric_id]
 if m['source_id']!='world-bank':raise SourceError('Not a World Bank metric')
 # Fixed lower bound keeps historical coverage stable across annual refreshes.
 raw,meta=wb_pages('country/all/indicator/'+m['code'],{'source':2,'date':f'2010:{date.today().year}'})
 rows=[]
 for x in raw:
  code=x.get('countryiso3code')
  if code not in countries:continue  # excludes regional and income aggregates
  if x.get('indicator',{}).get('id')!=m['code']:raise SourceError('Provider returned another indicator')
  rows.append(dict(place=code,name=countries[code],period=x['date'],value=x['value']))
 if not rows or not any(x['place']=='IND' and x['value'] is not None for x in rows):raise SourceError('India observations missing')
 period=max(x['period'] for x in rows if x['value'] is not None)
 rows=[x for x in rows if x['period']<=period]  # drop future null placeholders
 return ReleaseInput(metric_id=metric_id,source_url='https://api.worldbank.org/v2/country/all/indicator/'+m['code'],edition='World Development Indicators',reference_period=period,methodology=m['methodology'],note='Country/economy observations only. Regional and income aggregates are excluded. Revisions to historical values are preserved in separate releases.',rows=rows)

def hdi():
 content=fetch(HDI_URL).content
 # Official CSV contains Latin-1 country names in the current release.
 try:text=content.decode('utf-8-sig')
 except UnicodeDecodeError:text=content.decode('cp1252')
 reader=csv.DictReader(io.StringIO(text));fields=reader.fieldnames or []
 years=[f.removeprefix('hdi_') for f in fields if f.startswith('hdi_') and f[4:].isdigit()]
 if not years:raise SourceError('HDI year columns missing')
 latest=max(years);rank_key='hdi_rank_'+latest;rows=[]
 if rank_key not in fields:raise SourceError('HDI publisher rank missing')
 for x in reader:
  code=x.get('iso3','')
  if len(code)!=3 or not code.isupper():continue
  # Dataset also contains aggregate rows. Only assessed countries have a rank.
  rank=x.get(rank_key,'').strip()
  if not rank or rank in {'..','NA'}:continue
  for year in years:
   value=x.get('hdi_'+year,'').strip()
   rows.append(dict(place=code,name=x['country'],period=year,value=float(value) if value and value not in {'..','NA'} else None,rank=int(float(rank)) if year==latest else None))
 return ReleaseInput(upstream_hash=hashlib.sha256(content).hexdigest(),metric_id='hdi',source_url=HDI_URL,edition='Human Development Report 2025',reference_period=latest,methodology=METRICS['hdi']['methodology'],note='Publisher ranks are supplied for the latest reference year only. Historical scores use this edition’s revised series.',rows=rows)

async def run_import(metric_id,build,automatic=False,bootstrap=False):
 async with cursor() as cur:
  await cur.execute('INSERT INTO stats_import_runs(metric_id,status) VALUES(%s,\'running\') RETURNING id',(metric_id,));run=(await cur.fetchone())['id']
  await cur.execute('INSERT INTO stats_checks(metric_id) VALUES(%s) ON CONFLICT(metric_id) DO UPDATE SET attempted_at=now()',(metric_id,))
 try:
  body=await asyncio.to_thread(build)
  i,created=await stage(body,automatic=automatic,bootstrap=bootstrap)
  async with cursor() as cur:
   await cur.execute('SELECT status FROM stats_releases WHERE id=%s',(i,));status=(await cur.fetchone())['status']
   await cur.execute("UPDATE stats_checks SET succeeded_at=now(),error=NULL WHERE metric_id=%s",(metric_id,))
   await cur.execute('UPDATE stats_import_runs SET finished_at=now(),status=%s,release_id=%s WHERE id=%s',(status if created else 'unchanged',i,run))
  return {'metric':metric_id,'id':i,'status':status,'changed':created}
 except Exception as e:
  # Store bounded errors without provider credentials or response bodies.
  error=type(e).__name__+': '+str(e)[:250]
  async with cursor() as cur:
   await cur.execute('UPDATE stats_checks SET error=%s WHERE metric_id=%s',(error,metric_id))
   await cur.execute("UPDATE stats_import_runs SET finished_at=now(),status='failed',error=%s WHERE id=%s",(error,run))
  return {'metric':metric_id,'status':'failed','error':error}

async def refresh(include_hdi=False):
 try:
  raw,_=await asyncio.to_thread(wb_pages,'country')
  countries={x['id']:x['name'] for x in raw if x.get('region',{}).get('id') not in {'NA',None}}
 except Exception:
  def unavailable():raise SourceError('Country coverage lookup failed; no series were replaced')
  return [await run_import(m['id'],unavailable) for m in METRICS.values() if m['source_id']=='world-bank']
 results=[]
 wb_metrics=[m['id'] for m in METRICS.values() if m['source_id']=='world-bank']
 for mid in wb_metrics:
  results.append(await run_import(mid,lambda i=mid:world_bank(i,countries),True))
 # Second-pass self-healing retry for transient World Bank CDN blips.
 transient_indices=[
  idx for idx,r in enumerate(results)
  if r.get('status')=='failed' and 'SourceUnavailable' in (r.get('error') or '')
 ]
 if transient_indices:
  if SECOND_PASS_DELAY_SECONDS > 0:
   await asyncio.sleep(SECOND_PASS_DELAY_SECONDS)
  for idx in transient_indices:
   mid=results[idx]['metric']
   retry_res=await run_import(mid,lambda i=mid:world_bank(i,countries),True)
   retry_res['retried']=True
   results[idx]=retry_res
 if include_hdi:results.append(await run_import('hdi',hdi,False))
 return results


async def watch_sources():
 results=[]
 for source_id in ('undp','niti','survey'):
  try:
   response=await asyncio.to_thread(fetch,SOURCES[source_id].get('watch_url',SOURCES[source_id]['url']))
   # Hash the relevant official links, not rotating site navigation or timestamps.
   from html.parser import HTMLParser
   from urllib.parse import urljoin
   class Links(HTMLParser):
    def __init__(self):super().__init__();self.href=None;self.label='';self.items=[]
    def handle_starttag(self,tag,attrs):
     if tag=='a':self.href=dict(attrs).get('href');self.label=''
    def handle_data(self,data):
     if self.href:self.label+=data
    def handle_endtag(self,tag):
     if tag=='a' and self.href:
      if any(x in self.href.lower() for x in ('.pdf','.csv','.xlsx','dataprism','prism.hdrdata')):
       self.items.append(' '.join(self.label.split())+' | '+urljoin(SOURCES[source_id]['url'],self.href))
      self.href=None
   parsed=Links();parsed.feed(response.text);links=sorted(set(parsed.items))
   if not links:raise SourceError('No official release links found; source mapping needs inspection')
   digest=hashlib.sha256(('\n'.join(links)).encode()).hexdigest()
   async with cursor() as cur:
    await cur.execute("""INSERT INTO stats_source_watches(source_id,content_hash,checked_at,links) VALUES(%s,%s,now(),%s)
     ON CONFLICT(source_id) DO UPDATE SET checked_at=now(),error=NULL,
     needs_review=stats_source_watches.needs_review OR (stats_source_watches.content_hash IS NOT NULL AND stats_source_watches.content_hash<>excluded.content_hash),
     content_hash=excluded.content_hash,links=excluded.links""",(source_id,digest,__import__('psycopg').types.json.Jsonb(links)))
   results.append({'source':source_id,'status':'checked'})
  except Exception as e:
   error=type(e).__name__+': '+str(e)[:250]
   async with cursor() as cur:
    await cur.execute("INSERT INTO stats_source_watches(source_id,error) VALUES(%s,%s) ON CONFLICT(source_id) DO UPDATE SET error=excluded.error",(source_id,error))
   results.append({'source':source_id,'status':'failed','error':error})
 return results
