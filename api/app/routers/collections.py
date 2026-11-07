from ..services.source_identity import identities_for, display_identity
from ..services.question_readiness import answer_status_sql
from ..services.learning_taxonomy import CLERICAL_EXAMS, path_projection
from ..services.group_b_study import StudyArea, GROUP_B_COLLECTIONS, PAPER_ROLES, study_membership
from ..services.public_catalog_cache import public_catalog
from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from fastapi import APIRouter, HTTPException, Query

from ..db import cursor
from ..schemas import (
    CollectionDetail, CollectionPaper, CollectionSection, CollectionSummary,
    PaperQuestion, PaperQuestionPage,
)
from ..source_files import figure_image_url, source_pdf_url

router = APIRouter(prefix="/api/collections", tags=["collections"])

# Resolve every live section in one grouped query. The previous list endpoint
# ran one count scan for every question pool in every section (41 sections
# meant 82 repeated scans). These branches let paper-backed tracks use the
# paper index and taxonomy-backed tracks use the approved-subject index.
_MATCHED_QUERY = """
WITH live_sections AS (
    SELECT s.collection_id,s.version,s.path,s.query,s.pins,s.excludes
      FROM collection_sections s
      JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
     WHERE c.visibility='public' AND {collection_scope} {collection_filter}
), matched AS (
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           (v.answer_text IS NOT NULL
            AND v.answer_source IN ('official','key')
            AND NOT v.key_disputed
            AND v.source_defect IS DISTINCT FROM 'duplicate-options') AS scorable
      FROM live_sections s
      JOIN appearances a ON s.query ? 'paper_ids'
       AND a.paper_id = ANY(ARRAY(SELECT jsonb_array_elements_text(s.query->'paper_ids')))
      JOIN {all_view} v ON v.id=a.canonical_id
     WHERE v.id <> ALL(s.excludes)
       AND (v.id=ANY(s.pins) OR (
         (s.query->>'subject_id' IS NULL AND s.query->>'topic_id' IS NULL)
         OR EXISTS (SELECT 1 FROM v_question_paths p WHERE p.question_id=v.id
           AND (s.query->>'subject_id' IS NULL OR p.subject_id=s.query->>'subject_id')
           AND (s.query->>'topic_id' IS NULL OR p.topic_id=s.query->>'topic_id'))
       ))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           (v.answer_text IS NOT NULL
            AND v.answer_source IN ('official','key')
            AND NOT v.key_disputed
            AND v.source_defect IS DISTINCT FROM 'duplicate-options') AS scorable
      FROM live_sections s
      JOIN LATERAL (
        SELECT p.question_id FROM v_question_paths p WHERE p.subject_id=s.query->>'subject_id'
          AND (s.query->>'topic_id' IS NULL OR p.topic_id=s.query->>'topic_id')
        UNION ALL
        SELECT p.question_id FROM v_question_paths p WHERE s.query->>'subject_id' IS NULL AND p.topic_id=s.query->>'topic_id'
      ) qc ON TRUE
      JOIN {all_view} v ON v.id=qc.question_id
      LEFT JOIN appearances a ON a.canonical_id=v.id
     WHERE NOT (s.query ? 'paper_ids')
       AND (s.query ? 'subject_id' OR s.query ? 'topic_id')
       AND v.id <> ALL(s.excludes)
       AND NOT (v.id=ANY(s.pins))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           (v.answer_text IS NOT NULL
            AND v.answer_source IN ('official','key')
            AND NOT v.key_disputed
            AND v.source_defect IS DISTINCT FROM 'duplicate-options') AS scorable
      FROM live_sections s
      JOIN {all_view} v ON v.id=ANY(s.pins)
      LEFT JOIN appearances a ON a.canonical_id=v.id
     WHERE v.id <> ALL(s.excludes)
)"""

