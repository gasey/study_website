"""Single authoritative resolver for module section membership (FINNAPLAN v2 P4 / V.27).

The three-key section contract — paper_ids, subject_id, topic_id — plus pins,
excludes and collection_papers lives here once. Every caller (collections,
questions, facets, module_composition, review_scope, atlas_context) cites this
module. Internal SQL literals only; client text is never interpolated.
"""
from ..exam_scope import ExamScope, pool_view, scope_condition

PAPER_IDS_KEY = "paper_ids"
SUBJECT_ID_KEY = "subject_id"
TOPIC_ID_KEY = "topic_id"

_SCORABLE_EXPR = (
    "(v.answer_text IS NOT NULL"
    " AND v.answer_source IN ('official','key')"
    " AND NOT v.key_disputed"
    " AND v.source_defect IS DISTINCT FROM 'duplicate-options')"
)

_ALLOWED_ALIASES = frozenset({"a", "cs", "s", "ss"})


def _check_alias(alias: str) -> str:
    if alias not in _ALLOWED_ALIASES:
        raise ValueError(f"Unsupported SQL alias: {alias}")
    return alias


def has_paper_ids(section_query: dict) -> bool:
    return PAPER_IDS_KEY in section_query


def section_taxonomy_predicate(
    section_alias: str,
    question_expr: str = "v.id",
    *,
    require_approved: bool = True,
) -> str:
    """Match a section's optional subject_id and topic_id against v_question_paths."""
    s = _check_alias(section_alias)
    approved = " AND qp.review_status='approved'" if require_approved else ""
    return (
        f"({s}.query->>'{SUBJECT_ID_KEY}' IS NULL OR EXISTS ("
        f"SELECT 1 FROM v_question_paths qp WHERE qp.question_id={question_expr}"
        f"{approved} AND qp.subject_id={s}.query->>'{SUBJECT_ID_KEY}'))"
        f" AND ({s}.query->>'{TOPIC_ID_KEY}' IS NULL OR EXISTS ("
        f"SELECT 1 FROM v_question_paths qp WHERE qp.question_id={question_expr}"
        f"{approved} AND qp.topic_id={s}.query->>'{TOPIC_ID_KEY}'))"
    )


def section_appearance_predicate(section_alias: str, appearance_alias: str = "a") -> str:
    """Match an appearance row against a section's paper_ids, taxonomy, pins and excludes."""
    s = _check_alias(section_alias)
    a = _check_alias(appearance_alias)
    tax = section_taxonomy_predicate(s, f"{a}.canonical_id", require_approved=True)
    return (
        f"{a}.canonical_id <> ALL({s}.excludes) AND ("
        f"{a}.canonical_id = ANY({s}.pins) OR ("
        f"(NOT ({s}.query ? '{PAPER_IDS_KEY}') OR {a}.paper_id IN ("
        f"SELECT jsonb_array_elements_text({s}.query->'{PAPER_IDS_KEY}')))"
        f" AND {tax}))"
    )


def section_question_predicate(section_alias: str = "ss") -> str:
    """Match canonical question `v.id` against a specific collection_sections row."""
    s = _check_alias(section_alias)
    tax = section_taxonomy_predicate(s, "v.id", require_approved=True)
    return (
        f"v.id <> ALL({s}.excludes) AND ("
        f"v.id = ANY({s}.pins) OR ("
        f"(NOT ({s}.query ? '{PAPER_IDS_KEY}') OR EXISTS ("
        f"SELECT 1 FROM appearances sa WHERE sa.canonical_id=v.id"
        f" AND sa.paper_id IN (SELECT jsonb_array_elements_text({s}.query->'{PAPER_IDS_KEY}'))))"
        f" AND {tax}))"
    )


