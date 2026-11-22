"""Native-app authorization and learner-owned bookmarks. No bank administration."""
import base64
import hashlib
import hmac
import json
import secrets
from time import perf_counter
from html import escape
from typing import Annotated
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from ..config import settings
from ..db import cursor
from ..deps import require_account
from ..services.account_identity import account_session, csrf_token, digest
from ..services.mobile_identity import PREFIX,capabilities
from ..services.review_identity import Actor
from .auth import _check_rate, _same_origin
from .bank_workspace import QuestionReport, report_question
from .materials import write_guard

router = APIRouter(prefix='/api', tags=['mobile companion'])
from .mobile_authoring import router as authoring_router
router.include_router(authoring_router)
Account = Annotated[str, Depends(require_account)]
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Start(Strict):
    challenge: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    state: str = Field(pattern=r'^[A-Za-z0-9_-]{32,128}$')
    redirect_uri: str = Field(max_length=250)
class Authorize(Strict):
    flow: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
class Exchange(Authorize):
    code: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    verifier: str = Field(pattern=r'^[A-Za-z0-9._~-]{43,128}$')
    redirect_uri: str = Field(max_length=250)

def challenge_for(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()

def private(response):
    response.headers['Cache-Control']='private, no-store'
    response.headers['Referrer-Policy']='no-referrer'

@router.post('/mobile-auth/start')
async def start(body:Start, request:Request, response:Response):
    private(response)
    if body.redirect_uri not in settings.mobile_redirect_uris:
        raise HTTPException(422,'Unregistered mobile callback')
    await _check_rate('mobile-start', request.client.host if request.client else 'unknown')
    flow=secrets.token_urlsafe(32)
    async with cursor() as cur:
        await cur.execute('DELETE FROM mobile_auth_flows WHERE expires_at<now()')
        await cur.execute('INSERT INTO mobile_auth_flows(id,challenge,state,redirect_uri) VALUES(%s,%s,%s,%s)',(flow,body.challenge,body.state,body.redirect_uri))
    return {'flow':flow,'authorization_url':settings.public_origin+'/api/mobile-auth/authorize?'+urlencode({'flow':flow})}

@router.get('/mobile-auth/authorize')
async def authorize_page(request:Request, flow:str=Query(pattern=r'^[A-Za-z0-9_-]{43}$')):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM mobile_auth_flows WHERE id=%s AND expires_at>now() AND authorized_at IS NULL',(flow,))
        if not await cur.fetchone():raise HTTPException(400,'Sign-in link expired. Start again in the app.')
    session=await account_session(request)
    if not session:
        return RedirectResponse('/login?'+urlencode({'next':'/api/mobile-auth/authorize?'+urlencode({'flow':flow})}),status_code=303)
    async with cursor() as cur:
        await cur.execute('SELECT email FROM users WHERE id=%s',(session['user_id'],)); email=(await cur.fetchone())['email']
    nonce=secrets.token_urlsafe(24)
    # Deliberate confirmation prevents a third-party link silently connecting an app.
    html='''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Connect Finna</title>
    <style>body{background:#f4efe4;color:#1d1b18;font:18px system-ui;padding:32px;max-width:480px;margin:8vh auto}button{min-height:48px;background:#1d1b18;color:white;border:0;border-radius:12px;padding:12px 24px;font:inherit}p{line-height:1.6}</style>
    <h1>Continue in the app</h1><p>Connect <strong>'''+escape(email)+'''</strong> to Finna on your phone. Your questions, progress and existing access stay together.</p><button id="connect">Connect this account</button><p id="status" role="status"></p>
    <script nonce="'''+nonce+'''">document.getElementById('connect').onclick=async()=>{const b=document.getElementById('connect');b.disabled=true;try{const r=await fetch('/api/mobile-auth/authorize',{method:'POST',headers:{'Content-Type':'application/json','X-Review-CSRF':TOKEN},body:JSON.stringify({flow:FLOW})});const v=await r.json();if(!r.ok)throw new Error(v.detail);location.href=v.redirect;}catch(e){document.getElementById('status').textContent=e.message;b.disabled=false;}};</script></html>'''
    html=html.replace('TOKEN',json.dumps(csrf_token(request.cookies['ism_session']))).replace('FLOW',json.dumps(flow))
    result=HTMLResponse(html);private(result)
    result.headers['Content-Security-Policy']=f"default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-{nonce}'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    return result

@router.post('/mobile-auth/authorize')
async def authorize(body:Authorize,request:Request,response:Response):
    private(response);_same_origin(request)
    session=await account_session(request)
    if not session:raise HTTPException(401,'Sign in to connect your account')
    from ..services.audience import require_learner
    await require_learner(session['user_id'])
    code=secrets.token_urlsafe(32)
    async with cursor() as cur:
        await cur.execute('''UPDATE mobile_auth_flows SET code_hash=%s,parent_session_hash=%s,authorized_at=now(),expires_at=LEAST(expires_at,now()+interval '90 seconds')
          WHERE id=%s AND expires_at>now() AND authorized_at IS NULL RETURNING state,redirect_uri''',
          (digest(code),digest(request.cookies['ism_session']),body.flow));flow=await cur.fetchone()
        if not flow:raise HTTPException(400,'Sign-in link expired or already used')
    return {'redirect':flow['redirect_uri']+'?'+urlencode({'code':code,'state':flow['state'],'flow':body.flow})}

@router.post('/mobile-auth/exchange')
async def exchange(body:Exchange,request:Request,response:Response):
    private(response)
    await _check_rate('mobile-exchange',request.client.host if request.client else 'unknown')
    token=PREFIX+secrets.token_urlsafe(32)
    async with cursor() as cur:
        await cur.execute('''SELECT f.*,s.user_id,s.expires_at AS session_expiry FROM mobile_auth_flows f
          JOIN auth_sessions s ON s.token_hash=f.parent_session_hash
          WHERE f.id=%s AND f.code_hash=%s AND f.expires_at>now() AND f.consumed_at IS NULL
          AND s.expires_at>now() AND s.revoked_at IS NULL FOR UPDATE OF f,s''',(body.flow,digest(body.code)))
        flow=await cur.fetchone()
        if not flow or flow['redirect_uri']!=body.redirect_uri or not hmac.compare_digest(flow['challenge'],challenge_for(body.verifier)):
            raise HTTPException(400,'Invalid or expired authorization code')
        from ..services.audience import require_learner
        await require_learner(flow['user_id'])
        await cur.execute('UPDATE mobile_auth_flows SET consumed_at=now() WHERE id=%s',(body.flow,))
        await cur.execute('''INSERT INTO mobile_sessions(token_hash,public_id,user_id,parent_session_hash,expires_at)
          VALUES(%s,%s,%s,%s,LEAST(%s,now()+interval '30 days')) RETURNING expires_at''',
          (digest(token),secrets.token_urlsafe(16),flow['user_id'],flow['parent_session_hash'],flow['session_expiry']))
        expires=(await cur.fetchone())['expires_at']
    return {'access_token':token,'token_type':'Bearer','user_id':flow['user_id'],'expires_at':expires}

@router.get('/mobile/session')
async def mobile_session(request:Request,user:Account):
    async with cursor() as cur:
        await cur.execute("SELECT id,email,handle,CASE WHEN account_has_pro(id) THEN 'pro' ELSE 'free' END AS plan_code FROM users WHERE id=%s",(user,));row=await cur.fetchone()
    return {**row,'expires_at':getattr(request.state,'mobile_session',{}).get('expires_at'),
            'capabilities':capabilities()}

@router.post('/mobile/logout')
async def logout(request:Request,user:Account):
    token_hash=getattr(request.state,'mobile_token_hash',None)
    if not token_hash:raise HTTPException(400,'Mobile credential required')
    async with cursor() as cur:
        await cur.execute('UPDATE mobile_sessions SET revoked_at=now() WHERE token_hash=%s AND user_id=%s',(token_hash,user))
    return {'revoked':True}

@router.get('/mobile/bookmarks')
async def bookmarks(user:Account,offset:int=Query(0,ge=0),limit:int=Query(30,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute("SELECT b.question_id,b.created_at,CASE WHEN q.status IN ('live','held') THEN q.question ELSE 'Question withdrawn' END AS question FROM user_question_bookmarks b JOIN canonical_questions q ON q.id=b.question_id WHERE b.user_id=%s ORDER BY b.created_at DESC,b.question_id LIMIT %s OFFSET %s",(user,limit,offset));items=await cur.fetchall()
        await cur.execute('SELECT count(*) AS total FROM user_question_bookmarks WHERE user_id=%s',(user,));total=(await cur.fetchone())['total']
    return {'items':items,'total':total}

@router.get('/mobile/bookmarks/{qid}')
async def bookmark_state(qid:str,user:Account):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM user_question_bookmarks WHERE user_id=%s AND question_id=%s',(user,qid))
        return {'saved': bool(await cur.fetchone())}

@router.put('/mobile/bookmarks/{qid}')
async def save_bookmark(qid:str,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await cur.execute("SELECT 1 FROM canonical_questions WHERE id=%s AND status IN ('live','held')",(qid,))
        if not await cur.fetchone():raise HTTPException(404,'Question not available')
        await cur.execute('INSERT INTO user_question_bookmarks(user_id,question_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(user,qid))
    return {'saved':True}

@router.delete('/mobile/bookmarks/{qid}')
async def remove_bookmark(qid:str,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await cur.execute('DELETE FROM user_question_bookmarks WHERE user_id=%s AND question_id=%s',(user,qid))
    return {'saved':False}

@router.post('/mobile/questions/{qid}/report')
async def report(qid:str,body:QuestionReport,request:Request,user:Account):
    await write_guard(request,user)
    return await report_question(qid,body,Actor(user,'',False,False))

class ExpectedContext(Strict):
    direction: str | None = None
    passage: str | None = None
    question_markup: str | None = None
    options_markup: list[str | None] | None = None
    figure_image_url: str | None = None
    has_diagram: bool = False

class MobileAnswer(Strict):
    expected_context: ExpectedContext | None = None
    chosen_index:int=Field(ge=0,le=9)
    request_key:str=Field(min_length=16,max_length=100)
    expected_question:str=Field(max_length=100000)
    expected_options:list[str|None]=Field(min_length=1,max_length=10)
    collection_id:str|None=Field(default=None,max_length=80)
    paper_id:str|None=Field(default=None,max_length=500)

@router.post('/mobile/questions/{qid}/answer')
async def answer(qid:str,body:MobileAnswer,user:Account,response:Response):
    started=perf_counter()
    from .questions import _answer_question
    from ..schemas import AnswerSubmission
    submission=AnswerSubmission(chosen_index=body.chosen_index,collection_id=body.collection_id,paper_id=body.paper_id)
    async with cursor() as cur:
        # Serialize the entire replay/check/write transaction, including source locks.
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('answer-request:'+user+':'+body.request_key,))
        await cur.execute('SELECT 1 FROM practice_request_receipts WHERE user_id=%s AND request_key=%s',(user,body.request_key))
        replay=await cur.fetchone()
        if not replay:
            await cur.execute('SELECT question,options,direction,passage,question_markup,options_markup FROM canonical_questions WHERE id=%s FOR SHARE',(qid,));q=await cur.fetchone()
            if not q:raise HTTPException(404,'Question no longer available')
            if q['question']!=body.expected_question or q['options']!=body.expected_options:
                raise HTTPException(409,'This question changed after you opened it. Refresh and choose again; no answer was recorded.')
            if body.expected_context is not None:
                expected=body.expected_context.model_dump()
                for field in ('direction','passage','question_markup','options_markup'):
                    if q[field]!=expected[field]:
                        raise HTTPException(409,'The question context changed. Refresh before answering; no answer was recorded.')
                from ..source_files import figure_image_url
                await cur.execute('SELECT has_diagram,figure_image FROM appearances WHERE canonical_id=%s AND (%s::text IS NULL OR paper_id=%s) ORDER BY is_primary DESC,id FOR SHARE',(qid,body.paper_id,body.paper_id))
                sources=await cur.fetchall()
                if not any(bool(source['has_diagram'])==expected['has_diagram'] and figure_image_url(source['figure_image'])==expected['figure_image_url'] for source in sources):
                    raise HTTPException(409,'The source figure changed. Refresh before answering; no answer was recorded.')
        result=await _answer_question(qid,submission,user,idempotency_key=body.request_key,_cur=cur,_replay_checked=not replay)
    response.headers['Server-Timing']=f"answer;dur={(perf_counter()-started)*1000:.1f}"
    return result
