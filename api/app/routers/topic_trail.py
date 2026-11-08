from typing import Annotated
from uuid import uuid4
from datetime import timedelta
from fastapi import APIRouter,Depends,Request,Response,HTTPException,Query
from pydantic import Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import require_account,current_user
from ..services import games as g,game_selection as setup,topic_trail as trail
from ..services.review_identity import Actor,identity,require_role
from .games import Strict,activity_lock,availability,add_member,private
from .materials import write_guard
from .current_affairs import no_assessment
router=APIRouter(prefix='/api/topic-trail',tags=['Topic Trail'])
Account=Annotated[str,Depends(require_account)]
User=Annotated[str,Depends(current_user)]
Staff=Annotated[Actor,Depends(identity)]
class Start(Strict):
 pack_id:str=Field(max_length=80)
 context_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
 request_key:str=Field(min_length=16,max_length=100)
class Begin(Strict):
 position:int=Field(ge=0,le=10)
 double:bool=False
class Pack(Strict):
 id:str|None=Field(default=None,pattern=r'^trailpack_[0-9a-f]{32}$')
 expected_version:int=Field(default=0,ge=0)
 title:str=Field(min_length=5,max_length=100)
 collection_id:str=Field(max_length=100)
 taxonomy_id:str=Field(max_length=180)
 active:bool=True
 canonical_ids:list[str]|None=Field(default=None,max_length=100)
 reason:str=Field(min_length=20,max_length=3000)

@router.get('')
async def catalog(user:User,response:Response):
 private(response)
 async with cursor() as cur:
  await cur.execute('SELECT * FROM topic_trail_packs WHERE active ORDER BY title');packs=await cur.fetchall()
  rows=[]
  for p in packs:
   try:rows.append({k:v for k,v in (await trail.preview(cur,p)).items() if k!='context'})
   except HTTPException:continue
  await cur.execute("SELECT r.id FROM game_rooms r JOIN game_members m ON m.room_id=r.id WHERE m.user_id=%s AND m.released_at IS NULL",(user,));active=await cur.fetchone()
  await cur.execute('SELECT email IS NOT NULL AS registered FROM users WHERE id=%s',(user,));account=await cur.fetchone()
  return {'packs':rows,'active':active,'registered':bool(account and account['registered'])}

@router.post('/packs')
async def pack(body:Pack,actor:Staff,response:Response):
 private(response)
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  if body.collection_id not in ('udc','combined-prelims'):raise HTTPException(422,'Choose UDC or combined Prelims')
  await cur.execute("SELECT 1 FROM review_taxonomy WHERE id=%s AND active AND level IN ('topic','subtopic')",(body.taxonomy_id,))
  if not await cur.fetchone():raise HTTPException(422,'Choose one approved topic or subtopic')
  pid=body.id or 'trailpack_'+uuid4().hex
  await cur.execute('SELECT * FROM topic_trail_packs WHERE id=%s FOR UPDATE',(pid,));old=await cur.fetchone()
  if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Pack changed; refresh before saving')
  if body.canonical_ids is not None and (not body.canonical_ids or len(set(body.canonical_ids))!=len(body.canonical_ids) or any(not 1<=len(q)<=120 for q in body.canonical_ids)):raise HTTPException(422,'Choose a nonempty list of distinct source question IDs')
  p={**body.model_dump(),'id':pid,'version':body.expected_version+1}
  preview=await trail.preview(cur,p)
  if body.active and body.canonical_ids is not None and preview['available']!=len(body.canonical_ids):raise HTTPException(422,'Every selected source must be eligible, distinct, and inside this exam/topic pool')
  if body.active and preview['available']<10:raise HTTPException(422,'This exact short-text official-key pool needs at least ten questions')
  await cur.execute('INSERT INTO topic_trail_packs(id,title,collection_id,taxonomy_id,active,version,created_by,canonical_ids) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET title=excluded.title,collection_id=excluded.collection_id,taxonomy_id=excluded.taxonomy_id,active=excluded.active,version=excluded.version,canonical_ids=excluded.canonical_ids,updated_at=now()',(pid,body.title,body.collection_id,body.taxonomy_id,body.active,p['version'],actor.id,body.canonical_ids))
  await cur.execute('INSERT INTO topic_trail_pack_history(pack_id,actor_id,payload,reason) VALUES(%s,%s,%s,%s)',(pid,actor.id,Jsonb(p),body.reason))
  return {k:v for k,v in preview.items() if k!='context'}

