"""Bounded official RSS inputs and immutable private evidence revisions."""
import hashlib,json,re
from datetime import timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit,urlunsplit
from uuid import uuid4
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo
import requests
from psycopg.types.json import Jsonb
from . import youtube_current_affairs as yt
from .current_affairs_pages import PAGES,fetch_articles

FEEDS={
 'rbi-press':{'title':'RBI press releases','url':'https://rbi.org.in/pressreleases_rss.xml'},
 'rbi-notifications':{'title':'RBI notifications','url':'https://rbi.org.in/notifications_rss.xml'},
}
FEEDS.update(PAGES)
PROMPT_VERSION='official-ca-1'

class Text(HTMLParser):
 def __init__(self,value):
  super().__init__(convert_charrefs=True);self.parts=[];self.blocked=0;self.feed(value)
 def handle_starttag(self,tag,attrs):
  if tag in {'script','style','iframe','form','nav'}:self.blocked+=1
  if not self.blocked and tag in {'p','br','div','li','tr','h1','h2','h3'}:self.parts.append('\n')
  if not self.blocked and tag in {'td','th'}:self.parts.append(' | ')
 def handle_endtag(self,tag):
  if tag in {'script','style','iframe','form','nav'}:self.blocked=max(0,self.blocked-1)
  if not self.blocked and tag in {'p','div','li','tr'}:self.parts.append('\n')
 def handle_data(self,text):
  if not self.blocked:self.parts.append(text)

def units(value):
 parser=Text(value);paragraphs=[re.sub(r'\s+',' ',p).strip() for p in ''.join(parser.parts).split('\n')]
 rows=[]
 for p in paragraphs:
  while p:
   cut=min(len(p),3500)
   if cut<len(p):cut=p.rfind(' ',0,cut) or cut
   text=p[:cut].strip();p=p[cut:].strip()
   if text:rows.append({'id':len(rows),'text':text})
 if not rows or len(rows)>500 or sum(len(r['text']) for r in rows)>yt.MAX_TRANSCRIPT_CHARS:raise yt.PipelineError('Official source text is empty or exceeds the bounded input limit')
 return rows

def official_url(value):
 u=urlsplit(value.strip())
 if u.scheme!='https' or u.hostname not in {'rbi.org.in','www.rbi.org.in'} or u.username or u.password or u.port not in {None,443} or len(value)>1800 or any(c in value for c in '\r\n'):raise yt.PipelineError('Unexpected official source URL in RBI feed')
 return urlunsplit(('https','rbi.org.in',u.path,u.query,''))

def parse_feed(raw):
 if len(raw)>1_500_000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise yt.PipelineError('Official feed exceeds limits or contains unsupported XML declarations')
 try:root=ET.fromstring(raw)
 except ET.ParseError:raise yt.PipelineError('Official feed is not valid RSS XML') from None
 if root.tag!='rss':raise yt.PipelineError('Official feed format changed; expected RSS')
 rows=[]
 for item in root.findall('./channel/item')[:50]:
  title=(item.findtext('title') or '').strip();url=official_url(item.findtext('link') or '')
  if not 4<=len(title)<=1000:raise yt.PipelineError('Official source title is missing or oversized')
  raw_date=(item.findtext('pubDate') or '').strip()
  try:published=parsedate_to_datetime(raw_date)
  except (ValueError,TypeError):raise yt.PipelineError('Official source publication date is missing or invalid') from None
  basis='Publisher-supplied timezone'
  if published.tzinfo is None:published=published.replace(tzinfo=ZoneInfo('Asia/Kolkata'));basis='Publisher omitted timezone; normalized using Asia/Kolkata (assumption recorded)'
  body=item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or item.findtext('description') or ''
  row={'title':title,'source_url':url,'published_at':published.astimezone(timezone.utc),'publication_raw':raw_date,'timezone_basis':basis}
  try:row['cues']=units(body)
  except yt.PipelineError as error:row['collection_error']=str(error)
  rows.append(row)
 if not rows:raise yt.PipelineError('Official feed returned no entries; collection is not current merely because HTTP succeeded')
 return rows

def fetch_feed(feed_id):
 if feed_id not in FEEDS:raise yt.ConfigurationError('This source feed is not approved')
 if feed_id in PAGES:return fetch_articles(feed_id)
 try:
  with requests.get(FEEDS[feed_id]['url'],timeout=(5,25),allow_redirects=False,stream=True) as response:
   if response.status_code!=200:raise yt.PipelineError('Official source feed returned HTTP '+str(response.status_code))
   chunks=[];size=0
   for chunk in response.iter_content(16384):
    size+=len(chunk)
    if size>1_500_000:raise yt.PipelineError('Official source feed exceeds the byte limit')
    chunks.append(chunk)
  return parse_feed(b''.join(chunks))
 except requests.RequestException:raise yt.PipelineError('Official source feed is unavailable') from None

