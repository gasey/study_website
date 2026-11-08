from uuid import uuid4
from pathlib import Path
import importlib.util
import pytest
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from test_admin_workbench import workbench
from test_editorial_assignments import source


def edit_body(client,qid,aid,kind='taxonomy',patch=None):
    snap=client.get('/api/review/questions/'+qid,params={'appearance_id':aid}).json()
    return {'proposal':{'kind':kind,'canonical_id':qid,'appearance_id':aid,
      'subject_id':'mizo' if kind=='taxonomy' else snap['record']['classification']['subject_id'],
      'title':'An explicitly inspected admin correction','patch':patch or {'classification':{'subject_id':'mizo'},'relatedClassifications':[]},
      'rationale':'Inspected the source wording; this path fits the actual content.',
      'evidence':[{'kind':'reasoning','note':'Inspected the source wording and the proposed subject.'}]},
      'baseline_hash':snap['edit_hash'],'source_version':snap['baseline_token'],'report_ids':[]}


def worker_fixture(monkeypatch,conn):
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('simplification_worker',root/'scripts/bank-review-worker.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    def remote(sql,json_result=False):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return cur.fetchall() if json_result else ''
    monkeypatch.setattr(worker,'remote',remote)
    return worker


def test_admin_edit_is_final_idempotent_no_peer_review_and_scoped(client,actor,workbench,database,monkeypatch):
    ids,paper,alt=workbench;q=ids['unverified'];conn=database[1]
    h=actor('owner');h['Idempotency-Key']=uuid4().hex
    body=edit_body(client,q,'app-'+q)
    r=client.post('/api/admin/bank/edits',headers=h,json=body);assert r.status_code==200,r.text
    result=r.json();cid=result['contribution_id']
    assert result['publication']['state']=='publishing'
    assert client.post('/api/admin/bank/edits',headers=h,json=body).json()['decision_id']==result['decision_id']
    assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(cid,)).fetchone()[0]==0
    assert conn.execute('SELECT subject_id FROM question_classifications WHERE question_id=%s',(q,)).fetchone()[0]=='english'
    assert client.get('/api/contributions/'+cid).json()['admin_decision']['mode']=='taxonomy'
    assert client.post('/api/admin/bank/edits',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==409
    h2=actor('reviewer1');h2['Idempotency-Key']=uuid4().hex
    assert client.post('/api/admin/bank/edits',headers=h2,json=edit_body(client,ids['missing'],'app-'+ids['missing'])).status_code==403
    # A subject publisher cannot cross into a subject they cannot publish.
    gid=conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES('reviewer1','publisher','english','test','Isolated subject publisher') RETURNING id").fetchone()[0]
    try:assert client.post('/api/admin/bank/edits',headers=h2,json=edit_body(client,ids['missing'],'app-'+ids['missing'])).status_code==403
    finally:conn.execute('DELETE FROM review_grants WHERE id=%s',(gid,))
    worker=worker_fixture(monkeypatch,conn)
    with conn.cursor(row_factory=dict_row) as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE contribution_id=%s',(cid,)).fetchone()
    worker.validate_admin_authority(pub)
    # Queued jobs recheck the exact payload and current authority before application.
    bad={**pub,'manifest':{**pub['manifest'],'payload':{**pub['manifest']['payload'],'rationale':'Tampered rationale'}}}
    with pytest.raises(ValueError):worker.validate_admin_authority(bad)
    revoked=conn.execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='owner' AND revoked_at IS NULL RETURNING id").fetchall()
    try:
        with pytest.raises(ValueError,match='permission'):worker.validate_admin_authority(pub)
    finally:
        for g in revoked:conn.execute('UPDATE review_grants SET revoked_at=NULL WHERE id=%s',g)


def test_final_bulk_is_atomic_and_replay_safe(client,actor,workbench,database):
    ids,_,_=workbench;h=actor('owner');targets=[ids['missing'],ids['unverified']]
    preview=client.post('/api/admin/bank/retag/preview',headers=h,json={'targets':[{'question_id':q,'appearance_id':'app-'+q} for q in targets]})
    assert preview.status_code==200,preview.text
    body={'targets':[{k:p[k] for k in ('question_id','appearance_id','baseline_hash','source_version')} for p in preview.json()['items']],
      'classification':{'subject_id':'mizo'},'operation':'replace_primary','reason':'Source wording supports this subject for every selected question.'}
    bad={**body,'targets':[{**t,'source_version':'0'*64} if i==1 else t for i,t in enumerate(body['targets'])]}
    h['Idempotency-Key']=uuid4().hex
    assert client.post('/api/admin/bank/retag/apply',headers=h,json=bad).status_code==409
    assert database[1].execute('SELECT count(*) FROM admin_bank_decisions WHERE canonical_id=ANY(%s)',(targets,)).fetchone()[0]==0
    r=client.post('/api/admin/bank/retag/apply',headers=h,json=body);assert r.status_code==200,r.text
    assert len(r.json()['contribution_ids'])==2
    assert client.post('/api/admin/bank/retag/apply',headers=h,json=body).json()['id']==r.json()['id']
    assert all(i['state']=='publishing' for i in client.get('/api/admin/bank/retag/batches/'+r.json()['id']).json()['items'])


def test_issue_filters_counts_scope_missing_and_invalid_paths(client,actor,workbench,database):
    ids,paper,_=workbench;conn=database[1];actor('owner')
    conn.execute('DELETE FROM question_classifications WHERE question_id=%s',(ids['missing'],))
    conn.execute("UPDATE question_classifications SET topic_id='missing-node' WHERE question_id=%s",(ids['unverified'],))
    conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'subject','author','Wrong topic reported by a learner')",(ids['keyed'],))
    for issue,expected in [('no-subject',[ids['missing']]),('reported',[ids['keyed']]),('invalid',[ids['unverified']])]:
        r=client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':issue});assert r.status_code==200,r.text
        assert r.json()['total']==len(expected) and [q['id'] for q in r.json()['items']]==expected
        assert 'answerIndex' not in r.text and 'answer_text' not in r.text
    first=client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'all','limit':2}).json()
    second=client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'all','limit':2,'offset':2}).json()
    assert first['total']==second['total']==8
    assert not {q['id'] for q in first['items']}&{q['id'] for q in second['items']}
    actor('reviewer1');scoped=client.get('/api/admin/bank/tag-issues',params={'paper':paper,'issue':'all'}).json()
    assert ids['missing'] not in {q['id'] for q in scoped['items']} and ids['restricted'] not in {q['id'] for q in scoped['items']}
    actor('outsider');assert client.get('/api/admin/bank/tag-issues').status_code==403


