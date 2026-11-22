"""Private account planning and explicitly shared six-seat study desks."""

from typing import Annotated, Literal
from uuid import uuid4
import hashlib, json
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..config import settings
from ..services.review_identity import Actor, identity, require_role
from ..services.bank_review import protect_answer
from ..services import desk_notes,audience,community_audience
from .materials import write_guard as content_write_guard

router = APIRouter(prefix="/api/desk", tags=["study desk"])
User = Annotated[str, Depends(current_user)]
Account = Annotated[str, Depends(require_account)]
Staff = Annotated[Actor, Depends(identity)]


@router.get('/rooms/{did}/calendar')
async def room_calendar(did: str, start: date, end: date, user: Account, response: Response):
    from ..services import desk_calendar
    if end<start or (end-start).days>93:
        raise HTTPException(422,'Choose at most 93 days for the room calendar')
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        return await desk_calendar.view(cur,did,user,start,end)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Task(Strict):
    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=140)
    done: bool = False
    week: bool = False


class Note(Strict):
    question_id: str | None = Field(default=None, min_length=1, max_length=100)
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=140)
    body: str = Field(default="", max_length=4000)
    subject: str = Field(default="", max_length=100)


class Document(Strict):
    goal: str = Field(default="", max_length=140)
    goalSubject: str = Field(default="", max_length=100)
    tasks: list[Task] = Field(default_factory=list, max_length=200)
    notes: list[Note] = Field(default_factory=list, max_length=100)
    saved: list[str] = Field(default_factory=list, max_length=500)
    recent: list[str] = Field(default_factory=list, max_length=8)
    completedDays: list[date] = Field(default_factory=list, max_length=730)
    weeklyTarget: int = Field(default=100, ge=1, le=10000)

    @model_validator(mode="after")
    def unique_ids(self):
        for rows in [self.tasks, self.notes]:
            ids = [r.id for r in rows]
            if len(set(ids)) != len(ids):
                raise ValueError("Item IDs must be unique")
        if any(len(x) > 100 for x in self.saved + self.recent):
            raise ValueError("Question ID too long")
        return self


class Save(Strict):
    user_id: str = Field(min_length=1, max_length=100)
    expected_version: int = Field(ge=0)
    data: Document


class Version(Strict):
    expected_version: int = Field(ge=1)


class Room(Strict):
    name: str = Field(min_length=3, max_length=100)
    goal: str = Field(default="", max_length=500)


class UpdateRoom(Room, Version):
    pass


class WeeklyGoal(Strict):
    week_start: date
    expected_version: int = Field(ge=0)
    target: int = Field(ge=1, le=10000, strict=True)


class Invite(Strict):
    handle: str = Field(min_length=2, max_length=100)


class Decision(Strict):
    decision: Literal["accept", "decline", "cancel"]


class Sharing(Strict):
    progress: bool = False
    mistakes: bool = False
    times: bool = False
    muted: bool = False


class Item(Strict):
    kind: Literal["question", "note", "bookmark", "mistake", "update"]
    question_id: str | None = Field(default=None, max_length=100)
    title: str = Field(default="", max_length=140)
    body: str = Field(default="", max_length=4000)


class EditItem(Version):
    question_id: str | None = Field(default=None, min_length=1, max_length=100)
    title: str = Field(default="", max_length=140)
    body: str = Field(default="", max_length=4000)
    delete: bool = False


class DiscussionState(Version):
    state: Literal['needed', 'resolved']


class Message(Strict):
    note_id: str | None = Field(default=None, min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=2000)


class EditMessage(Message, Version):
    delete: bool = False


class Focus(Strict):
    minutes: int = Field(default=25, ge=5, le=120)
    desk_id: str | None = Field(default=None, max_length=100)


class FocusAction(Version):
    action: Literal["pause", "resume", "finish", "cancel"]


class Member(Strict):
    user_id: str = Field(min_length=1, max_length=100)


class Report(Strict):
    target_kind: Literal["desk", "item", "message", "invite"]
    target_id: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=10, max_length=2000)


class Resolve(Strict):
    reason: str = Field(min_length=10, max_length=2000)
    action: Literal["dismiss", "remove"] = "dismiss"


async def write_guard(request, user):
    if request.headers.get("x-desk-user", user) != user:
        raise HTTPException(409, "Your signed-in account changed; reload before saving")
    await content_write_guard(request, user)


async def private(response: Response):
    response.headers["Cache-Control"] = "private, no-store"


async def event(cur, user, action, did=None, detail=None):
    await cur.execute(
        "INSERT INTO study_desk_events(desk_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)",
        (did, user, action, Jsonb(detail or {})),
    )


def enabled():
    if not settings.study_desks_private_enabled:
        raise HTTPException(
            409,
            "Private desk invitations are not open yet. Your personal desk is available.",
        )


async def member(cur, did, user, owner=False, lock=False, include_restricted_owner=False):
    await cur.execute(
        "SELECT d.*,m.joined_at,m.sharing,m.muted FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL WHERE d.id=%s AND d.closed_at IS NULL"
        + ' AND '+('TRUE' if include_restricted_owner else audience.subject_sql('d.owner_id'))+' AND '+audience.subject_sql('m.user_id')
        + (" FOR UPDATE OF d" if lock else ""),
        (user, did),
    )
    r = await cur.fetchone()
    if not r:
        raise HTTPException(404, "Study desk not found or membership has ended")
    if owner and r["owner_id"] != user:
        raise HTTPException(403, "Only the desk owner can do this")
    return r


async def unrestricted(cur, user):
    await cur.execute(
        "SELECT 1 FROM sanctions WHERE user_id=%s AND kind IN ('mute','suspension') AND lifted_at IS NULL AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())",
        (user,),
    )
    if await cur.fetchone():
        raise HTTPException(
            403, "Your account is currently restricted from shared desk changes"
        )


async def blocked(cur, a, b):
    await cur.execute(
        "SELECT 1 FROM creator_blocks WHERE (user_id=%s AND blocked_id=%s) OR (user_id=%s AND blocked_id=%s)",
        (a, b, b, a),
    )
    return bool(await cur.fetchone())


async def notify(cur, user, key, text, did, invite=None):
    if invite is None:
        await cur.execute(
            "SELECT muted FROM study_desk_members WHERE desk_id=%s AND user_id=%s AND left_at IS NULL",
            (did, user),
        )
        prefs = await cur.fetchone()
        if prefs and prefs["muted"]:
            return
    await community_audience.notify(cur,user,
        "INSERT INTO review_notifications(user_id,event_key,message,study_desk_id,study_invite_id) VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        (user, key, text, did, invite),
    )


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@router.get("/personal", dependencies=[Depends(private)])
async def personal(user: User):
    async with cursor() as cur:
        await cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        await cur.execute(
            "SELECT avatar,handle,email IS NOT NULL AS registered FROM users WHERE id=%s",
            (user,),
        )
        who = await cur.fetchone()
        await cur.execute(
            "SELECT document,version FROM personal_desks WHERE user_id=%s", (user,)
        )
        row = await cur.fetchone()
        data = Document.model_validate(row["document"] if row else {}).model_dump(mode="json")
        visible = await desk_notes.document(cur,user,data)
    return {
        "user_id": user,
        **who,
        "data": visible,
        "hidden_notes": len(data['notes'])-len(visible['notes']),
        "version": row["version"] if row else 0,
        "private_desks_enabled": settings.study_desks_private_enabled,
    }


