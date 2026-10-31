import hashlib,json
from ..services.question_readiness import answer_status_sql, reviewed_answer_sql
from ..services.learning_taxonomy import CLERICAL_EXAMS, path_projection, topic_expression
from ..services.source_identity import identities_for, display_identity
from ..services.group_b_study import StudyArea, general_science_source, study_membership
from ..services.public_catalog_cache import public_catalog
from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from psycopg.types.json import Jsonb
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header

from ..db import cursor
from ..deps import current_user
from ..schemas import (
    AnswerResult,
    AnswerSubmission,
    Appearance,
    QuestionDetail,
    QuestionListItem,
    QuestionPaperPage,
    QuestionPage,
    TaxonomyFacet,
)
from ..source_files import figure_image_url, source_pdf_url
from ..services.bank_review import protect_answer
from ..services.bank_review import snapshot as review_snapshot
from ..services.answer_comparison import published_comparison

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Three pools, and the difference matters:
#   all      — every live question, including questions without an answer.
#   scorable — official/key answers only, 12,319 rows at the 2026-10-19 sync.
#   practice — any answer passing the safety filters, 66,464 rows at that sync;
#              inferred answers are visibly unverified.
# See docs/DECISIONS.md #3.


# Columns every question response is built from. Note the absence of
# answer_text: see schemas.py.
_COLS = f"""
    v.id, type, question, direction, question_markup, options_markup, passage,
    options, subject, topic, difficulty,
    qc.subject_id AS taxonomy_subject_id, qc.subject_label AS taxonomy_subject,
    qc.topic_id AS taxonomy_topic_id, qc.topic_label AS taxonomy_topic,
    qc.subtopic_id AS taxonomy_subtopic_id, qc.subtopic_label AS taxonomy_subtopic,
    qc.review_status AS classification_status,
    answer_source, (v.status='held') AS held,
    {answer_status_sql()} AS answer_status,
    (v.answer_source='derived' AND {reviewed_answer_sql()}) AS reviewed_derived,
    (answer_source IN ('official','key')) AS verified,
    source_defect, key_disputed, dispute_note, v.times_asked, first_year, last_year
"""


