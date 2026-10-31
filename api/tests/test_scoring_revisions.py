from test_account_hardening import headers as account_headers
from uuid import uuid4
import copy
import pytest
from app.services.scoring_revisions import evaluate,totals


def snapshot():return {'question':'Choose a letter','options':['A','B','C','D'],'answer_text':'B','answer_source':'official'}
def current():return {'type':'mcq','status':'live','question':'Choose a letter','options':['A','B','C','D'],'answer_text':'C','answer_source':'official','key_disputed':False,'source_defect':None,'reviewed_eligible':True}


def test_mapping_and_excluded_denominators():
    snap=snapshot();now=current()
    assert evaluate(snap,now,'C','official')['outcome']=='correct'
    now['options']=['D','C','B','A']
    assert evaluate(snap,now,'C','official')['outcome']=='correct'
    for patch,reason in [({'options':['A','B','C','X']},'options_unmappable'),({'question':'Choose a different letter'},'question_text_changed'),({'status':'held'},'question_held'),({'key_disputed':True},'disputed_key'),({'source_defect':'duplicate-options'},'source_defect'),({'answer_source':'inferred'},'unverified_answer'),({'answer_source':'derived'},'not_official_key')]:
        result=evaluate(snap,{**current(),**patch},'B','official');assert result['reason']==reason;assert result['outcome']=='excluded'
    assert evaluate(None,current(),'C','official')['reason']=='legacy_unversioned'
    result=totals([{'outcome':'excluded'}],2,.5)
    assert result['score'] is None and result['accuracy'] is None and result['scorable_total']==0
    assert evaluate(snap,{**current(),'answer_source':'derived','reviewed_eligible':False},'C','derived-practice')['reason']=='derived_review_missing'


def start_and_finish(client,actor,database,pick=1,mode='official'):
    conn=database[1];token=uuid4().hex[:10];qid='cq_score_'+token;cid='score-'+token
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active' WHERE id='owner'")
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq',%s,'[\"A\",\"B\",\"C\",\"D\"]','B','official')",(qid,'Choose a letter '+token))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) SELECT %s,'paper-test','mcq',question,options,1,'official',id,true FROM canonical_questions WHERE id=%s",('appearance-'+token,qid))
    conn.execute("INSERT INTO collections(id,title,kind,live_version) VALUES (%s,'Score test','exam',1)",(cid,))
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query,pins) VALUES (%s,1,'test','Test',0,'{}',ARRAY[%s])",(cid,qid))
    h=actor('owner');response=client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1,'answer_mode':mode,'marks_correct':2,'marks_wrong':.5})
    assert response.status_code==200,response.text
    mid=response.json()['id']
    response=client.post('/api/mocks/'+mid+'/submit',headers=h,json={'answers':[] if pick is None else [{'question_id':qid,'chosen_index':pick}]})
    assert response.status_code==200,response.text
    return qid,cid,mid,h,response.json()


def test_adjustment_history_originals_and_reversal(client,actor,database):
    conn=database[1];qid,cid,mid,h,original=start_and_finish(client,actor,database)
    path='/api/mocks/'+mid
    assert original['score']==2 and original['score_breakdown']['official_subset']['scorable_total']==1
    assert client.post(path+'/reassess').status_code==403
    initial=client.post(path+'/reassess',headers=h).json();assert initial['score']==2
    conn.execute('UPDATE canonical_questions SET answer_text=\'C\' WHERE id=%s',(qid,))
    history=client.get(path+'/assessments').json();assert history['pending'] is True
    changed=client.post(path+'/reassess',headers=h);assert changed.status_code==200,changed.text
    changed=changed.json();assert changed['score']==-.5 and changed['rows'][0]['reason']=='key_corrected'
    assert changed['original_score']==2
    assert client.post(path+'/reassess',headers=h).json()['id']==changed['id']
    assert conn.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',(changed['id']+':assessment',)).fetchone()[0]==1
    conn.execute('UPDATE canonical_questions SET answer_text=\'B\' WHERE id=%s',(qid,))
    restored=client.post(path+'/reassess',headers=h).json()
    assert restored['score']==2 and restored['id'] not in {initial['id'],changed['id']}
    history=client.get(path+'/assessments').json();assert history['items'][0]['id']==restored['id'] and history['pending'] is False
    assert len(history['items'])==3
    assert client.get(path).json()['score']==2 and client.get(path).json()['review'][0]['answer_text']=='B'
    assert conn.execute('SELECT correct FROM attempts WHERE mock_id=%s',(mid,)).fetchone()[0] is True
    with pytest.raises(Exception,match='append-only'):conn.execute('DELETE FROM mock_assessments WHERE mock_id=%s',(mid,))
    actor('author');assert client.get(path+'/assessments').status_code==404
    assert client.post(path+'/reassess',headers=actor('author')).status_code==404


