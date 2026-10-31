"""Server-earned learning XP and a separate, auditable reward-point wallet."""
import hashlib,hmac,secrets
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Request,Query,Header
from psycopg.types.json import Jsonb
from pydantic import BaseModel,ConfigDict,Field
from ..db import cursor
from ..deps import require_account,current_user
from ..config import settings
from ..services.review_identity import Actor,identity,require_role
from ..services import bank_review
from ..services.learning_rewards import level_bounds,RULE_VERSION
router=APIRouter(prefix='/api',tags=['learning rewards'])
Account=Annotated[str,Depends(require_account)]
Staff=Annotated[Actor,Depends(identity)]

def csrf(request):
    token=request.cookies.get('ism_session','')
    expected=hashlib.sha256(('bank-review:'+token).encode()).hexdigest()
    if not token or request.headers.get('origin')!=settings.public_origin or not hmac.compare_digest(request.headers.get('x-review-csrf',''),expected):raise HTTPException(403,'Refresh the page before saving')

class Visibility(BaseModel):
    model_config=ConfigDict(extra='forbid')
    public:bool
class Redeem(BaseModel):
    model_config=ConfigDict(extra='forbid')
    catalog_id:str=Field(max_length=100)
    version:int=Field(ge=1)
class CatalogUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version:int=Field(ge=1)
    points:int=Field(ge=1,le=1000000)
    enabled:bool
    reason:str=Field(min_length=10,max_length=1000)

@router.get('/rewards/me')
async def wallet(user:Account):
    async with cursor() as cur:
        await cur.execute('SELECT COALESCE(sum(xp),0)::int AS lifetime_xp,COALESCE(sum(points),0)::int AS points FROM reward_ledger WHERE user_id=%s',(user,));totals=await cur.fetchone()
        await cur.execute("SELECT COALESCE(sum(xp),0)::int AS xp FROM reward_ledger WHERE user_id=%s AND created_at>=(date_trunc('month',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",(user,));month=(await cur.fetchone())['xp']
        await cur.execute("SELECT COALESCE(sum(xp),0)::int AS xp FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game') AND created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",(user,));today=(await cur.fetchone())['xp']
        await cur.execute('SELECT board_public FROM reward_profiles WHERE user_id=%s',(user,));profile=await cur.fetchone()
        await cur.execute('SELECT * FROM reward_catalog ORDER BY points,id');catalog=await cur.fetchall()
        await cur.execute('SELECT id,catalog_id,points,starts_at,ends_at,created_at FROM reward_redemptions WHERE user_id=%s ORDER BY created_at DESC LIMIT 20',(user,));redemptions=await cur.fetchall()
    async with cursor() as cur:
        await cur.execute("SELECT (date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata')+interval '1 day') AT TIME ZONE 'Asia/Kolkata' AS resets_at");clock=await cur.fetchone()
        await cur.execute('SELECT kind,sum(xp)::int AS xp FROM reward_ledger WHERE user_id=%s GROUP BY kind',(user,));breakdown=await cur.fetchall()
    bounds=level_bounds(totals['lifetime_xp'])
    return {**totals,'monthly_xp':month,'daily_xp':today,'daily_cap':300,**bounds,'rule_version':RULE_VERSION,'daily_remaining':max(0,300-today),'resets_at':clock['resets_at'],'breakdown':breakdown,'public':bool(profile and profile['board_public']),'catalog':catalog,'redemptions':redemptions,'rules':{'verified_first_correct_xp':10,'verified_first_correct_points':1,'repeat_question_rewards':False,'redemption_cooldown_days':30}}

