#!/usr/bin/env python3
"""Prepare immutable comparison evidence; optional operator import. Never writes bank content."""
import argparse,csv,hashlib,json,re,subprocess,unicodedata
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parents[1]
POLICY='unicode-whitespace-stem-ordered-options-v2'
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(v):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(v or '')).casefold()).strip()
def identity(q):return normalize(q.get('question',q.get('text',''))),tuple(normalize(o) for o in q.get('options') or [])
def cid(aid):return 'cq_'+hashlib.md5(aid.encode()).hexdigest()[:16]
def answer(q):
 n=q.get('answerIndex');return n if type(n)is int and 0<=n<len(q.get('options')or[]) else None
def comparison(a,b):return 'agree' if a is not None and a==b else 'conflict' if a is not None and b is not None else 'module_only' if a is not None else 'bank_only' if b is not None else 'neither'
def load_source(p):
 if p.suffix=='.ts':return json.loads(subprocess.check_output(['node',str(ROOT/'scripts/export-module-source.mjs'),str(p)],text=True))
 return json.loads(p.read_text())
def prepare(module,source,crosswalk,bank,packets=(),answer_review=None):
 raw=load_source(source);questions=raw['questions'];
 if len(questions)>20000 or len({q['id'] for q in questions})!=len(questions):raise ValueError('Module records need unique IDs and at most 20000 rows')
 papers={p['id']:p for p in raw.get('papers',[])}
 old={}
 with crosswalk.open(newline='') as f:
  for row in csv.DictReader(f):
   if row['legacy_question_id'] in old:raise ValueError('Duplicate crosswalk question ID')
   old[row['legacy_question_id']]=row
 if set(old)!={q['id'] for q in questions}:raise ValueError('Crosswalk/source ID sets differ; regenerate report before intake')
 answer_review_sha=file_sha(answer_review) if answer_review else None
 historical_answers={}
 if answer_review:
  with answer_review.open(newline='') as f:
   for row in csv.DictReader(f):
    if row.get('legacy_question_id') in old:historical_answers[row['legacy_question_id']]=row
 data=json.loads(bank.read_text());byid={q['id']:q for q in data['questions']};index=defaultdict(list)
 for q in data['questions']:
  if identity(q)[0]:index[identity(q)].append(q)
 reviewed=defaultdict(list)
 for path in packets:
  d=json.loads(path.read_text());meta={k:v for k,v in d.items() if k not in {'claims','held'}}
  for claim in d.get('claims',[])+d.get('held',[]):
   if not isinstance(claim,dict):continue
   aid=claim.get('appearanceId',claim.get('appearance_id',claim.get('questionId')))
   if aid:reviewed[aid].append({'file':path.name,'sha256':file_sha(path),'metadata':meta,'claim':claim})
 run={'module_id':module,'source_file':source.name,'source_sha256':file_sha(source),'crosswalk_file':crosswalk.name,'crosswalk_sha256':file_sha(crosswalk),'bank_sha256':file_sha(bank),'policy':POLICY,'module_url':'https://map.hawayu.in/'+('udc-ldc' if module=='udc-ldc' else 'mpsc-combined-prelims')}
 run['id']='mar_'+digest({**run,'packets':[(p.name,file_sha(p)) for p in packets],'answer_review':answer_review_sha})[:32]
 items=[];stats=Counter()
 for q in questions:
  matches={x['id']:x for x in index.get(identity(q),[])} if identity(q)[0] else {}
  status='exact_unique' if len(matches)==1 else 'ambiguous_exact' if matches else 'unmatched'
  comp=comparison(answer(q),answer(next(iter(matches.values())))) if status=='exact_unique' else 'ambiguous' if matches else 'unmatched'
  paper=papers.get(q.get('paperId'),{})
  legacy={k:q[k] for k in ('type','subject','topic','topicLabel','answerSource','answerStatus','source','year','page','number','qnum','direction','passage','hasDiagram','figureImage','questionMarkup','optionsMarkup','explanation','derivedExplanation') if k in q}
  legacy.update(question=q.get('question',q.get('text','')),options=q.get('options') or [],answerIndex=answer(q),paper=paper)
  # Source hashes preserve the original artifact; request views use safe React text.
  item={'id':'mai_'+digest([run['id'],q['id']])[:32],'run_id':run['id'],'legacy_id':q['id'],'paper_id':q.get('paperId',''),'match_status':status,'comparison':comp,'legacy':legacy,'previous_report':{**old[q['id']],**({'answer_review':historical_answers[q['id']],'answer_review_file':answer_review.name,'answer_review_sha256':answer_review_sha} if q['id'] in historical_answers else {})},'reviewed_packets':[],'candidates':[]}
  historical=set(filter(None,old[q['id']].get('candidate_appearance_ids','').split('|')))
  historical.update(filter(None,[old[q['id']].get('source_appearance_id')]))
  for aid in sorted(set(matches)|historical):
   b=byid.get(aid,{})
   item['candidates'].append({'appearance_id':aid,'canonical_id':cid(aid),'imported':{'paper_id':b.get('paperId'),'answer_index':answer(b),'answer_source':b.get('answerSource'),'identity_sha256':digest(identity(b)),'identity_exact':aid in matches,'match_basis':'current_exact' if aid in matches else 'historical_crosswalk'}})
   item['reviewed_packets'].extend(reviewed.get(aid,[]))
  # Unmatched records may still have an earlier reviewed source claim.
  prior=old[q['id']].get('source_appearance_id')
  if prior and prior not in matches:item['reviewed_packets'].extend(reviewed.get(prior,[]))
  stats[status]+=1;stats['answer_'+comp]+=1;items.append(item)
 run['counts']=dict(stats)
 manifest={'schema':1,'run':run,'items':items};run['manifest_sha256']=digest(manifest)
 return manifest

