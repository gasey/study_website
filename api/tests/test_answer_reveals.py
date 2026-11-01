"""Real PostgreSQL coverage for viewing versus submitting, using synthetic learners."""
from uuid import uuid4
import pytest
from test_learning_workflows import official, learner


def setup(database, actor):
    q, a, p = official(database)
    user, headers = learner(database, actor)
    return q, p, user, headers, database[1]


def counts(conn, user):
    return tuple(conn.execute('SELECT count(*) FROM '+table+' WHERE user_id=%s', (user,)).fetchone()[0]
                 for table in ('attempts', 'reward_ledger'))


def test_view_is_not_attempt_and_cooldown_survives_requests(client, actor, database):
    q, p, user, h, conn = setup(database, actor)
    url = '/api/questions/'+q
    before = counts(conn, user)
    r = client.post(url+'/reveal', params={'paper_id': p}, headers=h)
    assert r.status_code == 200, r.text
    assert r.headers['cache-control'] == 'private, no-store'
    data = r.json()
    assert data['viewed'] and data['answer_text'] == 'B' and data['answer_index'] == 1
    assert 'correct' not in data and 'reward' not in data
    assert counts(conn, user) == before
    for context in ('practice', 'review', 'material', 'mock', 'duel', 'cup'):
        r = client.post(url+'/answer', json={'chosen_index': 1, 'context': context}, headers=h)
        assert r.status_code == 409 and '30 minutes' in r.text, r.text
    assert counts(conn, user) == before
    conn.execute("UPDATE answer_reveals SET revealed_at=now()-interval '31 minutes' WHERE user_id=%s AND canonical_id=%s", (user, q))
    r = client.post(url+'/answer', json={'chosen_index': 1, 'paper_id': p}, headers=h)
    assert r.status_code == 200 and r.json()['correct'], r.text
    assert counts(conn, user)[0] == before[0]+1


def test_comparison_also_blocks_immediate_credit(client, actor, database):
    q, p, user, h, conn = setup(database, actor)
    url = '/api/questions/'+q
    assert client.get(url+'/answer-comparison', params={'paper_id':p}).status_code == 200
    assert client.post(url+'/answer', json={'chosen_index':1}, headers=h).status_code == 409
    assert counts(conn,user) == (0,0)


def test_view_cannot_bypass_source_scope_or_mock(client, actor, database):
    q, p, user, h, conn = setup(database, actor)
    url = '/api/questions/'+q+'/reveal'
    assert client.post(url,params={'paper_id':'wrong'},headers=h).status_code == 404
    assert not conn.execute('SELECT 1 FROM answer_reveals WHERE user_id=%s',(user,)).fetchone()
    mid = uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'ldc',%s,60)",(mid,user,[q]))
    assert client.post(url,headers=h).status_code == 409
    assert not conn.execute('SELECT 1 FROM answer_reveals WHERE user_id=%s',(user,)).fetchone()
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    assert client.post(url,headers=h).status_code == 200


@pytest.mark.parametrize('defect', ['duplicate-options','unresolved-source'])
def test_unusable_answers_are_not_revealed(client,actor,database,defect):
    q,p,user,h,conn = setup(database,actor)
    conn.execute('UPDATE canonical_questions SET source_defect=%s WHERE id=%s',(defect,q))
    assert client.post('/api/questions/'+q+'/reveal',headers=h).status_code == 409
    assert counts(conn,user) == (0,0)


def test_checked_answer_replay_preserved_after_view(client,actor,database):
    q,p,user,h,conn=setup(database,actor)
    h={**h,'Idempotency-Key':uuid4().hex}
    url='/api/questions/'+q
    first=client.post(url+'/answer',json={'chosen_index':0},headers=h)
    assert first.status_code == 200,first.text
    assert client.post(url+'/reveal',headers=h).status_code == 200
    replay=client.post(url+'/answer',json={'chosen_index':0},headers=h)
    assert replay.status_code == 200 and replay.json()==first.json()
    assert counts(conn,user)[0]==1

@pytest.mark.parametrize('cup', [False, True])
def test_active_game_and_unclosed_cup_block_view(client,actor,database,cup):
    from psycopg.types.json import Jsonb
    q,p,user,h,conn=setup(database,actor)
    room=uuid4().hex; cup_id=uuid4().hex if cup else None
    questions=Jsonb([{'id':q}])
    if cup:
        conn.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 day',now()+interval '1 day',%s)",(cup_id,questions))
    conn.execute("""INSERT INTO game_rooms(id,owner_id,mode,state,capacity,cup_id,questions,round_seconds,request_key,request_hash)
      VALUES(%s,%s,%s,%s,1,%s,%s,30,%s,'test')""",(room,user,'cup' if cup else 'speed','finished' if cup else 'running',cup_id,questions,room))
    conn.execute('INSERT INTO game_members(room_id,user_id,released_at) VALUES(%s,%s,'+('now()' if cup else 'NULL')+')',(room,user))
    url='/api/questions/'+q
    assert client.post(url+'/reveal',headers=h).status_code==409
    assert client.get(url+'/answer-comparison').status_code==409
    assert not conn.execute('SELECT 1 FROM answer_reveals WHERE user_id=%s',(user,)).fetchone()
    assert counts(conn,user)==(0,0)


