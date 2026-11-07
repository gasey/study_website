from typing import Annotated, Literal
from datetime import timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..services import games as g
from ..services import game_selection as setup
from .materials import write_guard

router = APIRouter(prefix="/api/games", tags=["games"])
Account = Annotated[str, Depends(require_account)]
User = Annotated[str, Depends(current_user)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Create(Strict):
    mode: Literal["gauntlet", "speed", "duel", "party", "cup"]
    subject_id: str | None = Field(default=None, max_length=100)
    selection: setup.Selection | None = None
    preview_hash: str | None = Field(default=None,pattern=r"^[0-9a-f]{64}$")
    matchmaking: bool = False
    public_result: bool = False
    request_key: str = Field(min_length=16, max_length=100)


class Preview(Strict):
    mode:Literal["gauntlet","speed","duel","party","cup"]
    selection:setup.Selection

class Ready(Strict):
    ready:bool

class Join(Strict):
    code: str = Field(min_length=12, max_length=12, pattern="^[A-Fa-f0-9]{12}$")
    context_hash:str|None=Field(default=None,pattern=r"^[0-9a-f]{64}$")


class Answer(Strict):
    position: int = Field(ge=0, le=24)
    chosen_index: int | None = Field(default=None, ge=0, le=5)


class CupVisibility(Strict):
    cup_id: str = Field(min_length=10, max_length=20)
    enabled: bool


class Empty(Strict):
    pass


def private(response):
    response.headers["Cache-Control"] = "private, no-store"


async def activity_lock(cur, user):
    await cur.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))", ("learning-session:" + user,)
    )


async def availability(cur, user):
    await cur.execute(
        "SELECT r.id FROM game_members m JOIN game_rooms r ON r.id=m.room_id WHERE m.user_id=%s AND m.released_at IS NULL",
        (user,),
    )
    row = await cur.fetchone()
    if row:
        raise HTTPException(
            409, "Resume or leave your current game before starting another"
        )


async def add_member(cur, r, user, public=False):
    await cur.execute(
        "SELECT count(*) AS n FROM game_members WHERE room_id=%s AND left_at IS NULL",
        (r["id"],),
    )
    if (await cur.fetchone())["n"] >= r["capacity"]:
        raise HTTPException(409, "This game is full")
    await cur.execute(
        "SELECT 1 FROM game_members m JOIN creator_blocks b ON (b.user_id=%s AND b.blocked_id=m.user_id) OR (b.blocked_id=%s AND b.user_id=m.user_id) WHERE m.room_id=%s AND m.left_at IS NULL",
        (user, user, r["id"]),
    )
    if await cur.fetchone():
        raise HTTPException(403, "This game is not available")
    await cur.execute(
        "INSERT INTO game_members(room_id,user_id,public_result) VALUES(%s,%s,%s) ON CONFLICT(room_id,user_id) DO UPDATE SET left_at=NULL,released_at=NULL,joined_at=now(),ready=false,public_result=excluded.public_result",
        (r["id"], user, public),
    )
    await cur.execute("UPDATE game_rooms SET version=version+1 WHERE id=%s", (r["id"],))
    await g.event(cur, r["id"], user, "joined")


