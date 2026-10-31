from test_account_hardening import headers as account_headers
"""Trusted operator authority is explicit; no community quorum is forged."""
from uuid import uuid4
import pytest
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from app.services.review_policy import Proposal,digest
from app.services import bank_review as review
from app.services.operator_maintenance import queue_source
from test_learning_workflows import official

@pytest.fixture(autouse=True)
def isolate_export_queue(database):
 conn=database[1]
 existing=conn.execute("SELECT id FROM bank_publications WHERE state='exported'").fetchall()
 for row in existing:conn.execute("UPDATE bank_publications SET state='failed' WHERE id=%s",(row[0],))
 try:yield
 finally:
  for row in existing:conn.execute("UPDATE bank_publications SET state='exported' WHERE id=%s",(row[0],))

def prepared(client,actor,database):
 q,a,p=official(database);conn=database[1];owner='owner';actor(owner)
 conn.execute("UPDATE canonical_questions SET answer_source='derived' WHERE id=%s",(q,))
 conn.execute("UPDATE appearances SET answer_source='derived' WHERE id=%s",(a,))
 doc='operator-paper-'+uuid4().hex
 conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Synthetic paper','synthetic.pdf',%s,'paper','test')",(doc,p,'b'*64))
 proposal=Proposal(kind='transcription',canonical_id=q,appearance_id=a,subject_id='english',title='Synthetic source instruction repair',patch={'direction':'Choose the best answer from the four printed options.'},rationale='Compared the synthetic source with its registered paper.',evidence=[{'kind':'paper','document_id':doc,'sha256':'b'*64,'page':1,'note':'Synthetic source evidence for isolated testing only.'}])
 async def create():
  from app.db import cursor
  async with cursor()as cur:return await review.create(cur,owner,proposal,uuid4().hex)
 c=client.portal.call(create)
 args=dict(owner=owner,cid=c['id'],payload_hash=digest(proposal.model_dump(mode='json')),paper_id=p,source_sha='b'*64,reason='Source checked against the complete synthetic registered paper.',authorization='Synthetic owner explicitly delegated this isolated rehearsal.')
 return q,a,p,c,args

def run(client,args):
 async def go():
  from app.db import cursor
  async with cursor()as cur:return await queue_source(cur,**args)
 return client.portal.call(go)

def test_operator_source_authority_idempotency_and_no_peer_approvals(client,actor,database):
 q,a,p,c,args=prepared(client,actor,database)
 result=run(client,args);assert result['state']=='exported'
 assert run(client,args)['id']==result['id']
 conn=database[1]
 assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(c['id'],)).fetchone()[0]==0
 assert conn.execute('SELECT count(*) FROM contribution_credit WHERE contribution_id=%s',(c['id'],)).fetchone()[0]==0
 async def eligibility():
  from app.db import cursor
  async with cursor()as cur:
   contribution=await review.load(cur,c['id'],'owner');revision=await review.revision(cur,contribution)
   assert await review.eligible_reviews(cur,contribution,revision)
   changed={**revision,'payload':{**revision['payload'],'title':'Tampered'}}
   assert not await review.eligible_reviews(cur,contribution,changed)
 client.portal.call(eligibility)
 # Clean queue so later tests can independently export.
 conn.execute("UPDATE bank_publications SET state='applied' WHERE id=%s",(result['id'],))

def test_operator_rejects_wrong_identity_payload_and_source(client,actor,database):
 q,a,p,c,args=prepared(client,actor,database)
 for patch in ({'owner':'reviewer1'},{'payload_hash':'0'*64},{'paper_id':'wrong'},{'source_sha':'a'*64},{'authorization':'vague'}):
  with pytest.raises(HTTPException):run(client,{**args,**patch})
 assert database[1].execute('SELECT count(*) FROM bank_publications WHERE contribution_id=%s',(c['id'],)).fetchone()[0]==0

def test_operator_rebase_only_disjoint_fields(client,actor,database):
 q,a,p,c,args=prepared(client,actor,database);conn=database[1]
 conn.execute("UPDATE appearances SET passage='New independent source context' WHERE id=%s",(a,))
 with pytest.raises(HTTPException):run(client,args)
 result=run(client,{**args,'allow_rebase':True})
 assert conn.execute('SELECT revision FROM bank_contributions WHERE id=%s',(c['id'],)).fetchone()[0]==2
 conn.execute("UPDATE bank_publications SET state='applied' WHERE id=%s",(result['id'],))
 q,a,p,c,args=prepared(client,actor,database)
 conn.execute("UPDATE appearances SET direction='A conflicting instruction change' WHERE id=%s",(a,))
 with pytest.raises(HTTPException):run(client,{**args,'allow_rebase':True})

