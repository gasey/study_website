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
from .materials import write_guard as content_write_guard

router = APIRouter(prefix="/api/desk", tags=["study desk"])
User = Annotated[str, Depends(current_user)]
Account = Annotated[str, Depends(require_account)]
Staff = Annotated[Actor, Depends(identity)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Task(Strict):
    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=140)
    done: bool = False
    week: bool = False


class Note(Strict):
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
    title: str = Field(default="", max_length=140)
    body: str = Field(default="", max_length=4000)
    delete: bool = False


class Message(Strict):
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


async def member(cur, did, user, owner=False, lock=False):
    await cur.execute(
        "SELECT d.*,m.joined_at,m.sharing,m.muted FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL WHERE d.id=%s AND d.closed_at IS NULL"
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
    await cur.execute(
        "INSERT INTO review_notifications(user_id,event_key,message,study_desk_id,study_invite_id) VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        (user, key, text, did, invite),
    )


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@router.get("/personal", dependencies=[Depends(private)])
async def personal(user: User):
    async with cursor() as cur:
        await cur.execute(
            "SELECT avatar,handle,email IS NOT NULL AS registered FROM users WHERE id=%s",
            (user,),
        )
        who = await cur.fetchone()
        await cur.execute(
            "SELECT document,version FROM personal_desks WHERE user_id=%s", (user,)
        )
        row = await cur.fetchone()
    return {
        "user_id": user,
        **who,
        "data": Document.model_validate(row["document"] if row else {}).model_dump(
            mode="json"
        ),
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
            "SELECT version FROM personal_desks WHERE user_id=%s FOR UPDATE", (user,)
        )
        old = await cur.fetchone()
        if (old["version"] if old else 0) != body.expected_version:
            raise HTTPException(
                409,
                "Your desk changed on another device. Reload the account version or explicitly keep your local edits.",
            )
        qids = set(body.data.saved + body.data.recent)
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
        doc = body.data.model_dump(mode="json")
        await cur.execute(
            "INSERT INTO personal_desks(user_id,document) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET document=EXCLUDED.document,version=personal_desks.version+1,updated_at=now() RETURNING version",
            (user, Jsonb(doc)),
        )
        version = (await cur.fetchone())["version"]
    return {"data": doc, "version": version}


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
            "SELECT d.id,d.name,d.goal,d.owner_id,d.version,count(mm.user_id)::int AS members FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL LEFT JOIN study_desk_members mm ON mm.desk_id=d.id AND mm.left_at IS NULL WHERE d.closed_at IS NULL GROUP BY d.id ORDER BY d.created_at",
            (user,),
        )
        rows = await cur.fetchall()
        await cur.execute(
            "SELECT i.id,i.desk_id,i.sender_id,d.name,u.handle AS sender,i.expires_at FROM study_desk_invites i JOIN study_desks d ON d.id=i.desk_id AND d.closed_at IS NULL JOIN users u ON u.id=i.sender_id WHERE i.recipient_id=%s AND i.state='pending' AND i.expires_at>now() AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=i.sender_id) OR (b.user_id=i.sender_id AND b.blocked_id=%s)) ORDER BY i.created_at DESC LIMIT 30",
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
            "SELECT id FROM users WHERE handle=%s AND email IS NOT NULL", (body.handle,)
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
            "SELECT * FROM study_desks WHERE id=%s AND closed_at IS NULL FOR UPDATE",
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
            "SELECT m.user_id,u.handle,u.avatar,m.sharing,m.user_id=%s AS is_you FROM study_desk_members m JOIN users u ON u.id=m.user_id WHERE m.desk_id=%s AND m.left_at IS NULL ORDER BY m.joined_at,m.user_id",
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
            "SELECT i.id,i.recipient_id,u.handle,i.expires_at FROM study_desk_invites i JOIN users u ON u.id=i.recipient_id WHERE i.desk_id=%s AND i.state='pending' AND i.expires_at>now() AND %s=%s",
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


@router.get("/rooms/{did}/items", dependencies=[Depends(private)])
async def items(
    did: str,
    user: Account,
    kind: Literal["all", "question", "note", "bookmark", "mistake", "update"] = "all",
    before: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=50),
):
    async with cursor() as cur:
        await member(cur, did, user)
        await cur.execute(
            "SELECT x.id,x.author_id,u.handle AS author,x.kind,x.title,x.body,x.question_id,q.question,q.answer_source,x.version,x.created_at FROM study_desk_items x JOIN users u ON u.id=x.author_id LEFT JOIN canonical_questions q ON q.id=x.question_id WHERE x.desk_id=%s AND x.deleted_at IS NULL AND (%s='all' OR x.kind=%s) AND (%s::text IS NULL OR x.id<%s) AND "
            + VISIBLE
            + " AND (x.kind<>'mistake' OR x.author_id=%s OR EXISTS(SELECT 1 FROM study_desk_members m WHERE m.desk_id=x.desk_id AND m.user_id=x.author_id AND m.left_at IS NULL AND (m.sharing->>'mistakes')::boolean)) AND (x.kind<>'update' OR x.author_id=%s OR EXISTS(SELECT 1 FROM study_desk_members m WHERE m.desk_id=x.desk_id AND m.user_id=x.author_id AND m.left_at IS NULL AND (m.sharing->>'progress')::boolean)) AND (x.question_id IS NULL OR NOT EXISTS(SELECT 1 FROM mock_sessions s WHERE s.user_id=%s AND s.submitted_at IS NULL AND x.question_id=ANY(s.question_ids))) ORDER BY x.id DESC LIMIT %s",
            (did, kind, kind, before, before, user, user, user, user, user, limit + 1),
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
        await cur.execute(
            "UPDATE study_desk_items SET title=%s,body=%s,deleted_at=CASE WHEN %s THEN now() END,version=version+1,updated_at=now() WHERE id=%s",
            (
                "" if body.delete else body.title,
                "" if body.delete else body.body,
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


@router.get("/rooms/{did}/messages", dependencies=[Depends(private)])
async def messages(
    did: str,
    user: Account,
    before: int | None = Query(None, gt=0),
    limit: int = Query(30, ge=1, le=50),
):
    async with cursor() as cur:
        r = await member(cur, did, user)
        await cur.execute(
            "SELECT x.id,x.author_id,u.handle AS author,x.body,x.version,x.created_at FROM study_desk_messages x JOIN users u ON u.id=x.author_id WHERE x.desk_id=%s AND x.deleted_at IS NULL AND x.created_at>=%s AND (%s::bigint IS NULL OR x.id<%s) AND "
            + VISIBLE
            + " ORDER BY x.id DESC LIMIT %s",
            (did, r["joined_at"], before, before, user, user, limit + 1),
        )
        rows = await cur.fetchall()
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
    sha = fingerprint([did, body.body])
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
        await cur.execute(
            "INSERT INTO study_desk_messages(desk_id,author_id,body,request_key,request_hash) VALUES(%s,%s,%s,%s,%s) RETURNING id",
            (did, user, body.body, idempotency_key, sha),
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
        r = await member(cur, did, user, lock=True)
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