def matched_sections_cte(
    exam_scope: ExamScope,
    *,
    collection_filter: str = "",
    pool: str = "all",
) -> str:
    """Three-branch CTE resolving every live public section without whole-bank cross joins.

    Branch 1 uses the paper index for paper-backed exam modules.
    Branch 2 uses the v_question_paths subject/topic index for taxonomy-only subject modules.
    Branch 3 includes explicit pins.
    """
    c_scope = scope_condition("c", exam_scope)
    all_v = pool_view(pool, exam_scope)
    return f"""WITH live_sections AS (
    SELECT s.collection_id,s.version,s.path,s.query,s.pins,s.excludes
      FROM collection_sections s
      JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
     WHERE c.visibility='public' AND {c_scope} {collection_filter}
), matched AS (
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           {_SCORABLE_EXPR} AS scorable
      FROM live_sections s
      JOIN appearances a ON s.query ? '{PAPER_IDS_KEY}'
       AND a.paper_id = ANY(ARRAY(SELECT jsonb_array_elements_text(s.query->'{PAPER_IDS_KEY}')))
      JOIN {all_v} v ON v.id=a.canonical_id
     WHERE v.id <> ALL(s.excludes)
       AND (v.id=ANY(s.pins) OR (
         (s.query->>'{SUBJECT_ID_KEY}' IS NULL AND s.query->>'{TOPIC_ID_KEY}' IS NULL)
         OR EXISTS (SELECT 1 FROM v_question_paths p WHERE p.question_id=v.id
           AND (s.query->>'{SUBJECT_ID_KEY}' IS NULL OR p.subject_id=s.query->>'{SUBJECT_ID_KEY}')
           AND (s.query->>'{TOPIC_ID_KEY}' IS NULL OR p.topic_id=s.query->>'{TOPIC_ID_KEY}'))
       ))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           {_SCORABLE_EXPR} AS scorable
      FROM live_sections s
      JOIN LATERAL (
        SELECT p.question_id FROM v_question_paths p WHERE p.subject_id=s.query->>'{SUBJECT_ID_KEY}'
          AND (s.query->>'{TOPIC_ID_KEY}' IS NULL OR p.topic_id=s.query->>'{TOPIC_ID_KEY}')
        UNION ALL
        SELECT p.question_id FROM v_question_paths p WHERE s.query->>'{SUBJECT_ID_KEY}' IS NULL AND p.topic_id=s.query->>'{TOPIC_ID_KEY}'
      ) qc ON TRUE
      JOIN {all_v} v ON v.id=qc.question_id
      LEFT JOIN appearances a ON a.canonical_id=v.id
     WHERE NOT (s.query ? '{PAPER_IDS_KEY}')
       AND (s.query ? '{SUBJECT_ID_KEY}' OR s.query ? '{TOPIC_ID_KEY}')
       AND v.id <> ALL(s.excludes)
       AND NOT (v.id=ANY(s.pins))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,v.id,
           {_SCORABLE_EXPR} AS scorable
      FROM live_sections s
      JOIN {all_v} v ON v.id=ANY(s.pins)
      LEFT JOIN appearances a ON a.canonical_id=v.id
     WHERE v.id <> ALL(s.excludes)
       AND cardinality(s.pins)>0
)"""


def collection_membership_subquery(
    exam_scope: ExamScope,
    *,
    collection_param: str = "collection_id",
    section_path_param: str | None = None,
) -> str:
    """Canonical question ID subquery for one collection (paper-backed OR taxonomy-only).

    Uses the indexed v_question_paths branch for taxonomy-only subject modules
    instead of cross-joining all appearances in the bank.
    """
    c_scope = scope_condition("cc", exam_scope)
    ec_scope = scope_condition("ec", exam_scope)
    sec_filter = f" AND cs.path=%({section_path_param})s" if section_path_param else ""
    paper_sec_filter = (
        f" AND (%({section_path_param})s::text IS NULL OR ep.section_path=%({section_path_param})s)"
        if section_path_param
        else ""
    )
    return f"""WITH live_sections AS MATERIALIZED (
        SELECT cs.* FROM collection_sections cs JOIN collections cc
          ON cc.id=cs.collection_id AND cc.live_version=cs.version
        WHERE cs.collection_id=%({collection_param})s AND cc.visibility='public'
          AND {c_scope}{sec_filter}
    ), section_papers AS MATERIALIZED (
        SELECT cs.*,jsonb_array_elements_text(cs.query->'{PAPER_IDS_KEY}') AS paper_id
        FROM live_sections cs WHERE cs.query ? '{PAPER_IDS_KEY}'
    )
    SELECT ca.canonical_id AS id FROM section_papers cs
      JOIN appearances ca ON ca.paper_id=cs.paper_id
     WHERE ca.canonical_id <> ALL(cs.excludes)
       AND (ca.canonical_id = ANY(cs.pins) OR (
         (cs.query->>'{SUBJECT_ID_KEY}' IS NULL OR EXISTS (
           SELECT 1 FROM v_question_paths cqc WHERE cqc.question_id=ca.canonical_id
             AND cqc.review_status='approved' AND cqc.subject_id=cs.query->>'{SUBJECT_ID_KEY}'))
         AND (cs.query->>'{TOPIC_ID_KEY}' IS NULL OR EXISTS (
           SELECT 1 FROM v_question_paths cqt WHERE cqt.question_id=ca.canonical_id
             AND cqt.review_status='approved' AND cqt.topic_id=cs.query->>'{TOPIC_ID_KEY}'))
       ))
    UNION
    SELECT p.question_id AS id FROM live_sections cs
      JOIN LATERAL (
        SELECT vp.question_id FROM v_question_paths vp
         WHERE vp.review_status='approved'
           AND vp.subject_id=cs.query->>'{SUBJECT_ID_KEY}'
           AND (cs.query->>'{TOPIC_ID_KEY}' IS NULL OR vp.topic_id=cs.query->>'{TOPIC_ID_KEY}')
        UNION ALL
        SELECT vp.question_id FROM v_question_paths vp
         WHERE vp.review_status='approved'
           AND cs.query->>'{SUBJECT_ID_KEY}' IS NULL
           AND vp.topic_id=cs.query->>'{TOPIC_ID_KEY}'
      ) p ON TRUE
     WHERE NOT (cs.query ? '{PAPER_IDS_KEY}')
       AND (cs.query ? '{SUBJECT_ID_KEY}' OR cs.query ? '{TOPIC_ID_KEY}')
       AND p.question_id <> ALL(cs.excludes)
    UNION
    SELECT unnest(cs.pins) AS id FROM live_sections cs
     WHERE cardinality(cs.pins) > 0
    UNION
    SELECT ea.canonical_id AS id FROM appearances ea
      JOIN collection_papers ep ON ep.paper_id=ea.paper_id
      JOIN collections ec ON ec.id=ep.collection_id AND ec.live_version=ep.version
     WHERE ec.visibility='public' AND {ec_scope}
       AND ep.collection_id=%({collection_param})s AND ep.allow_browse{paper_sec_filter}"""