def test_operator_publication_acknowledgment_earns_no_maintenance_credit(client,actor,database):
 import importlib.util
 from pathlib import Path
 from psycopg.rows import dict_row
 q,a,p,c,args=prepared(client,actor,database);result=run(client,args);conn=database[1]
 with conn.cursor(row_factory=dict_row)as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(result['id'],)).fetchone()
 checksum='c'*64;conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at)VALUES(%s,1,now())',(checksum,))
 spec=importlib.util.spec_from_file_location('operator_worker_test',Path(__file__).resolve().parents[2]/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
 def remote(query,json_result=False):
  with conn.cursor(row_factory=dict_row)as cur:cur.execute(query);return cur.fetchall()if json_result else ''
 worker.remote=remote
 worker.acknowledge(pub,{'output_sha256':checksum,'publication_id':pub['id'],'appearance_id':a})
 assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(c['id'],)).fetchone()[0]=='published'
 assert conn.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pub['id'],)).fetchone()[0]==0
 assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(c['id'],)).fetchone()[0]==0

def test_publication_verifier_respects_retired_canonical_difficulty():
 import importlib.util
 from pathlib import Path
 spec=importlib.util.spec_from_file_location('retired_difficulty_worker',Path(__file__).resolve().parents[2]/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
 record={'id':'synthetic-a','question':'Synthetic stem','options':['A','B'],'answerIndex':1,'explanation':None,'difficulty':'legacy-medium'}
 live={'record':record,'is_primary':True,'canonical_question':'Synthetic stem','canonical_options':['A','B'],'answer_text':'B','canonical_explanation':None,'canonical_difficulty':None,'source_defect':None}
 worker.remote=lambda query,json_result=False:[]if'question_topic_links'in query else[live]
 worker.verify_live({'appearance_id':'synthetic-a','after':record},{'payload':{'patch':{'question':'Synthetic stem'}}})

def test_paper_view_preserves_printed_context_and_reports_defects(client,actor,database):
 q,a,p=official(database);conn=database[1]
 conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,allow_browse,as_mock)VALUES('ldc',1,%s,'test',true,false)",(p,))
 conn.execute("UPDATE appearances SET question='Exact printed wording',passage='Table from this exact printing',direction='Read the printed table first' WHERE id=%s",(a,))
 conn.execute("UPDATE canonical_questions SET passage='Different canonical context',source_defect='unresolved-source',dispute_note='The source question has incompatible choices.' WHERE id=%s",(q,))
 r=client.get('/api/collections/ldc/paper-questions',params={'paper_id':p});assert r.status_code==200,r.text
 item=r.json()['items'][0]
 assert item['question']=='Exact printed wording' and item['passage']=='Table from this exact printing'
 assert item['answer_status']=='needs-review' and item['source_defect']=='unresolved-source'
 assert 'incompatible choices'in item['dispute_note'] and 'answer_index'not in item

def test_unanswered_legacy_mcq_can_receive_source_context(tmp_path):
 from review_bank_store import record,transform
 question={'id':'synthetic','paperId':'paper','type':'mcq','question':'Read the original graph','options':['A','B'],'answerIndex':-1,'answerSource':None,'hasDiagram':False}
 manifest={'id':'pub_synthetic','baseline':{'record':record(question)},'payload':{'kind':'transcription','patch':{'direction':'Use the supplied original graph to answer.'},'evidence':[]}}
 result,_=transform({'papers':[{'id':'paper'}],'questions':[question]},manifest)
 assert result['questions'][0]['answerIndex']is None
 assert result['questions'][0]['direction']=='Use the supplied original graph to answer.'

def test_sync_skips_unchanged_question_rows_but_applies_repairs(database,tmp_path):
 import json,subprocess,hashlib
 from pathlib import Path
 root=Path(__file__).resolve().parents[2];conn=database[1]
 tables=('question_classifications','question_topic_links','collection_sections')
 for table in tables:conn.execute(f'CREATE TEMP TABLE noop_preserve_{table} AS SELECT * FROM {table}')
 bank=tmp_path/'bank.json';aid='noop-source';qid='cq_'+hashlib.md5(aid.encode()).hexdigest()[:16]
 q={'id':aid,'paperId':'paper-test','type':'mcq','question':'Synthetic no-op sync question','options':['A','B'],'answerIndex':1,'answerSource':'derived','qnum':'2','page':1,'difficulty':'medium','classifications':[{'subject_id':'english','is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]}
 tax=tmp_path/'taxonomy.json';tax.write_text('{"subjects":[{"id":"english","label":"English"}]}')
 def sync():
  bank.write_text(json.dumps({'papers':[{'id':'paper-test','examType':'Direct','examName':'Synthetic paper'}],'questions':[q]}));csv=tmp_path/'csv'
  subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(tax)],check=True,capture_output=True,text=True)
  script=(root/'scripts/sync-bank.sh').read_text();prepare=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv));apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
  r=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=prepare+'\n'+apply+'\nCOMMIT;',text=True,capture_output=True);assert r.returncode==0,r.stderr
 def versions():return (conn.execute('SELECT xmin::text FROM appearances WHERE id=%s',(aid,)).fetchone()[0],conn.execute('SELECT xmin::text FROM question_classifications WHERE question_id=%s',(qid,)).fetchone()[0])
 try:
  sync();before=versions();sync();assert versions()==before
  q['direction']='New original source instructions';sync();after=versions();assert after[0]!=before[0]and after[1]==before[1]
  assert conn.execute('SELECT direction FROM canonical_questions WHERE id=%s',(qid,)).fetchone()[0]==q['direction']
  assert conn.execute('SELECT difficulty FROM canonical_questions WHERE id=%s',(qid,)).fetchone()[0]is None
 finally:
  for table in tables:
   conn.execute(f'DELETE FROM {table}');conn.execute(f'INSERT INTO {table} SELECT * FROM noop_preserve_{table}');conn.execute(f'DROP TABLE noop_preserve_{table}')

