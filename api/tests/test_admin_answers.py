from uuid import uuid4
from psycopg.types.json import Jsonb
from test_learning_workflows import official,learner
from app.services.review_policy import digest

def setup(client,actor,database):
 q,a,p=official(database);h=actor('owner');h['Idempotency-Key']=uuid4().hex
 base='/api/admin/bank/questions/'+q+'/answer-decision'
 r=client.get(base,params={'appearance_id':a});assert r.status_code==200,r.text
 payload={'appearance_id':a,'baseline_hash':r.json()['baseline_hash'],'mode':'verified','answer_index':1,'explanation':'The source and worked reasoning support option B for this synthetic question.','reason':'Administrator checked the source and the complete solution.'}
 return q,a,p,h,base,payload

def test_admin_verified_is_explicit_queued_idempotent_and_not_peer_approval(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database)
 # Existing official solution can become a directly verified unofficial solution.
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text;result=r.json()
 assert result['state']=='queued'
 assert client.post(base,headers=h,json=payload).json()['id']==result['id']
 assert client.post(base,headers=h,json={**payload,'answer_index':2}).status_code==409
 conn=database[1];cid=result['contribution_id']
 assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(cid,)).fetchone()[0]==0
 assert conn.execute('SELECT count(*) FROM contribution_credit WHERE contribution_id=%s',(cid,)).fetchone()[0]==0
 assert conn.execute('SELECT answer_source FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0]=='official'
 manifest=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(result['publication_id'],)).fetchone()[0]
 assert manifest['admin_decision']['actor_id']=='owner' and manifest['payload']['patch']['answerSource']=='derived'
 d=client.get('/api/contributions/'+cid).json();assert d['admin_decision']['mode']=='verified' and d['state']=='publishing'
 # A second pending admin write cannot race a different answer onto the queue.
 assert client.post(base,headers={**h,'Idempotency-Key':uuid4().hex},json=payload).status_code==409

def test_admin_direct_does_not_allow_unprivileged_or_missing_csrf(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database)
 assert client.post(base,headers={'Idempotency-Key':uuid4().hex},json=payload).status_code==403
 learner(database,actor);assert client.get(base).status_code==403
 actor('reviewer1');assert client.get(base).status_code==403
 h=actor('owner');assert client.post(base,headers=h,json=payload).status_code==422

def test_admin_official_requires_exact_registered_key(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);payload['mode']='official';payload['answer_index']=2
 assert client.post(base,headers=h,json=payload).status_code==422
 conn=database[1];doc='adm-key-'+uuid4().hex
 conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES(%s,%s,'Synthetic official key','synthetic.pdf',%s,'official-key','final','test')",(doc,p,'a'*64))
 payload.update(document_id=doc,key_page=1)
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
 pub=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(r.json()['publication_id'],)).fetchone()[0]
 assert pub['payload']['evidence'][0]['answer_text']=='C' and pub['payload']['evidence'][0]['printed_question']=='1'
 assert pub['payload']['patch']['answerSource']=='official'

def test_admin_review_hold_and_unsolved_and_stale_guards(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);conn=database[1]
 conn.execute('UPDATE appearances SET direction=\'Changed source context\' WHERE id=%s',(a,))
 assert client.post(base,headers=h,json=payload).status_code==409
 payload['baseline_hash']=client.get(base).json()['baseline_hash'];payload.update(mode='needs-review',answer_index=None)
 r=client.post(base,headers=h,json=payload);assert r.status_code==200 and r.json()['state']=='held',r.text
 assert conn.execute('SELECT status FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0]=='held'
 assert conn.execute('SELECT count(*) FROM bank_publications WHERE contribution_id=%s',(r.json()['contribution_id'],)).fetchone()[0]==0
 payload.update(mode='verified',answer_index=1,baseline_hash=client.get(base).json()['baseline_hash'])
 assert client.post(base,headers={**h,'Idempotency-Key':uuid4().hex},json=payload).status_code==409
 # An unheld question can be explicitly marked unanswered, without inventing a key.
 q,a,p,h,base,payload=setup(client,actor,database);payload.update(mode='unsolved',answer_index=None,explanation='')
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
 patch=conn.execute('SELECT manifest->\'payload\'->\'patch\' FROM bank_publications WHERE id=%s',(r.json()['publication_id'],)).fetchone()[0]
 assert patch['answerIndex']is None and patch['answerSource']=='none'

def test_official_key_only_keeps_audit_reason_out_of_public_explanation(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);conn=database[1];doc='key-only-'+uuid4().hex
 conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES(%s,%s,'Synthetic final key','synthetic.pdf',%s,'official-key','final','test')",(doc,p,'a'*64))
 payload.update(mode='official',document_id=doc,key_page=1,explanation='')
 response=client.post(base,headers=h,json=payload);assert response.status_code==200,response.text
 manifest=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(response.json()['publication_id'],)).fetchone()[0]
 assert manifest['payload']['patch']['explanation'] is None
 assert manifest['payload']['rationale']==payload['reason']
 assert manifest['payload']['evidence'][0]['note']==payload['reason']

def test_admin_can_attest_existing_derived_solution_without_fake_content_change(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);conn=database[1]
 explanation='Existing worked solution checked directly by the synthetic administrator.'
 conn.execute("UPDATE canonical_questions SET answer_source='derived',explanation=%s WHERE id=%s",(explanation,q))
 conn.execute("UPDATE appearances SET answer_source='derived',explanation=%s WHERE id=%s",(explanation,a))
 payload.update(explanation=explanation,baseline_hash=client.get(base).json()['baseline_hash'])
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
 cid=r.json()['contribution_id'];d=client.get('/api/contributions/'+cid).json()
 async def eligible():
  from app.db import cursor
  from app.services import bank_review
  async with cursor()as cur:
   c=await bank_review.load(cur,cid,'owner');rev=await bank_review.revision(cur,c)
   assert await bank_review.eligible_reviews(cur,c,rev)
   altered={**rev,'payload':{**rev['payload'],'rationale':'changed'}}
   assert not await bank_review.eligible_reviews(cur,c,altered)
 client.portal.call(eligible)
 assert d['admin_decision']['mode']=='verified'