@router.post("/personal")
async def save_personal(body: Save, request: Request, user: Account):
    await write_guard(request, user)
    if body.user_id != user:
        raise HTTPException(409, "Your signed-in account changed; reload before saving")
    async with cursor() as cur:
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("personal-desk:" + user,)
        )
        await cur.execute(
            "SELECT version,document FROM personal_desks WHERE user_id=%s FOR UPDATE", (user,)
        )
        old = await cur.fetchone()
        if (old["version"] if old else 0) != body.expected_version:
            raise HTTPException(
                409,
                "Your desk changed on another device. Reload the account version or explicitly keep your local edits.",
            )
        qids = set(body.data.saved + body.data.recent + [n.question_id for n in body.data.notes if n.question_id])
        if qids:
            await cur.execute(
                "SELECT id FROM canonical_questions WHERE id=ANY(%s)", (list(qids),)
            )
            valid = {r["id"] for r in await cur.fetchall()}
            if valid != qids:
                raise HTTPException(
                    422,
                    "A saved or recent question is no longer available. Remove its stale reference before saving.",
                )
        if body.data.goalSubject:
            await cur.execute(
                "SELECT 1 FROM review_taxonomy WHERE id=%s AND level='subject' AND active",
                (body.data.goalSubject,),
            )
            if not await cur.fetchone():
                raise HTTPException(422, "Choose a current subject")
        previous = Document.model_validate(old['document'] if old else {}).model_dump(mode='json')
        incoming = body.data.model_dump(mode='json')
        doc = await desk_notes.preserve_locked(cur,user,previous,incoming)
        old_notes = {n['id']:n for n in previous['notes']}
        for n in incoming['notes']:
            if n.get('question_id') and n != old_notes.get(n['id']):
                await protect_answer(cur,user,n['question_id'])
        await cur.execute(
            "INSERT INTO personal_desks(user_id,document) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET document=EXCLUDED.document,version=personal_desks.version+1,updated_at=now() RETURNING version",
            (user, Jsonb(doc)),
        )
        version = (await cur.fetchone())["version"]
        visible = await desk_notes.document(cur,user,doc)
    return {"data": visible, "version": version}


@router.get("/overview", dependencies=[Depends(private)])
async def overview(user: User):
    async with cursor() as cur:
        await cur.execute(
            "SELECT count(*)::int AS answered,count(*) FILTER(WHERE correct)::int AS correct,count(DISTINCT canonical_id)::int AS unique_questions,count(*) FILTER(WHERE at>=date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')::int AS week_answers FROM attempts WHERE user_id=%s",
            (user,),
        )
        stats = await cur.fetchone()
        await cur.execute(
            "SELECT document FROM personal_desks WHERE user_id=%s", (user,)
        )
        doc = await cur.fetchone()
        data = Document.model_validate(doc["document"] if doc else {})
        ids = list(dict.fromkeys(data.saved + data.recent))
        await cur.execute(
            "SELECT q.id,q.question,q.type,q.answer_source,c.subject_label AS subject FROM canonical_questions q LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved' WHERE q.id=ANY(%s)",
            (ids,),
        )
        questions = await cur.fetchall()
        await cur.execute(
            "SELECT c.subject_label AS subject,count(*)::int AS answered,count(*) FILTER(WHERE a.correct)::int AS correct FROM attempts a JOIN question_classifications c ON c.question_id=a.canonical_id AND c.review_status='approved' WHERE a.user_id=%s GROUP BY c.subject_label ORDER BY count(*) DESC LIMIT 12",
            (user,),
        )
        subjects = await cur.fetchall()
        await cur.execute(
            "SELECT a.canonical_id AS id,q.question,count(*)::int AS times_wrong FROM attempts a JOIN canonical_questions q ON q.id=a.canonical_id WHERE a.user_id=%s AND NOT a.correct GROUP BY a.canonical_id,q.question ORDER BY count(*) DESC,a.canonical_id LIMIT 20",
            (user,),
        )
        mistakes = await cur.fetchall()
        await cur.execute(
            "SELECT *,LEAST(duration_seconds,elapsed_seconds+CASE WHEN resumed_at IS NOT NULL THEN GREATEST(0,extract(epoch FROM now()-resumed_at))::int ELSE 0 END) AS elapsed FROM study_focus_sessions WHERE user_id=%s ORDER BY created_at DESC LIMIT 20",
            (user,),
        )
        sessions = await cur.fetchall()
    return {
        "stats": stats,
        "questions": questions,
        "subjects": subjects,
        "mistakes": mistakes,
        "sessions": sessions,
        "server_time": datetime.now(timezone.utc),
    }


@router.get("/questions", dependencies=[Depends(private)])
async def question_previews(
    user: User, ids: list[str] = Query(default=[], max_length=30)
):
    if any(len(x) > 100 for x in ids):
        raise HTTPException(422, "Question ID too long")
    async with cursor() as cur:
        await cur.execute(
            "SELECT q.id,q.question,q.type,q.answer_source,c.subject_label AS subject FROM canonical_questions q LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved' WHERE q.id=ANY(%s)",
            (ids,),
        )
        rows = await cur.fetchall()
    return {"items": rows}


@router.get("/rooms", dependencies=[Depends(private)])
async def rooms(user: Account):
    async with cursor() as cur:
        await cur.execute(
            "SELECT d.id,d.name,d.goal,d.owner_id,d.version,count(mm.user_id)::int AS members FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL LEFT JOIN study_desk_members mm ON mm.desk_id=d.id AND mm.left_at IS NULL AND "+audience.subject_sql('mm.user_id')+" WHERE d.closed_at IS NULL AND "+audience.subject_sql('d.owner_id')+" GROUP BY d.id ORDER BY d.created_at",
            (user,),
        )
        rows = await cur.fetchall()
        await cur.execute(
            "SELECT i.id,i.desk_id,i.sender_id,d.name,u.handle AS sender,i.expires_at FROM study_desk_invites i JOIN study_desks d ON d.id=i.desk_id AND d.closed_at IS NULL JOIN users u ON u.id=i.sender_id WHERE "+audience.subject_sql('i.sender_id')+" AND "+audience.subject_sql('d.owner_id')+" AND i.recipient_id=%s AND i.state='pending' AND i.expires_at>now() AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=i.sender_id) OR (b.user_id=i.sender_id AND b.blocked_id=%s)) ORDER BY i.created_at DESC LIMIT 30",
            (user, user, user),
        )
        invites = await cur.fetchall()
        await cur.execute("SELECT account_has_pro(%s) AS pro", (user,))
        pro = (await cur.fetchone())["pro"]
    return {
        "items": rows,
        "invitations": invites,
        "can_create": pro,
        "enabled": settings.study_desks_private_enabled,
    }