@router.get("")
async def catalog(user: User, response: Response):
    private(response)
    async with cursor() as cur:
        now = await g.clock(cur)
        await cur.execute(
            "SELECT r.id,r.mode,r.state FROM game_members m JOIN game_rooms r ON r.id=m.room_id WHERE m.user_id=%s AND m.released_at IS NULL",
            (user,),
        )
        active = await cur.fetchone()
        await cur.execute(
            "SELECT m.room_id AS id,r.mode,r.state,m.score,m.correct,m.wrong,m.excluded,m.distance,m.pace_bonus,m.streak_bonus,m.courage_bonus,m.best_streak,r.finished_at FROM game_members m JOIN game_rooms r ON r.id=m.room_id WHERE m.user_id=%s AND r.state IN ('finished','cancelled') ORDER BY r.finished_at DESC LIMIT 10",
            (user,),
        )
        history = await cur.fetchall()
        await cur.execute("""SELECT m.id,m.collection_id,c.title AS collection_title,m.section_path,m.paper_id,m.answer_mode,
            GREATEST(0,m.duration_seconds-EXTRACT(EPOCH FROM (now()-m.started_at)))::int AS seconds_remaining
            FROM mock_sessions m LEFT JOIN collections c ON c.id=m.collection_id
            WHERE m.user_id=%s AND m.submitted_at IS NULL LIMIT 1""",(user,))
        active_mock=await cur.fetchone()
        if active_mock:
            from urllib.parse import quote,urlencode
            filters={}
            if active_mock['paper_id']:filters['paper']=active_mock['paper_id']
            elif active_mock['section_path']:filters['section']=active_mock['section_path']
            if active_mock['answer_mode']=='derived-practice':filters['mode']='derived'
            active_mock['resume_url']='/exams/'+quote(active_mock['collection_id'],safe='')+'/mock'+('?' + urlencode(filters) if filters else '')
        await cur.execute(
            "SELECT COALESCE(sum(xp),0)::int AS xp FROM reward_ledger WHERE user_id=%s AND kind='game' AND created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",
            (user,),
        )
        xp = (await cur.fetchone())["xp"]
        await cur.execute(
            "SELECT qc.subject_id AS id,max(qc.subject_label) AS title,count(DISTINCT v.id)::int AS questions FROM v_question_paths qc JOIN v_launch_scorable v ON v.id=qc.question_id WHERE qc.review_status='approved' GROUP BY qc.subject_id HAVING count(DISTINCT v.id)>=10 ORDER BY title"
        )
        subjects = await cur.fetchall()
        cid, opens, closes = g.cup_window(now)
        await cur.execute(
            "SELECT room_id FROM game_cup_entries WHERE cup_id=%s AND user_id=%s",
            (cid, user),
        )
        entry = await cur.fetchone()
        await cur.execute(
            "SELECT count(*)::int AS n FROM game_cup_entries WHERE cup_id=%s", (cid,)
        )
        entries = (await cur.fetchone())["n"]
        await cur.execute(
            "SELECT email IS NOT NULL AS registered FROM users WHERE id=%s", (user,)
        )
        registered = (await cur.fetchone())["registered"]
        selection_catalog=await setup.catalog(cur,user)
        return {
            "setup":selection_catalog,
            "registered": registered,
            "active": active,
            "active_mock": active_mock,
            "history": history,
            "game_xp_today": xp,
            "shared_daily_xp_cap": 300,
            "subjects": subjects,
            "cup": {
                "id": cid,
                "opens_at": opens,
                "closes_at": closes,
                "entry_room": entry["room_id"] if entry else None,
                "entries": entries,
            },
            "server_now": now,
        }


@router.post('/preview')
async def preview_selection(body:Preview,user:User,response:Response):
    private(response)
    async with cursor()as cur:
        result=await setup.preview(cur,body.selection,body.mode)
        return {k:v for k,v in result.items()if k!='context'}

@router.get('/exam-sections')
async def game_exam_sections(user:User,response:Response,collection_id:str=Query(max_length=120)):
    private(response)
    async with cursor()as cur:
        await setup.resolve(cur,setup.Selection(kind='exam',collection_id=collection_id),'speed')
        await cur.execute("SELECT s.path,s.title FROM collection_sections s JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version WHERE c.id=%s ORDER BY s.position,s.path",(collection_id,))
        return await cur.fetchall()

