"""Saved UDC study sets: real isolated PostgreSQL, synthetic learners and papers."""
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from psycopg.types.json import Jsonb
from test_learning_workflows import learner


def seed(database,n=3):
    conn=database[1];tag=uuid4().hex;p='set-paper-'+tag
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic UDC study paper',2025)",(p,))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) SELECT 'udc',live_version,%s,'papers' FROM collections WHERE id='udc'",(p,))
    ids=[]
    for i in range(n):
        q='set-'+tag+'-'+str(i);ids.append(q)
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,'B','official')",(q,'Synthetic set question '+str(i),Jsonb(['A','B','C','D'])))
        conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,type,question,options,answer_index,answer_source,is_primary,qnum) VALUES(%s,%s,%s,'mcq','Synthetic set question',%s,1,'official',true,%s)",(q+'-a',p,q,Jsonb(['A','B','C','D']),str(i+1)))
    return p,ids


def start(client,h,p,size=10,**filters):
    body={'request_key':uuid4().hex,'size':size,'filters':{'paper_id':p,**filters}}
    r=client.post('/api/study-sessions',headers=h,json=body)
    assert r.status_code==200,r.text
    return r.json(),body


def test_admin_edit_rejects_stale_options_and_saved_feedback_flags_later_correction(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database);conn=database[1]
    s,_=start(client,h,p);qid=ids[0];url='/api/study-sessions/'+s['id']
    token=s['items'][0]['presentation_hash']
    conn.execute('UPDATE canonical_questions SET options=%s WHERE id=%s',(Jsonb(['B','A','C','D']),qid))
    conn.execute('UPDATE appearances SET options=%s,answer_index=0 WHERE canonical_id=%s',(Jsonb(['B','A','C','D']),qid))
    body={'version':s['version'],'question_id':qid,'chosen_index':0,'presentation_hash':token}
    response=client.post(url+'/answer',headers=h,json=body)
    assert response.status_code==409 and 'no attempt was recorded' in response.json()['detail']
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    current=client.get(url).json()
    assert current['items'][0]['presentation_hash']!=token
    body['presentation_hash']=current['items'][0]['presentation_hash']
    response=client.post(url+'/answer',headers=h,json=body)
    assert response.status_code==200,response.text
    assert response.json()['results'][qid]['result']['correct'] is True
    conn.execute("UPDATE canonical_questions SET answer_text='C',answer_source='derived' WHERE id=%s",(qid,))
    conn.execute("UPDATE appearances SET answer_index=2,answer_source='derived' WHERE canonical_id=%s",(qid,))
    saved=client.get(url).json();answer=saved['results'][qid]
    assert answer['result']['answer_text']=='B' and answer['result']['correct'] is True
    assert {'answer','answer source'}<=set(answer['updated_fields'])
    assert saved['items'][0]['answer_source']=='official' and saved['items'][0]['answer_status']=='official'
    assert saved['summary']['correct']==1
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==1


def test_frozen_partial_set_refresh_and_scope(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database)
    s,body=start(client,h,p,size=20)
    assert s['requested_size']==20 and s['summary']['total']==3
    assert s['question_ids']==ids and len(s['items'])==3 and s['results']=={}
    assert 'answer_text' not in str(s['items'])
    assert {q['source_appearance']['paper_id'] for q in s['items']}=={p}
    again=client.post('/api/study-sessions',headers=h,json=body).json()
    assert again['id']==s['id']
    moved=client.post('/api/study-sessions/'+s['id']+'/position',headers=h,json={'version':s['version'],'position':2})
    assert moved.status_code==200,moved.text
    restored=client.get('/api/study-sessions/'+s['id']).json()
    assert restored['question_ids']==ids and restored['position']==2
    assert client.post('/api/study-sessions/'+s['id']+'/position',headers=h,json={'version':1,'position':0}).status_code==409
    assert client.post('/api/study-sessions/'+s['id']+'/position',headers=h,json={'version':restored['version'],'position':9}).status_code==422
    other,oh=learner(database,actor)
    assert client.get('/api/study-sessions/'+s['id'],headers=oh).status_code==404
    assert client.post('/api/study-sessions/'+s['id']+'/finish',headers=oh,json={'version':2}).status_code==404
    assert client.post('/api/study-sessions',headers=oh,json={**body,'request_key':uuid4().hex,'filters':{'paper_id':'not-udc'}}).status_code==422


