"""Student discovery and owner-managed dated editorial picks."""
from datetime import date,datetime,timedelta,timezone
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Response
from pydantic import BaseModel,ConfigDict,Field,HttpUrl,field_validator,model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user
from ..services import discovery as d
from ..services.review_identity import Actor,identity,require_role
from .current_affairs import no_assessment

router=APIRouter(prefix='/api/discovery',tags=['discovery'])
User=Annotated[str,Depends(current_user)]
Owner=Annotated[Actor,Depends(identity)]
Exam=Literal['udc','combined-prelims']

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Source(Strict):
    url:HttpUrl
    title:str=Field(min_length=5,max_length=250)
    published_on:date
    checked_on:date
    @field_validator('url')
    @classmethod
    def https(cls,v):
        if v.scheme!='https' or v.username or v.password:raise ValueError('Use an HTTPS primary source without credentials')
        return v
    @model_validator(mode='after')
    def dates(self):
        if self.published_on>self.checked_on or self.checked_on>date.today():raise ValueError('Evidence dates must not be in the future or reversed')
        return self
class Pick(Strict):
    id:str|None=Field(None,max_length=100)
    expected_version:int=Field(default=0,ge=0)
    collection_id:Exam
    taxonomy_id:str=Field(min_length=2,max_length=180)
    title:str=Field(min_length=5,max_length=150)
    why_now:str=Field(min_length=20,max_length=1000)
    sources:list[Source]=Field(min_length=1,max_length=5)
    fact_revision_id:int|None=Field(None,ge=1)
    expires_at:datetime|None=None
    reason:str=Field(min_length=20,max_length=1500)
class Decision(Strict):
    expected_version:int=Field(ge=1)
    action:Literal['publish','retire']
    reason:str=Field(min_length=20,max_length=1500)

@router.get('')
async def discover(user:User,response:Response,collection_id:Exam,limit:int=Query(3,ge=1,le=6)):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        try:await no_assessment(cur,user)
        except HTTPException as exc:
            if exc.status_code!=409:raise
            return {'collection_id':collection_id,'popular':[],'recommended':[],'hot':[],'withheld':True,'message':'Discovery unlocks after your assessment.','generated_at':None,'window_days':7}
        return {'collection_id':collection_id,'withheld':False,**await d.cards(cur,collection_id,limit)}

@router.get('/manage')
async def manage(actor:Owner,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await no_assessment(cur,actor.id)
        await cur.execute('SELECT * FROM discovery_picks ORDER BY updated_at DESC LIMIT 100');items=await cur.fetchall()
        await cur.execute("SELECT id,label FROM review_taxonomy WHERE active AND level IN ('topic','subtopic') ORDER BY label");topics=await cur.fetchall()
        await cur.execute("SELECT r.id,e.name FROM current_affairs_revisions r JOIN current_affairs_entities e ON e.live_revision=r.id WHERE r.state='published' ORDER BY r.id DESC LIMIT 100")
        return {'items':items,'topics':topics,'facts':await cur.fetchall()}

async def topic_valid(cur,collection,topic):
    await cur.execute("""SELECT 1 FROM review_taxonomy t WHERE t.id=%s AND t.active AND t.level IN ('topic','subtopic')
      AND EXISTS(SELECT 1 FROM v_question_paths v JOIN appearances a ON a.canonical_id=v.question_id
        JOIN collection_papers cp ON cp.paper_id=a.paper_id JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
        WHERE cp.collection_id=%s AND c.visibility='public' AND (v.topic_id=t.id OR v.subtopic_id=t.id))""",(topic,collection))
    if not await cur.fetchone():raise HTTPException(422,'Choose an approved topic available in this exam')

@router.post('/picks')
async def save(body:Pick,actor:Owner):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
        await topic_valid(cur,body.collection_id,body.taxonomy_id)
        expiry=body.expires_at or datetime.now(timezone.utc)+timedelta(days=14)
        if not expiry.tzinfo or not datetime.now(timezone.utc)<expiry<=datetime.now(timezone.utc)+timedelta(days=14,minutes=1):raise HTTPException(422,'Expiry must be in the next fourteen days with a timezone')
        pid=body.id or 'pick_'+uuid4().hex
        # Stable lock also serializes creation requests for an explicit new ID.
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('discovery:'+pid,))
        await cur.execute('SELECT * FROM discovery_picks WHERE id=%s FOR UPDATE',(pid,));old=await cur.fetchone()
        if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Pick changed; reload before saving')
        if not await d.fact_current(cur,body.fact_revision_id):raise HTTPException(422,'Supporting facts need current independently reviewed publication')
        payload=body.model_dump(mode='json');sources=[s.model_dump(mode='json') for s in body.sources]
        await cur.execute("""INSERT INTO discovery_picks(id,collection_id,taxonomy_id,title,why_now,sources,fact_revision_id,expires_at,created_by)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
          collection_id=excluded.collection_id,taxonomy_id=excluded.taxonomy_id,title=excluded.title,why_now=excluded.why_now,
          sources=excluded.sources,fact_revision_id=excluded.fact_revision_id,expires_at=excluded.expires_at,
          state='draft',published_at=NULL,version=discovery_picks.version+1,updated_at=now() RETURNING *""",
          (pid,body.collection_id,body.taxonomy_id,body.title,body.why_now,Jsonb(sources),body.fact_revision_id,expiry,actor.id))
        row=await cur.fetchone()
        await cur.execute('INSERT INTO discovery_pick_history(pick_id,actor_id,payload,reason) VALUES(%s,%s,%s,%s)',(pid,actor.id,Jsonb({'action':'save','record':payload,'version':row['version']}),body.reason))
        d.clear_cache();return row

@router.post('/picks/{pid}/decision')
async def decide(pid:str,body:Decision,actor:Owner):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));await no_assessment(cur,actor.id)
        await cur.execute('SELECT * FROM discovery_picks WHERE id=%s FOR UPDATE',(pid,));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Pick not found')
        if row['version']!=body.expected_version:raise HTTPException(409,'Pick changed; reload before deciding')
        if body.action=='publish':
            await topic_valid(cur,row['collection_id'],row['taxonomy_id'])
            if row['state']!='draft' or row['expires_at']<=datetime.now(timezone.utc):raise HTTPException(422,'Only an unexpired draft can be published')
            if not await d.fact_current(cur,row['fact_revision_id']):raise HTTPException(409,'Supporting facts are stale or withdrawn')
        await cur.execute("UPDATE discovery_picks SET state=%s,published_at=CASE WHEN %s='publish' THEN now() ELSE published_at END,version=version+1,updated_at=now() WHERE id=%s RETURNING *",('published' if body.action=='publish' else 'retired',body.action,pid));result=await cur.fetchone()
        await cur.execute('INSERT INTO discovery_pick_history(pick_id,actor_id,payload,reason) VALUES(%s,%s,%s,%s)',(pid,actor.id,Jsonb(body.model_dump()),body.reason))
        d.clear_cache();return result