@router.get('/join-preview')
async def join_preview(user:Account,response:Response,code:str=Query(pattern='^[A-Fa-f0-9]{12}$')):
    private(response)
    async with cursor()as cur:
        await g.permitted(cur,user)
        await cur.execute("SELECT r.* FROM game_rooms r WHERE r.join_code=%s AND r.state='waiting'AND r.created_at>now()-interval '10 minutes' AND NOT EXISTS(SELECT 1 FROM game_members m JOIN creator_blocks b ON(b.user_id=%s AND b.blocked_id=m.user_id)OR(b.blocked_id=%s AND b.user_id=m.user_id)WHERE m.room_id=r.id AND m.left_at IS NULL)",(code.upper(),user,user))
        r=await cur.fetchone()
        if not r:raise HTTPException(404,'This room is unavailable, expired or full')
        await cur.execute('SELECT count(*)AS n FROM game_members WHERE room_id=%s AND left_at IS NULL',(r['id'],));n=(await cur.fetchone())['n']
        if n>=r['capacity']:raise HTTPException(409,'This room is full')
        ctx=r.get('selection_context')
        return {'mode':r['mode'],'players':n,'capacity':r['capacity'],'context_hash':r.get('context_hash'),'label':ctx['label']if ctx else'Legacy room · '+(r['subject_id']or'Mixed subjects'),'source_label':ctx['source_label']if ctx else'MPSC & Mizoram recruitment','questions':len(r['questions']),'round_seconds':r['round_seconds'],'excluded_labels':ctx.get('excluded_labels',[])if ctx else[]}

@router.post('/rooms/{rid}/ready')
async def mark_ready(rid:str,body:Ready,request:Request,user:Account,response:Response):
    private(response)
    await write_guard(request,user)
    async with cursor()as cur:
        r=await g.room(cur,rid);m=await g.member(cur,r,user);await g.permitted(cur,user)
        now=await g.clock(cur);r=await g.advance(cur,r,now)
        if r['state']!='waiting'or m['left_at']:raise HTTPException(409,'This lobby is no longer accepting readiness')
        await cur.execute('UPDATE game_members SET ready=%s WHERE room_id=%s AND user_id=%s',(body.ready,rid,user));await cur.execute('UPDATE game_rooms SET version=version+1 WHERE id=%s',(rid,));await g.event(cur,rid,user,'ready',{'ready':body.ready})
        await cur.execute('SELECT count(*)AS n,bool_and(ready)AS all_ready FROM game_members WHERE room_id=%s AND left_at IS NULL',(rid,));state=await cur.fetchone()
        if r['mode']=='duel'and state['n']==2 and state['all_ready']:r=await g.start(cur,r,now)
        else:r=await g.room(cur,rid)
        return await g.view(cur,r,user,now)

