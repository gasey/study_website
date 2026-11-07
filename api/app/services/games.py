"""Durable game controller. Clients submit choices, never scores or time."""

import asyncio, hashlib, json, logging, secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from ..db import cursor
from ..source_files import source_pdf_url, figure_image_url
from .learning_rewards import touch_daily_streak

MODES = {
    "trail": (10, 20, 1),
    "gauntlet": (20, 25, 1),
    "speed": (10, 15, 1),
    "duel": (10, 20, 2),
    "party": (10, 25, 4),
    "cup": (25, 30, 1),
}
PUBLIC_FIELDS = (
    "id",
    "question",
    "options",
    "direction",
    "passage",
    "question_markup",
    "options_markup",
    "figure_image_url",
    "source_pdf_url",
    "exam_name",
    "year",
    "qnum",
    "page",
    "paper_id",
    "answer_source",
    "pillar",
    "pillar_label",
    "round_seconds",
    "courage_eligible",
)
IDENTITY = (
    "question",
    "options",
    "answer_text",
    "answer_source",
    "direction",
    "passage",
    "question_markup",
    "options_markup",
    "has_diagram",
    "figure_image",
    "appearance_id",
)
log = logging.getLogger(__name__)


def digest(data):
    return hashlib.sha256(
        json.dumps(
            data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


async def clock(cur):
    await cur.execute("SELECT clock_timestamp() AS now")
    return (await cur.fetchone())["now"]


async def event(cur, rid, actor, action, detail=None):
    await cur.execute(
        "INSERT INTO game_events(room_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)",
        (rid, actor, action, Jsonb(detail or {})),
    )


async def permitted(cur, user):
    await cur.execute(
        "SELECT 1 FROM sanctions WHERE user_id=%s AND kind IN ('mute','suspension') AND lifted_at IS NULL AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())",
        (user,),
    )
    if await cur.fetchone():
        raise HTTPException(403, "Your account is currently restricted from games")
    await cur.execute(
        "SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL", (user,)
    )
    if await cur.fetchone():
        raise HTTPException(409, "Finish your active mock before joining a game")


async def current_questions(cur, ids, context=None):
    if context:
        from .game_selection import candidates
        return {r["id"]:r for r in await candidates(cur,context,ids,True)}
    await cur.execute(
        """SELECT v.*,a.id AS appearance_id,COALESCE(a.direction,v.direction) AS direction,COALESCE(a.passage,v.passage) AS passage,
      COALESCE(a.question_markup,v.question_markup) AS question_markup,COALESCE(a.options_markup,v.options_markup) AS options_markup,
      COALESCE(a.has_diagram,false) AS has_diagram,a.figure_image,a.paper_id,a.qnum,a.page,p.exam_name,p.year,p.source_file,p.pdf_url
      FROM v_launch_scorable v LEFT JOIN LATERAL(SELECT x.* FROM appearances x WHERE x.canonical_id=v.id AND EXISTS(SELECT 1 FROM papers xp WHERE xp.id=x.paper_id AND xp.exam_scope_id='mizoram-recruitment') AND x.options=v.options AND x.question=v.question ORDER BY x.is_primary DESC,x.id LIMIT 1) a ON TRUE
      LEFT JOIN papers p ON p.id=a.paper_id WHERE v.id=ANY(%s)""",
        (ids,),
    )
    rows = await cur.fetchall()
    for r in rows:
        r["source_pdf_url"] = source_pdf_url(r.get("source_file"), r.get("pdf_url"))
        r["figure_image_url"] = figure_image_url(r.get("figure_image"))
    return {r["id"]: r for r in rows}


async def draw(cur, count, subject=None):
    from . import game_selection as setup
    mode='cup'if count==25 else'gauntlet'if count==20 else'speed'
    selection=setup.Selection(kind='area',area_id='subject:'+subject)if subject else setup.Selection(kind='mixed')
    context=await setup.resolve(cur,selection,mode);context['rules']['questions']=count
    return await setup.draw(cur,context)


def cup_window(now):
    local = now.astimezone(ZoneInfo("Asia/Kolkata"))
    day = local.date() + timedelta(days=(6 - local.weekday()) % 7)
    opens = datetime.combine(
        day, datetime.min.time(), ZoneInfo("Asia/Kolkata")
    ) + timedelta(hours=19)
    if local >= opens + timedelta(hours=1):
        opens += timedelta(days=7)
    return opens.date().isoformat(), opens, opens + timedelta(hours=1)


async def cup(cur, now):
    cid, opens, closes = cup_window(now)
    await cur.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))", ("game-cup:" + cid,)
    )
    await cur.execute("SELECT * FROM game_cups WHERE id=%s", (cid,))
    row = await cur.fetchone()
    if row:
        return row
    questions = await draw(cur, 25)
    await cur.execute(
        "INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,%s) RETURNING *",
        (cid, opens, closes, Jsonb(questions)),
    )
    return await cur.fetchone()