def source_hash(row):
 value={k:row[k] for k in ['title','source_url','publication_raw','timezone_basis','cues']}
 if row.get('language'):value['language']=row['language']
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def event(conn,item_id,action,detail=None,actor='current-affairs-worker'):
 conn.execute('INSERT INTO ca_source_events(item_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(item_id,actor,action,Jsonb(detail or {})))

def save_item(conn,feed_id,row):
 digest=source_hash(row);item_id='src_'+hashlib.sha256((feed_id+'\n'+row['source_url']).encode()).hexdigest()[:32]
 with conn.transaction():
  old=conn.execute('SELECT current_hash FROM ca_source_items WHERE id=%s FOR UPDATE',(item_id,)).fetchone()
  conn.execute('''INSERT INTO ca_source_items(id,feed_id,source_url,title,published_at,current_hash) VALUES(%s,%s,%s,%s,%s,%s)
   ON CONFLICT(id) DO UPDATE SET title=excluded.title,published_at=excluded.published_at,current_hash=excluded.current_hash,last_seen_at=now(),
   status=CASE WHEN ca_source_items.current_hash<>excluded.current_hash THEN 'source_ready' ELSE ca_source_items.status END,
   next_attempt_at=CASE WHEN ca_source_items.current_hash<>excluded.current_hash THEN now() ELSE ca_source_items.next_attempt_at END,
   last_error=CASE WHEN ca_source_items.current_hash<>excluded.current_hash THEN NULL ELSE ca_source_items.last_error END''',(item_id,feed_id,row['source_url'],row['title'],row['published_at'],digest))
  conn.execute('''INSERT INTO ca_source_revisions(item_id,content_hash,title,source_url,published_at,publication_raw,timezone_basis,cues,language)
   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',(item_id,digest,row['title'],row['source_url'],row['published_at'],row['publication_raw'],row['timezone_basis'],Jsonb(row['cues']),row.get('language','en')))
  if not old or old['current_hash']!=digest:event(conn,item_id,'source_captured',{'hash':digest,'source_verified':False,'timezone_basis':row['timezone_basis']})
 return item_id

def collect(conn):
 results=[]
 for feed in conn.execute('SELECT * FROM ca_source_feeds WHERE enabled ORDER BY id').fetchall():
  try:
   rows=fetch_feed(feed['id'])
   if not rows:raise yt.PipelineError('Official feed returned no items; earlier captured sources are retained')
   rejected=0
   for row in rows:
    if row.get('collection_error'):
     rejected+=1;event(conn,None,'source_capture_rejected',{'feed_id':feed['id'],'source_url':row['source_url'],'title':row['title'],'error':row['collection_error']})
    else:save_item(conn,feed['id'],row)
   if rejected==len(rows):raise yt.PipelineError('All releases exceeded source input limits or had no usable text; earlier evidence retained')
   message=str(rejected)+' releases could not be captured; see private source audit' if rejected else None
   conn.execute('UPDATE ca_source_feeds SET checked_at=now(),last_error=%s WHERE id=%s',(message,feed['id']))
   result={'source':feed['id'],'status':'source_partial' if rejected else 'source_ready','items':len(rows)-rejected}
   if rejected:result['rejected']=rejected
   results.append(result)
  except Exception as error:
   message=str(error) if isinstance(error,yt.PipelineError) else 'Official source input could not be processed'
   conn.execute('UPDATE ca_source_feeds SET last_error=%s WHERE id=%s',(message[:700],feed['id']))
   results.append({'source':feed['id'],'status':'feed_failed','error':message[:700]})
 return results

def save_draft(conn,item,draft,model):
 draft_id='source_draft_'+uuid4().hex
 with conn.transaction():
  result=conn.execute('''INSERT INTO ca_source_drafts(id,item_id,content_hash,prompt_version,model,payload)
   VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(item_id,content_hash,prompt_version,model) DO UPDATE SET item_id=excluded.item_id RETURNING id''',(draft_id,item['id'],item['current_hash'],PROMPT_VERSION,model,Jsonb(draft.model_dump()))).fetchone()
  conn.execute("UPDATE ca_source_items SET status='draft_ready',last_error=NULL WHERE id=%s AND current_hash=%s",(item['id'],item['current_hash']))
  event(conn,item['id'],'draft_staged',{'id':result['id'],'model':model,'hash':item['current_hash'],'source_verified':False})
 return result['id']
