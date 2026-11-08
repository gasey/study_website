"""Serial export preserves immutable approvals while avoiding unrelated-bank races."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from test_admin_answers import setup
from test_admin_workbench import workbench
from test_editorial_simplification import edit_body

@pytest.fixture
def serial(monkeypatch,database):
    conn=database[1]
    existing=conn.execute("SELECT id FROM bank_publications WHERE state='exported'").fetchall()
    intents=conn.execute("SELECT id FROM review_outbox WHERE kind='publication-intent' AND finished_at IS NULL").fetchall()
    conn.execute("UPDATE bank_publications SET state='failed' WHERE state='exported'")
    conn.execute("UPDATE review_outbox SET finished_at=now() WHERE kind='publication-intent' AND finished_at IS NULL")
    monkeypatch.setattr(settings,'publication_serial_queue',True)
    yield
    conn.execute("UPDATE bank_publications SET state='failed' WHERE state='exported'")
    conn.execute("UPDATE review_outbox SET finished_at=now() WHERE kind='publication-intent' AND finished_at IS NULL")
    for (pid,) in existing:conn.execute("UPDATE bank_publications SET state='exported' WHERE id=%s",(pid,))
    for (iid,) in intents:conn.execute('UPDATE review_outbox SET finished_at=NULL WHERE id=%s',(iid,))


def save(client,actor,database):
    q,a,p,h,base,payload=setup(client,actor,database)
    r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text
    return q,a,h,base,payload,r.json()


def promote(client):
    async def run():
        from app.db import cursor
        from app.services.bank_publication import promote_one
        async with cursor() as cur:return await promote_one(cur)
    return client.portal.call(run)


def finish_slot(conn,result):
    conn.execute("UPDATE bank_publications SET state='applied' WHERE id=%s",(result['publication_id'],))
    conn.execute("UPDATE bank_contributions SET state='published' WHERE id=%s",(result['contribution_id'],))


def test_later_save_is_exported_only_after_previous_sync(client,actor,database,serial):
    conn=database[1];*_,first=save(client,actor,database)
    original=conn.execute('SELECT manifest_hash,manifest FROM bank_publications WHERE id=%s',(first['publication_id'],)).fetchone()
    q,a,h,base,payload,second=save(client,actor,database)
    assert second['publication_id'] is None
    assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(second['contribution_id'],)).fetchone()[0]=='accepted'
    assert conn.execute('SELECT count(*) FROM bank_publications WHERE contribution_id=%s',(second['contribution_id'],)).fetchone()[0]==0
    replay=client.post(base,headers=h,json=payload).json()
    assert replay['state']=='accepted' and replay['publication_id'] is None and replay['replayed']
    assert promote(client)['id'] is None # an active export still owns the slot
    finish_slot(conn,first)
    fresh='d'*64;conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',(fresh,))
    exported=promote(client);assert exported['id']
    manifest=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(exported['id'],)).fetchone()[0]
    assert manifest['bank_sha256']==fresh
    assert manifest['payload']['canonical_id']==q
    assert manifest['admin_decision']['actor_id']=='owner'
    assert conn.execute('SELECT manifest_hash,manifest FROM bank_publications WHERE id=%s',(first['publication_id'],)).fetchone()==original
    assert promote(client)['state']=='empty'
    assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(second['contribution_id'],)).fetchone()[0]==0


@pytest.mark.parametrize('change',['source','permission'])
def test_promotion_rechecks_original_source_and_permissions(client,actor,database,serial,change):
    conn=database[1];*_,first=save(client,actor,database)
    q,a,h,base,payload,second=save(client,actor,database)
    finish_slot(conn,first)
    if change=='source':conn.execute("UPDATE appearances SET question=question||' changed' WHERE id=%s",(a,))
    else:conn.execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='owner' AND revoked_at IS NULL")
    try:
        result=promote(client)
        assert result['state']=='failed'
        assert conn.execute('SELECT count(*) FROM bank_publications WHERE contribution_id=%s',(second['contribution_id'],)).fetchone()[0]==0
        assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(second['contribution_id'],)).fetchone()[0]=='publication_failed'
    finally:
        if change=='permission':conn.execute("UPDATE review_grants SET revoked_at=NULL WHERE user_id='owner'")


def test_stale_retry_is_rejected_but_fresh_answer_save_is_possible(client,actor,database,serial):
    conn=database[1];q,a,h,base,payload,result=save(client,actor,database)
    pid=result['publication_id'];cid=result['contribution_id']
    conn.execute("UPDATE bank_publications SET state='failed',error='Bank snapshot changed since review export' WHERE id=%s",(pid,))
    conn.execute("UPDATE bank_contributions SET state='publication_failed' WHERE id=%s",(cid,))
    conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',('e'*64,))
    version=conn.execute('SELECT lock_version FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]
    r=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=h,json={'expected_version':version,'reason':'Retry after an unrelated bank publication completed.'})
    assert r.status_code==409 and 'fresh decision' in r.text
    assert conn.execute('SELECT state FROM bank_publications WHERE id=%s',(pid,)).fetchone()[0]=='failed'
    fresh=client.post(base,headers={**h,'Idempotency-Key':uuid4().hex},json=payload)
    assert fresh.status_code==200,fresh.text
    assert fresh.json()['publication_id'] and fresh.json()['contribution_id']!=cid
    assert conn.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]=='publication_failed'


def test_answer_and_tag_saves_share_one_pending_guard(client,actor,database,workbench,serial):
    ids,paper,_=workbench;q=ids['unverified'];a='app-'+q;h=actor('owner');h['Idempotency-Key']=uuid4().hex
    body=edit_body(client,q,a)
    r=client.post('/api/admin/bank/edits',headers=h,json=body);assert r.status_code==200,r.text
    base='/api/admin/bank/questions/'+q+'/answer-decision'
    baseline=client.get(base,params={'appearance_id':a}).json()['baseline_hash']
    payload={'appearance_id':a,'baseline_hash':baseline,'mode':'verified','answer_index':1,'explanation':'Synthetic worked reasoning supports this printed answer choice.','reason':'Inspected the synthetic source and verified the answer mapping.'}
    r=client.post(base,headers={**h,'Idempotency-Key':uuid4().hex},json=payload)
    assert r.status_code==409 and 'publication' in r.text


def test_failed_tag_can_be_replaced_and_deferred_replay_has_receipt(client,actor,database,workbench,serial):
    conn=database[1];ids,paper,_=workbench;q=ids['unverified'];a='app-'+q;h=actor('owner');h['Idempotency-Key']=uuid4().hex
    body=edit_body(client,q,a)
    first=client.post('/api/admin/bank/edits',headers=h,json=body).json()
    conn.execute("UPDATE bank_publications SET state='failed' WHERE id=%s",(first['publication']['id'],))
    conn.execute("UPDATE bank_contributions SET state='publication_failed' WHERE id=%s",(first['contribution_id'],))
    # Keep another question's export active, so the fresh tag decision is staged.
    *_,blocker=save(client,actor,database)
    h=actor('owner');h['Idempotency-Key']=uuid4().hex
    second=client.post('/api/admin/bank/edits',headers=h,json=body)
    assert second.status_code==200,second.text
    assert second.json()['publication']=={'id':None,'state':'accepted'}
    replay=client.post('/api/admin/bank/edits',headers=h,json=body)
    assert replay.status_code==200,replay.text
    assert replay.json()['publication']['state']=='accepted'


def test_tag_batch_stays_atomic_and_waits_for_global_slot(client,actor,database,workbench,serial):
    conn=database[1];ids,_,_=workbench;h=actor('owner');targets=[ids['missing'],ids['unverified']]
    preview=client.post('/api/admin/bank/retag/preview',headers=h,json={'targets':[{'question_id':q,'appearance_id':'app-'+q}for q in targets]}).json()['items']
    body={'targets':[{k:p[k]for k in ('question_id','appearance_id','baseline_hash','source_version')}for p in preview],
      'classification':{'subject_id':'mizo'},'operation':'replace_primary','reason':'Source wording supports every selected synthetic question.'}
    *_,blocker=save(client,actor,database)
    h=actor('owner');h['Idempotency-Key']=uuid4().hex
    assert client.post('/api/admin/bank/retag/apply',headers=h,json=body).status_code==409
    assert conn.execute('SELECT count(*) FROM admin_bank_decisions WHERE canonical_id=ANY(%s)',(targets,)).fetchone()[0]==0
    finish_slot(conn,blocker)
    r=client.post('/api/admin/bank/retag/apply',headers=h,json=body);assert r.status_code==200,r.text
    pubs=conn.execute('SELECT manifest,state FROM bank_publications WHERE contribution_id=ANY(%s)',(r.json()['contribution_ids'],)).fetchall()
    assert len(pubs)==2 and all(p[1]=='exported'for p in pubs)
    assert len({p[0]['bank_sha256']for p in pubs})==1


def test_two_distinct_saves_roundtrip_through_guarded_bank_sync(client,actor,database,serial,tmp_path,monkeypatch):
    import copy,json,subprocess,importlib.util
    from pathlib import Path
    from psycopg.rows import dict_row
    from review_bank_store import apply_manifest,sha
    root=Path(__file__).resolve().parents[2];conn=database[1]
    setups=[setup(client,actor,database)for _ in range(2)]
    records=[];papers=[]
    for q,a,p,h,base,payload in setups:
        record=copy.deepcopy(client.get(base).json()['snapshot']['record']);classification=record.pop('classification')
        record['classifications']=[{**classification,'is_primary':True,'source':'manual','review_status':'approved','taxonomy_version':'test'}]
        records.append(record);papers.append({'id':p,'examType':'Direct','examName':'Synthetic learning workflow','year':2020,'kind':'mcq','sourceFile':'Old_Questions/test.pdf'})
    bank=tmp_path/'bank.json';bank.write_text(json.dumps({'papers':papers,'questions':records}))
    original_sha=sha(bank);conn.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,2,now())',(original_sha,))
    results=[]
    for q,a,p,h,base,payload in setups:
        r=client.post(base,headers=h,json=payload);assert r.status_code==200,r.text;results.append(r.json())
    assert results[0]['publication_id'] and results[1]['publication_id'] is None
    spec=importlib.util.spec_from_file_location('serial_roundtrip_worker',root/'scripts/bank-review-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    def remote(sql,json_result=False):
        with conn.cursor(row_factory=dict_row)as cur:cur.execute(sql);return cur.fetchall()if json_result else ''
    monkeypatch.setattr(worker,'remote',remote)
    tables=('question_classifications','question_topic_links','collection_sections')
    for table in tables:conn.execute(f'CREATE TEMP TABLE serial_roundtrip_{table} AS SELECT * FROM {table}')
    tax=tmp_path/'taxonomy.json';tax.write_text('{"subjects":[{"id":"english","label":"English"}]}')
    script=(root/'scripts/sync-bank.sh').read_text()
    try:
        for index in range(2):
            pid=results[0]['publication_id']if index==0 else promote(client)['id']
            with conn.cursor(row_factory=dict_row)as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(pid,)).fetchone()
            assert pub['manifest']['bank_sha256']==sha(bank)
            receipt=apply_manifest(bank,tmp_path,pub['manifest'],pub['manifest_hash'])
            csv=tmp_path/('csv'+str(index))
            subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/bank_to_csv.py'),str(bank),str(csv),str(tax)],check=True,capture_output=True,text=True)
            prepare=script.split("SQL=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0].replace('/tmp/bank-csv',str(csv));apply=script.split("APPLY=$(cat <<'EOSQL'\n",1)[1].split('\nEOSQL',1)[0]
            sql=prepare+'\n'+apply+"\nINSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES ('"+receipt['output_sha256']+"',2,now());\nCOMMIT;"
            r=subprocess.run(['psql','-v','ON_ERROR_STOP=1','-d',database[0]],input=sql,text=True,capture_output=True);assert r.returncode==0,r.stderr
            worker.verify_live(receipt,pub['manifest']);worker.acknowledge(pub,receipt)
        for q,*_ in setups:
            assert conn.execute('SELECT answer_status FROM v_bank_answer_status WHERE id=%s',(q,)).fetchone()[0]=='verified'
        assert conn.execute('SELECT manifest->>\'bank_sha256\' FROM bank_publications WHERE id=%s',(results[0]['publication_id'],)).fetchone()[0]==original_sha
        assert conn.execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=ANY(%s)',([r['contribution_id']for r in results],)).fetchone()[0]==0
    finally:
        for table in tables:
            conn.execute(f'DELETE FROM {table}');conn.execute(f'INSERT INTO {table} SELECT * FROM serial_roundtrip_{table}');conn.execute(f'DROP TABLE serial_roundtrip_{table}')


def test_busy_export_lock_defers_without_deadlock(client,actor,database,serial):
    import psycopg
    blocker=psycopg.connect('dbname='+database[0])
    try:
        blocker.execute("SELECT pg_advisory_xact_lock(hashtextextended('bank-publication-export',0))")
        *_,result=save(client,actor,database)
        assert result['publication_id'] is None
        assert promote(client)['id'] is None
    finally:blocker.rollback();blocker.close()
    assert promote(client)['id']


def test_retry_of_preexport_failure_reopens_durable_intent(client,actor,database,serial):
    conn=database[1];*_,first=save(client,actor,database)
    q,a,h,base,payload,second=save(client,actor,database)
    finish_slot(conn,first)
    conn.execute("UPDATE appearances SET question=question||' changed' WHERE id=%s",(a,))
    assert promote(client)['state']=='failed'
    # Restore the exact approved source; retry is now valid but must wait behind another export.
    conn.execute("UPDATE appearances SET question='Synthetic learning question' WHERE id=%s",(a,))
    *_,blocker=save(client,actor,database)
    cid=second['contribution_id'];version=conn.execute('SELECT lock_version FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]
    r=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=h,json={'expected_version':version,'reason':'The original approved source has been restored exactly.'})
    assert r.status_code==200,r.text
    assert r.json()=={'id':None,'state':'accepted'}
    assert conn.execute('SELECT count(*) FROM review_outbox WHERE kind=\'publication-intent\' AND payload->>\'contribution_id\'=%s AND finished_at IS NULL',(cid,)).fetchone()[0]==1
    finish_slot(conn,blocker)
    assert promote(client)['id']


def test_promoter_cli_uses_the_durable_authorisation(client,actor,database,serial):
    import json,os,subprocess
    from pathlib import Path
    conn=database[1];*_,first=save(client,actor,database);*_,second=save(client,actor,database)
    finish_slot(conn,first)
    root=Path(__file__).resolve().parents[2];env={**os.environ,'PUBLICATION_SERIAL_QUEUE':'true'};env.pop('ISM_DB_TRANSPORT',None)
    r=subprocess.run([str(root/'api/.venv/bin/python'),str(root/'scripts/promote-publication-queue.py'),'--database',database[0]],cwd=root,env=env,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    result=json.loads(r.stdout);assert result['id']
    manifest=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(result['id'],)).fetchone()[0]
    assert manifest['contribution_id']==second['contribution_id'] and manifest['admin_decision']['actor_id']=='owner'


def test_export_reads_latest_sync_after_acquiring_slot(client,actor,database,serial,monkeypatch):
    from app.services import bank_publication
    original=bank_publication.export_slot
    fresh='f'*64
    async def race(cur,**kwargs):
        acquired=await original(cur,**kwargs)
        if acquired:
            # Previous publication finishes between the save's validation and slot.
            await cur.execute('INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES(%s,1,now())',(fresh,))
        return acquired
    monkeypatch.setattr(bank_publication,'export_slot',race)
    *_,result=save(client,actor,database)
    assert database[1].execute("SELECT manifest->>'bank_sha256' FROM bank_publications WHERE id=%s",(result['publication_id'],)).fetchone()[0]==fresh


def test_preexport_retry_preserves_original_admin_binding(client,actor,database,serial):
    conn=database[1];*_,first=save(client,actor,database)
    q,a,h,base,payload,second=save(client,actor,database)
    expected=conn.execute("SELECT payload->'extra' FROM review_outbox WHERE payload->>'contribution_id'=%s AND kind='publication-intent'",(second['contribution_id'],)).fetchone()[0]
    finish_slot(conn,first)
    conn.execute("UPDATE appearances SET question=question||' changed' WHERE id=%s",(a,))
    assert promote(client)['state']=='failed'
    conn.execute("UPDATE appearances SET question='Synthetic learning question' WHERE id=%s",(a,))
    *_,blocker=save(client,actor,database)
    cid=second['contribution_id'];version=conn.execute('SELECT lock_version FROM bank_contributions WHERE id=%s',(cid,)).fetchone()[0]
    r=client.post('/api/admin/bank/contributions/'+cid+'/publish',headers=h,json={'expected_version':version,'reason':'Original source restored exactly before retrying the saved decision.'})
    assert r.status_code==200,r.text
    finish_slot(conn,blocker)
    exported=promote(client);assert exported['id']
    manifest=conn.execute('SELECT manifest FROM bank_publications WHERE id=%s',(exported['id'],)).fetchone()[0]
    assert manifest['admin_decision']==expected['admin_decision']
    # Worker independently validates the binding against immutable decision rows.
    from test_editorial_simplification import worker_fixture
    from pytest import MonkeyPatch
    with MonkeyPatch.context() as patches:
        worker=worker_fixture(patches,conn)
        from psycopg.rows import dict_row
        with conn.cursor(row_factory=dict_row)as cur:pub=cur.execute('SELECT * FROM bank_publications WHERE id=%s',(exported['id'],)).fetchone()
        worker.validate_admin_authority(pub)


def test_worker_skips_terminal_intents_before_processing_valid_export(tmp_path,monkeypatch):
    import importlib.util
    from pathlib import Path
    from contextlib import nullcontext
    import bank_authority
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('skip_failed_intent_worker',root/'scripts/bank-review-worker.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    statuses=iter([{'state':'failed'},{'state':'cancelled'},{'state':'publishing'}]);promoted=[];acked=[]
    pub={'id':'pub_test','state':'exported','contribution_id':'con_test','manifest':{},'manifest_hash':'hash'}
    def promotion():
        result=next(statuses);promoted.append(result['state']);return result
    def remote(sql,json_result=False):
        if "WHERE state='exported'"in sql:return[pub]if promoted and promoted[-1]=='publishing'else[]
        if 'SELECT bank_checksum'in sql:return[{'bank_checksum':'output'}]
        return ''
    monkeypatch.setattr(worker,'promote_deferred',promotion);monkeypatch.setattr(worker,'remote',remote)
    monkeypatch.setattr(bank_authority,'require_writable',lambda _:None)
    monkeypatch.setattr(worker,'bank_lock',lambda _:nullcontext())
    monkeypatch.setattr(worker,'validate_admin_authority',lambda _:None)
    monkeypatch.setattr(worker,'apply_manifest',lambda *a,**kw:{'output_sha256':'output'})
    monkeypatch.setattr(worker,'sha',lambda _:'output')
    monkeypatch.setattr(worker,'verify_live',lambda *a:None)
    monkeypatch.setattr(worker,'acknowledge',lambda *a:acked.append(a))
    monkeypatch.setattr(worker.subprocess,'run',lambda *a,**kw:None)
    assert worker.once()is True
    assert promoted==['failed','cancelled','publishing']and len(acked)==1


def test_source_is_rechecked_after_slot_boundary(client,actor,database,serial,monkeypatch):
    from app.services import bank_publication
    original=bank_publication.export_slot
    q,a,p,h,base,payload=setup(client,actor,database)
    async def race(cur,**kwargs):
        acquired=await original(cur,**kwargs)
        if acquired:await cur.execute("UPDATE appearances SET question=question||' changed at slot' WHERE id=%s",(a,))
        return acquired
    monkeypatch.setattr(bank_publication,'export_slot',race)
    result=client.post(base,headers=h,json=payload)
    assert result.status_code==409 and 'question changed' in result.text.lower()
    assert database[1].execute('SELECT count(*) FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id WHERE c.canonical_id=%s',(q,)).fetchone()[0]==0
