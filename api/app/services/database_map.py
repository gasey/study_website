"""Owner-only content/workflow map. Exposes counts/schema, never private row values."""

NODES=[
 ('papers','Source papers','bank','The original exam identity, year and PDF reference.','/admin/bank?tab=exams'),
 ('appearances','Printed positions','bank','A question exactly where it appeared, including option order, page and printed number.','/admin/bank?tab=questions'),
 ('canonical_questions','Shared questions','bank','Reusable question content. One question can be used across sources and modules.','/admin/bank?tab=questions'),
 ('question_classifications','Primary learning paths','bank','The approved primary subject, topic and subtopic for a question.','/admin/bank?tab=retag'),
 ('review_documents','Source documents','bank','Registered original papers, key editions and their source hashes.','/admin/bank?tab=pdf-library'),
 ('bank_paper_profiles','Paper configurations','bank','Source provider, era, exact scheme revision and reviewed printed layout.','/admin/bank?tab=organization&organization_view=paper'),
 ('bank_question_contexts','Dated / regional context','bank','Region, language, reference period and when an answer changes over time.','/admin/bank?tab=retag'),
 ('question_topic_links','Related learning paths','bank','Additional approved learning paths without copying the question.','/admin/bank?tab=retag'),
 ('bank_source_providers','Source providers','bank','Exam boards, books, websites and other registered origins.','/admin/bank?tab=organization&organization_view=providers'),
 ('bank_scheme_revisions','Exam scheme editions','bank','Immutable current or legacy scheme revisions, with source evidence and unknown rules kept explicit.','/admin/bank?tab=organization'),
 ('bank_repeat_relations','Reviewed repeat links','bank','Source-bound repeat decisions; original IDs and appearances remain intact.','/admin/bank?tab=retag'),
 ('review_taxonomy','Learning taxonomy','bank','The registered subject/topic/subtopic definitions used by learning paths.','/admin/bank?tab=taxonomy'),
 ('collections','Exam / learning modules','delivery','Published entry points and their pinned configuration versions.','/admin/bank?tab=organization&organization_view=modules'),
 ('collection_sections','Module selection rules','delivery','Filters, pins and exclusions that select reusable questions.','/editorial'),
 ('collection_papers','Module paper membership','delivery','Which original papers a module includes, and whether browsing or mocks are allowed.','/editorial'),
 ('library_shelves','Library subject shelves','delivery','Learning views selected through approved topic paths.','/library'),
 ('learning_catalog','User collections & tests','delivery','Private drafts and published learning collections; owner decisions or independent review are recorded.','/learning/manage?kind=practice'),
 ('learning_test_publications','Published test editions','delivery','Immutable test settings and private question/key snapshots.','/tests'),
 ('mock_sessions','Mock attempts','delivery','Private learner sessions with saved rules, timing and original results.','/tests'),
 ('mock_session_questions','Attempt question snapshots','delivery','The exact content and option order used in each attempt.','/tests'),
 ('attempts','Recorded answers','delivery','Private learner answer history; this map shows only its row count.','/admin/bank?tab=database'),
 ('bank_contributions','Correction proposals','editing','Versioned correction proposals and their workflow state.','/admin/bank?tab=review'),
 ('contribution_revisions','Correction revisions','editing','Immutable proposed payloads and their original source comparison.','/admin/bank?tab=review'),
 ('admin_bank_decisions','Owner / admin decisions','editing','Attributable direct decisions, including automatic change summaries.','/admin/bank?tab=publications'),
 ('bank_publications','Publication receipts','editing','Queued/applied changes and their bank publication/readback receipts.','/admin/bank?tab=publications'),
 ('paper_workbench_drafts','Paper preparation','editing','Saved source-bound paper drafts.','/paper-workbench'),
 ('paper_workbench_reviews','Paper decisions','editing','Independent, owner or explicitly scoped AI approval records, kept distinct.','/paper-workbench'),
 ('paper_workbench_jobs','PDF / publication jobs','editing','Extraction, OCR, crop and publication work with durable status.','/admin/bank?tab=pdf-library&pdf_view=activity'),
]