@router.post("/rooms", status_code=201)
async def create_room(
    body: Room,
    request: Request,
    user: Account,
    idempotency_key: Annotated[str, Header(min_length=16, max_length=100)],
):
    enabled()
    await write_guard(request, user)
    did = "desk_" + fingerprint([user, idempotency_key])[:28]
    async with cursor() as cur:
        await unrestricted(cur, user)
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("desk-create:" + user,)
        )
        await cur.execute("SELECT id,name,goal FROM study_desks WHERE id=%s", (did,))
        old = await cur.fetchone()
        if old:
            if old["name"] != body.name or old["goal"] != body.goal:
                raise HTTPException(
                    409, "This create key was used for a different desk"
                )
            return {"id": did}
        await cur.execute("SELECT account_has_pro(%s) AS pro", (user,))
        if not (await cur.fetchone())["pro"]:
            raise HTTPException(
                403,
                "Creating a shared desk requires Pro. Joining an invited desk is free.",
            )
        await cur.execute(
            "SELECT count(*) AS n FROM study_desks WHERE owner_id=%s AND closed_at IS NULL",
            (user,),
        )
        if (await cur.fetchone())["n"] >= 3:
            raise HTTPException(409, "You can own up to three private desks")
        await cur.execute(
            "INSERT INTO study_desks(id,owner_id,name,goal) VALUES(%s,%s,%s,%s)",
            (did, user, body.name, body.goal),
        )
        await cur.execute(
            "INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s)", (did, user)
        )
        await event(cur, user, "created", did)
    return {"id": did}


@router.post("/rooms/{did}/settings")
async def room_settings(did: str, body: UpdateRoom, request: Request, user: Account):
    enabled()
    await write_guard(request, user)
    async with cursor() as cur:
        await unrestricted(cur, user)
        r = await member(cur, did, user, owner=True, lock=True)
        if r["version"] != body.expected_version:
            raise HTTPException(409, "Desk settings changed; refresh first")
        await cur.execute(
            "UPDATE study_desks SET name=%s,goal=%s,version=version+1 WHERE id=%s",
            (body.name, body.goal, did),
        )
        await event(cur, user, "settings", did)
    return {"saved": True}


@router.post("/rooms/{did}/invite", status_code=201)
async def invite(did: str, body: Invite, request: Request, user: Account):
    enabled()
    await write_guard(request, user)
    async with cursor() as cur:
        await unrestricted(cur, user)
        await member(cur, did, user, owner=True, lock=True)
        await cur.execute(
            "SELECT u.id FROM users u WHERE u.handle=%s AND u.email IS NOT NULL AND "+audience.subject_sql('u.id'), (body.handle,)
        )
        target = await cur.fetchone()
        if not target or target["id"] == user:
            raise HTTPException(
                404,
                "This invitation cannot be sent. Check the exact registered handle.",
            )
        recipient = target["id"]
        if await blocked(cur, user, recipient):
            raise HTTPException(
                404,
                "This invitation cannot be sent. Check the exact registered handle.",
            )
        await cur.execute(
            "SELECT 1 FROM study_desk_members WHERE desk_id=%s AND user_id=%s AND left_at IS NULL",
            (did, recipient),
        )
        if await cur.fetchone():
            raise HTTPException(409, "That person is already a member")
        await cur.execute(
            "SELECT id FROM study_desk_invites WHERE desk_id=%s AND recipient_id=%s AND state='pending' AND expires_at>now()",
            (did, recipient),
        )
        old = await cur.fetchone()
        if old:
            return old
        await cur.execute(
            "SELECT 1 FROM study_desk_invites WHERE desk_id=%s AND recipient_id=%s AND state='declined' AND created_at>now()-interval '30 days'",
            (did, recipient),
        )
        if await cur.fetchone():
            raise HTTPException(
                409, "A declined invitation cannot be repeated for 30 days"
            )
        await cur.execute(
            "SELECT count(*) AS n FROM study_desk_invites WHERE sender_id=%s AND created_at>now()-interval '1 day'",
            (user,),
        )
        if (await cur.fetchone())["n"] >= 10:
            raise HTTPException(429, "Daily invitation limit reached")
        await cur.execute(
            "UPDATE study_desk_invites SET state='expired' WHERE desk_id=%s AND recipient_id=%s AND state='pending'",
            (did, recipient),
        )
        iid = "invite_" + uuid4().hex
        await cur.execute(
            "INSERT INTO study_desk_invites(id,desk_id,sender_id,recipient_id) VALUES(%s,%s,%s,%s)",
            (iid, did, user, recipient),
        )
        await notify(
            cur,
            recipient,
            "desk-invite:" + iid,
            "You received a private study desk invitation",
            did,
            iid,
        )
        await event(cur, user, "invited", did, {"invite_id": iid})
    return {"id": iid}