@router.get("", response_model=QuestionPage)
async def list_questions(
    pool: Literal["all", "scorable", "practice"] = "all",
    answer_status: Literal["official", "verified", "needs-review", "unsolved", "written"] | None = None,
    q: str | None = Query(None, min_length=2, max_length=120),
    year_from: int | None = Query(None, ge=1900, le=2100),
    year_to: int | None = Query(None, ge=1900, le=2100),
    source: Annotated[list[str] | None, Query()] = None,
    subject_id: str | None = Query(None, min_length=2, max_length=100),
    topic_id: str | None = Query(None, min_length=2, max_length=160),
    study_area: StudyArea | None = None,
    shelf_id: str | None = Query(None, min_length=2, max_length=100),
    subtopic_id: str | None = Query(None, min_length=2, max_length=160),
    collection_id: str | None = Query(None, min_length=2, max_length=80),
    section_path: str | None = Query(None, min_length=2, max_length=160),
    paper_id: str | None = Query(None, min_length=1, max_length=500),
    essay_kind: Literal["essay", "letter", "precis", "comprehension"] | None = None,
    study_status: Literal["all", "unseen", "answered", "wrong"] = "all",
    repeats_only: bool = False,
    origin: Literal["paper", "community", "all"] = "paper",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(current_user),
    exam_scope: ExamScope = DEFAULT_SCOPE) -> QuestionPage:
    view = pool_view(pool, exam_scope)
    where: list[str] = []
    params: dict[str, object] = {}
    if exam_scope != 'all' and (collection_id or paper_id):
        # The candidate set is small. Probe its source scope by canonical ID
        # instead of DISTINCT-ing every appearance in the launch archive.
        view = pool_view(pool, 'all')
        where.append("""EXISTS (SELECT 1 FROM appearances qa JOIN papers qp ON qp.id=qa.paper_id
            WHERE qa.canonical_id=v.id AND qp.exam_scope_id='mizoram-recruitment' OFFSET 0)""")

    if origin != "all":
        where.append("EXISTS (SELECT 1 FROM appearances oa JOIN papers op ON op.id=oa.paper_id WHERE oa.canonical_id=v.id AND oa.is_primary AND ((op.exam_type='Community')=%(community)s)" + (" OFFSET 0" if collection_id or paper_id else "") + ")")
        params["community"] = origin == "community"

    if source:
        # Whitelisted against the enum rather than interpolated: this value
        # reaches a query, and the CHECK constraint is not a sanitiser.
        allowed = {"official", "key", "derived", "inferred", "none"}
        chosen = [s for s in source if s in allowed]
        if not chosen:
            raise HTTPException(422, "no recognised answer_source values")
        where.append("answer_source = ANY(%(source)s)")
        params["source"] = chosen
    if answer_status:
        where.append(f"({answer_status_sql()})=%(answer_status)s")
        params["answer_status"] = answer_status
    if repeats_only:
        where.append("times_asked >= 2")

    path_table = "question_classifications" if study_area else "v_question_paths"
    primary_path = " AND x.review_status='approved' AND x.is_primary" if study_area else ""
    # Only approved taxonomy claims feed learner filters. Pending proposals
    # remain stored with provenance but are never presented as established.
    clerical_science = collection_id in (*CLERICAL_EXAMS,'combined-prelims') and not study_area
    if clerical_science and (subject_id or topic_id or subtopic_id):
        # Match one projected path so the map and results share exact semantics.
        path_filters = ["x.question_id=v.id", "x.review_status='approved'"]
        for name, value in [('subject_id', subject_id), ('topic_id', topic_id), ('subtopic_id', subtopic_id)]:
            if value:
                path_filters.append(f"x.{name}=%({name})s")
                params[name] = value
        where.append(f"EXISTS (SELECT 1 FROM ({path_projection(clerical_science=True)}) x WHERE {' AND '.join(path_filters)})")
    elif subject_id == 'gk-gs':
        if study_area:
            general_membership, general_params = study_membership('gk-gs', collection_id, exam_scope)
            where.append(f"v.id IN ({general_membership})")
            params.update(general_params)
        else:
            where.append("EXISTS (SELECT 1 FROM v_question_paths x WHERE x.question_id=v.id AND x.subject_id IN ('general-knowledge','general-studies'))")
    elif subject_id:
        where.append(f"EXISTS (SELECT 1 FROM {path_table} x WHERE x.question_id=v.id AND x.subject_id=%(subject_id)s{primary_path})")
        params["subject_id"] = subject_id
    if topic_id and not clerical_science:
        topic_column = topic_expression("x", include_science=bool(study_area)) if topic_id.startswith("gk-gs:") else "x.topic_id"
        where.append(f"EXISTS (SELECT 1 FROM {path_table} x WHERE x.question_id=v.id AND {topic_column}=%(topic_id)s{primary_path})")
        params["topic_id"] = topic_id
    if subtopic_id and not clerical_science:
        where.append(f"EXISTS (SELECT 1 FROM {path_table} x WHERE x.question_id=v.id AND x.subtopic_id=%(subtopic_id)s{primary_path})")
        params['subtopic_id']=subtopic_id
    if shelf_id:
        where.append("v.id IN (SELECT x.question_id FROM library_shelves sh JOIN v_question_paths x ON (x.subject_id=ANY(sh.match_ids) OR x.topic_id=ANY(sh.match_ids) OR x.subtopic_id=ANY(sh.match_ids)) WHERE sh.active AND sh.id=%(shelf_id)s)")
        params['shelf_id']=shelf_id
    if study_area:
        membership, area_params = study_membership(study_area, collection_id, exam_scope)
        where.append(f"v.id IN ({membership})")
        params.update(area_params)
    elif collection_id == 'group-b':
        raise HTTPException(422, 'Choose a Group B learning area')
    if collection_id and collection_id != 'group-b' and not study_area:
        # Resolve the small collection membership once. A correlated EXISTS
        # here made PostgreSQL probe sections and papers for every one of the
        # 80k bank questions, even when this collection contains only 520.
        where.append(f"""v.id IN (
            WITH live_sections AS MATERIALIZED (
                SELECT cs.* FROM collection_sections cs JOIN collections cc
                  ON cc.id=cs.collection_id AND cc.live_version=cs.version
                WHERE cs.collection_id=%(collection_id)s AND cc.visibility='public'
                  AND {scope_condition('cc', exam_scope)}
            ), section_papers AS MATERIALIZED (
                SELECT cs.*,jsonb_array_elements_text(cs.query->'paper_ids') AS paper_id
                FROM live_sections cs WHERE cs.query ? 'paper_ids'
            ), section_candidates AS (
                SELECT ca.canonical_id,cs.query FROM section_papers cs
                JOIN appearances ca ON ca.paper_id=cs.paper_id
                UNION ALL
                SELECT ca.canonical_id,cs.query FROM live_sections cs
                CROSS JOIN appearances ca WHERE NOT (cs.query ? 'paper_ids')
            )
            SELECT ca.canonical_id FROM section_candidates ca
            WHERE (ca.query->>'subject_id' IS NULL OR EXISTS (
                SELECT 1 FROM v_question_paths cqc WHERE cqc.question_id=ca.canonical_id
                  AND cqc.review_status='approved' AND cqc.subject_id=ca.query->>'subject_id'))
              AND (ca.query->>'topic_id' IS NULL OR EXISTS (
                SELECT 1 FROM v_question_paths cqt WHERE cqt.question_id=ca.canonical_id
                  AND cqt.review_status='approved' AND cqt.topic_id=ca.query->>'topic_id'))
            UNION SELECT ea.canonical_id FROM appearances ea JOIN collection_papers ep
              ON ep.paper_id=ea.paper_id JOIN collections ec
              ON ec.id=ep.collection_id AND ec.live_version=ep.version
            WHERE ec.visibility='public' AND {scope_condition('ec', exam_scope)}
              AND ep.collection_id=%(collection_id)s)""")
        params["collection_id"] = collection_id
    if collection_id=='combined-prelims' and section_path=='papers':
        section_path=None  # Historical all-paper bookmarks predate the GS/Aptitude split.
    if section_path:
        where.append("""EXISTS (
            SELECT 1 FROM collection_sections ss
            JOIN collections sc ON sc.id=ss.collection_id AND sc.live_version=ss.version
            WHERE ss.collection_id=%(section_collection)s AND ss.path=%(section_path)s
              AND v.id <> ALL(ss.excludes)
              AND (v.id=ANY(ss.pins) OR (
                (NOT (ss.query ? 'paper_ids') OR EXISTS (
                  SELECT 1 FROM appearances sa WHERE sa.canonical_id=v.id
                    AND sa.paper_id IN (SELECT jsonb_array_elements_text(ss.query->'paper_ids'))))
                AND (ss.query->>'subject_id' IS NULL OR EXISTS (
                  SELECT 1 FROM v_question_paths scq WHERE scq.question_id=v.id
                    AND scq.review_status='approved' AND scq.subject_id=ss.query->>'subject_id'))
                AND (ss.query->>'topic_id' IS NULL OR EXISTS (
                  SELECT 1 FROM v_question_paths stq WHERE stq.question_id=v.id
                    AND stq.review_status='approved' AND stq.topic_id=ss.query->>'topic_id'))
              ))
        )""")
        params["section_collection"] = collection_id
        params["section_path"] = section_path
    if paper_id:
        where.append(f"""EXISTS(SELECT 1 FROM papers sp WHERE sp.id=%(paper_id)s AND {scope_condition('sp', exam_scope)})""")
        if collection_id and collection_id != 'group-b':
            where.append(f"""EXISTS (SELECT 1 FROM appearances pa
                JOIN collection_papers cp ON cp.paper_id=pa.paper_id
                JOIN collections pc ON pc.id=cp.collection_id AND pc.live_version=cp.version
                WHERE pa.canonical_id=v.id AND pa.paper_id=%(paper_id)s
                  AND cp.collection_id=%(collection_id)s AND pc.visibility='public' AND {scope_condition('pc', exam_scope)})""")
        else:
            where.append("EXISTS (SELECT 1 FROM appearances pa WHERE pa.canonical_id=v.id AND pa.paper_id=%(paper_id)s)")
        params["paper_id"] = paper_id
    if essay_kind:
        where.append("EXISTS (SELECT 1 FROM appearances ea WHERE ea.canonical_id=v.id AND ea.essay_kind=%(essay_kind)s)")
        params["essay_kind"] = essay_kind

    if study_status != "all":
        attempt_exists = """EXISTS (SELECT 1 FROM attempts sa WHERE sa.user_id=%(user_id)s
                         AND sa.canonical_id=v.id AND sa.collection_id IS NOT DISTINCT FROM %(study_collection)s)"""
        if study_area:
            attempt_exists="EXISTS (SELECT 1 FROM attempts sa WHERE sa.user_id=%(user_id)s AND sa.canonical_id=v.id AND sa.collection_id=ANY(%(gb_collections)s))"
        elif shelf_id and not collection_id:
            attempt_exists="EXISTS (SELECT 1 FROM attempts sa WHERE sa.user_id=%(user_id)s AND sa.canonical_id=v.id)"
        params["user_id"] = user_id
        params["study_collection"] = collection_id
        if study_status == "unseen":
            where.append(f"NOT {attempt_exists}")
        elif study_status == "answered":
            where.append(attempt_exists)
        else:
            scope="" if shelf_id and not collection_id else " AND sa.collection_id IS NOT DISTINCT FROM %(study_collection)s"
            inner_scope="" if shelf_id and not collection_id else " AND sa2.collection_id IS NOT DISTINCT FROM sa.collection_id"
            if study_area:
                scope=" AND sa.collection_id=ANY(%(gb_collections)s)"
                inner_scope=" AND sa2.collection_id=ANY(%(gb_collections)s)"
            where.append("EXISTS (SELECT 1 FROM attempts sa WHERE sa.user_id=%(user_id)s AND sa.canonical_id=v.id"+scope+" AND sa.id=(SELECT MAX(sa2.id) FROM attempts sa2 WHERE sa2.user_id=sa.user_id AND sa2.canonical_id=sa.canonical_id"+inner_scope+") AND NOT sa.correct)")

    if q:
        # Uses the GIN index on the generated tsvector; ~0.1-0.5 ms at 77k rows.
        where.append("search @@ plainto_tsquery('english', %(q)s)")
        params["q"] = q
    if shelf_id and (year_from is not None or year_to is not None):
        where.append("EXISTS (SELECT 1 FROM appearances ya JOIN papers yp ON yp.id=ya.paper_id WHERE ya.canonical_id=v.id AND yp.year BETWEEN %(year_from)s AND %(year_to)s)")
        params['year_from']=year_from or 1900
        params['year_to']=year_to or 2100
    else:
        if year_from is not None:
            where.append("last_year >= %(year_from)s")
            params["year_from"] = year_from
        if year_to is not None:
            where.append("first_year <= %(year_to)s")
            params["year_to"] = year_to

    source_area = ""
    if study_area:
        source_area = """AND a.paper_id IN (SELECT gp.paper_id FROM collection_papers gp
            JOIN collections gr ON gr.id=gp.collection_id AND gr.live_version=gp.version
            WHERE gp.collection_id=ANY(%(gb_collections)s) AND gp.allow_browse AND gr.visibility='public')"""
        if study_area == 'technical':
            source_area += " AND a.paper_id=ANY(%(gb_technical_papers)s)"
        elif study_area in ('common', 'gk-gs'):
            source_area += f" AND (qc.subject_id<>'science' OR {general_science_source('a')})"
        if paper_id:
            source_area += " AND a.paper_id=%(paper_id)s"
    elif collection_id:
        # A shared canonical question must show a source from the active exam.
        source_area = """AND (EXISTS (
            SELECT 1 FROM collection_papers cp JOIN collections c
              ON c.id=cp.collection_id AND c.live_version=cp.version
            WHERE cp.collection_id=%(collection_id)s AND c.visibility='public'
              AND cp.paper_id=a.paper_id
        ) OR EXISTS (
            SELECT 1 FROM collection_sections cs JOIN collections c
              ON c.id=cs.collection_id AND c.live_version=cs.version
            WHERE cs.collection_id=%(collection_id)s AND c.visibility='public'
              AND (NOT (cs.query ? 'paper_ids') OR
                a.paper_id IN (SELECT jsonb_array_elements_text(cs.query->'paper_ids')))
        ))"""
        if paper_id:
            source_area += " AND a.paper_id=%(paper_id)s"
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    async with cursor() as cur:
        if study_area:
            await cur.execute("SET LOCAL jit=off")
        source_sql = f"FROM {view} v"
        await cur.execute(f"SELECT COUNT(*) AS n {source_sql} {clause}", params)
        row = await cur.fetchone()
        total = row["n"] if row else 0

        # Deliberately NOT `ORDER BY random()` — 19.8 ms vs 0.67 ms measured,
        # and it degrades as the bank grows. times_asked DESC is indexed and
        # puts genuinely repeated questions first, which is what a learner
        # browsing the bank wants anyway.
        await cur.execute(
            f"""WITH selected AS MATERIALIZED (
                    SELECT v.id,v.times_asked FROM {view} v {clause}
                    ORDER BY v.times_asked DESC,v.id
                    LIMIT %(limit)s OFFSET %(offset)s
                )
                SELECT {_COLS},src.figure_image,COALESCE(src.has_diagram,false) AS has_diagram,
                       src.paper_id AS source_paper_id,src.year AS source_year,
                       src.exam AS source_exam,src.paper AS source_paper,
                       src.qnum AS source_qnum,src.page AS source_page,
                       src.series AS source_series,src.source_file,src.pdf_url
                  FROM selected JOIN v_all_questions v ON v.id=selected.id
                  LEFT JOIN question_classifications qc ON qc.question_id=v.id AND qc.review_status='approved'
                LEFT JOIN LATERAL (
                    SELECT a.figure_image,a.has_diagram,a.paper_id,a.qnum,a.page,a.series,
                           p.year,p.exam_name AS exam,p.paper_number AS paper,p.source_file,p.pdf_url
                      FROM appearances a JOIN papers p ON p.id=a.paper_id
                     WHERE a.canonical_id=v.id AND {scope_condition('p', exam_scope)} {source_area}
                     ORDER BY (a.paper_id=%(source_paper_id)s) DESC NULLS LAST,
                              (p.year BETWEEN %(source_year_from)s AND %(source_year_to)s) DESC NULLS LAST,
                              (a.figure_image IS NOT NULL) DESC,p.year DESC NULLS LAST,
                              a.page NULLS LAST LIMIT 1
                ) src ON TRUE
                ORDER BY selected.times_asked DESC, selected.id""",
            {**params, "source_paper_id": paper_id, "source_year_from": (year_from or 1900) if shelf_id and (year_from is not None or year_to is not None) else None, "source_year_to": (year_to or 2100) if shelf_id and (year_from is not None or year_to is not None) else None, "limit": limit, "offset": offset},
        )
        items = []
        selected_rows=await cur.fetchall()
        await cur.execute("SELECT * FROM v_question_paths WHERE question_id=ANY(%s) ORDER BY is_primary DESC,subject_label,topic_label",([r['id'] for r in selected_rows],))
        paths={}
        for path in await cur.fetchall():paths.setdefault(path['question_id'],[]).append(path)
        source_identities = await identities_for(cur, [r["source_paper_id"] for r in selected_rows if r.get("source_paper_id")])
        for row in selected_rows:
            row['taxonomy_paths']=paths.get(row['id'],[])
            source = None
            if row.get("source_paper_id"):
                source = Appearance(
                    paper_id=row["source_paper_id"], year=row.get("source_year"),
                    exam=row.get("source_exam"), paper=row.get("source_paper"),
                    qnum=row.get("source_qnum"), page=row.get("source_page"),
                    series=row.get("source_series"),
                    source_pdf_url=source_pdf_url(row.get("source_file"), row.get("pdf_url")),
                )
                source = source.model_copy(update=display_identity(source.paper_id, source.qnum, source_identities))
            items.append(QuestionListItem(
                **{**row, "figure_image_url": figure_image_url(row.get("figure_image")),
                   "source_appearance": source}
            ))

    return QuestionPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/taxonomy", response_model=list[TaxonomyFacet])
