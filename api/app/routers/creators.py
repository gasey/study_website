"""Opt-in creator identities. Never expose private account/progress/payment data."""
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from pydantic import Field,field_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user,require_account
from ..services.content_studio import Strict
from ..services.community_people import profile_standing
from ..services.profile_identity import PUBLIC_BIO, bio as save_bio
from ..services.review_identity import identity,Actor,require_role
from .materials import private,write_guard
router=APIRouter(prefix='/api',tags=['creators'],dependencies=[Depends(private)])
User=Annotated[str,Depends(current_user)]
Account=Annotated[str,Depends(require_account)]
Staff=Annotated[Actor,Depends(identity)]
class Settings(Strict):
    public:bool
    bio:str=Field(default='',max_length=600)
    expected_bio_version:int|None=Field(default=None,ge=0)
    @field_validator('bio')
    @classmethod
    def clean(cls,v):
        if any(ord(c)<32 and c not in '\n\t' for c in v):raise ValueError('Unsupported control characters')
        return v.strip()
class Toggle(Strict):enabled:bool
class Report(Strict):
    reason:Literal['spam','harassment','impersonation','other']
    note:str=Field(min_length=10,max_length=2000)
class Resolve(Strict):reason:str=Field(min_length=10,max_length=2000)

# Applied in public discovery and direct reading, in both directions.
BLOCKED="EXISTS(SELECT 1 FROM creator_blocks cb WHERE (cb.user_id=%s AND cb.blocked_id=u.id) OR (cb.user_id=u.id AND cb.blocked_id=%s))"
async def graph_lock(cur):
    # A single short graph mutation lock makes privacy/follow/block races serial.
    # No material writes or external work happen under this lock.
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))")
async def event(cur,actor,action,target=None,detail=None):
    await cur.execute('INSERT INTO creator_events(actor_id,action,target_id,detail) VALUES(%s,%s,%s,%s)',(actor,action,target,Jsonb(detail or {})))
async def target(cur,uid,viewer,public=True):
    await cur.execute('SELECT u.id,u.handle,u.avatar,COALESCE(cp.public,false) AS public,'+PUBLIC_BIO+' AS bio FROM users u LEFT JOIN creator_profiles cp ON cp.user_id=u.id WHERE u.id=%s AND u.email IS NOT NULL AND NOT '+BLOCKED,(uid,viewer,viewer))
    row=await cur.fetchone()
    if not row or public and not row['public'] and uid!=viewer:raise HTTPException(404,'Creator profile not available')
    return row

@router.get('/creators/settings')
async def settings(user:Account):
    async with cursor() as cur:
        await cur.execute("SELECT COALESCE(cp.public,false) AS public,COALESCE(cp.bio,'') AS bio,COALESCE(cp.bio_version,0) AS bio_version,COALESCE(cp.bio_needs_approval,false) AS bio_needs_approval,COALESCE(cp.bio_hidden,false) AS bio_hidden,u.id,u.handle FROM users u LEFT JOIN creator_profiles cp ON cp.user_id=u.id WHERE u.id=%s",(user,));row=await cur.fetchone()
        await cur.execute('SELECT u.id,u.handle,COALESCE(cp.public,false) AS public FROM creator_follows f JOIN users u ON u.id=f.creator_id LEFT JOIN creator_profiles cp ON cp.user_id=u.id WHERE f.follower_id=%s ORDER BY f.created_at DESC LIMIT 2001',(user,));following=await cur.fetchall()
        await cur.execute('SELECT u.id,u.handle FROM creator_blocks b JOIN users u ON u.id=b.blocked_id WHERE b.user_id=%s ORDER BY b.created_at DESC LIMIT 2001',(user,));blocked=await cur.fetchall()
    return {**row,'following':following,'blocked':blocked}
