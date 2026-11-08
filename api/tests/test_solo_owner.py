from uuid import uuid4
import pytest
from psycopg.rows import dict_row
from test_admin_workbench import workbench
from test_editorial_simplification import edit_body
from test_paper_workbench import paper,prepared,get,save
from test_learning_workflows import official
from test_shareable_tests import content


def routine(client,q,kind='taxonomy',patch=None):
    body=edit_body(client,q,'app-'+q,kind,patch)
    return {'kind':kind,'canonical_id':q,'appearance_id':'app-'+q,'patch':body['proposal']['patch'],
      'baseline_hash':body['baseline_hash'],'source_version':body['source_version']}


def test_owner_routine_without_reason_is_attributed_and_replay_safe(client,actor,workbench,database):
    ids,_,_=workbench;q=ids['unverified'];h=actor('owner');h['Idempotency-Key']=uuid4().hex
    assert client.get('/api/review/questions/'+q).json()['solo_owner']
    body=routine(client,q)
    r=client.post('/api/admin/bank/routine-edits',headers=h,json=body);assert r.status_code==200,r.text
    result=r.json();cid=result['contribution_id']
    reason=database[1].execute('SELECT reason FROM admin_bank_decisions WHERE contribution_id=%s',(cid,)).fetchone()[0]
    assert 'Automatic owner change summary' in reason and 'english' in reason and 'mizo' in reason
    assert 'inspected' not in reason.lower() and 'independent' not in reason.lower()
    assert database[1].execute('SELECT count(*) FROM contribution_decisions WHERE contribution_id=%s',(cid,)).fetchone()[0]==0
    database[1].execute("UPDATE question_classifications SET subject_id='mizo' WHERE question_id=%s",(q,))
    replay=client.post('/api/admin/bank/routine-edits',headers=h,json=body)
    assert replay.status_code==200 and replay.json()['decision_id']==result['decision_id']
    changed={**body,'appearance_id':'different-source'}
    assert client.post('/api/admin/bank/routine-edits',headers=h,json=changed).status_code==409
    assert database[1].execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='owner_routine_summary'",(cid,)).fetchone()[0]==1