def test_answer_replay_finish_and_wrong_review(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database);conn=database[1]
    s,_=start(client,h,p);url='/api/study-sessions/'+s['id']
    check={'version':s['version'],'question_id':ids[0],'chosen_index':0}
    def answer(_):return client.post(url+'/answer',headers=h,json=check)
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(answer,range(2)))
    assert [r.status_code for r in responses]==[200,200],[r.text for r in responses]
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==1
    s=responses[0].json();assert s['results'][ids[0]]['result']['correct'] is False
    assert s['summary']['wrong']==1
    r=client.get(url);assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
    s=r.json();assert s['results'][ids[0]]['chosen_index']==0
    conn.execute("UPDATE canonical_questions SET question='Changed after this attempt',options=%s WHERE id=%s",(Jsonb(['B','A','C','D']),ids[0]))
    conn.execute('UPDATE appearances SET has_diagram=true,figure_image=%s WHERE canonical_id=%s',('images/page-renders/'+('a'*20)+'.png',ids[0]))
    saved=client.get(url).json()['items'][0]
    assert saved['question']=='Synthetic set question 0' and saved['options']==['A','B','C','D']
    assert saved['figure_image_url'] is None and saved['has_diagram'] is False
    assert client.post(url+'/answer',headers=h,json={**check,'chosen_index':1}).status_code==409
    finish=client.post(url+'/finish',headers=h,json={'version':s['version']})
    assert finish.status_code==200,finish.text
    done=finish.json();assert done['summary']=={'correct':0,'wrong':1,'viewed':0,'skipped':2,'unofficial':0,'total':3}
    assert client.post(url+'/finish',headers=h,json={'version':1}).json()['summary']==done['summary']
    assert client.post(url+'/answer',headers=h,json={'version':done['version'],'question_id':ids[1],'chosen_index':1}).status_code==409
    review=client.post('/api/study-sessions',headers=h,json={'request_key':uuid4().hex,'review_session_id':s['id']})
    assert review.status_code==200,review.text
    assert review.json()['question_ids']==[ids[0]]
    journey=client.get('/api/me/exam-journey/udc').json()
    assert journey['active_study_session']['id']==review.json()['id']
    assert journey['recent_study_sessions'][0]['summary']['wrong']==1


def test_viewed_answers_never_become_attempts(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database);conn=database[1]
    s,_=start(client,h,p);url='/api/study-sessions/'+s['id']
    assert client.post(url+'/viewed',headers=h,json={'question_id':ids[0]}).status_code==409
    r=client.post('/api/questions/'+ids[0]+'/reveal',headers=h,params={'paper_id':p})
    assert r.status_code==200,r.text
    s=client.post(url+'/viewed',headers=h,json={'question_id':ids[0]}).json()
    assert s['summary']['viewed']==1 and s['summary']['correct']==0
    assert client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1}).status_code==409
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert client.post('/api/questions/'+ids[1]+'/reveal',headers=h,params={'paper_id':p}).status_code==200
    # No client acknowledgement for this reveal: finishing reconciles it.
    done=client.post(url+'/finish',headers=h,json={'version':s['version']}).json()
    assert done['summary']['viewed']==2 and done['summary']['skipped']==1


def test_changing_wrong_queue_does_not_shuffle_session(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database);conn=database[1]
    for q in ids:conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,collection_id,paper_id) VALUES(%s,%s,false,'A','practice','udc',%s)",(user,q,p))
    s,_=start(client,h,p,study_status='wrong');url='/api/study-sessions/'+s['id']
    r=client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert r.status_code==200,r.text
    s=r.json();s=client.post(url+'/position',headers=h,json={'version':s['version'],'position':1}).json()
    restored=client.get(url).json()
    assert restored['question_ids']==ids and restored['position']==1
    assert restored['results'][ids[0]]['result']['correct']


