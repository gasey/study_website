"""Portable queue recovery and source-conflict tests, without production/model calls."""
import importlib.util,json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('ai_queue',Path(__file__).resolve().parents[2]/'scripts/ai-question-review.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def item(qid='q'):
 snapshot={'record':{'id':'a'+qid,'paperId':'p','page':1,'qnum':'1','explanation':None,'classification':{'subject_id':'english'}},'paper':{'id':'p'},'metadata':{}}
 return {'canonical_id':qid,'appearance_id':'a'+qid,'snapshot':snapshot,'fingerprint':a.digest(snapshot),'document':{'id':'doc','sha256':'a'*64},'popular_score':0,'hot':False}

def prepared(tmp_path):
 q=a.Queue(tmp_path);source=item();q.refresh({'collection_id':'combined-prelims','items':[source]});row=q.claim('combined-prelims',5)[0]
 draft={'explanation':'The correct answer follows from the inspected arithmetic.','model':'test-drafter','evidence':[]};q.draft('q',row['claim'],draft)
 check={'draft_sha256':a.digest(draft),'source_fingerprint':source['fingerprint'],'source_inspected':True,'options_checked':True,'reasoning_checked':True,'exam_date_checked':True,'checker':'test-checker','notes':'Inspected the exact source and independently recomputed the complete arithmetic.','evidence':[{'kind':'reasoning','note':'Executable arithmetic: assert 2+2==4. No external factual claim.'}]}
 q.check('q',row['claim'],check);return q,row,source,draft

def test_resume_rotates_claim_and_preserves_draft(tmp_path):
 q,row,source,draft=prepared(tmp_path);resumed=q.claim('combined-prelims',5)[0]
 assert resumed['claim']!=row['claim'] and json.loads(resumed['draft'])==draft
 with pytest.raises(ValueError,match='Stale'):q.item('q',row['claim'])
 q.refresh({'collection_id':'combined-prelims','items':[]});assert q.item('q',resumed['claim'])['status']=='checked'

def test_concurrent_human_edit_stops_publication(tmp_path):
 q,row,source,draft=prepared(tmp_path)
 with pytest.raises(ValueError,match='Source changed'):a.publish(q,'q',row['claim'],transport=lambda d:{'fingerprint':'changed'})
 assert q.db.execute("SELECT status FROM items WHERE id='q'").fetchone()[0]=='stale'
 assert not q.packet()

def test_publication_ack_retry_does_not_resubmit(tmp_path):
 q,row,source,draft=prepared(tmp_path);calls=[]
 def transport(d):
  if d['operation']=='source':return {'fingerprint':source['fingerprint']}
  snap=json.loads(json.dumps(source['snapshot']));snap['record']['explanation']=draft['explanation']
  return {'publication':{'id':'pub','state':'applied'},'snapshot':snap}
 def maintenance(request):calls.append(request);return {'publications':[{'id':'pub','state':'exported'}]}
 result=a.publish(q,'q',row['claim'],transport=transport,maintenance=maintenance)
 assert result['state']=='applied' and len(calls)==1 and not q.packet()
 assert calls[0]['items'][0]['proposal']['patch']=={'explanation':draft['explanation']}

def test_uncertain_submission_reconciles_original(tmp_path):
 q,row,source,draft=prepared(tmp_path)
 def transport(d):
  if d['operation']=='source':return {'fingerprint':source['fingerprint']}
  if d['operation']=='reconcile':return {'publications':[{'id':'pub','state':'exported'}]}
  return {'publication':{'id':'pub','state':'exported'},'snapshot':source['snapshot']}
 def fail(request):raise TimeoutError('network lost after commit')
 with pytest.raises(TimeoutError):a.publish(q,'q',row['claim'],transport=transport,maintenance=fail)
 assert q.item('q',row['claim'])['status']=='submitting'
 assert a.publish(q,'q',row['claim'],transport=transport,maintenance=lambda r:pytest.fail('resubmitted'))['publication_id']=='pub'

def test_no_model_billing_fallback(tmp_path):
 q,row,source,draft=prepared(tmp_path)
 with pytest.raises(ValueError,match='subscription'):a.opencode_draft(q,'q',row['claim'],'opencode/gpt-6-luna')

def test_bad_check_and_changed_draft_rejected(tmp_path):
 q,row,source,draft=prepared(tmp_path)
 with pytest.raises(ValueError):q.check('q',row['claim'],{})
 with pytest.raises(ValueError):q.draft('q',row['claim'],draft)

def test_oldest_two_and_priority(tmp_path):
 q=a.Queue(tmp_path);items=[item(str(i)) for i in range(12)];items[-1]['popular_score']=20
 q.refresh({'collection_id':'combined-prelims','items':items});rows=q.claim('combined-prelims',10)
 ids={r['id'] for r in rows};assert {'0','1','11'}<=ids and len(ids)==10

def test_batch_guard_checks_oracle_and_fails_closed(monkeypatch):
 import types
 spec=importlib.util.spec_from_file_location('maintenance_guard',Path(__file__).resolve().parents[2]/'scripts/owner-bank-maintenance.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 called=[]
 def run(args,**kwargs):called.append(args);return types.SimpleNamespace(stdout='active\ninactive\n',returncode=0)
 monkeypatch.setattr(guard.subprocess,'run',run)
 guard.require_batch_worker_idle({'operation':'source-batch','items':[{}]});assert not called
 with pytest.raises(ValueError,match='Oracle publisher'):guard.require_batch_worker_idle({'operation':'source-batch','items':[{},{}]})
 assert 'ssh'==called[0][0] and 'ism-oracle-bank-review.timer' in called[0][-1]
 monkeypatch.setattr(guard.subprocess,'run',lambda *a,**k:types.SimpleNamespace(stdout='',returncode=255))
 with pytest.raises(ValueError,match='Cannot establish'):guard.require_batch_worker_idle({'operation':'source-batch','items':[{},{}]})

def test_go_runner_is_stateless_and_requires_subscription_billing(tmp_path,monkeypatch):
 import types
 q=a.Queue(tmp_path);source=item();q.refresh({'collection_id':'combined-prelims','items':[source]});row=q.claim('combined-prelims',5)[0]
 context=q.immutable('context',{'text':'Inspected synthetic PDF context.'})
 with q.db:q.db.execute('UPDATE items SET context_data=? WHERE id=?',(context,'q'))
 monkeypatch.setattr(a.subprocess,'run',lambda *args,**kw:types.SimpleNamespace(returncode=0,stdout='opencode/glm-5.3-flash\n'))
 calls=[]
 def request(body,session,key):
  calls.append(body);assert key=='test-only-key' and session==row['packet'];assert 'tools' not in body
  prompt=json.dumps(body,ensure_ascii=False)
  assert 'no minimum word count' in prompt and '80–130' not in prompt
  assert 'current primary evidence is supplied' in prompt
  return {'usage':{'cost':0,'opencode':{'billing_source':'go'}},'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'explanation':'A bounded source-grounded synthetic explanation.','model':'test','evidence':[]})}}]}
 r=a.opencode_draft(q,'q',row['claim'],'opencode-go/glm-5.3-flash',requester=request,key_loader=lambda:'test-only-key')
 assert r['billing_source']=='go' and len(calls)==1 and q.item('q',row['claim'])['draft_attempts']==1
 def paid(*args):return {'usage':{'cost':0.01,'opencode':{'billing_source':'balance'}}}
 with pytest.raises(ValueError,match='subscription-only'):a.opencode_draft(q,'q',row['claim'],'opencode-go/glm-5.3-flash',requester=paid,key_loader=lambda:'test-only-key')
 with pytest.raises(ValueError,match='billing is blocked'):a.opencode_draft(q,'q',row['claim'],'opencode-go/glm-5.3-flash',requester=request,key_loader=lambda:'test-only-key')


def test_not_needed_is_source_bound_and_does_not_publish(tmp_path):
 q=a.Queue(tmp_path);source=item();q.refresh({'collection_id':'combined-prelims','items':[source]});row=q.claim('combined-prelims',5)[0]
 reason='Direct supported recall; extra explanation would merely repeat the selected answer.'
 with pytest.raises(ValueError,match='Inspect the source'):q.not_needed('q',row['claim'],reason)
 context=q.immutable('context',{'text':'Synthetic inspected source.'})
 with q.db:q.db.execute('UPDATE items SET context_data=? WHERE id=?',(context,'q'))
 with pytest.raises(ValueError,match='Source changed'):q.not_needed('q',row['claim'],reason,transport=lambda d:{'fingerprint':'changed'})
 with pytest.raises(ValueError,match='ineligible'):q.not_needed('q',row['claim'],reason,transport=lambda d:{'fingerprint':source['fingerprint'],'eligible':False})
 assert q.item('q',row['claim'])['status']=='claimed'
 q.not_needed('q',row['claim'],reason,transport=lambda d:{'fingerprint':source['fingerprint']})
 assert not q.packet()
 r=q.db.execute("SELECT * FROM items WHERE id='q'").fetchone()
 assert r['status']=='not-needed' and r['publication'] is None and r['draft'] is None
 q.refresh({'collection_id':'combined-prelims','items':[source]})
 assert q.db.execute("SELECT status FROM items WHERE id='q'").fetchone()[0]=='not-needed'
 changed=item();changed['fingerprint']='new-source'
 q.refresh({'collection_id':'combined-prelims','items':[changed]})
 assert q.db.execute("SELECT status FROM items WHERE id='q'").fetchone()[0]=='pending'


def test_not_needed_cannot_abandon_checked_or_publishing_work(tmp_path):
 q,row,source,draft=prepared(tmp_path)
 with pytest.raises(ValueError,match='claimed item'):q.not_needed('q',row['claim'],'A substantive explanation disposition must not erase a checked draft.')
 assert q.item('q',row['claim'])['status']=='checked'


def remote_adapter():
 spec=importlib.util.spec_from_file_location('ai_remote_test',Path(__file__).resolve().parents[2]/'scripts/ai-review-remote.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.mark.parametrize('staff',[500,None])
def test_audit_reads_installed_limit_instead_of_copying_it(staff):
 source="async def create():\n await cur.execute(\"SELECT count(*)::int AS n FROM bank_contributions c WHERE c.author_id=%s AND c.created_at>now()-interval '1 day'\",(actor,))\n limit="+repr(staff)+" if admin_attestation else 30\n"
 sql,actual,learner=remote_adapter().allowance_policy(source)
 assert actual==staff and learner==30 and 'c.author_id=%s' in sql
 with pytest.raises(ValueError):remote_adapter().allowance_policy(source.replace('if admin_attestation','if unknown_flag'))
 with pytest.raises(ValueError):remote_adapter().allowance_policy(source.replace(repr(staff)+' if','dynamic_limit if'))


def test_remote_audit_uses_exact_writer_counter(client,actor,database):
 import inspect
 from uuid import uuid4
 from psycopg.types.json import Jsonb
 from test_learning_workflows import official
 from app.services import bank_review
 sql,staff,learner=remote_adapter().allowance_policy(inspect.getsource(bank_review.create))
 q,appearance,_=official(database);actor('owner');conn=database[1];prefix='audit_budget_'+uuid4().hex
 before=conn.execute(sql,('owner',)).fetchone()[0]
 conn.execute("INSERT INTO bank_contributions(id,author_id,canonical_id,appearance_id,kind,subject_id,title,idempotency_key,request_hash) SELECT %s||n::text,'owner',%s,%s,'taxonomy','english','Synthetic audit budget',%s||n::text,%s FROM generate_series(0,2)n",(prefix,q,appearance,prefix,'a'*64))
 detail=Jsonb({'owner_id':'owner','run_id':prefix})
 try:
  assert conn.execute(sql,('owner',)).fetchone()[0]==before+3
  conn.execute("INSERT INTO contribution_events(contribution_id,actor_id,action,detail) VALUES (%s,'operator:owner-source-maintenance','operator_taxonomy_authorization',%s)",(prefix+'0',detail))
  conn.execute("INSERT INTO contribution_events(contribution_id,actor_id,action,detail) VALUES (%s,'operator:owner-source-maintenance','owner_maintenance_quota_exemption',%s)",(prefix+'0',detail))
  assert conn.execute(sql,('owner',)).fetchone()[0]==before+2
 finally:
  conn.execute("UPDATE bank_contributions SET created_at=now()-interval '2 days' WHERE id LIKE %s",(prefix+'%',))