# These are editorial relationships, including rule-based selection; not all are FKs.
RELATIONSHIPS=[
 ('papers','appearances','contains printed positions'),
 ('appearances','canonical_questions','references the shared question'),
 ('canonical_questions','question_classifications','has one primary learning path'),
 ('canonical_questions','question_topic_links','can have additional paths'),
 ('canonical_questions','bank_question_contexts','has reference-period context'),
 ('canonical_questions','bank_repeat_relations','may have reviewed repeat links'),
 ('papers','review_documents','has registered paper / key evidence'),
 ('papers','bank_paper_profiles','has source and layout configuration'),
 ('bank_paper_profiles','bank_scheme_revisions','pins an exact scheme revision'),
 ('bank_paper_profiles','bank_source_providers','identifies its provider'),
 ('question_classifications','review_taxonomy','uses controlled definitions'),
 ('question_topic_links','review_taxonomy','uses controlled definitions'),
 ('question_classifications','library_shelves','matches approved shelf paths'),
 ('collections','collection_sections','organises selection rules'),
 ('collections','collection_papers','includes original papers'),
 ('collection_papers','papers','references source papers'),
 ('collection_sections','canonical_questions','selects through rules / pins'),
 ('learning_catalog','canonical_questions','reuses selected bank IDs'),
 ('learning_catalog','learning_test_publications','publishes immutable editions'),
 ('learning_test_publications','mock_sessions','starts edition-bound attempts'),
 ('mock_sessions','mock_session_questions','freezes presented questions'),
 ('mock_session_questions','canonical_questions','references the original ID'),
 ('mock_sessions','attempts','records submitted answers'),
 ('canonical_questions','attempts','retains learner history'),
 ('bank_contributions','contribution_revisions','retains proposed revisions'),
 ('bank_contributions','admin_bank_decisions','may have a direct admin decision'),
 ('bank_contributions','bank_publications','publishes through guarded receipts'),
 ('bank_publications','canonical_questions','applies reviewed changes'),
 ('paper_workbench_drafts','paper_workbench_reviews','records the approval kind'),
 ('paper_workbench_drafts','paper_workbench_jobs','queues source processing / publication'),
 ('paper_workbench_drafts','papers','publishes a source-bound paper'),
]


async def read_map(cur):
    ids=[n[0] for n in NODES]
    # SQL identifiers originate only in the registry above, never request input.
    await cur.execute('SELECT '+','.join('(SELECT count(*)::bigint FROM '+t+') AS '+t for t in ids)+',now() AS observed_at')
    totals=await cur.fetchone()
    await cur.execute('''SELECT c.relname AS table_id,a.attname AS name,format_type(a.atttypid,a.atttypmod) AS type,
      a.attnotnull AS required,EXISTS(SELECT 1 FROM pg_constraint p WHERE p.conrelid=c.oid AND p.contype='p' AND a.attnum=ANY(p.conkey)) AS primary_key
      FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid
      WHERE ns.nspname='public' AND c.relname=ANY(%s) AND a.attnum>0 AND NOT a.attisdropped
      ORDER BY c.relname,a.attnum''',(ids,))
    columns={t:[] for t in ids}
    for row in await cur.fetchall():columns[row['table_id']].append({k:v for k,v in row.items() if k!='table_id'})
    await cur.execute('''SELECT k.conname AS id,src.relname AS source,dest.relname AS target,
      ARRAY(SELECT a.attname FROM unnest(k.conkey) WITH ORDINALITY u(n,pos)
        JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=u.n ORDER BY u.pos) AS source_columns,
      ARRAY(SELECT a.attname FROM unnest(k.confkey) WITH ORDINALITY u(n,pos)
        JOIN pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=u.n ORDER BY u.pos) AS target_columns,
      EXISTS(SELECT 1 FROM pg_index i WHERE i.indrelid=k.conrelid AND i.indisunique AND i.indpred IS NULL
        AND i.indkey::smallint[] @> k.conkey AND k.conkey @> i.indkey::smallint[]) AS source_unique,
      EXISTS(SELECT 1 FROM pg_attribute a WHERE a.attrelid=k.conrelid AND a.attnum=ANY(k.conkey) AND NOT a.attnotnull) AS optional
      FROM pg_constraint k JOIN pg_class src ON src.oid=k.conrelid JOIN pg_class dest ON dest.oid=k.confrelid
      JOIN pg_namespace ns ON ns.oid=src.relnamespace
      WHERE k.contype='f' AND ns.nspname='public' AND src.relname=ANY(%s) AND dest.relname=ANY(%s)
      ORDER BY src.relname,dest.relname,k.conname''',(ids,ids))
    foreign_keys=await cur.fetchall()
    await cur.execute("SELECT count(*)::int AS questions,count(*) FILTER(WHERE topic_id IS NULL)::int AS without_topic,count(*) FILTER(WHERE subtopic_id IS NULL)::int AS without_subtopic FROM question_classifications WHERE is_primary AND review_status='approved'")
    return {'tables':[{'id':t,'title':title,'group':group,'description':description,'href':href,'total':totals[t],'columns':columns[t]} for t,title,group,description,href in NODES],
      'coverage':await cur.fetchone(),'relationships':RELATIONSHIPS,'foreign_keys':foreign_keys,
      'observed_at':totals['observed_at'],'read_only':True,
      'scope':'Selected content and workflow tables. Account, credential and billing tables are outside this map.'}