@router.post("/rooms")
async def create(body: Create, request: Request, user: Account, response: Response):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        await activity_lock(cur, user)
        await cur.execute(
            "SELECT room_id AS id,request_hash FROM game_start_requests WHERE user_id=%s AND request_key=%s",
            (user, body.request_key),
        )
        old = await cur.fetchone()
        dumped=body.model_dump()
        if body.selection is None:
            dumped.pop("selection");dumped.pop("preview_hash")
        h = g.digest(dumped)
        if old:
            if old["request_hash"] != h:
                raise HTTPException(
                    409, "Start request was already used for a different game"
                )
            r = await g.advance(cur, await g.room(cur, old["id"]), await g.clock(cur))
            return await g.view(cur, r, user, await g.clock(cur))
        await g.permitted(cur, user)
        await availability(cur, user)
        now = await g.clock(cur)
        if body.matchmaking and body.mode != "duel":
            raise HTTPException(422, "Random matching is available for duels")
        if body.mode == "cup" and body.subject_id:
            raise HTTPException(
                422, "The weekly cup uses the same mixed verified-key set for everyone"
            )
        if body.selection is None or not body.preview_hash:
            raise HTTPException(422,"Choose an area and confirm the game preview before starting")
        if body.subject_id:raise HTTPException(422,"Use the confirmed area instead of a separate subject filter")
        selected=await setup.preview(cur,body.selection,body.mode)
        if selected['context_hash']!=body.preview_hash:raise HTTPException(409,"This selection changed. Refresh the preview and confirm it again.")
        if not selected['can_start']:raise HTTPException(422,selected['message'])
        context=selected['context'];context_hash=selected['context_hash']
        if body.matchmaking:
            await cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))"
            )
            await cur.execute(
                "SELECT r.id FROM game_rooms r WHERE r.mode='duel' AND r.matchmaking AND r.state='waiting' AND r.context_hash=%s AND r.owner_id<>%s AND (SELECT count(*)FROM game_members gm WHERE gm.room_id=r.id AND gm.left_at IS NULL)<r.capacity AND r.created_at>%s-interval '10 minutes' AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=r.owner_id) OR (b.blocked_id=%s AND b.user_id=r.owner_id)) ORDER BY r.created_at LIMIT 1 FOR UPDATE SKIP LOCKED",
                (context_hash, user, now, user, user),
            )
            match = await cur.fetchone()
            if match:
                r = await g.room(cur, match["id"])
                await add_member(cur, r, user)
                await cur.execute("INSERT INTO game_preferences(user_id,selection)VALUES(%s,%s)ON CONFLICT(user_id)DO UPDATE SET selection=excluded.selection,updated_at=now()",(user,Jsonb(context['selector'])))
                # Both matched players explicitly ready in the shared lobby.
                r = await g.room(cur,r["id"])
                await cur.execute(
                    "INSERT INTO game_start_requests(user_id,request_key,room_id,request_hash) VALUES(%s,%s,%s,%s)",
                    (user, body.request_key, r["id"], h),
                )
                return await g.view(cur, r, user, now)
        count, seconds, capacity = g.MODES[body.mode]
        cup_id = None
        if body.mode == "cup":
            c = await g.cup(cur, now)
            if (
                not c["opens_at"]
                <= now
                <= c["closes_at"] - timedelta(seconds=count * seconds)
            ):
                raise HTTPException(
                    409,
                    "Weekly cup opens Sunday at 7 pm India time; last start is 7:47:30 pm",
                )
            await cur.execute(
                "SELECT room_id FROM game_cup_entries WHERE cup_id=%s AND user_id=%s",
                (c["id"], user),
            )
            if await cur.fetchone():
                raise HTTPException(409, "One weekly cup attempt per account")
            questions = c["questions"]
            cup_id = c["id"]
        else:
            questions = await setup.draw(cur,context)
        rid = "game_" + uuid4().hex
        code = None if capacity == 1 else g.secrets.token_hex(6).upper()
        await cur.execute(
            "INSERT INTO game_rooms(id,owner_id,mode,subject_id,capacity,join_code,matchmaking,cup_id,questions,round_seconds,request_key,request_hash,selection_context,context_hash) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                rid,
                user,
                body.mode,
                body.subject_id,
                capacity,
                code,
                body.matchmaking,
                cup_id,
                Jsonb(questions),
                seconds,
                body.request_key,
                h,Jsonb(context),context_hash,
            ),
        )
        r = await g.room(cur, rid)
        await add_member(cur, r, user, body.public_result)
        await cur.execute(
            "INSERT INTO game_start_requests(user_id,request_key,room_id,request_hash) VALUES(%s,%s,%s,%s)",
            (user, body.request_key, rid, h),
        )
        if cup_id:
            await cur.execute(
                "INSERT INTO game_cup_entries(cup_id,user_id,room_id) VALUES(%s,%s,%s)",
                (cup_id, user, rid),
            )
        if body.mode!='cup':
            await cur.execute("INSERT INTO game_preferences(user_id,selection)VALUES(%s,%s)ON CONFLICT(user_id)DO UPDATE SET selection=excluded.selection,updated_at=now()",(user,Jsonb(context['selector'])))
        if capacity == 1:
            r = await g.start(cur, r, now)
        return await g.view(cur, r, user, now)


@router.post("/join")
async def join(body: Join, request: Request, user: Account, response: Response):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        await activity_lock(cur, user)
        await g.permitted(cur, user)
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))"
        )
        await cur.execute(
            "SELECT id FROM game_rooms WHERE join_code=%s", (body.code.upper(),)
        )
        found = await cur.fetchone()
        if not found:
            raise HTTPException(404, "Room code not found")
        now = await g.clock(cur)
        r = await g.advance(cur, await g.room(cur, found["id"]), now)
        await cur.execute(
            "SELECT 1 FROM game_members WHERE room_id=%s AND user_id=%s AND left_at IS NULL",
            (r["id"], user),
        )
        if await cur.fetchone():
            return await g.view(cur, r, user, now)
        await availability(cur, user)
        if r["state"] != "waiting":
            raise HTTPException(409, "This room has started or expired")
        if r.get("context_hash")and body.context_hash!=r["context_hash"]:raise HTTPException(409,"Preview this room and accept its area before joining")
        await add_member(cur, r, user)
        if r["mode"] == "duel"and not r.get("selection_context"):
            r = await g.start(cur, r, now)
        return await g.view(cur, await g.room(cur, r["id"]), user, now)


