"""Account rollups, composed plans and calendar reads; no production fixtures."""
from datetime import timedelta
from uuid import uuid4
from app.services import activity_progress,mastery
from test_learning_loop import questions,attempt,run,due
from test_learning_workflows import learner


def test_progress_rollup_matches_history_scopes_replay_and_repair(client,actor,database):
    conn=database[1];user,h=learner(database,actor);paper,ids=questions(database,3)
    for i in range(9):
        aid=attempt(conn,user,ids[i%3],correct=i%2==0,context='review' if i%2 else 'practice')
        # Legacy SQL scope edits are repaired by reconciliation, not learner input.
        conn.execute("UPDATE attempts SET collection_id='udc',section_path=%s WHERE id=%s",('papers' if i<6 else None,aid))
    before=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    run(client,activity_progress.reconcile,user)
    page=client.get('/api/me/progress?detail=true',headers=h)
    assert page.status_code==200,page.text
    p=page.json();assert (p['answered'],p['correct'],p['unique_questions'])==(9,5,3)
    assert run(client,activity_progress.read,user,True).answered==9
    assert p['subjects'][0]['answered']==9 and p['collections'][0]['scope_id']=='udc'
    scoped=client.get('/api/me/progress?detail=true&collection_id=udc&section_path=papers').json()
    assert (scoped['answered'],scoped['correct'],scoped['unique_questions'])==(6,3,3)
    assert scoped['sections'][0]['scope_id']=='papers'
    # Demonstrate that reads use rollups, not a hidden fallback scan.
    conn.execute('UPDATE user_activity_daily SET answered=answered+10 WHERE user_id=%s AND day=(SELECT min(day) FROM user_activity_daily WHERE user_id=%s)',(user,user))
    assert client.get('/api/me/progress').json()['answered']>9
    run(client,activity_progress.reconcile,user)
    assert client.get('/api/me/progress').json()['answered']==9
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==before
    # Real answers update counters transactionally, even outside the question router.
    attempt(conn,user,ids[0],False,context='game')
    assert client.get('/api/me/progress').json()['answered']==10
    client.cookies.clear();client.get('/api/auth/session')
    guest=conn.execute('SELECT id FROM users WHERE email IS NULL ORDER BY created_at DESC LIMIT 1').fetchone()[0]
    attempt(conn,guest,ids[0],False)
    assert client.get('/api/me/progress').json()['answered']==1
    assert conn.execute('SELECT count(*) FROM user_activity_daily WHERE user_id=%s',(guest,)).fetchone()[0]==0


def test_today_saved_exam_focus_honesty_primary_switch_and_no_write_on_read(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,8)
    conn.execute('UPDATE question_classifications SET topic_id=%s WHERE question_id=ANY(%s)',('today-'+uuid4().hex,ids))
    for q in ids[:5]:attempt(conn,user,q,False)
    run(client,mastery.refresh,user)
    due(conn,user,ids[5:6])
    response=client.get('/api/me/today',headers=h)
    assert response.status_code==200,response.text
    assert response.json()['exam'] is None and response.json()['new_questions'] is None
    assert client.put('/api/me/exam-bookmarks/udc/primary',headers=h).status_code==200
    before=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    daily_before=conn.execute('SELECT count(*) FROM game_dailies').fetchone()[0]
    today=client.get('/api/me/today').json()
    from app.services.today import compose
    assert run(client,compose,user)['exam']['id']=='udc'
    assert today['exam']['id']=='udc' and today['exam']['is_primary']
    assert today['new_questions']['target']==2 and today['new_questions']['subject_id']=='english'
    assert today['due_count']==1 and len(today['quests'])==3
    assert client.put('/api/me/exam-bookmarks/ldc/primary',headers=h).status_code==200
    switched=client.get('/api/me/today').json()
    assert switched['exam']['id']=='ldc' and switched['due_count']==today['due_count'] and switched['new_questions'] is None
    earned=client.get('/api/me/mastery').json()
    assert earned['exam']['id']=='ldc' and earned['items'][0]['in_primary_exam'] is False
    assert client.delete('/api/me/exam-bookmarks/ldc',headers=h).status_code==200
    assert client.get('/api/me/exam-bookmarks').json()['primary_collection_id']=='udc'
    assert client.patch('/api/me/focus-subjects',headers=h,json={'subject_ids':['mizo']}).status_code==200
    focused=client.get('/api/me/today').json()
    assert focused['due_count']==1 and focused['new_questions'] is None
    assert conn.execute('SELECT count(*) FROM game_dailies').fetchone()[0]==daily_before
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==before
    client.cookies.clear()
    guest=client.get('/api/me/today').json()
    assert guest['account'] is False and guest['exam'] is None and guest['quests']==[]


def test_calendar_forecast_early_review_and_guest_official_only(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,1)
    due(conn,user,ids)
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    future=day+timedelta(days=7)
    conn.execute('UPDATE review_items SET due_on=%s WHERE user_id=%s',(future,user))
    route='/api/me/calendar-layers?start='+day.isoformat()+'&end='+future.isoformat()
    response=client.get(route,headers=h)
    assert response.status_code==200,response.text
    assert response.json()['forecast']==[{'day':future.isoformat(),'count':1}]
    assert response.json()['habit']==[{'day':day.isoformat(),'count':1}]
    assert client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex}).status_code==422
    early=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'through':future.isoformat()})
    assert early.status_code==200,early.text
    s=early.json()
    answer=client.post('/api/study-sessions/'+s['id']+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1})
    assert answer.status_code==200,answer.text
    assert conn.execute('SELECT due_on FROM review_items WHERE user_id=%s',(user,)).fetchone()[0]==day+timedelta(days=3)
    client.cookies.clear()
    guest=client.get(route).json()
    assert guest['forecast']==[] and guest['habit']==[]
