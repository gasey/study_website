"""Opt-in creator identities. Never expose private account/progress/payment data."""
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from pydantic import Field,field_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services import audience
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
    await cur.execute('SELECT u.id,u.handle,u.avatar,COALESCE(cp.public,false) AS public,'+PUBLIC_BIO+' AS bio FROM users u LEFT JOIN creator_profiles cp ON cp.user_id=u.id WHERE u.id=%s AND u.email IS NOT NULL AND NOT '+BLOCKED+' AND '+audience.subject_sql('u.id'),(uid,viewer,viewer))
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
async def directory(user:User,q:str=Query('',max_length=100),sort:Literal['discover','alpha']='discover',seed:str=Query('',max_length=64),offset:int=Query(0,ge=0,le=100000),limit:int=Query(12,ge=1,le=50)):
    async with cursor() as cur:
        where='cp.public AND u.email IS NOT NULL AND NOT '+BLOCKED+' AND (%s=\'\' OR u.handle ILIKE %s) AND '+audience.subject_sql('u.id')
        args=(user,user,q,'%'+q+'%')
        await cur.execute('SELECT count(*)::int AS n FROM creator_profiles cp JOIN users u ON u.id=cp.user_id WHERE '+where,args);total=(await cur.fetchone())['n']
        if sort=='discover' and not q.strip():
            rotate=seed.strip() or ''
            await cur.execute("""WITH viewer_exams AS (
                SELECT collection_id FROM user_exam_bookmarks WHERE user_id=%s
              ), pool AS (
                SELECT u.id,u.handle,u.avatar,"""+PUBLIC_BIO+""" AS bio,
                  (SELECT count(*)::int FROM materials m WHERE m.author_id=u.id AND m.status='published' AND m.published_revision IS NOT NULL) AS materials,
                  GREATEST(1, floor(sqrt(GREATEST(0, COALESCE((SELECT sum(rl.xp) FROM reward_ledger rl WHERE rl.user_id=u.id), 0)) / 40.0)))::int AS level,
                  COALESCE((SELECT jsonb_agg(jsonb_build_object('id',c.id,'title',c.title,'is_primary',b.is_primary) ORDER BY b.is_primary DESC,b.created_at DESC)
                    FROM (SELECT collection_id,is_primary,created_at FROM user_exam_bookmarks WHERE user_id=u.id ORDER BY is_primary DESC,created_at DESC LIMIT 3) b
                    JOIN collections c ON c.id=b.collection_id AND c.kind='exam' AND c.visibility='public'),'[]'::jsonb) AS target_exams,
                  EXISTS(SELECT 1 FROM user_exam_bookmarks b JOIN viewer_exams ve ON ve.collection_id=b.collection_id WHERE b.user_id=u.id) AS same_exam,
                  (COALESCE(rp.board_public,false) AND EXISTS(SELECT 1 FROM reward_ledger rl WHERE rl.user_id=u.id AND rl.created_at>=now()-interval '7 days' AND rl.xp>0)) AS active_week
                FROM creator_profiles cp JOIN users u ON u.id=cp.user_id
                LEFT JOIN reward_profiles rp ON rp.user_id=u.id
                WHERE """+where+"""
              )
              SELECT id,handle,avatar,bio,materials,level,target_exams
              FROM pool
              ORDER BY (
                (CASE WHEN same_exam THEN 30 ELSE 0 END)
                + (CASE WHEN active_week THEN 22 ELSE 0 END)
                + (CASE WHEN materials>0 THEN 18 ELSE 0 END)
                + (CASE WHEN avatar IS NOT NULL THEN 8 ELSE 0 END)
                + (abs(hashtext(id || COALESCE(NULLIF(%s,''), to_char(now() AT TIME ZONE 'Asia/Kolkata','YYYY-MM-DD-HH24')))) %% 35)
              ) DESC, handle, id
              LIMIT %s OFFSET %s""",(user,*args,rotate,limit,offset))
            rows=await cur.fetchall()
        else:
            await cur.execute("""SELECT u.id,u.handle,u.avatar,"""+PUBLIC_BIO+""" AS bio,
                (SELECT count(*)::int FROM materials m WHERE m.author_id=u.id AND m.status='published' AND m.published_revision IS NOT NULL) AS materials,
                GREATEST(1, floor(sqrt(GREATEST(0, COALESCE((SELECT sum(rl.xp) FROM reward_ledger rl WHERE rl.user_id=u.id), 0)) / 40.0)))::int AS level,
                COALESCE((SELECT jsonb_agg(jsonb_build_object('id',c.id,'title',c.title,'is_primary',b.is_primary) ORDER BY b.is_primary DESC,b.created_at DESC)
                  FROM (SELECT collection_id,is_primary,created_at FROM user_exam_bookmarks WHERE user_id=u.id ORDER BY is_primary DESC,created_at DESC LIMIT 3) b
                  JOIN collections c ON c.id=b.collection_id AND c.kind='exam' AND c.visibility='public'),'[]'::jsonb) AS target_exams
                FROM creator_profiles cp JOIN users u ON u.id=cp.user_id WHERE """+where+' ORDER BY u.handle,u.id LIMIT %s OFFSET %s',(*args,limit,offset));rows=await cur.fetchall()
    return {'items':rows,'total':total,'sort':sort}


