"""Bounded daily/weekly private briefs with version-bound original evidence."""
import hashlib,json,os,re
from datetime import datetime,time,timedelta,timezone
from uuid import uuid4
from zoneinfo import ZoneInfo
from psycopg.types.json import Jsonb
from . import youtube_current_affairs as yt

PROMPT_VERSION='brief-ca-1'
MAX_SOURCES=8
MAX_CHARS=80000
TOPICS=[('Mizoram',r'mizoram|aizawl|ropuiliani|lalduhoma'),('Economy',r'inflat|price index|gdp|budget|bank|monetary|fiscal|econom'),('Schemes and governance',r'scheme|policy|act\b|bill\b|cabinet|mission|yojana|constitution'),('Science and technology',r'science|space|satellite|research|technology|genome'),('Environment',r'climate|environment|forest|wildlife|biodiversity'),('International',r'international|bilateral|summit|united nations|treaty'),('Awards and sport',r'award|sports?|championship|medal')]

def relevance(source):
 text=source['title']+' '+source['cues'][0]['text'][:1200]
 topics=[name for name,pattern in TOPICS if re.search(pattern,text,re.I)]
 if source.get('feed_id')=='mizoram-dipr' and 'Mizoram' not in topics:topics.insert(0,'Mizoram')
 routine=bool(re.search(r'money market operations|reference rate|auction result|liquidity adjustment|traffic sp',source['title'],re.I))
 return {'topics':topics or ['General current affairs'],'priority':1 if routine else 5+min(len(topics),3),'basis':'Transparent keyword triage; source review still required','routine':routine}

def snapshot(candidates):
 selected=[];omitted=[];characters=0
 for source in sorted(candidates,key=lambda s:(-relevance(s)['priority'],-s['published_at'].timestamp(),s['id'])):
  size=sum(len(c['text']) for c in source['cues'])
  if len(selected)>=MAX_SOURCES or characters+size>MAX_CHARS:
   omitted.append({'id':source['id'],'kind':source['kind'],'reason':'Source-count or complete-evidence character limit'});continue
  selected.append(source);characters+=size
 units=[];seen={};sources=[]
 for source in selected:
  sources.append({key:source.get(key) for key in ['id','kind','title','source_url','content_hash','language','evidence_kind']}|{'published_at':source['published_at'].isoformat(),'relevance':relevance(source)})
  for cue in source['cues']:
   ref={'kind':source['kind'],'id':source['id'],'local_id':cue['id']}
   if 'start' in cue:ref['start']=cue['start']
   normalized=re.sub(r'\s+',' ',cue['text']).strip().casefold()
   # Short labels/table values need their original context. Combine substantial
   # exact prose only across different sources, retaining every local position.
   match=next((index for index in seen.get(normalized,[]) if not any(r['kind']==source['kind'] and r['id']==source['id'] for r in units[index]['source_refs'])),None) if len(normalized)>=100 and len(normalized.split())>=12 else None
   if match is None:
    match=len(units);units.append({'id':match,'text':cue['text'],'source_refs':[]});seen.setdefault(normalized,[]).append(match)
   units[match]['source_refs'].append(ref)
 return {'sources':sources,'units':units,'coverage':{'available_sources':len(candidates),'selected_sources':len(selected),'omitted':omitted,'exact_duplicate_passages':sum(len(s['cues']) for s in selected)-len(units),'selection_policy':'Exam-topic keyword triage, then newest publication; at most eight complete sources and 80,000 characters. Publication date does not establish an event/effective date.'}}