def import_manifest(conn,manifest,actor='operator:module-audit-import'):
 from psycopg.types.json import Jsonb
 r=manifest['run'];unsigned=json.loads(json.dumps(manifest));unsigned['run'].pop('manifest_sha256',None)
 if digest(unsigned)!=r['manifest_sha256']:raise ValueError('Manifest hash mismatch')
 if len(manifest['items'])>20000:raise ValueError('Bounded intake: maximum 20000 records per run')
 with conn.transaction():
  conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",('module-import:'+r['id'],))
  existing=conn.execute('SELECT manifest_sha256 FROM module_audit_runs WHERE id=%s',(r['id'],)).fetchone()
  if existing:
   if existing[0]!=r['manifest_sha256']:raise ValueError('Run ID already has different evidence')
   return {'id':r['id'],'replayed':True,'items':len(manifest['items'])}
  conn.execute('INSERT INTO module_audit_runs(id,module_id,source_file,source_sha256,crosswalk_file,crosswalk_sha256,bank_sha256,manifest_sha256,policy,module_url,counts,imported_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',tuple(r[k] for k in ['id','module_id','source_file','source_sha256','crosswalk_file','crosswalk_sha256','bank_sha256','manifest_sha256','policy','module_url'])+(Jsonb(r['counts']),actor))
  with conn.cursor() as cur:
   cur.executemany('INSERT INTO module_audit_items(id,run_id,legacy_id,paper_id,match_status,comparison,legacy,previous_report,reviewed_packets) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[(i['id'],r['id'],i['legacy_id'],i['paper_id'],i['match_status'],i['comparison'],Jsonb(i['legacy']),Jsonb(i['previous_report']),Jsonb(i['reviewed_packets'])) for i in manifest['items']])
   cur.executemany('INSERT INTO module_audit_candidates(item_id,appearance_id,canonical_id,imported) VALUES(%s,%s,%s,%s)',[(i['id'],c['appearance_id'],c['canonical_id'],Jsonb(c['imported'])) for i in manifest['items'] for c in i['candidates']])
   cur.executemany('INSERT INTO module_audit_triage(item_id) VALUES(%s)',[(i['id'],) for i in manifest['items']])
 return {'id':r['id'],'replayed':False,'items':len(manifest['items'])}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--module',choices=['udc-ldc','combined-prelims']);p.add_argument('--source',type=Path);p.add_argument('--crosswalk',type=Path);p.add_argument('--bank',type=Path,default=ROOT.parent/'mpsc-question-bankv2/bank/mpsc_bank_v2.json');p.add_argument('--packet',type=Path,action='append',default=[]);p.add_argument('--answer-review',type=Path);p.add_argument('--output',type=Path);p.add_argument('--load',type=Path);p.add_argument('--database',help='Local PostgreSQL DSN; never printed');p.add_argument('--allow-historical-bank',action='store_true');args=p.parse_args()
 if args.load:
  if not args.database:p.error('--load requires --database')
  import psycopg
  with psycopg.connect(args.database) as conn:
   m=json.loads(args.load.read_text())
   if not args.allow_historical_bank:
    synced=conn.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1').fetchone()
    if not synced or synced[0]!=m['run']['bank_sha256']:raise ValueError('Bank import hash does not match the latest completed sync; recheck the bank or explicitly import a historical audit')
   print(json.dumps(import_manifest(conn,m)))
 else:
  if not all([args.module,args.source,args.crosswalk,args.output]):p.error('Prepare requires --module --source --crosswalk --output')
  m=prepare(args.module,args.source,args.crosswalk,args.bank,args.packet,args.answer_review);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':'))+'\n');print(json.dumps({'id':m['run']['id'],'counts':m['run']['counts'],'items':len(m['items']),'manifest_sha256':m['run']['manifest_sha256']}))
if __name__=='__main__':main()