def collection_source_area_sql(collection_param: str = "collection_id") -> str:
    """Restrict displayed source appearances to those belonging to the active collection."""
    return f"""AND (EXISTS (
        SELECT 1 FROM collection_papers cp JOIN collections c
          ON c.id=cp.collection_id AND c.live_version=cp.version
        WHERE cp.collection_id=%({collection_param})s AND c.visibility='public'
          AND cp.paper_id=a.paper_id
    ) OR EXISTS (
        SELECT 1 FROM collection_sections cs JOIN collections c
          ON c.id=cs.collection_id AND c.live_version=cs.version
        WHERE cs.collection_id=%({collection_param})s AND c.visibility='public'
          AND (NOT (cs.query ? '{PAPER_IDS_KEY}') OR
            a.paper_id IN (SELECT jsonb_array_elements_text(cs.query->'{PAPER_IDS_KEY}')))
    ))"""


def bounded_papers_sql() -> str:
    """SQL collecting explicit paper IDs for bounded review scopes."""
    return f"""WITH sections AS MATERIALIZED (SELECT cs.* FROM collection_sections cs
      JOIN collections c ON c.id=cs.collection_id AND c.live_version=cs.version WHERE cs.collection_id=ANY(%s))
      SELECT cp.paper_id FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
        WHERE cp.collection_id=ANY(%s) AND cp.allow_browse
      UNION SELECT jsonb_array_elements_text(query->'{PAPER_IDS_KEY}') FROM sections
      UNION SELECT a.paper_id FROM appearances a JOIN sections s ON a.canonical_id=ANY(s.pins)"""


def atlas_binding_predicate(section_alias: str = "s") -> str:
    """Match a collection section's subject/topic keys against an Atlas topic binding."""
    s = _check_alias(section_alias)
    return (
        f"{s}.query->>'{SUBJECT_ID_KEY}'=b.live->>'{SUBJECT_ID_KEY}'"
        f" AND ({s}.query->>'{TOPIC_ID_KEY}' IS NULL OR {s}.query->>'{TOPIC_ID_KEY}'=b.live->>'{TOPIC_ID_KEY}')"
    )


async def collection_behavior(cur, collection_ids: list[str], exam_scope: ExamScope) -> dict:
    """Read declared per-module behaviour flags and section shape from data."""
    if not collection_ids:
        return {
            "exists": False,
            "series_grouping": False,
            "science_projection": False,
            "gk_gs_label": None,
            "has_wide_taxonomy": False,
            "section_paths": set(),
        }
    await cur.execute(
        f"""SELECT BOOL_OR(c.series_grouping) AS series_grouping,
                   BOOL_OR(c.science_projection) AS science_projection,
                   MIN(c.gk_gs_label) AS gk_gs_label,
                   COUNT(DISTINCT c.id)::int AS found
              FROM collections c
             WHERE c.id = ANY(%s)
               AND c.visibility = 'public'
               AND {scope_condition('c', exam_scope)}""",
        (collection_ids,),
    )
    head = await cur.fetchone()
    if not head or not head["found"]:
        return {
            "exists": False,
            "series_grouping": False,
            "science_projection": False,
            "gk_gs_label": None,
            "has_wide_taxonomy": False,
            "section_paths": set(),
        }
    await cur.execute(
        f"""SELECT s.path,
                   (NOT (s.query ? '{PAPER_IDS_KEY}')
                    AND (s.query ? '{SUBJECT_ID_KEY}' OR s.query ? '{TOPIC_ID_KEY}')) AS wide_taxonomy
              FROM collection_sections s
              JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
             WHERE s.collection_id = ANY(%s)
               AND c.visibility = 'public'
               AND {scope_condition('c', exam_scope)}""",
        (collection_ids,),
    )
    sections = await cur.fetchall()
    return {
        "exists": True,
        "series_grouping": bool(head["series_grouping"]),
        "science_projection": bool(head["science_projection"]),
        "gk_gs_label": head["gk_gs_label"],
        "has_wide_taxonomy": any(row["wide_taxonomy"] for row in sections),
        "section_paths": {row["path"] for row in sections},
    }
