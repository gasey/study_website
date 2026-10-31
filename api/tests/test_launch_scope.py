"""The launch stays in Mizoram while global canonical data remains extensible."""
from uuid import uuid4
from psycopg.types.json import Jsonb


def test_outside_and_unassigned_imports_do_not_enter_launch_pools(client,actor,database):
    conn=database[1];tag=uuid4().hex[:8];sid='outside-'+tag;pid='scope-paper-'+tag;cid='scope-exam-'+tag
    before=client.get('/api/library/shelves').json()
    before_geo=next(s['questions'] for s in before if s['id']=='geography')
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) VALUES (%s,'Direct','English OutsideScopeSentinel',2026,'outside-mizoram')",(pid,))
    conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version,exam_scope_id) VALUES (%s,'OutsideScopeSentinel Exam','exam','public',1,'outside-mizoram')",(cid,))
    conn.execute('INSERT INTO collection_papers(collection_id,version,paper_id) VALUES (%s,1,%s)',(cid,pid))
    ids=[]
    for n in range(12):
        qid='cq_scope_'+tag+'_'+str(n);ids.append(qid)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES (%s,'mcq',%s,%s,'B','official')",(qid,'OutsideScopeSentinel question '+str(n),Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) VALUES (%s,%s,'mcq',%s,%s,1,'official',%s,true)",('a_'+qid,pid,'OutsideScopeSentinel question '+str(n),Jsonb(['A','B','C','D']),qid))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES (%s,%s,'OutsideScopeSentinel','test','manual','approved')",(qid,sid))
        conn.execute("INSERT INTO question_topic_links VALUES (%s,'general-studies/geography','general-studies','General Studies','general-studies/geography','Geography',NULL,NULL,'test','manual','approved','Synthetic source-scope test')",(qid,))
    h=actor('author')
    assert client.get('/api/questions?q=OutsideScopeSentinel').json()['total']==0
    assert client.get('/api/questions/'+ids[0]).status_code==404
    assert client.post('/api/questions/'+ids[0]+'/answer',headers=h,json={'chosen_index':1}).status_code==404
    assert client.get('/api/collections/'+cid).status_code==404
    assert cid not in [c['id'] for c in client.get('/api/collections').json()]
    assert pid not in [p['id'] for p in client.get('/api/questions/papers').json()['items']]
    assert not any(f['subject_id']==sid for f in client.get('/api/questions/taxonomy').json())
    search=client.get('/api/search?q=OutsideScopeSentinel').json()
    assert all(g['total']==0 for g in search['groups'] if g['category'] in ('questions','exams'))
    assert sid not in [s['id'] for s in client.get('/api/games').json()['subjects']]
    r=client.post('/api/games/rooms',headers=h,json={'mode':'speed','subject_id':sid,'request_key':uuid4().hex});assert r.status_code==422,r.text
    assert client.post('/api/mocks',headers=h,json={'collection_id':cid,'count':1,'duration_minutes':1}).status_code==404
    assert next(s['questions'] for s in client.get('/api/library/shelves').json() if s['id']=='geography')==before_geo
    # Explicit All exams opens the full engine, preserving source and grading.
    assert client.get('/api/questions?q=OutsideScopeSentinel&exam_scope=all').json()['total']==12
    detail=client.get('/api/questions/'+ids[0]+'?exam_scope=all')
    assert detail.status_code==200 and detail.json()['appearances'][0]['paper_id']==pid
    assert client.post('/api/questions/'+ids[0]+'/answer?exam_scope=all',headers=h,json={'chosen_index':1}).json()['correct'] is True
    assert client.get('/api/collections/'+cid+'?exam_scope=all').json()['paper_list'][0]['id']==pid
    assert cid in [c['id'] for c in client.get('/api/collections?exam_scope=all').json()]
    assert pid in [p['id'] for p in client.get('/api/questions/papers?exam_scope=all').json()['items']]
    assert any(f['subject_id']==sid for f in client.get('/api/questions/taxonomy?exam_scope=all').json())
    global_search=client.get('/api/search?q=OutsideScopeSentinel&exam_scope=all').json()
    assert next(g['total'] for g in global_search['groups'] if g['category']=='questions')==12
    assert next(s['questions'] for s in client.get('/api/library/shelves?exam_scope=all').json() if s['id']=='geography')==before_geo+12
    assert cid in [e['id'] for e in client.get('/api/library/shelves/geography?exam_scope=all').json()['exams']]
    assert client.get('/api/questions?exam_scope=bogus').status_code==422
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES (%s,1,'general','General',1,%s)",(cid,Jsonb({'paper_ids':[pid]})))
    mock=client.post('/api/mocks?exam_scope=all',headers=h,json={'collection_id':cid,'count':1,'duration_minutes':1})
    assert mock.status_code==200,mock.text
    assert mock.json()['questions'][0]['id'] in ids
    assert client.post('/api/mocks/'+mock.json()['id']+'/submit',headers=h,json={'answers':[]}).status_code==200
    # All does not make private or retired exam collections public.
    conn.execute("UPDATE collections SET visibility='hidden' WHERE id=%s",(cid,))
    assert client.get('/api/collections/'+cid+'?exam_scope=all').status_code==404
    conn.execute("UPDATE collections SET visibility='public' WHERE id=%s",(cid,))
    # Canonical source truth remains available to the future multi-scope engine.
    conn.execute("UPDATE collections SET exam_scope_id='mizoram-recruitment' WHERE id=%s",(cid,))
    assert client.get('/api/collections/'+cid).json()['paper_list']==[]
    conn.execute("UPDATE collections SET exam_scope_id='outside-mizoram' WHERE id=%s",(cid,))
    assert conn.execute('SELECT count(*) FROM v_scorable WHERE id=ANY(%s)',(ids,)).fetchone()[0]==12
    conn.execute('UPDATE papers SET exam_scope_id=NULL WHERE id=%s',(pid,))
    assert client.get('/api/questions?q=OutsideScopeSentinel').json()['total']==0
    # A paper may be assigned to the launch explicitly without copying questions.
    conn.execute("UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE id=%s",(pid,))
    assert client.get('/api/questions?q=OutsideScopeSentinel').json()['total']==12
    assert sid in [s['id'] for s in client.get('/api/games').json()['subjects']]
    conn.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id=%s",(pid,))
