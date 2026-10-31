from ..services.public_catalog_cache import public_catalog
"""Subject shelves are saved classification queries, never question copies."""
from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope

from typing import Literal
from fastapi import APIRouter, HTTPException
from ..db import cursor

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/shelves")
async def shelves(pool: Literal["all", "practice", "scorable"] = "all", exam_scope: ExamScope = DEFAULT_SCOPE):
    return await public_catalog(('shelves',pool,exam_scope),lambda:_shelves(pool,exam_scope))


async def _shelves(pool,exam_scope):
    async with cursor() as cur:
        await cur.execute(f"""SELECT s.id,s.title,s.description,s.match_ids,s.position,
          (SELECT count(*)::int FROM {pool_view(pool, exam_scope)} v WHERE EXISTS(SELECT 1 FROM v_question_paths p WHERE p.question_id=v.id AND (p.subject_id=ANY(s.match_ids) OR p.topic_id=ANY(s.match_ids) OR p.subtopic_id=ANY(s.match_ids)))) AS questions
          FROM library_shelves s WHERE s.active ORDER BY s.position,s.id""")
        return await cur.fetchall()


@router.get("/shelves/{shelf_id}")
async def shelf(shelf_id: str, pool: Literal["all", "practice", "scorable"] = "all", exam_scope: ExamScope = DEFAULT_SCOPE):
    async with cursor() as cur:
        await cur.execute(
            "SELECT * FROM library_shelves WHERE id=%s AND active", (shelf_id,)
        )
        item = await cur.fetchone()
        if not item:
            raise HTTPException(404, "Subject shelf not found")
        await cur.execute(
            f"""SELECT DISTINCT p.subject_id,p.subject_label AS subject,p.topic_id,p.topic_label AS topic,p.subtopic_id,p.subtopic_label AS subtopic,count(DISTINCT p.question_id)::int AS questions
          FROM v_question_paths p JOIN {pool_view(pool, exam_scope)} v ON v.id=p.question_id
          WHERE EXISTS(SELECT 1 FROM v_question_paths m WHERE m.question_id=p.question_id AND (m.subject_id=ANY(%s) OR m.topic_id=ANY(%s) OR m.subtopic_id=ANY(%s)))
          GROUP BY p.subject_id,p.subject_label,p.topic_id,p.topic_label,p.subtopic_id,p.subtopic_label ORDER BY p.subject_label,p.topic_label,p.subtopic_label""",
            (item["match_ids"],) * 3,
        )
        item["topics"] = await cur.fetchall()
        await cur.execute(
            f"""SELECT c.id,c.title FROM collections c WHERE c.visibility='public' AND {scope_condition('c', exam_scope)} AND EXISTS(
          SELECT 1 FROM collection_papers cp JOIN appearances a ON a.paper_id=cp.paper_id JOIN v_question_paths p ON p.question_id=a.canonical_id
          WHERE cp.collection_id=c.id AND cp.version=c.live_version AND (p.subject_id=ANY(%s) OR p.topic_id=ANY(%s) OR p.subtopic_id=ANY(%s))) ORDER BY c.title""",
            (item["match_ids"],) * 3,
        )
        item["exams"] = await cur.fetchall()
        return item