_STATS_QUERY = _MATCHED_QUERY + """, section_stats AS (
    SELECT collection_id,version,path,
           COUNT(DISTINCT id)::int AS questions,
           COUNT(DISTINCT id) FILTER (WHERE scorable)::int AS scorable,
           COUNT(DISTINCT paper_id)::int AS papers
      FROM matched
     GROUP BY collection_id,version,path
)
SELECT * FROM section_stats

"""


async def _section_stats(collection_id: str | None = None, exam_scope: ExamScope = DEFAULT_SCOPE) -> dict[tuple[str, int, str], dict]:
    collection_filter = "AND c.id=%(collection_id)s" if collection_id else ""
    async with cursor() as cur:
        await cur.execute(_STATS_QUERY.format(collection_filter=collection_filter, collection_scope=scope_condition('c',exam_scope), all_view=pool_view('all',exam_scope)),
                          {"collection_id": collection_id} if collection_id else {})
        rows = await cur.fetchall()
    return {(r["collection_id"], r["version"], r["path"]): r for r in rows}


@router.get("", response_model=list[CollectionSummary])
async def list_collections(exam_scope: ExamScope = DEFAULT_SCOPE) -> list[CollectionSummary]:
    return await public_catalog(('collections',exam_scope),lambda:_list_collections(exam_scope))


async def _list_collections(exam_scope: ExamScope) -> list[CollectionSummary]:
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT c.id,c.title,c.kind,c.route,c.visibility,c.live_version,
                      COUNT(s.path)::int AS sections
                 FROM collections c
                 LEFT JOIN collection_sections s
                   ON s.collection_id=c.id AND s.version=c.live_version
                WHERE c.visibility='public' AND {scope_condition('c', exam_scope)}
                GROUP BY c.id,c.title,c.kind,c.route,c.visibility,c.position,c.live_version
                ORDER BY c.position,c.title"""
        )
        collections = await cur.fetchall()
    stats = await _section_stats(exam_scope=exam_scope)
    output = []
    # Section paths are fetched below as one cheap metadata query; counts are
    # then reduced in Python, avoiding correlated SQL subqueries.
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT s.collection_id,s.version,s.path FROM collection_sections s
                JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
                WHERE c.visibility='public' AND {scope_condition('c', exam_scope)}"""
        )
        section_keys = await cur.fetchall()
    paths_by_collection: dict[str, list[str]] = {}
    for row in section_keys:
        paths_by_collection.setdefault(row["collection_id"], []).append(row["path"])
    for collection in collections:
        section_stats = [stats.get((collection["id"], collection["live_version"], path), {})
                         for path in paths_by_collection.get(collection["id"], [])]
        output.append(CollectionSummary(
            id=collection["id"], title=collection["title"], kind=collection["kind"],
            route=collection["route"], visibility=collection["visibility"],
            sections=collection["sections"],
            scorable=sum(row.get("scorable", 0) for row in section_stats),
            questions=sum(row.get("questions", 0) for row in section_stats),
        ))
    return output


@router.get('/group-b/study-config')
async def group_b_study_config():
    return PAPER_ROLES


@router.get("/{collection_id}", response_model=CollectionDetail)
async def get_collection(collection_id: str, exam_scope: ExamScope = DEFAULT_SCOPE) -> CollectionDetail:
    return await public_catalog(('collection-detail',collection_id,exam_scope),lambda:_get_collection(collection_id,exam_scope))


@router.get("/{collection_id}/header")
async def collection_header(collection_id: str, exam_scope: ExamScope = DEFAULT_SCOPE):
    # No coverage/answer scans: this lets a validated public exam open quickly.
    async with cursor() as cur:
        await cur.execute(
            f"SELECT id,title,kind,route,visibility FROM collections WHERE id=%s AND visibility='public' AND {scope_condition('collections', exam_scope)}",
            (collection_id,),
        )
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, 'collection not found')
    return row