def test_routine_privilege_stale_source_and_answer_evidence_stay_enforced(client,actor,workbench,database):
    ids,_,_=workbench;h=actor('owner');q=ids['missing'];body=routine(client,q)
    assert client.post('/api/admin/bank/routine-edits',headers={**actor('reviewer1'),'Idempotency-Key':uuid4().hex},json=body).status_code==403
    actor('owner');body=routine(client,q)
    database[1].execute('UPDATE appearances SET page=page+1 WHERE id=%s',('app-'+q,))
    assert client.post('/api/admin/bank/routine-edits',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==409
    q=ids['unverified'];body=routine(client,q,'transcription',{'options':['First','Second','Third','Fourth'],'answerIndex':0})
    assert client.post('/api/admin/bank/routine-edits',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==422
    body['note']='A note alone must not replace the missing worked answer evidence.'
    assert client.post('/api/admin/bank/routine-edits',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==422
    body['kind']='answer'
    assert client.post('/api/admin/bank/routine-edits',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==422


def test_owner_batch_note_optional_and_preview_binding_unchanged(client,actor,workbench,database):
    ids,_,_=workbench;h=actor('owner');q=ids['missing']
    preview=client.post('/api/admin/bank/retag/preview',headers=h,json={'targets':[{'question_id':q,'appearance_id':'app-'+q}]}).json()['items']
    body={'targets':[{k:p[k] for k in ('question_id','appearance_id','baseline_hash','source_version')} for p in preview],
      'classification':{'subject_id':'mizo'}}
    r=client.post('/api/admin/bank/retag/apply',headers={**h,'Idempotency-Key':uuid4().hex},json=body)
    assert r.status_code==200,r.text
    assert 'Automatic owner change summary' in database[1].execute('SELECT reason FROM admin_bank_decisions WHERE canonical_id=%s',(q,)).fetchone()[0]


def test_owner_can_publish_own_collection_without_self_review_fiction(client,actor,database):
    q=official(database)[0];h=actor('owner');p=content([q]);r=client.post('/api/learning-catalog',headers=h,json={'content':p,'reason':'Save an owner-authored test with actual bank questions.'})
    assert r.status_code==200,r.text
    row=r.json();eid=row['id']
    assert client.get('/api/learning-catalog/manage?timed=true').json()['can_owner_publish']
    body={'expected_version':row['version'],'action':'owner_publish','preview_confirmed':True}
    assert client.post('/api/learning-catalog/'+eid+'/decision',headers=h,json={**body,'preview_confirmed':False}).status_code==422
    assert client.post('/api/learning-catalog/'+eid+'/decision',headers=actor('author'),json=body).status_code==403
    r=client.post('/api/learning-catalog/'+eid+'/decision',headers=actor('owner'),json=body)
    assert r.status_code==200,r.text
    assert r.json()['state']=='published' and r.json()['live_test_version']==2
    assert client.post('/api/learning-catalog/'+eid+'/decision',headers=actor('owner'),json=body).status_code==200
    assert database[1].execute('SELECT count(*) FROM learning_test_publications WHERE entry_id=%s',(eid,)).fetchone()[0]==1
    history=database[1].execute('SELECT action,reason FROM learning_catalog_history WHERE entry_id=%s ORDER BY version DESC LIMIT 1',(eid,)).fetchone()
    assert history[0]=='owner_publish' and 'Owner publication decision' in history[1]
    assert client.get('/api/tests/'+eid).json()['revision']==2


def test_owner_paper_preview_publish_binding_and_revocation(client,actor,paper,database):
    did,h=paper;v=prepared(client,did,h)
    before=get(client,did)
    preview=client.get('/api/paper-workbench/drafts/'+did+'/owner-preview')
    assert preview.status_code==200,preview.text
    assert preview.json()['questions']==1 and preview.json()['version']==v
    body={'expected_version':v,'preview_hash':preview.json()['preview_hash'],'inspected':True}
    assert client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=h,json={**body,'inspected':False}).status_code==422
    assert client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=actor('reviewer1'),json=body).status_code==403
    r=client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=actor('owner'),json=body)
    assert r.status_code==202,r.text
    assert r.json()['approval_kind']=='owner'
    replay=client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=actor('owner'),json=body)
    assert replay.status_code==202 and replay.json()['job_id']==r.json()['job_id']
    conn=database[1]
    assert conn.execute("SELECT count(*) FROM paper_workbench_reviews WHERE draft_id=%s AND review_kind='independent'",(did,)).fetchone()[0]==0
    assert get(client,did)['state']=='queued'
    async def validate(changed=False):
        from app.db import cursor
        from app.services.paper_approval import validate_approval
        async with cursor() as cur:
            await cur.execute('SELECT * FROM paper_workbench_drafts WHERE id=%s',(did,));d=await cur.fetchone()
            await cur.execute("SELECT * FROM paper_workbench_reviews WHERE draft_id=%s AND review_kind='owner'",(did,));review=await cur.fetchone()
            if changed:d={**d,'payload':{**d['payload'],'title':'Changed source content'}}
            await validate_approval(cur,d,review)
    client.portal.call(validate)
    with pytest.raises(ValueError):client.portal.call(validate,True)
    grants=conn.execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='owner' AND role='owner' AND revoked_at IS NULL RETURNING id").fetchall()
    try:
        with pytest.raises(Exception):client.portal.call(validate)
    finally:
        for (gid,) in grants:conn.execute('UPDATE review_grants SET revoked_at=NULL WHERE id=%s',(gid,))
    assert before['payload']==get(client,did)['payload']


def test_owner_paper_preview_invalidated_by_save(client,actor,paper):
    did,h=paper;v=prepared(client,did,h);preview=client.get('/api/paper-workbench/drafts/'+did+'/owner-preview').json()
    p=get(client,did)['payload'];p['title']='A changed saved draft'
    assert save(client,did,h,p,v).status_code==200
    r=client.post('/api/paper-workbench/drafts/'+did+'/owner-publish',headers=h,json={'expected_version':v,'preview_hash':preview['preview_hash'],'inspected':True})
    assert r.status_code==409 and get(client,did)['state']=='draft'


def test_database_map_live_counts_schema_and_owner_boundary(client,actor,database):
    actor('reviewer1');assert client.get('/api/admin/bank/database-map').status_code==403
    actor('owner');r=client.get('/api/admin/bank/database-map');assert r.status_code==200,r.text
    d=r.json();assert d['read_only'] and d['observed_at']
    tables={t['id']:t for t in d['tables']}
    assert len(tables)==28 and 'users' not in tables and 'auth_sessions' not in tables
    assert tables['canonical_questions']['total']==database[1].execute('SELECT count(*) FROM canonical_questions').fetchone()[0]
    assert any(c['name']=='id' and c['primary_key'] for c in tables['canonical_questions']['columns'])
    assert any(f['source']=='appearances' and f['target']=='canonical_questions' and f['source_columns']==['canonical_id'] for f in d['foreign_keys'])
    assert all(f['source'] in tables and f['target'] in tables for f in d['foreign_keys'])
    assert 'owner@example.test' not in r.text and 'test-session-' not in r.text
    client.cookies.clear();assert client.get('/api/admin/bank/database-map').status_code==401
