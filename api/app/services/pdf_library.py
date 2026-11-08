"""Snapshot reconciliation. Counts and filters share the same source identities."""

# Paths are compared only within known roots. A hash match groups bytes, never
# merges registered paper IDs. All filesystem work belongs to the scan worker.
LIBRARY = r"""
WITH files AS MATERIALIZED (
 SELECT f.*,CASE WHEN root IN ('canonical','served') THEN regexp_replace(relative_path,'^pdfs/','') END AS source_path
 FROM pdf_library_files f WHERE scan_id=%(scan)s
), matches AS MATERIALIZED (
 SELECT DISTINCT p.id AS paper_id,f.sha256 FROM papers p JOIN files f
 ON f.source_path=regexp_replace(COALESCE(p.source_file,p.id),'^pdfs/','')
 UNION
 SELECT DISTINCT d.paper_id,f.sha256 FROM review_documents d JOIN files f ON f.sha256=d.sha256
 WHERE d.kind='paper' AND d.paper_id IS NOT NULL
), assets AS MATERIALIZED (
 SELECT sha256,count(*)::int AS copies,bool_and(valid_pdf) AS valid_pdf,
 (array_agg(id ORDER BY CASE root WHEN 'served' THEN 0 WHEN 'canonical' THEN 1 ELSE 2 END,id))[1] AS file_id,
 min(bytes) AS bytes,jsonb_agg(jsonb_build_object('root',root,'path',relative_path,'id',id) ORDER BY root,relative_path) AS paths,
 min(relative_path) AS filename,
 CASE WHEN bool_or(relative_path LIKE 'Old_Questions/%%') THEN 'paper'
 WHEN bool_or(relative_path LIKE 'Answer_Keys/%%') THEN 'official-key' ELSE 'document' END AS archive_kind
 FROM files GROUP BY sha256
), document_hashes AS MATERIALIZED (
 SELECT sha256,min(title) AS title,min(kind) AS kind,count(*)::int AS registered_documents FROM review_documents GROUP BY sha256
), paper_assets AS MATERIALIZED (
 SELECT paper_id,count(*)::int AS asset_count,min(sha256) AS sha256 FROM matches GROUP BY paper_id
), statuses AS MATERIALIZED (
 SELECT s.* FROM v_bank_answer_status s WHERE %(answers)s AND (%(key)s='' OR EXISTS(
 SELECT 1 FROM appearances a WHERE a.canonical_id=s.id AND 'paper:'||a.paper_id=%(key)s))
), counts AS MATERIALIZED (
 SELECT a.paper_id,count(*)::int AS questions,
 count(*) FILTER(WHERE s.answer_status='official')::int AS official,
 count(*) FILTER(WHERE s.answer_status='verified')::int AS verified,
 count(*) FILTER(WHERE s.answer_status='needs-review')::int AS needs_review,
 count(*) FILTER(WHERE s.answer_status='unsolved')::int AS unsolved,
 count(*) FILTER(WHERE s.answer_status='written')::int AS written,
 count(*) FILTER(WHERE NULLIF(btrim(q.explanation),'') IS NOT NULL)::int AS explained
 FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id AND q.status<>'merged'
 LEFT JOIN statuses s ON s.id=q.id GROUP BY a.paper_id
), docs AS MATERIALIZED (
 SELECT paper_id,count(*) FILTER(WHERE kind='paper')::int AS registered_documents,
 count(*) FILTER(WHERE kind='official-key' AND key_status='final')::int AS final_keys,
 count(*) FILTER(WHERE kind='official-key' AND key_status='provisional')::int AS provisional_keys
 FROM review_documents GROUP BY paper_id
), modules AS MATERIALIZED (
 SELECT cp.paper_id,jsonb_agg(jsonb_build_object('id',c.id,'title',c.title,'version',c.live_version) ORDER BY c.title) AS modules
 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version
 WHERE c.visibility='public' GROUP BY cp.paper_id
), draft_rows AS MATERIALIZED (
 SELECT id,state,version,updated_at,last_error,published_paper_id,source_sha256,
 payload->>'target_paper_id' AS target_paper_id FROM paper_workbench_drafts
), paper_rows AS (
 SELECT 'paper:'||p.id AS key,p.id AS paper_id,COALESCE(p.exam_name,p.id) AS title,p.year,'paper'::text AS kind,
 regexp_replace(COALESCE(p.source_file,p.id),'^.*/','') AS source_label,
 COALESCE(n.questions,0) AS questions,COALESCE(n.official,0) AS official,COALESCE(n.verified,0) AS verified,
 COALESCE(n.needs_review,0) AS needs_review,COALESCE(n.unsolved,0) AS unsolved,COALESCE(n.written,0) AS written,
 COALESCE(n.explained,0) AS explained,COALESCE(d.registered_documents,0) AS registered_documents,
 COALESCE(d.final_keys,0) AS final_keys,COALESCE(d.provisional_keys,0) AS provisional_keys,
 COALESCE(m.modules,'[]') AS modules,
 COALESCE(pa.asset_count,0) AS asset_count,pa.sha256
 FROM papers p LEFT JOIN counts n ON n.paper_id=p.id LEFT JOIN docs d ON d.paper_id=p.id
 LEFT JOIN modules m ON m.paper_id=p.id LEFT JOIN paper_assets pa ON pa.paper_id=p.id
), other_rows AS (
 SELECT 'file:'||a.sha256 AS key,NULL::text AS paper_id,
 COALESCE(d.title,regexp_replace(a.filename,'^.*/','')) AS title,NULL::int AS year,COALESCE(d.kind,a.archive_kind) AS kind,
 regexp_replace(a.filename,'^.*/','') AS source_label,
 0 AS questions,0 AS official,0 AS verified,0 AS needs_review,0 AS unsolved,0 AS written,0 AS explained,
 COALESCE(d.registered_documents,0) AS registered_documents,
 0 AS final_keys,0 AS provisional_keys,'[]'::jsonb AS modules,1 AS asset_count,a.sha256
 FROM assets a LEFT JOIN document_hashes d ON d.sha256=a.sha256 WHERE NOT EXISTS(SELECT 1 FROM matches x WHERE x.sha256=a.sha256)
), base AS MATERIALIZED (
 SELECT r.*,CASE WHEN r.asset_count=1 THEN a.file_id END AS file_id,a.bytes,a.copies,a.valid_pdf,
 CASE WHEN r.asset_count>1 THEN COALESCE((SELECT jsonb_agg(jsonb_build_object('root',f.root,'path',f.relative_path,'id',f.id))
 FROM files f JOIN matches x ON x.sha256=f.sha256 WHERE x.paper_id=r.paper_id),'[]') ELSE COALESCE(a.paths,'[]') END AS paths,
 CASE WHEN r.asset_count>1 THEN 'ambiguous' WHEN r.asset_count=1 THEN 'available'
 WHEN %(scan)s::bigint IS NULL THEN 'unknown' ELSE 'not-found' END AS file_status,
 CASE WHEN wd.id IS NULL THEN NULL ELSE jsonb_build_object('id',wd.id,'state',wd.state,'version',wd.version,
 'updated_at',wd.updated_at,'error',wd.last_error,'published_paper_id',wd.published_paper_id) END AS draft,
 (r.paper_id IS NOT NULL AND r.questions=0) AS empty_paper,
 (r.paper_id IS NOT NULL AND r.registered_documents=0) AS missing_registration,
 (r.paper_id IS NULL AND r.registered_documents=0 AND wd.id IS NULL) AS unlinked
 FROM (SELECT * FROM paper_rows UNION ALL SELECT * FROM other_rows) r
 LEFT JOIN assets a ON a.sha256=r.sha256
 LEFT JOIN LATERAL(SELECT * FROM draft_rows w WHERE
 w.published_paper_id=r.paper_id OR w.target_paper_id=r.paper_id OR (w.source_sha256=r.sha256
 AND (r.paper_id IS NULL OR COALESCE(w.published_paper_id,w.target_paper_id) IS NULL))
 ORDER BY CASE WHEN w.published_paper_id=r.paper_id OR w.target_paper_id=r.paper_id THEN 0 ELSE 1 END,
 w.updated_at DESC,w.id LIMIT 1) wd ON true
), filtered AS MATERIALIZED (
 SELECT * FROM base WHERE (%(q)s='' OR title ILIKE %(like)s OR paper_id ILIKE %(like)s OR sha256=%(q)s OR paths::text ILIKE %(like)s)
 AND (%(year)s::int IS NULL OR year=%(year)s)
 AND (%(kind)s='' OR kind=%(kind)s)
 AND (%(module)s='' OR EXISTS(SELECT 1 FROM jsonb_array_elements(modules) m WHERE m->>'id'=%(module)s))
 AND (CASE %(gap)s WHEN 'empty' THEN empty_paper WHEN 'unlinked' THEN unlinked WHEN 'ambiguous' THEN asset_count>1
 WHEN 'registration' THEN missing_registration WHEN 'missing-file' THEN file_status='not-found'
 WHEN 'review' THEN draft->>'state' IN ('draft','review','approved','failed')
 WHEN 'answers' THEN needs_review+unsolved>0
 WHEN 'attention' THEN empty_paper OR missing_registration OR unlinked OR asset_count>1 OR file_status='not-found'
 OR valid_pdf=false OR draft->>'state' IN ('draft','review','approved','failed') ELSE true END)
 AND (%(key)s='' OR key=%(key)s)
)
SELECT (SELECT count(*)::int FROM filtered) AS total,
 COALESCE((SELECT jsonb_agg(to_jsonb(page)) FROM (SELECT * FROM filtered ORDER BY
 CASE WHEN EXISTS(SELECT 1 FROM jsonb_array_elements(modules) m WHERE m->>'id' IN ('ldc','udc','assistant')) THEN 0 ELSE 1 END,
 year DESC NULLS LAST,title,key LIMIT %(limit)s OFFSET %(offset)s) page),'[]') AS items,
 (SELECT jsonb_build_object('registered_papers',count(*) FILTER(WHERE paper_id IS NOT NULL),
 'empty_papers',count(*) FILTER(WHERE empty_paper),'missing_registrations',count(*) FILTER(WHERE missing_registration),
 'unlinked_files',count(*) FILTER(WHERE unlinked),'ambiguous',count(*) FILTER(WHERE asset_count>1),
 'missing_files',count(*) FILTER(WHERE file_status='not-found')) FROM base) AS summary
"""


async def listing(cur, scan_id, *, q='', gap='', module='', year=None, kind='', key='', offset=0, limit=20):
    await cur.execute(LIBRARY, {'scan': scan_id, 'q': q, 'like': '%' + q + '%', 'gap': gap, 'answers': bool(key) or gap=='answers',
                              'module': module, 'year': year, 'kind': kind, 'key': key, 'offset': offset, 'limit': limit})
    return await cur.fetchone()