def test_mock_and_result_keep_frozen_source_figure(client,actor,database):
 from test_learning_workflows import learner
 q,a,p=official(database);conn=database[1]
 original='images/page-renders/'+'1'*64+'.png';changed='images/page-renders/'+'2'*64+'.png'
 conn.execute('UPDATE appearances SET has_diagram=true,figure_image=%s WHERE id=%s',(original,a))
 conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,allow_browse,allow_practice,as_mock)VALUES('ldc',1,%s,'test',true,true,true)",(p,))
 learner(database,actor)
 r=client.post('/api/mocks', headers=account_headers(client),json={'collection_id':'ldc','paper_id':p,'answer_mode':'official'});assert r.status_code==200,r.text
 mock=r.json();expected='/papers/figures/'+'1'*64+'.png';assert mock['questions'][0]['figure_image_url']==expected
 conn.execute('UPDATE appearances SET figure_image=%s WHERE id=%s',(changed,a))
 assert client.get('/api/mocks/current').json()['questions'][0]['figure_image_url']==expected
 result=client.post('/api/mocks/'+mock['id']+'/submit', headers=account_headers(client),json={'answers':[{'question_id':q,'chosen_index':1}]});assert result.status_code==200,result.text
 assert result.json()['n_correct']==1 and result.json()['review'][0]['figure_image_url']==expected
 assert client.get('/api/mocks/'+mock['id']).json()['review'][0]['figure_image_url']==expected

def test_staff_source_intake_keeps_learner_limit_and_requires_owner(client,actor,database):
 from app.services.operator_maintenance import intake_source
 q,a,p,c,args=prepared(client,actor,database);conn=database[1]
 payload=conn.execute('SELECT payload FROM contribution_revisions WHERE contribution_id=%s AND revision=1',(c['id'],)).fetchone()[0]
 # An owner can do bounded maintenance after the ordinary 30-submission budget.
 ids=['con_quota_'+uuid4().hex for _ in range(30)]
 for ident in ids:
  conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash)VALUES(%s,'owner',%s,%s,'source_request','english','Synthetic daily budget fixture',%s,%s)",(ident,q,a,ident,'a'*64))
 async def call(owner,authorization):
  from app.db import cursor
  async with cursor()as cur:return await intake_source(cur,owner,payload,authorization)
 try:
  result=client.portal.call(call,'owner','Owner explicitly delegated this isolated source maintenance rehearsal.')
  assert result['state']=='draft'
  assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(result['id'],)).fetchone()[0]==0
  async def ordinary():
   from app.db import cursor
   async with cursor()as cur:return await review.create(cur,'owner',Proposal.model_validate(payload),uuid4().hex)
  with pytest.raises(HTTPException)as blocked:client.portal.call(ordinary)
  assert blocked.value.status_code==429
  with pytest.raises(HTTPException)as blocked:client.portal.call(call,'reviewer1','Synthetic explicit authorization cannot grant owner permissions.')
  assert blocked.value.status_code==403
  with pytest.raises(HTTPException):client.portal.call(call,'owner','vague')
 finally:
  conn.execute('DELETE FROM bank_contributions WHERE id=ANY(%s)',(ids,))

def test_staff_intake_budget_is_bounded_and_internal_flag_cannot_grant_access(client,database):
 conn=database[1];prefix='con_staff_cap_'+uuid4().hex;ids=[prefix+str(i)for i in range(500)]
 conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash) SELECT %s||n::text,'owner','cq_test','appearance-test','source_request','english','Synthetic staff budget fixture',%s||n::text,%s FROM generate_series(0,499)n",(prefix,prefix,'a'*64))
 p=Proposal(kind='answer',canonical_id='cq_test',appearance_id='appearance-test',subject_id='english',title='Synthetic bounded administrative answer',patch={'answerIndex':1,'answerSource':'derived','explanation':'Synthetic explanation for the isolated budget test only.'},rationale='Synthetic administrative review for the isolated budget test.',evidence=[{'kind':'reasoning','note':'Synthetic reasoning for a disposable database test only.'}])
 async def create(user):
  from app.db import cursor
  async with cursor()as cur:return await review.create(cur,user,p,uuid4().hex,admin_attestation=True)
 try:
  with pytest.raises(HTTPException)as blocked:client.portal.call(create,'owner')
  assert blocked.value.status_code==429 and 'staff maintenance'in blocked.value.detail
  with pytest.raises(HTTPException)as blocked:client.portal.call(create,'author')
  assert blocked.value.status_code==403
 finally:conn.execute('DELETE FROM bank_contributions WHERE id=ANY(%s)',(ids,))
