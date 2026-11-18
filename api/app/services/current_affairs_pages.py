"""Fixed official public-page collectors; no search API or arbitrary URL fetching."""
import re
from datetime import datetime,timezone
from html import escape
from html.parser import HTMLParser
from urllib.parse import parse_qs,urljoin,urlsplit
from zoneinfo import ZoneInfo
import requests
from . import youtube_current_affairs as yt

PAGES={
 'pib-releases':{'title':'PIB national releases','url':'https://www.pib.gov.in/allRel.aspx?reg=1&lang=1'},
 'mizoram-dipr':{'title':'Mizoram DIPR releases','url':'https://dipr.mizoram.gov.in/'},
}
LIMIT=4_000_000
class Node:
 def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 def find(self,**attrs):
  if all(value in self.attrs.get(key,'').split() for key,value in attrs.items()):return self
  for child in self.children:
   if isinstance(child,Node):
    found=child.find(**attrs)
    if found:return found
 def walk(self):
  yield self
  for child in self.children:
   if isinstance(child,Node):yield from child.walk()
 def text(self,markup=False):
  if self.tag in {'script','style','iframe','form','nav','gallery'} or self.attrs.get('id')=='attachment-meta':return ''
  if self.tag=='br':return '<br/>' if markup else ' '
  if markup and self.tag=='tr':
   cells=[re.sub(r'\s+',' ',c.text()).strip() for c in self.children if isinstance(c,Node) and c.tag in {'td','th'}]
   return '<p>'+escape(' | '.join(cells))+'</p>'
  value=''.join(c.text(markup) if isinstance(c,Node) else escape(c) if markup else c for c in self.children)
  if self.tag in {'p','div','li','tr','h1','h2','h3'}:return '<p>'+value+'</p>' if markup else ' '+value+' '
  return value
class Tree(HTMLParser):
 def __init__(self,raw):
  super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.count=0
  if len(raw)>LIMIT:raise yt.PipelineError('Official page exceeds the byte limit')
  self.feed(raw.decode('utf-8-sig',errors='replace'))
 def handle_starttag(self,tag,attrs):
  self.count+=1
  if self.count>40000 or len(self.stack)>150:raise yt.PipelineError('Official page structure exceeds limits')
  node=Node(tag,attrs);self.stack[-1].children.append(node)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(node)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for index in range(len(self.stack)-1,0,-1):
   if self.stack[index].tag==tag:del self.stack[index:];break
 def handle_data(self,data):self.stack[-1].children.append(data)

def approved_url(value,feed_id,listing=False):
 u=urlsplit(value)
 host='dipr.mizoram.gov.in' if feed_id=='mizoram-dipr' else 'www.pib.gov.in'
 if feed_id not in PAGES or u.scheme!='https' or u.hostname not in ({host,'pib.gov.in'} if host=='www.pib.gov.in' else {host}) or u.username or u.password or u.port not in {None,443} or len(value)>1800 or any(c in value for c in '\r\n'):
  raise yt.PipelineError('Unexpected official page URL')
 if listing:
  if value!=PAGES[feed_id]['url']:raise yt.PipelineError('Unexpected official listing URL')
  return value
 if feed_id=='mizoram-dipr':
  if not re.fullmatch(r'/post/[a-zA-Z0-9_-]{1,400}',u.path) or u.query:raise yt.PipelineError('Unexpected DIPR article URL')
  return 'https://'+host+u.path
 query=parse_qs(u.query)
 if u.path not in {'/PressReleaseDetail.aspx','/PressReleasePage.aspx'} or set(query)-{'PRID','reg','lang'} or len(query.get('PRID',[]))!=1 or not re.fullmatch(r'\d{5,10}',query['PRID'][0]):raise yt.PipelineError('Unexpected PIB release URL')
 return 'https://www.pib.gov.in/PressReleaseDetail.aspx?PRID='+query['PRID'][0]+'&reg=1&lang=1'

