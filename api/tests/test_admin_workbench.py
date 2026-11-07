"""Read-only repair workspace uses canonical scope and exact source appearance."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb

@pytest.fixture
def workbench(client,actor,database):
    conn=database[1];suffix=uuid4().hex[:8];paper='repair-paper-'+suffix
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,source_file,year) VALUES (%s,'Direct','Synthetic repair paper','Old_Questions/test.pdf',2020)",(paper,))
    ids={kind:'repair-'+suffix+'-'+kind for kind in ['missing','held','defect','keyed','unverified','descriptive','malformed','restricted']}
    for kind,qid in ids.items():
        answer=None if kind in {'missing','descriptive'} else 'B' if kind=='malformed' else 'B'
        source='official' if kind=='keyed' else 'derived'
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,status,source_defect) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (qid,'descriptive' if kind=='descriptive' else 'mcq','Synthetic repair '+kind,Jsonb([] if kind=='descriptive' else ['B','B'] if kind=='malformed' else ['A','B','C','D']),answer,source,'held' if kind=='held' else 'live','unresolved-source' if kind=='defect' else None))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,%s,%s,'test','manual','approved')",(qid,'mizo' if kind=='restricted' else 'english','Mizo' if kind=='restricted' else 'English'))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page,direction,question_markup) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,true,'1',1,'Choose one option','**Synthetic repair**')",
            ('app-'+qid,paper,'descriptive' if kind=='descriptive' else 'mcq','Synthetic repair '+kind,Jsonb([] if kind=='descriptive' else ['A','B','C','D']),None if answer is None or kind=='malformed' else 1,source,qid))
    other='alternate-'+suffix
    conn.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES (%s,'Direct','Alternate synthetic paper')",(other,))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES (%s,%s,'mcq','Alternate printed words',%s,2,'derived',%s,false,'19',4)",('alt-'+suffix,other,Jsonb(['C','A','B','D']),ids['unverified']))
    return ids,paper,'alt-'+suffix


def test_admin_issue_filters_and_pagination(client,actor,workbench):
    ids,paper,alt=workbench;actor('owner')
    for issue in ['missing','held','defect','keyed','descriptive','malformed']:
        response=client.get('/api/admin/bank/questions',params={'paper_id':paper,'issue':issue})
        assert response.status_code==200,response.text
        assert [q['id'] for q in response.json()['items']]==[ids[issue]]
    response=client.get('/api/admin/bank/questions',params={'paper_id':paper,'missing':True})
    assert [q['id'] for q in response.json()['items']]==[ids['missing']]
    assert response.json()['items'][0]['missing_answer'] is True
    first=client.get('/api/admin/bank/questions',params={'paper_id':paper,'limit':2}).json()
    second=client.get('/api/admin/bank/questions',params={'paper_id':paper,'limit':2,'offset':2}).json()
    assert first['total']==second['total']==8
    assert not set(q['id'] for q in first['items'])&set(q['id'] for q in second['items'])
    assert client.get('/api/admin/bank/questions',params={'issue':'made-up'}).status_code==422
    assert client.get('/api/admin/bank/questions',params={'q':'x'*201}).status_code==422


def test_inspection_scope_exact_appearance_and_active_mock(client,actor,workbench,database):
    ids,paper,alt=workbench;h=actor('reviewer1')
    assert client.get('/api/admin/bank/questions/'+ids['restricted']+'/inspect').status_code==404
    rows=client.get('/api/admin/bank/questions',params={'paper_id':paper}).json()['items']
    assert ids['restricted'] not in {q['id'] for q in rows}
    qid=ids['unverified']
    response=client.get('/api/admin/bank/questions/'+qid+'/inspect',params={'appearance_id':alt})
    assert response.status_code==200,response.text
    body=response.json();assert body['snapshot']['record']['id']==alt
    assert body['snapshot']['record']['options']==['C','A','B','D']
    assert body['snapshot']['record']['qnum']=='19' and body['snapshot']['record']['page']==4
    assert body['appearance_total']==2
    assert body['canonical']['answer_text']=='B'
    paper_rows=client.get('/api/admin/bank/questions',params={'paper_id':body['snapshot']['paper']['id']}).json()['items']
    assert len(paper_rows)==1 and paper_rows[0]['appearance_id']==alt and paper_rows[0]['qnum']=='19'
    assert client.get('/api/admin/bank/questions/'+qid+'/inspect',params={'appearance_id':'app-'+ids['missing']}).status_code==404
    cid='wb-collection-'+uuid4().hex
    database[1].execute("INSERT INTO collections(id,title,kind) VALUES (%s,'Synthetic repair mock','exam')",(cid,))
    database[1].execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES (%s,'reviewer1',%s,%s,60)",('wb-'+uuid4().hex,cid,[qid]))
    assert client.get('/api/admin/bank/questions/'+qid+'/inspect').status_code==409
    actor('outsider')
    assert client.get('/api/admin/bank/questions/'+qid+'/inspect').status_code==404
    assert client.get('/api/admin/bank/questions').status_code==403


def test_inspector_source_formatting_and_paging(client,actor,workbench):
    ids,paper,alt=workbench;actor('owner')
    body=client.get('/api/admin/bank/questions/'+ids['missing']+'/inspect').json()
    assert body['snapshot']['record']['direction']=='Choose one option'
    assert body['snapshot']['record']['questionMarkup']=='**Synthetic repair**'
    assert body['snapshot']['paper']['source_pdf_url']=='/papers/source/Old_Questions/test.pdf'
    assert body['snapshot']['record']['answerIndex'] is None
    body=client.get('/api/admin/bank/questions/'+ids['missing']+'/inspect',params={'appearance_offset':50}).json()
    assert body['appearances']==[] and body['appearance_total']==1


def test_review_tasks_are_disjoint_scoped_and_follow_latest_kind(client,actor,workbench,database):
    ids,paper,_=workbench;conn=database[1]
    def work(qid,kind,state,days=0):
        cid='queue-'+uuid4().hex
        conn.execute("""INSERT INTO bank_contributions(id,author_id,canonical_id,kind,subject_id,title,state,idempotency_key,request_hash,updated_at)
          VALUES(%s,'owner',%s,%s,'english','Synthetic queue work',%s,%s,'test',now()-(%s*interval '1 day'))""",(cid,qid,kind,state,cid,days))
        return cid
    failed=work(ids['unverified'],'answer','publication_failed')
    work(ids['keyed'],'answer','publication_failed',1)
    work(ids['keyed'],'answer','published') # old failure cannot hide newer completion
    pending=work(ids['missing'],'explanation','publishing')
    actor('owner');params={'paper_id':paper,'issue':'all'}
    all_rows=client.get('/api/admin/bank/questions',params=params).json()
    assert all_rows['total']==8
    assert all_rows['task_counts']=={'all':8,'failed':1,'publishing':1,'source':2,'answer':2,'other':2}
    lanes={}
    for lane in ('answer','source','failed','publishing'):
        response=client.get('/api/admin/bank/questions',params={**params,'review_task':lane})
        assert response.status_code==200,response.text
        body=response.json();assert body['total']==body['task_counts'][lane]
        lanes[lane]={r['id'] for r in body['items']}
        assert all(r['review_reason'] for r in body['items'])
    assert lanes['failed']=={ids['unverified']}
    assert lanes['publishing']=={ids['missing']}
    assert lanes['source']=={ids['held'],ids['defect']}
    assert not any(lanes[a]&lanes[b] for a in lanes for b in lanes if a!=b)
    row=client.get('/api/admin/bank/questions',params={**params,'review_task':'failed'}).json()['items'][0]
    assert row['work_id']==failed and row['work_kind']=='answer'
    actor('reviewer1')
    body=client.get('/api/admin/bank/questions',params=params).json()
    assert body['total']==7 and body['task_counts']['answer']==1
    assert ids['restricted'] not in {r['id'] for r in body['items']}
    assert client.get('/api/admin/bank/questions',params={'review_task':'pretend-done'}).status_code==422
    actor('outsider');assert client.get('/api/admin/bank/questions',params={'review_task':'failed'}).status_code==403
