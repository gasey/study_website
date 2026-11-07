from test_account_hardening import headers as account_headers
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import copy
import json
import hashlib
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.services.review_policy import Proposal,quorum,validate_target
from review_bank_store import apply_manifest,digest,record,sha


def proposal(kind='answer'):
    return {'kind':kind,'canonical_id':'cq_test','appearance_id':'appearance-test','subject_id':'english',
        'title':'Synthetic reviewed answer correction','patch':{'answerIndex':2,'answerSource':'derived','explanation':'The synthetic source supports option C.'},
        'rationale':'Independent synthetic reasoning supports correcting this answer.',
        'evidence':[{'kind':'reasoning','note':'Synthetic evidence for isolated testing only.'}]}

def create(client,actor):
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    p=proposal();r=client.post('/api/contributions',headers=h,json=p)
    assert r.status_code==201,r.text
    return r.json(),h,p

def test_strict_session_csrf_idempotency(client,actor):
    client.cookies.clear()
    assert client.get('/api/review/session',headers={'X-Device-Id':'11111111-1111-4111-8111-111111111111'}).status_code==401
    h=actor('author')
    assert client.post('/api/contributions',json=proposal()).status_code==403
    assert client.post('/api/contributions',headers={**h,'Origin':'https://evil.example'},json=proposal()).status_code==403
    c,h,p=create(client,actor)
    assert client.post('/api/contributions',headers=h,json=p).json()['id']==c['id']
    p['title']='A different idempotent payload'
    assert client.post('/api/contributions',headers=h,json=p).status_code==409
    actor('outsider')
    assert client.get('/api/contributions/'+c['id']).status_code==404
    assert client.get('/api/admin/bank/summary').status_code==403


