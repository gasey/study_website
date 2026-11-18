"""Owner-only pipeline inspection and private CMS handoff; no learner publication."""
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Response
from pydantic import Field
from psycopg.types.json import Jsonb
from starlette.responses import JSONResponse
from ..db import cursor
from ..services.review_identity import Actor,identity,require_role
from ..services import youtube_current_affairs as yt
from ..services import content_studio as cms
from ..services import current_affairs_sources as sources
from ..services import current_affairs_briefs as briefs
from .current_affairs import no_assessment
router=APIRouter(prefix='/api/current-affairs/automation',tags=['YouTube current-affairs automation'])
Owner=Annotated[Actor,Depends(identity)]
async def private(response:Response):response.headers['Cache-Control']='private, no-store'
router.dependencies.append(Depends(private))

class Channel(yt.Strict):
 id:str=Field(pattern=r'^UC[A-Za-z0-9_-]{22}$')
 title:str=Field(min_length=2,max_length=300)
 enabled:bool=True
 languages:list[str]=Field(default=['hi-orig','hi','en-orig','en'],min_length=1,max_length=6)
class Retry(yt.Strict):mode:Literal['captions','generation']='captions'
class Decision(yt.Strict):action:Literal['material_draft','reject'];note:str=Field(min_length=15,max_length=1500)

@router.get('')
async def overview(actor:Owner,offset:int=Query(0,ge=0,le=100000)):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('SELECT * FROM ca_youtube_channels ORDER BY title');channels=await cur.fetchall()
  await cur.execute('SELECT status,count(*)::int AS n FROM ca_youtube_videos GROUP BY status');counts={r['status']:r['n'] for r in await cur.fetchall()}
  await cur.execute('''SELECT v.*,c.title AS channel,(SELECT count(*)::int FROM ca_youtube_drafts d WHERE d.video_id=v.id AND d.status='pending') AS pending_drafts FROM ca_youtube_videos v JOIN ca_youtube_channels c ON c.id=v.channel_id ORDER BY v.published_at DESC,v.id LIMIT 25 OFFSET %s''',(offset,));videos=await cur.fetchall()
  await cur.execute('SELECT * FROM ca_youtube_runs ORDER BY id DESC LIMIT 5');runs=await cur.fetchall()
  await cur.execute("SELECT count(*)::int AS n FROM ca_youtube_generation_calls WHERE started_at>now()-interval '24 hours'");calls=(await cur.fetchone())['n']
  await cur.execute('SELECT count(*)::int AS n FROM ca_youtube_videos');total=(await cur.fetchone())['n']
 generation=next((r['summary'].get('generation') for r in runs if r['summary'].get('generation')),{'configured':False,'model':None,'call_limit':6})
 providers=next((r['summary'].get('providers') for r in runs if r['summary'].get('providers')),{'free_only':True,'gemini_ready':False,'supadata_ready':False,'video_input':'captions'})
 return {'providers':providers,'channels':channels,'counts':counts,'videos':videos,'total':total,'offset':offset,'runs':runs,'generation':{**generation,'calls_last_24h':calls},'policy':'Automatic discovery, captions and private drafts. No automatic learner publication.'}

@router.post('/channels')
async def channel(body:Channel,actor:Owner):
 import re
 if any(not re.fullmatch(r'[A-Za-z0-9-]{2,20}',x) for x in body.languages):raise HTTPException(422,'Use exact caption language codes')
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('INSERT INTO ca_youtube_channels(id,title,enabled,languages) VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET title=excluded.title,enabled=excluded.enabled,languages=excluded.languages',(body.id,body.title,body.enabled,Jsonb(body.languages)))
  await cur.execute('INSERT INTO ca_youtube_events(actor_id,action,detail) VALUES(%s,%s,%s)',(actor.id,'channel_configured',Jsonb(body.model_dump())))
 return {'id':body.id,'enabled':body.enabled}