async def taxonomy_facets(
    pool: Literal["all", "scorable", "practice"] = "all",
    exam_scope: ExamScope = DEFAULT_SCOPE, learning: bool = False) -> list[TaxonomyFacet]:
    """Distinct approved v2 subject/topic values with counts in this pool."""
    return await public_catalog(('taxonomy',pool,exam_scope,learning),lambda:_taxonomy_facets(pool,exam_scope,learning))


async def _taxonomy_facets(pool,exam_scope,learning=False):
    view = pool_view(pool, exam_scope)
    async with cursor() as cur:
        await cur.execute(
            f"""WITH eligible AS MATERIALIZED (
                 SELECT p.* FROM ({path_projection() if learning else "SELECT * FROM v_question_paths"}) p JOIN {view} v ON v.id=p.question_id
               ), totals AS (
                 SELECT subject_id,count(DISTINCT question_id)::int AS subject_questions FROM eligible GROUP BY subject_id
               ), facets AS (
                 SELECT subject_id,MIN(subject_label) AS subject,topic_id,MIN(topic_label) AS topic,count(DISTINCT question_id)::int AS questions
                 FROM eligible GROUP BY subject_id,topic_id
               ) SELECT f.*,t.subject_questions FROM facets f JOIN totals t USING(subject_id) ORDER BY f.subject,f.topic NULLS FIRST"""
        )
        return [TaxonomyFacet(**r) for r in await cur.fetchall()]


