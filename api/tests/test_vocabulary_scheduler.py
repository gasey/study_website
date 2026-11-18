"""Shared dated vocabulary queue, real scoring receipts and existing session caps."""
from uuid import uuid4
from datetime import timedelta
from test_vocabulary import seed,who,pick
from test_vocabulary_decks import prepare
from test_learning_workflows import learner
from test_learning_habit import review
from app.services.vocabulary_scheduler import DAILY_NEW

def requested(client,h,qid):
    r=client.post('/api/vocabulary/card',headers=h,json={'question_id':qid});assert r.status_code==200,r.text
    return r.json()['card']
def due(conn,user,qid,box=1):
    conn.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date,box=%s WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(box,user,qid))
def aged(conn,user):
    conn.execute("UPDATE attempts SET at=now()-interval '2 days' WHERE user_id=%s",(user,))
    conn.execute("UPDATE vocabulary_state SET first_review_at=now()-interval '2 days',last_exposure_at=now()-interval '2 days' WHERE user_id=%s",(user,))

def test_vocabulary_shares_queue_today_forecast_graduation_and_stale_card_guards(client,actor,database):
    conn=database[1];prepare(conn);qid=seed(conn,1)[0];user,h=learner(database,actor);h={**h,'x-vocabulary-user':user}
    c=requested(client,h,qid);assert c['question_id']==qid
    assert conn.execute('SELECT count(*) FROM daily_learning_plans WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert pick(client,h,c).status_code==200
    r=conn.execute("SELECT box,due_on,last_result FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid)).fetchone()
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    assert r==(1,day+timedelta(days=1),True)
    summary=client.get('/api/me/review-queue').json();assert summary['scheduled_count']==1 and summary['items'][0]['item_type']=='vocab'
    assert client.get('/api/me/today').json()['vocabulary']['target']==DAILY_NEW==5
    # Legacy fields are informational: changing that old due clock alone cannot
    # issue an authoritative review or change Today/queue/calendar counts.
    conn.execute("UPDATE vocabulary_state SET due_at=now()-interval '1 day' WHERE user_id=%s AND question_id=%s",(user,qid))
    assert requested(client,h,qid) is None
    due(conn,user,qid);aged(conn,user)
    c=requested(client,h,qid)
    # A checked answer through the ordinary Bank player invalidates this older
    # recognition presentation before it can insert another grade.
    answer=client.post('/api/questions/'+qid+'/answer',headers=h,json={'chosen_index':1});assert answer.status_code==200,answer.text
    before=conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]
    assert pick(client,h,c).status_code==409
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==before
    due(conn,user,qid,5);aged(conn,user);c=requested(client,h,qid)
    result=pick(client,h,c);assert result.status_code==200,result.text
    assert result.json()['graduated'] and result.json()['next_due'] is None and result.json()['stage']==6
    assert client.get('/api/me/review-queue').json()['scheduled_count']==0
    assert requested(client,h,qid) is None
    # Replay restores the exact old receipt, regardless of subsequent queue state.
    restored=client.post('/api/vocabulary/card',headers=h,json={'resume_id':c['id']});assert restored.json()['result']==result.json()
    wrong=client.post('/api/questions/'+qid+'/answer',headers=h,json={'chosen_index':0});assert wrong.status_code==200,wrong.text
    assert conn.execute("SELECT box,last_result FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid)).fetchone()==(1,False)

def test_five_new_limit_does_not_hide_due_vocabulary_and_saved_sessions_use_existing_awards(client,actor,database):
    conn=database[1];prepare(conn);ids=seed(conn,8);user,h=learner(database,actor);h={**h,'x-vocabulary-user':user}
    for qid in ids[:5]:assert pick(client,h,requested(client,h,qid)).status_code==200
    assert requested(client,h,ids[5]) is None
    assert client.get('/api/me/today').json()['vocabulary']['remaining']==0
    aged(conn,user)
    for qid in ids[5:]:assert pick(client,h,requested(client,h,qid)).status_code==200
    aged(conn,user)
    for qid in ids:due(conn,user,qid)
    # Preserve an old question projection; one canonical item still appears once.
    conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result) VALUES(%s,'question',%s,%s,1,current_date,false)",(user,ids[0],ids[0]))
    queue=client.get('/api/me/review-queue').json();assert queue['due_count']==queue['vocabulary_due_count']==8
    today=client.get('/api/me/today').json();assert today['due_count']==today['vocabulary']['due']==8
    layers=client.get('/api/me/calendar-layers',params={'start':conn.execute('SELECT current_date').fetchone()[0].isoformat(),'end':(conn.execute('SELECT current_date').fetchone()[0]+timedelta(days=1)).isoformat()}).json()
    assert sum(x['count'] for x in layers['forecast'])==8
    # Canonical vocabulary uses the same frozen question engine and timed finish
    # receipt as ordinary Smart Review; no per-card curated award is introduced.
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'item_type':'vocab','size':8});assert r.status_code==200,r.text
    assert set(r.json()['question_ids'])==set(ids)
    done=review(client,h,conn,ids,correct=8)
    assert done['summary']['reward']['status']=='awarded'
    assert done['summary']['reward']['points']==2
    assert client.post('/api/study-sessions/'+done['id']+'/finish',headers=h,json={'version':1}).json()['summary']==done['summary']
    assert conn.execute('SELECT count(*) FROM review_session_rewards WHERE user_id=%s',(user,)).fetchone()[0]==1
    assert client.get('/api/me/review-queue').json()['due_count']==0

