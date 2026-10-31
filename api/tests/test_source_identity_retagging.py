"""Operational identity and taxonomy changes must remain separate and reviewable."""
from uuid import uuid4
import pytest
from test_admin_workbench import workbench
BASE='/api/admin/bank'


def identity_body(client,paper):
    current=client.get(BASE+'/inventory/identity',params={'paper_id':paper}).json()
    return {'paper_id':paper,'expected_version':current['saved']['version'] if current['saved'] else 0,
            'expected_context':current['context'],'source_checked':True,
            'exam_title':'Reviewed UDC examination','exam_year':2025,
            'paper_title':'Paper I · General Knowledge and English',
            'sections':[{'title':'General Knowledge','qnum_from':1,'qnum_to':75}],
            'evidence_page':1,'reason':'Inspected original cover and printed section heading for this test.'}


def test_identity_permissions_conflicts_sections_and_source_display(client,actor,workbench,database):
    ids,paper,_=workbench
    h=actor('owner');body=identity_body(client,paper)
    assert client.post(BASE+'/inventory/identity',json=body).status_code==403
    invalid={**body,'sections':[{'title':'GK','qnum_from':5,'qnum_to':3}]}
    assert client.post(BASE+'/inventory/identity',headers=h,json=invalid).status_code==422
    invalid={**body,'sections':[{'title':'GK','qnum_from':1,'qnum_to':10},{'title':'English','qnum_from':10,'qnum_to':20}]}
    assert client.post(BASE+'/inventory/identity',headers=h,json=invalid).status_code==422
    # A changed source after opening the form cannot be attested accidentally.
    database[1].execute("UPDATE appearances SET page=2 WHERE paper_id=%s",(paper,))
    assert client.post(BASE+'/inventory/identity',headers=h,json=body).status_code==409
    body=identity_body(client,paper)
    r=client.post(BASE+'/inventory/identity',headers=h,json=body);assert r.status_code==200,r.text
    assert r.json()['version']==1
    assert client.post(BASE+'/inventory/identity',headers=h,json=body).status_code==409
    detail=client.get('/api/questions/'+ids['unverified']).json()
    printed=next(a for a in detail['appearances'] if a['paper_id']==paper)
    assert printed['paper_label']==body['paper_title'] and printed['section_label']=='General Knowledge'
    assert printed['exam']==body['exam_title'] and printed['year']==2025
    # No question tag or bank-authored paper metadata was rewritten.
    assert detail['taxonomy_subject_id']=='english'
    assert database[1].execute('SELECT year FROM papers WHERE id=%s',(paper,)).fetchone()[0]==2020
    r=client.get('/api/questions',params={'paper_id':paper,'q':'Synthetic repair','limit':100})
    assert r.status_code==200,r.text
    assert all(q['source_appearance']['section_label']=='General Knowledge' for q in r.json()['items'])
    assert any(e['action']=='source_identity_verified'and e['target_id']==paper for e in client.get(BASE+'/inventory/events').json())
    assert any(i['paper_id']==paper for i in client.get(BASE+'/inventory/export').json()['bank_paper_identities'])
    # Changed source references no longer inherit an admin overlay.
    database[1].execute("UPDATE papers SET source_file='Old_Questions/replacement.pdf' WHERE id=%s",(paper,))
    assert next(a for a in client.get('/api/questions/'+ids['unverified']).json()['appearances'] if a['paper_id']==paper)['paper_label'] is None
    actor('reviewer1');assert client.get(BASE+'/inventory/identity',params={'paper_id':paper}).status_code==403
    actor('outsider');assert client.get(BASE+'/retag/batches').status_code==403


def preview(client,headers,ids):
    r=client.post(BASE+'/retag/preview',headers=headers,json={'targets':[{'question_id':q,'appearance_id':'app-'+q} for q in ids]})
    assert r.status_code==200,r.text
    assert 'answerIndex'not in r.text and 'answer_text'not in r.text
    return r.json()['items']


def batch_body(items):
    return {'targets':[{k:q[k] for k in ('question_id','appearance_id','baseline_hash')} for q in items],
            'classification':{'subject_id':'mizo','topic_id':None,'subtopic_id':None},
            'rationale':'Synthetic topic repair after inspecting each selected question.',
            'evidence_note':'The wording of each question supports the proposed subject in this isolated test.'}