def test_admin_primary_source_and_current_mock_protection(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);conn=database[1]
 alt='alt-'+uuid4().hex
 conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,type,question,options,is_primary) SELECT %s,paper_id,canonical_id,type,question,options,false FROM appearances WHERE id=%s",(alt,a))
 assert client.get(base,params={'appearance_id':alt}).status_code==409
 mid='adm-mock-'+uuid4().hex
 conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','ldc',%s,60)",(mid,[q]))
 assert client.get(base).status_code==409
 conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))

def test_direct_admin_publication_roundtrip_verifies_without_maintenance_points(client,actor,database,tmp_path,monkeypatch):
 import copy,json,subprocess,importlib.util
 from pathlib import Path
 from psycopg.rows import dict_row
 from review_bank_store import apply_manifest,sha
 qid,aid,pid,h,base,payload=setup(client,actor,database);conn=database[1];root=Path(__file__).resolve().parents[2]
 snap=client.get(base).json()['snapshot'];q=copy.deepcopy(snap['record']);classification=q.pop('classification');q['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
 bank=tmp_path/'bank.json';bank.write_text(json.dumps({'papers':[{'id':pid,'examType':'Direct','examName':'Synthetic learning workflow','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'}],'questions':[q]}))
 conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',(sha(bank),))
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text;pubid=r.json()['publication_id']
 with conn.cursor(row_factory=dict_row)as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pubid,)).fetchone()
 receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
 tax=tmp_path/'taxonomy.json';tax.write_text('{"subjects":[{"id":"english","label":"English"}]}');csv=tmp_path/'csv'
 subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(tax)],check=True,capture_output=True,text=True)
 script=(root/'scripts/sync-bank.sh').read_text();prepare=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv));apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
 sql=prepare+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+receipt['output_sha256']+"',1,now());\nCOMMIT;"
 # The production sync replaces global classification/link collections. Preserve the
 # other tests' synthetic records when rehearsing it in this shared test database.
 for table in ('question_classifications','question_topic_links','collection_sections'):
  conn.execute(f'CREATE TEMP TABLE admin_roundtrip_{table} AS SELECT * FROM {table}')
 try:
  result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True);assert result.returncode==0,result.stderr
  spec=importlib.util.spec_from_file_location('direct_admin_worker_fixture',root/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
  def remote(query,json_result=False):
   with conn.cursor(row_factory=dict_row)as cur:cur.execute(query);return cur.fetchall()if json_result else ''
  monkeypatch.setattr(worker,'remote',remote);worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt)
  assert conn.execute('SELECT answer_status FROM v_bank_answer_status WHERE id=%s',(qid,)).fetchone()[0]=='verified'
  assert client.get('/api/questions/'+qid).json()['reviewed_derived']is True
  assert conn.execute('SELECT count(*) FROM v_scorable WHERE id=%s',(qid,)).fetchone()[0]==0
  assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(pub['contribution_id'],)).fetchone()[0]==0
  assert conn.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pubid,)).fetchone()[0]==0
 finally:
  for table in ('question_classifications','question_topic_links','collection_sections'):
   conn.execute(f'DELETE FROM {table}')
   conn.execute(f'INSERT INTO {table} SELECT * FROM admin_roundtrip_{table}')
   conn.execute(f'DROP TABLE admin_roundtrip_{table}')

def test_separate_review_preserves_official_key_and_records_exact_solution(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);payload.update(preserve_official_key=True,answer_index=0)
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
 conn=database[1];m=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(r.json()['publication_id'],)).fetchone()[0]
 assert m['payload']['kind']=='explanation'and set(m['payload']['patch'])=={'explanation'}
 assert m['admin_decision']['preserve_official_key']is True and m['admin_decision']['solution_answer_text']=='A'
 assert m['payload']['evidence'][0]['answer_text']=='A'
 assert conn.execute('SELECT answer_source FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0]=='official'
 # The synthetic original answer is B; a disagreeing reviewed A holds scoring.
 assert conn.execute('SELECT status FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0]=='held'

def test_separate_review_requires_existing_official_answer(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);conn=database[1]
 conn.execute("UPDATE appearances SET answer_source='inferred' WHERE id=%s",(a,))
 payload.update(preserve_official_key=True,baseline_hash=client.get(base).json()['baseline_hash'])
 assert client.post(base,headers=h,json=payload).status_code==422

def test_agreeing_separate_review_keeps_question_live(client,actor,database):
 q,a,p,h,base,payload=setup(client,actor,database);payload.update(preserve_official_key=True,answer_index=1)
 r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
 assert database[1].execute('SELECT status FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0]=='live'

def test_answer_comparison_is_private_source_bound_and_test_protected(client,actor,database):
 q,a,p=official(database);user,h=learner(database,actor)
 url='/api/questions/'+q+'/answer-comparison'
 r=client.get(url);assert r.status_code==200,r.text
 assert r.headers['cache-control']=='private, no-store'and r.json()['official']['imported']
 assert r.json()['solution']is None
 assert client.get(url,params={'paper_id':'wrong-paper'}).status_code==404
 mid='comparison-mock-'+uuid4().hex;conn=database[1]
 conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds)VALUES(%s,%s,'ldc',%s,60)",(mid,user,[q]))
 assert client.get(url).status_code==409
 conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
 assert client.get(url).status_code==200
