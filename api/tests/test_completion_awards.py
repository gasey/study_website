"""Prospective awards from real server controllers; only disposable data."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_games_search import game_case,daily_case,create,play
from test_learning_loop import questions,attempt,run
from test_learning_habit import learner,due,review
from app.services import mastery,learning_rollups


def timed_game(client,conn,h,r,right=10,timed=True):
    while r['state']=='running':
        if timed:conn.execute("UPDATE game_rooms SET round_started_at=clock_timestamp()-interval '3.1 seconds' WHERE id=%s",(r['id'],))
        q=conn.execute('SELECT questions FROM game_rooms WHERE id=%s',(r['id'],)).fetchone()[0][r['position']]
        correct=q['options'].index(q['answer_text'])
        response=play(client,h,r,correct if r['position']<right else (correct+1)%len(q['options']))
        assert response.status_code==200,response.text
        r=response.json()
    return r


def test_game_completion_points_cap_xp_continue_and_replay(client,game_case):
    conn,subject,users,h,_=game_case
    for n in range(3):
        r=create(client,h[0],subject).json()
        done=timed_game(client,conn,h[0],r,right=6)
        assert done['state']=='finished'
        row=conn.execute("SELECT xp,points,rule_version FROM reward_ledger WHERE event_key=%s",('game:'+users[0]+':'+r['id'],)).fetchone()
        assert row==(15,2 if n<2 else 0,'learning-v2')
        # Saved answer retry and concurrent room reads cannot remint completion.
        with ThreadPoolExecutor(max_workers=3) as pool:
            responses=list(pool.map(lambda _:client.get('/api/games/rooms/'+r['id'],headers=h[0]),range(3)))
        assert all(x.status_code==200 for x in responses)
        choice=conn.execute('SELECT chosen_index FROM game_answers WHERE room_id=%s AND user_id=%s AND position=0',(r['id'],users[0])).fetchone()[0]
        assert play(client,h[0],{**done,'position':0},choice).status_code==200
    assert conn.execute('SELECT count(*) FROM game_completion_rewards WHERE user_id=%s',(users[0],)).fetchone()[0]==3


@pytest.mark.parametrize('right,timed',[(5,True),(10,False)])
def test_low_accuracy_or_rushed_game_has_no_completion(client,game_case,right,timed):
    conn,subject,users,h,_=game_case
    r=create(client,h[0],subject).json();timed_game(client,conn,h[0],r,right=right,timed=timed)
    assert conn.execute('SELECT count(*) FROM game_completion_rewards WHERE user_id=%s',(users[0],)).fetchone()[0]==0


def test_losing_duel_at_sixty_percent_still_earns_completion(client,game_case):
    conn,subject,users,h,_=game_case
    r=create(client,h[0],subject,mode='duel',matchmaking=True).json()
    assert create(client,h[1],subject,mode='duel',matchmaking=True).status_code==200
    client.post('/api/games/rooms/'+r['id']+'/ready',headers=h[0],json={'ready':True})
    r=client.post('/api/games/rooms/'+r['id']+'/ready',headers=h[1],json={'ready':True}).json()
    while r['state']=='running':
        conn.execute("UPDATE game_rooms SET round_started_at=clock_timestamp()-interval '3.1 seconds' WHERE id=%s",(r['id'],))
        q=conn.execute('SELECT questions FROM game_rooms WHERE id=%s',(r['id'],)).fetchone()[0][r['position']]
        correct=q['options'].index(q['answer_text']);position=r['position']
        assert play(client,h[0],r,correct if position<6 else (correct+1)%len(q['options'])).status_code==200
        r=play(client,h[1],r,correct).json()
    assert conn.execute('SELECT correct FROM game_members WHERE room_id=%s AND user_id=%s',(r['id'],users[0])).fetchone()[0]==6
    assert conn.execute('SELECT count(*) FROM game_completion_rewards WHERE room_id=%s',(r['id'],)).fetchone()[0]==2


def test_daily_completion_is_not_an_accuracy_award_and_cannot_replay(client,daily_case):
    conn,users,h=daily_case
    r=create(client,h[0],None,mode='daily').json();timed_game(client,conn,h[0],r,right=0)
    assert conn.execute("SELECT xp,points FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'daily:%%'",(users[0],)).fetchone()==(10,1)
    assert create(client,h[0],None,mode='daily').status_code==409
    assert conn.execute('SELECT count(*) FROM game_completion_rewards WHERE user_id=%s',(users[0],)).fetchone()[0]==1


def mock_fixture(client,actor,database,user,ids,*,timed=True,source='official',skip=False,late=False,legacy=False,held=False):
    conn=database[1];cid='completion-'+uuid4().hex;mid='mock-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind) VALUES(%s,'Synthetic completion test','exam')",(cid,))
    conn.execute('''INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,answer_mode,duration_seconds,marks_correct,marks_wrong,started_at)
      VALUES(%s,%s,%s,%s,'official',600,1,0,clock_timestamp()-make_interval(secs=>%s))''',(mid,user,cid,ids,700 if late else 3*len(ids)+1 if timed else 0))
    for q in ids:
        conn.execute("INSERT INTO mock_session_questions(mock_id,canonical_id,position,options,snapshot) VALUES(%s,%s,%s,'[\"A\",\"B\",\"C\",\"D\"]',%s)",(mid,q,ids.index(q),None if legacy else Jsonb({'question':conn.execute('SELECT question FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0],'options':['A','B','C','D'],'answer_text':'B','answer_source':source})))
    if held:conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(ids[0],))
    return mid,{'answers':[{'question_id':q,'chosen_index':0} for q in (ids[:1] if skip else ids)]}


def test_full_mock_completion_cap_and_real_role(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,3)
    for n in range(2):
        mid,body=mock_fixture(client,actor,database,user,ids)
        response=client.post('/api/mocks/'+mid+'/submit',headers=h,json=body)
        assert response.status_code==200,response.text
        assert conn.execute('SELECT xp,points FROM reward_ledger WHERE event_key=%s',('mock:'+user+':'+mid,)).fetchone()==(30,3 if n==0 else 0)
        assert client.post('/api/mocks/'+mid+'/submit',headers=h,json=body).status_code==409
    # Trigger execution also works under the actual application role.
    mid,body=mock_fixture(client,actor,database,user,ids)
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        for i,q in enumerate(ids):conn.execute("INSERT INTO attempts(user_id,canonical_id,context,mock_id,position,chosen_text,correct) VALUES(%s,%s,'mock',%s,%s,'A',false)",(user,q,mid,i))
        conn.execute('UPDATE mock_sessions SET submitted_at=clock_timestamp(),late=false,elapsed_seconds=10,n_correct=0,n_wrong=3,n_skipped=0,score=0 WHERE id=%s',(mid,))
    assert conn.execute('SELECT count(*) FROM mock_completion_rewards WHERE user_id=%s',(user,)).fetchone()[0]==3


@pytest.mark.parametrize('kw',[{'timed':False},{'skip':True},{'late':True},{'legacy':True},{'source':'inferred'},{'held':True}])
def test_mock_completion_excludes_incomplete_rushed_late_or_unverified(client,actor,database,kw):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,3)
    mid,body=mock_fixture(client,actor,database,user,ids,**kw)
    response=client.post('/api/mocks/'+mid+'/submit',headers=h,json=body)
    assert response.status_code==200,response.text
    assert conn.execute('SELECT count(*) FROM mock_completion_rewards WHERE mock_id=%s',(mid,)).fetchone()[0]==0


def test_proficient_live_crossing_once_ever_and_worker_never_awards(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,11)
    for q in ids[:9]:attempt(conn,user,q)
    run(client,mastery.refresh,user)
    r=client.post('/api/questions/'+ids[9]+'/answer',headers=h,json={'chosen_index':1})
    assert r.status_code==200,r.text
    receipt=conn.execute("SELECT l.xp,l.points,m.origin FROM mastery_milestones m JOIN reward_ledger l ON l.id=m.ledger_id WHERE m.user_id=%s",(user,)).fetchone()
    assert receipt==(30,3,'activity')
    # Demote, remove the rollup altogether, re-promote: the lifetime latch survives.
    for q in ids[:6]:attempt(conn,user,q,False)
    run(client,mastery.refresh,user)
    conn.execute('DELETE FROM user_topic_mastery WHERE user_id=%s',(user,))
    for q in ids[:6]:
        r=client.post('/api/questions/'+q+'/answer',headers=h,json={'chosen_index':1})
        assert r.status_code==200,r.text
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'mastery:%%'",(user,)).fetchone()[0]==1
    other,oh=learner(database,actor)
    for q in ids:attempt(conn,other,q)
    run(client,learning_rollups.cycle)
    run(client,mastery.refresh,other)
    assert conn.execute('SELECT origin,ledger_id FROM mastery_milestones WHERE user_id=%s',(other,)).fetchone()==('baseline',None)
    assert client.post('/api/questions/'+ids[0]+'/answer',headers=oh,json={'chosen_index':1}).status_code==200
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'mastery:%%'",(other,)).fetchone()[0]==0


def test_mastered_delayed_timed_review_and_global_points_cap(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,20)
    due(conn,user,ids[:8])
    for q in ids:attempt(conn,user,q)
    run(client,mastery.refresh,user)
    conn.execute("UPDATE user_topic_mastery SET proficient_at=now()-interval '15 days' WHERE user_id=%s",(user,))
    # A completed, timed review supplies the delayed review requirement while
    # existing proficiency remains valid throughout the session.
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',0,25,'Synthetic full points budget')",(user,uuid4().hex))
    done=review(client,h,conn,ids[:8],correct=8)
    assert done['finished_at']
    row=conn.execute("SELECT l.xp,l.points,m.review_session_id FROM mastery_milestones m JOIN reward_ledger l ON l.id=m.ledger_id WHERE m.user_id=%s AND m.tier='mastered'",(user,)).fetchone()
    assert row==(60,0,done['id'])
    assert client.post('/api/study-sessions/'+done['id']+'/finish',headers=h,json={'version':1}).status_code==200
    assert conn.execute("SELECT count(*) FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'mastery:%%'",(user,)).fetchone()[0]==1


def test_game_finalization_and_milestone_award_with_actual_app_role(client,actor,database,game_case):
    from app.services import games
    conn,subject,users,h,_=game_case
    r=create(client,h[0],subject).json()
    frozen=conn.execute('SELECT questions FROM game_rooms WHERE id=%s',(r['id'],)).fetchone()[0]
    # Synthetic server-owned choices; actual finish() performs identity checks,
    # grading, discovery, member updates and the completion trigger as mpsc.
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        for i,q in enumerate(frozen):
            conn.execute('INSERT INTO game_answers(room_id,user_id,position,chosen_index,correct,elapsed_ms) VALUES(%s,%s,%s,%s,true,3100)',(r['id'],users[0],i,q['options'].index(q['answer_text'])))
    async def finish_as_role(cur,rid):
        room=await games.room(cur,rid)
        await games.finish(cur,room,await games.clock(cur))
    run(client,finish_as_role,r['id'])
    assert conn.execute('SELECT l.xp,l.points FROM game_completion_rewards c JOIN reward_ledger l ON l.id=c.ledger_id WHERE c.room_id=%s',(r['id'],)).fetchone()==(15,2)
    user,_=learner(database,actor);_,ids=questions(database,10)
    for q in ids[:9]:attempt(conn,user,q)
    run(client,mastery.prepare,user,ids[-1])
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc');aid=attempt(conn,user,ids[-1])
    run(client,learning_rollups.record,user,aid)
    assert conn.execute("SELECT l.xp,l.points FROM mastery_milestones m JOIN reward_ledger l ON l.id=m.ledger_id WHERE m.user_id=%s",(user,)).fetchone()==(30,3)