async def room(cur, rid, lock=True):
    await cur.execute(
        "SELECT * FROM game_rooms WHERE id=%s" + (" FOR UPDATE" if lock else ""), (rid,)
    )
    r = await cur.fetchone()
    if not r:
        raise HTTPException(404, "Game not found")
    return r


async def member(cur, r, user):
    await cur.execute(
        "SELECT * FROM game_members WHERE room_id=%s AND user_id=%s", (r["id"], user)
    )
    m = await cur.fetchone()
    if not m:
        raise HTTPException(404, "Game not found")
    await cur.execute(
        "SELECT 1 FROM game_members m JOIN creator_blocks b ON (b.user_id=%s AND b.blocked_id=m.user_id) OR (b.blocked_id=%s AND b.user_id=m.user_id) WHERE m.room_id=%s AND m.left_at IS NULL",
        (user, user, r["id"]),
    )
    if await cur.fetchone():
        raise HTTPException(
            403,
            "Game unavailable due to a blocked participant; leave from Games to release your seat",
        )
    return m


def question_round_seconds(r, pos=0):
    if r["mode"] == "speed":
        return r["round_seconds"]
    qs = r.get("questions") or []
    if 0 <= pos < len(qs):
        q_secs = qs[pos].get("round_seconds")
        if isinstance(q_secs, int) and 5 <= q_secs <= 60:
            return q_secs
    return r["round_seconds"]


async def start(cur, r, now):
    if r["state"] != "waiting":
        raise HTTPException(409, "This game has already started")
    await cur.execute(
        "SELECT count(*) AS n FROM game_members WHERE room_id=%s AND left_at IS NULL",
        (r["id"],),
    )
    n = (await cur.fetchone())["n"]
    if n < (2 if r["mode"] in ("duel", "party") else 1):
        raise HTTPException(409, "Wait for another player before starting")
    if r.get("selection_context") and r["mode"] in ("duel","party"):
        await cur.execute("SELECT 1 FROM game_members WHERE room_id=%s AND left_at IS NULL AND NOT ready",(r['id'],))
        if await cur.fetchone():raise HTTPException(409,"Every player must confirm this area and mark Ready first")
        await cur.execute("SELECT user_id FROM game_members WHERE room_id=%s AND left_at IS NULL ORDER BY user_id",(r['id'],))
        for player in await cur.fetchall():await permitted(cur,player['user_id'])
        await cur.execute("SELECT 1 FROM creator_blocks b JOIN game_members a ON a.user_id=b.user_id AND a.room_id=%s AND a.left_at IS NULL JOIN game_members z ON z.user_id=b.blocked_id AND z.room_id=a.room_id AND z.left_at IS NULL",(r['id'],))
        if await cur.fetchone():raise HTTPException(409,"This room contains a blocked participant. Leave and choose another room.")
    first_secs = question_round_seconds(r, 0)
    duration = (
        1800
        if r["mode"] == "trail"
        else 60
        if r["mode"] == "speed"
        else sum(question_round_seconds(r, i) for i in range(len(r["questions"])))
    )
    await cur.execute(
        "UPDATE game_rooms SET state='running',round_started_at=%s,round_ends_at=%s,deadline=%s,version=version+1 WHERE id=%s",
        (
            now,
            now + timedelta(seconds=first_secs),
            now + timedelta(seconds=duration),
            r["id"],
        ),
    )
    if r["mode"]=="trail":await cur.execute("UPDATE game_rooms SET round_ends_at=deadline WHERE id=%s",(r["id"],))
    await event(cur, r["id"], r["owner_id"], "started")
    return await room(cur, r["id"])