def test_batch_atomic_stale_idempotency_and_review_flow(client,actor,workbench,database):
    ids,paper,_=workbench;h=actor('owner');targets=[ids['missing'],ids['unverified']]
    items=preview(client,h,targets);body=batch_body(items);key='batch-'+uuid4().hex
    # Reject every write if even the last preview changed.
    bad={**body,'targets':[body['targets'][0],{**body['targets'][1],'baseline_hash':'0'*64}]}
    r=client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':key},json=bad)
    assert r.status_code==409,r.text
    assert database[1].execute('SELECT count(*) FROM bank_contributions WHERE canonical_id=ANY(%s)',(targets,)).fetchone()[0]==0
    r=client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':key},json=body)
    assert r.status_code==200,r.text;result=r.json()
    assert len(result['contribution_ids'])==2
    assert client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':key},json=body).json()==result
    altered={**body,'rationale':'Different rationale which must not reuse the previous request key.'}
    assert client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':key},json=altered).status_code==409
    detail=client.get(BASE+'/retag/batches/'+result['id']);assert detail.status_code==200
    assert detail.headers['cache-control']=='private, no-store'
    assert all(i['state']=='submitted'and not i['can_review'] for i in detail.json()['items'])
    cid=result['contribution_ids'][0]
    c=client.get('/api/contributions/'+cid).json()
    assert client.post('/api/review/'+cid+'/decisions',headers=h,json={'expected_version':c['lock_version'],'reason':'Synthetic independent review guard check.','decision':'approve'}).status_code==403
    # Tags remain untouched until independent approval and ordinary publication.
    assert database[1].execute('SELECT subject_id FROM question_classifications WHERE question_id=%s',(targets[0],)).fetchone()[0]=='english'
    database[1].execute("INSERT INTO review_grants(user_id,role,granted_by,reason) VALUES('reviewer2','senior','test','Global permission for isolated batch review')")
    rh=actor('reviewer2');d=client.get(BASE+'/retag/batches/'+result['id']).json();assert all(i['can_review']for i in d['items'])
    for item in d['items']:
        r=client.post('/api/review/'+item['id']+'/decisions',headers=rh,json={'expected_version':item['lock_version'],'reason':'Independently inspected the question and selected taxonomy path.','decision':'approve'})
        assert r.status_code==200 and r.json()['state']=='accepted',r.text
    actor('owner');d=client.get(BASE+'/retag/batches/'+result['id']).json();assert all(i['can_publish']for i in d['items'])
    assert client.get(BASE+'/retag/batches').json()


def test_batch_rejects_duplicate_targets_noops_invalid_path_and_active_mock(client,actor,workbench,database):
    ids,paper,_=workbench;h=actor('owner');target={'question_id':ids['missing'],'appearance_id':'app-'+ids['missing']}
    assert client.post(BASE+'/retag/preview',headers=h,json={'targets':[target,target]}).status_code==422
    items=preview(client,h,[ids['missing']]);body=batch_body(items);body['classification']={'subject_id':'english'}
    assert client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==422
    body['classification']={'subject_id':'mizo','topic_id':'not-a-valid-topic'}
    assert client.post(BASE+'/retag/proposals',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==422
    mid=uuid4().hex
    database[1].execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','ldc',%s,60)",(mid,[ids['missing']]))
    assert client.post(BASE+'/retag/preview',headers=h,json={'targets':[target]}).status_code==409
    database[1].execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    actor('reviewer1');assert client.post(BASE+'/retag/proposals',headers=actor('reviewer1'),json=body).status_code==422  # Missing key rejected before permission; supplying one is forbidden.
    assert client.post(BASE+'/retag/proposals',headers={**actor('reviewer1'),'Idempotency-Key':uuid4().hex},json=body).status_code==403


def test_shared_gk_gs_topics_counts_legacy_links_and_pending_exclusion(client,actor,database):
    from test_library_topics import question
    from psycopg.types.json import Jsonb
    conn=database[1];actor('owner')
    gs,gs_a=question(conn,primary='general-studies',related=False)
    gk,gk_a=question(conn,primary='general-studies',related=False)
    pending,_=question(conn,primary='general-studies',related=False)
    conn.execute("UPDATE question_classifications SET subject_id='general-knowledge',subject_label='General Knowledge',topic_id='general-knowledge/geography' WHERE question_id=%s",(gk,))
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE question_id=%s",(pending,))
    # A canonical question with both approved paths counts only once.
    conn.execute("INSERT INTO question_topic_links VALUES (%s,'general-knowledge/geography','general-knowledge','General Knowledge','general-knowledge/geography','Geography',NULL,NULL,'test','manual','approved','Synthetic shared discovery path')",(gs,))
    facets=client.get('/api/questions/taxonomy',params={'learning':True}).json()
    assert not any(f['subject_id']in ('general-knowledge','general-studies')for f in facets)
    geography=next(f for f in facets if f['subject_id']=='gk-gs'and f['topic']=='Geography')
    assert geography['topic_id']=='gk-gs:geography'
    params={'subject_id':'gk-gs','topic_id':'gk-gs:geography','q':'synthetic library river','limit':100}
    result=client.get('/api/questions',params=params);assert result.status_code==200,result.text
    got={q['id']for q in result.json()['items']}
    assert {gs,gk}<=got and pending not in got
    assert result.json()['total']==len(got)
    assert client.get('/api/questions',params={**params,'topic_id':'general-studies/geography'}).status_code==200
    # Group B topic maps and topic filters use identical shared topic IDs.
    for a in (gs_a,gk_a):
        pid='shared-topic-paper-'+a
        conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) VALUES(%s,'Direct_NG','Synthetic common GK paper',2025,'mizoram-recruitment')",(pid,))
        conn.execute('UPDATE appearances SET paper_id=%s WHERE id=%s',(pid,a))
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) VALUES('group-b-non-gazetted',1,%s,false)",(pid,))
    tree=client.get('/api/collections/group-b/study-topics',params={'study_area':'gk-gs'}).json()
    shared=next(s for s in tree['subjects']if s['id']=='gk-gs')
    item=next(t for t in shared['topics']if t['id']=='gk-gs:geography')
    assert item['questions']==2
    rows=client.get('/api/questions',params={**params,'collection_id':'group-b','study_area':'gk-gs'}).json()
    assert rows['total']==2
