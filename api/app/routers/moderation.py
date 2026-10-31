import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import cursor
from ..deps import admin_actor
from ..schemas import ModerationActionRequest, ModerationItem, ModerationQueueResponse, ModerationSummary

router = APIRouter(prefix="/api/admin/moderation", tags=["moderation"])
Admin = Annotated[str, Depends(admin_actor)]
Tabs = Literal["Reported", "New users", "Appeals", "My actions"]


async def _summary(cur, actor: str) -> ModerationSummary:
    await cur.execute(
        """SELECT
             (SELECT COUNT(DISTINCT post_id)::int FROM abuse_reports WHERE status='open') AS open_reports,
             (SELECT COUNT(*)::int FROM posts WHERE needs_approval) AS pending_posts,
             (SELECT COUNT(*)::int FROM appeals WHERE status='open') AS open_appeals,
             (SELECT COUNT(*)::int FROM mod_actions
               WHERE actor_id=%s AND created_at >= date_trunc('day', now())) AS handled_today""",
        (actor,),
    )
    return ModerationSummary(**(await cur.fetchone()))


@router.get("/queue", response_model=ModerationQueueResponse)
async def moderation_queue(
    actor: Admin,
    tab: Tabs = "Reported",
    limit: int = Query(40, ge=1, le=100),
) -> ModerationQueueResponse:
    async with cursor() as cur:
        return await queue_items(cur, actor, tab, limit)