@router.get("/rooms/{rid}")
async def read_room(rid: str, user: Account, response: Response):
    private(response)
    async with cursor() as cur:
        r = await g.room(cur, rid)
        await g.member(cur, r, user)
        now = await g.clock(cur)
        r = await g.advance(cur, r, now)
        return await g.view(cur, r, user, now)


@router.post("/rooms/{rid}/start")
async def start_room(
    rid: str, body: Empty, request: Request, user: Account, response: Response
):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        r = await g.room(cur, rid)
        await g.member(cur, r, user)
        await g.permitted(cur, user)
        if r["owner_id"] != user:
            raise HTTPException(403, "Only the host can start this room")
        now = await g.clock(cur)
        r = await g.advance(cur, r, now)
        if r["state"] == "waiting":
            r = await g.start(cur, r, now)
        return await g.view(cur, r, user, now)


@router.post("/rooms/{rid}/answer")
async def answer(
    rid: str, body: Answer, request: Request, user: Account, response: Response
):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        r = await g.room(cur, rid)
        m = await g.member(cur, r, user)
        await g.permitted(cur, user)
        now = await g.clock(cur)
        await cur.execute(
            "SELECT chosen_index FROM game_answers WHERE room_id=%s AND user_id=%s AND position=%s",
            (rid, user, body.position),
        )
        previous = await cur.fetchone()
        if previous:
            if previous["chosen_index"] != body.chosen_index:
                raise HTTPException(409, "This answer has already been recorded")
            r = await g.advance(cur, r, now)
            return await g.view(cur, r, user, now)
        if r["state"] != "running" or m["left_at"]:
            raise HTTPException(409, "This game is not accepting answers")
        if now >= r["round_ends_at"] or now >= r["deadline"]:
            r = await g.advance(cur, r, now)
            return await g.view(cur, r, user, now)
        if body.position != r["current_position"]:
            raise HTTPException(
                409, "The round has changed; reload the current question"
            )
        if r["mode"]=="trail" and r["trail_phase"]!="question":raise HTTPException(409,"Reveal the next trail question first")
        q = r["questions"][body.position]
        if body.chosen_index is not None and body.chosen_index >= len(q["options"]):
            raise HTTPException(422, "Choose an available option")
        correct = (
            body.chosen_index is not None
            and q["options"][body.chosen_index] == q["answer_text"]
        )
        elapsed = max(0, int((now - r["round_started_at"]).total_seconds() * 1000))
        await cur.execute(
            "INSERT INTO game_answers(room_id,user_id,position,chosen_index,correct,elapsed_ms) VALUES(%s,%s,%s,%s,%s,%s)",
            (rid, user, body.position, body.chosen_index, correct, elapsed),
        )
        await cur.execute("UPDATE game_rooms SET version=version+1 WHERE id=%s", (rid,))
        if r["mode"] == "gauntlet":
            if correct:
                await cur.execute(
                    "UPDATE game_members SET streak=streak+1,distance=distance+100*LEAST(streak+1,5) WHERE room_id=%s AND user_id=%s",
                    (rid, user),
                )
            else:
                await cur.execute(
                    "UPDATE game_members SET lives=GREATEST(0,lives-1),streak=0 WHERE room_id=%s AND user_id=%s",
                    (rid, user),
                )
        await g.event(cur, rid, user, "answered", {"position": body.position})
        r = await g.advance(cur, await g.room(cur, rid), now)
        return await g.view(cur, r, user, now)