def prepare(conn,now=None):
 today=(now or datetime.now(timezone.utc)).astimezone(ZoneInfo('Asia/Kolkata')).date();results=[]
 for cadence,days in [('daily',1),('weekly',7)]:
  start=today-timedelta(days=days-1);lower=datetime.combine(start,time.min,ZoneInfo('Asia/Kolkata'));upper=datetime.combine(today+timedelta(days=1),time.min,ZoneInfo('Asia/Kolkata'))
  candidates=conn.execute('''SELECT i.id,i.feed_id,'official' AS kind,r.title,r.source_url,r.content_hash,r.published_at,r.cues,r.language,'official_release' AS evidence_kind
   FROM ca_source_items i JOIN ca_source_feeds f ON f.id=i.feed_id AND f.enabled JOIN ca_source_revisions r ON r.item_id=i.id AND r.content_hash=i.current_hash
   WHERE i.published_at>=%s AND i.published_at<%s ORDER BY i.published_at DESC,i.id LIMIT 100''',(lower,upper)).fetchall()
  candidates+=conn.execute('''SELECT v.id,'video' AS kind,v.title,t.content_hash,v.published_at,t.cues,t.language,t.evidence_kind
   FROM ca_youtube_videos v JOIN ca_youtube_channels c ON c.id=v.channel_id AND c.enabled JOIN ca_youtube_transcripts t ON t.video_id=v.id AND t.content_hash=v.transcript_hash
   WHERE v.published_at>=%s AND v.published_at<%s ORDER BY v.published_at DESC,v.id LIMIT 30''',(lower,upper)).fetchall()
  for candidate in candidates:
   if candidate['kind']=='video':candidate['source_url']=yt.source_url(candidate['id'])
  inputs=snapshot(candidates)
  if not inputs['sources']:continue
  inputs['coverage']['candidate_window']='Newest 100 official releases and 30 captured videos in the stated Asia/Kolkata publication-date window. This is not full news coverage.'
  digest=hashlib.sha256(json.dumps(inputs,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();brief_id='brief_'+cadence+'_'+today.isoformat()
  with conn.transaction():
   conn.execute('''INSERT INTO ca_briefs(id,cadence,period_start,period_end,current_hash) VALUES(%s,%s,%s,%s,%s)
    ON CONFLICT(id) DO UPDATE SET current_hash=excluded.current_hash,updated_at=CASE WHEN ca_briefs.current_hash<>excluded.current_hash THEN now() ELSE ca_briefs.updated_at END,
    status=CASE WHEN ca_briefs.current_hash<>excluded.current_hash THEN 'source_ready' ELSE ca_briefs.status END,
    next_attempt_at=CASE WHEN ca_briefs.current_hash<>excluded.current_hash THEN now() ELSE ca_briefs.next_attempt_at END,
    last_error=CASE WHEN ca_briefs.current_hash<>excluded.current_hash THEN NULL ELSE ca_briefs.last_error END''',(brief_id,cadence,start,today,digest))
   conn.execute('INSERT INTO ca_brief_inputs(brief_id,content_hash,payload) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(brief_id,digest,Jsonb(inputs)))
  results.append({'brief':brief_id,'status':'brief_collected','sources':len(inputs['sources'])})
 return results

def validate(payload,inputs):
 generated=yt.validate_generated(payload,inputs['units'])
 normalized=[re.sub(r'\W+','',f.text.casefold()) for f in generated.facts]
 if len(normalized)!=len(set(normalized)):raise yt.PipelineError('Brief contains duplicate facts; combine their source references')
 return generated

def save_draft(conn,brief,generated,model):
 result=conn.execute('''INSERT INTO ca_brief_drafts(id,brief_id,content_hash,model,prompt_version,payload) VALUES(%s,%s,%s,%s,%s,%s)
  ON CONFLICT(brief_id,content_hash,model,prompt_version) DO NOTHING RETURNING id''',('brief_draft_'+uuid4().hex,brief['id'],brief['current_hash'],model,PROMPT_VERSION,Jsonb(generated.model_dump()))).fetchone()
 if not result:result=conn.execute('SELECT id FROM ca_brief_drafts WHERE brief_id=%s AND content_hash=%s AND model=%s AND prompt_version=%s',(brief['id'],brief['current_hash'],model,PROMPT_VERSION)).fetchone()
 conn.execute("UPDATE ca_briefs SET status='draft_ready',last_error=NULL WHERE id=%s AND current_hash=%s",(brief['id'],brief['current_hash']))
 return result['id']

async def sources_current(cur,inputs,lock=False):
 for source in sorted(inputs['sources'],key=lambda s:(s['kind'],s['id'])):
  query='SELECT current_hash AS hash FROM ca_source_items WHERE id=%s' if source['kind']=='official' else 'SELECT transcript_hash AS hash FROM ca_youtube_videos WHERE id=%s'
  await cur.execute(query+(' FOR SHARE' if lock else ''),(source['id'],));row=await cur.fetchone()
  if not row or row['hash']!=source['content_hash']:return False
 return True
