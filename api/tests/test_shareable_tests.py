"""Real disposable-Postgres tests: normal creators, independent review and guest attempts."""
import hashlib
from uuid import uuid4
import pytest
from test_learning_workflows import official,learner


def content(ids,**changes):
    return {'kind':'practice','title':'Synthetic shared test '+uuid4().hex[:8],
      'description':'Read each question and choose one answer. Blanks carry no deduction.',
      'subject_id':'english','question_ids':ids,
      'test_config':{'duration_minutes':7,'marks_correct':2,'marks_wrong':0.5,'answer_mode':'official'},**changes}


def create(client,actor,database,ids=None,**changes):
    user,h=learner(database,actor)
    p=content(ids or [official(database)[0]],**changes)
    r=client.post('/api/learning-catalog',headers=h,json={'content':p,'reason':'A normal website user saves a test using existing question IDs.'})
    assert r.status_code==200,r.text
    return user,p,r.json()


def decide(client,actor,eid,user,version,action):
    return client.post('/api/learning-catalog/'+eid+'/decision',headers=actor(user),json={
      'expected_version':version,'action':action,'reason':'Inspected the test instructions, sources, question selection and marking rules.'})


def publish(client,actor,row,author):
    assert decide(client,actor,row['id'],author,row['version'],'submit').status_code==200
    r=decide(client,actor,row['id'],'reviewer1',row['version']+1,'publish')
    assert r.status_code==200,r.text
    return r.json()


def guest_start(client,eid,revision,**changes):
    headers={'Origin':'https://study.hawayu.in'}
    token=client.cookies.get('ism_session')
    if token:headers['X-Review-CSRF']=hashlib.sha256(('bank-review:'+token).encode()).hexdigest()
    return client.post('/api/mocks',headers=headers,json={
      'collection_id':'shared-tests','learning_test_id':eid,'learning_test_version':revision,**changes})


def test_normal_user_draft_independent_review_and_answer_free_share(client,actor,database):
    user,p,row=create(client,actor,database);eid=row['id']
    assert client.get('/api/tests/'+eid).status_code==404
    assert client.get('/api/tests/'+eid+'/share').status_code==404
    assert eid not in [r['id'] for r in client.get('/api/tests').json()['items']]
    assert decide(client,actor,eid,user,1,'publish').status_code==403
    published=publish(client,actor,row,user)
    client.cookies.clear()
    landing=client.get('/api/tests/'+eid)
    assert landing.status_code==200,landing.text
    meta=landing.json();assert meta['question_count']==1 and meta['revision']==published['live_test_version']==3
    assert not any(k in landing.text for k in ['answer_text','explanation','question_ids','questions"','published_by'])
    share=client.get('/api/tests/'+eid+'/share');assert share.status_code==200
    assert 'og:title' in share.text and p['title'] in share.text and '/tests/'+eid in share.text
    assert 'answer_text' not in share.text
    assert any(r['id']==eid for r in client.get('/api/tests',params={'q':p['title']}).json()['items'])
    assert 'ism_guest' not in landing.cookies


def test_guest_frozen_order_rules_resume_result_privacy_and_stats(client,actor,database):
    qs=[official(database)[0] for _ in range(2)]
    user,p,row=create(client,actor,database,qs);pub=publish(client,actor,row,user);eid=row['id']
    client.cookies.clear()
    r=guest_start(client,eid,3,count=200,duration_minutes=1,marks_correct=10,marks_wrong=10,answer_mode='derived-practice',paper_mode='full',paper_id='not-a-paper')
    assert r.status_code==200,r.text
    m=r.json();mid=m['id']
    assert m['duration_seconds']==420 and m['answer_mode']=='official' and m['paper_mode']=='practice'
    assert [q['id'] for q in m['questions']]==qs
    assert not any(k in r.text for k in ['answer_text','explanation','answer_index'])
    assert client.get('/api/mocks/current').json()['learning_test_id']==eid
    assert client.get('/api/tests/find').status_code==401  # Builder requires a real account.
    assert client.put('/api/mocks/'+mid+'/answers',json={'question_id':qs[0],'chosen_index':1,'marked':True,'position':1}).status_code==200
    resumed=client.get('/api/mocks/current').json();assert resumed['saved_answers']=={qs[0]:1} and resumed['current_position']==1
    database[1].execute("UPDATE canonical_questions SET answer_text='C',explanation='A later source update' WHERE id=%s",(qs[0],))
    result=client.post('/api/mocks/'+mid+'/submit',json={'answers':[{'question_id':qs[1],'chosen_index':0}]})
    assert result.status_code==200,result.text
    r=result.json();assert r['score']==1.5 and r['n_correct']==1 and r['n_wrong']==1
    assert r['learning_test_id']==eid and r['learning_test_version']==3
    assert r['review'][0]['answer_text']=='B'
    readback=client.get('/api/mocks/'+mid);assert readback.status_code==200 and readback.json()['learning_test_title']==p['title']
    assert guest_start(client,eid,3).status_code==409  # The published source snapshot is now stale.
    actor('outsider');assert client.get('/api/mocks/'+mid).status_code==404
    assert client.get('/api/tests/'+eid+'/stats').status_code==404
    actor(user);stats=client.get('/api/tests/'+eid+'/stats').json()
    assert stats['editions'][0]['completions']==1 and stats['editions'][0]['starts']==1
    assert all(set(r)=={'revision','starts','completions','late_completions'} for r in stats['editions'])


