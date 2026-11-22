from pathlib import Path
import ast,json,sys,hashlib
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'api'))
from app.services.question_readiness import answer_status_sql
from app.exam_scope import scope_condition,pool_view
r=root/'reports/finna-collection-counts-staged-20261119';source=(r/'collections.before.py').read_text();assert hashlib.sha256(source.encode()).hexdigest()=='fb3803cb6ebbe7f50c9bbef809c535c6e7cf53b41c58ebd78397379e65f1acda'
proposed=source.replace('SELECT av.*, {answer_status_sql(\'av\')} AS answer_status\n                    FROM paper_questions',"SELECT av.id,av.type,av.status,av.key_disputed,av.source_defect,\n                           av.answer_text IS NOT NULL AS has_answer,\n                           NULLIF(btrim(av.explanation),'') IS NULL AS missing_explanation,\n                           {answer_status_sql('av')} AS answer_status\n                    FROM paper_questions")
proposed=proposed.replace('SELECT av.*, {answer_status_sql(\'av\')} AS answer_status\n            FROM (SELECT DISTINCT',"SELECT av.id,av.source_defect,av.answer_text IS NOT NULL AS has_answer,\n                   {answer_status_sql('av')} AS answer_status\n            FROM (SELECT DISTINCT")
proposed=proposed.replace("av.answer_text IS NOT NULL AND av.source_defect", "av.has_answer AND av.source_defect").replace("av.type='mcq' AND NULLIF(btrim(av.explanation),'') IS NULL", "av.type='mcq' AND av.missing_explanation")
assert proposed!=source
# Compare narrow projections first, then the single evaluation of source scope.
shared=proposed.replace('WITH live_sections AS (',"WITH eligible_questions AS MATERIALIZED (\n    SELECT id,answer_text,answer_source,key_disputed,source_defect FROM {all_view}\n), live_sections AS (",1).replace('JOIN {all_view} v','JOIN eligible_questions v')
variants={'before':source,'narrow':proposed,'shared':shared}
id_query='''
WITH live_sections AS (
    SELECT s.collection_id,s.version,s.path,s.query,s.pins,s.excludes
      FROM collection_sections s
      JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
     WHERE c.visibility='public' AND {collection_scope} {collection_filter}
), candidates AS MATERIALIZED (
    SELECT s.collection_id,s.version,s.path,a.paper_id,a.canonical_id AS id
      FROM live_sections s
      JOIN appearances a ON s.query ? 'paper_ids'
       AND a.paper_id = ANY(ARRAY(SELECT jsonb_array_elements_text(s.query->'paper_ids')))
     WHERE a.canonical_id <> ALL(s.excludes)
       AND (a.canonical_id=ANY(s.pins) OR (
         (s.query->>'subject_id' IS NULL AND s.query->>'topic_id' IS NULL)
         OR EXISTS (SELECT 1 FROM v_question_paths p WHERE p.question_id=a.canonical_id
           AND (s.query->>'subject_id' IS NULL OR p.subject_id=s.query->>'subject_id')
           AND (s.query->>'topic_id' IS NULL OR p.topic_id=s.query->>'topic_id'))
       ))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,qc.question_id AS id
      FROM live_sections s
      JOIN LATERAL (
        SELECT p.question_id FROM v_question_paths p WHERE p.subject_id=s.query->>'subject_id'
          AND (s.query->>'topic_id' IS NULL OR p.topic_id=s.query->>'topic_id')
        UNION ALL
        SELECT p.question_id FROM v_question_paths p WHERE s.query->>'subject_id' IS NULL AND p.topic_id=s.query->>'topic_id'
      ) qc ON TRUE
      LEFT JOIN appearances a ON a.canonical_id=qc.question_id
     WHERE NOT (s.query ? 'paper_ids')
       AND (s.query ? 'subject_id' OR s.query ? 'topic_id')
       AND qc.question_id <> ALL(s.excludes)
       AND NOT (qc.question_id=ANY(s.pins))
    UNION ALL
    SELECT s.collection_id,s.version,s.path,a.paper_id,pin.id
      FROM live_sections s
      CROSS JOIN LATERAL unnest(s.pins) pin(id)
      LEFT JOIN appearances a ON a.canonical_id=pin.id
     WHERE pin.id <> ALL(s.excludes)
), scoped AS MATERIALIZED (
    SELECT v.id,
           (v.answer_text IS NOT NULL
            AND v.answer_source IN ('official','key')
            AND NOT v.key_disputed
            AND v.source_defect IS DISTINCT FROM 'duplicate-options') AS scorable
      FROM (SELECT DISTINCT id FROM candidates) ids
      JOIN {all_view} v ON v.id=ids.id
), matched AS (
    SELECT c.collection_id,c.version,c.path,c.paper_id,c.id,v.scorable
      FROM candidates c JOIN scoped v ON v.id=c.id
)'''
start=proposed.index('_MATCHED_QUERY = """');end=proposed.index('\n\n_STATS_QUERY',start)
variants['ids']=proposed[:start]+'_MATCHED_QUERY = """'+id_query+'"""'+proposed[end:]
for name,s in variants.items():
 target=r/('collections.'+name+'.py')
 if target.exists():assert target.read_text()==s,'Frozen proposal changed'
 else:target.write_text(s)
queries={}
for scope in ('mizoram-recruitment','all'):
 queries[scope]={}
 for name,s in variants.items():
  if name not in ('before','ids'):continue
  tree=ast.parse(s);env={'answer_status_sql':answer_status_sql,'scope_condition':scope_condition,'pool_view':pool_view,'exam_scope':scope}
  for var in ('_MATCHED_QUERY','_STATS_QUERY'):
   node=next(n for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id==var);env[var]=eval(compile(ast.Expression(node.value),'<query>','eval'),env)
  collection_scope=scope_condition('c',scope);all_view=pool_view('all',scope)
  matched=env['_MATCHED_QUERY'].format(collection_scope=collection_scope,all_view=all_view,collection_filter='AND c.id=%(collection_id)s');env['matched_query']=matched
  fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_get_collection')
  expressions=[n.args[0] for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute']
  evaluated=[]
  for exp in expressions:
   try:value=eval(compile(ast.Expression(exp),'<query>','eval'),env)
   except (NameError,TypeError):continue
   if isinstance(value,str):evaluated.append(value)
  paper=next(q for q in evaluated if 'WITH paper_questions AS MATERIALIZED' in q)
  detail=next(q for q in evaluated if 'is_total' in q)
  queries[scope][name]={'sections':env['_STATS_QUERY'].format(collection_scope=collection_scope,all_view=all_view,collection_filter=''), 'paper':paper,'detail':detail}
payload=json.dumps(queries,indent=2)+'\n';target=r/'queries.json'
if target.exists():assert target.read_text()==payload,'Frozen query payload changed'
else:target.write_text(payload)
print({name:hashlib.sha256(s.encode()).hexdigest() for name,s in variants.items()})
