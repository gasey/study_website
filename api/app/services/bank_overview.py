"""Read-only coverage, configuration and historical work; never a certification."""
FACTS = """WITH facts AS MATERIALIZED (
 SELECT q.id,q.status,q.type,
 c.question_id IS NULL AS missing_subject,
 c.question_id IS NOT NULL AND NULLIF(c.topic_id,'') IS NULL AS missing_topic,
 q.type='mcq' AND q.answer_text IS NULL AS missing_answer,
 q.type='mcq' AND NULLIF(btrim(q.explanation),'') IS NULL AS missing_explanation,
 q.source_defect IS NOT NULL OR q.key_disputed AS source_issue
 FROM canonical_questions q LEFT JOIN question_classifications c
 ON c.question_id=q.id AND c.review_status='approved' WHERE q.status<>'merged'
) """
COUNTS = """count(f.id)::int AS questions,
 count(f.id) FILTER(WHERE f.status='live')::int AS live,
 count(f.id) FILTER(WHERE f.status='held')::int AS held,
 count(f.id) FILTER(WHERE f.type='descriptive')::int AS written,
 count(f.id) FILTER(WHERE f.missing_subject)::int AS missing_subject,
 count(f.id) FILTER(WHERE f.missing_topic)::int AS missing_topic,
 count(f.id) FILTER(WHERE f.missing_answer)::int AS missing_answer,
 count(f.id) FILTER(WHERE f.missing_explanation)::int AS missing_explanation,
 count(f.id) FILTER(WHERE f.source_issue)::int AS source_issue"""

async def overview(cur):
    await cur.execute(FACTS+'SELECT '+COUNTS+' FROM facts f')
    totals=await cur.fetchone()
    await cur.execute(FACTS+""", membership AS (
      SELECT DISTINCT cp.collection_id,a.canonical_id
      FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
      JOIN appearances a ON a.paper_id=cp.paper_id WHERE cp.allow_browse
    ), paper_counts AS (
      SELECT cp.collection_id,count(*)::int AS papers,
       count(*) FILTER(WHERE bp.scheme_id IS NOT NULL)::int AS mapped_papers
      FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
      LEFT JOIN bank_paper_profiles bp ON bp.paper_id=cp.paper_id
      WHERE cp.allow_browse GROUP BY cp.collection_id
    ) SELECT c.id,c.title,COALESCE(p.papers,0) AS papers,COALESCE(p.mapped_papers,0) AS mapped_papers,"""+COUNTS+"""
      FROM collections c LEFT JOIN membership m ON m.collection_id=c.id
      LEFT JOIN facts f ON f.id=m.canonical_id LEFT JOIN paper_counts p ON p.collection_id=c.id
      WHERE c.kind='exam' AND c.live_version IS NOT NULL
      GROUP BY c.id,p.papers,p.mapped_papers ORDER BY c.position,c.title,c.id""")
    exams=await cur.fetchall()
    await cur.execute("""SELECT now() AS generated_at,
      (SELECT count(*) FROM papers)::int AS papers,
      (SELECT count(DISTINCT scheme_id) FROM bank_scheme_revisions)::int AS schemes,
      (SELECT count(*) FROM bank_paper_profiles WHERE scheme_id IS NOT NULL)::int AS mapped_papers,
      (SELECT count(DISTINCT canonical_id) FROM editorial_checks)::int AS questions_with_inspections,
      (SELECT count(*) FROM bank_contributions WHERE state='published')::int AS published_corrections""")
    activity=await cur.fetchone()
    return {'totals':totals,'exams':exams,**activity}
