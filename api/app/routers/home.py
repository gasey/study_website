from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from datetime import date

from fastapi import APIRouter

from ..db import cursor
from ..schemas import HomeCollection, HomeResponse, QuestionListItem

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("", response_model=HomeResponse)
async def homepage(exam_scope: ExamScope = DEFAULT_SCOPE) -> HomeResponse:
    """Live, public data for the landing page.

    The featured question rotates once a day through the official/transcribed
    scorable pool. It never picks an inferred answer and remains interactive
    through the existing answer endpoint.
    """
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT (SELECT COUNT(*) FROM canonical_questions WHERE {question_scope('canonical_questions', exam_scope)})::int AS total,
                      (SELECT COUNT(*) FROM {pool_view('scorable', exam_scope)})::int AS scorable,
                      (SELECT COUNT(*) FROM {pool_view('practice', exam_scope)})::int AS practice,
                      (SELECT COUNT(*) FROM {pool_view('scorable', exam_scope)}
                        WHERE type='mcq' AND jsonb_array_length(options) >= 2)::int AS featured_pool"""
        )
        counts = await cur.fetchone() or {}
        await cur.execute(
            f"""SELECT c.id, c.title, c.kind, c.route,
                      COUNT(s.path)::int AS sections
                 FROM collections c
                 LEFT JOIN collection_sections s
                   ON s.collection_id=c.id AND s.version=c.live_version
                WHERE c.visibility='public' AND {scope_condition('c', exam_scope)}
                GROUP BY c.id, c.title, c.kind, c.route, c.position
                ORDER BY c.position, c.title"""
        )
        collections = [HomeCollection(**row) for row in await cur.fetchall()]
        pool_size = counts.get("featured_pool", 0)
        question = None
        source = None
        if pool_size:
            day_offset = date.today().toordinal() % pool_size
            await cur.execute(
                f"""SELECT v.id, v.type, v.question, v.options, v.subject, v.topic,
                          v.difficulty, qc.subject_id AS taxonomy_subject_id,
                          qc.subject_label AS taxonomy_subject,
                          qc.topic_id AS taxonomy_topic_id,
                          qc.topic_label AS taxonomy_topic,
                          qc.subtopic_id AS taxonomy_subtopic_id,
                          qc.subtopic_label AS taxonomy_subtopic,
                          qc.review_status AS classification_status,
                          v.answer_source,
                          (v.answer_source IN ('official','key')) AS verified,
                          v.source_defect, v.times_asked, v.first_year, v.last_year,
                          (SELECT p.exam_name ||
                                  CASE WHEN p.paper_number IS NOT NULL THEN ' · ' || p.paper_number ELSE '' END ||
                                  CASE WHEN p.year IS NOT NULL THEN ' · ' || p.year::text ELSE '' END
                             FROM appearances a JOIN papers p ON p.id=a.paper_id
                            WHERE a.canonical_id=v.id AND {scope_condition('p', exam_scope)}
                            ORDER BY a.is_primary DESC, p.year DESC NULLS LAST, a.qnum
                            LIMIT 1) AS source
                     FROM {pool_view('scorable', exam_scope)} v
                     LEFT JOIN question_classifications qc
                       ON qc.question_id=v.id AND qc.review_status='approved'
                    WHERE v.type='mcq' AND jsonb_array_length(v.options) >= 2
                    ORDER BY v.id
                    OFFSET %s LIMIT 1""",
                (day_offset,),
            )
            row = await cur.fetchone()
            if row:
                data = dict(row)
                source = data.pop("source")
                question = QuestionListItem(**data)

    return HomeResponse(
        total_questions=counts.get("total", 0),
        scorable_questions=counts.get("scorable", 0),
        practice_questions=counts.get("practice", 0),
        featured_question=question,
        featured_source=source,
        collections=collections,
    )