async def queue_items(cur, actor: str, tab: str, limit: int):
    counts = await _summary(cur, actor)
    if tab == "Reported":
        await cur.execute(
            """SELECT 'report:' || p.id::text AS id, 'reported' AS item_type,
                      p.id AS post_id, NULL::bigint AS appeal_id, NULL::bigint AS action_id,
                      p.canonical_id, q.question, p.body,p.source_links,
                      COALESCE(NULLIF(u.name,''), u.handle, 'MPSC learner') AS author,
                      COALESCE(u.role, 'learner') AS author_role, p.created_at,
                      array_agg(DISTINCT ar.reason ORDER BY ar.reason) AS reasons,
                      COUNT(DISTINCT ar.id)::int AS report_count,
                      SUM(ar.weight)::float AS report_score,
                      MIN(ar.created_at)::text AS signal,
                      string_agg(DISTINCT ar.note, E'\n') AS note, NULL::text AS action,
                      false AS undone, NULL::jsonb AS before_state
                 FROM abuse_reports ar
                 JOIN posts p ON p.id=ar.post_id
                 JOIN canonical_questions q ON q.id=p.canonical_id
                 LEFT JOIN users u ON u.id=p.author_id
                WHERE ar.status='open'
                GROUP BY p.id, q.id, u.id
                ORDER BY SUM(ar.weight) DESC, MIN(ar.created_at), p.id
                LIMIT %s""",
            (limit,),
        )
    elif tab == "New users":
        await cur.execute(
            """SELECT 'post:' || p.id::text AS id, 'new_user' AS item_type,
                      p.id AS post_id, NULL::bigint AS appeal_id, NULL::bigint AS action_id,
                      p.canonical_id, q.question, p.body,p.source_links,
                      COALESCE(NULLIF(u.name,''), u.handle, 'MPSC learner') AS author,
                      COALESCE(u.role, 'learner') AS author_role, p.created_at,
                      ARRAY['first_post']::text[] AS reasons, 0::int AS report_count,
                      0::float AS report_score,
                      CASE WHEN u.created_at IS NULL THEN 'Awaiting first-post review'
                           ELSE 'Account created ' || to_char(u.created_at, 'YYYY-MM-DD') END AS signal,
                      NULL::text AS note, NULL::text AS action,
                      false AS undone, NULL::jsonb AS before_state
                 FROM posts p
                 JOIN canonical_questions q ON q.id=p.canonical_id
                 LEFT JOIN users u ON u.id=p.author_id
                WHERE p.needs_approval
                ORDER BY p.created_at, p.id
                LIMIT %s""",
            (limit,),
        )
    elif tab == "Appeals":
        await cur.execute(
            """SELECT 'appeal:' || a.id::text AS id, 'appeal' AS item_type,
                      ma.post_id, a.id AS appeal_id, ma.id AS action_id,
                      ma.canonical_id, q.question, a.body,
                      COALESCE(NULLIF(u.name,''), u.handle, 'MPSC learner') AS author,
                      COALESCE(u.role, 'learner') AS author_role, a.created_at,
                      ARRAY[]::text[] AS reasons, 0::int AS report_count,
                      0::float AS report_score,
                      'Appeals must be decided by a different moderator' AS signal,
                      ma.action || CASE WHEN ma.note IS NOT NULL THEN ': ' || ma.note ELSE '' END AS note,
                      NULL::text AS action, false AS undone, NULL::jsonb AS before_state
                 FROM appeals a
                 JOIN mod_actions ma ON ma.id=a.action_id
                 LEFT JOIN posts p ON p.id=ma.post_id
                 LEFT JOIN canonical_questions q ON q.id=COALESCE(ma.canonical_id,p.canonical_id)
                 JOIN users u ON u.id=a.user_id
                WHERE a.status='open'
                ORDER BY a.created_at, a.id
                LIMIT %s""",
            (limit,),
        )
    else:
        await cur.execute(
            """SELECT 'action:' || ma.id::text AS id, 'action' AS item_type,
                      ma.post_id, NULL::bigint AS appeal_id, ma.id AS action_id,
                      ma.canonical_id, q.question,
                      COALESCE(p.body, ma.note, ma.action) AS body,
                      COALESCE(NULLIF(u.name,''), u.handle, 'Staff action') AS author,
                      COALESCE(u.role, 'staff') AS author_role, ma.created_at,
                      CASE WHEN ma.rule IS NULL THEN ARRAY[]::text[] ELSE ARRAY[ma.rule] END AS reasons,
                      0::int AS report_count, 0::float AS report_score,
                      NULL::text AS signal, ma.note, ma.action,
                      EXISTS (SELECT 1 FROM mod_actions undo WHERE undo.reverses=ma.id) AS undone,
                      ma.before_state
                 FROM mod_actions ma
                 LEFT JOIN posts p ON p.id=ma.post_id
                 LEFT JOIN canonical_questions q ON q.id=COALESCE(ma.canonical_id,p.canonical_id)
                 LEFT JOIN users u ON u.id=ma.target_user
                WHERE ma.actor_id=%s
                ORDER BY ma.created_at DESC, ma.id DESC
                LIMIT %s""",
            (actor, limit),
        )
    items = [ModerationItem(**row) for row in await cur.fetchall()]
    return ModerationQueueResponse(tab=tab, counts=counts, items=items)


