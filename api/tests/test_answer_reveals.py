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