async def release(cur, r, state, now):
    await cur.execute(
        "UPDATE game_rooms SET state=%s,finished_at=%s,version=version+1 WHERE id=%s",
        (state, now, r["id"]),
    )
    await cur.execute(
        "UPDATE game_members SET released_at=COALESCE(released_at,%s) WHERE room_id=%s",
        (now, r["id"]),
    )
    await event(cur, r["id"], None, state)


async def finish(cur, r, now):
    if r["state"] not in ("running", "waiting"):
        return
    await cur.execute(
        "SELECT id FROM canonical_questions WHERE id=ANY(%s) ORDER BY id FOR SHARE",
        ([q["id"] for q in r["questions"]],),
    )
    current = await current_questions(cur, [q["id"] for q in r["questions"]], r.get("selection_context"))
    await cur.execute(
        "SELECT * FROM game_members WHERE room_id=%s ORDER BY user_id", (r["id"],)
    )
    players = await cur.fetchall()
    is_foundation_comp = (
        (r.get("selection_context") or {}).get("rules", {}).get("scoring")
        == "foundation-competitive-v1"
    )
    for p in players:
        await cur.execute(
            "SELECT * FROM game_answers WHERE room_id=%s AND user_id=%s ORDER BY position",
            (r["id"], p["user_id"]),
        )
        answers = await cur.fetchall()
        right = wrong = skipped = excluded = score = elapsed = distance = streak = 0
        pace_total = streak_total = courage_total = best_streak = 0
        for a in answers:
            q = r["questions"][a["position"]]
            live = current.get(q["id"])
            valid = live and all(live.get(k) == q.get(k) for k in IDENTITY)
            if not valid:
                excluded += 1
                await cur.execute(
                    "UPDATE game_answers SET excluded=true WHERE room_id=%s AND user_id=%s AND position=%s",
                    (r["id"], p["user_id"], a["position"]),
                )
                continue
            chosen = (
                q["options"][a["chosen_index"]]
                if a["chosen_index"] is not None
                else None
            )
            if chosen is None:
                skipped += 1
                streak = 0
            elif a["correct"]:
                right += 1
                streak += 1
                if streak > best_streak:
                    best_streak = streak
                distance += 100 * min(streak, 5)
                if r["mode"] == "trail":
                    score += 200 if a["position"] == r.get("trail_boost_position") else 100
                else:
                    q_secs = question_round_seconds(r, a["position"])
                    pace_pts = max(
                        0,
                        50 - int(a["elapsed_ms"] / max(1, q_secs * 1000) * 50),
                    )
                    streak_pts = 0
                    courage_pts = 0
                    if is_foundation_comp:
                        streak_pts = (
                            15
                            if streak == 2
                            else 30
                            if streak == 3
                            else 40
                            if streak == 4
                            else 50
                            if streak >= 5
                            else 0
                        )
                        courage_pts = 25 if q.get("courage_eligible") else 0
                    pace_total += pace_pts
                    streak_total += streak_pts
                    courage_total += courage_pts
                    score += 100 + pace_pts + streak_pts + courage_pts
                elapsed += a["elapsed_ms"]
            else:
                wrong += 1
                streak = 0
                elapsed += a["elapsed_ms"]
            if chosen is not None:
                await cur.execute(
                    "INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES(%s,%s,%s,%s,'game',%s) RETURNING id",
                    (p["user_id"], q["id"], a["correct"], chosen, Jsonb(q)),
                )
                aid = (await cur.fetchone())["id"]
                await cur.execute(
                    "UPDATE game_answers SET attempt_id=%s WHERE room_id=%s AND user_id=%s AND position=%s",
                    (aid, r["id"], p["user_id"], a["position"]),
                )
                if a["correct"] and not p["left_at"]:
                    await cur.execute("SELECT reward_study_attempt(%s)", (aid,))
        if not p["left_at"] and (right + wrong) > 0:
            await touch_daily_streak(cur, p["user_id"])
        await cur.execute(
            "UPDATE game_members SET correct=%s,wrong=%s,skipped=%s,excluded=%s,score=%s,elapsed_ms=%s,distance=%s,pace_bonus=%s,streak_bonus=%s,courage_bonus=%s,best_streak=%s WHERE room_id=%s AND user_id=%s",
            (
                right,
                wrong,
                skipped,
                excluded,
                distance if r["mode"] == "gauntlet" else score,
                elapsed,
                distance,
                pace_total,
                streak_total,
                courage_total,
                best_streak,
                r["id"],
                p["user_id"],
            ),
        )
    await release(cur, r, "finished", now)