def test_unmappable_excluded_and_legacy_not_fabricated(client,actor,database):
    conn=database[1];qid,cid,mid,h,result=start_and_finish(client,actor,database,pick=None)
    conn.execute('UPDATE canonical_questions SET options=\'["X","B","C","D"]\' WHERE id=%s',(qid,))
    adjusted=client.post('/api/mocks/'+mid+'/reassess',headers=h).json()
    assert adjusted['n_excluded']==1 and adjusted['n_wrong']==0 and adjusted['score'] is None
    assert adjusted['rows'][0]['reason']=='options_unmappable'
    # Real legacy history is never backfilled with today's answer as an old key.
    old='legacy-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,submitted_at,elapsed_seconds,n_correct,n_wrong,n_skipped,score) VALUES (%s,'owner',%s,ARRAY[%s],1200,now(),10,0,0,1,0)",(old,cid,qid))
    legacy=client.post('/api/mocks/'+old+'/reassess',headers=h).json()
    assert legacy['legacy_unversioned'] is True and legacy['rows'][0]['original_answer'] is None
    assert legacy['rows'][0]['reason']=='legacy_unversioned' and legacy['score'] is None
    assert client.get('/api/mocks/'+old).json()['legacy_unversioned'] is True


def test_derived_label_alone_cannot_start_new_timed_estimate(client,actor,database):
    conn=database[1];qid,cid,mid,h,result=start_and_finish(client,actor,database)
    conn.execute("UPDATE canonical_questions SET answer_source='derived' WHERE id=%s",(qid,))
    response=client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1,'answer_mode':'derived-practice'})
    assert response.status_code==422,response.text
    adjusted=client.post('/api/mocks/'+mid+'/reassess',headers=h).json()
    assert adjusted['n_excluded']==1 and adjusted['rows'][0]['reason']=='not_official_key'


def test_practice_snapshot_and_worker_job(client,actor,database):
    from app.db import cursor
    from app.services.scoring_revisions import process_job
    conn=database[1];qid,cid,mid,h,result=start_and_finish(client,actor,database)
    response=client.post('/api/questions/'+qid+'/answer', headers=account_headers(client),json={'chosen_index':1,'context':'practice'})
    assert response.status_code==200,response.text
    attempt=conn.execute("SELECT id,scoring_snapshot FROM attempts WHERE canonical_id=%s AND context='practice'",(qid,)).fetchone()
    assert attempt[1]['answer_text']=='B'
    conn.execute("UPDATE canonical_questions SET answer_text='C' WHERE id=%s",(qid,))
    conn.execute("UPDATE assessment_jobs SET requested_at='1900-01-01' WHERE canonical_id=%s",(qid,))
    async def run():
        async with cursor() as cur:return await process_job(cur)
    assert client.portal.call(run) is True
    assessment=conn.execute('SELECT payload FROM attempt_assessments WHERE attempt_id=%s',(attempt[0],)).fetchone()[0]
    assert assessment['outcome']=='wrong' and assessment['original_correct'] is True
    assert conn.execute('SELECT correct FROM attempts WHERE id=%s',(attempt[0],)).fetchone()[0] is True
    assert conn.execute('SELECT count(*) FROM mock_assessments WHERE mock_id=%s',(mid,)).fetchone()[0]==1
    summary=client.get('/api/me/score-summary').json()
    assert summary['practice_adjusted']['assessed']>=1