@router.get("/papers", response_model=QuestionPaperPage)
async def list_question_papers(
    q: str | None = Query(None, min_length=2, max_length=120),
    subject_id: str | None = Query(None, min_length=2, max_length=100),
    year_from: int | None = Query(None, ge=1900, le=2100),
    year_to: int | None = Query(None, ge=1900, le=2100),
    exam_type: Literal["Direct", "Direct_NG", "LDE", "Departmental"] | None = None,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    exam_scope: ExamScope = DEFAULT_SCOPE) -> QuestionPaperPage:
    """Paper-wise directory for General English, including complete source papers.

    Title matching captures English papers before tagging is complete; approved
    English classifications also catch papers whose filenames omit that label.
    Counts are based on printed appearances, while scoring eligibility comes
    from the canonical official-key view.
    """
    where = ["""(
        COALESCE(p.exam_name, '') ILIKE '%%english%%'
        OR COALESCE(p.source_file, '') ILIKE '%%english%%'
        OR COALESCE(p.paper_subject, '') ILIKE '%%english%%'
        OR EXISTS (
            SELECT 1 FROM appearances ea
            JOIN v_question_paths eqc ON eqc.question_id=ea.canonical_id
            WHERE ea.paper_id=p.id AND eqc.review_status='approved'
              AND eqc.subject_id='english'
        )
    )""" if not subject_id else """EXISTS (
        SELECT 1 FROM appearances sa JOIN v_question_paths sqc
          ON sqc.question_id=sa.canonical_id AND sqc.review_status='approved'
        WHERE sa.paper_id=p.id AND sqc.subject_id=%(subject_id)s
    )"""]
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if subject_id:
        params["subject_id"] = subject_id
    if q:
        where.append("(COALESCE(p.exam_name,'') ILIKE %(needle)s OR COALESCE(p.source_file,'') ILIKE %(needle)s OR COALESCE(p.post,'') ILIKE %(needle)s)")
        params["needle"] = f"%{q}%"
    if year_from is not None:
        where.append("p.year >= %(year_from)s")
        params["year_from"] = year_from
    if year_to is not None:
        where.append("p.year <= %(year_to)s")
        params["year_to"] = year_to
    if exam_type:
        where.append("p.exam_type = %(exam_type)s")
        params["exam_type"] = exam_type
    where.append(f"""{scope_condition('p', exam_scope)}""")
    clause = " AND ".join(where)

    async with cursor() as cur:
        await cur.execute(
            f"""SELECT p.id, p.exam_name AS exam, p.exam_type, p.year, p.month,
                       p.paper_number, p.source_file, p.pdf_url,
                       COUNT(DISTINCT a.id)::int AS questions,
                       (COUNT(DISTINCT a.id) FILTER (WHERE cq.answer_text IS NOT NULL))::int AS answered,
                       (COUNT(DISTINCT a.id) FILTER (WHERE sc.id IS NOT NULL))::int AS scorable,
                       COUNT(*) OVER()::int AS total
                  FROM papers p
                  JOIN appearances a ON a.paper_id=p.id
                  LEFT JOIN canonical_questions cq ON cq.id=a.canonical_id
                  LEFT JOIN {pool_view('scorable', exam_scope)} sc ON sc.id=a.canonical_id
                 WHERE {clause}
                 GROUP BY p.id
                HAVING COUNT(DISTINCT a.id) > 0
                 ORDER BY p.year DESC NULLS LAST, p.exam_name NULLS LAST,
                          p.paper_number NULLS LAST, p.source_file
                 LIMIT %(limit)s OFFSET %(offset)s""",
            params,
        )
        rows = await cur.fetchall()
    total = rows[0]["total"] if rows else 0
    items = []
    for row in rows:
        item = {k: v for k, v in row.items() if k not in ("total", "pdf_url")}
        item["source_pdf_url"] = source_pdf_url(row.get("source_file"), row.get("pdf_url"))
        items.append(item)
    return QuestionPaperPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{question_id}/answer-comparison")
