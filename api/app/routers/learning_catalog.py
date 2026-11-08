"""Reviewed learning collections. Never copies or writes canonical questions."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Annotated, Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user
from ..services.review_identity import Actor, identity, require_role
from ..services.review_policy import safe_url
from .current_affairs import no_assessment
from ..services.shareable_tests import TestConfig, capture as capture_test, freeze as freeze_test

router = APIRouter(prefix='/api/learning-catalog', tags=['learning catalog'])
Account = Annotated[Actor, Depends(identity)]
User = Annotated[str, Depends(current_user)]

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Source(Strict):
    title: str = Field(min_length=3, max_length=250)
    url: str = Field(max_length=2048)
    checked_on: date
    @model_validator(mode='after')
    def check(self):
        safe_url(self.url)
        if self.checked_on > datetime.now(ZoneInfo('Asia/Kolkata')).date():
            raise ValueError('Verification date cannot be in the future')
        return self

class Theme(Strict):
    year: int = Field(ge=1900, le=2100)
    text: str = Field(min_length=3, max_length=1000)
    source: Source

class Content(Strict):
    kind: Literal['day','practice']
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20, max_length=5000)
    subject_id: str = Field(min_length=2, max_length=100)
    question_ids: list[str] = Field(default_factory=list, max_length=100)
    sources: list[Source] = Field(default_factory=list, max_length=10)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    occurrences: list[date] = Field(default_factory=list, max_length=30)
    themes: list[Theme] = Field(default_factory=list, max_length=30)
    suggested_minutes: int | None = Field(default=None, ge=1, le=180)
    test_config: TestConfig | None = None
    @model_validator(mode='after')
    def check(self):
        if len(set(self.question_ids)) != len(self.question_ids) or any(not 1 <= len(q) <= 120 for q in self.question_ids):
            raise ValueError('Use distinct canonical question IDs')
        if self.test_config and self.kind!='practice': raise ValueError('Timed tests belong to practice collections')
        if self.kind == 'day':
            if not self.sources: raise ValueError('Important days need a verified source')
            if self.month is not None and self.day is not None:
                date(2000,self.month,self.day)
                if self.occurrences: raise ValueError('Choose a recurring date or explicit year dates')
            elif self.month is not None or self.day is not None or not self.occurrences:
                raise ValueError('Supply month and day, or verified year-specific dates')
        elif self.month or self.day or self.occurrences or self.themes:
            raise ValueError('Date fields belong to Important Days')
        if len({t.year for t in self.themes}) != len(self.themes): raise ValueError('Only one theme per year')
        if len(set(self.occurrences)) != len(self.occurrences): raise ValueError('Remove duplicate dates')
        return self

class Save(Strict):
    id: str | None = Field(default=None, pattern=r'^learn_[0-9a-f]{32}$')
    expected_version: int = Field(default=0, ge=0)
    content: Content
    reason: str = Field(min_length=10,max_length=1500)

class Decision(Strict):
    expected_version: int = Field(ge=1)
    action: Literal['submit','publish','owner_publish','request_changes','reject','withdraw']
    reason: str = Field(default='',max_length=1500)
    preview_confirmed: bool = False

    @model_validator(mode='after')
    def reason_for_review(self):
        if self.action!='owner_publish' and len(self.reason.strip())<20:raise ValueError('Explain this review decision in at least 20 characters')
        return self

def next_date(payload, today):
    dates = [date.fromisoformat(d) for d in payload.get('occurrences',[])]
    if payload.get('month') and payload.get('day'):
        for year in range(today.year,today.year+5):
            try: dates.append(date(year,payload['month'],payload['day']))
            except ValueError: pass
    return min((d for d in dates if d >= today), default=None)

async def validate_content(cur, content):
    if content.test_config:
        await capture_test(cur,content.model_dump(mode='json'))
    await cur.execute("SELECT 1 FROM review_taxonomy WHERE id=%s AND level='subject' AND active",(content.subject_id,))
    if not await cur.fetchone(): raise HTTPException(422,'Choose an approved subject')
    if content.question_ids:
        await cur.execute("SELECT id FROM v_all_questions WHERE id=ANY(%s) AND status='live'",(content.question_ids,))
        if {r['id'] for r in await cur.fetchall()} != set(content.question_ids):
            raise HTTPException(422,'Linked questions must be live bank records')

async def record(cur, row, actor, action, reason):
    await cur.execute('INSERT INTO learning_catalog_history(entry_id,version,actor_id,action,payload,reason) VALUES(%s,%s,%s,%s,%s,%s)',
        (row['id'],row['version'],actor,action,Jsonb(row['payload']),reason))

@router.get('')
async def catalog(user:User,response:Response,kind:Literal['day','practice']='day',month:int|None=Query(None,ge=1,le=12),subject_id:str|None=Query(None,max_length=100),q:str=Query('',max_length=120)):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await no_assessment(cur,user)
        await cur.execute("SELECT id,live_payload AS content FROM learning_catalog WHERE kind=%s AND live_payload IS NOT NULL ORDER BY live_payload->>'title'",(kind,))
        rows=await cur.fetchall(); result=[]; today=datetime.now(ZoneInfo('Asia/Kolkata')).date()
        for row in rows:
            p=row['content']
            if subject_id and p['subject_id']!=subject_id: continue
            if q.casefold() not in (p['title']+' '+p['description']).casefold(): continue
            if month and p.get('month')!=month and not any(date.fromisoformat(d).month==month for d in p.get('occurrences',[])):continue
            await cur.execute('SELECT count(*)::int AS n FROM v_mock_practice WHERE id=ANY(%s)',(p['question_ids'],))
            available=(await cur.fetchone())['n']
            result.append({**row,'next_date':next_date(p,today),'available':available})
        return {'items':result,'today':today}

@router.get('/manage')
async def manage(actor:Account,response:Response,timed:bool=False):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await cur.execute('''SELECT e.* FROM learning_catalog e WHERE (author_id=%s OR EXISTS(
            SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
            AND g.role IN ('owner','senior','reviewer') AND (g.subject_id IS NULL OR g.subject_id=e.payload->>'subject_id')))
            AND (NOT %s OR (e.author_id=%s AND jsonb_typeof(e.payload->'test_config')='object'))
            ORDER BY updated_at DESC LIMIT 100''',(actor.id,actor.id,timed,actor.id))
        rows=await cur.fetchall()
        for r in rows:
            await cur.execute('SELECT version,action,reason,created_at FROM learning_catalog_history WHERE entry_id=%s ORDER BY version DESC LIMIT 20',(r['id'],))
            r['history']=await cur.fetchall()
        from ..services.owner_workflow import is_owner
        return {'items':rows,'user_id':actor.id,'can_owner_publish':await is_owner(cur,actor.id)}

@router.post('')
async def save(body:Save,actor:Account,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        eid=body.id or 'learn_'+uuid4().hex
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(eid,))
        await cur.execute('SELECT * FROM learning_catalog WHERE id=%s FOR UPDATE',(eid,));old=await cur.fetchone()
        if old and old['author_id']!=actor.id: raise HTTPException(403,'Only the author can revise this proposal')
        if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Entry changed; reload before saving')
        if old and old['state']=='submitted':raise HTTPException(409,'Wait for review before revising')
        if old and old['kind']!=body.content.kind:raise HTTPException(422,'Entry kind cannot change')
        if body.content.test_config and not old:
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('test-creator:'+actor.id,))
            await cur.execute("SELECT count(*) AS n FROM learning_catalog WHERE author_id=%s AND payload->'test_config' IS NOT NULL AND payload->'test_config'<>'null'::jsonb",(actor.id,))
            if (await cur.fetchone())['n']>=50:raise HTTPException(429,'You can keep up to 50 test collections. Revise an existing test.')
        await validate_content(cur,body.content)
        await cur.execute('''INSERT INTO learning_catalog(id,kind,author_id,payload) VALUES(%s,%s,%s,%s)
            ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,state='draft',version=learning_catalog.version+1,updated_at=now() RETURNING *''',
            (eid,body.content.kind,actor.id,Jsonb(body.content.model_dump(mode='json'))))
        row=await cur.fetchone();await record(cur,row,actor.id,'save',body.reason);return row

@router.post('/{eid}/decision')
async def decision(eid:str,body:Decision,actor:Account,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await cur.execute('SELECT * FROM learning_catalog WHERE id=%s FOR UPDATE',(eid,));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Entry unavailable')
        if body.action=='owner_publish':
            await require_role(cur,actor.id,roles=('owner',))
            if not body.preview_confirmed:raise HTTPException(422,'Preview the test or collection before publishing as owner')
            if row['state']=='published' and row['version']==body.expected_version+1:
                await cur.execute("SELECT 1 FROM learning_catalog_history WHERE entry_id=%s AND version=%s AND action='owner_publish' AND actor_id=%s",(eid,row['version'],actor.id))
                if await cur.fetchone():return row
        if row['version']!=body.expected_version:raise HTTPException(409,'Entry changed; reload before reviewing')
        if body.action=='owner_publish':
            if row['state'] not in ('draft','changes_requested','rejected','submitted'):raise HTTPException(409,'Save a new draft before publishing another edition')
            content=Content.model_validate(row['payload']);await validate_content(cur,content)
            if content.kind=='practice':
                await cur.execute('SELECT count(*) AS n FROM v_mock_practice WHERE id=ANY(%s)',(content.question_ids,))
                if not content.question_ids or (await cur.fetchone())['n']!=len(content.question_ids):raise HTTPException(422,'Every practice question needs an eligible reviewed answer')
            revision=row['version']+1
            if content.test_config:await freeze_test(cur,eid,revision,row['payload'],actor.id)
            await cur.execute("UPDATE learning_catalog SET state='published',version=version+1,updated_at=now(),live_payload=payload,live_test_version=%s WHERE id=%s RETURNING *",(revision if content.test_config else None,eid))
            updated=await cur.fetchone()
            reason='Owner publication decision: '+content.title+'.'+(' Owner note: '+body.reason.strip() if body.reason.strip() else '')
            await record(cur,updated,actor.id,'owner_publish',reason)
            return updated
        if body.action=='submit':
            if row['author_id']!=actor.id:raise HTTPException(403,'Only the author can submit')
            if row['state'] not in ('draft','changes_requested','rejected'):raise HTTPException(409,'Not a draft')
            state='submitted'
        else:
            own_test_withdraw=body.action=='withdraw' and row['author_id']==actor.id and (row.get('live_payload') or {}).get('test_config')
            if not own_test_withdraw:await require_role(cur,actor.id,row['payload']['subject_id'],roles=('owner','senior','reviewer'))
            if body.action!='withdraw' and row['author_id']==actor.id:raise HTTPException(403,'An independent reviewer must decide')
            if body.action=='withdraw':
                if row['live_payload'] is None:raise HTTPException(409,'Nothing published to withdraw')
                state='withdrawn'
            else:
                if row['state']!='submitted':raise HTTPException(409,'Submit this revision for review first')
                state={'publish':'published','request_changes':'changes_requested','reject':'rejected'}[body.action]
            if body.action=='publish':
                content=Content.model_validate(row['payload']);await validate_content(cur,content)
                if content.kind=='practice':
                    await cur.execute('SELECT count(*) AS n FROM v_mock_practice WHERE id=ANY(%s)',(content.question_ids,))
                    if not content.question_ids or (await cur.fetchone())['n']!=len(content.question_ids):raise HTTPException(422,'Every practice question needs an eligible reviewed answer')
        test_revision=row.get('live_test_version')
        if body.action=='publish':
            test_revision=row['version']+1 if content.test_config else None
            if content.test_config:await freeze_test(cur,eid,test_revision,row['payload'],actor.id)
        elif body.action=='withdraw':test_revision=None
        await cur.execute('''UPDATE learning_catalog SET state=%s,version=version+1,updated_at=now(),live_test_version=%s,
            live_payload=CASE WHEN %s='publish' THEN payload WHEN %s='withdraw' THEN NULL ELSE live_payload END WHERE id=%s RETURNING *''',
            (state,test_revision,body.action,body.action,eid))
        row=await cur.fetchone();await record(cur,row,actor.id,body.action,body.reason);return row


@router.get('/overview')
async def overview(user:User,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute("SELECT count(*)::int AS answered,count(*) FILTER(WHERE correct)::int AS correct FROM attempts WHERE user_id=%s AND at>=now()-interval '7 days'",(user,))
        activity=await cur.fetchone()
        await cur.execute("SELECT count(*)::int AS n FROM mock_sessions WHERE user_id=%s AND submitted_at>=now()-interval '7 days'",(user,))
        activity['completed_mocks']=(await cur.fetchone())['n']
        await cur.execute("SELECT c.id,c.title FROM user_exam_bookmarks b JOIN collections c ON c.id=b.collection_id WHERE b.user_id=%s AND c.visibility='public' ORDER BY c.position,c.title",(user,))
        return {'activity':activity,'exams':await cur.fetchall()}