@router.get("/{collection_id}/study-topics")
async def collection_study_topics(collection_id: str, exam_scope: ExamScope = DEFAULT_SCOPE, study_area: StudyArea | None = None, section_path: str | None = Query(None,max_length=200)):
    """Approved taxonomy within this exam's browsable source papers.

    Counts are distinct canonical questions at each level. A question with
    multiple approved paths may appear in more than one subject or topic, so
    child counts are never added to claim an exam total.
    """
    return await public_catalog(
        ('collection-study-topics', collection_id, exam_scope, study_area, section_path),
        lambda: _collection_study_topics(collection_id, exam_scope, study_area, section_path),
    )


async def _collection_study_topics(collection_id: str, exam_scope: ExamScope, study_area: StudyArea | None = None, section_path: str | None = None):
    if collection_id == 'group-b':
        study_area = study_area or 'common'
    membership = None
    area_params = {}
    if study_area:
        membership, area_params = study_membership(study_area, collection_id, exam_scope)
    collection_ids = list(GROUP_B_COLLECTIONS) if collection_id == 'group-b' else [collection_id]
    area_clause = f"AND v.id IN ({membership})" if membership else ""
    async with cursor() as cur:
        await cur.execute(
            f"SELECT id,title FROM collections WHERE id=ANY(%s) AND visibility='public' AND {scope_condition('collections', exam_scope)}",
            (collection_ids,),
        )
        collection = await cur.fetchone()
        if collection is None:
            raise HTTPException(404, "collection not found")
        if collection_id == 'group-b':
            collection = {'id': 'group-b', 'title': 'Group B — English & GK/GS'}
        await cur.execute("SET LOCAL jit=off")
        await cur.execute(
            f"""WITH exam_questions AS MATERIALIZED (
                SELECT DISTINCT a.canonical_id AS id
                  FROM collection_papers cp
                  JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                  JOIN papers paper ON paper.id=cp.paper_id
                  JOIN appearances a ON a.paper_id=cp.paper_id
                  JOIN {pool_view('all', exam_scope)} v ON v.id=a.canonical_id
                 WHERE cp.collection_id=ANY(%(study_collections)s) AND cp.allow_browse
                   AND (%(section_path)s::text IS NULL OR cp.section_path=%(section_path)s)
                   AND c.visibility='public' AND {scope_condition('c', exam_scope)}
                   AND {scope_condition('paper', exam_scope)} {area_clause}
            )
            SELECT GROUPING(path.subject_id) AS subject_group,
                   GROUPING(path.topic_id) AS topic_group,
                   GROUPING(path.subtopic_id) AS subtopic_group,
                   path.subject_id,MIN(path.subject_label) AS subject_label,
                   path.topic_id,MIN(path.topic_label) AS topic_label,
                   path.subtopic_id,MIN(path.subtopic_label) AS subtopic_label,
                   COUNT(DISTINCT exam_questions.id)::int AS questions
              FROM exam_questions
              LEFT JOIN ({path_projection(include_science=study_area in ("common", "gk-gs"), clerical_science=collection_id in (*CLERICAL_EXAMS,'combined-prelims') and not study_area)}) path ON path.question_id=exam_questions.id
                AND path.review_status='approved'
                AND (NOT %(primary_only)s OR path.is_primary)
             GROUP BY GROUPING SETS (
               (), (path.subject_id), (path.subject_id,path.topic_id),
               (path.subject_id,path.topic_id,path.subtopic_id)
             )""",
            {"study_collections": collection_ids, "primary_only": bool(study_area), "section_path": section_path, **area_params},
        )
        rows = await cur.fetchall()
    total = 0
    unclassified = 0
    subjects = {}
    for row in rows:
        if row['subject_group']:
            total = row['questions']
        elif row['topic_group']:
            if row['subject_id'] is None:
                unclassified = row['questions']
            else:
                subjects[row['subject_id']] = {
                    'id': row['subject_id'], 'title': ('General Knowledge' if collection_id in ('udc', 'ldc', 'assistant') and not study_area and row['subject_id']=='gk-gs' else 'General Studies' if collection_id=='combined-prelims' and row['subject_id']=='gk-gs' else row['subject_label'] or row['subject_id']),
                    'questions': row['questions'], 'topics': [],
                }
    for row in rows:
        if not row['subject_group'] and not row['topic_group'] and row['subtopic_group']:
            subject = subjects.get(row['subject_id'])
            if subject and row['topic_id']:
                subject['topics'].append({
                    'id': row['topic_id'], 'title': row['topic_label'] or row['topic_id'],
                    'questions': row['questions'], 'subtopics': [],
                })
    topics = {(subject['id'], topic['id']): topic for subject in subjects.values() for topic in subject['topics']}
    for row in rows:
        if not row['subject_group'] and not row['topic_group'] and not row['subtopic_group'] and row['subtopic_id']:
            topic = topics.get((row['subject_id'], row['topic_id']))
            if topic:
                topic['subtopics'].append({
                    'id': row['subtopic_id'], 'title': row['subtopic_label'] or row['subtopic_id'],
                    'questions': row['questions'],
                })
    ordered = sorted(subjects.values(), key=lambda item: (-item['questions'], item['title']))
    for subject in ordered:
        subject['topics'].sort(key=lambda item: (-item['questions'], item['title']))
        for topic in subject['topics']:
            topic['subtopics'].sort(key=lambda item: (-item['questions'], item['title']))
    return {'collection_id': collection_id, 'title': collection['title'],
            'questions': total, 'unclassified': unclassified, 'subjects': ordered}