@router.post("/invites/{iid}")
async def decide_invite(iid: str, body: Decision, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute("SELECT * FROM study_desk_invites WHERE id=%s", (iid,))
        i = await cur.fetchone()
        if not i or user not in [i["recipient_id"], i["sender_id"]]:
            raise HTTPException(404, "Invitation not found")
        if body.decision == "cancel" and user != i["sender_id"]:
            raise HTTPException(403, "Only the sender may cancel")
        if body.decision != "cancel" and user != i["recipient_id"]:
            raise HTTPException(403, "Only the recipient may decide")
        await cur.execute(
            "SELECT d.* FROM study_desks d WHERE d.id=%s AND d.closed_at IS NULL AND "+(audience.subject_sql('d.owner_id') if body.decision=='accept' else 'TRUE')+" FOR UPDATE",
            (i["desk_id"],),
        )
        room = await cur.fetchone()
        if not room:
            raise HTTPException(409, "This desk is closed")
        await cur.execute(
            "SELECT * FROM study_desk_invites WHERE id=%s FOR UPDATE", (iid,)
        )
        i = await cur.fetchone()
        state = {"accept": "accepted", "decline": "declined", "cancel": "cancelled"}[
            body.decision
        ]
        if i["state"] == state:
            return {"state": state}
        if i["state"] != "pending" or i["expires_at"] <= datetime.now(timezone.utc):
            raise HTTPException(409, "Invitation expired or already decided")
        if body.decision == "accept":
            enabled()
            await unrestricted(cur, user)
            if room["owner_id"] != i["sender_id"]:
                raise HTTPException(
                    409, "The desk owner changed; ask for a new invitation"
                )
            if await blocked(cur, user, i["sender_id"]):
                raise HTTPException(409, "This invitation is no longer available")
            await cur.execute(
                "SELECT count(*) AS n FROM study_desk_members WHERE desk_id=%s AND left_at IS NULL",
                (i["desk_id"],),
            )
            if (await cur.fetchone())["n"] >= 6:
                raise HTTPException(409, "This desk has no free seats")
            await cur.execute(
                'INSERT INTO study_desk_members(desk_id,user_id) VALUES(%s,%s) ON CONFLICT(desk_id,user_id) DO UPDATE SET left_at=NULL,joined_at=now(),sharing=\'{"progress":false,"mistakes":false,"times":false}\',muted=false',
                (i["desk_id"], user),
            )
            await notify(
                cur,
                i["sender_id"],
                "desk-accepted:" + iid,
                "Your study desk invitation was accepted",
                i["desk_id"],
            )
        await cur.execute(
            "UPDATE study_desk_invites SET state=%s WHERE id=%s", (state, iid)
        )
        await event(cur, user, state, i["desk_id"], {"invite_id": iid})
    return {"state": state}


@router.get("/rooms/{did}", dependencies=[Depends(private)])
async def read_room(did: str, user: Account):
    async with cursor() as cur:
        r = await member(cur, did, user)
        await cur.execute(
            "SELECT m.user_id,u.handle,u.avatar,m.sharing,m.user_id=%s AS is_you FROM study_desk_members m JOIN users u ON u.id=m.user_id WHERE m.desk_id=%s AND m.left_at IS NULL AND "+audience.subject_sql('m.user_id')+" ORDER BY m.joined_at,m.user_id",
            (user, did),
        )
        members = await cur.fetchall()
        for m in members:
            m["blocked"] = (
                await blocked(cur, user, m["user_id"]) if not m["is_you"] else False
            )
            if m['blocked']:m['avatar']=None
            # Never serialize another member's private sharing preferences.
            prefs = m.pop("sharing")
            m["progress"] = None
            if (m["is_you"] or prefs.get("progress")) and not m["blocked"]:
                await cur.execute(
                    "SELECT count(*)::int AS answered,count(*) FILTER(WHERE correct)::int AS correct FROM attempts WHERE user_id=%s",
                    (m["user_id"],),
                )
                m["progress"] = await cur.fetchone()
            m["focusing"] = False
            if prefs.get("times") and not m["blocked"]:
                await cur.execute(
                    "SELECT 1 FROM study_focus_sessions WHERE user_id=%s AND desk_id=%s AND state='running' AND elapsed_seconds+extract(epoch FROM now()-resumed_at)<duration_seconds",
                    (m["user_id"], did),
                )
                m["focusing"] = bool(await cur.fetchone())
        await cur.execute(
            "SELECT i.id,i.recipient_id,u.handle,i.expires_at FROM study_desk_invites i JOIN users u ON u.id=i.recipient_id WHERE i.desk_id=%s AND i.state='pending' AND i.expires_at>now() AND "+audience.subject_sql('i.recipient_id')+" AND %s=%s",
            (did, user, r["owner_id"]),
        )
        invites = await cur.fetchall()
    return {
        "id": did,
        "name": r["name"],
        "goal": r["goal"],
        "version": r["version"],
        "owner_id": r["owner_id"],
        "members": members,
        "sharing": {**r["sharing"], "muted": r["muted"]},
        "invitations": invites,
        "joined_at": r["joined_at"],
    }


@router.get("/rooms/{did}/weekly-goal", dependencies=[Depends(private)])
async def weekly_goal(did: str, user: Account):
    enabled()
    from ..services import desk_goals
    async with cursor() as cur:
        # Consent and counts must describe the same snapshot, including blocks.
        await cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        r = await member(cur, did, user)
        result = await desk_goals.summary(cur, did, user, await desk_goals.clock(cur))
    return result | {"can_edit": r["owner_id"] == user}


@router.post("/rooms/{did}/weekly-goal")
async def save_weekly_goal(did: str, body: WeeklyGoal, request: Request, user: Account):
    enabled()
    await write_guard(request, user)
    from ..services import desk_goals
    async with cursor() as cur:
        await unrestricted(cur, user)
        await member(cur, did, user, owner=True, lock=True)
        period = await desk_goals.clock(cur)
        if body.week_start != period['week_start']:
            raise HTTPException(409, "The IST week changed; refresh before setting a goal")
        await cur.execute("SELECT version FROM study_desk_weekly_goals WHERE desk_id=%s AND week_start=%s FOR UPDATE", (did, body.week_start))
        old = await cur.fetchone()
        if (old['version'] if old else 0) != body.expected_version:
            raise HTTPException(409, "The weekly goal changed; refresh before saving")
        await cur.execute('''INSERT INTO study_desk_weekly_goals(desk_id,week_start,target,updated_by)
          VALUES(%s,%s,%s,%s) ON CONFLICT(desk_id,week_start) DO UPDATE SET
          target=EXCLUDED.target,updated_by=EXCLUDED.updated_by,version=study_desk_weekly_goals.version+1,
          updated_at=clock_timestamp() RETURNING version''', (did, body.week_start, body.target, user))
        version = (await cur.fetchone())['version']
        await event(cur, user, "weekly_goal_set", did, {
            "week_start": body.week_start.isoformat(), "target": body.target, "version": version,
        })
    return {"saved": True, "version": version}


@router.post("/rooms/{did}/sharing")
async def sharing(did: str, body: Sharing, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        previous = await member(cur, did, user)
        if any(
            getattr(body, field) and not previous["sharing"].get(field)
            for field in ("progress", "mistakes", "times")
        ):
            enabled()
            await unrestricted(cur, user)
        await cur.execute(
            "UPDATE study_desk_members SET sharing=%s,muted=%s WHERE desk_id=%s AND user_id=%s",
            (Jsonb(body.model_dump(exclude={"muted"})), body.muted, did, user),
        )
        await event(cur, user, "sharing_changed", did)
    return {"saved": True}


VISIBLE = "NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=x.author_id) OR (b.user_id=x.author_id AND b.blocked_id=%s))"
def visible_sql():
    return VISIBLE+' AND '+audience.subject_sql('x.author_id')


GAME_VISIBLE = """NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
 LEFT JOIN game_cups cup ON cup.id=gr.cup_id WHERE gm.user_id=%s
 AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
 AND gr.questions @> jsonb_build_array(jsonb_build_object('id',x.question_id)))"""


@router.get("/rooms/{did}/items", dependencies=[Depends(private)])
async def items(
    did: str,
    user: Account,
    kind: Literal["all", "question", "note", "bookmark", "mistake", "update"] = "all",
    discussion: Literal['all', 'needed', 'resolved'] = 'all',
    before: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=50),
):
    async with cursor() as cur:
        await member(cur, did, user)
        await cur.execute(
            "SELECT x.id,x.author_id,u.handle AS author,x.kind,x.title,x.body,x.question_id,q.question,q.answer_source,x.version,x.discussion_state,x.created_at FROM study_desk_items x JOIN users u ON u.id=x.author_id LEFT JOIN canonical_questions q ON q.id=x.question_id WHERE x.desk_id=%s AND x.deleted_at IS NULL AND (%s='all' OR x.kind=%s) AND (%s::text IS NULL OR x.id<%s) AND (%s='all' OR x.discussion_state=%s) AND "
            + visible_sql()
            + " AND (x.kind<>'note' OR EXISTS(SELECT 1 FROM study_desk_members nm JOIN users nu ON nu.id=nm.user_id AND nu.closed_at IS NULL WHERE nm.desk_id=x.desk_id AND nm.user_id=x.author_id AND nm.left_at IS NULL AND nm.joined_at<=x.created_at)) AND (x.kind<>'mistake' OR x.author_id=%s OR EXISTS(SELECT 1 FROM study_desk_members m WHERE m.desk_id=x.desk_id AND m.user_id=x.author_id AND m.left_at IS NULL AND (m.sharing->>'mistakes')::boolean)) AND (x.kind<>'update' OR x.author_id=%s OR EXISTS(SELECT 1 FROM study_desk_members m WHERE m.desk_id=x.desk_id AND m.user_id=x.author_id AND m.left_at IS NULL AND (m.sharing->>'progress')::boolean)) AND (x.question_id IS NULL OR (NOT EXISTS(SELECT 1 FROM mock_sessions s WHERE s.user_id=%s AND s.submitted_at IS NULL AND x.question_id=ANY(s.question_ids)) AND " + GAME_VISIBLE + ")) ORDER BY x.id DESC LIMIT %s",
            (did, kind, kind, before, before, discussion, discussion, user, user, user, user, user, user, limit + 1),
        )
        rows = await cur.fetchall()
    return {
        "items": rows[:limit],
        "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
    }


@router.post("/rooms/{did}/items", status_code=201)
async def add_item(
    did: str,
    body: Item,
    request: Request,
    user: Account,
    idempotency_key: Annotated[str, Header(min_length=16, max_length=100)],
):
    enabled()
    await write_guard(request, user)
    sha = fingerprint({"desk": did, **body.model_dump()})
    itemid = (
        "item_"
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        + uuid4().hex[:8]
    )
    async with cursor() as cur:
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("desk-items:" + user,)
        )
        r = await member(cur, did, user, lock=True)
        await unrestricted(cur, user)
        await cur.execute(
            "SELECT id,request_hash FROM study_desk_items WHERE author_id=%s AND request_key=%s",
            (user, idempotency_key),
        )
        old = await cur.fetchone()
        if old:
            if old["request_hash"] != sha:
                raise HTTPException(409, "Request key belongs to another share")
            return {"id": old["id"]}
        if body.kind in ["question", "bookmark", "mistake"] and not body.question_id:
            raise HTTPException(422, "Choose a bank question")
        if body.question_id:
            await protect_answer(cur, user, body.question_id)
            await cur.execute(
                "SELECT 1 FROM canonical_questions WHERE id=%s AND status IN ('live','held')",
                (body.question_id,),
            )
            if not await cur.fetchone():
                raise HTTPException(404, "Question not found")
        if body.kind == "mistake" and not r["sharing"].get("mistakes"):
            raise HTTPException(
                403, "Enable deliberate mistake sharing before posting a mistake"
            )
        if body.kind == "update" and not r["sharing"].get("progress"):
            raise HTTPException(
                403, "Enable progress sharing before posting a progress update"
            )
        if body.kind in ["question", "mistake", "update"] and len(body.body) < 5:
            raise HTTPException(422, "Add a short note explaining what you are sharing")
        if body.kind == "note" and len(body.body) < 1:
            raise HTTPException(422, "Write a note")
        await cur.execute(
            "INSERT INTO study_desk_items(id,desk_id,author_id,kind,question_id,title,body,request_key,request_hash) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                itemid,
                did,
                user,
                body.kind,
                body.question_id,
                body.title,
                body.body,
                idempotency_key,
                sha,
            ),
        )
        await event(cur, user, "item_added", did, {"item_id": itemid})
    return {"id": itemid}