@router.post("/rooms/{rid}/leave")
async def leave(
    rid: str, body: Empty, request: Request, user: Account, response: Response
):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        r = await g.room(cur, rid)
        await cur.execute(
            "SELECT * FROM game_members WHERE room_id=%s AND user_id=%s", (rid, user)
        )
        m = await cur.fetchone()
        if not m:
            raise HTTPException(404, "Game not found")
        now = await g.clock(cur)
        if not m["left_at"] and r["state"] in ("waiting", "running"):
            await cur.execute(
                "UPDATE game_members SET left_at=%s,released_at=%s WHERE room_id=%s AND user_id=%s",
                (now, now, rid, user),
            )
            await cur.execute(
                "UPDATE game_rooms SET version=version+1 WHERE id=%s", (rid,)
            )
            await g.event(cur, rid, user, "left")
            if r["state"] == "waiting":
                if r["owner_id"] == user:
                    await g.release(cur, r, "cancelled", now)
                else:
                    await cur.execute(
                        "UPDATE game_members SET released_at=%s WHERE room_id=%s AND user_id=%s",
                        (now, rid, user),
                    )
            else:
                # A forfeit frees the active reservation immediately; its
                # later finalization never acquires a reward lock for this user.
                await g.advance(cur, r, now)
        return {"left": True}


@router.get("/cup/board")
async def cup_board(
    user: User,
    response: Response,
    cup_id: str = Query(max_length=20),
    offset: int = Query(0, ge=0, le=10000),
):
    private(response)
    async with cursor() as cur:
        await cur.execute(
            """WITH ranked AS(SELECT m.user_id,u.handle,u.avatar,m.score,m.correct,m.excluded,m.public_result,
          dense_rank() OVER(ORDER BY m.score DESC,m.elapsed_ms)::int AS rank FROM game_cup_entries e JOIN game_rooms r ON r.id=e.room_id AND r.state='finished'
          JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id AND m.left_at IS NULL JOIN users u ON u.id=m.user_id WHERE e.cup_id=%s)
          SELECT handle,avatar,score,correct,excluded,rank,public_result,user_id=%s AS is_you FROM ranked p WHERE (p.public_result OR p.user_id=%s)
           AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.user_id) OR (b.user_id=p.user_id AND b.blocked_id=%s)) ORDER BY rank,handle LIMIT 21 OFFSET %s""",
            (cup_id, user, user, user, user, offset),
        )
        rows = await cur.fetchall()
        return {"items": rows[:20], "has_more": len(rows) > 20}


@router.post("/cup/visibility")
async def cup_visibility(
    body: CupVisibility, request: Request, user: Account, response: Response
):
    private(response)
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "UPDATE game_members SET public_result=%s WHERE user_id=%s AND room_id=(SELECT room_id FROM game_cup_entries WHERE cup_id=%s AND user_id=%s) RETURNING room_id",
            (body.enabled, user, body.cup_id, user),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Cup entry not found")
        await g.event(
            cur, row["room_id"], user, "cup_visibility", {"public": body.enabled}
        )
    return {"public_result": body.enabled}