async def _get_collection(collection_id: str, exam_scope: ExamScope) -> CollectionDetail:
    async with cursor() as cur:
        await cur.execute("SET LOCAL jit=off")
        await cur.execute(
            f"""SELECT id,title,kind,route,visibility,live_version FROM collections WHERE id=%s AND {scope_condition('collections', exam_scope)}""",
            (collection_id,),
        )
        head = await cur.fetchone()
        if head is None or head["visibility"] != "public":
            raise HTTPException(404, "collection not found")
        await cur.execute(
            """SELECT path,title,position,formats,note FROM collection_sections
                WHERE collection_id=%s AND version=%s ORDER BY position""",
            (collection_id, head["live_version"]),
        )
        metadata = await cur.fetchall()
        await cur.execute(
            f"""WITH paper_questions AS MATERIALIZED (
                    SELECT DISTINCT a.canonical_id
                    FROM collection_papers cp JOIN appearances a ON a.paper_id=cp.paper_id
                    JOIN papers p ON p.id=cp.paper_id
                    WHERE cp.collection_id=%s AND cp.version=%s AND cp.allow_browse
                      AND {scope_condition('p', exam_scope)}
                ), readiness AS MATERIALIZED (
                    SELECT av.*, {answer_status_sql('av')} AS answer_status
                    FROM paper_questions pq JOIN canonical_questions av ON av.id=pq.canonical_id
                    WHERE av.status IN ('live','held')
                )
                SELECT cp.paper_id AS id,COALESCE(cp.display_title,p.exam_name) AS title,
                      p.year,p.exam_name AS exam,p.paper_number,p.paper_subject AS subject,
                      p.source_file,p.pdf_url,cp.section_path,cp.allow_browse,cp.allow_practice,
                      cp.as_mock AS allow_timed_test,cp.duration_minutes,
                      cp.marks_correct,cp.marks_wrong,cp.rule_source,cp.instructions,
                      COUNT(DISTINCT av.id)::int AS questions,
                      COUNT(DISTINCT a.canonical_id) FILTER (WHERE av.answer_status='official')::int AS scorable,
                      COUNT(DISTINCT a.canonical_id) FILTER (WHERE av.type='descriptive')::int AS descriptive,
                      COUNT(DISTINCT a.canonical_id) FILTER (WHERE cp.allow_practice AND av.answer_status IN ('official','verified'))::int AS practice_count,
                      COUNT(DISTINCT av.id) FILTER (WHERE cp.allow_practice AND av.status='live' AND av.answer_text IS NOT NULL AND av.source_defect IS DISTINCT FROM 'duplicate-options' AND av.source_defect IS DISTINCT FROM 'unresolved-source')::int AS answerable_count,
                      COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='verified')::int AS verified_solutions,
                      COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='needs-review')::int AS needs_review,
                      COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='unsolved')::int AS unsolved,
                      COUNT(DISTINCT av.id) FILTER (WHERE av.type='mcq' AND NULLIF(btrim(av.explanation),'') IS NULL)::int AS missing_explanations,
                      COUNT(DISTINCT av.id) FILTER (WHERE av.status='held' OR av.key_disputed OR av.source_defect IN ('duplicate-options','unresolved-source'))::int AS blocked_count
                 FROM collection_papers cp
                 JOIN papers p ON p.id=cp.paper_id
                 LEFT JOIN appearances a ON a.paper_id=p.id
                 LEFT JOIN readiness av ON av.id=a.canonical_id
                WHERE cp.collection_id=%s AND cp.version=%s AND cp.allow_browse AND {scope_condition('p', exam_scope)}
                GROUP BY cp.paper_id,cp.display_title,p.exam_name,p.year,p.paper_number,
                         p.paper_subject,p.source_file,p.pdf_url,cp.section_path,cp.allow_browse,
                         cp.allow_practice,cp.as_mock,cp.duration_minutes,cp.marks_correct,
                         cp.marks_wrong,cp.rule_source,cp.instructions
                ORDER BY p.year DESC NULLS LAST,p.paper_number,p.paper_subject,cp.paper_id""",
            (collection_id, head["live_version"], collection_id, head["live_version"]),
        )
        paper_rows = await cur.fetchall()
        source_identities = await identities_for(cur, [r['id'] for r in paper_rows])
        papers = [CollectionPaper(
            **{**r, "paper_label": display_identity(r["id"], None, source_identities)["paper_label"], "source_pdf_url": source_pdf_url(r.get("source_file"), r.get("pdf_url")),
               "marks_correct": float(r["marks_correct"]) if r["marks_correct"] is not None else None,
               "marks_wrong": float(r["marks_wrong"]) if r["marks_wrong"] is not None else None}
        ) for r in paper_rows]
    # The paper query is scoped by its paper, and matched already scopes question IDs.
    # Reapplying launch views here would rescan the complete appearance index.
    # Count distinct questions across paper appearances; do not add section totals
    # or treat the presence of an unreviewed answer as reviewed mock eligibility.
    async with cursor() as cur:
        await cur.execute("SET LOCAL jit=off")
        matched_query = _MATCHED_QUERY.format(
            collection_filter="AND c.id=%(collection_id)s",
            collection_scope=scope_condition('c',exam_scope),
            all_view=pool_view('all',exam_scope))
        await cur.execute(matched_query + f""", readiness AS MATERIALIZED (
            SELECT av.*, {answer_status_sql('av')} AS answer_status
            FROM (SELECT DISTINCT id FROM matched) ids JOIN v_all_questions av ON av.id=ids.id
        ) SELECT mx.path,GROUPING(mx.path) AS is_total,
            COUNT(DISTINCT av.id)::int AS questions,
            COUNT(DISTINCT mx.paper_id)::int AS papers,
            COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='official')::int AS scorable,
            COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status IN ('official','verified'))::int AS practice_count,
            COUNT(DISTINCT av.id) FILTER (WHERE av.answer_text IS NOT NULL AND av.source_defect IS DISTINCT FROM 'duplicate-options' AND av.source_defect IS DISTINCT FROM 'unresolved-source')::int AS answerable_count,
            COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='needs-review')::int AS needs_review,
            COUNT(DISTINCT av.id) FILTER (WHERE av.answer_status='unsolved')::int AS unsolved
            FROM matched mx
            JOIN readiness av ON av.id=mx.id
            GROUP BY GROUPING SETS ((mx.path),())""",
            {"collection_id":collection_id})
        detail_stats = await cur.fetchall()
    totals = next(row for row in detail_stats if row['is_total'])
    readiness = {key:totals[key] for key in ('practice_count','answerable_count','needs_review','unsolved')}
    stats = {(collection_id,head['live_version'],row['path']):row for row in detail_stats if not row['is_total']}
    sections = []
    for row in metadata:
        counts = stats.get((collection_id, head["live_version"], row["path"]), {})
        sections.append(CollectionSection(
            **row, papers=counts.get("papers", 0),
            scorable=counts.get("scorable", 0), questions=counts.get("questions", 0),
        ))
    return CollectionDetail(
        id=head["id"], title=head["title"], kind=head["kind"], route=head["route"],
        visibility=head["visibility"], sections=len(sections),
        scorable=sum(s.scorable for s in sections), questions=sum(s.questions for s in sections),
        section_list=sections, paper_list=papers, **readiness,
    )