@router.post("/rooms/{did}/items/{iid}")
async def edit_item(
    did: str, iid: str, body: EditItem, request: Request, user: Account
):
    if not body.delete:
        enabled()
    await write_guard(request, user)
    async with cursor() as cur:
        if not body.delete:
            await unrestricted(cur, user)
        r = await member(cur, did, user, lock=True)
        await cur.execute(
            "SELECT * FROM study_desk_items WHERE id=%s AND desk_id=%s AND deleted_at IS NULL FOR UPDATE",
            (iid, did),
        )
        item = await cur.fetchone()
        if not item:
            raise HTTPException(404, "Shared item not found")
        if item["author_id"] != user and not (body.delete and r["owner_id"] == user):
            raise HTTPException(
                403, "Only the author may edit; the owner can remove a shared item"
            )
        if item["version"] != body.expected_version:
            raise HTTPException(409, "Shared item changed; refresh before editing")
        qid = body.question_id if 'question_id' in body.model_fields_set else item['question_id']
        if 'question_id' in body.model_fields_set and item['kind']!='note':
            raise HTTPException(422,'Only notes may change their question attachment')
        if not body.delete:
            await protect_answer(cur,user,item['question_id'])
            await protect_answer(cur,user,qid)
            if qid:
                await cur.execute("SELECT 1 FROM canonical_questions WHERE id=%s AND status IN ('live','held')",(qid,))
                if not await cur.fetchone():raise HTTPException(404,'Question not found')
        await cur.execute(
            "UPDATE study_desk_items SET title=%s,body=%s,question_id=%s,deleted_at=CASE WHEN %s THEN now() END,version=version+1,updated_at=now() WHERE id=%s",
            (
                "" if body.delete else body.title,
                "" if body.delete else body.body,
                qid,
                body.delete,
                iid,
            ),
        )
        await event(
            cur,
            user,
            "item_deleted" if body.delete else "item_edited",
            did,
            {"item_id": iid},
        )
    return {"saved": True}


@router.post('/rooms/{did}/items/{iid}/discussion')
async def discussion_state(did: str, iid: str, body: DiscussionState, request: Request, user: Account):
    enabled()
    await write_guard(request, user)
    async with cursor() as cur:
        await unrestricted(cur, user)
        await member(cur, did, user, lock=True)
        await cur.execute('''SELECT x.* FROM study_desk_items x WHERE x.id=%s AND x.desk_id=%s
          AND x.deleted_at IS NULL AND x.kind IN ('question','mistake') AND x.question_id IS NOT NULL
          AND ''' + visible_sql() + ''' AND (x.kind<>'mistake' OR x.author_id=%s OR EXISTS(
            SELECT 1 FROM study_desk_members m WHERE m.desk_id=x.desk_id AND m.user_id=x.author_id
            AND m.left_at IS NULL AND m.sharing->>'mistakes'='true')) FOR UPDATE OF x''',
          (iid,did,user,user,user))
        item = await cur.fetchone()
        if not item:
            raise HTTPException(404, 'Shared question not found')
        await protect_answer(cur, user, item['question_id'])
        if item['version'] != body.expected_version:
            raise HTTPException(409, 'Shared question changed; refresh before updating discussion')
        if item['discussion_state'] == 'none' and body.state == 'resolved':
            raise HTTPException(409, 'Flag the question for discussion first')
        if item['discussion_state'] == body.state:
            return {'saved': True, 'version': item['version']}
        await cur.execute('''UPDATE study_desk_items SET discussion_state=%s,version=version+1,
          updated_at=clock_timestamp() WHERE id=%s RETURNING version''', (body.state,iid))
        version = (await cur.fetchone())['version']
        await event(cur, user, 'discussion_'+body.state, did, {'item_id':iid,'version':version})
    return {'saved':True,'version':version}


@router.get("/rooms/{did}/messages", dependencies=[Depends(private)])
async def messages(
    did: str,
    user: Account,
    before: int | None = Query(None, gt=0),
    limit: int = Query(30, ge=1, le=50),
):
    async with cursor() as cur:
        await cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        r = await member(cur, did, user)
        await cur.execute(
            "SELECT x.id,x.author_id,u.handle AS author,x.body,x.note_id,x.version,x.created_at FROM study_desk_messages x JOIN users u ON u.id=x.author_id WHERE x.desk_id=%s AND x.deleted_at IS NULL AND x.created_at>=%s AND (%s::bigint IS NULL OR x.id<%s) AND "
            + visible_sql()
            + " ORDER BY x.id DESC LIMIT %s",
            (did, r["joined_at"], before, before, user, user, limit + 1),
        )
        rows = await cur.fetchall()
        for row in rows:
            if row.get('note_id'):
                try:
                    linked = await desk_notes.shared(cur,did,row['note_id'],user)
                    row['note_title'] = linked['title'] or 'Shared note'
                except HTTPException:
                    row['body'] = 'Linked note is unavailable or assessment-locked.'
                    row['note_id'] = None
    return {
        "items": rows[:limit],
        "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
    }