@router.get('/creators/discover')
async def discover_spotlight(user:User,seed:str=Query('',max_length=64),exam_id:str|None=Query(None,max_length=80),limit:int=Query(6,ge=1,le=12)):
    """Algorithmic + rotating spotlight of public learner profiles and published study notes."""
    from ..services.learning_rewards import level_bounds
    from ..services import weekly_boards
    rotate=seed.strip()
    async with cursor() as cur:
        clock=await weekly_boards.window(cur)
        await cur.execute("""WITH viewer_exams AS (
            SELECT collection_id FROM user_exam_bookmarks WHERE user_id=%s
            UNION SELECT %s::text WHERE %s::text IS NOT NULL
          ), pool AS (
            SELECT u.id,u.handle,u.avatar,"""+PUBLIC_BIO+""" AS bio,
              (SELECT count(*)::int FROM materials m WHERE m.author_id=u.id AND m.status='published' AND m.published_revision IS NOT NULL) AS materials,
              COALESCE((SELECT sum(rl.xp)::int FROM reward_ledger rl WHERE rl.user_id=u.id),0) AS lifetime_xp,
              COALESCE((SELECT sum(rl.xp)::int FROM reward_ledger rl WHERE rl.user_id=u.id AND rl.created_at>=%s AND rl.created_at<%s AND rl.created_at<=%s),0) AS raw_weekly_xp,
              COALESCE(rp.board_public,false) AS board_public,
              COALESCE((SELECT jsonb_agg(jsonb_build_object('id',c.id,'title',c.title,'is_primary',b.is_primary) ORDER BY b.is_primary DESC,b.created_at DESC)
                FROM (SELECT collection_id,is_primary,created_at FROM user_exam_bookmarks WHERE user_id=u.id ORDER BY is_primary DESC,created_at DESC LIMIT 3) b
                JOIN collections c ON c.id=b.collection_id AND c.kind='exam' AND c.visibility='public'),'[]'::jsonb) AS target_exams,
              (SELECT c.title FROM user_exam_bookmarks b JOIN viewer_exams ve ON ve.collection_id=b.collection_id JOIN collections c ON c.id=b.collection_id WHERE b.user_id=u.id ORDER BY b.is_primary DESC LIMIT 1) AS shared_exam_title
            FROM creator_profiles cp JOIN users u ON u.id=cp.user_id
            LEFT JOIN reward_profiles rp ON rp.user_id=u.id
            WHERE cp.public AND u.email IS NOT NULL AND u.id IS DISTINCT FROM %s
              AND NOT """+BLOCKED+""" AND """+audience.subject_sql('u.id')+"""
          )
          SELECT id,handle,avatar,bio,materials,lifetime_xp,
            CASE WHEN board_public THEN raw_weekly_xp ELSE NULL END AS weekly_xp,
            target_exams,shared_exam_title,
            CASE
              WHEN shared_exam_title IS NOT NULL THEN 'Same exam · ' || shared_exam_title
              WHEN board_public AND raw_weekly_xp>0 THEN 'Active this week'
              WHEN materials>0 THEN 'Note contributor'
              ELSE 'Mizoram learner'
            END AS match_reason
          FROM pool
          ORDER BY (
            (CASE WHEN shared_exam_title IS NOT NULL THEN 35 ELSE 0 END)
            + (CASE WHEN board_public AND raw_weekly_xp>0 THEN 25 ELSE 0 END)
            + (CASE WHEN materials>0 THEN 20 ELSE 0 END)
            + (CASE WHEN avatar IS NOT NULL THEN 10 ELSE 0 END)
            + (abs(hashtext(id || COALESCE(NULLIF(%s,''), to_char(now() AT TIME ZONE 'Asia/Kolkata','YYYY-MM-DD-HH24')))) %% 40)
          ) DESC, handle, id
          LIMIT %s""",(user,exam_id,exam_id,clock['start_at'],clock['end_at'],clock['as_of'],user,user,user,rotate,limit))
        learner_rows=await cur.fetchall()
        learners=[]
        for r in learner_rows:
            lvl=level_bounds(r['lifetime_xp'])
            learners.append({
                'id':r['id'],
                'handle':r['handle'],
                'avatar':r['avatar'],
                'bio':r['bio'],
                'materials':r['materials'],
                'level':lvl['level'],
                'scholar_title':lvl['title'],
                'weekly_xp':r['weekly_xp'],
                'target_exams':r['target_exams'],
                'match_reason':r['match_reason'],
            })

        await cur.execute("""WITH viewer_exams AS (
            SELECT collection_id FROM user_exam_bookmarks WHERE user_id=%s
            UNION SELECT %s::text WHERE %s::text IS NOT NULL
          )
          SELECT m.id,m.author_id,m.published_at,
            COALESCE(r.payload->>'title',m.title) AS title,
            COALESCE(r.payload->>'summary','') AS summary,
            COALESCE(r.payload->>'kind','note') AS kind,
            COALESCE(cp.public,false) AS creator_public,
            CASE WHEN m.author_id='team' THEN 'Finna Editorial' ELSE COALESCE(u.handle,'Contributor') END AS author,
            (SELECT count(*)::int FROM material_votes v WHERE v.material_id=m.id AND v.helpful) AS helpful,
            (SELECT count(*)::int FROM material_votes v WHERE v.material_id=m.id AND v.studied) AS studied
          FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision
          LEFT JOIN users u ON u.id=m.author_id LEFT JOIN creator_profiles cp ON cp.user_id=m.author_id
          WHERE m.status='published'
            AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%s))
            AND """+audience.subject_sql('m.author_id',team=True)+"""
          ORDER BY (
            (CASE WHEN (r.payload->>'collection_id') IN (SELECT collection_id FROM viewer_exams) THEN 25 ELSE 0 END)
            + LEAST(25, (SELECT count(*)::int FROM material_votes v WHERE v.material_id=m.id AND v.helpful) * 5)
            + (CASE WHEN m.published_at>=now()-interval '30 days' THEN 15 ELSE 0 END)
            + (abs(hashtext(m.id || COALESCE(NULLIF(%s,''), to_char(now() AT TIME ZONE 'Asia/Kolkata','YYYY-MM-DD-HH24')))) %% 35)
          ) DESC, m.published_at DESC
          LIMIT 4""",(user,exam_id,exam_id,user,user,rotate))
        materials=await cur.fetchall()
    return {'learners':learners,'materials':materials,'seed':rotate or 'hourly'}