@router.get("/{collection_id}/paper-questions", response_model=PaperQuestionPage)
async def list_paper_questions(
    collection_id: str,
    paper_id: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    exam_scope: ExamScope = DEFAULT_SCOPE) -> PaperQuestionPage:
    """Browse a paper in printed order, preserving this appearance's options.

    Held items remain visible as source records, with their grading blocked.
    Correct answers are never included. Practice submissions use `option_order`
    to translate the printed choice back to the canonical option position.
    """
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT 1 FROM collection_papers cp
                 JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
                WHERE cp.collection_id=%s AND cp.paper_id=%s AND cp.allow_browse
                  AND c.visibility='public' AND {scope_condition('c', exam_scope)} AND EXISTS(SELECT 1 FROM papers sp WHERE sp.id=cp.paper_id AND {scope_condition('sp', exam_scope)})""",
            (collection_id, paper_id),
        )
        if await cur.fetchone() is None:
            raise HTTPException(404, "paper not found in this exam")
        await cur.execute(
            f"""SELECT COUNT(*)::int AS n,
                      COUNT(DISTINCT v.id) FILTER(WHERE v.id IN(SELECT id FROM {pool_view('mock_practice', exam_scope)}))::int AS practice_count
                 FROM appearances a JOIN canonical_questions v ON v.id=a.canonical_id
                WHERE a.paper_id=%s AND v.status IN ('live','held')""", (paper_id,),
        )
        counts = await cur.fetchone()
        total = counts["n"]
        practice_count = counts["practice_count"]
        await cur.execute(
            f"""SELECT v.id,a.id AS appearance_id,a.qnum,a.page,p.year,a.series,
                      a.type,a.question,COALESCE(a.direction,v.direction) AS direction,
                      COALESCE(a.question_markup,v.question_markup) AS question_markup,
                      COALESCE(a.options_markup,v.options_markup) AS options_markup,
                      COALESCE(a.passage,v.passage) AS passage,a.marks,a.essay_kind,a.options,a.option_order,v.answer_source,
                      v.source_defect,v.key_disputed,v.dispute_note,(v.status='held') AS held,
                      (SELECT bs.answer_status FROM v_bank_answer_status bs WHERE bs.id=v.id) AS answer_status,
                      (v.answer_source='derived' AND EXISTS(SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=v.id)) AS reviewed_derived,
                      a.figure_image,
                      (v.answer_source IN ('official','key')) AS verified,
                      qc.subject_id AS taxonomy_subject_id,qc.subject_label AS taxonomy_subject,
                      qc.topic_id AS taxonomy_topic_id,qc.topic_label AS taxonomy_topic
                 FROM appearances a JOIN papers p ON p.id=a.paper_id
                 JOIN canonical_questions v ON v.id=a.canonical_id AND v.status IN ('live','held')
                 LEFT JOIN question_classifications qc
                   ON qc.question_id=v.id AND qc.review_status='approved'
                WHERE a.paper_id=%s
                ORDER BY a.qnum_seq NULLS LAST,a.qnum,a.id
                LIMIT %s OFFSET %s""", (paper_id, limit, offset),
        )
        items = [PaperQuestion(**{**r, "figure_image_url": figure_image_url(r.get("figure_image"))}) for r in await cur.fetchall()]
    return PaperQuestionPage(items=items,total=total,practice_count=practice_count,limit=limit,offset=offset)
