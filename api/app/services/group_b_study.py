"""Learning areas are independent of recruitment streams and source paper titles.

Only approved primary content tags select common questions. Science requires
an explicit GK/GS paper role; technical membership requires an explicit paper
role rather than the complement of common subjects. Related tags never promote
specialist questions into common practice. Unknown roles remain in full papers.
"""
import json
from pathlib import Path
from typing import Literal
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from ..exam_scope import scope_condition

StudyArea = Literal['common', 'english', 'gk-gs', 'technical']
GROUP_B_COLLECTIONS = ('group-b-gazetted', 'group-b-non-gazetted')
PAPER_ROLES = json.loads((Path(__file__).parents[1] / 'data/group-b-paper-roles.json').read_text())


def source_paper_label(paper_id: str) -> str | None:
    """Return only a source-verified heading, independently of question taxonomy."""
    return next((r["paper_label"] for r in PAPER_ROLES["rules"]
                 if r["paper_id"] == paper_id and r.get("paper_label")), None)


def general_science_source(alias: str) -> str:
    """Match the source appearance, including reviewed mixed-paper boundaries.

    CASE guards numeric casts even if PostgreSQL reorders predicates. Unknown
    or compound question numbers cannot satisfy a bounded source role.
    """
    if alias not in ('ga', 'a'):
        raise ValueError('Unsupported source appearance alias')
    number = f"CASE WHEN {alias}.qnum ~ '^[0-9]{{1,6}}$' THEN {alias}.qnum::int END"
    return f"""EXISTS (SELECT 1 FROM jsonb_to_recordset(%(gb_general_roles)s)
        AS role(paper_id text,qnum_from integer,qnum_to integer)
        WHERE role.paper_id={alias}.paper_id
          AND (role.qnum_from IS NULL OR {number}>=role.qnum_from)
          AND (role.qnum_to IS NULL OR {number}<=role.qnum_to))"""


def study_membership(area: StudyArea, collection_id: str | None, exam_scope):
    if collection_id and collection_id != 'group-b' and collection_id not in GROUP_B_COLLECTIONS:
        raise HTTPException(422, 'Group B learning areas require a Group B collection')
    collections = [collection_id] if collection_id in GROUP_B_COLLECTIONS else list(GROUP_B_COLLECTIONS)
    params = {
        'gb_collections': collections,
        'gb_general_roles': Jsonb([r for r in PAPER_ROLES['rules'] if r['role'] == 'gk-gs' and r['collection_id'] in collections]),
        'gb_technical_papers': [r['paper_id'] for r in PAPER_ROLES['rules'] if r['role'] == 'technical' and r['collection_id'] in collections],
    }
    english = "gc.subject_id='english'"
    general = f"(gc.subject_id IN ('general-knowledge','general-studies') OR (gc.subject_id='science' AND {general_science_source('ga')}))"
    technical = "(ga.paper_id=ANY(%(gb_technical_papers)s) AND gc.subject_id NOT IN ('english','general-knowledge','general-studies'))"
    condition = {'english': english, 'gk-gs': general, 'common': f'({english} OR {general})', 'technical': technical}[area]
    sql = f"""SELECT ga.canonical_id FROM collection_papers gp
        JOIN collections gr ON gr.id=gp.collection_id AND gr.live_version=gp.version
        JOIN papers gpaper ON gpaper.id=gp.paper_id
        JOIN appearances ga ON ga.paper_id=gp.paper_id
        JOIN question_classifications gc ON gc.question_id=ga.canonical_id
          AND gc.review_status='approved' AND gc.is_primary
        WHERE gp.collection_id=ANY(%(gb_collections)s) AND gp.allow_browse
          AND gr.visibility='public' AND {scope_condition('gr', exam_scope)}
          AND {scope_condition('gpaper', exam_scope)} AND {condition}"""
    return sql, params
