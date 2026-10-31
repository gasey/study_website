"""Staff-verified official notices, calendar dates and private learner follows."""

from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..services.review_identity import Actor, identity, require_role
from .materials import write_guard

router = APIRouter(prefix="/api", tags=["exam calendar"])
User = Annotated[str, Depends(current_user)]
Account = Annotated[str, Depends(require_account)]
Staff = Annotated[Actor, Depends(identity)]
Kind = Literal["notification", "deadline", "admit_card", "exam", "answer_key", "result"]
PUBLIC = "e.id,e.collection_id,c.title AS exam_title,e.title,e.kind,e.starts_on,e.ends_on,e.summary,e.source_url,e.source_reference,e.verification_note,e.verified_on,e.version,e.published_at,e.updated_at,e.state"
JOIN = " FROM exam_calendar_events e LEFT JOIN collections c ON c.id=e.collection_id "
TODAY = "(now() AT TIME ZONE 'Asia/Kolkata')::date"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Event(Strict):
    title: str = Field(min_length=3, max_length=180)
    collection_id: str | None = Field(default=None, max_length=100)
    kind: Kind
    starts_on: date | None = None
    ends_on: date | None = None
    summary: str = Field(default="", max_length=3000)
    source_url: str = Field(max_length=2000)
    source_reference: str = Field(min_length=3, max_length=300)
    verification_note: str = Field(min_length=10, max_length=1000)
    verified_on: date
    state: Literal["draft", "published", "archived"] = "draft"

    @field_validator("source_url")
    @classmethod
    def official(cls, v):
        try:
            u = urlsplit(v)
            port = u.port
        except ValueError:
            raise ValueError("Invalid official source URL")
        if (
            u.scheme != "https"
            or u.hostname not in {"mpsc.mizoram.gov.in", "mpsconline.mizoram.gov.in"}
            or u.username
            or u.password
            or port not in (None, 443)
            or any(ord(x) < 33 for x in v)
        ):
            raise ValueError(
                "Use an HTTPS source on the official MPSC website or application portal"
            )
        return v

    @model_validator(mode="after")
    def dates(self):
        if self.ends_on and (not self.starts_on or self.ends_on < self.starts_on):
            raise ValueError("End date must follow start date")
        if self.kind != "notification" and not self.starts_on:
            raise ValueError("This event needs an official date")
        from zoneinfo import ZoneInfo
        from datetime import datetime

        if self.verified_on > datetime.now(ZoneInfo("Asia/Kolkata")).date():
            raise ValueError("Verification date cannot be in the future")
        return self


class Save(Strict):
    expected_version: int = Field(ge=0)
    reason: str = Field(min_length=10, max_length=1000)
    event: Event


class Toggle(Strict):
    enabled: bool


class Follow(Toggle):
    collection_id: str = Field(min_length=1, max_length=100)


class Watch(Toggle):
    event_id: str = Field(min_length=1, max_length=100)


def span(start: date, end: date):
    if end < start or (end - start).days > 366:
        raise HTTPException(422, "Choose a date range of at most 366 days")


@router.get("/calendar/events")
async def events(
    response: Response,
    start: date,
    end: date,
    kind: Kind | None = None,
    collection_id: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
):
    span(start, end)
    response.headers["Cache-Control"] = "public, max-age=30"
    async with cursor() as cur:
        where = "WHERE (e.collection_id IS NULL OR c.visibility='public') AND e.state='published' AND e.starts_on<=%s AND COALESCE(e.ends_on,e.starts_on)>=%s AND (%s::text IS NULL OR e.kind=%s) AND (%s::text IS NULL OR e.collection_id=%s)"
        args = (end, start, kind, kind, collection_id, collection_id)
        await cur.execute("SELECT count(*) AS n" + JOIN + where, args)
        total = (await cur.fetchone())["n"]
        await cur.execute(
            "SELECT "
            + PUBLIC
            + JOIN
            + where
            + " ORDER BY e.starts_on,e.id LIMIT %s OFFSET %s",
            (*args, limit, offset),
        )
        return {"items": await cur.fetchall(), "total": total}