@router.get('/manage')
async def manage(actor:Staff,response:Response):
 private(response)
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  await cur.execute('SELECT * FROM topic_trail_packs ORDER BY title');rows=await cur.fetchall();packs=[]
  for p in rows:packs.append({**{k:v for k,v in (await trail.preview(cur,p)).items() if k!='context'},'canonical_ids':p['canonical_ids']})
  await cur.execute("SELECT id,label,level FROM review_taxonomy WHERE active AND level IN ('topic','subtopic') ORDER BY id")
  return {'packs':packs,'topics':await cur.fetchall()}

@router.post('/start')
async def start(body:Start,request:Request,user:Account,response:Response):
 private(response);await write_guard(request,user)
 async with cursor() as cur:
  await activity_lock(cur,user);h=g.digest(body.model_dump())
  await cur.execute('SELECT room_id,request_hash FROM game_start_requests WHERE user_id=%s AND request_key=%s',(user,body.request_key));old=await cur.fetchone();now=await g.clock(cur)
  if old:
   if old['request_hash']!=h:raise HTTPException(409,'Start request already used')
   return await g.view(cur,await g.advance(cur,await g.room(cur,old['room_id']),now),user,now)
  await g.permitted(cur,user);await availability(cur,user)
  await cur.execute('SELECT * FROM topic_trail_packs WHERE id=%s AND active FOR SHARE',(body.pack_id,));p=await cur.fetchone()
  if not p:raise HTTPException(404,'Trail pack unavailable')
  selected=await trail.preview(cur,p)
  if selected['context_hash']!=body.context_hash or not selected['can_start']:raise HTTPException(409,'This trail pool changed; choose the pack again')
  questions=await setup.draw(cur,selected['context']);rid='game_'+uuid4().hex
  await cur.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,request_key,request_hash,selection_context,context_hash) VALUES(%s,%s,'trail',1,%s,20,%s,%s,%s,%s)",(rid,user,Jsonb(questions),body.request_key,h,Jsonb(selected['context']),selected['context_hash']))
  r=await g.room(cur,rid);await add_member(cur,r,user)
  await cur.execute('INSERT INTO game_start_requests(user_id,request_key,room_id,request_hash) VALUES(%s,%s,%s,%s)',(user,body.request_key,rid,h))
  r=await g.start(cur,await g.room(cur,rid),now)
  return await g.view(cur,r,user,now)

@router.post('/{rid}/begin')
async def begin(rid:str,body:Begin,request:Request,user:Account,response:Response):
 private(response);await write_guard(request,user)
 async with cursor() as cur:
  r=await g.room(cur,rid);m=await g.member(cur,r,user);await g.permitted(cur,user);now=await g.clock(cur);r=await g.advance(cur,r,now)
  if r['mode']!='trail' or m['left_at'] or r['state']!='running':raise HTTPException(409,'Trail is no longer running')
  if r['trail_phase']=='question':
   if body.position==r['current_position'] and body.double==(r['trail_boost_position']==body.position):return await g.view(cur,r,user,now)
   raise HTTPException(409,'Double next must be chosen before the question is revealed')
  target=r['current_position']+(1 if r['trail_phase']=='feedback' else 0)
  if body.position!=target:raise HTTPException(409,'Trail position changed; refresh')
  if target==len(r['questions']):
   await g.finish(cur,r,now);return await g.view(cur,await g.room(cur,rid),user,now)
  if body.double and r['trail_boost_position'] is not None:raise HTTPException(409,'Double next was already used')
  await cur.execute("UPDATE game_rooms SET current_position=%s,trail_phase='question',trail_boost_position=CASE WHEN %s THEN %s ELSE trail_boost_position END,round_started_at=%s,round_ends_at=%s,version=version+1 WHERE id=%s",(target,body.double,target,now,now+timedelta(seconds=20),rid))
  await g.event(cur,rid,user,'trail_reveal',{'position':target,'double':body.double})
  return await g.view(cur,await g.room(cur,rid),user,now)

@router.get('/pool')
async def pool(actor:Staff,response:Response,collection_id:str=Query(max_length=100),taxonomy_id:str=Query(max_length=180)):
 private(response)
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
  if collection_id not in ('udc','combined-prelims'):raise HTTPException(422,'Choose UDC or Prelims')
  await cur.execute("SELECT 1 FROM review_taxonomy WHERE id=%s AND active AND level IN ('topic','subtopic')",(taxonomy_id,))
  if not await cur.fetchone():raise HTTPException(422,'Choose an approved topic')
  ctx=await trail.context(cur,dict(id='pool',title='Candidate source inspection',collection_id=collection_id,taxonomy_id=taxonomy_id,version=1))
  rows=await setup.candidates(cur,ctx,full=True)
  return {'total':len(rows),'questions':[{k:r.get(k) for k in ('id','question','options','answer_text','answer_source','exam_name','year','qnum','page','source_pdf_url')} for r in rows[:150]]}
