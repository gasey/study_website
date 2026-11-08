"""Conservative, presentation-only collapse of identical booklet text variants.

This is not a canonical merge. Source papers, attempts and timed papers retain
their identities. Figures, source differences and different solutions stay apart.
"""
from .question_readiness import reviewed_answer_sql


def study_series_pool(view, clause, *, members=False):
    # The candidate filters run before grouping; learner status runs afterwards.
    # Prefer the most recently attempted member so legacy progress is still usable
    # and an answered series does not return as an unseen parallel booklet.
    selection='SELECT candidate.*'+(',ranked.series_ever_wrong' if not members else '')+' FROM series_candidates candidate'
    if not members:selection+=' JOIN series_ranked ranked ON ranked.id=candidate.id AND ranked.series_rank=1'
    return rf"""(
      WITH series_candidates AS MATERIALIZED (
        SELECT v.*, latest.attempt_id AS study_attempt_id, COALESCE(latest.ever_wrong,false) AS study_ever_wrong,
          CASE WHEN src.family IS NOT NULL AND v.type='mcq'
            AND NOT COALESCE(src.has_diagram,false) AND src.figure_image IS NULL
            AND NOT EXISTS (SELECT 1 FROM appearances figure_source
              WHERE figure_source.canonical_id=v.id
                AND (figure_source.has_diagram OR figure_source.figure_image IS NOT NULL))
            AND src.question=v.question AND src.options=v.options
            THEN jsonb_build_array(src.family,v.question,v.options,
              v.direction,v.passage,v.question_markup,v.options_markup,
              src.direction,src.passage,src.question_markup,src.options_markup,
              v.answer_text,v.answer_source,v.explanation,v.status,
              v.key_disputed,v.source_defect,
              CASE WHEN v.answer_source='derived' THEN {reviewed_answer_sql()} ELSE false END)
            ELSE jsonb_build_array(v.id) END AS study_series_key
        FROM {view} v
        LEFT JOIN LATERAL (
          SELECT jsonb_build_array(p.year,p.paper_number,
              regexp_replace(p.id,'[ -]+Series[ -]+[A-D](\.*\.pdf)$','.pdf','i')) AS family,
            a.question,a.options,a.direction,a.passage,a.question_markup,a.options_markup,
            a.has_diagram,a.figure_image
          FROM appearances a JOIN papers p ON p.id=a.paper_id
          JOIN collection_papers cp ON cp.paper_id=p.id
          JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
          WHERE a.canonical_id=v.id AND a.is_primary
            AND cp.collection_id=%(series_collection)s AND c.visibility='public'
            AND p.year IS NOT NULL
            AND p.id ~* '[ -]+Series[ -]+[A-D](\.*\.pdf)$'
          ORDER BY a.id LIMIT 1
        ) src ON TRUE
        LEFT JOIN LATERAL (
          SELECT MAX(id) AS attempt_id,bool_or(NOT correct) AS ever_wrong FROM attempts
          WHERE user_id=%(series_user)s AND canonical_id=v.id
            AND collection_id=%(series_collection)s
        ) latest ON TRUE
        {clause}
      ), series_ranked AS (
        SELECT id,bool_or(study_ever_wrong) OVER (PARTITION BY study_series_key) AS series_ever_wrong,row_number() OVER (PARTITION BY study_series_key
          ORDER BY study_attempt_id DESC NULLS LAST,id) AS series_rank
        FROM series_candidates
      )
      {selection}
    )"""