def test_quorum_self_review_and_publication(client,actor):
    c,h,p=create(client,actor);cid=c['id']
    r=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':c['lock_version']});assert r.status_code==200,r.text
    c=r.json()
    assert client.post('/api/review/'+cid+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','reason':'I am the author and cannot approve this.'}).status_code==403
    for name,expected in [('reviewer1','in_review'),('reviewer2','accepted')]:
        h=actor(name)
        r=client.post('/api/review/'+cid+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','reason':'I checked the synthetic evidence independently.'})
        assert r.status_code==200,r.text
        c=r.json();assert c['state']==expected
    h=actor('owner')
    r=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=h,json={'expected_version':c['lock_version']})
    assert r.status_code==200,r.text
    assert r.json()['state']=='publishing'
    assert client.get('/api/community/contributors').json()==[] # acceptance alone earns nothing


def test_stale_edit_and_immutable_history(client,actor,database):
    c,h,p=create(client,actor);cid=c['id'];p['patch']['answerIndex']=0
    r=client.post('/api/contributions/'+cid+'/revisions',headers=h,json={'expected_version':1,'proposal':p})
    assert r.status_code==200,r.text
    assert r.json()['revision']==2
    assert client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':1}).status_code==409
    conn=database[1]
    with pytest.raises(Exception,match='append-only'):
        conn.execute('UPDATE contribution_revisions SET actor_id=actor_id WHERE contribution_id=%s',(cid,))


def test_subject_scope_and_revocation(client,actor,database):
    c,h,p=create(client,actor);cid=c['id']
    r=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':1});c=r.json()
    conn=database[1]
    grant=conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES ('outsider','reviewer','mizo','test','Out of scope synthetic reviewer') RETURNING id").fetchone()[0]
    try:
        h=actor('outsider')
        assert client.post('/api/review/'+cid+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','reason':'This approval is out of subject scope.'}).status_code==403
        assert client.get('/api/review/queue').json()['items']==[]
    finally:conn.execute('DELETE FROM review_grants WHERE id=%s',(grant,))


def test_bad_patch_and_official_key_rejected(client,actor):
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    p=proposal();p['patch']['status']='live'
    assert client.post('/api/contributions',headers=h,json=p).status_code==422
    p=proposal();p['patch']['answerSource']='official'
    assert client.post('/api/contributions',headers=h,json=p).status_code==422
    p=proposal();p['patch']['answerIndex']=7
    assert client.post('/api/contributions',headers=h,json=p).status_code==422


def test_hold_is_explicit_and_reversible(client,actor,database):
    h=actor('owner')
    r=client.post('/api/admin/bank/questions/cq_test/hold',headers=h,json={'reason':'Synthetic scoring hold for a reviewed defect'})
    assert r.status_code==200,r.text
    assert database[1].execute("SELECT status FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='held'
    r=client.post('/api/admin/bank/questions/cq_test/release',headers=h,json={'reason':'Synthetic defect has now been resolved'})
    assert r.status_code==200,r.text
    assert database[1].execute("SELECT status FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='live'


def synthetic_manifest(tmp_path):
    bank=tmp_path/'bank.json';q={'id':'source-1','paperId':'paper','type':'mcq','question':'Synthetic question','options':['A','B','C','D'],'answerIndex':1,'answerSource':'derived','page':1,'qnum':'1','hasDiagram':False,
      'classifications':[{'subject_id':'english','topic_id':None,'subtopic_id':None,'is_primary':True}]}
    bank.write_text(json.dumps({'papers':[{'id':'paper'}],'questions':[q]}))
    manifest={'schema':1,'id':'pub_test','contribution_id':'con_test','author_id':'test','bank_sha256':sha(bank),
        'baseline':{'record':record(q)},'payload':{'kind':'answer','patch':{'answerIndex':2,'answerSource':'derived','explanation':'A synthetic corrected explanation'},'evidence':[]},'documents':[]}
    return bank,manifest


def test_file_publication_replay_and_drift(tmp_path):
    bank,m=synthetic_manifest(tmp_path);original=bank.read_bytes()
    preview=apply_manifest(bank,tmp_path,m,digest(m),dry_run=True)
    assert bank.read_bytes()==original
    receipt=apply_manifest(bank,tmp_path,m,digest(m))
    assert json.loads(bank.read_text())['questions'][0]['answerIndex']==2
    assert apply_manifest(bank,tmp_path,m,digest(m))==receipt
    changed=json.loads(bank.read_text());changed['questions'][0]['question']='Concurrent unrelated modification';bank.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='reconciliation'):apply_manifest(bank,tmp_path,m,digest(m))


def test_missing_evidence_hash_and_unsafe_path(tmp_path):
    bank,m=synthetic_manifest(tmp_path)
    m['documents']=[{'source_file':'../escape.pdf','sha256':'b'*64}]
    with pytest.raises(ValueError,match='evidence'):apply_manifest(bank,tmp_path,m,digest(m))
    assert not (tmp_path/'bank.json.review').exists()


def test_option_remapping_requires_explicit_index():
    p=proposal();p['kind']='transcription';p['patch']={'options':['C','A','B','D']}
    parsed=Proposal.model_validate(p)
    with pytest.raises(ValueError,match='re-map'):validate_target(parsed,{'options':['A','B','C','D'],'answerIndex':1})
    assert quorum('answer',{'answerSource':'official'}, {'answerIndex':2})==(2,True)


def auth_headers(user):
    token='test-session-'+user
    return {'Cookie':'ism_session='+token,'Origin':'https://study.hawayu.in',
            'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest()}


def test_concurrent_duplicate_create_and_review_race(client,actor,database):
    h=auth_headers('author');h['Idempotency-Key']=uuid4().hex;p=proposal()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:client.post('/api/contributions',headers=h,json=p),range(2)))
    assert [r.status_code for r in responses]==[201,201]
    assert responses[0].json()['id']==responses[1].json()['id']
    c=responses[0].json();cid=c['id']
    c=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':c['lock_version']}).json()
    def decide(user):
        return client.post('/api/review/'+cid+'/decisions',headers=auth_headers(user),json={'expected_version':c['lock_version'],'decision':'approve','reason':'Independent simultaneous review of synthetic evidence.'})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(decide,['reviewer1','reviewer2']))
    assert sorted(r.status_code for r in responses)==[200,409]
    assert database[1].execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(cid,)).fetchone()[0]==1