async def advance(cur, r, now):
    if r["state"] == "waiting":
        if now >= r["created_at"] + timedelta(minutes=10):
            await release(cur, r, "cancelled", now)
            return await room(cur, r["id"])
        return r
    if r["state"] != "running":
        return r
    if r["mode"]=="trail":
        from .topic_trail import advance as trail_advance
        return await trail_advance(cur,r,now)
    for _ in range(26):
        await cur.execute(
            "SELECT user_id,lives FROM game_members WHERE room_id=%s AND left_at IS NULL",
            (r["id"],),
        )
        active = await cur.fetchall()
        if (
            not active
            or now >= r["deadline"]
            or r["current_position"] >= len(r["questions"])
            or r["mode"] == "gauntlet"
            and all(p["lives"] <= 0 for p in active)
        ):
            await finish(cur, r, now)
            return await room(cur, r["id"])
        await cur.execute(
            "SELECT count(*) AS n FROM game_answers WHERE room_id=%s AND position=%s AND user_id=ANY(%s)",
            (r["id"], r["current_position"], [p["user_id"] for p in active]),
        )
        answered = (await cur.fetchone())["n"]
        if now < r["round_ends_at"] and answered < len(active):
            return r
        cur_secs = question_round_seconds(r, r["current_position"])
        for p in active:
            await cur.execute(
                "INSERT INTO game_answers(room_id,user_id,position,correct,elapsed_ms) VALUES(%s,%s,%s,false,%s) ON CONFLICT DO NOTHING RETURNING user_id",
                (
                    r["id"],
                    p["user_id"],
                    r["current_position"],
                    cur_secs * 1000,
                ),
            )
            timedout = await cur.fetchone()
            if timedout and r["mode"] == "gauntlet":
                await cur.execute(
                    "UPDATE game_members SET lives=GREATEST(0,lives-1),streak=0 WHERE room_id=%s AND user_id=%s",
                    (r["id"], p["user_id"]),
                )
        next_start = r["round_ends_at"] if now >= r["round_ends_at"] else now
        next_pos = r["current_position"] + 1
        next_secs = question_round_seconds(r, next_pos)
        await cur.execute(
            "UPDATE game_rooms SET current_position=current_position+1,round_started_at=%s,round_ends_at=%s,version=version+1 WHERE id=%s",
            (
                next_start,
                min(next_start + timedelta(seconds=next_secs), r["deadline"]),
                r["id"],
            ),
        )
        r = await room(cur, r["id"])
    return r