@router.get('/videos/{vid}')
async def inspect(vid:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await no_assessment(cur,actor.id)
  await cur.execute('SELECT * FROM ca_youtube_videos WHERE id=%s',(vid,));video=await cur.fetchone()
  if not video:raise HTTPException(404,'Video not found')
  await cur.execute('SELECT * FROM ca_youtube_transcripts WHERE video_id=%s AND content_hash=%s',(vid,video['transcript_hash']));transcript=await cur.fetchone()
  await cur.execute('SELECT * FROM ca_youtube_drafts WHERE video_id=%s ORDER BY created_at DESC LIMIT 20',(vid,));drafts=await cur.fetchall()
  await cur.execute('SELECT * FROM ca_youtube_events WHERE video_id=%s ORDER BY id DESC LIMIT 20',(vid,));events=await cur.fetchall()
 return {'video':video,'transcript':transcript,'drafts':drafts,'events':events}

@router.post('/videos/{vid}/retry')
async def retry(vid:str,body:Retry,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('SELECT transcript_hash FROM ca_youtube_videos WHERE id=%s FOR UPDATE',(vid,));row=await cur.fetchone()
  if not row:raise HTTPException(404,'Video not found')
  if body.mode=='generation' and not row['transcript_hash']:raise HTTPException(409,'Capture a transcript before generation')
  await cur.execute("UPDATE ca_youtube_videos SET status=%s,next_attempt_at=now(),last_error=NULL,updated_at=now() WHERE id=%s",('transcript_pending' if body.mode=='captions' else 'transcript_ready',vid))
  await cur.execute('INSERT INTO ca_youtube_events(video_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(vid,actor.id,'retry_queued',Jsonb(body.model_dump())))
 return {'queued':True,'message':'Queued for the next scheduled worker run'}

@router.post('/drafts/{draft_id}/decision')
async def decide(draft_id:str,body:Decision,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await no_assessment(cur,actor.id)
  await cur.execute('SELECT d.*,v.title,v.published_at,v.transcript_hash AS current_hash FROM ca_youtube_drafts d JOIN ca_youtube_videos v ON v.id=d.video_id WHERE d.id=%s FOR UPDATE OF d',(draft_id,));draft=await cur.fetchone()
  if not draft:raise HTTPException(404,'Draft not found')
  if draft['status']=='exported' and body.action=='material_draft':return {'material_id':draft['material_id'],'published':False}
  if draft['status']!='pending':raise HTTPException(409,'This draft has already been handled')
  if body.action=='material_draft' and draft['transcript_hash']!=draft['current_hash']:raise HTTPException(409,'The video source changed; inspect the current evidence before handoff')
  material_id=None
  if body.action=='material_draft':
   await cur.execute('SELECT cues,evidence_kind FROM ca_youtube_transcripts WHERE video_id=%s AND content_hash=%s',(draft['video_id'],draft['transcript_hash']));transcript=await cur.fetchone()
   generated=yt.validate_generated(draft['payload'],transcript['cues']);lookup={c['id']:c for c in transcript['cues']}
   blocks=[cms.Block(id='context',type='callout',text='Draft based on a YouTube recap. Check claims against primary sources before publication. The video publication date is not necessarily each fact’s reporting period.')]
   if transcript['evidence_kind']=='model_video_analysis':blocks.append(cms.Block(id='analysis-warning',type='callout',text='Evidence was produced by AI video analysis, not downloaded publisher captions. Check source timestamps and claims.'))
   for fact in generated.facts:
    start=lookup[fact.cue_ids[0]]['start'];blocks.extend([cms.Block(id=fact.id,type='paragraph',text=fact.text),cms.Block(id=fact.id+'-source',type='link',text='Video reference · '+str(int(start))+' seconds',url=yt.source_url(draft['video_id'],start))])
   document=cms.Document(title=draft['title'][:180],summary=generated.summary[:600],tags=['current-affairs','youtube-draft'],blocks=blocks)
   # Reuse the private content studio draft contract. No publication or bank import.
   material_id='mat_'+uuid4().hex
   await cur.execute('INSERT INTO materials(id,author_id,title,tags,blocks) VALUES(%s,%s,%s,%s,%s)',(material_id,actor.id,document.title,document.tags,Jsonb([b.model_dump() for b in document.blocks])))
   await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)',(material_id,Jsonb(document.model_dump()),actor.id))
   await cms.event(cur,material_id,actor.id,'youtube_draft_imported',{'video_id':draft['video_id'],'transcript_hash':draft['transcript_hash'],'generation_model':draft['model'],'source_verified':False})
  await cur.execute('UPDATE ca_youtube_drafts SET status=%s,material_id=%s WHERE id=%s',('exported' if material_id else 'rejected',material_id,draft_id))
  await cur.execute('INSERT INTO ca_youtube_events(video_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(draft['video_id'],actor.id,body.action,Jsonb({'draft_id':draft_id,'note':body.note,'material_id':material_id,'published':False})))
 return {'material_id':material_id,'published':False}

@router.get('/briefs')
async def brief_overview(actor:Owner,offset:int=Query(0,ge=0,le=100000)):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute("SELECT b.*,jsonb_array_length(i.payload->'sources') AS source_count FROM ca_briefs b JOIN ca_brief_inputs i ON i.brief_id=b.id AND i.content_hash=b.current_hash ORDER BY period_end DESC,cadence LIMIT 20 OFFSET %s",(offset,));items=await cur.fetchall()
  await cur.execute('SELECT count(*)::int n FROM ca_briefs');total=(await cur.fetchone())['n']
  await cur.execute("SELECT summary FROM ca_youtube_runs WHERE summary ? 'providers' ORDER BY id DESC LIMIT 1");run=await cur.fetchone()
 return {'items':items,'total':total,'offset':offset,'generation_ready':bool(run and run['summary']['providers'].get('generation_ready'))}

@router.get('/briefs/{brief_id}')
async def brief_inspect(brief_id:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute('SELECT b.*,i.payload AS inputs FROM ca_briefs b JOIN ca_brief_inputs i ON i.brief_id=b.id AND i.content_hash=b.current_hash WHERE b.id=%s',(brief_id,));brief=await cur.fetchone()
  if not brief:raise HTTPException(404,'Brief not found')
  await cur.execute('SELECT * FROM ca_brief_drafts WHERE brief_id=%s ORDER BY created_at DESC LIMIT 10',(brief_id,));drafts=await cur.fetchall()
  current=await briefs.sources_current(cur,brief['inputs'])
 return {'brief':brief,'drafts':drafts,'sources_current':current}

@router.post('/briefs/{brief_id}/retry')
async def brief_retry(brief_id:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute("UPDATE ca_briefs SET status='source_ready',last_error=NULL,next_attempt_at=now() WHERE id=%s RETURNING id",(brief_id,))
  if not await cur.fetchone():raise HTTPException(404,'Brief not found')
  await cur.execute('INSERT INTO ca_source_events(actor_id,action,detail) VALUES(%s,%s,%s)',(actor.id,'brief_retry_queued',Jsonb({'brief_id':brief_id})))
 return {'message':'Brief queued for the next worker run; generation requires the configured free provider'}

@router.post('/brief-drafts/{draft_id}/decision')
async def brief_decide(draft_id:str,body:Decision,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute('''SELECT d.*,b.current_hash,b.cadence,b.period_start,b.period_end,i.payload AS inputs FROM ca_brief_drafts d
   JOIN ca_briefs b ON b.id=d.brief_id JOIN ca_brief_inputs i ON i.brief_id=d.brief_id AND i.content_hash=d.content_hash WHERE d.id=%s FOR UPDATE OF d,b''',(draft_id,));draft=await cur.fetchone()
  if not draft:raise HTTPException(404,'Brief draft not found')
  if draft['status']=='exported' and body.action=='material_draft':return {'material_id':draft['material_id'],'published':False}
  if draft['status']!='pending':raise HTTPException(409,'This brief draft has already been handled')
  material_id=None
  if body.action=='material_draft':
   if draft['content_hash']!=draft['current_hash'] or not await briefs.sources_current(cur,draft['inputs'],lock=True):raise HTTPException(409,'Brief evidence changed; wait for the next collection and inspect the current sources')
   generated=briefs.validate(draft['payload'],draft['inputs']);lookup={c['id']:c for c in draft['inputs']['units']};source_lookup={(s['kind'],s['id']):s for s in draft['inputs']['sources']}
   blocks=[cms.Block(id='context',type='callout',text='AI-prepared private current-affairs brief. Related claims are grouped as draft suggestions, not verified facts. Check each claim, reporting/effective dates and conflicting sources before publication.'),cms.Block(id='coverage',type='paragraph',text=draft['inputs']['coverage']['candidate_window']+' '+draft['inputs']['coverage']['selection_policy'])]
   for index,source in enumerate(draft['inputs']['sources']):blocks.append(cms.Block(id='source-'+str(index),type='link',text=('Model video analysis · ' if source['evidence_kind']=='model_video_analysis' else '')+source['title'][:200],url=source['source_url']))
   for fact in generated.facts:
    citations=[]
    for cue_id in fact.cue_ids:
     for ref in lookup[cue_id]['source_refs']:
      source=source_lookup[(ref['kind'],ref['id'])];citation=source['title'][:150]+' · '+(('model video analysis at ' if source['evidence_kind']=='model_video_analysis' else 'video ')+str(int(ref['start']))+' seconds' if 'start' in ref else 'passage '+str(ref['local_id']+1))
      if citation not in citations:citations.append(citation)
    blocks.extend([cms.Block(id=fact.id,type='paragraph',text=fact.text),cms.Block(id=fact.id+'-evidence',type='paragraph',text='Sources: '+'; '.join(citations))])
   document=cms.Document(title=(draft['cadence'].title()+' current affairs · '+str(draft['period_start'])+' to '+str(draft['period_end']))[:180],summary=generated.summary[:600],tags=['current-affairs','brief-draft'],blocks=blocks);material_id='mat_'+uuid4().hex
   await cur.execute('INSERT INTO materials(id,author_id,title,tags,blocks) VALUES(%s,%s,%s,%s,%s)',(material_id,actor.id,document.title,document.tags,Jsonb([b.model_dump() for b in document.blocks])))
   await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)',(material_id,Jsonb(document.model_dump()),actor.id))
   await cms.event(cur,material_id,actor.id,'current_affairs_brief_imported',{'brief_id':draft['brief_id'],'input_hash':draft['content_hash'],'model':draft['model'],'source_verified':False})
  await cur.execute('UPDATE ca_brief_drafts SET status=%s,material_id=%s WHERE id=%s',('exported' if material_id else 'rejected',material_id,draft_id))
  await cur.execute('INSERT INTO ca_source_events(actor_id,action,detail) VALUES(%s,%s,%s)',(actor.id,'brief_'+body.action,Jsonb({'draft_id':draft_id,'brief_id':draft['brief_id'],'material_id':material_id,'note':body.note,'published':False})))
 return {'material_id':material_id,'published':False}

class YouTubeBodyLimit:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  if not (scope.get('type')=='http' and scope.get('method')=='POST' and scope.get('path','').startswith('/api/current-affairs/automation/')):return await self.app(scope,receive,send)
  size=0;messages=[]
  while True:
   message=await receive()
   if message['type']=='http.disconnect':return
   size+=len(message.get('body',b''))
   if size>32768:return await JSONResponse({'detail':'Automation action exceeds 32 KiB'},status_code=413)(scope,receive,send)
   messages.append(message)
   if not message.get('more_body',False):break
  async def replay():return messages.pop(0) if messages else await receive()
  await self.app(scope,replay,send)

class FeedToggle(yt.Strict):enabled:bool

@router.get('/sources')
async def source_overview(actor:Owner,offset:int=Query(0,ge=0,le=100000)):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('SELECT * FROM ca_source_feeds ORDER BY id');feeds=await cur.fetchall()
  await cur.execute('SELECT * FROM ca_source_items ORDER BY published_at DESC,id LIMIT 25 OFFSET %s',(offset,));items=await cur.fetchall()
  await cur.execute('SELECT count(*)::int AS n FROM ca_source_items');total=(await cur.fetchone())['n']
  await cur.execute("SELECT detail,created_at FROM ca_source_events WHERE action='source_capture_rejected' ORDER BY id DESC LIMIT 10");issues=await cur.fetchall()
  await cur.execute("SELECT coalesce(sum(reserved_credits),0)::int AS n FROM ca_caption_calls WHERE started_at>=date_trunc('month',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'");credits=(await cur.fetchone())['n']
  await cur.execute("SELECT summary FROM ca_youtube_runs WHERE summary ? 'providers' ORDER BY id DESC LIMIT 1");run=await cur.fetchone()
 providers=run['summary']['providers'] if run else {'free_only':True,'gemini_ready':False,'supadata_ready':False,'source_generation_enabled':False}
 return {'collection_issues':issues,'feeds':[{**f,'url':sources.FEEDS[f['id']]['url']} for f in feeds],'items':items,'total':total,'offset':offset,'providers':providers,'supadata_reserved_credits_this_month':credits}

@router.post('/sources/{feed_id}')
async def source_toggle(feed_id:str,body:FeedToggle,actor:Owner):
 if feed_id not in sources.FEEDS:raise HTTPException(404,'Source feed not found')
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('UPDATE ca_source_feeds SET enabled=%s WHERE id=%s',(body.enabled,feed_id))
  await cur.execute('INSERT INTO ca_source_events(actor_id,action,detail) VALUES(%s,%s,%s)',(actor.id,'feed_configured',Jsonb({'feed_id':feed_id,'enabled':body.enabled})))
 return {'enabled':body.enabled}

@router.get('/items/{item_id}')
async def source_inspect(item_id:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute('SELECT * FROM ca_source_items WHERE id=%s',(item_id,));item=await cur.fetchone()
  if not item:raise HTTPException(404,'Source item not found')
  await cur.execute('SELECT * FROM ca_source_revisions WHERE item_id=%s AND content_hash=%s',(item_id,item['current_hash']));evidence=await cur.fetchone()
  await cur.execute('SELECT * FROM ca_source_drafts WHERE item_id=%s ORDER BY created_at DESC LIMIT 20',(item_id,));drafts=await cur.fetchall()
 return {'item':item,'evidence':evidence,'drafts':drafts}

@router.post('/items/{item_id}/retry')
async def source_retry(item_id:str,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute("UPDATE ca_source_items SET status='source_ready',next_attempt_at=now(),last_error=NULL WHERE id=%s RETURNING id",(item_id,))
  if not await cur.fetchone():raise HTTPException(404,'Source item not found')
  await cur.execute('INSERT INTO ca_source_events(item_id,actor_id,action) VALUES(%s,%s,%s)',(item_id,actor.id,'generation_queued'))
 return {'queued':True,'message':'Queued for the next run with official-source generation enabled'}

@router.post('/source-drafts/{draft_id}/decision')
async def source_decide(draft_id:str,body:Decision,actor:Owner):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  await cur.execute('''SELECT d.*,i.current_hash,r.title,r.source_url,r.cues FROM ca_source_drafts d JOIN ca_source_items i ON i.id=d.item_id
   JOIN ca_source_revisions r ON r.item_id=d.item_id AND r.content_hash=d.content_hash WHERE d.id=%s FOR UPDATE OF d,i''',(draft_id,));draft=await cur.fetchone()
  if not draft:raise HTTPException(404,'Source draft not found')
  if draft['status']=='exported' and body.action=='material_draft':return {'material_id':draft['material_id'],'published':False}
  if draft['status']!='pending':raise HTTPException(409,'This source draft has already been handled')
  if body.action=='material_draft' and draft['current_hash']!=draft['content_hash']:raise HTTPException(409,'Official source changed; inspect the current revision before handoff')
  material_id=None
  if body.action=='material_draft':
   generated=yt.validate_generated(draft['payload'],draft['cues'])
   blocks=[cms.Block(id='context',type='callout',text='AI-prepared study draft based on an official release. Check each claim, effective date and reporting period against the cited source before publication.'),cms.Block(id='official-source',type='link',text='Official source release',url=draft['source_url'])]
   for fact in generated.facts:blocks.extend([cms.Block(id=fact.id,type='paragraph',text=fact.text),cms.Block(id=fact.id+'-evidence',type='paragraph',text='Source paragraphs: '+', '.join(str(x+1) for x in fact.cue_ids))])
   doc=cms.Document(title=draft['title'][:180],summary=generated.summary[:600],tags=['current-affairs','official-draft'],blocks=blocks);material_id='mat_'+uuid4().hex
   await cur.execute('INSERT INTO materials(id,author_id,title,tags,blocks) VALUES(%s,%s,%s,%s,%s)',(material_id,actor.id,doc.title,doc.tags,Jsonb([b.model_dump() for b in doc.blocks])))
   await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)',(material_id,Jsonb(doc.model_dump()),actor.id))
   await cms.event(cur,material_id,actor.id,'official_source_draft_imported',{'item_id':draft['item_id'],'source_hash':draft['content_hash'],'generation_model':draft['model'],'source_verified':False})
  await cur.execute('UPDATE ca_source_drafts SET status=%s,material_id=%s WHERE id=%s',('exported' if material_id else 'rejected',material_id,draft_id))
  await cur.execute('INSERT INTO ca_source_events(item_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(draft['item_id'],actor.id,body.action,Jsonb({'draft_id':draft_id,'note':body.note,'material_id':material_id,'published':False})))
 return {'material_id':material_id,'published':False}
