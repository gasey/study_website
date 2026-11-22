#!/usr/bin/env python3
"""Use indexed receipt probes for small sets and bulk authority for large sets."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'api'))
from app.services.question_readiness import answer_status_sql
from app.exam_scope import pool_view,scope_condition
PRIOR=ROOT/'reports/finna-collection-counts-staged-20261119';REPORT=ROOT/'reports/finna-collection-counts-adaptive-20261119'
before=(PRIOR/'collections.before.py').read_text();assert hashlib.sha256(before.encode()).hexdigest()=='fb3803cb6ebbe7f50c9bbef809c535c6e7cf53b41c58ebd78397379e65f1acda'
candidate=(PRIOR/'collections.narrow.py').read_text()
candidate=candidate.replace("{answer_status_sql('av')} AS answer_status", "CASE WHEN (SELECT COUNT(*) FROM paper_questions)>=50000\n                           THEN bs.answer_status ELSE {answer_status_sql('av')} END AS answer_status",1)
clause='FROM paper_questions pq JOIN canonical_questions av ON av.id=pq.canonical_id';assert clause in candidate;candidate=candidate.replace(clause,clause+'\n                    JOIN v_bank_answer_status bs ON bs.id=av.id',1)
candidate=candidate.replace('matched_query + f""", readiness AS MATERIALIZED (','matched_query + f""", question_ids AS MATERIALIZED (\n            SELECT DISTINCT id FROM matched\n        ), readiness AS MATERIALIZED (',1)
candidate=candidate.replace("{answer_status_sql('av')} AS answer_status", "CASE WHEN (SELECT COUNT(*) FROM question_ids)>=50000\n                   THEN bs.answer_status ELSE {answer_status_sql('av')} END AS answer_status",1)
clause='FROM (SELECT DISTINCT id FROM matched) ids JOIN v_all_questions av ON av.id=ids.id';assert clause in candidate;candidate=candidate.replace(clause,'FROM question_ids ids JOIN v_all_questions av ON av.id=ids.id\n            JOIN v_bank_answer_status bs ON bs.id=av.id',1)
candidate=candidate.replace('    # The paper query is scoped', '    # Keep indexed receipt probes below 50k questions. The measured full-bank\n    # authority scan is only cheaper for large pools; CASE evaluates one branch.\n    # The paper query is scoped',1)
variants={'before':before,'adaptive':candidate}
for name,value in variants.items():
 p=REPORT/('collections.'+name+'.py')
 if p.exists():assert p.read_text()==value
 else:p.write_text(value)
queries={}
for scope in ('mizoram-recruitment','all'):
 queries[scope]={}
 for name,source in variants.items():
  tree=ast.parse(source);env={'answer_status_sql':answer_status_sql,'scope_condition':scope_condition,'pool_view':pool_view,'exam_scope':scope}
  for var in ('_MATCHED_QUERY','_STATS_QUERY'):
   n=next(n for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id==var);env[var]=eval(compile(ast.Expression(n.value),'<query>','eval'),env)
  env['matched_query']=env['_MATCHED_QUERY'].format(collection_scope=scope_condition('c',scope),all_view=pool_view('all',scope),collection_filter='AND c.id=%(collection_id)s')
  fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_get_collection');evaluated=[]
  for n in ast.walk(fn):
   if not(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute'):continue
   try:v=eval(compile(ast.Expression(n.args[0]),'<query>','eval'),env)
   except(NameError,TypeError):continue
   if isinstance(v,str):evaluated.append(v)
  queries[scope][name]={'sections':env['_STATS_QUERY'].format(collection_scope=scope_condition('c',scope),all_view=pool_view('all',scope),collection_filter=''),'paper':next(q for q in evaluated if 'WITH paper_questions AS MATERIALIZED' in q),'detail':next(q for q in evaluated if 'is_total' in q)}
p=REPORT/'queries.json';payload=json.dumps(queries,indent=2)+'\n'
if p.exists():assert p.read_text()==payload
else:p.write_text(payload)
print({n:hashlib.sha256(s.encode()).hexdigest() for n,s in variants.items()})