def get_page(url,feed_id,listing=False):
 approved_url(url,feed_id,listing)
 try:
  with requests.get(url,timeout=(5,20),stream=True,allow_redirects=False,headers={'User-Agent':'Finna-Current-Affairs/1.0 (public official releases)'}) as response:
   if response.status_code!=200:raise yt.PipelineError('Official page returned HTTP '+str(response.status_code))
   data=[];size=0
   for chunk in response.iter_content(16384):
    size+=len(chunk)
    if size>LIMIT:raise yt.PipelineError('Official page exceeds the byte limit')
    data.append(chunk)
   return b''.join(data)
 except requests.RequestException:raise yt.PipelineError('Official page is unavailable') from None

def discover(raw,feed_id):
 tree=Tree(raw);links=[]
 for node in tree.root.walk():
  href=node.attrs.get('href','')
  if node.tag!='a' or not (href.startswith('/post/') if feed_id=='mizoram-dipr' else 'PressReleaseDetail.aspx?' in href):continue
  try:url=approved_url(urljoin(PAGES[feed_id]['url'],href),feed_id)
  except yt.PipelineError:continue
  if url not in links:links.append(url)
  if len(links)>=8:break
 if not links:raise yt.PipelineError('Official listing contains no approved article links; source structure may have changed')
 return links

def parse_article(raw,url,feed_id):
 from .current_affairs_sources import units
 url=approved_url(url,feed_id);root=Tree(raw).root
 if feed_id=='mizoram-dipr':
  title_node=root.find(**{'class':'post-title'});body=root.find(**{'class':'post-content'});date_node=root.find(**{'class':'post-meta'})
  raw_date=re.search(r'Dated:\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3})\s+(\d{2,4})\s+(\d{1,2}:\d{2}\s*[AP]M)',date_node.text() if date_node else '',re.I)
  if not raw_date:raise yt.PipelineError('DIPR article publication date is missing or changed')
  stamp=' '.join(raw_date.groups());published=datetime.strptime(stamp,'%d %b %y %I:%M %p' if len(raw_date[3])==2 else '%d %b %Y %I:%M %p')
  language='und'
 else:
  title_node=root.find(id='Titleh2');body=root.find(id='pibReleaseBody');date_node=root.find(id='PrDateTime')
  raw_date=re.search(r'(\d{1,2}\s+[A-Z]{3}\s+\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)',date_node.text() if date_node else '',re.I)
  if not raw_date:raise yt.PipelineError('PIB article publication date is missing or changed')
  stamp=raw_date[1];published=datetime.strptime(stamp.upper().replace('AM',' AM').replace('PM',' PM'),'%d %b %Y %I:%M %p');language='en'
 if not title_node or not body:raise yt.PipelineError('Official article title/body structure changed')
 title=re.sub(r'\s+',' ',title_node.text()).strip()
 if not 4<=len(title)<=1000:raise yt.PipelineError('Official article title is missing or oversized')
 cues=units(body.text(markup=True))
 if sum(len(c['text']) for c in cues)<100:raise yt.PipelineError('Official article has insufficient body evidence')
 return {'title':title,'source_url':url,'published_at':published.replace(tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc),'publication_raw':stamp,'timezone_basis':'Publisher omitted timezone; normalized using Asia/Kolkata (assumption recorded)','language':language,'cues':cues}

def fetch_articles(feed_id):
 links=discover(get_page(PAGES[feed_id]['url'],feed_id,listing=True),feed_id);rows=[]
 for url in links:
  try:
   target=url.replace('/PressReleaseDetail.aspx?','/PressReleasePage.aspx?') if feed_id=='pib-releases' else url
   rows.append(parse_article(get_page(target,feed_id),url,feed_id))
  except yt.PipelineError as error:rows.append({'source_url':url,'title':'Official release capture unavailable','collection_error':str(error)})
 return rows