def test_guest_identity_and_expired_account_boundaries(client,actor,database):
    p,ids=seed(database);client.cookies.clear()
    s,_=start(client,{'Origin':'https://study.hawayu.in'},p)
    proof=client.cookies.get('ism_guest');assert proof
    assert client.post('/api/questions/'+ids[1]+'/reveal',params={'paper_id':p}).status_code==200
    checked=client.post('/api/study-sessions/'+s['id']+'/answer',json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert checked.status_code==200,checked.text
    assert client.get('/api/study-sessions/'+s['id']).status_code==200
    client.cookies.clear()
    assert client.get('/api/study-sessions/'+s['id'],headers={'X-Device-Id':str(uuid4())}).status_code==404
    client.cookies.clear();client.cookies.set('ism_guest',proof)
    user,h=learner(database,actor)
    client.cookies.set('ism_guest',proof)
    adopted=client.post('/api/auth/guest-progress/save',headers=h,json={})
    assert adopted.status_code==200,adopted.text
    restored=client.get('/api/study-sessions/'+s['id'])
    assert restored.status_code==200 and restored.json()['results'][ids[0]]['result']['correct']
    blocked=client.post('/api/questions/'+ids[1]+'/answer',headers=h,json={'chosen_index':1,'paper_id':p,'collection_id':'udc'})
    assert blocked.status_code==409 and '30 minutes' in blocked.text
    client.cookies.clear();client.cookies.set('ism_session','expired-test')
    assert client.post('/api/study-sessions',headers={'Origin':'https://study.hawayu.in'},json={'request_key':uuid4().hex}).status_code in (401,403)


def test_atomic_failure_cannot_leave_an_attempt_or_award(client,actor,database,monkeypatch):
    from fastapi import HTTPException
    from app.routers import study_sessions
    user,h=learner(database,actor);p,ids=seed(database)
    s,_=start(client,h,p);original=study_sessions._answer_question
    async def fail_after_check(*args,**kwargs):
        await original(*args,**kwargs)
        raise HTTPException(503,'Synthetic failure after checking, before saving set')
    monkeypatch.setattr(study_sessions,'_answer_question',fail_after_check)
    r=client.post('/api/study-sessions/'+s['id']+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert r.status_code==503
    conn=database[1]
    for table in ('attempts','practice_request_receipts','reward_ledger'):
        assert conn.execute('SELECT count(*) FROM '+table+' WHERE user_id=%s',(user,)).fetchone()[0]==0
    monkeypatch.setattr(study_sessions,'_answer_question',original)
    r=client.post('/api/study-sessions/'+s['id']+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert r.status_code==200 and r.json()['summary']['correct']==1


def test_finished_feedback_cannot_bypass_active_test(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database)
    s,_=start(client,h,p);url='/api/study-sessions/'+s['id']
    r=client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert r.status_code==200
    s=client.post(url+'/finish',headers=h,json={'version':r.json()['version']}).json()
    mid=uuid4().hex;conn=database[1]
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'ldc',%s,60)",(mid,user,[ids[0]]))
    assert client.get(url).status_code==409
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    assert client.get(url).status_code==200


def test_unofficial_feedback_is_not_presented_as_official(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database,1)
    database[1].execute("UPDATE canonical_questions SET answer_source='inferred' WHERE id=%s",(ids[0],))
    s,_=start(client,h,p);r=client.post('/api/study-sessions/'+s['id']+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert r.status_code==200,r.text
    assert r.json()['summary']['unofficial']==1
    assert r.json()['results'][ids[0]]['result']['verified'] is False


def test_twenty_question_cap_is_real(client,actor,database):
    user,h=learner(database,actor);p,ids=seed(database,23)
    s,_=start(client,h,p,size=20)
    assert s['requested_size']==20 and s['total']==20 and len(s['items'])==20
    assert len(set(s['question_ids']))==20
    assert set(s['question_ids'])<set(ids)
    assert s['summary']['skipped']==20
    assert database[1].execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0