def test_edition_republish_draft_isolation_and_creator_withdrawal(client,actor,database):
    user,p,row=create(client,actor,database);eid=row['id'];publish(client,actor,row,user)
    h=actor(user);replacement={**p,'title':'A replacement that is still private'}
    r=client.post('/api/learning-catalog',headers=h,json={'id':eid,'expected_version':3,'content':replacement,'reason':'Revise the test without replacing the existing published edition.'})
    assert r.status_code==200,r.text
    assert client.get('/api/tests/'+eid).json()['title']==p['title']
    pub=publish(client,actor,r.json(),user);assert pub['live_test_version']==6
    client.cookies.clear();assert guest_start(client,eid,3).status_code==409
    m=guest_start(client,eid,6);assert m.status_code==200,m.text
    cookie=dict(client.cookies)
    assert decide(client,actor,eid,user,6,'withdraw').status_code==200
    client.cookies.clear();client.cookies.update(cookie)
    assert client.get('/api/tests/'+eid).status_code==404
    assert client.get('/api/mocks/current').json()['learning_test_version']==6
    mid=m.json()['id'];assert client.post('/api/mocks/'+mid+'/submit',json={'answers':[]}).status_code==200
    assert client.get('/api/mocks/'+mid).status_code==200
    assert guest_start(client,eid,6).status_code==404
    with pytest.raises(Exception):
        database[1].execute("UPDATE learning_test_publications SET payload='{}'::jsonb WHERE entry_id=%s",(eid,))


def test_test_input_safety_ownership_and_active_assessment_boundaries(client,actor,database):
    user,p,row=create(client,actor,database,title='<script>alert("x")</script> test')
    eid=row['id'];publish(client,actor,row,user)
    share=client.get('/api/tests/'+eid+'/share').text
    assert '<script>' not in share and '&lt;script&gt;' in share
    actor(user)
    assert client.get('/api/tests/find',params={'subject':'english'}).status_code==200
    assert 'answer_text' not in client.get('/api/tests/find',params={'subject':'english'}).text
    assert client.get('/api/tests/selection',params={'ids':p['question_ids']}).status_code==200
    actor('outsider')
    assert decide(client,actor,eid,'outsider',3,'withdraw').status_code==403
    bad={**p,'question_ids':[p['question_ids'][0]]*2}
    assert client.post('/api/learning-catalog',headers=actor(user),json={'content':bad,'reason':'Duplicate IDs may not create two slots.'}).status_code==422
    bad={**p,'test_config':{**p['test_config'],'marks_wrong':11}}
    assert client.post('/api/learning-catalog',headers=actor(user),json={'content':bad,'reason':'Out-of-range marks must not be accepted.'}).status_code==422
    m=guest_start(client,eid,3);assert m.status_code==200,m.text
    assert client.get('/api/tests/find').status_code==409
    assert client.get('/api/tests/selection',params={'ids':p['question_ids']}).status_code==409
    assert client.get('/api/learning-catalog/manage').status_code==409
    assert client.post('/api/mocks/'+m.json()['id']+'/submit',headers=actor(user),json={'answers':[]}).status_code==200


def test_shared_free_access_and_per_test_rate_limit_preserve_standard_quota(client,actor,database):
    user,p,row=create(client,actor,database);eid=row['id'];publish(client,actor,row,user)
    actor('outsider');conn=database[1]
    standard='standard-'+uuid4().hex
    conn.execute("""INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,submitted_at,elapsed_seconds,n_correct,n_wrong,n_skipped,score)
        VALUES(%s,'outsider','ldc',%s,60,now(),1,1,0,0,1)""",(standard,p['question_ids']))
    for _ in range(3):
        r=guest_start(client,eid,3);assert r.status_code==200,r.text
        assert client.post('/api/mocks/'+r.json()['id']+'/submit',headers=actor('outsider'),json={'answers':[]}).status_code==200
    assert guest_start(client,eid,3).status_code==429
    assert conn.execute("SELECT count(*) FROM mock_sessions WHERE user_id='outsider' AND learning_test_id=%s",(eid,)).fetchone()[0]==3