async def _post_state(cur, post_id: int) -> dict:
    await cur.execute(
        """SELECT id, hidden, needs_approval, hidden_by, hidden_reason
             FROM posts WHERE id=%s FOR UPDATE""",
        (post_id,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "post not found")
    await cur.execute("SELECT id, status FROM abuse_reports WHERE post_id=%s", (post_id,))
    row["reports"] = await cur.fetchall()
    return row


async def _log_action(cur, actor: str, action: str, *, post_id: int | None = None,
                      appeal_id: int | None = None, target_user: str | None = None,
                      canonical_id: str | None = None, rule: str | None = None,
                      note: str | None = None, before_state: dict | None = None,
                      reverses: int | None = None) -> int:
    await cur.execute(
        """INSERT INTO mod_actions
             (actor_id, action, post_id, target_user, canonical_id, rule, note, before_state, reverses)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id""",
        (actor, action, post_id, target_user, canonical_id, rule, note,
         json.dumps(before_state, default=str) if before_state is not None else None, reverses),
    )
    return (await cur.fetchone())["id"]


@router.post("/posts/{post_id}/action")
async def review_post(post_id: int, body: ModerationActionRequest, actor: Admin) -> dict:
    return await moderate_post(post_id, body, actor)


async def moderate_post(post_id: int, body: ModerationActionRequest, actor: str, *, session_owner=False) -> dict:
    if body.action not in {"approve", "reject", "hide", "dismiss"}:
        raise HTTPException(422, "action is not valid for a post")
    if body.action in {"reject", "hide"} and not (body.note or "").strip():
        raise HTTPException(422, "a moderator note is required for this action")
    async with cursor() as cur:
        if session_owner:
            from ..services.review_identity import require_role
            from ..services.bank_review import protect_answer
            await require_role(cur, actor, roles=('owner',))
            await cur.execute('SELECT author_id,canonical_id FROM posts WHERE id=%s FOR UPDATE', (post_id,))
            target=await cur.fetchone()
            if not target: raise HTTPException(404, 'Post not found')
            if target['author_id']==actor: raise HTTPException(403, 'Another moderator must review your post')
            await protect_answer(cur, actor, target['canonical_id'])
        before = await _post_state(cur, post_id)
        await cur.execute("SELECT canonical_id, author_id, needs_approval FROM posts WHERE id=%s", (post_id,))
        post = await cur.fetchone()
        if body.action in {"approve", "reject"} and not post["needs_approval"]:
            raise HTTPException(409, "post is no longer awaiting approval")
        if body.action == "approve":
            await cur.execute("SELECT COUNT(*)::int AS n FROM abuse_reports WHERE post_id=%s AND status='open'", (post_id,))
            if (await cur.fetchone())["n"]:
                raise HTTPException(409, "resolve open conduct reports before publishing this post")
        if body.action in {"hide", "dismiss"}:
            await cur.execute("SELECT COUNT(*)::int AS n FROM abuse_reports WHERE post_id=%s AND status='open'", (post_id,))
            if not (await cur.fetchone())["n"]:
                raise HTTPException(409, "post has no open reports")
        if body.action == "approve":
            await cur.execute("UPDATE posts SET needs_approval=false WHERE id=%s AND needs_approval", (post_id,))
            from .discussions import notify_reply
            await notify_reply(cur, post_id)
        elif body.action == "reject":
            await cur.execute(
                """UPDATE posts SET needs_approval=false, hidden=true, hidden_by='admin',
                          hidden_reason=%s WHERE id=%s""",
                (body.note or "Rejected during moderation review", post_id),
            )
            await cur.execute("UPDATE abuse_reports SET status='upheld' WHERE post_id=%s AND status='open'", (post_id,))
        elif body.action == "hide":
            await cur.execute(
                "UPDATE posts SET hidden=true, hidden_by='admin', hidden_reason=%s WHERE id=%s",
                (body.note or "Hidden after moderation report review", post_id),
            )
            await cur.execute("UPDATE abuse_reports SET status='upheld' WHERE post_id=%s AND status='open'", (post_id,))
        else:
            await cur.execute("UPDATE abuse_reports SET status='dismissed' WHERE post_id=%s AND status='open'", (post_id,))
            if before["hidden"] and before["hidden_by"] is None and before["hidden_reason"] is None:
                # The report trigger auto-hides without recording a human
                # moderator. Dismissing all reports may safely undo that hide.
                await cur.execute("UPDATE posts SET hidden=false WHERE id=%s", (post_id,))
        await cur.execute("SELECT reason FROM abuse_reports WHERE post_id=%s ORDER BY created_at LIMIT 1", (post_id,))
        report = await cur.fetchone()
        rule = report["reason"] if report else None
        await _log_action(
            cur, actor, body.action, post_id=post_id,
            target_user=post["author_id"] if post["author_id"] != "team" else None,
            canonical_id=post["canonical_id"],
            rule=rule, note=body.note, before_state=before,
        )
    return {"ok": True}


@router.post("/appeals/{appeal_id}/action")
async def decide_appeal(appeal_id: int, body: ModerationActionRequest, actor: Admin) -> dict:
    if body.action not in {"grant_appeal", "deny_appeal"}:
        raise HTTPException(422, "action is not valid for an appeal")
    if body.action == "deny_appeal" and not (body.note or "").strip():
        raise HTTPException(422, "a note is required when denying an appeal")
    async with cursor() as cur:
        await cur.execute(
            """SELECT a.*, ma.actor_id AS original_actor, ma.post_id,
                      ma.canonical_id, ma.target_user, s.lifted_at, s.lifted_by
                 FROM appeals a JOIN mod_actions ma ON ma.id=a.action_id
                 LEFT JOIN sanctions s ON s.id=a.sanction_id
                WHERE a.id=%s FOR UPDATE OF a""",
            (appeal_id,),
        )
        appeal = await cur.fetchone()
        if not appeal:
            raise HTTPException(404, "appeal not found")
        if appeal["status"] != "open":
            raise HTTPException(409, "appeal is no longer open")
        if appeal["original_actor"] == actor:
            raise HTTPException(409, "another moderator must decide this appeal")
        before = {"appeal_id": appeal_id, "status": appeal["status"], "decided_by": appeal["decided_by"], "decided_at": appeal["decided_at"], "sanction_id": appeal["sanction_id"], "lifted_at": appeal["lifted_at"], "lifted_by": appeal["lifted_by"]}
        status = "granted" if body.action == "grant_appeal" else "denied"
        await cur.execute("UPDATE appeals SET status=%s, decided_by=%s, decided_at=now() WHERE id=%s", (status, actor, appeal_id))
        if status == "granted" and appeal["sanction_id"] is not None:
            await cur.execute("UPDATE sanctions SET lifted_at=now(), lifted_by=%s WHERE id=%s AND lifted_at IS NULL", (actor, appeal["sanction_id"]))
        await _log_action(cur, actor, body.action, post_id=appeal["post_id"], target_user=appeal["user_id"], canonical_id=appeal["canonical_id"], note=body.note, before_state=before)
    return {"ok": True}


@router.post("/actions/{action_id}/undo")
async def undo_action(action_id: int, actor: Admin) -> dict:
    async with cursor() as cur:
        await cur.execute("SELECT * FROM mod_actions WHERE id=%s AND actor_id=%s FOR UPDATE", (action_id, actor))
        original = await cur.fetchone()
        if not original:
            raise HTTPException(404, "action not found")
        if original["action"] == "restore" or original["before_state"] is None:
            raise HTTPException(409, "this action cannot be undone")
        await cur.execute("SELECT 1 FROM mod_actions WHERE reverses=%s", (action_id,))
        if await cur.fetchone():
            raise HTTPException(409, "action has already been undone")
        state = original["before_state"]
        if original["post_id"] is not None:
            await _post_state(cur, original["post_id"])
            await cur.execute(
                """UPDATE posts SET hidden=%s, needs_approval=%s, hidden_by=%s, hidden_reason=%s
                    WHERE id=%s""",
                (state["hidden"], state["needs_approval"], state["hidden_by"], state["hidden_reason"], original["post_id"]),
            )
            for report in state.get("reports", []):
                await cur.execute("UPDATE abuse_reports SET status=%s WHERE id=%s", (report["status"], report["id"]))
        if state.get("appeal_id") is not None:
            await cur.execute(
                "UPDATE appeals SET status=%s, decided_by=%s, decided_at=%s WHERE id=%s",
                (state["status"], state["decided_by"], state["decided_at"], state["appeal_id"]),
            )
            if state.get("sanction_id") is not None:
                await cur.execute("UPDATE sanctions SET lifted_at=%s, lifted_by=%s WHERE id=%s", (state["lifted_at"], state["lifted_by"], state["sanction_id"]))
        await _log_action(cur, actor, "restore", post_id=original["post_id"], target_user=original["target_user"], canonical_id=original["canonical_id"], note=f"Undo action {action_id}", before_state={"reversed_action": action_id}, reverses=action_id)
        await cur.execute("UPDATE mod_actions SET review_result='reversed' WHERE id=%s", (action_id,))
    return {"ok": True}
