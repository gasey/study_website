"""Real isolated DB: mixed pages and attempt filters, without recording live data."""
from uuid import uuid4
from test_study_sessions import seed, start
from test_learning_workflows import learner


def test_seeded_pages_cover_filtered_pool_and_refresh_stays_stable(client, actor, database):
    _,h=learner(database,actor);p,ids=seed(database,36)
    query={'collection_id':'udc','paper_id':p,'order':'mixed','seed':'first-mix','limit':12}
    def page(**extra):
        r=client.get('/api/questions',headers=h,params={**query,**extra})
        assert r.status_code==200,r.text
        return r.json()
    first=page();again=page();second=page(offset=12);third=page(offset=24)
    getids=lambda p:[q['id'] for q in p['items']]
    assert getids(first)==getids(again)
    assert set(getids(first)+getids(second)+getids(third))==set(ids)
    assert len(set(getids(first)+getids(second)+getids(third)))==36
    assert getids(first)!=getids(page(seed='another-mix'))
    assert getids(page(order='repeated'))==sorted(ids)[:12]
    assert first['total']==36
    assert all(q['source_appearance']['paper_id']==p for q in first['items'])
    assert all('answer_text' not in q for q in first['items'])
    for seed_value in ['',"bad;seed",'x'*65]:
        assert client.get('/api/questions',headers=h,params={**query,'seed':seed_value}).status_code==422


def test_never_attempted_and_ever_wrong_are_distinct_from_latest_wrong(client,actor,database):
    user,h=learner(database,actor);other,oh=learner(database,actor);p,ids=seed(database,4)
    conn=database[1]
    for qid,correct in [(ids[0],False),(ids[0],True),(ids[1],False),(ids[2],True)]:
        conn.execute("INSERT INTO attempts(user_id,canonical_id,paper_id,collection_id,context,chosen_text,correct) VALUES(%s,%s,%s,'udc','practice','A',%s)",(user,qid,p,correct))
    def filtered(status,headers=h):
        actor(other if headers is oh else user)
        r=client.get('/api/questions',headers=headers,params={'collection_id':'udc','paper_id':p,'study_status':status,'order':'mixed','seed':'stable'})
        assert r.status_code==200,r.text
        return {q['id'] for q in r.json()['items']}
    assert filtered('unseen')=={ids[3]}
    assert filtered('ever_wrong')==set(ids[:2])
    assert filtered('wrong')=={ids[1]}
    assert filtered('answered')==set(ids[:3])
    assert filtered('ever_wrong',oh)==set()
    assert filtered('unseen',oh)==set(ids)
    client.post('/api/questions/'+ids[3]+'/reveal',headers=h,params={'paper_id':p})
    assert filtered('unseen')=={ids[3]},'Reading an answer is not an attempt'


def test_mixed_saved_sets_preserve_order_and_next_set_seed(client,actor,database):
    _,h=learner(database,actor);p,ids=seed(database,30)
    first,body=start(client,h,p,order='mixed',seed='saved-mix')
    replay=client.post('/api/study-sessions',headers=h,json=body).json()
    restored=client.get('/api/study-sessions/'+first['id'],headers=h).json()
    assert first['question_ids']==replay['question_ids']==restored['question_ids']
    assert first['filters']['seed']=='saved-mix'
    second,_=start(client,h,p,order='mixed',seed='saved-mix',offset=10)
    assert not set(first['question_ids'])&set(second['question_ids'])
    different,_=start(client,h,p,order='mixed',seed='fresh-mix')
    assert different['question_ids']!=first['question_ids']


def test_booklet_history_survives_changed_representative(client,actor,database):
    from psycopg.types.json import Jsonb
    user,h=learner(database,actor);conn=database[1];tag=uuid4().hex
    text='Synthetic unique booklet '+tag
    qs=[]
    for letter in ['A','B']:
        p,ids=seed(database,1);qid=ids[0];qs.append(qid)
        source='Old_Questions/Test-'+tag+' Series '+letter+'.pdf'
        conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,paper_number) VALUES(%s,'Direct','Test',2025,'I')",(source,))
        conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path) SELECT 'udc',live_version,%s,'papers' FROM collections WHERE id='udc'",(source,))
        conn.execute('UPDATE appearances SET paper_id=%s,question=%s WHERE canonical_id=%s',(source,text,qid))
        conn.execute('UPDATE canonical_questions SET question=%s WHERE id=%s',(text,qid))
    for qid,correct in zip(qs,[False,True]):
        conn.execute("INSERT INTO attempts(user_id,canonical_id,collection_id,context,correct,chosen_text) VALUES(%s,%s,'udc','practice',%s,'A')",(user,qid,correct))
    params={'collection_id':'udc','q':tag,'order':'mixed','seed':'grouped','study_status':'ever_wrong'}
    r=client.get('/api/questions',headers=h,params=params)
    assert r.status_code==200,r.text
    assert r.json()['total']==1 and r.json()['items'][0]['id']==qs[1]
    assert client.get('/api/questions',headers=h,params={**params,'study_status':'wrong'}).json()['total']==0


def test_account_checkpoint_keeps_mixed_sequence(client,actor,database):
    user,h=learner(database,actor)
    body={'order':'mixed','seed':'resume-sequence','status':'ever_wrong','offset':23}
    r=client.post('/api/me/exam-checkpoint/udc',headers=h,json=body)
    assert r.status_code==200,r.text
    state=client.get('/api/me/exam-journey/udc',headers=h).json()['checkpoint']['state']
    assert all(state[key]==value for key,value in body.items())