def test_restore_is_private_and_does_not_renew_or_submit(client,actor,database):
    q,p,user,h,conn=setup(database,actor)
    first=client.post('/api/questions/'+q+'/reveal',headers=h).json()
    stamp=conn.execute('SELECT revealed_at FROM answer_reveals WHERE user_id=%s AND canonical_id=%s',(user,q)).fetchone()[0]
    payload={'items':[{'question_id':q,'paper_id':p},{'question_id':q,'paper_id':'wrong-paper'},{'question_id':'absent'}]}
    r=client.post('/api/questions/practice-state',json=payload,headers=h)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    states=r.json()['items'];state=states[0]
    assert state['viewed'] and state['answer']['answer_text']=='B' and state['retry_at']==first['retry_at']
    assert 0<state['retry_after_seconds']<=1800
    assert not states[1]['viewed'] and not states[2]['viewed']
    assert conn.execute('SELECT revealed_at FROM answer_reveals WHERE user_id=%s AND canonical_id=%s',(user,q)).fetchone()[0]==stamp
    assert counts(conn,user)==(0,0)
    _,other_h=learner(database,actor)
    assert not client.post('/api/questions/practice-state',json=payload,headers=other_h).json()['items'][0]['viewed']


def test_restore_rechecks_active_assessment_and_expires_honestly(client,actor,database):
    q,p,user,h,conn=setup(database,actor)
    assert client.post('/api/questions/'+q+'/reveal',headers=h).status_code==200
    mid=uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds)VALUES(%s,%s,'ldc',%s,60)",(mid,user,[q]))
    payload={'items':[{'question_id':q,'paper_id':p},{'question_id':'cq_test'}]}
    state=client.post('/api/questions/practice-state',headers=h,json=payload).json()['items']
    assert state[0]['restricted'] and state[0]['answer'] is None and not state[1]['restricted']
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))
    conn.execute("UPDATE answer_reveals SET revealed_at=now()-interval '31 minutes' WHERE user_id=%s AND canonical_id=%s",(user,q))
    state=client.post('/api/questions/practice-state',headers=h,json=payload).json()['items'][0]
    assert state['viewed'] and state['retry_after_seconds']==0
    assert client.post('/api/questions/'+q+'/answer',headers=h,json={'chosen_index':1}).status_code==200
    state=client.post('/api/questions/practice-state',headers=h,json=payload).json()['items'][0]
    assert not state['viewed'] and state['answer'] is None


def test_restore_batch_is_bounded(client,actor,database):
    _,_,_,h,_=setup(database,actor)
    for items in ([],[{'question_id':'cq_test'}]*101):
        assert client.post('/api/questions/practice-state',headers=h,json={'items':items}).status_code==422


def test_next_uses_printed_order_and_scope(client,actor,database):
    from psycopg.types.json import Jsonb
    q,p,user,h,conn=setup(database,actor)
    second,aid,p2=official(database)
    conn.execute("UPDATE appearances SET paper_id=%s,qnum='2',options=%s WHERE id=%s",(p,Jsonb(['D','C','B','A']),aid))
    r=client.get('/api/questions/'+q+'/next',params={'paper_id':p})
    assert r.status_code==200 and r.json()=={'question_id':second,'paper_id':p},r.text
    assert client.get('/api/questions/'+second+'/next',params={'paper_id':p}).json()['question_id'] is None
    assert client.get('/api/questions/'+q+'/next',params={'paper_id':p2}).status_code==404
    assert counts(conn,user)==(0,0)


def test_reveal_unlocks_discussion_without_attempt_and_keeps_test_gate(client,actor,database):
    q,p,user,h,conn=setup(database,actor)
    thread='/api/community/questions/'+q+'/discussion'
    assert not client.get(thread).json()['allowed']
    assert client.post('/api/questions/'+q+'/reveal',headers=h).status_code==200
    assert client.get(thread).json()['allowed']
    r=client.post(thread,headers={**h,'Idempotency-Key':uuid4().hex},json={'kind':'doubt','body':'Can someone explain the reasoning behind this option?'})
    assert r.status_code==201,r.text
    assert counts(conn,user)==(0,0)
    mid=uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds)VALUES(%s,%s,'ldc',%s,60)",(mid,user,[q]))
    assert client.get(thread).status_code==409
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))


def test_saved_revision_waits_until_reveal_window_expires(client,actor,database):
    from psycopg.types.json import Jsonb
    q,p,user,h,conn=setup(database,actor)
    conn.execute('INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)',(user,Jsonb({'saved':[q]})))
    assert client.get('/api/learning/revision',headers={**h,'X-Learning-User':user}).json()['available']==1
    assert client.post('/api/questions/'+q+'/reveal',headers=h).status_code==200
    assert client.get('/api/learning/revision',headers={**h,'X-Learning-User':user}).json()['available']==0
    conn.execute("UPDATE answer_reveals SET revealed_at=now()-interval '31 minutes' WHERE user_id=%s AND canonical_id=%s",(user,q))
    assert client.get('/api/learning/revision',headers={**h,'X-Learning-User':user}).json()['available']==1
