#!/usr/bin/env python3
"""Rehearse empty-source publication using disposable local accounts and SQL.

Runs the real API, document publisher, guarded fixture-bank writer and normal sync
SQL. Only CSV transport paths and the disposable database name differ. No canonical
bank, authority policy, live account or production review is changed.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'api/tests'),str(ROOT/'api'),str(ROOT/'scripts')]
import conftest
import pytest
from psycopg.rows import dict_row
from paper_bank_store import PAPER_FIELDS
from test_paper_workbench import paper,registered_empty,prepared,get,save,bind_original,approve_original,transition,scoped_ai_review,ai_flags


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',required=True,type=Path)
 parser.add_argument('--owner-decision',action='store_true',help='Exercise an explicit solo-owner decision through the full isolated publisher')
 parser.add_argument('--owner-ai-provisional-key',action='store_true',help='Exercise attributed owner/AI approval and a synthetic provisional key')
 args=parser.parse_args();output=args.output.resolve()
 if args.owner_decision and args.owner_ai_provisional_key:parser.error('Choose one approval mode')
 if output.exists():raise ValueError('Use a fresh disposable output directory')
 canonical=ROOT.parent/'mpsc-question-bankv2'
 if output.is_relative_to(canonical) or canonical.is_relative_to(output):raise ValueError('Output must not overlap the recovery bank')
 output.mkdir(parents=True,mode=0o700)
 real_bank=canonical/'bank/mpsc_bank_v2.json'
 before_real=hashlib.sha256(real_bank.read_bytes()).hexdigest()
 dbs=conftest.database.__wrapped__();dbname,conn=next(dbs)
 clients=conftest.client.__wrapped__((dbname,conn));client=next(clients)
 patch=pytest.MonkeyPatch()
 try:
  assert dbname.startswith('ism_review_test_')
  actor=conftest.actor.__wrapped__(client)
  private=output/'private'
  did,h=paper.__wrapped__(client,actor,(dbname,conn),private,patch)
  did,h,pid,doc=registered_empty.__wrapped__(client,actor,(did,h),(dbname,conn))
  prepared(client,did,h);detail=get(client,did);payload=detail['payload']
  payload['questions'][0].update(type='descriptive',question='Write a unique synthetic response for '+did,options=[])
  payload['questions'].append({**payload['questions'][0],'id':'synthetic_mcq_01','number':'2','type':'mcq','question':'Choose a unique synthetic option for '+did,'options':['Choice one','Choice two']})
  payload['expected_questions']=2
  if args.owner_ai_provisional_key:
   from app.services import paper_jobs
   patch.setattr(paper_jobs,'pdf_pages',lambda path:1)  # Synthetic PDF fixture only.
   uploaded=client.post('/api/paper-workbench/uploads',headers={**h,'content-type':'application/pdf'},content=b'%PDF-1.4\nSynthetic provisional key fixture '+did.encode())
   assert uploaded.status_code==201,uploaded.text
   payload.update(key_sha256=uploaded.json()['sha256'],key_title='Synthetic provisional key',key_status='provisional',key_series='')
   payload['questions'][1].update(answer_index=0,answer_source='key',key_page=1)
  assert save(client,did,h,payload,detail['version']).status_code==200
  version=bind_original(client,did,h)
  # Read-only bank fixture includes the existing synthetic question and every
  # metadata row seeded by migrations. Normal sync must preserve those identities.
  with conn.cursor(row_factory=dict_row) as cur:
   rows=cur.execute('SELECT * FROM papers ORDER BY id').fetchall()
   papers=[{key:row.get(column) for column,key in PAPER_FIELDS.items()} for row in rows]
   sittings={row['id']:{'id':row['id'],'examName':row['exam_name'],'examType':row['exam_type'],'year':row['year'],'month':row['month']} for row in cur.execute('SELECT * FROM sittings').fetchall()}
  old={'id':'appearance-test','paperId':'paper-test','type':'mcq','qnum':'1','page':1,'question':'Choose the correct synthetic option','options':['A','B','C','D'],'answerIndex':1,'answerSource':'derived','classifications':[{'subject_id':'english','subject_label':'English','taxonomy_version':'test','source':'manual','review_status':'approved','is_primary':True}]}
  bank={'papers':papers,'sittings':sittings,'questions':[old]}
  original=next(p for p in papers if p['id']==pid);original['preserve_legacy_metadata']={'value':'unchanged'}
  workshop=output/'workshop';bank_root=workshop/'mpsc-question-bankv2';scripts=workshop/'india-study-map-app/scripts'
  scripts.mkdir(parents=True);(bank_root/'bank').mkdir(parents=True)
  bank_path=bank_root/'bank/mpsc_bank_v2.json';bank_path.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
  private_source=private/'sources'/(get(client,did)['source_sha256']+'.pdf')
  source=bank_root/'pdfs'/pid;source.parent.mkdir(parents=True);shutil.copyfile(private_source,source)
  shutil.copyfile(ROOT/'scripts/paper_bank_store.py',scripts/'paper_bank_store.py')
  # Execute exactly the checked-in staging and APPLY SQL in a child process.
  # The child's database name is fixed here and cannot come from production env.
  fail_once=output/'interrupt-after-sync';fail_once.touch()
  config={'database':dbname,'bank':str(bank_path),'root':str(ROOT),'csv':str(output/'csv'),'taxonomy':str(canonical/'taxonomies/question-bank-v2.json'),'fail_once':str(fail_once)}
  config_path=output/'sync-config.json';config_path.write_text(json.dumps(config))
  sync=scripts/'sync-bank.sh'
  sync.write_text('#!'+sys.executable+'\n'+r'''
import hashlib,json,subprocess,sys
from pathlib import Path
c=json.loads(Path(CONFIG).read_text())
assert c['database'].startswith('ism_review_test_')
root=Path(c['root']);bank=Path(c['bank']);csv=Path(c['csv'])
subprocess.run([sys.executable,str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),c['taxonomy']],check=True,capture_output=True)
script=(root/'scripts/sync-bank.sh').read_text()
setup=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv))
apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
sha=hashlib.sha256(bank.read_bytes()).hexdigest();n=len(json.loads(bank.read_text())['questions'])
sql=setup+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+sha+"',"+str(n)+",now());\nCOMMIT;"
result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',c['database']],input=sql,text=True,capture_output=True)
if result.returncode:raise RuntimeError(result.stderr)
marker=Path(c['fail_once'])
if marker.exists():
 marker.unlink()
 raise SystemExit('Intentional disposable interruption after SQL committed, before acknowledgement')
'''.replace('CONFIG',repr(str(config_path))))
  sync.chmod(0o700)
  from app.config import settings
  patch.setattr(settings,'canonical_workshop_root',str(bank_root));patch.setattr(settings,'paper_archive_root',str(output/'public/source'))
  if args.owner_ai_provisional_key:
   submitted=transition(client,did,h,'submit',version);assert submitted.status_code==200,submitted.text
   version=submitted.json()['version'];scoped_ai_review(client,did,patch,output)
   approved=transition(client,did,h,'owner-ai-review',version,**ai_flags());assert approved.status_code==200,approved.text
   version=approved.json()['version']
  elif not args.owner_decision:version,h=approve_original(client,actor,did,h,version)
  if args.owner_decision:
   preview=client.get('/api/paper-workbench/drafts/'+did+'/owner-preview');assert preview.status_code==200,preview.text
   queued=client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=h,json={'expected_version':version,'preview_hash':preview.json()['preview_hash'],'inspected':True})
  else:queued=transition(client,did,h,'publish',version)
  assert queued.status_code==202,queued.text
  from app.services.paper_jobs import once
  assert client.portal.call(once,['publish'])
  interrupted=conn.execute('SELECT state FROM paper_workbench_jobs WHERE id=%s',(queued.json()['job_id'],)).fetchone()[0]
  assert interrupted=='failed'
  first_output=hashlib.sha256(bank_path.read_bytes()).hexdigest()
  retry=client.post('/api/paper-workbench/jobs/'+queued.json()['job_id']+'/retry',headers=h,json={});assert retry.status_code==202,retry.text
  assert client.portal.call(once,['publish'])
  job=conn.execute('SELECT state,error FROM paper_workbench_jobs WHERE id=%s',(queued.json()['job_id'],)).fetchone()
  assert job[0]=='done',job
  after=get(client,did);assert after['state']=='published' and after['published_paper_id']==pid
  result=json.loads(bank_path.read_text())
  assert hashlib.sha256(bank_path.read_bytes()).hexdigest()==first_output
  assert result['papers']==bank['papers'] and result['questions'][0]==old and len(result['questions'])==3
  for pos,q in enumerate(result['questions'][1:]):
   keyed=args.owner_ai_provisional_key and pos==1
   assert q['paperId']==pid and q['answerSource']==('key'if keyed else'none') and q['answerIndex']==(0 if keyed else None)
  assert conn.execute('SELECT count(*) FROM appearances WHERE paper_id=%s',(pid,)).fetchone()[0]==2
  assert conn.execute("SELECT count(*) FROM review_documents WHERE paper_id=%s AND kind='paper'",(pid,)).fetchone()[0]==1
  if args.owner_ai_provisional_key:
   assert conn.execute("SELECT key_status FROM review_documents WHERE paper_id=%s AND kind='official-key'",(pid,)).fetchone()[0]=='provisional'
   assert after['reviews'][0]['review_kind']=='owner_ai'
   assert 'Owner-authorized AI-assisted' in result['questions'][-1]['classifications'][0]['evidence']
  assert not (bank_root/'pdfs/Old_Questions/Uploaded'/(after['source_sha256']+'.pdf')).exists()
  assert conn.execute("SELECT answer_text,answer_source FROM canonical_questions WHERE id='cq_test'").fetchone()==('B','derived')
  assert hashlib.sha256(real_bank.read_bytes()).hexdigest()==before_real
  report={'mode':'disposable local rehearsal','production_published':False,'real_independent_reviews':False,'synthetic_review_only':True,'existing_paper_id':pid,'published_paper_id':after['published_paper_id'],'paper_metadata_preserved':True,'source_registration_count':1,'uploaded_alias_created':False,'new_written':1,'new_unanswered_mcq':1,'original_question_answer_preserved':True,'worker_job':job[0],'interrupted_after_sql_commit':interrupted,'retry_reused_receipt_without_second_append':True,'normal_sync_sql_and_full_readback_passed':True,'recovery_bank_unchanged':True}
  if args.owner_decision:
   assert after['reviews'][0]['review_kind']=='owner'
   assert 'Owner paper decision' in result['questions'][-1]['classifications'][0]['evidence']
   report.update(review_kind='owner',independent_human_approval_created=False,owner_decision_attributed=True)
  if args.owner_ai_provisional_key:report.update(review_kind='owner_ai',key_status='provisional',new_unanswered_mcq=0,new_keyed_mcq=1,independent_human_approval_created=False)
  (output/'rehearsal.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 finally:
  try:next(clients)
  except StopIteration:pass
  try:next(dbs)
  except StopIteration:pass
  patch.undo()


if __name__=='__main__':main()
