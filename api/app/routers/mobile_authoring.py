"""Native learner authoring. Never delegates staff identity or publication rights."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import require_account
from ..services.review_identity import Actor
from ..services.review_policy import Proposal
from . import bank_workspace as bank, learning_catalog as learning, billing
from .materials import write_guard
from .current_affairs import no_assessment

router = APIRouter(prefix='/mobile', tags=['mobile learner authoring'])

async def learner(request: Request, response: Response, user: Annotated[str, Depends(require_account)]):
    response.headers['Cache-Control'] = 'private, no-store'
    if request.method not in {'GET','HEAD','OPTIONS'}:
        await write_guard(request, user)
    return Actor(user, '', False, False)

Account = Annotated[Actor, Depends(learner)]

@router.get('/taxonomy')
async def taxonomy(actor: Account):
    return await bank.taxonomy(actor)

def original(proposal):
    if proposal.kind != 'new_question' or proposal.canonical_id or proposal.appearance_id or proposal.reverts_publication:
        raise HTTPException(403, 'This editor accepts original MCQ proposals only')

async def owned_question(cid, actor):
    async with cursor() as cur:
        await cur.execute("SELECT 1 FROM bank_contributions WHERE id=%s AND author_id=%s AND kind='new_question' AND canonical_id IS NULL", (cid, actor.id))
        if not await cur.fetchone():
            raise HTTPException(404, 'Your MCQ draft was not found')

@router.get('/contributions/summary')
async def contribution_summary(actor: Account):
    return await bank.summary(actor)

@router.get('/contributions')
async def contributions(actor: Account, before: str | None = None):
    # Only original-question drafts belong to this authoring surface.
    async with cursor() as cur:
        await cur.execute("""SELECT id,title,state,revision,lock_version FROM bank_contributions
          WHERE author_id=%s AND kind='new_question' AND canonical_id IS NULL
          AND (%s::text IS NULL OR (created_at,id)<(SELECT created_at,id FROM bank_contributions WHERE id=%s AND author_id=%s))
          ORDER BY created_at DESC,id DESC LIMIT 21""", (actor.id,before,before,actor.id))
        rows=await cur.fetchall()
    return {'items':rows[:20], 'next_cursor':rows[19]['id'] if len(rows)>20 else None}

@router.post('/contributions', status_code=201)
async def create_question(proposal: Proposal, actor: Account, idempotency_key: Annotated[str | None, Header()] = None):
    original(proposal)
    return await bank.create(proposal, actor, idempotency_key, None)

@router.get('/contributions/{cid}')
async def question_detail(cid: str, actor: Account):
    await owned_question(cid,actor)
    detail=await bank.detail(cid,actor)
    # A real owner using a learner token still receives no staff capabilities.
    detail['permissions']=[]
    return detail

@router.post('/contributions/{cid}/revisions')
async def revise_question(cid: str, body: bank.Revise, actor: Account):
    original(body.proposal)
    await owned_question(cid,actor)
    async with cursor() as cur:
        await cur.execute('''SELECT c.* FROM bank_contributions c JOIN contribution_revisions r
          ON r.contribution_id=c.id AND r.revision=c.revision WHERE c.id=%s AND c.author_id=%s
          AND c.lock_version=%s AND c.state='draft' AND r.payload=%s''',
          (cid,actor.id,body.expected_version+1,Jsonb(body.proposal.model_dump(mode='json'))))
        replay=await cur.fetchone()
        if replay:return replay
    return await bank.revise(cid,body,actor,None)

@router.post('/contributions/{cid}/submit')
async def submit_question(cid: str, body: bank.Transition, actor: Account):
    await owned_question(cid,actor)
    async with cursor() as cur:
        await cur.execute("SELECT * FROM bank_contributions WHERE id=%s AND author_id=%s AND lock_version=%s AND state='submitted'",(cid,actor.id,body.expected_version+1))
        replay=await cur.fetchone()
        if replay:return replay
    return await bank.submit(cid,body,actor)

@router.post('/contributions/{cid}/withdraw')
async def withdraw_question(cid: str, body: bank.Transition, actor: Account):
    await owned_question(cid,actor)
    return await bank.withdraw(cid,body,actor)

@router.get('/learning')
async def learning_drafts(actor: Account):
    async with cursor() as cur:
        await no_assessment(cur,actor.id)
        await cur.execute('SELECT * FROM learning_catalog WHERE author_id=%s ORDER BY updated_at DESC LIMIT 100',(actor.id,))
        rows=await cur.fetchall()
        for row in rows:
            await cur.execute('SELECT version,action,reason,created_at FROM learning_catalog_history WHERE entry_id=%s ORDER BY version DESC LIMIT 20',(row['id'],))
            row['history']=await cur.fetchall()
    return {'items':rows,'user_id':actor.id}

@router.post('/learning')
async def save_learning(body: learning.Save, actor: Account, response: Response):
    # A lost save response can be replayed only for the same exact next revision.
    if body.id:
        async with cursor() as cur:
            await no_assessment(cur,actor.id)
            await cur.execute('SELECT * FROM learning_catalog WHERE id=%s AND author_id=%s',(body.id,actor.id))
            row=await cur.fetchone()
            if row and row['version']==body.expected_version+1 and row['payload']==body.content.model_dump(mode='json') and row['state']=='draft':
                return row
    return await learning.save(body,actor,response)

class LearnerDecision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version:int=Field(ge=1)
    action:Literal['submit','withdraw']
    reason:str=Field(min_length=20,max_length=1500)

@router.post('/learning/{eid}/decision')
async def learning_decision(eid: str, body: LearnerDecision, actor: Account, response: Response):
    async with cursor() as cur:
        await cur.execute('SELECT author_id,live_payload FROM learning_catalog WHERE id=%s',(eid,))
        row=await cur.fetchone()
        if not row or row['author_id']!=actor.id:raise HTTPException(404,'Your draft was not found')
        if body.action=='withdraw' and not (row['live_payload'] or {}).get('test_config'):
            raise HTTPException(403,'Only your published timed test can be withdrawn here')
    return await learning.decision(eid,learning.Decision(**body.model_dump()),actor,response)

@router.get('/billing')
async def billing_status(actor: Account):
    return await billing.billing_me(actor.id)

@router.get('/security')
async def security(request: Request, actor: Account):
    mobile=getattr(request.state,'mobile_session',None)
    if not mobile:raise HTTPException(400,'Open this page from the signed-in app')
    async with cursor() as cur:
        await cur.execute('''SELECT public_id AS id,created_at,expires_at,public_id=%s AS current
          FROM mobile_sessions WHERE user_id=%s AND revoked_at IS NULL AND expires_at>now() ORDER BY created_at DESC''',(mobile['public_id'],actor.id))
        native=await cur.fetchall()
        await cur.execute('''SELECT s.public_id AS id,s.created_at,s.expires_at,s.token_hash=m.parent_session_hash AS current
          FROM auth_sessions s JOIN mobile_sessions m ON m.public_id=%s AND m.user_id=s.user_id
          WHERE s.user_id=%s AND s.revoked_at IS NULL AND s.expires_at>now() ORDER BY s.created_at DESC''',(mobile['public_id'],actor.id))
        browser=await cur.fetchall()
    return {'mobile':native,'browser':browser}

class Revoke(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind:Literal['mobile','browser']
    id:str=Field(min_length=1,max_length=100)

@router.post('/security/revoke')
async def revoke_session(body: Revoke, request: Request, actor: Account):
    mobile=getattr(request.state,'mobile_session',None)
    if not mobile:raise HTTPException(400,'Mobile session required')
    async with cursor() as cur:
        if body.kind=='mobile':
            if body.id==mobile['public_id']:raise HTTPException(409,'Use Sign out for this device')
            await cur.execute('UPDATE mobile_sessions SET revoked_at=now() WHERE user_id=%s AND public_id=%s AND revoked_at IS NULL',(actor.id,body.id))
        else:
            await cur.execute('''UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND public_id=%s AND revoked_at IS NULL
              AND token_hash<>(SELECT parent_session_hash FROM mobile_sessions WHERE public_id=%s AND user_id=%s)''',(actor.id,body.id,mobile['public_id'],actor.id))
        count=cur.rowcount
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'mobile_sessions_revoked',%s)",(actor.id,Jsonb({'kind':body.kind,'count':count})))
    return {'revoked':count}