def test_revoked_approval_prevents_export(client,actor,database):
    c,h,p=create(client,actor);cid=c['id'];c=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':1}).json()
    for user in ['reviewer1','reviewer2']:
        r=client.post('/api/review/'+cid+'/decisions',headers=auth_headers(user),json={'expected_version':c['lock_version'],'decision':'approve','reason':'Review completed before permission revocation.'});assert r.status_code==200,r.text;c=r.json()
    conn=database[1];conn.execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='reviewer1'")
    try:
        assert client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=auth_headers('owner'),json={'expected_version':c['lock_version']}).status_code==409
    finally:conn.execute("UPDATE review_grants SET revoked_at=NULL WHERE user_id='reviewer1'")


def test_private_baseline_and_active_mock_gate(client,actor,database):
    c,h,p=create(client,actor);cid=c['id']
    result=client.get('/api/contributions/'+cid,headers=auth_headers('author')).json()
    assert result['current']['baseline']['record']['answerIndex'] is None
    assert result['current']['baseline_hash']==''
    conn=database[1]
    conn.execute("INSERT INTO collections(id,title,kind) VALUES ('test-mock','Synthetic mock','exam') ON CONFLICT DO NOTHING")
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES ('active-test-mock','author','test-mock',ARRAY['cq_test'],600)")
    try:
        assert client.get('/api/review/questions/cq_test',headers=auth_headers('author')).status_code==409
        assert client.get('/api/contributions/'+cid,headers=auth_headers('author')).status_code==409
        assert client.post('/api/questions/cq_test/answer',headers=auth_headers('author'),json={'chosen_index':1}).status_code==409
    finally:conn.execute("DELETE FROM mock_sessions WHERE id='active-test-mock'")


def test_request_limit_and_unsafe_evidence(client,actor):
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    r=client.post('/api/contributions',headers=h,content='x'*65537)
    assert r.status_code==413
    p=proposal();p['evidence'][0]['url']='javascript:alert(1)'
    assert client.post('/api/contributions',headers=h,json=p).status_code==422


def test_prepared_receipt_recovers_before_file_replace(tmp_path,monkeypatch):
    import review_bank_store as store
    bank,m=synthetic_manifest(tmp_path);original=bank.read_bytes();real_atomic=store.atomic
    def crash(path,data):
        if Path(path)==bank:raise RuntimeError('Injected crash before bank replacement')
        return real_atomic(path,data)
    monkeypatch.setattr(store,'atomic',crash)
    with pytest.raises(RuntimeError):apply_manifest(bank,tmp_path,m,digest(m))
    assert bank.read_bytes()==original
    assert (tmp_path/'review-receipts/pub_test.json').exists()
    monkeypatch.setattr(store,'atomic',real_atomic)
    receipt=apply_manifest(bank,tmp_path,m,digest(m))
    assert sha(bank)==receipt['output_sha256']