def test_published_correction_reassesses_real_mock_pipeline(client,actor,database,tmp_path,monkeypatch):
    import json,subprocess,importlib.util
    from pathlib import Path
    from psycopg.rows import dict_row
    from review_bank_store import apply_manifest,sha
    from app.db import cursor
    from app.services.scoring_revisions import process_job
    conn=database[1];root=Path(__file__).resolve().parents[2]
    qid,cid,mid,h,original=start_and_finish(client,actor,database,pick=2,mode='derived-practice')
    assert original['score']==-.5
    snap=client.get('/api/review/questions/'+qid,headers=h).json();q=copy.deepcopy(snap['record']);classification=q.pop('classification')
    classification={'subject_id':'english'};q['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
    # The source's primary taxonomy must be registered before review.
    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,'english','English','test','manual','approved')",(qid,))
    bank=tmp_path/'bank.json';bank.write_text(json.dumps({'papers':[{'id':'paper-test','examType':'Direct','examName':'Synthetic source paper','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'}],'questions':[q]}))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES (%s,1,now())',(sha(bank),))
    payload={'kind':'answer','canonical_id':qid,'appearance_id':q['id'],'subject_id':'english','title':'Synthetic revised answer for scoring pipeline','patch':{'answerIndex':2,'answerSource':'derived','explanation':'Independent synthetic reasoning supports option C for this test.'},'rationale':'Synthetic correction to demonstrate the complete scoring revision pipeline.','evidence':[{'kind':'reasoning','note':'Synthetic source evidence, never a real bank answer or official key.'}]}
    h=actor('author');response=client.post('/api/contributions',headers={**h,'Idempotency-Key':uuid4().hex},json=payload);assert response.status_code==201,response.text
    c=response.json();con_id=c['id'];c=client.post('/api/contributions/'+con_id+'/submit',headers=h,json={'expected_version':1}).json()
    for user in ['reviewer1','reviewer2']:
        response=client.post('/api/review/'+con_id+'/decisions',headers=actor(user),json={'expected_version':c['lock_version'],'decision':'approve','reason':'Independent synthetic review supports this revised derived answer.'});assert response.status_code==200,response.text;c=response.json()
    response=client.post('/api/admin/bank/contributions/'+con_id+'/publish',headers=actor('owner'),json={'expected_version':c['lock_version']});assert response.status_code==200,response.text
    pub_id=response.json()['id']
    with conn.cursor(row_factory=dict_row) as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pub_id,)).fetchone()
    receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
    tax=tmp_path/'taxonomy.json';tax.write_text('{"subjects":[{"id":"english","label":"English"}]}');csv=tmp_path/'csv'
    subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(tax)],check=True,capture_output=True,text=True)
    script=(root/'scripts/sync-bank.sh').read_text();setup=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv));apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
    sql=setup+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+receipt['output_sha256']+"',1,now());\nCOMMIT;"
    result=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True);assert result.returncode==0,result.stderr
    spec=importlib.util.spec_from_file_location('assessment_worker_fixture',root/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    def local(query,json_result=False):
        with conn.cursor(row_factory=dict_row) as cur:cur.execute(query);return cur.fetchall() if json_result else ''
    monkeypatch.setattr(worker,'remote',local);worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt)
    assert conn.execute('SELECT count(*) FROM v_mock_practice WHERE id=%s',(qid,)).fetchone()[0]==1
    assert client.get('/api/questions/'+qid).json()['reviewed_derived'] is True
    assert conn.execute('SELECT count(*) FROM v_scorable WHERE id=%s',(qid,)).fetchone()[0]==0
    conn.execute("UPDATE assessment_jobs SET requested_at='1800-01-01' WHERE canonical_id=%s",(qid,))
    async def run():
        async with cursor() as cur:return await process_job(cur)
    client.portal.call(run)
    h=actor('owner');history=client.get('/api/mocks/'+mid+'/assessments').json();assert history['pending'] is False
    adjusted=history['items'][0]
    assert adjusted['score']==2 and adjusted['original_score']==-.5
    assert adjusted['official_subset']['scorable_total']==0 and adjusted['official_subset']['score'] is None
    assert client.get('/api/mocks/'+mid).json()['score']==-.5
    assert conn.execute('SELECT sum(amount),count(*) FROM contribution_credit WHERE publication_id=%s',(pub_id,)).fetchone()==(10,1)