@router.post('/creators/settings')
async def save_settings(body:Settings,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await graph_lock(cur)
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
        await cur.execute('SELECT bio_version FROM creator_profiles WHERE user_id=%s FOR UPDATE',(user,))
        prior=await cur.fetchone()
        if body.expected_bio_version is not None and body.expected_bio_version!=(prior['bio_version'] if prior else 0):raise HTTPException(409,'Your bio changed. Reload before saving.')
        await save_bio(cur,user,body.bio)
        await cur.execute('INSERT INTO creator_profiles(user_id,public) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET public=excluded.public,updated_at=clock_timestamp()',(user,body.public))
        await cur.execute('UPDATE users SET identity_version=identity_version+1 WHERE id=%s',(user,))
        await event(cur,user,'profile_settings',user,{'public':body.public})
    return {'saved':True}
@router.get('/creators')
async def directory(user:User,q:str=Query('',max_length=100),offset:int=Query(0,ge=0,le=100000),limit:int=Query(12,ge=1,le=50)):
    async with cursor() as cur:
        where='cp.public AND u.email IS NOT NULL AND NOT '+BLOCKED+' AND (%s=\'\' OR u.handle ILIKE %s)'
        args=(user,user,q,'%'+q+'%')
        await cur.execute('SELECT count(*)::int AS n FROM creator_profiles cp JOIN users u ON u.id=cp.user_id WHERE '+where,args);total=(await cur.fetchone())['n']
        await cur.execute("SELECT u.id,u.handle,u.avatar,"+PUBLIC_BIO+" AS bio,(SELECT count(*)::int FROM materials m WHERE m.author_id=u.id AND m.status='published' AND m.published_revision IS NOT NULL) AS materials FROM creator_profiles cp JOIN users u ON u.id=cp.user_id WHERE "+where+' ORDER BY u.handle,u.id LIMIT %s OFFSET %s',(*args,limit,offset));rows=await cur.fetchall()
    return {'items':rows,'total':total}
@router.get('/creators/{uid}')
async def profile(uid:str,user:User,offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        row=await target(cur,uid,user)
        await cur.execute('SELECT EXISTS(SELECT 1 FROM creator_follows WHERE follower_id=%s AND creator_id=%s) AS following,(SELECT count(*)::int FROM creator_follows f WHERE f.creator_id=%s) AS followers',(user,uid,uid));row.update(await cur.fetchone())
        await cur.execute("SELECT count(*)::int AS n FROM materials WHERE author_id=%s AND status='published' AND published_revision IS NOT NULL",(uid,));row['materials']=(await cur.fetchone())['n']
        row['community']=await profile_standing(cur,uid,user)
        # Honor the existing contribution attribution consent independently.
        await cur.execute("SELECT c.id,c.title,c.kind,c.canonical_id,c.updated_at FROM bank_contributions c JOIN users u ON u.id=c.author_id WHERE c.author_id=%s AND c.state='published' AND u.contribution_public AND NOT EXISTS(SELECT 1 FROM mock_sessions ms WHERE ms.user_id=%s AND ms.submitted_at IS NULL AND c.canonical_id=ANY(ms.question_ids)) ORDER BY c.updated_at DESC,c.id LIMIT 13 OFFSET %s",(uid,user,offset));contributions=await cur.fetchall()
    return {**row,'is_self':uid==user,'contributions':contributions[:12],'has_more_contributions':len(contributions)>12}
@router.post('/creators/{uid}/follow')
async def follow(uid:str,body:Toggle,request:Request,user:Account):
    if uid==user:raise HTTPException(422,'You cannot follow yourself')
    await write_guard(request,user)
    async with cursor() as cur:
        await graph_lock(cur)
        if body.enabled:
            await target(cur,uid,user)
            await cur.execute('SELECT count(*) AS n FROM creator_follows WHERE follower_id=%s',(user,))
            if (await cur.fetchone())['n']>=2000:
                await cur.execute('SELECT 1 FROM creator_follows WHERE follower_id=%s AND creator_id=%s',(user,uid))
                if not await cur.fetchone():raise HTTPException(409,'Following limit reached; unfollow a creator first')
            await cur.execute('INSERT INTO creator_follows(follower_id,creator_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(user,uid))
        else:await cur.execute('DELETE FROM creator_follows WHERE follower_id=%s AND creator_id=%s',(user,uid))
        await event(cur,user,'follow' if body.enabled else 'unfollow',uid)
    return {'following':body.enabled}
@router.post('/creators/{uid}/block')
async def block(uid:str,body:Toggle,request:Request,user:Account):
    if uid==user:raise HTTPException(422,'You cannot block yourself')
    await write_guard(request,user)
    async with cursor() as cur:
        await graph_lock(cur)
        if body.enabled:
            await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(uid,))
            if not await cur.fetchone():raise HTTPException(404,'Creator not found')
            await cur.execute('SELECT count(*) AS n FROM creator_blocks WHERE user_id=%s',(user,))
            if (await cur.fetchone())['n']>=2000:
                await cur.execute('SELECT 1 FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(user,uid))
                if not await cur.fetchone():raise HTTPException(409,'Block limit reached')
            await cur.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(user,uid))
            await cur.execute('DELETE FROM creator_follows WHERE (follower_id=%s AND creator_id=%s) OR (follower_id=%s AND creator_id=%s)',(user,uid,uid,user))
            await cur.execute("UPDATE study_desk_invites SET state='cancelled' WHERE state='pending' AND ((sender_id=%s AND recipient_id=%s) OR (sender_id=%s AND recipient_id=%s))",(user,uid,uid,user))
        else:await cur.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(user,uid))
        await event(cur,user,'block' if body.enabled else 'unblock',uid)
    return {'blocked':body.enabled}
@router.post('/creators/{uid}/report')
async def report(uid:str,body:Report,request:Request,user:Account):
    if uid==user:raise HTTPException(422,'You cannot report yourself')
    await write_guard(request,user)
    async with cursor() as cur:
        # Report before or after blocking without revealing a private profile.
        await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(uid,))
        if not await cur.fetchone():raise HTTPException(404,'Creator not found')
        await cur.execute("INSERT INTO creator_reports(reporter_id,creator_id,reason,note) VALUES(%s,%s,%s,%s) ON CONFLICT(reporter_id,creator_id) DO UPDATE SET reason=EXCLUDED.reason,note=EXCLUDED.note,state='open',resolution=NULL,resolved_by=NULL,updated_at=now()",(user,uid,body.reason,body.note))
        await event(cur,user,'report',uid,body.model_dump())
    return {'saved':True}