@router.get('/creators/{uid}')
async def profile(uid:str,user:User,offset:int=Query(0,ge=0,le=100000)):
    from ..services.learning_rewards import level_bounds,league_division
    from ..services import weekly_boards
    async with cursor() as cur:
        row=await target(cur,uid,user)
        await cur.execute('SELECT EXISTS(SELECT 1 FROM creator_follows WHERE follower_id=%s AND creator_id=%s) AS following,(SELECT count(*)::int FROM creator_follows f WHERE f.creator_id=%s AND '+audience.subject_sql('f.follower_id')+') AS followers',(user,uid,uid));row.update(await cur.fetchone())
        await cur.execute("SELECT count(*)::int AS n FROM materials WHERE author_id=%s AND status='published' AND published_revision IS NOT NULL",(uid,));row['materials']=(await cur.fetchone())['n']
        row['community']=await profile_standing(cur,uid,user)
        # Level, scholar title, target exams, and opted-in competitive stats
        await cur.execute('SELECT COALESCE(sum(xp),0)::int AS lifetime_xp FROM reward_ledger WHERE user_id=%s',(uid,))
        lifetime_xp=(await cur.fetchone())['lifetime_xp']
        lvl=level_bounds(lifetime_xp)
        row['level']=lvl['level']
        row['scholar_title']=lvl['title']
        await cur.execute("""SELECT c.id,c.title,b.is_primary
            FROM user_exam_bookmarks b JOIN collections c ON c.id=b.collection_id
            WHERE b.user_id=%s AND c.kind='exam' AND c.visibility='public'
            ORDER BY b.is_primary DESC,b.created_at DESC LIMIT 6""",(uid,))
        row['target_exams']=await cur.fetchall()
        await cur.execute('SELECT COALESCE(board_public,false) AS board_public,district,COALESCE(current_streak_days,0)::int AS streak_days FROM reward_profiles WHERE user_id=%s',(uid,))
        rp=await cur.fetchone()
        board_public=bool(rp['board_public']) if rp else False
        row['board_public']=board_public
        show_scores=board_public or uid==user
        row['district']=(rp['district'] if rp and show_scores else None)
        if show_scores:
            clock=await weekly_boards.window(cur)
            await cur.execute("""SELECT COALESCE(sum(xp),0)::int AS weekly_xp FROM reward_ledger
                WHERE user_id=%s AND created_at>=%s AND created_at<%s AND created_at<=%s""",(uid,clock['start_at'],clock['end_at'],clock['as_of']))
            weekly_xp=(await cur.fetchone())['weekly_xp']
            await cur.execute("""SELECT count(*)::int AS plays, COALESCE(max(m.score),0)::int AS best
                FROM game_daily_entries e JOIN game_rooms r ON r.id=e.room_id AND r.state='finished'
                JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id AND m.left_at IS NULL
                WHERE e.user_id=%s AND m.correct+m.wrong>0""",(uid,))
            daily_row=await cur.fetchone()
            await cur.execute("""SELECT count(*)::int AS plays, COALESCE(max(m.score),0)::int AS best
                FROM game_cup_entries e JOIN game_rooms r ON r.id=e.room_id AND r.state='finished'
                JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id AND m.left_at IS NULL
                WHERE e.user_id=%s AND m.correct+m.wrong>0""",(uid,))
            cup_row=await cur.fetchone()
            await cur.execute("""SELECT count(*)::int AS wins FROM game_members m JOIN game_rooms r ON r.id=m.room_id
                WHERE m.user_id=%s AND r.mode='duel' AND r.state='finished' AND m.left_at IS NULL AND m.correct+m.wrong>0
                AND EXISTS(SELECT 1 FROM game_members o WHERE o.room_id=r.id AND o.user_id<>m.user_id AND o.left_at IS NULL AND o.correct+o.wrong>0)
                AND NOT EXISTS(SELECT 1 FROM game_members o WHERE o.room_id=r.id AND o.user_id<>m.user_id AND o.left_at IS NULL AND o.score>=m.score)""",(uid,))
            duel_wins=(await cur.fetchone())['wins']
            await cur.execute("""SELECT COALESCE(max(score),0)::int AS best, count(*)::int AS runs
                FROM block_puzzle_runs WHERE user_id=%s AND score>0""",(uid,))
            blocks_row=await cur.fetchone()
            row['scores']={
                'weekly_xp':weekly_xp,
                'league':league_division(weekly_xp)['name'],
                'lifetime_xp':lifetime_xp,
                'streak_days':rp['streak_days'] if rp else 0,
                'daily_five_plays':daily_row['plays'] if daily_row else 0,
                'daily_five_best':daily_row['best'] if daily_row else 0,
                'cup_plays':cup_row['plays'] if cup_row else 0,
                'cup_best':cup_row['best'] if cup_row else 0,
                'duel_wins':duel_wins,
                'blocks_best':blocks_row['best'] if blocks_row else 0,
                'blocks_runs':blocks_row['runs'] if blocks_row else 0,
            }
        else:
            row['scores']=None
        # Public study & community activity summary counts (no private spoilers/answers).
        await cur.execute("""SELECT
            (SELECT count(DISTINCT canonical_id)::int FROM attempts WHERE user_id=%s AND canonical_id IS NOT NULL) AS questions_answered,
            (SELECT count(DISTINCT canonical_id)::int FROM attempts WHERE user_id=%s AND canonical_id IS NOT NULL AND correct) AS questions_correct,
            (SELECT count(*)::int FROM (
                SELECT question_id AS qid FROM user_question_bookmarks WHERE user_id=%s
                UNION
                SELECT canonical_question_id AS qid FROM personal_vault_items WHERE user_id=%s AND canonical_question_id IS NOT NULL
            ) sq) AS saved_questions,
            (SELECT count(*)::int FROM posts WHERE author_id=%s AND kind IN ('study','material-share') AND parent_id IS NULL AND NOT hidden AND NOT before_fix AND NOT needs_approval) AS posts_count,
            (SELECT count(*)::int FROM posts WHERE author_id=%s AND kind='doubt' AND canonical_id IS NOT NULL AND NOT hidden AND NOT before_fix AND NOT needs_approval) AS doubts_count,
            (SELECT count(*)::int FROM posts WHERE author_id=%s AND kind IN ('explanation','reply') AND canonical_id IS NOT NULL AND NOT hidden AND NOT before_fix AND NOT needs_approval) AS answers_count,
            (SELECT count(*)::int FROM personal_vault_shares WHERE owner_id=%s) AS shared_packs_count,
            (SELECT count(*)::int FROM learning_catalog WHERE author_id=%s AND live_payload IS NOT NULL AND live_test_version IS NOT NULL) AS shared_tests_count""",
            (uid,uid,uid,uid,uid,uid,uid,uid,uid))
        act=dict(await cur.fetchone())
        if not show_scores:
            act['questions_correct']=None
        row['activity']=act
        # Honor the existing contribution attribution consent independently.
        await cur.execute("SELECT c.id,c.title,c.kind,c.canonical_id,c.updated_at FROM bank_contributions c JOIN users u ON u.id=c.author_id WHERE c.author_id=%s AND c.state='published' AND u.contribution_public AND NOT EXISTS(SELECT 1 FROM mock_sessions ms WHERE ms.user_id=%s AND ms.submitted_at IS NULL AND c.canonical_id=ANY(ms.question_ids)) ORDER BY c.updated_at DESC,c.id LIMIT 13 OFFSET %s",(uid,user,offset));contributions=await cur.fetchall()
    return {**row,'is_self':uid==user,'contributions':contributions[:12],'has_more_contributions':len(contributions)>12}