def test_report_links_only_resolve_matching_applied_correction_and_no_credit(client,actor,workbench,database,monkeypatch,tmp_path):
    import copy,json
    from review_bank_store import apply_manifest,sha
    ids,_,_=workbench;q=ids['unverified'];conn=database[1];h=actor('owner');h['Idempotency-Key']=uuid4().hex
    conn.execute("UPDATE canonical_questions SET direction='Choose one option',question_markup='**Synthetic repair**' WHERE id=%s",(q,))
    rid=conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'subject','author','Inspect tags') RETURNING id",(q,)).fetchone()[0]
    other=conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'wrong_key','author','Inspect answer') RETURNING id",(q,)).fetchone()[0]
    body=edit_body(client,q,'app-'+q);body['report_ids']=[other]
    assert client.post('/api/admin/bank/edits',headers=h,json=body).status_code==422
    # Isolated JSON roundtrip; production bank is never opened or mutated.
    snap=client.get('/api/review/questions/'+q,params={'appearance_id':'app-'+q}).json();record=copy.deepcopy(snap['record']);classification=record.pop('classification')
    record['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
    bank=tmp_path/'bank.json';bank.write_text(json.dumps({'papers':[{'id':record['paperId'],'examType':'Direct','examName':'Synthetic repair paper','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'}],'questions':[record]}))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',(sha(bank),))
    body['report_ids']=[rid];r=client.post('/api/admin/bank/edits',headers=h,json=body);assert r.status_code==200,r.text
    pubid=r.json()['publication']['id'];assert conn.execute('SELECT status FROM content_reports WHERE id=%s',(rid,)).fetchone()[0]=='open'
    with conn.cursor(row_factory=dict_row) as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pubid,)).fetchone()
    worker=worker_fixture(monkeypatch,conn);worker.validate_admin_authority(pub)
    receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
    assert json.loads(bank.read_text())['questions'][0]['classifications'][0]['subject_id']=='mizo'
    # Emulate only this isolated sync's changed taxonomy row; worker readback must match.
    conn.execute("UPDATE question_classifications SET subject_id='mizo',subject_label='Mizo',topic_id=NULL,subtopic_id=NULL WHERE question_id=%s",(q,))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',(receipt['output_sha256'],))
    worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt);worker.acknowledge(pub,receipt)
    assert conn.execute('SELECT status FROM content_reports WHERE id=%s',(rid,)).fetchone()[0]=='fixed'
    assert conn.execute('SELECT status FROM content_reports WHERE id=%s',(other,)).fetchone()[0]=='open'
    assert conn.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pubid,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM contribution_events WHERE action='linked_report_fixed' AND detail->>'publication_id'=%s",(pubid,)).fetchone()[0]==1


