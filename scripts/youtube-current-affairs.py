#!/usr/bin/env python3
"""Bounded YouTube automation operator. Generated content remains private drafts."""
import argparse, json, os, sys, time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from app.services import youtube_current_affairs as yt
from app.services import current_affairs_sources as sources,current_affairs_providers as providers
from app.services import current_affairs_briefs as briefs

def connect():
 if os.environ.get('DATABASE_URL'):return psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,row_factory=dict_row)
 return psycopg.connect(autocommit=True,row_factory=dict_row)

def event(conn,vid,action,detail=None,actor='youtube-worker'):
 conn.execute('INSERT INTO ca_youtube_events(video_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(vid,actor,action,Jsonb(detail or {})))

def add_metadata(conn,value):
 vid=yt.video_id(value['id']);cid=value.get('channel_id','')
 if not yt.CHANNEL_RE.fullmatch(cid):raise ValueError('Metadata must identify a real YouTube channel ID')
 title=str(value.get('title','')).strip();channel=str(value.get('channel','')).strip()
 if not title or len(title)>1000 or not channel or len(channel)>300:raise ValueError('Missing or oversized video/channel title')
 if value.get('timestamp'):
  published=datetime.fromtimestamp(value['timestamp'],timezone.utc);precision='timestamp'
 else:published=datetime.strptime(value['upload_date'],'%Y%m%d').replace(tzinfo=timezone.utc);precision='day'
 with conn.transaction():
  conn.execute('INSERT INTO ca_youtube_channels(id,title) VALUES(%s,%s) ON CONFLICT(id) DO UPDATE SET title=excluded.title',(cid,channel))
  conn.execute('INSERT INTO ca_youtube_videos(id,channel_id,title,published_at,published_precision) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',(vid,cid,title,published,precision))
  event(conn,vid,'video_registered',{'source':'operator-supplied downloader metadata','channel_id':cid})
 return vid

def save_transcript(conn,vid,cues,language,automatic,provider,evidence_kind='captions'):
 digest=yt.transcript_hash(cues)
 with conn.transaction():
  conn.execute('INSERT INTO ca_youtube_transcripts(video_id,content_hash,language,automatic,provider,cues,evidence_kind) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',(vid,digest,language,automatic,provider,Jsonb(cues),evidence_kind))
  conn.execute("UPDATE ca_youtube_videos SET transcript_hash=%s,status='transcript_ready',last_error=NULL,updated_at=now() WHERE id=%s",(digest,vid))
  event(conn,vid,'transcript_saved',{'hash':digest,'language':language,'automatic':automatic,'provider':provider,'cues':len(cues)})
 return digest

def save_generated(conn,vid,digest,generated,model,prompt_version=yt.PROMPT_VERSION):
 payload=generated.model_dump();draft='yt_draft_'+uuid4().hex
 with conn.transaction():
  row=conn.execute('''INSERT INTO ca_youtube_drafts(id,video_id,transcript_hash,prompt_version,model,payload)
   VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(video_id,transcript_hash,prompt_version,model) DO UPDATE SET video_id=excluded.video_id RETURNING id''',(draft,vid,digest,prompt_version,model,Jsonb(payload))).fetchone()
  conn.execute("UPDATE ca_youtube_videos SET status='draft_ready',last_error=NULL,updated_at=now() WHERE id=%s",(vid,))
  event(conn,vid,'draft_staged',{'id':row['id'],'model':model,'prompt_version':prompt_version,'source_verified':False})
 return row['id']

def reserve_generation(conn,calls,model,vid=None,item_id=None,brief_id=None,deadline=None):
 if deadline is not None and time.monotonic()>deadline-160:raise yt.ProviderDeferred('Worker time budget is nearly exhausted; generation remains queued for the next run')
 try:cap=max(0,min(20,int(os.environ.get('CA_DAILY_CALL_LIMIT','6'))))
 except ValueError:raise yt.ConfigurationError('Invalid generation attempt limit') from None
 count=conn.execute("SELECT count(*) AS n FROM ca_youtube_generation_calls WHERE started_at>now()-interval '24 hours'").fetchone()['n']
 if count>=cap:raise yt.ProviderDeferred('The rolling 24-hour generation attempt limit has been reached; queued for a later retry')
 calls.append(conn.execute('INSERT INTO ca_youtube_generation_calls(video_id,source_item_id,brief_id,model) VALUES(%s,%s,%s,%s) RETURNING id',(vid,item_id,brief_id,model)).fetchone()['id'])

def finish_calls(conn,calls,success):
 for call in calls:conn.execute('UPDATE ca_youtube_generation_calls SET status=%s WHERE id=%s',('succeeded' if success and call==calls[-1] else 'failed',call))

def run(conn,limit=3,collect_only=False):
 if not conn.execute('SELECT pg_try_advisory_lock(1508202601) AS locked').fetchone()['locked']:return {'status':'already_running'}
 run_id=conn.execute('INSERT INTO ca_youtube_runs DEFAULT VALUES RETURNING id').fetchone()['id'];results=[];provider_deferred=False;deadline=time.monotonic()+720
 try:
  results.extend(sources.collect(conn))
  channels=[] if collect_only else conn.execute('SELECT * FROM ca_youtube_channels WHERE enabled ORDER BY id').fetchall()
  for channel in channels:
   try:
    rows=yt.fetch_feed(channel['id'])
    with conn.transaction():
     for row in rows:
      conn.execute('INSERT INTO ca_youtube_videos(id,channel_id,title,published_at) VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET title=excluded.title',(row['id'],row['channel_id'],row['title'],row['published_at']))
     conn.execute('UPDATE ca_youtube_channels SET checked_at=now(),last_error=NULL WHERE id=%s',(channel['id'],))
   except Exception as error:
    conn.execute('UPDATE ca_youtube_channels SET last_error=%s WHERE id=%s',(safe_error(error),channel['id']));results.append({'channel':channel['id'],'status':'feed_failed','error':safe_error(error)})
  brief_slot=int(os.environ.get('CA_BRIEFS_ENABLED','1')=='1' and yt.generation_config()['configured'] and not collect_only)
  video_slots=max(0,limit-1-brief_slot) if os.environ.get('CA_SOURCE_GENERATION_ENABLED')=='1' else max(0,limit-brief_slot)
  videos=[] if collect_only or not video_slots else conn.execute("SELECT v.*,c.languages FROM ca_youtube_videos v JOIN ca_youtube_channels c ON c.id=v.channel_id WHERE c.enabled AND v.status<>'draft_ready' AND v.next_attempt_at<=now() ORDER BY v.published_at DESC,v.id LIMIT %s",(video_slots,)).fetchall()
  for video in videos:
   vid=video['id'];calls=[];caption_calls=[]
   try:
    before_call=lambda model:reserve_generation(conn,calls,model,vid=vid,deadline=deadline)
    row=conn.execute('SELECT * FROM ca_youtube_transcripts WHERE video_id=%s AND content_hash=%s',(vid,video['transcript_hash'])).fetchone()
    if (not row or video['status']=='transcript_pending') and os.environ.get('CA_VIDEO_INPUT')=='gemini_url':
     cues,generated,model=providers.gemini_video(vid,video['title'],video['published_at'].isoformat(),before_call)
     with conn.transaction():
      digest=save_transcript(conn,vid,cues,'en',None,'Gemini video analysis','model_video_analysis')
      draft=save_generated(conn,vid,digest,generated,model,'yt-video-ca-1')
    else:
     if not row or video['status']=='transcript_pending':
      conn.execute("UPDATE ca_youtube_videos SET attempts=attempts+1,status='transcript_pending',updated_at=now() WHERE id=%s",(vid,))
      caption_provider=os.environ.get('CA_CAPTION_PROVIDER','yt-dlp')
      if caption_provider=='supadata':
       def before_caption():
        _,cap=providers.supadata_settings()
        used=conn.execute("SELECT coalesce(sum(reserved_credits),0) AS n FROM ca_caption_calls WHERE started_at>=date_trunc('month',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'").fetchone()['n']
        if used>=cap:raise yt.CaptionDeferred('Supadata monthly native-caption budget reached; no upgrade attempted')
        caption_calls.append(conn.execute('INSERT INTO ca_caption_calls(video_id) VALUES(%s) RETURNING id',(vid,)).fetchone()['id'])
       cues,language,automatic=providers.supadata_captions(vid,video['languages'],before_caption);method='Supadata native captions (original caption type not reported)'
      elif caption_provider=='yt-dlp':cues,language,automatic=yt.fetch_captions(vid,video['languages']);method='yt-dlp public captions'
      else:raise yt.ConfigurationError('Unknown caption provider; no fallback attempted')
      digest=save_transcript(conn,vid,cues,language,automatic,method)
      for call in caption_calls:conn.execute("UPDATE ca_caption_calls SET status='succeeded' WHERE id=%s",(call,))
     else:cues=row['cues'];digest=row['content_hash']
     generated,model,_=yt.generate(video['title'],video['published_at'].isoformat(),cues,before_call)
     draft=save_generated(conn,vid,digest,generated,model)
    finish_calls(conn,calls,True)
    for call in caption_calls:conn.execute("UPDATE ca_caption_calls SET status='succeeded' WHERE id=%s",(call,))
    results.append({'video':vid,'status':'draft_ready','draft':draft})
   except Exception as error:
    finish_calls(conn,calls,False)
    for call in caption_calls:conn.execute("UPDATE ca_caption_calls SET status='failed' WHERE id=%s AND status='started'",(call,))
    state='quota_wait' if isinstance(error,yt.ProviderDeferred) else 'needs_configuration' if isinstance(error,yt.ConfigurationError) else 'transcript_pending' if isinstance(error,yt.CaptionUnavailable) else 'generation_failed'
    delay=6 if isinstance(error,yt.ProviderDeferred) else min(24,2**min(video['attempts']+1,5))
    conn.execute("UPDATE ca_youtube_videos SET status=%s,last_error=%s,next_attempt_at=now()+(%s * interval '1 hour'),updated_at=now() WHERE id=%s",(state,safe_error(error),delay,vid))
    event(conn,vid,state,{'error':safe_error(error),'retry_hours':delay});results.append({'video':vid,'status':state,'error':safe_error(error)})
    if isinstance(error,yt.ProviderDeferred):provider_deferred=not isinstance(error,yt.CaptionDeferred);break
  if not collect_only and not provider_deferred and os.environ.get('CA_SOURCE_GENERATION_ENABLED')=='1':
   items=conn.execute("SELECT i.*,r.cues FROM ca_source_items i JOIN ca_source_feeds f ON f.id=i.feed_id JOIN ca_source_revisions r ON r.item_id=i.id AND r.content_hash=i.current_hash WHERE f.enabled AND i.status<>'draft_ready' AND i.next_attempt_at<=now() ORDER BY i.published_at DESC,i.id LIMIT %s",(max(0,limit-len(videos)-brief_slot),)).fetchall()
   for item in items:
    calls=[]
    try:
     if sum(len(c['text']) for c in item['cues'])<80:raise yt.PipelineError('Source text is too short for supported study questions')
     generated,model,_=yt.generate(item['title'],item['published_at'].isoformat(),item['cues'],lambda model:reserve_generation(conn,calls,model,item_id=item['id'],deadline=deadline),source_kind='official_release')
     draft=sources.save_draft(conn,item,generated,model);finish_calls(conn,calls,True);results.append({'item':item['id'],'status':'draft_ready','draft':draft})
    except Exception as error:
     finish_calls(conn,calls,False);state='quota_wait' if isinstance(error,yt.ProviderDeferred) else 'needs_configuration' if isinstance(error,yt.ConfigurationError) else 'generation_failed'
     conn.execute("UPDATE ca_source_items SET status=%s,last_error=%s,next_attempt_at=now()+interval '6 hours' WHERE id=%s",(state,safe_error(error),item['id']))
     sources_event={'error':safe_error(error),'source_verified':False}
     conn.execute('INSERT INTO ca_source_events(item_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(item['id'],'current-affairs-worker',state,Jsonb(sources_event)))
     results.append({'item':item['id'],'status':state,'error':safe_error(error)})
     if isinstance(error,yt.ProviderDeferred):provider_deferred=True;break
  if os.environ.get('CA_BRIEFS_ENABLED','1')=='1':
   results.extend(briefs.prepare(conn))
   if brief_slot and not provider_deferred:
    job=conn.execute('''SELECT b.*,i.payload AS inputs FROM ca_briefs b JOIN ca_brief_inputs i ON i.brief_id=b.id AND i.content_hash=b.current_hash
     WHERE b.status<>'draft_ready' AND b.next_attempt_at<=now() AND b.period_end>=(now() AT TIME ZONE 'Asia/Kolkata')::date-1
     ORDER BY (SELECT max(d.created_at) FROM ca_brief_drafts d WHERE d.brief_id=b.id) ASC NULLS FIRST,b.period_end DESC,b.cadence,b.id LIMIT 1''').fetchone()
    if job:
     calls=[]
     try:
      generated,model,_=yt.generate(job['cadence'].title()+' current affairs '+str(job['period_end']),str(job['period_end']),job['inputs']['units'],lambda model:reserve_generation(conn,calls,model,brief_id=job['id'],deadline=deadline),source_kind='multi_source_'+job['cadence']+'_brief')
      generated=briefs.validate(generated.model_dump(),job['inputs']);draft=briefs.save_draft(conn,job,generated,model);finish_calls(conn,calls,True)
      results.append({'brief':job['id'],'status':'draft_ready','draft':draft})
     except Exception as error:
      finish_calls(conn,calls,False);state='quota_wait' if isinstance(error,yt.ProviderDeferred) else 'needs_configuration' if isinstance(error,yt.ConfigurationError) else 'generation_failed'
      conn.execute("UPDATE ca_briefs SET status=%s,last_error=%s,next_attempt_at=now()+interval '6 hours' WHERE id=%s",(state,safe_error(error),job['id']))
      sources.event(conn,None,'brief_'+state,{'brief_id':job['id'],'error':safe_error(error)})
      results.append({'brief':job['id'],'status':state,'error':safe_error(error)})
  status='partial' if any(x['status'] not in {'draft_ready','source_ready','brief_collected'} for x in results) else 'succeeded'
  conn.execute('UPDATE ca_youtube_runs SET status=%s,finished_at=now(),summary=%s WHERE id=%s',(status,Jsonb({'results':results,'generation':yt.generation_config(),'providers':providers.public_config(),'collect_only':collect_only}),run_id))
  return {'status':status,'run_id':run_id,'results':results}
 except BaseException:
  conn.execute("UPDATE ca_youtube_runs SET status='failed',finished_at=now() WHERE id=%s",(run_id,));raise
 finally:conn.execute('SELECT pg_advisory_unlock(1508202601)')

def safe_error(error):
 if isinstance(error,yt.PipelineError):return str(error)[:700]
 # Requests/downloader exceptions may embed credentials or signed URLs.
 return type(error).__name__+': the source request or stored input could not be processed'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--metadata-file',help='Register one video from yt-dlp --dump-single-json output')
 parser.add_argument('--video',help='Existing video ID, for a supplied transcript or generated draft')
 parser.add_argument('--transcript-json3',help='Import supplied caption JSON3 without contacting YouTube')
 parser.add_argument('--language',default='hi');parser.add_argument('--automatic',action='store_true')
 parser.add_argument('--generated-file',help='Stage JSON generated from this exact transcript; does not publish')
 parser.add_argument('--model',default='operator-supplied-draft',help='Accurate generation attribution for --generated-file')
 parser.add_argument('--collect-only',action='store_true',help='Collect official sources without video or AI processing')
 parser.add_argument('--run',action='store_true');parser.add_argument('--limit',type=int,choices=range(1,4),default=3)
 args=parser.parse_args()
 with connect() as conn:
  vid=add_metadata(conn,json.loads(Path(args.metadata_file).read_text())) if args.metadata_file else yt.video_id(args.video) if args.video else None
  if args.transcript_json3:
   if not vid:parser.error('--video is required for transcript import')
   file=Path(args.transcript_json3)
   if file.stat().st_size>yt.MAX_CAPTION_BYTES:raise ValueError('Caption file is too large')
   save_transcript(conn,vid,yt.normalized_cues(json.loads(file.read_text())),args.language,args.automatic,'operator-supplied JSON3 captions')
  if args.generated_file:
   if not vid:parser.error('--video is required for generated draft import')
   row=conn.execute('SELECT t.* FROM ca_youtube_transcripts t JOIN ca_youtube_videos v ON v.id=t.video_id AND v.transcript_hash=t.content_hash WHERE v.id=%s',(vid,)).fetchone()
   if not row:raise ValueError('A captured transcript is required before staging generated content')
   file=Path(args.generated_file)
   if file.stat().st_size>100000:raise ValueError('Generated file is too large')
   result=yt.validate_generated(json.loads(file.read_text()),row['cues']);print(json.dumps({'draft':save_generated(conn,vid,row['content_hash'],result,args.model),'published':False}))
  if args.run or args.collect_only:
   result=run(conn,args.limit,args.collect_only);print(json.dumps(result));return 1 if result['status'] in {'partial','failed'} else 0
  if vid:print(json.dumps({'video':vid,'published':False}))
 return 0
if __name__=='__main__':sys.exit(main())