def test_answer_only_sync_predicate_executes_real_sql(database):
    conn=database[1]
    text=(Path(__file__).resolve().parents[2]/'scripts/sync-bank.sh').read_text()
    start=text.index('UPDATE canonical_questions c SET\n    question = a.question')
    end=text.index(';',start)+1
    sql=text[start:end]
    conn.execute("UPDATE appearances SET answer_index=3 WHERE id='appearance-test'")
    try:
        conn.execute(sql)
        assert conn.execute("SELECT answer_text FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='D'
    finally:
        conn.execute("UPDATE appearances SET answer_index=1 WHERE id='appearance-test'")
        conn.execute(sql)


def test_complete_file_sync_receipt_credit_and_replay(client,actor,database,tmp_path,monkeypatch):
    """Real API -> reviews -> manifest -> file -> actual sync SQL -> receipt.

    Execute the worker's real acknowledgement SQL on the isolated PostgreSQL
    database. No network calls or real-bank writes occur in this test.
    """
    import importlib.util
    import subprocess
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    app_root=Path(__file__).resolve().parents[2]
    conn=database[1]
    baseline=client.get('/api/review/questions/cq_test',headers=auth_headers('owner')).json()
    q=copy.deepcopy(baseline['record']);classification=q.pop('classification')
    q['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
    bank=tmp_path/'synthetic-bank.json'
    bank.write_text(json.dumps({'papers':[{'id':'paper-test','examType':'Direct','examName':'Synthetic source paper','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'}],'questions':[q]}))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES (%s,1,now())',(sha(bank),))
    c,h,p=create(client,actor);cid=c['id'];c=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':1}).json()
    for user in ['reviewer1','reviewer2']:
        result=client.post('/api/review/'+cid+'/decisions',headers=auth_headers(user),json={'expected_version':c['lock_version'],'decision':'approve','reason':'Independent verification for the complete publication test.'});assert result.status_code==200,result.text;c=result.json()
    response=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=auth_headers('owner'),json={'expected_version':c['lock_version']});assert response.status_code==200,response.text
    pid=response.json()['id']
    with conn.cursor(row_factory=dict_row) as cur:
        pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pid,)).fetchone()
    receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
    taxonomy=tmp_path/'taxonomy.json';taxonomy.write_text(json.dumps({'subjects':[{'id':'english','label':'English'}]}))
    csv=tmp_path/'csv'
    subprocess.run([str(app_root/'api/.venv/bin/python'),str(app_root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(taxonomy)],capture_output=True,text=True,check=True)
    script=(app_root/'scripts/sync-bank.sh').read_text()
    setup=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv))
    apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
    sql=setup+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+receipt['output_sha256']+"',1,now());\nCOMMIT;"
    result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    spec=importlib.util.spec_from_file_location('review_worker',app_root/'scripts/bank-review-worker.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    def local(query,json_result=False):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            return cur.fetchall() if json_result else ''
    monkeypatch.setattr(worker,'remote',local)
    worker.verify_live(receipt,pub['manifest'])
    worker.acknowledge(pub,receipt)
    worker.acknowledge(pub,receipt) # lost response retry
    assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]=='published'
    assert conn.execute('SELECT sum(amount),count(*) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()==(10,1)
    assert conn.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',(pid+':notice',)).fetchone()[0]==1
    assert conn.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='published'",(cid,)).fetchone()[0]==1
    # A later ordinary bank sync preserves the newly published correction.
    result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=setup+'\n'+apply+'\nCOMMIT;',text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert conn.execute("SELECT answer_text FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='C'
    board=client.get('/api/community/contributors').json()
    assert board[0]['credit']==10

    # A compensating revision is reviewed and published, never a silent restore.
    response=client.post('/api/admin/bank/publications/'+pid+'/revert-proposal',headers=auth_headers('owner'),json={'expected_version':1,'reason':'The synthetic correction is reversed after checking the original reasoning.'})
    assert response.status_code==200,response.text
    reversal=response.json();rid=reversal['id']
    response=client.post('/api/contributions/'+rid+'/submit',headers=auth_headers('owner'),json={'expected_version':reversal['lock_version']})
    assert response.status_code==200,response.text
    reversal=response.json()
    for user in ['reviewer1','reviewer2']:
        response=client.post('/api/review/'+rid+'/decisions',headers=auth_headers(user),json={'expected_version':reversal['lock_version'],'decision':'approve','reason':'Independent review supports restoring the original synthetic answer.'})
        assert response.status_code==200,response.text;reversal=response.json()
    response=client.post('/api/admin/bank/contributions/'+rid+'/publish',headers=auth_headers('owner'),json={'expected_version':reversal['lock_version']})
    assert response.status_code==200,response.text
    with conn.cursor(row_factory=dict_row) as cur:
        reverse_pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(response.json()['id'],)).fetchone()
    reverse_receipt=apply_manifest(bank,tmp_path,reverse_pub['manifest'],reverse_pub['manifest_hash'])
    subprocess.run([str(app_root/'api/.venv/bin/python'),str(app_root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(taxonomy)],capture_output=True,text=True,check=True)
    sql=setup+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+reverse_receipt['output_sha256']+"',1,now());\nCOMMIT;"
    result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    worker.verify_live(reverse_receipt,reverse_pub['manifest'])
    worker.acknowledge(reverse_pub,reverse_receipt);worker.acknowledge(reverse_pub,reverse_receipt)
    assert conn.execute("SELECT answer_text FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='B'
    assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]=='reverted'
    assert conn.execute('SELECT sum(amount) FROM contribution_credit WHERE contribution_id=%s',(cid,)).fetchone()[0]==0
    assert client.get('/api/community/contributors').json()==[]


def test_original_mcq_publication_and_public_privacy(client,actor,database,tmp_path,monkeypatch):
    import importlib.util
    import subprocess
    from psycopg.rows import dict_row
    root=Path(__file__).resolve().parents[2];conn=database[1]
    snapshot=client.get('/api/review/questions/cq_test',headers=auth_headers('owner')).json()
    q=copy.deepcopy(snapshot['record']);classification=q.pop('classification')
    q['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
    bank=tmp_path/'bank.json'
    bank.write_text(json.dumps({'papers':[{'id':'paper-test','examType':'Direct','examName':'Synthetic paper','year':2020,'kind':'mcq'}],'questions':[q]}))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES (%s,1,now())',(sha(bank),))
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    payload={'kind':'new_question','subject_id':'english','title':'Synthetic original vocabulary question',
        'patch':{'question':'Which word means a synthetic demonstration?','options':['Example','Ocean','Mountain','River'],'answerIndex':0,'answerSource':'derived','explanation':'An example is a demonstration used to illustrate a concept.','classification':{'subject_id':'english'}},
        'rationale':'An original question designed to demonstrate the contribution workflow.',
        'evidence':[{'kind':'reasoning','note':'Original synthetic wording with a clear worked explanation.'}]}
    response=client.post('/api/contributions',headers=h,json=payload);assert response.status_code==201,response.text
    c=response.json();cid=c['id']
    c=client.post('/api/contributions/'+cid+'/submit',headers=h,json={'expected_version':1}).json()
    for user in ['reviewer1','reviewer2']:
        response=client.post('/api/review/'+cid+'/decisions',headers=auth_headers(user),json={'expected_version':c['lock_version'],'decision':'approve','reason':'The original synthetic question and answer are independently checked.'})
        assert response.status_code==200,response.text;c=response.json()
    response=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=auth_headers('owner'),json={'expected_version':c['lock_version']});assert response.status_code==200,response.text
    pid=response.json()['id']
    with conn.cursor(row_factory=dict_row) as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pid,)).fetchone()
    receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
    assert apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])==receipt
    taxonomy=tmp_path/'taxonomy.json';taxonomy.write_text(json.dumps({'subjects':[{'id':'english','label':'English'}]}));csv=tmp_path/'csv'
    subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(taxonomy)],capture_output=True,text=True,check=True)
    script=(root/'scripts/sync-bank.sh').read_text()
    setup=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv))
    apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
    sql=setup+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+receipt['output_sha256']+"',2,now());\nCOMMIT;"
    result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True);assert result.returncode==0,result.stderr
    spec=importlib.util.spec_from_file_location('new_mcq_worker',root/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    def local(query,json_result=False):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query);return cur.fetchall() if json_result else ''
    monkeypatch.setattr(worker,'remote',local)
    worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt);worker.acknowledge(pub,receipt)
    assert conn.execute('SELECT sum(amount),count(*) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()==(25,1)
    row=conn.execute('SELECT canonical_id FROM appearances WHERE id=%s',(receipt['appearance_id'],)).fetchone();assert row
    assert conn.execute('SELECT count(*) FROM v_scorable WHERE id=%s',(row[0],)).fetchone()[0]==0
    h=actor('author')
    assert client.post('/api/contributions/'+cid+'/vote',headers=h,json={}).status_code==403
    h=actor('outsider')
    for _ in range(2):assert client.post('/api/contributions/'+cid+'/vote',headers=h,json={}).status_code==200
    assert conn.execute('SELECT count(*) FROM contribution_votes WHERE contribution_id=%s',(cid,)).fetchone()[0]==1
    assert conn.execute('SELECT sum(amount) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()[0]==25
    h=actor('author');response=client.post('/api/contributions/visibility',headers=h,json={'public':False});assert response.status_code==200,response.text
    assert client.get('/api/community/contributors').json()==[]
    conn.execute("UPDATE users SET contribution_public=true WHERE id='author'")


def test_mock_freezes_content_key_and_duplicate_submission(client,actor,database):
    conn=database[1]
    conn.execute("INSERT INTO collections(id,title,kind,live_version) VALUES ('snapshot-test','Synthetic mock snapshot','exam',1)")
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES ('snapshot-test',1,'english','English',0,'{\"paper_ids\":[\"paper-test\"]}')")
    # Other modules add two-option questions to paper-test in this session.
    # This snapshot test changes the key to D, so pin its four-option fixture.
    conn.execute("UPDATE collection_sections SET query='{}',pins=ARRAY['cq_test'] WHERE collection_id='snapshot-test'")
    actor('outsider')
    response=client.post('/api/mocks', headers=account_headers(client),json={'collection_id':'snapshot-test','section_path':'english','count':1,'duration_minutes':20,'answer_mode':'derived-practice'})
    assert response.status_code==200,response.text
    mock=response.json();mid=mock['id'];original=mock['questions'][0]
    assert 'answer_text' not in original
    snapshot=conn.execute('SELECT snapshot FROM mock_session_questions WHERE mock_id=%s',(mid,)).fetchone()[0]
    assert snapshot['answer_text']=='B'
    conn.execute("UPDATE canonical_questions SET question='Changed after the mock started',answer_text='D' WHERE id=%s",(original['id'],))
    try:
        resumed=client.get('/api/mocks/current').json()
        assert resumed['questions'][0]['question']==original['question']
        with pytest.raises(Exception,match='immutable'):
            conn.execute("UPDATE mock_session_questions SET snapshot='{}' WHERE mock_id=%s",(mid,))
        def submit():return client.post('/api/mocks/'+mid+'/submit', headers=account_headers(client),json={'answers':[{'question_id':original['id'],'chosen_index':1}]})
        with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(lambda _:submit(),range(2)))
        assert sorted(r.status_code for r in results)==[200,409]
        result=next(r.json() for r in results if r.status_code==200)
        assert result['n_correct']==1 and result['score']==1
        assert result['review'][0]['answer_text']=='B'
        later=client.get('/api/mocks/'+mid).json()
        assert later['review'][0]['question']==original['question'] and later['review'][0]['answer_text']=='B'
        assert conn.execute('SELECT count(*) FROM attempts WHERE mock_id=%s',(mid,)).fetchone()[0]==1
    finally:
        conn.execute("UPDATE canonical_questions SET question=%s,answer_text='B' WHERE id=%s",(original['question'],original['id']))


def test_registry_bootstrap_uses_repository_taxonomy_version(tmp_path,monkeypatch):
    import importlib.util
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('registry_worker',root/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    (tmp_path/'taxonomies').mkdir();(tmp_path/'pdfs').mkdir()
    (tmp_path/'taxonomies/question-bank-v2.json').write_text(json.dumps({'taxonomy_version':'2.2','subjects':[{'id':'english','label':'English','topics':[{'id':'english/grammar','label':'Grammar'}]}]}))
    bank=tmp_path/'bank.json';bank.write_text('{"papers":[],"questions":[]}')
    calls=[];monkeypatch.setattr(worker,'BANK_ROOT',tmp_path);monkeypatch.setattr(worker,'BANK',bank);monkeypatch.setattr(worker,'remote',lambda query,*args:calls.append(query))
    worker.bootstrap(None)
    assert len(calls)==1 and "'2.2'" in calls[0] and 'english/grammar' in calls[0]


def test_legacy_reports_do_not_hold_and_require_real_publication(client,actor,database):
    conn=database[1]
    rid=conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES ('cq_test','wrong_key','author','Synthetic report for the review intake') RETURNING id").fetchone()[0]
    assert conn.execute("SELECT status FROM canonical_questions WHERE id='cq_test'").fetchone()[0]=='live'
    actor('reviewer1');items=client.get('/api/admin/bank/reports').json()
    assert any(r['id']==rid for r in items)
    actor('outsider');assert client.get('/api/admin/bank/reports').status_code==403
    h=actor('reviewer1')
    response=client.post('/api/admin/bank/reports/'+str(rid)+'/resolve',headers=h,json={'status':'fixed','publication_id':'pub_missing','reason':'A report must not be called fixed before its correction is live.'})
    assert response.status_code==422,response.text
    response=client.post('/api/admin/bank/reports/'+str(rid)+'/resolve',headers=h,json={'status':'rejected','reason':'Synthetic report is invalid after checking the source question.'})
    assert response.status_code==200,response.text
    assert conn.execute('SELECT status,resolved_by FROM content_reports WHERE id=%s',(rid,)).fetchone()==('rejected','reviewer1')
    assert conn.execute("SELECT count(*) FROM contribution_events WHERE action='legacy_report_rejected' AND detail->>'report_id'=%s",(str(rid),)).fetchone()[0]==1


def test_key_mapping_and_registered_source_fulfillment(client,actor,database):
    conn=database[1]
    conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES ('test-key','paper-test','Synthetic final key','pdfs/key.pdf',%s,'official-key','final','test'),('test-paper','paper-test','Synthetic source','pdfs/paper.pdf',%s,'paper',NULL,'test')",('b'*64,'c'*64))
    h=actor('author');h['Idempotency-Key']=uuid4().hex
    p=proposal();p['patch']['answerSource']='official'
    p['evidence']=[{'kind':'official-key','document_id':'test-key','sha256':'b'*64,'page':1,'printed_question':'1','series':None,'answer_text':'C','note':'Synthetic exact final-key mapping for option C.'}]
    response=client.post('/api/contributions',headers=h,json=p);assert response.status_code==201,response.text
    for field,value in [('sha256','d'*64),('printed_question','99'),('answer_text','D'),('series','B')]:
        invalid=copy.deepcopy(p);invalid['evidence'][0][field]=value
        response=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=invalid);assert response.status_code==422,response.text
    request={'kind':'source_request','subject_id':'english','title':'Synthetic source paper fulfillment','patch':{'paperId':'paper-test','sourceUrl':'https://example.test/paper.pdf','explanation':'Synthetic source paper for registered evidence testing.'},'rationale':'Link the requested paper to its exact registered source document.','evidence':[{'kind':'reasoning','note':'Unmapped reasoning cannot fulfill a registered source request.'}]}
    response=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=request);assert response.status_code==422,response.text
    request['evidence']=[{'kind':'paper','document_id':'test-paper','sha256':'c'*64,'page':1,'note':'Synthetic source document is registered for this exact paper.'}]
    response=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=request);assert response.status_code==201,response.text
    docs=client.get('/api/review/documents?paper_id=paper-test').json()
    assert {d['id'] for d in docs}=={'test-key','test-paper'}
    assert all('source_file' not in d for d in docs)
