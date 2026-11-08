"""Read-only task lanes; workflow grouping never changes answer eligibility."""
async def page(cur,where,params,paper_id,exam_id,year,task,ordering,limit,offset):
    # Evaluate the full scoped bank once. Only the bounded page looks up source
    # appearances; counts never multiply a canonical question by its appearances.
    candidate_sql='SELECT * FROM filtered' if paper_id else 'SELECT * FROM filtered ORDER BY id LIMIT %s OFFSET %s'
    page_limit=' LIMIT %s OFFSET %s' if paper_id else ''
    query="""WITH bank_status AS MATERIALIZED (SELECT * FROM v_bank_answer_status), latest_kind AS MATERIALIZED (
      SELECT DISTINCT ON (canonical_id,kind) canonical_id,kind,id,state,updated_at
      FROM bank_contributions WHERE canonical_id IS NOT NULL AND state<>'draft'
      ORDER BY canonical_id,kind,updated_at DESC,id DESC
    ), outstanding AS MATERIALIZED (
      SELECT DISTINCT ON (canonical_id) canonical_id,id,state,kind
      FROM latest_kind WHERE state IN ('accepted','publishing','publication_failed')
      ORDER BY canonical_id,CASE WHEN state IN ('accepted','publishing') THEN 0 ELSE 1 END,updated_at DESC,id DESC
    ), scoped AS MATERIALIZED (
      SELECT q.id,bs.answer_status,w.id AS work_id,w.state AS work_state,w.kind AS work_kind,
       CASE WHEN w.state IN ('accepted','publishing') THEN 'publishing'
        WHEN w.state='publication_failed' THEN 'failed'
        WHEN q.status='held' OR q.key_disputed OR q.source_defect IS NOT NULL
          OR (bs.answer_status='needs-review' AND q.answer_source IN ('official','key')) THEN 'source'
        WHEN bs.answer_status IN ('needs-review','unsolved') THEN 'answer'
        ELSE 'other' END AS review_task
      FROM canonical_questions q JOIN bank_status bs ON bs.id=q.id
      LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved'
      LEFT JOIN outstanding w ON w.canonical_id=q.id WHERE """+where+"""
    ), filtered AS MATERIALIZED (
      SELECT * FROM scoped WHERE (%s='all' OR review_task=%s)
    ), candidates AS MATERIALIZED ("""+candidate_sql+"""
    ), selected AS (
      SELECT q.id,q.type,q.question,q.answer_source,q.answer_text IS NULL AS missing_answer,
       q.status,q.source_defect,q.key_disputed,f.answer_status,c.subject_id,c.subject_label,c.topic_label,
       a.id AS appearance_id,a.paper_id,a.qnum,a.page,p.exam_name AS paper_title,
       f.review_task,f.work_id,f.work_state,f.work_kind
      FROM candidates f JOIN canonical_questions q ON q.id=f.id
      LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved'
      LEFT JOIN LATERAL (SELECT a.id,a.paper_id,a.qnum,a.page FROM appearances a WHERE a.canonical_id=q.id
       AND (%s::text IS NULL OR a.paper_id=%s)
       AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=a.paper_id AND ep.exam_id=%s))
       AND (%s::int IS NULL OR EXISTS(SELECT 1 FROM papers yp WHERE yp.id=a.paper_id AND yp.year=%s))
       ORDER BY a.is_primary DESC,a.id LIMIT 1) a ON true
      LEFT JOIN papers p ON p.id=a.paper_id ORDER BY """+ordering+page_limit+"""
    ) SELECT (SELECT count(*)::int FROM filtered) AS total,
      (SELECT COALESCE(jsonb_object_agg(review_task,n),'{}'::jsonb) FROM
       (SELECT review_task,count(*)::int AS n FROM scoped GROUP BY review_task) counts) AS task_counts,
      (SELECT COALESCE(jsonb_agg(to_jsonb(selected)),'[]'::jsonb) FROM selected) AS items"""
    paging=(limit,offset)
    args=(*params,task,task,*(() if paper_id else paging),paper_id,paper_id,exam_id,exam_id,year,year,*(paging if paper_id else ()))
    await cur.execute(query,args)
    result=await cur.fetchone()
    for row in result['items']:
        if row['review_task']=='publishing':reason=('An answer' if row['work_kind']=='answer' else 'A '+row['work_kind'].replace('_',' '))+' decision is queued. This list updates automatically when publication finishes.'
        elif row['review_task']=='failed':reason='The latest '+row['work_kind']+' publication failed. Open its details before retrying.'
        elif row['status']=='held':reason='Held from scoring; resolve the hold before confirming the answer.'
        elif row['key_disputed']:reason='The recorded key is disputed; compare the key and printed source.'
        elif row['source_defect']:reason='Source problem: '+row['source_defect']+'. Repair it before confirming the answer.'
        elif row['review_task']=='source':reason='The recorded options cannot support scoring. Compare the printed options and key.'
        elif row['missing_answer'] and row['type']=='mcq':reason='No MCQ answer is recorded.'
        elif row['answer_status']=='needs-review':reason=('Stored inferred answer' if row['answer_source']=='inferred' else 'Stored answer')+' has no current applied verification.'
        elif row['answer_status']=='verified':reason='Supported unofficial answer; verified publication is recorded.'
        elif row['answer_status']=='official':reason='Official or transcribed key is recorded.'
        else:reason='Written question; review its transcription and marking guidance.'
        row['review_reason']=reason
    result['task_counts']['all']=sum(result['task_counts'].values())
    return result
