"""Unified search respects the audience of every underlying product."""
from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope

from typing import Annotated, Literal
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from ..db import cursor
from ..deps import current_user

router = APIRouter(prefix="/api", tags=["global search"])
KINDS = ("questions", "people", "notes", "desks", "listings", "exams")


@router.get("/search")
async def search(
    response: Response,
    user: Annotated[str, Depends(current_user)],
    q: str = Query(min_length=2, max_length=120),
    category: Literal[
        "all", "questions", "people", "notes", "desks", "listings", "exams"
    ] = "all",
    offset: int = Query(0, ge=0, le=10000),
    exam_scope: ExamScope = DEFAULT_SCOPE):
    response.headers["Cache-Control"] = "private, no-store"
    q = " ".join(q.split())
    if len(q) < 2:
        raise HTTPException(422, "Enter at least two non-space characters")
    pattern = (
        "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    )
    queries = {
        "questions": (
            f"""SELECT v.id,v.question AS title,COALESCE(qc.subject_label,'Question bank') AS meta,''::text AS snippet FROM {pool_view('all', exam_scope)} v LEFT JOIN question_classifications qc ON qc.question_id=v.id AND qc.review_status='approved' WHERE v.search @@ plainto_tsquery('english',%s) OR v.question ILIKE %s OR qc.subject_label ILIKE %s OR qc.topic_label ILIKE %s OR qc.subject_id ILIKE %s OR EXISTS(SELECT 1 FROM v_question_paths sp WHERE sp.question_id=v.id AND (sp.subject_label ILIKE %s OR sp.topic_label ILIKE %s OR sp.subtopic_label ILIKE %s))""",
            (q, pattern, pattern, pattern, pattern, pattern, pattern, pattern),
        ),
        "people": (
            "SELECT u.id,u.handle AS title,'Public creator'::text AS meta,p.bio AS snippet FROM users u JOIN creator_profiles p ON p.user_id=u.id AND p.public WHERE u.email IS NOT NULL AND (u.handle ILIKE %s OR p.bio ILIKE %s) AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=u.id) OR (b.user_id=u.id AND b.blocked_id=%s))",
            (pattern, pattern, user, user),
        ),
        "desks": (
            "SELECT d.id,d.name AS title,'Your private desk'::text AS meta,d.goal AS snippet FROM study_desks d JOIN study_desk_members m ON m.desk_id=d.id AND m.user_id=%s AND m.left_at IS NULL WHERE d.closed_at IS NULL AND (d.name ILIKE %s OR d.goal ILIKE %s)",
            (user, pattern, pattern),
        ),
        "exams": (
            f"""SELECT id,title,'Exam collection'::text AS meta,''::text AS snippet FROM collections WHERE visibility='public' AND {scope_condition('collections', exam_scope)} AND (title ILIKE %s OR id ILIKE %s)""",
            (pattern, pattern),
        ),
    }
    material = """SELECT m.id,r.payload->>'title' AS title,CASE r.payload->>'access' WHEN 'paid-preview' THEN 'Paid preview · checkout unavailable' WHEN 'pro' THEN 'Pro material' ELSE 'Published material' END AS meta,r.payload->>'summary' AS snippet
      FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision
      WHERE m.status='published' AND (r.payload->>'title' ILIKE %s OR r.payload->>'summary' ILIKE %s OR r.payload->'tags' ? %s)
      AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%s))"""
    args = (pattern, pattern, q, user, user)
    queries["listings"] = (material + " AND r.payload->>'access'='paid-preview'", args)
    queries["notes"] = (
        material
        + " UNION ALL SELECT 'private:'||(n->>'id'),n->>'title','Your private note',n->>'body' FROM personal_desks d CROSS JOIN LATERAL jsonb_array_elements(COALESCE(d.document->'notes','[]')) n WHERE d.user_id=%s AND (n->>'title' ILIKE %s OR n->>'body' ILIKE %s)",
        (*args, user, pattern, pattern),
    )
    groups = []
    async with cursor() as cur:
        for name in KINDS if category == "all" else (category,):
            sql, args = queries[name]
            await cur.execute(
                "SELECT count(*)::int AS total FROM (" + sql + ") result", args
            )
            total = (await cur.fetchone())["total"]
            await cur.execute(
                "SELECT id,title,meta,left(COALESCE(snippet,''),200) AS snippet FROM ("
                + sql
                + ") result ORDER BY title,id LIMIT %s OFFSET %s",
                (
                    *args,
                    4 if category == "all" else 20,
                    0 if category == "all" else offset,
                ),
            )
            items = await cur.fetchall()
            for item in items:
                eid = quote(item["id"], safe="")
                item["url"] = (
                    "/desk?tab=notes"
                    if item["id"].startswith("private:")
                    else "/"
                    + {
                        "questions": "bank",
                        "people": "creators",
                        "notes": "materials",
                        "desks": "desk",
                        "listings": "materials",
                        "exams": "exams",
                    }[name]
                    + "/"
                    + eid
                )
            groups.append({"category": name, "total": total, "items": items})
    return {"query": q, "category": category, "offset": offset, "groups": groups}