@router.get("/leaderboard")
async def competitive_leaderboard(
    user: User,
    response: Response,
    track: Literal["league", "cup", "gk_gs", "everyday_math", "english"] = "league",
    period: Literal["week", "month", "all"] = "week",
    cohort: Literal["all", "arts-comfort", "science-bridge", "balanced-core", "commerce-core"] = "all",
    offset: int = Query(0, ge=0, le=10000),
):
    from ..services.learning_rewards import level_bounds, league_division
    private(response)
    async with cursor() as cur:
        if track == "league":
            await cur.execute(
                """WITH bounds AS (
                    SELECT CASE WHEN %s='all' THEN NULL
                           ELSE date_trunc(%s, now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata'
                           END AS start_at
                ),
                totals AS (
                    SELECT l.user_id, u.handle, u.avatar,
                           COALESCE(p.stream_cohort, 'balanced-core') AS stream_cohort,
                           COALESCE(p.current_streak_days, 0) AS streak,
                           COALESCE(p.board_public, false) AS board_public,
                           sum(l.xp)::int AS xp,
                           (SELECT COALESCE(sum(x.xp),0)::int FROM reward_ledger x WHERE x.user_id=l.user_id) AS lifetime_xp
                    FROM reward_ledger l
                    JOIN users u ON u.id=l.user_id
                    LEFT JOIN reward_profiles p ON p.user_id=l.user_id
                    CROSS JOIN bounds b
                    WHERE (b.start_at IS NULL OR l.created_at>=b.start_at)
                      AND (COALESCE(p.board_public, false) OR l.user_id=%s)
                      AND (%s='all' OR COALESCE(p.stream_cohort, 'balanced-core')=%s)
                      AND NOT EXISTS (
                          SELECT 1 FROM creator_blocks cb
                          WHERE (cb.user_id=%s AND cb.blocked_id=l.user_id)
                             OR (cb.user_id=l.user_id AND cb.blocked_id=%s)
                      )
                    GROUP BY l.user_id, u.handle, u.avatar, p.stream_cohort, p.current_streak_days, p.board_public
                    HAVING sum(l.xp)>0
                ),
                ranked AS (
                    SELECT *, dense_rank() OVER (ORDER BY xp DESC)::int AS rank
                    FROM totals
                )
                SELECT user_id, handle, avatar, stream_cohort, streak, xp AS score, lifetime_xp, rank, (user_id=%s) AS is_you
                FROM ranked
                ORDER BY rank, handle
                LIMIT 21 OFFSET %s""",
                (
                    period,
                    "week" if period == "week" else "month",
                    user,
                    cohort,
                    cohort,
                    user,
                    user,
                    user,
                    offset,
                ),
            )
            raw_rows = await cur.fetchall()
            items = []
            for r in raw_rows[:20]:
                lvl = level_bounds(r["lifetime_xp"])
                div = league_division(r["score"])
                items.append({
                    "handle": r["handle"],
                    "avatar": r["avatar"],
                    "rank": r["rank"],
                    "score": r["score"],
                    "level": lvl["level"],
                    "title": lvl["title"],
                    "league_division": div["name"],
                    "stream_cohort": r["stream_cohort"],
                    "streak": r["streak"],
                    "is_you": r["is_you"],
                })
            return {"track": track, "period": period, "cohort": cohort, "items": items, "has_more": len(raw_rows) > 20}

        if track == "cup":
            now = await g.clock(cur)
            cid, _, _ = g.cup_window(now)
            await cur.execute(
                """WITH ranked AS (
                    SELECT m.user_id, u.handle, u.avatar, m.score, m.correct, m.elapsed_ms,
                           m.pace_bonus, m.best_streak, m.public_result,
                           COALESCE(p.stream_cohort, 'balanced-core') AS stream_cohort,
                           COALESCE(p.current_streak_days, 0) AS streak,
                           (SELECT COALESCE(sum(x.xp),0)::int FROM reward_ledger x WHERE x.user_id=m.user_id) AS lifetime_xp,
                           dense_rank() OVER (ORDER BY m.score DESC, m.elapsed_ms ASC)::int AS rank
                    FROM game_cup_entries e
                    JOIN game_rooms r ON r.id=e.room_id AND r.state='finished'
                    JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id AND m.left_at IS NULL
                    JOIN users u ON u.id=m.user_id
                    LEFT JOIN reward_profiles p ON p.user_id=m.user_id
                    WHERE e.cup_id=%s
                      AND (m.public_result OR COALESCE(p.board_public, false) OR m.user_id=%s)
                      AND (%s='all' OR COALESCE(p.stream_cohort, 'balanced-core')=%s)
                      AND NOT EXISTS (
                          SELECT 1 FROM creator_blocks cb
                          WHERE (cb.user_id=%s AND cb.blocked_id=m.user_id)
                             OR (cb.user_id=m.user_id AND cb.blocked_id=%s)
                      )
                )
                SELECT user_id, handle, avatar, score, correct, elapsed_ms, pace_bonus, best_streak, stream_cohort, streak, lifetime_xp, rank, (user_id=%s) AS is_you
                FROM ranked
                ORDER BY rank, handle
                LIMIT 21 OFFSET %s""",
                (cid, user, cohort, cohort, user, user, user, offset),
            )
            raw_rows = await cur.fetchall()
            items = []
            for r in raw_rows[:20]:
                lvl = level_bounds(r["lifetime_xp"])
                items.append({
                    "handle": r["handle"],
                    "avatar": r["avatar"],
                    "rank": r["rank"],
                    "score": r["score"],
                    "correct": r["correct"],
                    "elapsed_ms": r["elapsed_ms"],
                    "pace_bonus": r["pace_bonus"],
                    "best_streak": r["best_streak"],
                    "level": lvl["level"],
                    "title": lvl["title"],
                    "stream_cohort": r["stream_cohort"],
                    "streak": r["streak"],
                    "is_you": r["is_you"],
                })
            return {"track": track, "period": period, "cohort": cohort, "cup_id": cid, "items": items, "has_more": len(raw_rows) > 20}

        # Pillar High-Score Boards: gk_gs, everyday_math, english
        preset_map = {
            "gk_gs": ("gk-foundation", "arts-comfort", "science-bridge", "balanced-core"),
            "everyday_math": ("math-foundation", "balanced-core", "commerce-core"),
            "english": ("english-foundation", "arts-comfort", "balanced-core"),
        }
        allowed_presets = list(preset_map[track])
        await cur.execute(
            """WITH best_runs AS (
                SELECT m.user_id, u.handle, u.avatar,
                       max(m.score)::int AS score,
                       max(m.correct)::int AS correct,
                       min(m.elapsed_ms)::int AS elapsed_ms,
                       max(m.pace_bonus)::int AS pace_bonus,
                       max(m.best_streak)::int AS best_streak,
                       COALESCE(p.stream_cohort, 'balanced-core') AS stream_cohort,
                       COALESCE(p.current_streak_days, 0) AS streak,
                       (SELECT COALESCE(sum(x.xp),0)::int FROM reward_ledger x WHERE x.user_id=m.user_id) AS lifetime_xp
                FROM game_members m
                JOIN game_rooms r ON r.id=m.room_id AND r.state='finished'
                JOIN users u ON u.id=m.user_id
                LEFT JOIN reward_profiles p ON p.user_id=m.user_id
                WHERE m.left_at IS NULL AND m.score > 0
                  AND (COALESCE(p.board_public, false) OR m.public_result OR m.user_id=%s)
                  AND (%s='all' OR COALESCE(p.stream_cohort, 'balanced-core')=%s)
                  AND (
                      (r.selection_context->'selector'->>'preset_id') = ANY(%s)
                      OR r.selection_context IS NOT NULL
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM creator_blocks cb
                      WHERE (cb.user_id=%s AND cb.blocked_id=m.user_id)
                         OR (cb.user_id=m.user_id AND cb.blocked_id=%s)
                  )
                GROUP BY m.user_id, u.handle, u.avatar, p.stream_cohort, p.current_streak_days
            ),
            ranked AS (
                SELECT *, dense_rank() OVER (ORDER BY score DESC, elapsed_ms ASC)::int AS rank
                FROM best_runs
            )
            SELECT user_id, handle, avatar, score, correct, elapsed_ms, pace_bonus, best_streak, stream_cohort, streak, lifetime_xp, rank, (user_id=%s) AS is_you
            FROM ranked
            ORDER BY rank, handle
            LIMIT 21 OFFSET %s""",
            (user, cohort, cohort, allowed_presets, user, user, user, offset),
        )
        raw_rows = await cur.fetchall()
        items = []
        for r in raw_rows[:20]:
            lvl = level_bounds(r["lifetime_xp"])
            items.append({
                "handle": r["handle"],
                "avatar": r["avatar"],
                "rank": r["rank"],
                "score": r["score"],
                "correct": r["correct"],
                "elapsed_ms": r["elapsed_ms"],
                "pace_bonus": r["pace_bonus"],
                "best_streak": r["best_streak"],
                "level": lvl["level"],
                "title": lvl["title"],
                "stream_cohort": r["stream_cohort"],
                "streak": r["streak"],
                "is_you": r["is_you"],
            })
        return {"track": track, "period": period, "cohort": cohort, "items": items, "has_more": len(raw_rows) > 20}