@router.post("/rooms/{did}/messages", status_code=201)
async def send_message(
    did: str,
    body: Message,
    request: Request,
    user: Account,
    idempotency_key: Annotated[str, Header(min_length=16, max_length=100)],
):
    enabled()
    await write_guard(request, user)
    if body.note_id and getattr(request.state,'mobile_session',None):
        raise HTTPException(403,'Shared-note links are available on the website')
    sha = fingerprint([did, body.body] + ([body.note_id] if body.note_id else []))
    async with cursor() as cur:
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("desk-messages:" + user,)
        )
        await member(cur, did, user, lock=True)
        await unrestricted(cur, user)
        await cur.execute(
            "SELECT id,request_hash FROM study_desk_messages WHERE author_id=%s AND request_key=%s",
            (user, idempotency_key),
        )
        old = await cur.fetchone()
        if old:
            if old["request_hash"] != sha:
                raise HTTPException(409, "Request key belongs to another message")
            return {"id": old["id"]}
        if body.note_id:await desk_notes.shared(cur,did,body.note_id,user)
        await cur.execute(
            "INSERT INTO study_desk_messages(desk_id,author_id,body,note_id,request_key,request_hash) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
            (did, user, body.body, body.note_id, idempotency_key, sha),
        )
        mid = (await cur.fetchone())["id"]
        await event(cur, user, "message_sent", did, {"message_id": mid})
        await cur.execute(
            "SELECT user_id FROM study_desk_members WHERE desk_id=%s AND user_id<>%s AND left_at IS NULL AND NOT muted",
            (did, user),
        )
        recipients = await cur.fetchall()
        for recipient in recipients:
            if not await blocked(cur, user, recipient["user_id"]):
                await notify(
                    cur,
                    recipient["user_id"],
                    "desk-chat:"
                    + did
                    + ":"
                    + recipient["user_id"]
                    + ":"
                    + datetime.now(timezone.utc).strftime("%Y%m%d%H"),
                    "New messages in your private study desk",
                    did,
                )
    return {"id": mid}


@router.post("/rooms/{did}/messages/{mid}")
async def edit_message(
    did: str, mid: int, body: EditMessage, request: Request, user: Account
):
    if not body.delete:
        enabled()
    await write_guard(request, user)
    async with cursor() as cur:
        if not body.delete:
            await unrestricted(cur, user)
        r = await member(cur, did, user, lock=True)
        await cur.execute(
            "SELECT * FROM study_desk_messages WHERE id=%s AND desk_id=%s AND deleted_at IS NULL FOR UPDATE",
            (mid, did),
        )
        m = await cur.fetchone()
        if not m or m["created_at"] < r["joined_at"]:
            raise HTTPException(404, "Message not found")
        if m["author_id"] != user and not (body.delete and r["owner_id"] == user):
            raise HTTPException(
                403, "Only the author may edit; the owner can remove a message"
            )
        if m["version"] != body.expected_version:
            raise HTTPException(409, "Message changed; refresh first")
        if body.note_id is not None and body.note_id!=m.get('note_id'):
            raise HTTPException(422,'A message keeps its original note link')
        if m.get('note_id') and not body.delete:
            if getattr(request.state,'mobile_session',None):raise HTTPException(403,'Use the website for shared-note links')
            await desk_notes.shared(cur,did,m['note_id'],user)
        await cur.execute(
            "UPDATE study_desk_messages SET body=%s,deleted_at=CASE WHEN %s THEN now() END,version=version+1,updated_at=now() WHERE id=%s",
            ("" if body.delete else body.body, body.delete, mid),
        )
        await event(
            cur,
            user,
            "message_deleted" if body.delete else "message_edited",
            did,
            {"message_id": mid},
        )
    return {"saved": True}