def test_recognition_quarantine_preserves_receipts_bank_queue_and_readers(client,actor,database,tmp_path,monkeypatch):
    from app.services import vocabulary_release
    conn=database[1];prepare(conn);qid=seed(conn,1)[0];user,h=learner(database,actor);h={**h,'x-vocabulary-user':user}
    c=requested(client,h,qid);result=pick(client,h,c);assert result.status_code==200,result.text
    path=tmp_path/'writes.json';path.write_text('{"version":1,"writes_enabled":false}')
    monkeypatch.setattr(vocabulary_release,'STATE_PATH',path)
    assert client.post('/api/vocabulary/card',headers=h,json={}).status_code==503
    restored=client.post('/api/vocabulary/card',headers=h,json={'resume_id':c['id']});assert restored.status_code==200 and restored.json()['result']==result.json()
    assert pick(client,h,c).json()==result.json()
    assert client.get('/api/vocabulary/overview').status_code==client.get('/api/me/review-queue').status_code==200
    assert client.post('/api/questions/'+qid+'/answer',headers=h,json={'chosen_index':0}).status_code==200
    assert conn.execute("SELECT box,last_result FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid)).fetchone()==(1,False)
    path.write_text('{"version":true,"writes_enabled":true}');assert not vocabulary_release.enabled()
    path.unlink();assert not vocabulary_release.enabled()

def test_stale_source_returns_graduated_word_to_shared_due_queue_without_old_key_promotion(client,actor,database):
    conn=database[1];prepare(conn);qid=seed(conn,1)[0];user,h=learner(database,actor);h={**h,'x-vocabulary-user':user}
    assert pick(client,h,requested(client,h,qid)).status_code==200
    conn.execute("UPDATE review_items SET box=5,due_on=NULL WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid))
    conn.execute("UPDATE vocabulary_state SET score_version=score_version+100 WHERE user_id=%s AND question_id=%s",(user,qid))
    queue=client.get('/api/me/review-queue').json();assert queue['due_count']==queue['vocabulary_due_count']==1
    assert queue['items'][0]['box']==1
    assert client.get('/api/me/today').json()['vocabulary']['due']==1
    response=client.post('/api/questions/'+qid+'/answer',headers=h,json={'chosen_index':1});assert response.status_code==200,response.text
    assert conn.execute("SELECT box,due_on IS NOT NULL FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid)).fetchone()==(1,True)
    # A current scored Bank answer clears the stale projection without another
    # recognition grade. Both engines now use the same next-day schedule.
    assert requested(client,h,qid) is None
    assert client.get('/api/me/review-queue').json()['due_count']==0
    assert client.get('/api/vocabulary/overview?exam_scope=all').json()['due']==0


def test_source_replacement_starts_at_box_one_even_after_old_delayed_exposure(client,actor,database):
    conn=database[1];prepare(conn);qid=seed(conn,1)[0];user,h=learner(database,actor);h={**h,'x-vocabulary-user':user}
    assert pick(client,h,requested(client,h,qid)).status_code==200
    aged(conn,user)
    conn.execute("UPDATE review_items SET box=5,due_on=NULL WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid))
    conn.execute("UPDATE vocabulary_state SET content_hash='old-content',score_version=score_version+100 WHERE user_id=%s AND question_id=%s",(user,qid))
    card=requested(client,h,qid);r=pick(client,h,card);assert r.status_code==200,r.text
    assert not r.json()['graduated'] and r.json()['stage']==1
    assert conn.execute("SELECT box FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid)).fetchone()==(1,)
