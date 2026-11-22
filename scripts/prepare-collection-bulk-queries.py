#!/usr/bin/env python3
"""Freeze bulk-readiness proposals without changing earlier count evidence."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'api'))
from app.services.question_readiness import answer_status_sql
from app.exam_scope import pool_view,scope_condition
PRIOR=ROOT/'reports/finna-collection-counts-staged-20261119'
REPORT=ROOT/'reports/finna-collection-counts-bulk-20261119'
source=(PRIOR/'collections.before.py').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='fb3803cb6ebbe7f50c9bbef809c535c6e7cf53b41c58ebd78397379e65f1acda'
variants={'before':source}
for name,base in [('bulk',source),('bulk_narrow',(PRIOR/'collections.narrow.py').read_text())]:
 candidate=base.replace("{answer_status_sql('av')} AS answer_status",'bs.answer_status')
 for clause in ('FROM paper_questions pq JOIN canonical_questions av ON av.id=pq.canonical_id','FROM (SELECT DISTINCT id FROM matched) ids JOIN v_all_questions av ON av.id=ids.id'):
  assert clause in candidate
  candidate=candidate.replace(clause,clause+'\n                    JOIN v_bank_answer_status bs ON bs.id=av.id')
 candidate=candidate.replace('from ..services.question_readiness import answer_status_sql\n','')
 variants[name]=candidate
for name,value in variants.items():
 target=REPORT/('collections.'+name+'.py')
 if target.exists():assert target.read_text()==value,'Frozen proposal changed'
 else:target.write_text(value)
queries={}
for scope in ('mizoram-recruitment','all'):
 queries[scope]={}
 for name,source in variants.items():
  tree=ast.parse(source);env={'answer_status_sql':answer_status_sql,'scope_condition':scope_condition,'pool_view':pool_view,'exam_scope':scope}
  for var in ('_MATCHED_QUERY','_STATS_QUERY'):
   node=next(n for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id==var)
   env[var]=eval(compile(ast.Expression(node.value),'<query>','eval'),env)
  env['matched_query']=env['_MATCHED_QUERY'].format(collection_scope=scope_condition('c',scope),all_view=pool_view('all',scope),collection_filter='AND c.id=%(collection_id)s')
  fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_get_collection');evaluated=[]
  for n in ast.walk(fn):
   if not (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute'):continue
   try:v=eval(compile(ast.Expression(n.args[0]),'<query>','eval'),env)
   except (NameError,TypeError):continue
   if isinstance(v,str):evaluated.append(v)
  queries[scope][name]={'sections':env['_STATS_QUERY'].format(collection_scope=scope_condition('c',scope),all_view=pool_view('all',scope),collection_filter=''),'paper':next(q for q in evaluated if 'WITH paper_questions AS MATERIALIZED' in q),'detail':next(q for q in evaluated if 'is_total' in q)}
payload=json.dumps(queries,indent=2)+'\n';target=REPORT/'queries.json'
if target.exists():assert target.read_text()==payload
else:target.write_text(payload)
print({name:hashlib.sha256(s.encode()).hexdigest() for name,s in variants.items()})