async def view(cur, r, user, now):
    m = await member(cur, r, user)
    await cur.execute(
        "SELECT m.user_id,m.score,m.correct,m.wrong,m.skipped,m.excluded,m.lives,m.distance,m.left_at,m.ready,m.elapsed_ms,m.pace_bonus,m.streak_bonus,m.courage_bonus,m.best_streak,u.handle,u.avatar FROM game_members m JOIN users u ON u.id=m.user_id WHERE m.room_id=%s ORDER BY m.joined_at,m.user_id",
        (r["id"],),
    )
    players = await cur.fetchall()
    q = None
    mine = None
    review = []
    review_at = None
    if r["state"] == "running" and not m["left_at"]:
        raw = r["questions"][r["current_position"]]
        q = {k: raw.get(k) for k in PUBLIC_FIELDS}
        await cur.execute(
            "SELECT chosen_index FROM game_answers WHERE room_id=%s AND user_id=%s AND position=%s",
            (r["id"], user, r["current_position"]),
        )
        mine = await cur.fetchone()
    if r["cup_id"]:
        await cur.execute("SELECT closes_at FROM game_cups WHERE id=%s", (r["cup_id"],))
        review_at = (await cur.fetchone())["closes_at"]
    if r["state"] == "finished" and (not review_at or now >= review_at):
        await cur.execute(
            "SELECT position,chosen_index,correct,excluded FROM game_answers WHERE room_id=%s AND user_id=%s ORDER BY position",
            (r["id"], user),
        )
        answers = await cur.fetchall()
        for a in answers:
            raw = r["questions"][a["position"]]
            review.append(
                {
                    **{k: raw.get(k) for k in PUBLIC_FIELDS},
                    **a,
                    "answer_index": raw["options"].index(raw["answer_text"]),
                    "explanation": raw.get("explanation"),
                }
            )
    if r["state"] != "finished":
        for p in players:
            for key in (
                "score",
                "correct",
                "wrong",
                "skipped",
                "excluded",
                "elapsed_ms",
                "pace_bonus",
                "streak_bonus",
                "courage_bonus",
                "best_streak",
            ):
                p.pop(key, None)
        if r["mode"] != "gauntlet":
            for p in players:
                p.pop("distance", None)
                p.pop("lives", None)
    result = {
        "id": r["id"],
        "owner_id": r["owner_id"],
        "mode": r["mode"],
        "state": r["state"],
        "subject_id": r["subject_id"],
        "selection": {k:r['selection_context'][k]for k in ['label','source_label','rules','excluded_labels']}if r.get('selection_context')else None,
        "context_hash": r.get('context_hash'),
        "round_seconds": question_round_seconds(r, r["current_position"]) if r["state"] == "running" else r['round_seconds'],
        "capacity": r["capacity"],
        "join_code": r["join_code"] if r["state"] == "waiting" else None,
        "cup_id": r["cup_id"],
        "version": r["version"],
        "position": r["current_position"],
        "total": len(r["questions"]),
        "server_now": now,
        "round_ends_at": r["round_ends_at"],
        "deadline": r["deadline"],
        "viewer_id": user,
        "players": players,
        "question": q,
        "answered": mine is not None,
        "chosen_index": mine["chosen_index"] if mine else None,
        "review": review,
        "review_available_at": review_at,
    }

    if r["mode"]=="trail":
        from .topic_trail import decorate
        result=await decorate(cur,r,user,result)
    return result


async def worker():
    while True:
        try:
            async with cursor() as cur:
                now = await clock(cur)
                await cur.execute(
                    "SELECT id FROM game_rooms WHERE (state='running' AND (round_ends_at<=%s OR deadline<=%s)) OR (state='waiting' AND created_at<%s-interval '10 minutes') ORDER BY created_at LIMIT 20 FOR UPDATE SKIP LOCKED",
                    (now, now, now),
                )
                ids = [r["id"] for r in await cur.fetchall()]
                for rid in ids:
                    await advance(cur, await room(cur, rid), now)
        except Exception:
            log.exception("Game clock sweep deferred")
        await asyncio.sleep(2)
