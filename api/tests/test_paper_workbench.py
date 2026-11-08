"""Disposable source-first preparation and independent review boundary tests."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb

@pytest.fixture
def paper(client,actor,database,tmp_path,monkeypatch):
 from app.config import settings
 monkeypatch.setattr(settings,'paper_workbench_root',str(tmp_path))
 h=actor('owner')
 r=client.post('/api/paper-workbench/uploads',content=b'%PDF-1.4\nsynthetic fixture '+uuid4().hex.encode(),headers={**h,'content-type':'application/pdf','x-filename':'Synthetic%20paper.pdf'})
 assert r.status_code==201,r.text
 assert r.json()['filename']=='Synthetic paper.pdf'
 r=client.post('/api/paper-workbench/drafts',headers=h,json={'source_sha256':r.json()['sha256'],'title':'Synthetic paper','exam_name':'Synthetic exam','year':2020})
 assert r.status_code==201,r.text
 did=r.json()['id'];jid=r.json()['job_id'];c=database[1]
 c.execute("UPDATE paper_workbench_jobs SET state='done',result=%s WHERE id=%s",(Jsonb({'pages':2}),jid))
 c.execute('UPDATE paper_workbench_drafts SET extraction_id=%s WHERE id=%s',(jid,did))
 return did,h

def get(client,did):return client.get('/api/paper-workbench/drafts/'+did).json()
def save(client,did,h,p,version):return client.post('/api/paper-workbench/drafts/'+did+'/save',headers=h,json={'expected_version':version,'payload':p})
def prepared(client,did,h):
 d=get(client,did);p=d['payload'];p.update(identity_page=1,identity_note='Cover explicitly records the synthetic exam and 2020 sitting.',expected_questions=1,questions=[{'id':uuid4().hex,'number':'1','page':2,'question':'Choose a synthetic option.','options':['One','Two'],'subject_id':'english'}])
 r=save(client,did,h,p,d['version']);assert r.status_code==200,r.text
 return r.json()['version']
def transition(client,did,h,kind,v,**extra):return client.post('/api/paper-workbench/drafts/'+did+'/'+kind,headers=h,json={'expected_version':v,'reason':'Inspected original synthetic source and recorded the evidence.',**extra})
def assign(client,did,h,v):
 r=transition(client,did,h,'reviewer',v,email='outsider@example.test');assert r.status_code==200,r.text

def test_private_exact_assignment_and_revocation(client,actor,paper):
 did,h=paper;assign(client,did,h,1)
 actor('outsider');assert client.get('/api/paper-workbench/drafts/'+did).status_code==200
 actor('author');assert client.get('/api/paper-workbench/drafts/'+did).status_code==404
 actor('outsider');assert save(client,did,actor('outsider'),get(client,did)['payload'],1).status_code==403
 h=actor('owner');r=transition(client,did,h,'reviewer',1,email='outsider@example.test',active=False);assert r.status_code==200,r.text
 actor('outsider');assert client.get('/api/paper-workbench/drafts/'+did).status_code==404

def test_partial_draft_optimistic_lock_and_history_restore(client,actor,paper):
 did,h=paper;d=get(client,did);p=d['payload'];p['questions']=[{'id':uuid4().hex,'number':'1','page':1}]
 assert save(client,did,h,p,1).status_code==200
 assert save(client,did,h,p,1).status_code==409
 assert transition(client,did,h,'submit',2).status_code==422
 r=transition(client,did,h,'restore',2,version=1);assert r.status_code==200,r.text
 d=get(client,did);assert d['payload']['questions']==[] and d['version']==3 and len(d['history'])==3

def test_independent_review_save_invalidates_approval_and_history_immutable(client,actor,paper,database):
 did,h=paper;v=prepared(client,did,h);assign(client,did,h,v)
 r=transition(client,did,h,'submit',v);assert r.status_code==200,r.text;v=r.json()['version']
 flags=dict(source_checked=True,options_checked=True,answers_checked=True,explanations_checked=True)
 assert transition(client,did,h,'review',v,decision='approve',**flags).status_code==403
 h2=actor('outsider');assert transition(client,did,h2,'review',v,decision='approve',**{**flags,'answers_checked':False}).status_code==422
 r=transition(client,did,h2,'review',v,decision='approve',**flags);assert r.status_code==200,r.text
 h=actor('owner');d=get(client,did);p=d['payload'];p['questions'][0]['question']='A newly edited synthetic question.'
 assert save(client,did,h,p,d['version']).status_code==200
 assert transition(client,did,h,'publish',d['version']+1).status_code==409
 import psycopg
 with pytest.raises(psycopg.Error):database[1].execute('DELETE FROM paper_workbench_history WHERE draft_id=%s',(did,))

def test_processing_never_changes_manual_payload(client,actor,paper):
 did,h=paper;v=prepared(client,did,h);before=get(client,did)['payload']
 r=client.post('/api/paper-workbench/drafts/'+did+'/process',headers=h,json={'kind':'ocr','page':2,'rotation':90});assert r.status_code==202,r.text
 assert get(client,did)['payload']==before
 assert client.post('/api/paper-workbench/drafts/'+did+'/process',headers=h,json={'kind':'crop','x':.9,'width':.2}).status_code==422
 assert client.post('/api/paper-workbench/drafts/'+did+'/process',headers=h,json={'kind':'crop','rotation':90}).status_code==422
 assert client.post('/api/paper-workbench/drafts/'+did+'/save',json={'expected_version':v,'payload':before}).status_code==403

@pytest.mark.parametrize('field,value',[('expected_questions',2),('identity_page',3),('identity_note','too short')])
def test_complete_submission_requires_source_bounds_and_count(client,actor,paper,field,value):
 did,h=paper;v=prepared(client,did,h);p=get(client,did)['payload'];p[field]=value
 assert save(client,did,h,p,v).status_code==200
 assert transition(client,did,h,'submit',v+1).status_code==422

def test_cross_draft_crop_denied(client,actor,paper,database):
 did,h=paper;v=prepared(client,did,h);c=database[1];other='pwdraft_'+uuid4().hex
 c.execute("INSERT INTO paper_workbench_drafts(id,author_id,source_sha256,payload) SELECT %s,author_id,source_sha256,payload FROM paper_workbench_drafts WHERE id=%s",(other,did))
 jid='pwjob_'+uuid4().hex;c.execute("INSERT INTO paper_workbench_jobs(id,draft_id,kind,state,result) VALUES(%s,%s,'crop','done','{}')",(jid,other))
 p=get(client,did)['payload'];p['questions'][0]['figure_job']=jid
 assert save(client,did,h,p,v).status_code==422
 assert client.get('/api/paper-workbench/drafts/'+did+'/images/'+jid).status_code==404

def test_pure_append_preserves_existing_records():
 from paper_bank_store import build
 from app.routers.paper_workbench import Payload
 p=Payload(title='Synthetic paper',exam_name='Synthetic exam',year=2020,questions=[{'id':'question1','number':'1','page':1,'question':'Synthetic question','options':['One','Two'],'subject_id':'english'}]).model_dump()
 bank={'papers':[{'id':'existing'}],'questions':[{'id':'existing_question','question':'Unchanged'}]}
 out,pid,ids=build(bank,{'payload':p,'source_sha256':'a'*64,'taxonomy':[{'id':'english','label':'English'}],'taxonomy_version':'test','draft_id':'pwdraft_test','submission_id':'test'})
 assert out['papers'][0]==bank['papers'][0] and out['questions'][0]==bank['questions'][0]
 assert len(bank['questions'])==1 and len(out['questions'])==2 and out['questions'][1]['answerSource']=='none'
 with pytest.raises(ValueError):build(out,{'payload':p,'source_sha256':'a'*64})

def test_prepared_paper_receipt_survives_interruption(tmp_path,monkeypatch):
 import json,hashlib
 import paper_bank_store as store
 from review_bank_store import atomic
 from app.routers.paper_workbench import Payload
 bank=tmp_path/'bank.json';atomic(bank,{'papers':[],'questions':[]})
 p=Payload(title='Synthetic complete paper',exam_name='Synthetic exam',questions=[{'id':'question1','number':'1','page':1,'question':'Synthetic question','options':['One','Two'],'subject_id':'english'}]).model_dump()
 m={'payload':p,'source_sha256':'a'*64,'taxonomy':[{'id':'english','label':'English'}],'taxonomy_version':'test','draft_id':'pwdraft_test','submission_id':'test','payload_hash':'test'}
 monkeypatch.setattr(store,'check_candidate',lambda *args:None)
 monkeypatch.setattr(store.shutil,'disk_usage',lambda *args:type('Usage',(),{'free':20*1024**3})())
 def interrupted(*args,**kw):raise RuntimeError('synthetic crash before replacement')
 monkeypatch.setattr(store,'write_guarded',interrupted)
 receipt=tmp_path/'receipts/paper.json'
 with pytest.raises(RuntimeError):store.apply(bank,tmp_path,m,receipt)
 assert receipt.is_file() and json.loads(bank.read_text())['questions']==[]
 def write(path,out,locked=False):assert locked;atomic(path,out)
 monkeypatch.setattr(store,'write_guarded',write)
 r=store.apply(bank,tmp_path,m,receipt)
 assert hashlib.sha256(bank.read_bytes()).hexdigest()==r['output_sha256']
 assert store.apply(bank,tmp_path,m,receipt)==r and len(json.loads(bank.read_text())['questions'])==1
 m['submission_id']='another submission'
 with pytest.raises(ValueError):store.apply(bank,tmp_path,m,receipt)

def test_missing_official_key_page_rejected(client,actor,paper,database,monkeypatch):
 did,h=paper;v=prepared(client,did,h);d=get(client,did);p=d['payload']
 r=client.post('/api/paper-workbench/uploads',headers={**h,'content-type':'application/pdf'},content=b'%PDF-1.4\nsynthetic-key-file '+uuid4().hex.encode());assert r.status_code==201
 p.update(key_sha256=r.json()['sha256'],key_title='Synthetic official key',key_series='',key_status='final')
 p['questions'][0].update(answer_source='key',answer_index=0,key_page=3)
 assert save(client,did,h,p,v).status_code==200
 from app.services import paper_jobs
 monkeypatch.setattr(paper_jobs,'pdf_pages',lambda path:2)
 assert transition(client,did,h,'submit',v+1).status_code==422


def test_keyed_answer_requires_explicit_key_edition():
 from app.routers.paper_workbench import Payload
 from pydantic import ValidationError
 p=dict(title='Synthetic key edition',exam_name='Synthetic exam',key_sha256='a'*64,
        questions=[{'id':'question1','number':'1','page':1,'question':'Choose one.',
                    'options':['One','Two'],'subject_id':'english','answer_index':0,'answer_source':'key','key_page':1}])
 with pytest.raises(ValidationError,match='provisional or final'):Payload(**p)
 for status in ('provisional','final'):assert Payload(**p,key_status=status).key_status==status


@pytest.mark.parametrize('status',['provisional','final'])
def test_published_key_retains_edition_and_refuses_conflicting_retry(client,database,status):
 import asyncio
 from psycopg.rows import dict_row
 from app.routers.paper_workbench import Payload
 from app.services.paper_publish import register_key_document
 class AsyncCursor:
  def __init__(self):self.cur=database[1].cursor(row_factory=dict_row)
  async def execute(self,*args):self.cur.execute(*args)
  async def fetchone(self):return self.cur.fetchone()
 cur=AsyncCursor();sha=uuid4().hex*2
 p=Payload(title='Synthetic paper',exam_name='Synthetic exam',key_sha256=sha,key_title='Synthetic '+status+' key',key_status=status)
 asyncio.run(register_key_document(cur,'paper-test',p,'owner'))
 asyncio.run(register_key_document(cur,'paper-test',p,'owner'))
 row=database[1].execute('SELECT key_status FROM review_documents WHERE sha256=%s',(sha,)).fetchone()
 assert row[0]==status
 p.key_status='final'if status=='provisional'else'provisional'
 with pytest.raises(ValueError,match='differs from the inspected edition'):
  asyncio.run(register_key_document(cur,'paper-test',p,'owner'))
 assert database[1].execute('SELECT key_status FROM review_documents WHERE sha256=%s',(sha,)).fetchone()[0]==status


def scoped_ai_review(client,did,monkeypatch,tmp_path):
 import json
 from app.services import paper_approval
 from app.services.review_policy import digest
 d=get(client,did);path=tmp_path/'scoped-review.json'
 scope={'id':'synthetic-exact-scope','owner_id':'owner','authorization':'Synthetic owner authorization; not an independent human approval.',
        'model':'Synthetic AI model','evidence_sha256':'a'*64,
        'drafts':[{'id':did,'source_sha256':d['source_sha256'],'payload_hash':digest(d['payload'])}]}
 path.write_text(json.dumps(scope));monkeypatch.setattr(paper_approval,'SCOPE_FILE',path)
 return path


def ai_flags():return dict(decision='approve',source_checked=True,options_checked=True,answers_checked=True,explanations_checked=True)


def test_owner_ai_review_fails_closed_without_exact_scope(client,actor,paper,monkeypatch,tmp_path):
 from app.services import paper_approval
 monkeypatch.setattr(paper_approval,'SCOPE_FILE',tmp_path/'missing.json')
 did,h=paper;v=prepared(client,did,h);v=transition(client,did,h,'submit',v).json()['version']
 assert transition(client,did,h,'owner-ai-review',v,**ai_flags()).status_code==403
 assert transition(client,did,h,'review',v,**ai_flags()).status_code==403
 assert get(client,did)['state']=='review' and get(client,did)['reviews']==[]


def test_owner_ai_review_attribution_owner_boundary_and_publication(client,actor,paper,monkeypatch,tmp_path,database):
 did,h=paper;v=prepared(client,did,h);v=transition(client,did,h,'submit',v).json()['version']
 scoped_ai_review(client,did,monkeypatch,tmp_path)
 assign(client,did,h,v)
 assert transition(client,did,actor('outsider'),'owner-ai-review',v,**ai_flags()).status_code==403
 h=actor('owner');assert transition(client,did,h,'owner-ai-review',v,**{**ai_flags(),'options_checked':False}).status_code==422
 result=transition(client,did,h,'owner-ai-review',v,**ai_flags());assert result.status_code==200,result.text
 d=get(client,did);assert d['state']=='approved' and d['reviews'][0]['review_kind']=='owner_ai' and d['reviews'][0]['review_model']=='Synthetic AI model'
 assert d['history'][0]['action']=='ai_reviewed'
 result=transition(client,did,h,'publish',d['version']);assert result.status_code==202,result.text
 assert database[1].execute("SELECT review_kind,reviewer_id FROM paper_workbench_reviews WHERE draft_id=%s",(did,)).fetchone()==('owner_ai','owner')


def test_owner_ai_review_save_invalidates_and_cannot_approve_edited_payload(client,actor,paper,monkeypatch,tmp_path):
 did,h=paper;v=prepared(client,did,h);v=transition(client,did,h,'submit',v).json()['version'];scoped_ai_review(client,did,monkeypatch,tmp_path)
 assert transition(client,did,h,'owner-ai-review',v,**ai_flags()).status_code==200
 d=get(client,did);p=d['payload'];p['questions'][0]['question']='Another synthetic source question.'
 v=save(client,did,h,p,d['version']).json()['version']
 assert transition(client,did,h,'publish',v).status_code==409
 v=transition(client,did,h,'submit',v).json()['version']
 assert transition(client,did,h,'owner-ai-review',v,**ai_flags()).status_code==403


def test_owner_ai_review_cannot_replay_changed_installed_scope(client,actor,paper,monkeypatch,tmp_path):
 import json
 did,h=paper;v=prepared(client,did,h);v=transition(client,did,h,'submit',v).json()['version'];path=scoped_ai_review(client,did,monkeypatch,tmp_path)
 v=transition(client,did,h,'owner-ai-review',v,**ai_flags()).json()['version']
 scope=json.loads(path.read_text());scope['evidence_sha256']='b'*64;path.write_text(json.dumps(scope))
 assert transition(client,did,h,'publish',v).status_code==409


def test_ai_paper_classification_does_not_claim_independent_review():
 from paper_bank_store import build
 from app.routers.paper_workbench import Payload
 p=Payload(title='Synthetic paper',exam_name='Synthetic exam',questions=[{'id':'question1','number':'1','page':1,'question':'Choose one.','options':['One','Two'],'subject_id':'english'}]).model_dump()
 out,_,_=build({'papers':[],'questions':[]},{'payload':p,'source_sha256':'a'*64,'taxonomy':[{'id':'english','label':'English'}],'taxonomy_version':'test','draft_id':'pwdraft_test','submission_id':'test','review_kind':'owner_ai'})
 assert out['questions'][0]['classifications'][0]['evidence']=='Owner-authorized AI-assisted paper review test'


@pytest.fixture
def registered_empty(client,actor,paper,database):
 did,h=paper;c=database[1];pid='Old_Questions/Synthetic/'+uuid4().hex+'.pdf'
 sha=c.execute('SELECT source_sha256 FROM paper_workbench_drafts WHERE id=%s',(did,)).fetchone()[0]
 c.execute("INSERT INTO papers(id,exam_type,exam_name,paper_number,year,source_file,pdf_path) VALUES(%s,'Departmental','Synthetic exam','I',2020,%s,%s)",(pid,pid,'pdfs/'+pid))
 doc='synthetic-'+uuid4().hex
 c.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Synthetic registered original',%s,%s,'paper','test')",(doc,pid,'pdfs/'+pid,sha))
 return did,h,pid,doc


def bind_original(client,did,h):
 d=get(client,did);source=d['registered_sources'][0];p=d['payload']
 p.update(target_paper_id=source['paper_id'],target_source_version=source['source_version'],exam_name=source['exam_name'],year=source['year'],paper_subject=source['paper_subject'] or '')
 r=save(client,did,h,p,d['version']);assert r.status_code==200,r.text
 return r.json()['version']


def approve_original(client,actor,did,h,v):
 assign(client,did,h,v)
 r=transition(client,did,h,'submit',v);assert r.status_code==200,r.text
 h2=actor('outsider')
 r=transition(client,did,h2,'review',r.json()['version'],decision='approve',source_checked=True,options_checked=True,answers_checked=True,explanations_checked=True);assert r.status_code==200,r.text
 return r.json()['version'],actor('owner')


def test_registered_empty_written_source_still_needs_independent_approval(client,actor,registered_empty,database):
 did,h,pid,doc=registered_empty;prepared(client,did,h)
 d=get(client,did);p=d['payload'];p['questions'][0].update(type='descriptive',question='Write a synthetic response.',options=[])
 assert save(client,did,h,p,d['version']).status_code==200
 # Registered source IDs cannot silently become a second Uploaded paper.
 assert transition(client,did,h,'submit',get(client,did)['version']).status_code==409
 v=bind_original(client,did,h)
 assert transition(client,did,h,'publish',v).status_code==409
 r=transition(client,did,h,'submit',v);assert r.status_code==200
 flags=dict(decision='approve',source_checked=True,options_checked=True,answers_checked=True,explanations_checked=True)
 assert transition(client,did,h,'review',r.json()['version'],**flags).status_code==403
 assign(client,did,h,r.json()['version']);h2=actor('outsider')
 r=transition(client,did,h2,'review',r.json()['version'],**flags);assert r.status_code==200,r.text
 h=actor('owner');r=transition(client,did,h,'publish',r.json()['version']);assert r.status_code==202,r.text
 c=database[1]
 assert c.execute('SELECT count(*) FROM appearances WHERE paper_id=%s',(pid,)).fetchone()[0]==0
 assert c.execute('SELECT count(*) FROM review_documents WHERE id=%s',(doc,)).fetchone()[0]==1
 assert get(client,did)['payload']['target_paper_id']==pid


@pytest.mark.parametrize('change',['paper','document','ambiguous','populated','wrong-pdf'])
def test_registered_source_changed_before_submission_is_rejected(client,actor,registered_empty,database,change):
 did,h,pid,doc=registered_empty;prepared(client,did,h);v=bind_original(client,did,h);c=database[1]
 if change=='paper':c.execute("UPDATE papers SET paper_number='II' WHERE id=%s",(pid,))
 elif change=='document':c.execute("UPDATE review_documents SET title='Changed registered original' WHERE id=%s",(doc,))
 elif change=='ambiguous':c.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) SELECT %s,'paper-test',title,source_file,sha256,kind,'test' FROM review_documents WHERE id=%s",('synthetic-'+uuid4().hex,doc))
 elif change=='populated':c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum) VALUES(%s,%s,'mcq','A concurrent extraction','[]','cq_test','1')",('synthetic-'+uuid4().hex,pid))
 else:c.execute("UPDATE review_documents SET sha256=%s WHERE id=%s",('b'*64,doc))
 assert transition(client,did,h,'submit',v).status_code==409


def test_binding_and_registered_identity_cannot_be_forged(client,actor,registered_empty):
 did,h,pid,_=registered_empty;prepared(client,did,h);v=bind_original(client,did,h)
 d=get(client,did);p=d['payload'];p['target_source_version']='a'*64
 assert save(client,did,h,p,v).status_code==409
 p=d['payload'];p['target_source_version']=d['registered_sources'][0]['source_version'];p['exam_name']='Another examination'
 assert save(client,did,h,p,v).status_code==422
 p['exam_name']=d['registered_sources'][0]['exam_name'];p['target_source_version']=None
 assert save(client,did,h,p,v).status_code==422


def test_relink_after_approval_requires_another_review(client,actor,registered_empty,database):
 did,h,pid,doc=registered_empty;prepared(client,did,h);v=bind_original(client,did,h)
 v,h=approve_original(client,actor,did,h,v)
 database[1].execute("UPDATE review_documents SET title='Corrected document title' WHERE id=%s",(doc,))
 v=bind_original(client,did,h)
 assert get(client,did)['state']=='draft' and get(client,did)['submission_id'] is None
 assert transition(client,did,h,'publish',v).status_code==409


@pytest.mark.parametrize('change',['identity','populated'])
def test_registered_source_worker_rechecks_binding_after_approval(client,actor,registered_empty,database,tmp_path,monkeypatch,change):
 from pathlib import Path
 import shutil
 from fastapi import HTTPException
 from app.config import settings
 from app.services.paper_publish import publish_job
 did,h,pid,doc=registered_empty;prepared(client,did,h);v=bind_original(client,did,h);v,h=approve_original(client,actor,did,h,v)
 r=transition(client,did,h,'publish',v);assert r.status_code==202
 c=database[1];d=c.execute('SELECT to_jsonb(d) FROM paper_workbench_drafts d WHERE id=%s',(did,)).fetchone()[0]
 job=c.execute('SELECT to_jsonb(j) FROM paper_workbench_jobs j WHERE id=%s',(r.json()['job_id'],)).fetchone()[0]
 root=tmp_path/'workshop/mpsc-question-bankv2';scripts=root.parent/'india-study-map-app/scripts';scripts.mkdir(parents=True)
 shutil.copyfile(Path(__file__).resolve().parents[2]/'scripts/paper_bank_store.py',scripts/'paper_bank_store.py')
 monkeypatch.setattr(settings,'canonical_workshop_root',str(root))
 if change=='identity':
  c.execute("UPDATE papers SET paper_number='II' WHERE id=%s",(pid,))
  with pytest.raises(HTTPException,match='registered source changed'):client.portal.call(publish_job,job,d)
 else:
  c.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,qnum) VALUES(%s,%s,'mcq','A concurrent extraction','[]','cq_test','1')",('synthetic-'+uuid4().hex,pid))
  with pytest.raises(ValueError,match='no matching publication receipt'):client.portal.call(publish_job,job,d)
 assert not (root/'bank/mpsc_bank_v2.json').exists()


def existing_manifest():
 from app.routers.paper_workbench import Payload
 from app.services.review_policy import digest
 from paper_bank_store import PAPER_FIELDS
 pid='Old_Questions/Synthetic/common.pdf'
 original={'id':pid,'examType':'Departmental','examName':'Synthetic exam','year':2020,'sourceFile':pid,'paperNumber':'I','customLegacyField':{'preserve':True}}
 bank={'papers':[original,{'id':'unrelated'}],'questions':[{'id':'old-question','paperId':'unrelated','answerIndex':1,'preserve':'history'}]}
 snapshot={'paper':{column:original.get(key) for column,key in PAPER_FIELDS.items()},'documents':[{'id':'original-doc','paper_id':pid,'title':'Synthetic original','source_file':'pdfs/'+pid,'sha256':'a'*64}]}
 p=Payload(title='Synthetic common paper',exam_name='Synthetic exam',year=2020,target_paper_id=pid,target_source_version=digest(snapshot),questions=[{'id':'written01','number':'1','page':1,'type':'descriptive','question':'Write a synthetic response.','subject_id':'english'}]).model_dump()
 m={'payload':p,'source_sha256':'a'*64,'taxonomy':[{'id':'english','label':'English'}],'taxonomy_version':'test','draft_id':'pwdraft_existing','submission_id':'approved-submission','payload_hash':digest(p),'existing_source':{'paper_id':pid,'snapshot':snapshot}}
 return bank,m


def test_empty_source_build_keeps_all_paper_metadata_and_existing_records():
 import copy
 from paper_bank_store import build
 bank,m=existing_manifest();before=copy.deepcopy(bank)
 out,pid,ids=build(bank,m)
 assert bank==before and out['papers']==before['papers'] and out['questions'][:-1]==before['questions']
 assert out['questions'][-1]['paperId']==pid==m['payload']['target_paper_id']
 assert out['questions'][-1]['answerIndex'] is None and out['questions'][-1]['answerSource']=='none'
 assert len(out['papers'])==2 and not any('Uploaded/' in x['id'] for x in out['papers'])


def test_empty_source_preserves_sql_backfilled_scope_without_rewriting_legacy_json():
 from paper_bank_store import build
 from app.services.review_policy import digest
 bank,m=existing_manifest()
 m['existing_source']['snapshot']['paper']['exam_scope_id']='mizoram-recruitment'
 m['payload']['target_source_version']=digest(m['existing_source']['snapshot'])
 out,_,_=build(bank,m)
 assert out['papers']==bank['papers'] and 'examScopeId' not in out['papers'][0]
 bank['papers'][0]['examScopeId']='outside-mizoram'
 with pytest.raises(ValueError,match='metadata changed'):build(bank,m)


@pytest.mark.parametrize('change',['populated','paper','binding','missing','ambiguous','wrong-pdf','draft-identity'])
def test_empty_source_build_rejects_concurrent_changes_or_bad_binding(change):
 from paper_bank_store import build
 bank,m=existing_manifest();pid=m['payload']['target_paper_id']
 if change=='populated':bank['questions'].append({'id':'another-extraction','paperId':pid})
 elif change=='paper':bank['papers'][0]['paperNumber']='II'
 elif change=='binding':m['payload']['target_source_version']='b'*64
 elif change=='missing':bank['papers']=bank['papers'][1:]
 elif change=='ambiguous':bank['papers'].append(bank['papers'][0].copy())
 elif change=='wrong-pdf':m['source_sha256']='b'*64
 else:m['payload']['exam_name']='Another examination'
 with pytest.raises(ValueError):build(bank,m)


def test_existing_source_receipt_recovers_without_second_append(tmp_path,monkeypatch):
 import json
 import paper_bank_store as store
 from review_bank_store import atomic
 bank,m=existing_manifest();path=tmp_path/'bank.json';atomic(path,bank)
 monkeypatch.setattr(store,'check_candidate',lambda *args:None)
 monkeypatch.setattr(store.shutil,'disk_usage',lambda *args:type('Usage',(),{'free':20*1024**3})())
 def interrupted(*args,**kw):raise RuntimeError('Interrupted before replacement')
 monkeypatch.setattr(store,'write_guarded',interrupted)
 receipt=tmp_path/'receipt.json'
 with pytest.raises(RuntimeError):store.apply(path,tmp_path,m,receipt)
 assert json.loads(path.read_text())==bank
 monkeypatch.setattr(store,'write_guarded',lambda path,out,locked=False:atomic(path,out))
 result=store.apply(path,tmp_path,m,receipt)
 assert store.apply(path,tmp_path,m,receipt)==result
 after=json.loads(path.read_text());assert len(after['papers'])==len(bank['papers']) and len(after['questions'])==len(bank['questions'])+1
 m['payload']['target_paper_id']='other-paper'
 with pytest.raises(ValueError):store.apply(path,tmp_path,m,receipt)


def test_registered_original_pdf_must_match_and_stay_inside_archive(tmp_path):
 import hashlib
 from app.services.paper_publish import original_pdf
 folder=tmp_path/'pdfs';folder.mkdir();pdf=folder/'original.pdf';pdf.write_bytes(b'%PDF-synthetic-original')
 sha=hashlib.sha256(pdf.read_bytes()).hexdigest()
 assert original_pdf(tmp_path,'original.pdf',sha)==pdf
 with pytest.raises(ValueError):original_pdf(tmp_path,'original.pdf','b'*64)
 with pytest.raises(ValueError):original_pdf(tmp_path,'missing.pdf',sha)
 outside=tmp_path/'outside.pdf';outside.write_bytes(pdf.read_bytes());(folder/'link.pdf').symlink_to(outside)
 for source in ['../outside.pdf',str(outside),'link.pdf']:
  with pytest.raises(ValueError):original_pdf(tmp_path,source,sha)