async def answer_comparison(question_id: str, response: Response,
    user_id: Annotated[str, Depends(current_user)],
    paper_id: str | None = Query(None, max_length=500),
    exam_scope: ExamScope = DEFAULT_SCOPE):
    """Explicit answer reveal, protected against active mocks, games and cups."""
    response.headers['Cache-Control'] = 'private, no-store'
    async with cursor() as cur:
        await protect_answer(cur, user_id, question_id)
        await cur.execute(f'''SELECT a.id,q.status,q.key_disputed,q.dispute_note,q.source_defect
          FROM canonical_questions q JOIN appearances a ON a.canonical_id=q.id
          JOIN papers p ON p.id=a.paper_id WHERE q.id=%s AND q.status<>'merged'
          AND (%s::text IS NULL OR a.paper_id=%s) AND {scope_condition('p', exam_scope)}
          ORDER BY a.is_primary DESC,a.id LIMIT 1''', (question_id,paper_id,paper_id))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, 'Question source not found in this exam scope')
        snap = await review_snapshot(cur, question_id, row['id'])
        await cur.execute('''SELECT p.id,p.state,p.manifest,p.finished_at
          FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id
          WHERE c.canonical_id=%s AND p.state='applied' AND c.kind IN ('answer','explanation')
          ORDER BY p.finished_at DESC,p.id DESC LIMIT 200''', (question_id,))
        publications = await cur.fetchall()
        refs = list({e.get('document_id') for p in publications
            for e in p['manifest'].get('payload',{}).get('evidence',[])
            if e.get('kind')=='official-key' and e.get('document_id')})
        await cur.execute('SELECT id,paper_id,title,sha256,key_status,kind FROM review_documents WHERE id=ANY(%s)', (refs,))
        documents = {d['id']: d for d in await cur.fetchall()}
        result = published_comparison(snap['record'], publications, documents,
            held=row['status']=='held' or row['key_disputed'] or row['source_defect'] in ('duplicate-options','unresolved-source'),
            review_note=row['dispute_note'])
        # Older imports can carry an official answer without a registered key
        # publication. Preserve that label without inventing a key citation.
        current = snap['record']
        if result['official'] is None and current.get('answerSource') in ('official','key'):
            ai=current.get('answerIndex');opts=current.get('options')or[]
            if type(ai)is int and 0<=ai<len(opts):
                result['official']={'answer_index':ai,'answer_text':opts[ai],
                    'explanation':current.get('explanation')or'', 'publication_id':None,
                    'published_at':None,'document':None,'imported':True}
                if result['solution']:
                    result['relation']='agree' if opts[ai]==result['solution']['answer_text'] else 'disagree'
    return result


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(question_id: str, exam_scope: ExamScope = DEFAULT_SCOPE) -> QuestionDetail:
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT q.id,q.type,q.question,q.direction,q.question_markup,q.options_markup,
                       q.passage,q.options,q.subject,q.topic,q.difficulty,
                       qc.subject_id AS taxonomy_subject_id,qc.subject_label AS taxonomy_subject,
                       qc.topic_id AS taxonomy_topic_id,qc.topic_label AS taxonomy_topic,
                       qc.subtopic_id AS taxonomy_subtopic_id,qc.subtopic_label AS taxonomy_subtopic,
                       qc.review_status AS classification_status,
                       q.answer_source,(q.status='held') AS held,(q.answer_source IN ('official','key')) AS verified,
                       (q.answer_source='derived' AND EXISTS(SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=q.id)) AS reviewed_derived,
                       q.source_defect,q.key_disputed,q.dispute_note,
                       (SELECT bs.answer_status FROM v_bank_answer_status bs WHERE bs.id=q.id) AS answer_status,
                       q.times_asked,q.first_year,q.last_year
                  FROM canonical_questions q
                  LEFT JOIN question_classifications qc
                    ON qc.question_id=q.id AND qc.review_status='approved'
                 WHERE q.id=%s AND q.status <> 'merged' AND {question_scope('q', exam_scope)}""",
            (question_id,),
        )
        row = await cur.fetchone()
        if row is None:
            raise HTTPException(404, "question not found")

        await cur.execute(
            f"""SELECT a.paper_id, p.year, p.exam_name AS exam, p.paper_number AS paper,
                      a.qnum, a.page, a.series, a.direction, a.question_markup,a.options_markup,
                      a.figure_image,
                      p.source_file, p.pdf_url
                 FROM appearances a JOIN papers p ON p.id = a.paper_id
                WHERE a.canonical_id = %s AND {scope_condition('p', exam_scope)}
                ORDER BY p.year DESC NULLS LAST""",
            (question_id,),
        )
        appearance_rows = await cur.fetchall()
        source_identities = await identities_for(cur, [r["paper_id"] for r in appearance_rows])
        appearances = [Appearance(
            **{**r, "source_pdf_url": source_pdf_url(r.get("source_file"), r.get("pdf_url")),
               "figure_image_url": figure_image_url(r.get("figure_image"))}
        ).model_copy(update=display_identity(r["paper_id"], r.get("qnum"), source_identities)) for r in appearance_rows]

    return QuestionDetail(**row, appearances=appearances)


@router.post("/{question_id}/answer", response_model=AnswerResult)
async def answer_question(
    question_id: str,
    body: AnswerSubmission,
    user_id: Annotated[str, Depends(current_user)],
    idempotency_key:Annotated[str|None,Header(min_length=16,max_length=100)]=None,
    exam_scope: ExamScope = DEFAULT_SCOPE) -> AnswerResult:
    """Grade an answer, record the attempt, and reveal the key.

    Grading compares option TEXT, not index: the canonical row stores the
    answer as text precisely so a reprint with shuffled options cannot
    inherit the wrong letter.
    """
    if body.section_path and not body.collection_id:
        raise HTTPException(422, "section_path requires collection_id")
    request_hash=hashlib.sha256(json.dumps({'question':question_id,'scope':exam_scope,**body.model_dump()},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    async def replay(cur):
        await cur.execute('SELECT request_hash,response FROM practice_request_receipts WHERE user_id=%s AND request_key=%s',(user_id,idempotency_key))
        prior=await cur.fetchone()
        if prior:
            if prior['request_hash']!=request_hash:raise HTTPException(409,'This answer request was already used for a different answer')
            return AnswerResult(**prior['response'])
    if idempotency_key:
        async with cursor() as cur:
            prior=await replay(cur)
            if prior:return prior
    resolved_section = None if body.collection_id=='combined-prelims' and body.section_path=='papers' else body.section_path
    async with cursor() as cur:
        await protect_answer(cur,user_id,question_id)
        if body.collection_id:
            if body.paper_id:
                await cur.execute(
                    f"""SELECT cp.section_path FROM collection_papers cp
                         JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                        WHERE cp.collection_id=%s AND cp.paper_id=%s AND c.visibility='public' AND {scope_condition('c', exam_scope)}
                          AND EXISTS (SELECT 1 FROM appearances a WHERE a.paper_id=cp.paper_id
                                      AND a.canonical_id=%s)""",
                    (body.collection_id, body.paper_id, question_id),
                )
                source = await cur.fetchone()
                if source is None:
                    raise HTTPException(422, "question source does not belong to this exam")
                if resolved_section and source["section_path"] and resolved_section != source["section_path"]:
                    raise HTTPException(422, "paper does not belong to this module section")
                resolved_section = resolved_section or source["section_path"]
            elif resolved_section:
                await cur.execute(
                    f"""SELECT 1 FROM collection_sections cs
                         JOIN collections c ON c.id=cs.collection_id AND c.live_version=cs.version
                         JOIN canonical_questions v ON v.id=%s
                        WHERE cs.collection_id=%s AND cs.path=%s AND c.visibility='public' AND {scope_condition('c', exam_scope)}
                          AND v.id <> ALL(cs.excludes)
                          AND (v.id=ANY(cs.pins) OR (
                            (NOT (cs.query ? 'paper_ids') OR EXISTS (
                              SELECT 1 FROM appearances a WHERE a.canonical_id=%s
                                AND a.paper_id IN (SELECT jsonb_array_elements_text(cs.query->'paper_ids'))))
                            AND (cs.query->>'subject_id' IS NULL OR EXISTS (
                              SELECT 1 FROM question_classifications qc WHERE qc.question_id=%s
                                AND qc.review_status='approved' AND qc.subject_id=cs.query->>'subject_id'))
                            AND (cs.query->>'topic_id' IS NULL OR EXISTS (
                              SELECT 1 FROM question_classifications qt WHERE qt.question_id=%s
                                AND qt.review_status='approved' AND qt.topic_id=cs.query->>'topic_id'))
                          ))""",
                    (question_id,body.collection_id,resolved_section,question_id,question_id,question_id),
                )
                if await cur.fetchone() is None:
                    raise HTTPException(422, "question is not in this module section")
            else:
                await cur.execute(
                    f"""SELECT 1 FROM collections WHERE id=%s AND visibility='public' AND {scope_condition('collections', exam_scope)}""",
                    (body.collection_id,),
                )
                if await cur.fetchone() is None:
                    raise HTTPException(422, "question source does not belong to this exam")
        await cur.execute(
            f"""SELECT q.question,q.options,q.answer_text,q.answer_source,q.explanation,q.status,q.source_defect,
                   a.id AS appearance_id,COALESCE(a.direction,q.direction) AS direction,
                   COALESCE(a.passage,q.passage) AS passage,COALESCE(a.question_markup,q.question_markup) AS question_markup,
                   COALESCE(a.options_markup,q.options_markup) AS options_markup,a.has_diagram,a.figure_image
                 FROM canonical_questions q LEFT JOIN LATERAL (SELECT x.* FROM appearances x WHERE x.canonical_id=q.id
                    AND EXISTS(SELECT 1 FROM papers sp WHERE sp.id=x.paper_id AND {scope_condition('sp', exam_scope)})
                    AND (%s::text IS NULL OR x.paper_id=%s) ORDER BY x.is_primary DESC,x.id LIMIT 1) a ON TRUE
                 WHERE q.id = %s AND {question_scope('q', exam_scope)}""",
            (body.paper_id,body.paper_id,question_id),
        )
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(404, "question not found")
    if body.paper_id and row['appearance_id'] is None:
        raise HTTPException(422, "This question source is not available in the selected exam scope")
    if row["status"] != "live" or row["answer_text"] is None or row["source_defect"] in {"duplicate-options","unresolved-source"}:
        # Held, withdrawn, or simply unanswered: 17,696 rows have no key at all.
        raise HTTPException(409, "this question has no usable answer")

    options: list[str] = row["options"]
    if body.chosen_index >= len(options):
        raise HTTPException(422, "chosen_index out of range")

    answer_text = row["answer_text"]
    try:
        answer_index = options.index(answer_text)
    except ValueError:
        # answer_text not among options. The schema CHECK makes this
        # impossible to store, so reaching here means data was changed
        # out from under the constraint.
        raise HTTPException(500, "answer is not one of the options") from None

    chosen_text = options[body.chosen_index]
    correct = chosen_text == answer_text

    # Store the TEXT the learner chose, not its index. When a key is later
    # corrected, attempts can be re-scored against the new answer; an index
    # would be meaningless if the options were ever re-ordered.
    async with cursor() as cur:
        if idempotency_key:
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('answer-request:'+user_id+':'+idempotency_key,))
            prior=await replay(cur)
            if prior:return prior
        # Free accounts receive 50 bank practice answers per calendar day.
        # A transaction lock keeps simultaneous tabs from spending the last
        # remaining answer twice; mock answers are handled by the mock runner.
        if body.context == "practice":
            await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("practice:" + user_id,))
            await cur.execute("SELECT account_has_pro(id) AS pro FROM users WHERE id=%s", (user_id,))
            entitlement=await cur.fetchone()
            if not entitlement or not entitlement["pro"]:
                await cur.execute("SELECT count(*)::int AS n FROM attempts WHERE user_id=%s AND context='practice' AND at>=date_trunc('day',now())", (user_id,))
                if (await cur.fetchone())["n"] >= 50:
                    raise HTTPException(429,"Daily free practice limit reached. Join Pro for unlimited practice.")
        await cur.execute(
            """INSERT INTO attempts (user_id, canonical_id, correct, chosen_text, context,
                                      collection_id,paper_id,section_path,scoring_snapshot)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, question_id, correct, chosen_text, body.context,
             body.collection_id, body.paper_id,resolved_section,Jsonb({k:row[k] for k in ('question','options','answer_text','answer_source','appearance_id','direction','passage','question_markup','options_markup','has_diagram','figure_image')})),
        )

        attempt=(await cur.fetchone())['id']
        from ..services.learning_rewards import attempt_reward
        reward=await attempt_reward(cur,user_id,question_id,attempt,correct,row['answer_source'],body.context)

        result=AnswerResult(
            reward=reward,correct=correct,answer_index=answer_index,answer_text=answer_text,
            answer_source=row['answer_source'],verified=row['answer_source'] in ('official','key'),
            explanation=row['explanation'] or None)
        if idempotency_key:
            await cur.execute('INSERT INTO practice_request_receipts(user_id,request_key,request_hash,attempt_id,response) VALUES(%s,%s,%s,%s,%s)',(user_id,idempotency_key,request_hash,attempt,Jsonb(result.model_dump())))
    return result