def test_passage_and_figure_changes_do_not_mark_old_answers_wrong(client,actor,database):
    conn=database[1];qid,cid,mid,h,original=start_and_finish(client,actor,database)
    # A passage-only source correction leaves stem/options untouched.
    conn.execute("UPDATE appearances SET passage='A corrected passage changes the task.' WHERE canonical_id=%s",(qid,))
    adjusted=client.post('/api/mocks/'+mid+'/reassess',headers=h).json()
    assert adjusted['rows'][0]['reason']=='question_context_changed'
    assert adjusted['n_wrong']==0 and adjusted['n_excluded']==1
    assert conn.execute('SELECT count(*) FROM new_score_jobs j JOIN appearances a ON a.id=j.appearance_id WHERE a.canonical_id=%s AND j.finished_at IS NULL',(qid,)).fetchone()[0]==1
    snap=snapshot();now=current();snap['figure_image']='images/old.png';now['figure_image']='images/new.png'
    assert evaluate(snap,now,'B','official')['reason']=='question_context_changed'


def test_new_answers_preserve_historical_scan_progress(client,actor,database):
    conn=database[1];qid,cid,mid,h,result=start_and_finish(client,actor,database)
    conn.execute("INSERT INTO assessment_jobs(canonical_id,mock_cursor,attempt_cursor) VALUES (%s,'retained-cursor',123456) ON CONFLICT(canonical_id) DO UPDATE SET mock_cursor='retained-cursor',attempt_cursor=123456",(qid,))
    response=client.post('/api/questions/'+qid+'/answer', headers=account_headers(client),json={'chosen_index':1,'context':'practice'})
    assert response.status_code==200,response.text
    assert conn.execute('SELECT mock_cursor,attempt_cursor FROM assessment_jobs WHERE canonical_id=%s',(qid,)).fetchone()==('retained-cursor',123456)
    assert conn.execute("SELECT count(*) FROM new_score_jobs j JOIN attempts a ON a.id=j.attempt_id WHERE a.canonical_id=%s AND a.context='practice'",(qid,)).fetchone()[0]==1


def test_overlapping_reverse_order_mock_submissions_do_not_deadlock(client,actor,database):
    from concurrent.futures import ThreadPoolExecutor
    from psycopg.types.json import Jsonb
    from test_bank_review import auth_headers
    conn=database[1];a,cid,_,_,_=start_and_finish(client,actor,database);b,_,_,_,_=start_and_finish(client,actor,database)
    mids=[]
    for user,ids in [('owner',[a,b]),('outsider',[b,a])]:
        mid='overlap-'+uuid4().hex;mids.append((user,mid,ids))
        conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES (%s,%s,%s,%s,1200)",(mid,user,cid,ids))
        for pos,qid in enumerate(ids):
            text=conn.execute('SELECT question FROM canonical_questions WHERE id=%s',(qid,)).fetchone()[0]
            snap={**snapshot(),'question':text,'explanation':None}
            conn.execute('INSERT INTO mock_session_questions(mock_id,position,canonical_id,options,snapshot) VALUES (%s,%s,%s,%s,%s)',(mid,pos,qid,Jsonb(snap['options']),Jsonb(snap)))
    def submit(item):
        user,mid,ids=item
        return client.post('/api/mocks/'+mid+'/submit',headers=auth_headers(user),json={'answers':[{'question_id':qid,'chosen_index':1} for qid in ids]})
    with ThreadPoolExecutor(max_workers=2) as executor:responses=list(executor.map(submit,mids))
    assert [r.status_code for r in responses]==[200,200],[r.text for r in responses]
    assert conn.execute('SELECT count(*) FROM new_score_jobs WHERE mock_id=ANY(%s)',([m[1] for m in mids],)).fetchone()[0]==2