@router.get("/calendar/notices")
async def notices(
    response: Response,
    kind: Kind | None = None,
    collection_id: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
):
    response.headers["Cache-Control"] = "public, max-age=30"
    async with cursor() as cur:
        await cur.execute(
            "SELECT "
            + PUBLIC
            + JOIN
            + "WHERE (e.collection_id IS NULL OR c.visibility='public') AND e.state='published' AND (%s::text IS NULL OR e.kind=%s) AND (%s::text IS NULL OR e.collection_id=%s) ORDER BY e.published_at DESC,e.id LIMIT %s OFFSET %s",
            (kind, kind, collection_id, collection_id, limit + 1, offset),
        )
        rows = await cur.fetchall()
        return {"items": rows[:limit], "has_more": len(rows) > limit}


@router.get("/calendar/events/{eid}")
async def public_event(eid: str, response: Response):
    response.headers["Cache-Control"] = "public, max-age=30"
    async with cursor() as cur:
        await cur.execute(
            "SELECT "
            + PUBLIC
            + JOIN
            + "WHERE (e.collection_id IS NULL OR c.visibility='public') AND e.id=%s AND (e.state='published' OR (e.state='archived' AND e.published_at IS NOT NULL))",
            (eid,),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Notice not found or withdrawn")
        return row


@router.get("/me/calendar")
async def personal(user: User, response: Response):
    response.headers["Cache-Control"] = "private, no-store"
    async with cursor() as cur:
        await cur.execute(
            "SELECT collection_id FROM user_exam_bookmarks WHERE user_id=%s", (user,)
        )
        follows = [r["collection_id"] for r in await cur.fetchall()]
        await cur.execute(
            "SELECT event_id FROM user_calendar_saved WHERE user_id=%s", (user,)
        )
        saved = [r["event_id"] for r in await cur.fetchall()]
        await cur.execute(
            "SELECT reminders FROM user_calendar_preferences WHERE user_id=%s", (user,)
        )
        pref = await cur.fetchone()
        await cur.execute(
            "SELECT "
            + PUBLIC
            + JOIN
            + "WHERE (e.collection_id IS NULL OR c.visibility='public') AND e.state='published' AND COALESCE(e.ends_on,e.starts_on)>="
            + TODAY
            + " AND (e.collection_id=ANY(%s) OR e.id=ANY(%s)) ORDER BY e.starts_on,e.id LIMIT 1",
            (follows, saved),
        )
        upcoming = await cur.fetchone()
        await cur.execute(
            "SELECT email IS NOT NULL AS registered FROM users WHERE id=%s", (user,)
        )
        account = await cur.fetchone()
        return {
            "registered": bool(account and account["registered"]),
            "following": follows,
            "saved": saved,
            "reminders": bool(pref and pref["reminders"]),
            "upcoming": upcoming,
        }


@router.post("/me/calendar/reminders")
async def preferences(body: Toggle, user: Account, request: Request):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET reminders=excluded.reminders,updated_at=now()",
            (user, body.enabled),
        )
    return {"reminders": body.enabled}


@router.post("/me/calendar/follow")
async def follow(body: Follow, user: Account, request: Request):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "SELECT 1 FROM collections WHERE id=%s AND visibility='public'",
            (body.collection_id,),
        )
        if not await cur.fetchone():
            raise HTTPException(404, "Exam not found")
        if body.enabled:
            await cur.execute("SELECT 1 FROM users WHERE id=%s FOR UPDATE", (user,))
            await cur.execute(
                "SELECT count(*) AS n FROM user_exam_bookmarks WHERE user_id=%s AND NOT EXISTS(SELECT 1 FROM user_exam_bookmarks WHERE user_id=%s AND collection_id=%s)",
                (user, user, body.collection_id),
            )
            if (await cur.fetchone())["n"] >= 100:
                raise HTTPException(409, "At most 100 followed exams are supported")
            await cur.execute(
                "INSERT INTO user_exam_bookmarks(user_id,collection_id) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                (user, body.collection_id),
            )
        else:
            await cur.execute(
                "DELETE FROM user_exam_bookmarks WHERE user_id=%s AND collection_id=%s",
                (user, body.collection_id),
            )
    return {"following": body.enabled}