ACTIVE_EXAM_GUARD = """
  NOT EXISTS(SELECT 1 FROM mock_sessions ms WHERE ms.user_id=%(viewer)s AND ms.submitted_at IS NULL AND q.id=ANY(ms.question_ids))
  AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id LEFT JOIN game_cups cup ON cup.id=gr.cup_id
    WHERE gm.user_id=%(viewer)s AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
    AND gr.questions @> jsonb_build_array(jsonb_build_object('id',q.id)))
"""

VIEWER_UNLOCKED_Q = """(
  %(viewer)s = %(uid)s
  OR EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=%(viewer)s AND a.canonical_id=q.id)
  OR EXISTS(SELECT 1 FROM answer_reveals ar WHERE ar.user_id=%(viewer)s AND ar.canonical_id=q.id)
  OR EXISTS(SELECT 1 FROM discussion_disclosures d WHERE d.user_id=%(viewer)s AND d.canonical_id=q.id)
)"""


@router.get('/creators/{uid}/activity')
async def creator_activity(
    uid: str,
    user: User,
    tab: Literal['posts', 'doubts', 'saved', 'answered'] = Query('posts'),
    offset: int = Query(0, ge=0, le=100000),
    limit: int = Query(12, ge=1, le=30),
):
    from ..services.community_policy import helpful_count
    from ..services.study_posts import reference_visible
    async with cursor() as cur:
        await target(cur, uid, user)
        await cur.execute('SELECT COALESCE(board_public,false) AS board_public FROM reward_profiles WHERE user_id=%s', (uid,))
        rp = await cur.fetchone()
        show_scores = bool(rp and rp['board_public']) or uid == user
        params = {'uid': uid, 'viewer': user, 'user': user, 'limit': limit + 1, 'offset': offset, 'scope': 'all'}

        if tab == 'posts':
            sql = f"""SELECT p.id, p.kind, p.body, p.topic_tag, t.label AS topic_label,
                    p.source_context->'study_reference' AS reference,
                    {helpful_count()} AS helpful,
                    (SELECT count(*)::int FROM posts r WHERE r.parent_id=p.id AND NOT r.hidden AND NOT r.before_fix AND NOT r.needs_approval) AS reply_count,
                    p.created_at
                FROM posts p
                LEFT JOIN review_taxonomy t ON t.id=p.topic_tag
                LEFT JOIN canonical_questions q ON q.id=CASE WHEN p.source_context->'study_reference'->>'kind'='question' THEN p.source_context->'study_reference'->>'id' END
                WHERE p.author_id=%(uid)s
                  AND p.kind IN ('study','material-share')
                  AND p.parent_id IS NULL
                  AND NOT p.hidden AND NOT p.before_fix
                  AND (NOT p.needs_approval OR p.author_id=%(viewer)s)
                  AND {reference_visible()}
                  AND (q.id IS NULL OR (q.status IN ('live','held') AND {ACTIVE_EXAM_GUARD}))
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT %(limit)s OFFSET %(offset)s"""
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            return {'tab': tab, 'items': rows[:limit], 'has_more': len(rows) > limit}

        if tab == 'doubts':
            sql = f"""SELECT p.id, p.kind, p.canonical_id, p.accepted, p.pinned, p.created_at,
                    q.question, q.subject, q.topic,
                    {helpful_count()} AS helpful,
                    {VIEWER_UNLOCKED_Q} AS unlocked,
                    CASE WHEN {VIEWER_UNLOCKED_Q} THEN p.body ELSE NULL END AS body
                FROM posts p
                JOIN canonical_questions q ON q.id=p.canonical_id
                WHERE p.author_id=%(uid)s
                  AND p.kind IN ('doubt','explanation','reply')
                  AND p.canonical_id IS NOT NULL
                  AND NOT p.hidden AND NOT p.before_fix
                  AND (NOT p.needs_approval OR p.author_id=%(viewer)s)
                  AND q.status IN ('live','held')
                  AND {ACTIVE_EXAM_GUARD}
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT %(limit)s OFFSET %(offset)s"""
            await cur.execute(sql, params)
            rows = [dict(r) for r in await cur.fetchall()]
            for r in rows:
                r['spoiler_locked'] = not bool(r.pop('unlocked'))
            return {'tab': tab, 'items': rows[:limit], 'has_more': len(rows) > limit}

        if tab == 'saved':
            shared_packs = []
            shared_tests = []
            if offset == 0:
                await cur.execute(
                    """SELECT token, title, description, mode, duration_minutes,
                              jsonb_array_length(COALESCE(items,'[]'::jsonb))::int AS item_count,
                              clones_count, created_at
                         FROM personal_vault_shares
                        WHERE owner_id=%s
                        ORDER BY created_at DESC LIMIT 8""",
                    (uid,),
                )
                shared_packs = await cur.fetchall()
                await cur.execute(
                    """SELECT p.entry_id,
                              COALESCE(p.payload->>'title', c.id) AS title,
                              COALESCE(p.payload->>'description', '') AS description,
                              jsonb_array_length(COALESCE(p.payload->'question_ids','[]'::jsonb))::int AS question_count,
                              COALESCE((p.payload->'config'->>'duration_minutes')::int, 0) AS duration_minutes,
                              p.published_at
                         FROM learning_catalog c
                         JOIN learning_test_publications p ON p.entry_id=c.id AND p.revision=c.live_test_version
                        WHERE c.author_id=%s AND c.live_payload IS NOT NULL
                        ORDER BY p.published_at DESC LIMIT 8""",
                    (uid,),
                )
                shared_tests = await cur.fetchall()

            sql = f"""WITH saved_union AS (
                    SELECT question_id AS canonical_id, created_at AS saved_at
                      FROM user_question_bookmarks WHERE user_id=%(uid)s
                    UNION ALL
                    SELECT canonical_question_id AS canonical_id, updated_at AS saved_at
                      FROM personal_vault_items WHERE user_id=%(uid)s AND canonical_question_id IS NOT NULL
                ), dedup AS (
                    SELECT canonical_id, max(saved_at) AS saved_at
                      FROM saved_union
                     GROUP BY canonical_id
                )
                SELECT d.canonical_id, d.saved_at, q.question, q.subject, q.topic
                  FROM dedup d
                  JOIN canonical_questions q ON q.id=d.canonical_id
                 WHERE q.status IN ('live','held')
                   AND {ACTIVE_EXAM_GUARD}
                 ORDER BY d.saved_at DESC, d.canonical_id
                 LIMIT %(limit)s OFFSET %(offset)s"""
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            return {
                'tab': tab,
                'items': rows[:limit],
                'has_more': len(rows) > limit,
                'shared_packs': shared_packs,
                'shared_tests': shared_tests,
            }

        # tab == 'answered'
        sql = f"""WITH latest AS (
                SELECT DISTINCT ON (a.canonical_id)
                       a.canonical_id, a.correct, a.at AS answered_at
                  FROM attempts a
                 WHERE a.user_id=%(uid)s AND a.canonical_id IS NOT NULL
                 ORDER BY a.canonical_id, a.at DESC, a.id DESC
            )
            SELECT l.canonical_id, l.answered_at, q.question, q.subject, q.topic,
                   CASE WHEN %(show_scores)s AND {VIEWER_UNLOCKED_Q}
                        THEN (CASE WHEN l.correct THEN 'correct' ELSE 'wrong' END)
                        ELSE NULL END AS outcome
              FROM latest l
              JOIN canonical_questions q ON q.id=l.canonical_id
             WHERE q.status IN ('live','held')
               AND {ACTIVE_EXAM_GUARD}
             ORDER BY l.answered_at DESC, l.canonical_id
             LIMIT %(limit)s OFFSET %(offset)s"""
        await cur.execute(sql, {**params, 'show_scores': show_scores})
        rows = await cur.fetchall()
        return {'tab': tab, 'items': rows[:limit], 'has_more': len(rows) > limit}
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