def test_quick_inspection_truthful_no_note_and_tag_only_keeps_content_checks(client,actor,source,database):
    pid,qid,appearance=source;h=actor('owner');conn=database[1]
    invite=client.post('/api/editorial/assignments',headers=h,json={'email':'outsider@example.test','collection_id':'udc','reason':'Exact isolated source inspection assignment.'}).json()
    aid=invite['id'];client.post('/api/editorial/assignments/'+aid+'/activate',headers=h,json={'expected_version':invite['version'],'reason':'Activate this exact isolated reviewer.'})
    h=actor('outsider');snap=client.get('/api/review/questions/'+qid,params={'appearance_id':appearance}).json()
    body={'appearance_id':appearance,'source_version':snap['baseline_token'],'inspection_version':snap['inspection_version'],'attestation':'source-review-v1','outcome':'checked','note':''}
    r=client.post('/api/editorial/assignments/'+aid+'/quick-checks',headers=h,json=body);assert r.status_code==200,r.text
    row=conn.execute('SELECT note,attestation,fingerprints FROM editorial_checks WHERE id=%s',(r.json()['id'],)).fetchone()
    assert row[0]=='' and row[1].startswith('I compared') and row[2]['v']==1
    conn.execute("UPDATE question_classifications SET topic_id='english/tag-only-test' WHERE question_id=%s",(qid,))
    qs=client.get('/api/editorial/assignments/'+aid+'/questions',params={'paper':pid}).json()['items'];assert qs[0]['previous_check']['stale'] is False
    current=client.get('/api/review/questions/'+qid,params={'appearance_id':appearance}).json()
    current_body={**body,'source_version':current['baseline_token'],'inspection_version':current['inspection_version']}
    conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Changed evidence','Old_Questions/test.pdf',%s,'paper','test')",('proof-'+uuid4().hex,pid,'e'*64))
    changed=client.post('/api/editorial/assignments/'+aid+'/quick-checks',headers=h,json=current_body)
    assert changed.status_code==409 and 'evidence changed' in changed.json()['detail']
    conn.execute("UPDATE appearances SET options=%s WHERE id=%s",(Jsonb(['Changed','B','C','D']),appearance))
    qs=client.get('/api/editorial/assignments/'+aid+'/questions',params={'paper':pid}).json()['items'];assert set(qs[0]['previous_check']['changed_aspects'])=={'source','answer','explanation'}
    assert client.post('/api/editorial/assignments/'+aid+'/quick-checks',headers=h,json=body).status_code==409
    # Final admin decisions remain unavailable to this assigned editor.
    assert client.get('/api/review/questions/'+qid).json()['can_publish'] is False


def test_public_tag_report_is_deduplicated_and_enters_admin_queue(client,actor,workbench,database):
    ids,paper,_=workbench;q=ids['unverified'];h=actor('author')
    body={'appearance_id':'app-'+q,'note':'This question appears to have an incorrect learning subject.'}
    r=client.post('/api/review/questions/'+q+'/tag-report',headers=h,json=body);assert r.status_code==200,r.text
    assert client.post('/api/review/questions/'+q+'/tag-report',headers=h,json=body).json()['id']==r.json()['id']
    assert database[1].execute("SELECT count(*) FROM content_reports WHERE canonical_id=%s AND kind='subject'",(q,)).fetchone()[0]==1
    assert client.get('/api/admin/bank/editorial-inbox').status_code==403
    actor('owner');items=client.get('/api/admin/bank/tag-issues',params={'issue':'reported','paper':paper}).json()['items']
    assert len(items)==1 and items[0]['report_count']==1
    assert database[1].execute('SELECT subject_id FROM question_classifications WHERE question_id=%s',(q,)).fetchone()[0]=='english'