@router.get('/admin/bank/creator-reports')
async def reports(actor:Staff,offset:int=Query(0,ge=0,le=100000),report_id:int|None=Query(None,ge=1)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("SELECT r.id,r.creator_id,u.handle,r.reason,r.note,r.updated_at FROM creator_reports r JOIN users u ON u.id=r.creator_id WHERE r.state='open' AND (%s::bigint IS NULL OR r.id=%s) ORDER BY r.id LIMIT 21 OFFSET %s",(report_id,report_id,offset));rows=await cur.fetchall()
    return {'items':rows[:20],'has_more':len(rows)>20}
@router.post('/admin/bank/creator-reports/{rid}/resolve')
async def resolve(rid:int,body:Resolve,request:Request,actor:Staff):
    await write_guard(request,actor.id)
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("UPDATE creator_reports SET state='resolved',resolution=%s,resolved_by=%s,updated_at=now() WHERE id=%s AND state='open' RETURNING creator_id",(body.reason,actor.id,rid));r=await cur.fetchone()
        if not r:raise HTTPException(409,'Report already resolved or missing')
        await event(cur,actor.id,'resolve_report',r['creator_id'],{'report_id':rid,'reason':body.reason})
    return {'resolved':True}


class BioDecision(Strict):
    expected_version:int=Field(ge=0)
    action:Literal['approve','hide']
    reason:str=Field(min_length=10,max_length=2000)

@router.get('/admin/bank/profile-bios')
async def bio_queue(actor:Staff,offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('''SELECT cp.user_id,u.handle,cp.bio,cp.bio_version,cp.bio_needs_approval,cp.bio_hidden
          FROM creator_profiles cp JOIN users u ON u.id=cp.user_id WHERE cp.bio<>'' AND
          (cp.bio_needs_approval OR EXISTS(SELECT 1 FROM creator_reports r WHERE r.creator_id=cp.user_id AND r.state='open'))
          ORDER BY cp.updated_at,cp.user_id LIMIT 21 OFFSET %s''',(offset,))
        rows=await cur.fetchall()
        return {'items':rows[:20],'has_more':len(rows)>20}

@router.post('/admin/bank/profile-bios/{uid}/decision')
async def bio_decision(uid:str,body:BioDecision,request:Request,actor:Staff):
    await write_guard(request,actor.id)
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await graph_lock(cur)
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(uid,))
        await cur.execute('SELECT bio_version,bio FROM creator_profiles WHERE user_id=%s FOR UPDATE',(uid,))
        old=await cur.fetchone()
        if not old:raise HTTPException(404,'Bio not found')
        if old['bio_version']!=body.expected_version:raise HTTPException(409,'This bio changed. Reload before deciding.')
        await cur.execute('UPDATE creator_profiles SET bio_needs_approval=false,bio_hidden=%s,bio_version=bio_version+1,updated_at=clock_timestamp() WHERE user_id=%s',(body.action=='hide',uid))
        await cur.execute('UPDATE users SET identity_version=identity_version+1 WHERE id=%s',(uid,))
        await event(cur,actor.id,'bio_'+body.action,uid,{'version':body.expected_version+1,'bio':old['bio'],'reason':body.reason})
    return {'saved':True}