@router.get('/rewards/history')
async def history(user:Account,before:int|None=None,limit:int=Query(20,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('SELECT id,kind,xp,points,note,created_at FROM reward_ledger WHERE user_id=%s AND (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s',(user,before,before,limit+1));rows=await cur.fetchall()
    return {'items':rows[:limit],'next_cursor':rows[limit-1]['id'] if len(rows)>limit else None}

@router.post('/rewards/visibility')
async def visibility(body:Visibility,request:Request,user:Account):
    csrf(request)
    async with cursor() as cur:
        await cur.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET board_public=EXCLUDED.board_public',(user,body.public))
    return {'public':body.public}

@router.get('/rewards/leaderboard')
async def board(request:Request,period:Literal['week','month','all']='month',offset:int=Query(0,ge=0,le=10000),limit:int=Query(20,ge=1,le=100)):
    from ..services.account_identity import account_session
    account=await account_session(request)
    user=account['user_id'] if account else None
    async with cursor() as cur:
        await cur.execute("""WITH bounds AS(SELECT now() AS as_of,
          CASE WHEN %s='all' THEN NULL ELSE date_trunc(%s,now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' END AS start_at,
          CASE WHEN %s='all' THEN NULL ELSE (date_trunc(%s,now() AT TIME ZONE 'Asia/Kolkata')+CASE WHEN %s='week' THEN interval '1 week' ELSE interval '1 month' END) AT TIME ZONE 'Asia/Kolkata' END AS end_at),
          totals AS(SELECT l.user_id,u.handle,u.avatar,sum(l.xp)::int AS xp
            FROM reward_ledger l JOIN users u ON u.id=l.user_id
            JOIN reward_profiles p ON p.user_id=l.user_id AND p.board_public CROSS JOIN bounds b
            WHERE b.start_at IS NULL OR l.created_at>=b.start_at
            GROUP BY l.user_id,u.handle,u.avatar HAVING sum(l.xp)>0),
          ranked AS(SELECT *,dense_rank() OVER(ORDER BY xp DESC)::int AS rank FROM totals),
          page AS(SELECT user_id,handle,avatar,xp,rank FROM ranked ORDER BY xp DESC,user_id LIMIT %s OFFSET %s)
          SELECT b.*, (SELECT count(*)::int FROM ranked) AS total,
            COALESCE((SELECT jsonb_agg(jsonb_build_object('handle',p.handle,'avatar',p.avatar,'xp',p.xp,'rank',p.rank) ORDER BY p.xp DESC,p.user_id) FROM page p),'[]'::jsonb) AS items,
            (SELECT jsonb_build_object('rank',rank,'xp',xp) FROM ranked WHERE user_id=%s) AS placement
          FROM bounds b""",(period,'week' if period=='week' else 'month',period,'week' if period=='week' else 'month',period,limit,offset,user))
        row=await cur.fetchone()
    return {'items':row['items'],'total':row['total'],'period':period,'timezone':'Asia/Kolkata',
            'period_start':row['start_at'],'period_end':row['end_at'],'as_of':row['as_of'],
            'placement':row['placement'],'rule_version':RULE_VERSION}

@router.post('/rewards/redeem')
async def redeem(body:Redeem,request:Request,user:Account,idempotency_key:Annotated[str,Header(min_length=16,max_length=100)]):
    csrf(request)
    async with cursor() as cur:
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",('rewards:'+user,))
        await cur.execute('SELECT * FROM reward_redemptions WHERE user_id=%s AND idempotency_key=%s',(user,idempotency_key));existing=await cur.fetchone()
        if existing:
            if existing['catalog_id']!=body.catalog_id or existing['catalog_version']!=body.version:raise HTTPException(409,'This redemption key was used for a different offer')
            return existing
        await cur.execute('SELECT * FROM reward_catalog WHERE id=%s FOR SHARE',(body.catalog_id,));offer=await cur.fetchone()
        if not offer or not offer['enabled']:raise HTTPException(409,'This reward is not open for redemption yet')
        if offer['version']!=body.version:raise HTTPException(409,'The reward changed. Refresh before redeeming')
        await cur.execute("SELECT 1 FROM reward_redemptions WHERE user_id=%s AND created_at>now()-interval '30 days'",(user,))
        if await cur.fetchone():raise HTTPException(409,'One subscription reward may be redeemed every 30 days')
        await cur.execute('SELECT COALESCE(sum(points),0) AS balance FROM reward_ledger WHERE user_id=%s',(user,))
        if (await cur.fetchone())['balance']<offer['points']:raise HTTPException(409,'Not enough reward points')
        await cur.execute("SELECT plan_code,plan_status,plan_ends_at,trial_ends_at,razorpay_subscription_id FROM users WHERE id=%s",(user,));plan=await cur.fetchone()
        if plan['razorpay_subscription_id'] and plan['plan_status'] in ('active','authenticated'):raise HTTPException(409,'Redeem after your paid subscription finishes, so rewards do not overlap a renewal')
        if plan['plan_code']=='pro' and plan['plan_status'] in ('active','authenticated') and not plan['plan_ends_at']:raise HTTPException(409,'Your paid subscription must have a known end date before redeeming')
        await cur.execute("SELECT GREATEST(now(),COALESCE(max(ends_at),now()),%s::timestamptz,%s::timestamptz) AS starts FROM reward_redemptions WHERE user_id=%s",(plan['plan_ends_at'] if plan['plan_code']=='pro' else None,plan['trial_ends_at'] if plan['plan_status']=='trial' else None,user));starts=(await cur.fetchone())['starts']
        rid='red_'+secrets.token_hex(16)
        await cur.execute("INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,points,starts_at,ends_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s+make_interval(days=>%s)) RETURNING *",(rid,user,idempotency_key,offer['id'],offer['version'],offer['points'],starts,starts,offer['pro_days']));result=await cur.fetchone()
        await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'redemption',%s,%s)",(user,rid,-offer['points'],offer['title']))
    return result

@router.get('/admin/bank/rewards')
async def admin_catalog(actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM reward_catalog ORDER BY id');return await cur.fetchall()

@router.post('/admin/bank/rewards/{catalog_id}')
async def update_catalog(catalog_id:str,body:CatalogUpdate,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('UPDATE reward_catalog SET points=%s,enabled=%s,version=version+1,updated_at=now() WHERE id=%s AND version=%s RETURNING *',(body.points,body.enabled,catalog_id,body.version));row=await cur.fetchone()
        if not row:raise HTTPException(409,'Offer changed. Reload before saving')
        await bank_review.event(cur,None,actor.id,'reward_catalog_changed',{'catalog_id':catalog_id,'points':body.points,'enabled':body.enabled,'reason':body.reason})
    return row

@router.get('/me/exam-journey/{collection_id}')
async def journey(collection_id:str,user:Annotated[str,Depends(current_user)]):
    async with cursor() as cur:
        await cur.execute("SELECT 1 FROM collections WHERE id=%s AND visibility='public'",(collection_id,))
        if not await cur.fetchone():raise HTTPException(404,'Exam not found')
        await cur.execute('SELECT id,collection_id,section_path,paper_id,answer_mode,started_at FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL ORDER BY started_at DESC LIMIT 1',(user,));active=await cur.fetchone()
        await cur.execute('SELECT id,score,n_correct,n_wrong,n_skipped,submitted_at FROM mock_sessions WHERE user_id=%s AND collection_id=%s AND submitted_at IS NOT NULL ORDER BY submitted_at DESC LIMIT 5',(user,collection_id));recent=await cur.fetchall()
        await cur.execute("SELECT canonical_id,section_path,paper_id,at FROM attempts WHERE user_id=%s AND collection_id=%s AND context='practice' ORDER BY at DESC,id DESC LIMIT 1",(user,collection_id));practice=await cur.fetchone()
        await cur.execute('SELECT state,updated_at FROM exam_study_checkpoints WHERE user_id=%s AND collection_id=%s',(user,collection_id));checkpoint=await cur.fetchone()
    return {'active_mock':active,'recent_results':recent,'last_practice':practice,'checkpoint':checkpoint}


class ExamCheckpoint(BaseModel):
    model_config=ConfigDict(extra='forbid')
    section:str=Field(default='',max_length=160)
    paper:str=Field(default='',max_length=300)
    q:str=Field(default='',max_length=200)
    subject_id:str=Field(default='',max_length=100)
    topic_id:str=Field(default='',max_length=160)
    subtopic_id:str=Field(default='',max_length=160)
    pool:Literal['all','scorable','practice']='scorable'
    status:Literal['all','unseen','answered','wrong']='all'
    offset:int=Field(default=0,ge=0,le=100000)

@router.post('/me/exam-checkpoint/{collection_id}')
async def save_checkpoint(collection_id:str,body:ExamCheckpoint,request:Request,user:Account):
    csrf(request)
    async with cursor() as cur:
        await cur.execute("SELECT live_version FROM collections WHERE id=%s AND visibility='public'",(collection_id,));collection=await cur.fetchone()
        if not collection:raise HTTPException(404,'Exam not found')
        if body.paper:
            await cur.execute('SELECT 1 FROM collection_papers WHERE collection_id=%s AND paper_id=%s',(collection_id,body.paper))
            if not await cur.fetchone():raise HTTPException(422,'Paper does not belong to this exam')
        if body.section:
            await cur.execute('SELECT 1 FROM collection_sections WHERE collection_id=%s AND version=%s AND path=%s',(collection_id,collection['live_version'],body.section))
            if not await cur.fetchone():raise HTTPException(422,'Section does not belong to this exam')
        await cur.execute('INSERT INTO exam_study_checkpoints(user_id,collection_id,state) VALUES(%s,%s,%s) ON CONFLICT(user_id,collection_id) DO UPDATE SET state=EXCLUDED.state,updated_at=now() RETURNING updated_at',(user,collection_id,Jsonb(body.model_dump())));row=await cur.fetchone()
    return {'saved':True,**row}


@router.get('/admin/bank/reward-diagnostics')
async def reward_diagnostics(actor:Staff,email:str|None=Query(None,max_length=254)):
    """Owner-only, read-only reconciliation. Never repairs or changes balances."""
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("""SELECT
          (SELECT count(*) FROM reward_question_claims c LEFT JOIN reward_ledger l ON l.event_key='question:'||c.user_id||':'||c.canonical_id WHERE l.id IS NULL)::int AS claims_without_receipts,
          (SELECT count(*) FROM reward_ledger l WHERE l.event_key LIKE 'question:%' AND NOT EXISTS(SELECT 1 FROM reward_question_claims c WHERE c.user_id=l.user_id AND l.event_key='question:'||c.user_id||':'||c.canonical_id))::int AS receipts_without_claims,
          (SELECT count(*) FROM (SELECT user_id FROM reward_ledger GROUP BY user_id HAVING sum(points)<0) d)::int AS wallets_in_debt,
          (SELECT count(*) FROM (SELECT user_id,(created_at AT TIME ZONE 'Asia/Kolkata')::date AS day FROM reward_ledger WHERE kind IN ('study','game') GROUP BY user_id,day HAVING sum(xp)>300) d)::int AS over_cap_days,
          (SELECT count(*) FROM reward_ledger WHERE rule_version='legacy-v1')::int AS legacy_receipts,
          (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND attempts>=5)::int AS mail_failed,
          (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND attempts<5 AND created_at>now()-interval '30 minutes')::int AS mail_pending,
          (SELECT count(*) FROM account_mail_outbox WHERE sent_at IS NULL AND created_at<=now()-interval '30 minutes')::int AS mail_expired""")
        result=await cur.fetchone()
        result['account']=None
        if email:
            await cur.execute('SELECT id,handle FROM users WHERE lower(email)=%s',(email.strip().lower(),));user=await cur.fetchone()
            if user:
                await cur.execute('SELECT id,kind,xp,points,note,rule_version,source_attempt_id,reverses_id,created_at FROM reward_ledger WHERE user_id=%s ORDER BY id DESC LIMIT 50',(user['id'],));ledger=await cur.fetchall()
                await cur.execute('SELECT action,created_at,detail FROM account_security_events WHERE user_id=%s ORDER BY id DESC LIMIT 25',(user['id'],));events=await cur.fetchall()
                result['account']={'handle':user['handle'],'ledger':ledger,'security_events':events}
        return result