def test_approve_publish_combines_last_step_without_lowering_public_quorum(client,actor,workbench,database):
    from test_bank_review import proposal
    ids,_,_=workbench;q=ids['unverified'];h=actor('author');h['Idempotency-Key']=uuid4().hex
    p=proposal();p.update(canonical_id=q,appearance_id='app-'+q)
    c=client.post('/api/contributions',headers=h,json=p).json()
    r=client.post('/api/contributions/'+c['id']+'/submit',headers=h,json={'expected_version':c['lock_version']});assert r.status_code==200,r.text;c=r.json()
    assert client.post('/api/review/'+c['id']+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','publish':True,'reason':'Authors cannot approve their own submissions.'}).status_code==403
    h=actor('owner')
    r=client.post('/api/review/'+c['id']+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','publish':True,'reason':'Checked the proposed answer against the supplied evidence.'})
    assert r.status_code==200,r.text;c=r.json();assert c['state']=='in_review'
    assert database[1].execute('SELECT count(*) FROM bank_publications WHERE contribution_id=%s',(c['id'],)).fetchone()[0]==0
    gid=database[1].execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES('reviewer1','publisher','english','test','Synthetic combined review and publication') RETURNING id").fetchone()[0]
    try:
        h=actor('reviewer1');r=client.post('/api/review/'+c['id']+'/decisions',headers=h,json={'expected_version':c['lock_version'],'decision':'approve','publish':True,'reason':'Second independent review confirms this exact answer revision.'})
        assert r.status_code==200,r.text;assert r.json()['state']=='publishing' and r.json()['publication_id']
    finally:database[1].execute('DELETE FROM review_grants WHERE id=%s',(gid,))


def test_new_admin_path_keeps_mfa_csrf_and_answer_mapping_guards(client,actor,workbench,database,monkeypatch):
    from app.config import settings
    ids,_,alt=workbench;q=ids['unverified'];h=actor('owner');h['Idempotency-Key']=uuid4().hex
    body=edit_body(client,q,'app-'+q)
    assert client.post('/api/admin/bank/edits',headers={'Idempotency-Key':h['Idempotency-Key']},json=body).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.post('/api/admin/bank/edits',headers=h,json=body).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    body=edit_body(client,q,'app-'+q,'transcription',{'answerIndex':2})
    assert client.post('/api/admin/bank/edits',headers=h,json=body).status_code==422
    body=edit_body(client,q,alt,'transcription',{'options':['X','A','B','D'],'answerIndex':0,'explanation':'A different answer requires checking the primary shared source.'})
    assert client.post('/api/admin/bank/edits',headers=h,json=body).status_code==409
    keyed=ids['keyed'];body=edit_body(client,keyed,'app-'+keyed,'transcription',{'options':['A','Changed B','C','D'],'answerIndex':1,'explanation':'The exact official key is still required for this changed option.'})
    assert client.post('/api/admin/bank/edits',headers=h,json=body).status_code==422
    assert database[1].execute('SELECT count(*) FROM admin_bank_decisions WHERE canonical_id=ANY(%s)',([q,keyed],)).fetchone()[0]==0


def test_bulk_worker_publishes_one_snapshot_and_resumes_failed_sync(client,actor,workbench,database,monkeypatch,tmp_path):
    import copy,json
    from review_bank_store import sha
    ids,paper,_=workbench;targets=[ids['missing'],ids['unverified']];conn=database[1];h=actor('owner')
    conn.execute("UPDATE canonical_questions SET direction='Choose one option',question_markup='**Synthetic repair**' WHERE id=ANY(%s)",(targets,))
    records=[]
    for q in targets:
        snap=client.get('/api/review/questions/'+q,params={'appearance_id':'app-'+q}).json()
        record=copy.deepcopy(snap['record']);classification=record.pop('classification')
        record['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
        records.append(record)
    bank=tmp_path/'bank.json';bank.write_text(json.dumps({'papers':[{'id':paper,'examType':'Direct','examName':'Synthetic repair paper','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'}],'questions':records}))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,2,now())',(sha(bank),))
    preview=client.post('/api/admin/bank/retag/preview',headers=h,json={'targets':[{'question_id':q,'appearance_id':'app-'+q} for q in targets]}).json()['items']
    body={'targets':[{k:p[k] for k in ('question_id','appearance_id','baseline_hash','source_version')} for p in preview],
      'classification':{'subject_id':'mizo'},'operation':'replace_primary','reason':'Inspected every selected source; Mizo fits both questions.'}
    r=client.post('/api/admin/bank/retag/apply',headers={**h,'Idempotency-Key':uuid4().hex},json=body);assert r.status_code==200,r.text
    bid=r.json()['id'];cids=r.json()['contribution_ids'];worker=worker_fixture(monkeypatch,conn)
    monkeypatch.setattr(worker,'BANK',bank);monkeypatch.setattr(worker,'BANK_ROOT',tmp_path)
    remote=worker.remote
    def isolated_queue(sql,json_result=False):
        if sql.startswith("SELECT * FROM bank_publications WHERE state='exported'"):
            sql="SELECT * FROM bank_publications WHERE state='exported' AND contribution_id IN ("+','.join(worker.literal(c) for c in cids)+') ORDER BY id LIMIT 1'
        return remote(sql,json_result)
    monkeypatch.setattr(worker,'remote',isolated_queue)
    attempts=[]
    def sync(args,**kwargs):
        assert args==[str(worker.ROOT/'scripts/sync-bank.sh')]
        attempts.append(1)
        if len(attempts)==1:raise RuntimeError('Synthetic process interruption before database sync')
        conn.execute("UPDATE question_classifications SET subject_id='mizo',subject_label='Mizo',topic_id=NULL,subtopic_id=NULL WHERE question_id=ANY(%s)",(targets,))
        conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,2,now())',(sha(bank),))
    monkeypatch.setattr(worker.subprocess,'run',sync)
    with pytest.raises(RuntimeError):worker.once()
    # Both file changes are durable together, while neither failed job is claimed applied.
    assert all(q['classifications'][0]['subject_id']=='mizo' for q in json.loads(bank.read_text())['questions'])
    assert conn.execute("SELECT count(*) FROM bank_publications WHERE contribution_id=ANY(%s) AND state='failed'",(cids,)).fetchone()[0]==2
    output=sha(bank);batch=client.get('/api/admin/bank/retag/batches/'+bid).json()
    r=client.post('/api/admin/bank/retag/batches/'+bid+'/retry',headers=h,json={'expected_versions':{i['id']:i['lock_version'] for i in batch['items']}});assert r.status_code==200,r.text
    worker.once()
    assert sha(bank)==output and len(attempts)==2
    assert conn.execute("SELECT count(*) FROM bank_publications WHERE contribution_id=ANY(%s) AND state='applied'",(cids,)).fetchone()[0]==2
    assert conn.execute('SELECT count(DISTINCT receipt->>\'output_sha256\') FROM bank_publications WHERE contribution_id=ANY(%s)',(cids,)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM contribution_credit WHERE contribution_id=ANY(%s)',(cids,)).fetchone()[0]==0


def test_answer_form_rejects_evidence_registry_drift(client,actor,database):
    from test_admin_answers import setup
    q,a,p,h,url,body=setup(client,actor,database)
    database[1].execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'New evidence','synthetic.pdf',%s,'paper','test')",('drift-'+uuid4().hex,p,'f'*64))
    r=client.post(url,headers=h,json=body)
    assert r.status_code==409,r.text


def test_tag_discovery_shared_sources_bank_scope_and_empty_pages(client,actor,workbench,database):
    ids,paper,alt=workbench;conn=database[1];actor('owner');qid=ids['unverified']
    other=conn.execute('SELECT paper_id FROM appearances WHERE id=%s',(alt,)).fetchone()[0]
    conn.execute("UPDATE papers SET exam_type='Community',year=2026 WHERE id=%s",(other,))
    endpoint='/api/admin/bank/tag-issues'
    def find(**filters):
        r=client.get(endpoint,params={'issue':'all','q':qid,**filters})
        assert r.status_code==200,r.text
        return r.json()
    shared=find()
    assert shared['total']==1 and shared['items'][0]['appearance_id']=='app-'+qid
    website=find(bank='website')
    assert website['total']==1 and website['items'][0]['appearance_id']==alt
    assert website['items'][0]['bank']=='website' and website['items'][0]['year']==2026
    mpsc=find(bank='mpsc')
    assert mpsc['total']==1 and mpsc['items'][0]['appearance_id']=='app-'+qid
    assert find(paper=other)['items'][0]['appearance_id']==alt
    assert find(year=2026)['items'][0]['appearance_id']==alt
    assert find(bank='website',year=2020)=={'total':0,'items':[]}
    assert find(offset=20)=={'total':1,'items':[]}
    # Only current browsable module membership may supply a source appearance.
    version=conn.execute("SELECT live_version FROM collections WHERE id='udc'").fetchone()[0]
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) VALUES('udc',%s,%s,'papers')",(version,other))
    assert find(module='udc')['items'][0]['appearance_id']==alt
    conn.execute("UPDATE collection_papers SET allow_browse=false WHERE collection_id='udc' AND version=%s AND paper_id=%s",(version,other))
    assert find(module='udc')=={'total':0,'items':[]}
    # Two open reports count twice but never duplicate the canonical question.
    for reporter in ['author','reviewer1']:
        conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES(%s,'subject',%s,'Please review the classification against the source')",(qid,reporter))
    reported=find(issue='reported',bank='website')
    assert reported['total']==1 and reported['items'][0]['report_count']==2