@router.post("/me/calendar/save")
async def watch(body: Watch, user: Account, request: Request):
    await write_guard(request, user)
    async with cursor() as cur:
        await cur.execute(
            "SELECT 1 FROM exam_calendar_events WHERE id=%s AND state='published'",
            (body.event_id,),
        )
        if not await cur.fetchone() and body.enabled:
            raise HTTPException(404, "Notice not found")
        if body.enabled:
            await cur.execute("SELECT 1 FROM users WHERE id=%s FOR UPDATE", (user,))
            await cur.execute(
                "SELECT count(*) AS n FROM user_calendar_saved WHERE user_id=%s AND NOT EXISTS(SELECT 1 FROM user_calendar_saved WHERE user_id=%s AND event_id=%s)",
                (user, user, body.event_id),
            )
            if (await cur.fetchone())["n"] >= 500:
                raise HTTPException(409, "At most 500 saved notices are supported")
            await cur.execute(
                "INSERT INTO user_calendar_saved(user_id,event_id) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                (user, body.event_id),
            )
        else:
            await cur.execute(
                "DELETE FROM user_calendar_saved WHERE user_id=%s AND event_id=%s",
                (user, body.event_id),
            )
    return {"saved": body.enabled}


@router.get("/admin/calendar")
async def admin_list(
    actor: Staff, response: Response, offset: int = Query(0, ge=0, le=100000)
):
    response.headers["Cache-Control"] = "private, no-store"
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        await cur.execute(
            "SELECT e.*,c.title AS exam_title"
            + JOIN
            + "ORDER BY e.updated_at DESC,e.id LIMIT 50 OFFSET %s",
            (offset,),
        )
        return {"items": await cur.fetchall()}


@router.post("/admin/calendar/{eid}")
async def save_event(eid: str, body: Save, actor: Staff):
    if len(eid) > 100:
        raise HTTPException(422, "Notice ID too long")
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        # Serializes creation and updates of the same absent/existing ID.
        await cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", ("calendar:" + eid,)
        )
        await cur.execute(
            "SELECT * FROM exam_calendar_events WHERE id=%s FOR UPDATE", (eid,)
        )
        old = await cur.fetchone()
        if (old["version"] if old else 0) != body.expected_version:
            raise HTTPException(409, "This notice changed. Reload before saving.")
        if body.event.collection_id:
            await cur.execute(
                "SELECT 1 FROM collections WHERE id=%s AND visibility='public'",
                (body.event.collection_id,),
            )
            if not await cur.fetchone():
                raise HTTPException(422, "Choose a public exam collection")
        if old and old["published_at"] is not None and body.event.state == "draft":
            raise HTTPException(
                422, "Withdraw a published notice instead of returning it to draft"
            )
        data = body.event.model_dump(mode="json")
        version = body.expected_version + 1
        columns = list(data)
        if old:
            await cur.execute(
                "UPDATE exam_calendar_events SET "
                + ",".join(k + "=%s" for k in columns)
                + ",version=%s,updated_by=%s,updated_at=now(),published_at=CASE WHEN %s='published' THEN now() ELSE published_at END WHERE id=%s",
                (*data.values(), version, actor.id, body.event.state, eid),
            )
        else:
            await cur.execute(
                "INSERT INTO exam_calendar_events(id,"
                + ",".join(columns)
                + ",created_by,updated_by,published_at) VALUES("
                + ",".join(["%s"] * (len(columns) + 3))
                + ",CASE WHEN %s='published' THEN now() END)",
                (eid, *data.values(), actor.id, actor.id, body.event.state),
            )
        await cur.execute(
            "INSERT INTO calendar_history(event_id,actor_id,version,reason,snapshot) VALUES(%s,%s,%s,%s,%s)",
            (eid, actor.id, version, body.reason, Jsonb(data)),
        )
        await cur.execute("SELECT * FROM exam_calendar_events WHERE id=%s", (eid,))
        return await cur.fetchone()


@router.get("/admin/calendar/{eid}/history")
async def history(eid: str, actor: Staff, response: Response):
    response.headers["Cache-Control"] = "private, no-store"
    async with cursor() as cur:
        await require_role(cur, actor.id, roles=("owner",))
        await cur.execute(
            "SELECT version,reason,snapshot,created_at,actor_id FROM calendar_history WHERE event_id=%s ORDER BY version DESC LIMIT 100",
            (eid,),
        )
        return {"items": await cur.fetchall()}
