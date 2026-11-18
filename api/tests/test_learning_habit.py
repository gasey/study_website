"""Prospective habit gates with real PostgreSQL, role, receipt and route execution."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_learning_workflows import learner
from test_learning_loop import questions,attempt,due,run
from app.services.learning_habit import capture_plan,plan_status


def review(client,h,conn,ids,correct=8,timed=True,finish=True,through=None):
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':len(ids),'through':through})
    assert r.status_code==200,r.text
    s=r.json();url='/api/study-sessions/'+s['id']
    for i,q in enumerate(s['question_ids']):
        if i:s=client.post(url+'/position',headers=h,json={'version':s['version'],'position':i}).json()
        if timed:conn.execute("UPDATE review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND canonical_id=%s",(s['id'],q))
        r=client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':q,'chosen_index':1 if i<correct else 0})
        assert r.status_code==200,r.text
        s=r.json()
    if not finish:return s
    r=client.post(url+'/finish',headers=h,json={'version':s['version']});assert r.status_code==200,r.text
    return r.json()


def test_review_award_replay_two_slots_and_shared_xp_cap(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,24)
    for n in range(3):
        batch=ids[n*8:(n+1)*8];due(conn,user,batch)
        # Leave only7 XP at the shared ceiling before the second review.
        if n==1:conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',273,0,'Synthetic remaining budget')",(user,uuid4().hex))
        done=review(client,h,conn,batch,correct=5)
        reward=done['summary']['reward']
        assert reward['status']==('daily_cap' if n==2 else 'awarded'),reward
        assert (reward['xp'],reward['points'])==((0,0) if n==2 else (7,2) if n==1 else (20,2))
        url='/api/study-sessions/'+done['id']+'/finish'
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(lambda _:client.post(url,headers=h,json={'version':1}),range(2)))
        assert all(r.status_code==200 and r.json()['summary']['reward']==reward for r in responses)
    rows=conn.execute("SELECT event_key,xp,points FROM reward_ledger WHERE user_id=%s AND event_key LIKE 'review:%%' ORDER BY id",(user,)).fetchall()
    assert len(rows)==2 and sum(r[2] for r in rows)==4
    assert conn.execute("SELECT sum(xp) FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game')",(user,)).fetchone()[0]==300
    assert conn.execute('SELECT count(*) FROM review_item_completions WHERE user_id=%s',(user,)).fetchone()[0]==24
    # Discovery can use a fractional remainder without exceeding300XP.
    other,oh=learner(database,actor);_,new=questions(database,1)
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',299,0,'Synthetic partial budget')",(other,uuid4().hex))
    response=client.post('/api/questions/'+new[0]+'/answer',headers=oh,json={'chosen_index':1})
    assert response.status_code==200,response.text
    assert conn.execute('SELECT sum(xp) FROM reward_ledger WHERE user_id=%s',(other,)).fetchone()[0]==300


def test_review_fast_low_accuracy_early_duplicate_and_skips_do_not_pay(client,actor,database):
    conn=database[1]
    for correct,timed in [(8,False),(4,True)]:
        user,h=learner(database,actor);_,ids=questions(database,8);due(conn,user,ids)
        done=review(client,h,conn,ids,correct=correct,timed=timed)
        assert done['summary']['reward']['status']=='not_eligible'
        assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0
    user,h=learner(database,actor);_,ids=questions(database,8);due(conn,user,ids)
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    conn.execute('UPDATE review_items SET due_on=%s WHERE user_id=%s',(day+timedelta(days=3),user))
    early=review(client,h,conn,ids,through=(day+timedelta(days=3)).isoformat())
    assert early['summary']['reward']['status']=='not_eligible'
    assert conn.execute('SELECT count(*) FROM review_item_completions WHERE user_id=%s',(user,)).fetchone()[0]==0
    # Two pre-composed sets cannot pay twice for the same scheduled occurrence.
    user,h=learner(database,actor);_,ids=questions(database,8);due(conn,user,ids)
    pending=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8}).json()
    done=review(client,h,conn,ids)
    assert done['summary']['reward']['status']=='awarded'
    skipped=client.post('/api/study-sessions/'+pending['id']+'/finish',headers=h,json={'version':pending['version']})
    assert skipped.status_code==200 and skipped.json()['summary']['reward']['status']=='not_eligible'
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1


def test_account_streak_qualification_shields_staleness_and_guest(client,actor,database):
    conn=database[1];_,ids=questions(database,8)
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    for i,(source,context,expected) in enumerate([('official','practice',1),('key','review',1),('official','game',1),('inferred','practice',0),('derived','practice',0),('official','mock',0)]):
        user,h=learner(database,actor);attempt(conn,user,ids[i],False,source=source,context=context)
        p=client.get('/api/me/progress',headers=h).json();w=client.get('/api/rewards/me').json()
        assert p['current_streak']==w['current_streak_days']==expected,(source,context,p,w)
        assert p['streak_basis']=='account learning'
    user,h=learner(database,actor)
    conn.execute('INSERT INTO reward_profiles(user_id,current_streak_days,longest_streak_days,last_active_ist_date,streak_shields) VALUES(%s,4,4,%s,1)',(user,day-timedelta(days=2)))
    attempt(conn,user,ids[0],False)
    assert client.get('/api/me/progress?collection_id=udc').json()['current_streak']==5
    assert client.get('/api/rewards/me').json()['streak_shields']==0
    attempt(conn,user,ids[1],False)
    assert client.get('/api/me/progress?detail=true').json()['current_streak']==5
    conn.execute('UPDATE reward_profiles SET last_active_ist_date=%s WHERE user_id=%s',(day-timedelta(days=3),user))
    assert client.get('/api/rewards/me').json()['current_streak_days']==client.get('/api/me/progress').json()['current_streak']==0
    # No historical backfill, future timestamps or views can qualify today.
    other,oh=learner(database,actor)
    for at in [(day-timedelta(days=2)).isoformat()+' 12:00:00+05:30',(day+timedelta(days=1)).isoformat()+' 12:00:00+05:30']:
        attempt(conn,other,ids[0],False,at=at)
    assert client.get('/api/me/progress',headers=oh).json()['current_streak']==0
    assert client.post('/api/questions/'+ids[2]+'/reveal',headers=oh).status_code==200
    assert client.get('/api/me/progress').json()['current_streak']==0
    client.cookies.clear();client.get('/api/auth/session')
    guest=conn.execute('SELECT id FROM users WHERE email IS NULL ORDER BY created_at DESC LIMIT 1').fetchone()[0]
    attempt(conn,guest,ids[0],False)
    assert client.get('/api/me/progress?detail=true').json()['streak_basis']=='device activity'
    assert conn.execute('SELECT count(*) FROM reward_profiles WHERE user_id=%s',(guest,)).fetchone()[0]==0


def test_quests_frozen_plan_read_purity_cutover_and_replay(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,10);due(conn,user,ids[:8])
    before=conn.execute('SELECT count(*) FROM daily_learning_plans').fetchone()[0]
    today=client.get('/api/me/today',headers=h).json()
    assert not today['plan_status']['started']
    assert conn.execute('SELECT count(*) FROM daily_learning_plans').fetchone()[0]==before
    done=review(client,h,conn,ids[:8]);assert done['summary']['reward']['status']=='awarded'
    state=run(client,plan_status,user)
    assert state['started'] and not state['completed']
    frozen=conn.execute('SELECT snapshot FROM daily_learning_plans WHERE user_id=%s',(user,)).fetchone()[0]
    assert client.patch('/api/me/focus-subjects',headers=h,json={'subject_ids':['mizo']}).status_code==200
    assert client.put('/api/me/exam-bookmarks/ldc/primary',headers=h).status_code==200
    assert conn.execute('SELECT snapshot FROM daily_learning_plans WHERE user_id=%s',(user,)).fetchone()[0]==frozen
    wallet=client.get('/api/rewards/me').json();quests={q['key']:q for q in wallet['daily_quests']['quests']}
    assert quests['review_ring']['completed'] and not quests['plan_ring']['completed']
    for key in ['review_ring','cross_stream_triad']:
        r=client.post('/api/rewards/daily-quests/'+key+'/claim',headers=h)
        assert r.status_code==200,r.text
        if key=='review_ring':receipt=r.json()
        else:assert r.json()['ledger_id']==receipt['ledger_id']
    assert client.post('/api/rewards/daily-quests/plan_ring/claim',headers=h).status_code==409
    # A cutover-day old receipt settles its new ring; old data is unchanged.
    other,oh=learner(database,actor)
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'game',30,3,'Synthetic legacy receipt') RETURNING id",(other,uuid4().hex))
    ledger=conn.execute('SELECT max(id) FROM reward_ledger WHERE user_id=%s',(other,)).fetchone()[0]
    conn.execute("INSERT INTO daily_quest_claims(user_id,ist_date,quest_key,xp_awarded,points_awarded,ledger_id) VALUES(%s,(now() AT TIME ZONE 'Asia/Kolkata')::date,'cross_stream_triad',30,3,%s)",(other,ledger))
    r=client.post('/api/rewards/daily-quests/review_ring/claim',headers=oh)
    assert r.status_code==200 and r.json()['ledger_id']==ledger
    assert client.get('/api/rewards/me').json()['current_streak_days']==0
    assert conn.execute('SELECT count(*) FROM daily_quest_claims WHERE user_id=%s',(other,)).fetchone()[0]==1


def test_review_duplicate_schedule_occurrence_cannot_pay_again(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,8);due(conn,user,ids)
    frozen=conn.execute('SELECT item_id,due_on FROM review_items WHERE user_id=%s',(user,)).fetchall()
    second=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'size':8}).json()
    first=review(client,h,conn,ids)
    assert first['summary']['reward']['status']=='awarded'
    # Existing freshness policy requires a real later retry. A trusted fixture
    # moves history earlier; the client still uses the frozen second session.
    conn.execute("UPDATE attempts SET at=at-interval '1 day' WHERE user_id=%s",(user,))
    s=second;url='/api/study-sessions/'+s['id']
    for i,q in enumerate(s['question_ids']):
        if i:s=client.post(url+'/position',headers=h,json={'version':s['version'],'position':i}).json()
        conn.execute("UPDATE review_session_items SET opened_at=clock_timestamp()-interval '4 seconds' WHERE session_id=%s AND canonical_id=%s",(s['id'],q))
        r=client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':q,'chosen_index':1})
        assert r.status_code==200,r.text
        s=r.json()
    result=client.post(url+'/finish',headers=h,json={'version':s['version']})
    assert result.status_code==200,result.text
    assert result.json()['summary']['reward']['status']=='not_eligible'
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM review_item_completions WHERE user_id=%s',(user,)).fetchone()[0]==8


def test_plan_completion_claim_caps_and_new_target_does_not_chase_history(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,9)
    conn.execute('UPDATE question_classifications SET topic_id=%s WHERE question_id=ANY(%s)',('habit-'+uuid4().hex,ids))
    for q in ids[:5]:attempt(conn,user,q,False)
    from app.services.mastery import refresh
    run(client,refresh,user)
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=h).status_code==200
    run(client,capture_plan,user)
    state=run(client,plan_status,user)
    assert state['new_target']['target']==4 and state['new_target']['progress']==0
    for q in ids[5:]:
        response=client.post('/api/questions/'+q+'/answer',headers=h,json={'chosen_index':0})
        assert response.status_code==200,response.text
    state=run(client,plan_status,user)
    assert state['new_target']['progress']==4 and state['new_target']['completed']
    # Daily Five is a real server-owned room and result, without awarding via
    # test SQL. Its controller's shared-set/scoring behavior has separate tests.
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    did=day.isoformat();room='daily-plan-'+uuid4().hex
    conn.execute("INSERT INTO game_dailies(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour','[]') ON CONFLICT DO NOTHING",(did,))
    conn.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,request_key,request_hash,daily_id,state,finished_at) VALUES(%s,%s,'daily',1,'[]',20,%s,'synthetic',%s,'finished',now())",(room,user,uuid4().hex,did))
    conn.execute('INSERT INTO game_members(room_id,user_id,correct,wrong,released_at) VALUES(%s,%s,0,1,now())',(room,user))
    conn.execute('INSERT INTO game_daily_entries(daily_id,user_id,room_id) VALUES(%s,%s,%s)',(did,user,room))
    state=run(client,plan_status,user)
    assert state['completed'] and state['progress']==state['target']==2
    response=client.get('/api/me/today',headers=h)
    assert response.json()['new_questions']['target']==4 and response.json()['new_questions']['completed']
    # Partial or exhausted XP budget never prevents point receipt replay safety.
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'study',295,0,'Synthetic daily budget')",(user,uuid4().hex))
    first=client.post('/api/rewards/daily-quests/plan_ring/claim',headers=h)
    assert first.status_code==200,first.text
    assert (first.json()['xp_awarded'],first.json()['points_awarded'])==(5,5)
    old=client.post('/api/rewards/daily-quests/mastery_closure/claim',headers=h)
    assert old.status_code==200 and old.json()['ledger_id']==first.json()['ledger_id']
    warm=client.post('/api/rewards/daily-quests/warmup_circuit/claim',headers=h)
    assert warm.status_code==200 and warm.json()['xp_awarded']==0 and warm.json()['points_awarded']==2
    assert conn.execute("SELECT sum(xp) FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game')",(user,)).fetchone()[0]==300


def test_submitted_mock_streak_eligible_wrong_late_and_missing_proof(client,actor,database):
    conn=database[1];_,ids=questions(database,3)
    for i,(late,source,expected) in enumerate([(False,'official',1),(True,'official',0),(False,'inferred',0)]):
        user,h=learner(database,actor);mid='habit-mock-'+uuid4().hex
        conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,600)",(mid,user,[ids[i]]))
        conn.execute('INSERT INTO mock_session_questions(mock_id,canonical_id,position,options,snapshot) VALUES(%s,%s,0,%s,%s)',(mid,ids[i],Jsonb(['A','B','C','D']),Jsonb({'answer_source':source})))
        conn.execute("INSERT INTO attempts(user_id,canonical_id,mock_id,chosen_text,correct,context) VALUES(%s,%s,%s,'A',false,'mock')",(user,ids[i],mid))
        assert client.get('/api/me/progress',headers=h).json()['current_streak']==0
        conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=1,n_correct=0,n_wrong=1,n_skipped=0,score=0,late=%s WHERE id=%s',(late,mid))
        assert client.get('/api/me/progress').json()['current_streak']==client.get('/api/rewards/me').json()['current_streak_days']==expected
    user,h=learner(database,actor)
    conn.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context,scoring_snapshot) VALUES(%s,%s,'A',false,'practice','{}')",(user,ids[0]))
    assert client.get('/api/me/progress',headers=h).json()['current_streak']==0


def test_finished_review_award_executes_as_real_application_role(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,8);due(conn,user,ids)
    s=review(client,h,conn,ids,finish=False)
    # Freeze the same server-owned finish data, then execute the award service
    # under the production role. No HTTP/test role can supply scoring inputs.
    conn.execute('UPDATE practice_study_sessions SET finished_at=clock_timestamp() WHERE id=%s',(s['id'],))
    from app.services.learning_habit import review_finish
    result=run(client,review_finish,{'id':s['id'],'user_id':user})
    assert result['status']=='awarded' and (result['xp'],result['points'])==(20,2)
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1