@router.post("/rooms/{did}/leave")
async def leave(did: str, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        r = await member(cur, did, user, lock=True, include_restricted_owner=True)
        if r["owner_id"] == user:
            raise HTTPException(
                409, "Transfer ownership or close the desk before leaving"
            )
        await cur.execute(
            "UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id=%s",
            (did, user),
        )
        await event(cur, user, "left", did)
    return {"left": True}


@router.post("/rooms/{did}/remove")
async def remove(did: str, body: Member, request: Request, user: Account):
    await write_guard(request, user)
    if body.user_id == user:
        raise HTTPException(422, "Use Leave or Close desk")
    async with cursor() as cur:
        await member(cur, did, user, owner=True, lock=True)
        await cur.execute(
            "UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id=%s AND left_at IS NULL",
            (did, body.user_id),
        )
        await event(cur, user, "member_removed", did, {"user_id": body.user_id})
    return {"removed": True}


@router.post("/rooms/{did}/transfer")
async def transfer(did: str, body: Member, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        await member(cur, did, user, owner=True, lock=True)
        await member(cur, did, body.user_id)
        if body.user_id == user or await blocked(cur, user, body.user_id):
            raise HTTPException(422, "Choose another active member")
        await cur.execute("SELECT account_has_pro(%s) AS pro", (body.user_id,))
        if not (await cur.fetchone())["pro"]:
            raise HTTPException(
                409, "The new owner needs Pro to maintain the shared desk"
            )
        await cur.execute(
            "UPDATE study_desks SET owner_id=%s,version=version+1 WHERE id=%s",
            (body.user_id, did),
        )
        await cur.execute(
            "UPDATE study_desk_invites SET state='cancelled' WHERE desk_id=%s AND state='pending'",
            (did,),
        )
        await event(cur, user, "ownership_transferred", did, {"user_id": body.user_id})
    return {"transferred": True}


@router.post("/rooms/{did}/close")
async def close(did: str, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        await member(cur, did, user, owner=True, lock=True)
        await cur.execute(
            "UPDATE study_desks SET closed_at=now(),version=version+1 WHERE id=%s",
            (did,),
        )
        await cur.execute(
            "UPDATE study_desk_invites SET state='cancelled' WHERE desk_id=%s AND state='pending'",
            (did,),
        )
        await event(cur, user, "closed", did)
    return {"closed": True}


@router.post("/focus", status_code=201)
async def start_focus(
    body: Focus,
    request: Request,
    user: Account,
    idempotency_key: Annotated[str, Header(min_length=16, max_length=100)],
):
    await write_guard(request, user)
    sid = "focus_" + fingerprint([user, idempotency_key])[:28]
    async with cursor() as cur:
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("focus:" + user,)
        )
        if body.desk_id:
            await member(cur, body.desk_id, user)
        await cur.execute("SELECT * FROM study_focus_sessions WHERE id=%s", (sid,))
        old = await cur.fetchone()
        if old:
            if (
                old["duration_seconds"] != body.minutes * 60
                or old["desk_id"] != body.desk_id
            ):
                raise HTTPException(409, "Request key belongs to another session")
            return old
        await cur.execute(
            "SELECT 1 FROM study_focus_sessions WHERE user_id=%s AND state IN ('running','paused')",
            (user,),
        )
        if await cur.fetchone():
            raise HTTPException(
                409, "Resume or finish your existing focus session first"
            )
        await cur.execute(
            "INSERT INTO study_focus_sessions(id,user_id,desk_id,duration_seconds,state,resumed_at) VALUES(%s,%s,%s,%s,'running',now()) RETURNING *",
            (sid, user, body.desk_id, body.minutes * 60),
        )
        r = await cur.fetchone()
    return r


@router.post("/focus/{sid}")
async def change_focus(sid: str, body: FocusAction, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "SELECT *,elapsed_seconds+CASE WHEN resumed_at IS NOT NULL THEN GREATEST(0,extract(epoch FROM now()-resumed_at))::int ELSE 0 END AS elapsed FROM study_focus_sessions WHERE id=%s AND user_id=%s FOR UPDATE",
            (sid, user),
        )
        r = await cur.fetchone()
        if not r:
            raise HTTPException(404, "Focus session not found")
        if r["version"] != body.expected_version:
            raise HTTPException(
                409, "Focus session changed on another device. Refresh first."
            )
        if r["state"] not in ["running", "paused"]:
            raise HTTPException(409, "Focus session has already ended")
        state = {
            "pause": "paused",
            "resume": "running",
            "finish": "completed",
            "cancel": "cancelled",
        }[body.action]
        if (
            body.action == "pause"
            and r["state"] != "running"
            or body.action == "resume"
            and r["state"] != "paused"
        ):
            raise HTTPException(409, "This session is already in that state")
        if state == "completed" and r["elapsed"] < r["duration_seconds"]:
            raise HTTPException(
                409,
                "The focus timer is not complete. End early instead to keep your actual study time.",
            )
        await cur.execute(
            "UPDATE study_focus_sessions SET state=%s,elapsed_seconds=%s,resumed_at=CASE WHEN %s='running' THEN now() END,ended_at=CASE WHEN %s IN ('completed','cancelled') THEN now() END,version=version+1 WHERE id=%s RETURNING *",
            (state, min(r["elapsed"], r["duration_seconds"]), state, state, sid),
        )
        result = await cur.fetchone()
    return result


@router.post("/rooms/{did}/report", status_code=201)
async def report(did: str, body: Report, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        r = await member(cur, did, user)
        if body.target_kind == "desk":
            snapshot = {"name": r["name"], "goal": r["goal"]}
        elif body.target_kind == "item":
            await cur.execute(
                "SELECT id,body,title,author_id,version,created_at FROM study_desk_items WHERE id=%s AND desk_id=%s",
                (body.target_id, did),
            )
            snapshot = await cur.fetchone()
        elif body.target_kind == "message":
            if not body.target_id.isdigit():
                raise HTTPException(422, "Choose an existing message")
            await cur.execute(
                "SELECT id,body,author_id,version,created_at FROM study_desk_messages WHERE id=%s AND desk_id=%s AND created_at>=%s",
                (int(body.target_id), did, r["joined_at"]),
            )
            snapshot = await cur.fetchone()
        else:
            await cur.execute(
                "SELECT id,sender_id,recipient_id,state FROM study_desk_invites WHERE id=%s AND desk_id=%s AND recipient_id=%s",
                (body.target_id, did, user),
            )
            snapshot = await cur.fetchone()
        if not snapshot:
            raise HTTPException(404, "Reported content is unavailable")
        snapshot = json.loads(json.dumps(snapshot, default=str))
        await cur.execute(
            "INSERT INTO study_desk_reports(desk_id,reporter_id,target_kind,target_id,reason,snapshot) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(reporter_id,target_kind,target_id) DO NOTHING",
            (did, user, body.target_kind, body.target_id, body.reason, Jsonb(snapshot)),
        )
        await event(
            cur,
            user,
            "reported",
            did,
            {"kind": body.target_kind, "target_id": body.target_id},
        )
    return {"reported": True}


@router.get("/admin/reports", dependencies=[Depends(private)])
async def reports(staff: Staff):
    async with cursor() as cur:
        await require_role(cur, staff.id, roles=("owner",))
        await cur.execute(
            "SELECT id,desk_id,target_kind,target_id,reason,snapshot,created_at FROM study_desk_reports WHERE state='open' ORDER BY id LIMIT 40"
        )
        rows = await cur.fetchall()
        await event(
            cur,
            staff.id,
            "report_queue_read",
            detail={"report_ids": [r["id"] for r in rows]},
        )
    return {"items": rows}


@router.post("/admin/reports/{rid}/resolve")
async def resolve(rid: int, body: Resolve, staff: Staff):
    async with cursor() as cur:
        await require_role(cur, staff.id, roles=("owner",))
        await cur.execute(
            "SELECT * FROM study_desk_reports WHERE id=%s AND state='open' FOR UPDATE",
            (rid,),
        )
        r = await cur.fetchone()
        if not r:
            raise HTTPException(409, "Report already resolved or unavailable")
        if r["snapshot"].get("author_id", r["snapshot"].get("sender_id")) == staff.id:
            raise HTTPException(
                403, "Another moderator must decide a report on your own content"
            )
        if body.action == "remove":
            table = {"item": "study_desk_items", "message": "study_desk_messages"}.get(
                r["target_kind"]
            )
            if not table:
                raise HTTPException(
                    422,
                    "Desk/invitation reports need an operational account review; remove applies to reported items/messages only",
                )
            target = (
                int(r["target_id"]) if r["target_kind"] == "message" else r["target_id"]
            )
            await cur.execute(
                "SELECT author_id,version FROM "
                + table
                + " WHERE id=%s AND desk_id=%s AND deleted_at IS NULL FOR UPDATE",
                (target, r["desk_id"]),
            )
            current = await cur.fetchone()
            if not current:
                raise HTTPException(
                    409, "The reported content has already been withdrawn"
                )
            if current["author_id"] == staff.id:
                raise HTTPException(
                    403, "Another moderator must decide a report on your own content"
                )
            if current["version"] != r["snapshot"].get("version"):
                raise HTTPException(
                    409,
                    "The content changed after this report. Inspect the retained version; do not remove a newer unreported version.",
                )
            await cur.execute(
                "UPDATE "
                + table
                + " SET body='',deleted_at=now(),version=version+1 WHERE id=%s",
                (target,),
            )
        await cur.execute(
            "UPDATE study_desk_reports SET state='resolved',resolution=%s,retain_until=now()+interval '180 days' WHERE id=%s",
            (body.reason, rid),
        )
        await event(
            cur,
            staff.id,
            "report_resolved",
            r["desk_id"],
            {"report_id": rid, "action": body.action},
        )
    return {"resolved": True}


@router.post("/invites/{iid}/report", status_code=201)
async def report_invite(iid: str, body: Resolve, request: Request, user: Account):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "SELECT id,desk_id,sender_id,recipient_id,state FROM study_desk_invites WHERE id=%s AND recipient_id=%s",
            (iid, user),
        )
        r = await cur.fetchone()
        if not r:
            raise HTTPException(404, "Invitation not found")
        await cur.execute(
            "INSERT INTO study_desk_reports(desk_id,reporter_id,target_kind,target_id,reason,snapshot) VALUES(%s,%s,'invite',%s,%s,%s) ON CONFLICT(reporter_id,target_kind,target_id) DO NOTHING",
            (r["desk_id"], user, iid, body.reason, Jsonb(r)),
        )
        await event(
            cur, user, "reported", r["desk_id"], {"kind": "invite", "target_id": iid}
        )
    return {"reported": True}


class PracticeStart(Strict):
    preview_hash: str = Field(pattern='^[0-9a-f]{64}$')
    request_key: str = Field(min_length=16, max_length=100)


class PracticeJoin(Strict):
    context_hash: str = Field(pattern='^[0-9a-f]{64}$')


@router.get('/rooms/{did}/practice', dependencies=[Depends(private)])
async def practice_sessions(did: str, user: Account):
    enabled()
    from ..services import desk_games, games as g
    async with cursor() as cur:
        await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        await member(cur,did,user)
        preview = desk_games.public_preview(await desk_games.preview(cur,did,user))
        await cur.execute('''SELECT r.*,m.joined_at AS player_joined_at,m.left_at AS player_left_at,
          (SELECT count(*)::int FROM game_members p WHERE p.room_id=r.id AND p.left_at IS NULL) AS players
          FROM game_rooms r LEFT JOIN game_members m ON m.room_id=r.id AND m.user_id=%s
          WHERE r.desk_id=%s AND r.state IN ('waiting','running')
          AND r.created_at>now()-interval '10 minutes' ORDER BY r.created_at DESC LIMIT 10''',(user,did))
        sessions = []
        for r in await cur.fetchall():
            try:
                await desk_games.access(cur,r,user,r['player_joined_at'])
            except HTTPException:
                continue
            joined = r['player_joined_at'] is not None and r['player_left_at'] is None
            sessions.append({'id':r['id'],'state':r['state'],'players':r['players'],
              'capacity':r['capacity'],'context_hash':r['context_hash'],'joined':joined,
              'can_join':not joined and r['state']=='waiting' and r['players']<r['capacity'],
              'questions':len(r['questions']),'round_seconds':r['round_seconds']})
        await cur.execute('''SELECT r.id,r.mode,r.state FROM game_members m JOIN game_rooms r ON r.id=m.room_id
          WHERE m.user_id=%s AND m.released_at IS NULL''',(user,))
        active = await cur.fetchone()
    return {'preview':preview,'sessions':sessions,'active_game':active}


@router.post('/rooms/{did}/practice', dependencies=[Depends(private)])
async def start_practice(did: str, body: PracticeStart, request: Request, user: Account):
    enabled()
    await write_guard(request,user)
    from ..services import desk_games, games as g, game_selection as setup
    from .games import activity_lock, availability, add_member
    from ..services.learning_habit import capture_plan
    async with cursor() as cur:
        await activity_lock(cur,user)
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))")
        await member(cur,did,user,lock=True)
        await unrestricted(cur,user)
        h = g.digest({'desk_id':did,**body.model_dump()})
        await cur.execute('SELECT room_id,request_hash FROM game_start_requests WHERE user_id=%s AND request_key=%s',(user,body.request_key))
        old = await cur.fetchone()
        if old:
            if old['request_hash']!=h:raise HTTPException(409,'Start request belongs to a different session')
            r = await g.room(cur,old['room_id'])
            await g.member(cur,r,user)
            r = await g.advance(cur,r,await g.clock(cur))
            return await g.view(cur,r,user,await g.clock(cur))
        await g.permitted(cur,user)
        await availability(cur,user)
        selected = await desk_games.preview(cur,did,user)
        if selected['context_hash']!=body.preview_hash:
            raise HTTPException(409,'The shared set changed. Refresh the preview and confirm it again.')
        if not selected['can_start']:raise HTTPException(422,selected['message'])
        ctx = selected['context']; questions = await setup.draw(cur,ctx)
        ids = {q['id'] for q in questions}
        ctx['desk_sources'] = [s for s in ctx['desk_sources'] if s['question_id'] in ids]
        # A new game must also respect a completed cup's embargo, not only an
        # active reservation. The preview excludes these for this host already.
        for q in questions:await protect_answer(cur,user,q['id'])
        await capture_plan(cur,user)
        rid = 'game_'+uuid4().hex
        _,seconds,capacity = g.MODES['party']
        await cur.execute('''INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,
          request_key,request_hash,selection_context,context_hash,desk_id)
          VALUES(%s,%s,'party',%s,%s,%s,%s,%s,%s,%s,%s)''',
          (rid,user,capacity,Jsonb(questions),seconds,body.request_key,h,Jsonb(ctx),g.digest(ctx),did))
        r = await g.room(cur,rid)
        await desk_games.access(cur,r,user)
        await add_member(cur,r,user)
        await cur.execute('INSERT INTO game_start_requests(user_id,request_key,room_id,request_hash) VALUES(%s,%s,%s,%s)',(user,body.request_key,rid,h))
        await event(cur,user,'practice_created',did,{'game_id':rid})
        return await g.view(cur,await g.room(cur,rid),user,await g.clock(cur))