def test_admission_rechecks_eligibility_after_question_draw(client,actor,database,monkeypatch):
    import asyncio,threading
    from concurrent.futures import ThreadPoolExecutor
    from app.routers import mocks
    conn=database[1];qid,cid,mid,h,_=start_and_finish(client,actor,database)
    drawn=threading.Event();release=threading.Event();original=mocks._candidate_ids
    async def delayed(cur,collection,section,mode,exam_scope="mizoram-recruitment"):
        ids=await original(cur,collection,section,mode,exam_scope)
        drawn.set();await asyncio.to_thread(release.wait,3)
        return ids
    monkeypatch.setattr(mocks,'_candidate_ids',delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(lambda:client.post('/api/mocks', headers=account_headers(client),json={'collection_id':cid,'count':1,'answer_mode':'official'}))
        assert drawn.wait(3)
        conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(qid,));release.set()
        response=future.result(timeout=5)
    assert response.status_code==409,response.text
    assert conn.execute("SELECT count(*) FROM mock_sessions WHERE user_id='owner' AND submitted_at IS NULL").fetchone()[0]==0


def test_exact_source_admission_and_type_changes_enqueue(client,actor,database):
    from app.db import cursor
    from app.services.scoring_revisions import capture_mock_questions
    conn=database[1];qid,cid,mid,h,_=start_and_finish(client,actor,database)
    appearance=conn.execute('SELECT id FROM appearances WHERE canonical_id=%s',(qid,)).fetchone()[0]
    # A second appearance has the same stem/options but different instructions.
    other='other-'+uuid4().hex
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,direction) SELECT %s,paper_id,type,question,options,answer_index,answer_source,canonical_id,false,'Choose the INCORRECT answer' FROM appearances WHERE id=%s",(other,appearance))
    async def capture(aid):
        async with cursor() as cur:return await capture_mock_questions(cur,[qid],[aid],'official')
    assert client.portal.call(capture,other)==[]
    primary=client.portal.call(capture,None);assert primary[0]['appearance_id']==appearance
    conn.execute("UPDATE canonical_questions SET type='descriptive' WHERE id=%s",(qid,))
    assert conn.execute('SELECT finished_at FROM assessment_jobs WHERE canonical_id=%s',(qid,)).fetchone()[0] is None


def test_original_and_adjusted_history_block_active_overlap(client,actor,database):
    conn=database[1];qid,cid,mid,h,_=start_and_finish(client,actor,database)
    open_id='open-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES (%s,'owner',%s,ARRAY[%s],1200)",(open_id,cid,qid))
    assert client.get('/api/mocks/'+mid).status_code==409
    assert client.get('/api/mocks/'+mid+'/assessments').status_code==409
    assert client.post('/api/mocks/'+mid+'/reassess',headers=h).status_code==409
    conn.execute("UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=1,n_correct=0,n_wrong=0,n_skipped=1,score=0 WHERE id=%s",(open_id,))


def test_owner_retries_stalled_jobs_without_changing_assessments(client,actor,database):
    conn=database[1];qid,cid,mid,h,_=start_and_finish(client,actor,database)
    before=conn.execute('SELECT count(*) FROM mock_assessments').fetchone()[0]
    conn.execute("INSERT INTO assessment_jobs(canonical_id,failures,last_error) VALUES (%s,5,'Synthetic failure') ON CONFLICT(canonical_id) DO UPDATE SET failures=5",(qid,))
    conn.execute('UPDATE new_score_jobs SET failures=5 WHERE mock_id=%s',(mid,))
    assert client.post('/api/admin/bank/assessments/retry',headers=actor('outsider'),json={'reason':'Synthetic recovery check by unauthorized account.'}).status_code==403
    response=client.post('/api/admin/bank/assessments/retry',headers=actor('owner'),json={'reason':'Synthetic recovery after correcting the worker condition.'})
    assert response.status_code==200,response.text
    assert response.json()['retried']>=2
    assert conn.execute('SELECT failures FROM assessment_jobs WHERE canonical_id=%s',(qid,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM mock_assessments').fetchone()[0]==before