@router.post('/rooms/{did}/practice/{rid}/join', dependencies=[Depends(private)])
async def join_practice(did: str, rid: str, body: PracticeJoin, request: Request, user: Account):
    enabled()
    await write_guard(request,user)
    from ..services import desk_games, games as g
    from .games import activity_lock, availability, add_member
    async with cursor() as cur:
        await activity_lock(cur,user)
        await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('creator-graph-v1',0))")
        r = await g.room(cur,rid)
        if r.get('desk_id')!=did:raise HTTPException(404,'Desk practice not found')
        await desk_games.access(cur,r,user)
        await unrestricted(cur,user)
        await g.permitted(cur,user)
        r = await g.advance(cur,r,await g.clock(cur))
        await cur.execute('SELECT * FROM game_members WHERE room_id=%s AND user_id=%s',(rid,user))
        old = await cur.fetchone()
        if old and old['left_at'] is None:
            await desk_games.access(cur,r,user,old['joined_at'])
            return await g.view(cur,r,user,await g.clock(cur))
        # A departed Desk epoch cannot resurrect an old frozen seat by rejoining.
        if old:raise HTTPException(409,'You left this session. Start or join a new one.')
        await availability(cur,user)
        if r['state']!='waiting':raise HTTPException(409,'This practice session has started or expired')
        if body.context_hash!=r['context_hash']:raise HTTPException(409,'Refresh and confirm this shared set before joining')
        for q in r['questions']:await protect_answer(cur,user,q['id'])
        await add_member(cur,r,user)
        await event(cur,user,'practice_joined',did,{'game_id':rid})
        return await g.view(cur,await g.room(cur,rid),user,await g.clock(cur))


@router.get('/rooms/{did}/notes/{iid}', dependencies=[Depends(private)])
async def read_shared_note(did: str, iid: str, user: Account):
    enabled()
    async with cursor() as cur:
        await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        await member(cur,did,user)
        return await desk_notes.shared(cur,did,iid,user)
