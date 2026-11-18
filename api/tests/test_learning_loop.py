"""Learning rollups and Smart Review against an isolated PostgreSQL database."""
from datetime import date,timedelta
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.db import cursor
from app.services import mastery,review_queue,learning_rollups
from app.services.scoring_revisions import assess_attempt
from test_learning_workflows import learner
from test_study_sessions import seed


def questions(database,n=20):
    paper,ids=seed(database,n)
    conn=database[1]
    for q in ids:
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','english/test','Synthetic topic','test','manual','approved')",(q,))
    return paper,ids


def attempt(conn,user,q,correct=True,at=None,source='official',context='practice'):
    snapshot={'question':conn.execute('SELECT question FROM canonical_questions WHERE id=%s',(q,)).fetchone()[0],
      'options':['A','B','C','D'],'answer_text':'B','answer_source':source,
      'context_basis':'primary_appearance','has_diagram':False}
    return conn.execute('''INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot,at)
      VALUES(%s,%s,%s,%s,%s,%s,COALESCE(%s::timestamptz,clock_timestamp())) RETURNING id''',
      (user,q,correct,'B' if correct else 'A',context,Jsonb(snapshot),at)).fetchone()[0]


def run(client,fn,*args):
    async def invoke():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            return await fn(cur,*args)
    return client.portal.call(invoke)


def row(conn,user):
    return conn.execute('SELECT state,distinct_attempted,distinct_correct_latest,proficient_at,mastered_at FROM user_topic_mastery WHERE user_id=%s',(user,)).fetchone()


def test_rollup_ground_truth_retries_provenance_and_reassessment(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,12)
    for i,q in enumerate(ids):attempt(conn,user,q,correct=i<8,source='inferred' if i==0 else 'official')
    attempt(conn,user,ids[-1],correct=True)  # latest, not all-attempt accuracy
    # Even a now-verified question cannot launder an originally inferred attempt.
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE question_id=%s",(ids[1],))
    ledger=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    run(client,mastery.refresh,user)
    r=row(conn,user);assert r[:3]==('proficient',10,7)
    payload=client.get('/api/me/mastery',headers=h)
    assert payload.status_code==200 and payload.headers['cache-control']=='private, no-store'
    assert payload.json()['items'][0]['accuracy']==70
    assert 'not an exam-readiness certification' in payload.json()['basis']
    # Latest adjusted assessment overrides original correctness; immutable originals survive.
    aid=conn.execute('SELECT id FROM attempts WHERE user_id=%s AND canonical_id=%s',(user,ids[2])).fetchone()[0]
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'test',%s)",(aid,uuid4().hex,Jsonb({'outcome':'wrong'})))
    run(client,mastery.refresh,user)
    assert row(conn,user)[:3]==('practicing',10,6)
    assert conn.execute('SELECT correct FROM attempts WHERE id=%s',(aid,)).fetchone()[0] is True
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(ids[3],))
    run(client,mastery.refresh,user)
    assert row(conn,user)[1]==9
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==ledger


def test_incremental_answer_and_correction_job(client,actor,database):
    conn=database[1];user,h=learner(database,actor);p,ids=questions(database,1)
    response=client.post('/api/questions/'+ids[0]+'/answer',headers=h,json={'chosen_index':0,'paper_id':p})
    assert response.status_code==200,response.text
    assert row(conn,user)[:3]==('exploring',1,0)
    assert conn.execute('SELECT box,last_result FROM review_items WHERE user_id=%s',(user,)).fetchone()==(1,False)
    aid=conn.execute('SELECT id FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]
    conn.execute("UPDATE canonical_questions SET answer_text='A' WHERE id=%s",(ids[0],))
    run(client,assess_attempt,aid)
    # Exercise the durable worker under the real application role.
    run(client,learning_rollups.cycle)
    assert row(conn,user)[:3]==('exploring',1,1)
    assert conn.execute('SELECT box,last_result FROM review_items WHERE user_id=%s',(user,)).fetchone()==(1,True)
    assert conn.execute("SELECT last_ok IS NOT NULL,note FROM worker_heartbeats WHERE worker='mastery-reconciler'").fetchone()==(True,'ok: Reconciliation cycle complete')


def test_leitner_intervals_graduation_replay_and_ist(client,actor,database):
    conn=database[1];user,_=learner(database,actor);_,ids=questions(database,1);q=ids[0]
    wrong=attempt(conn,user,q,False,'2026-11-17 18:31:00+00')
    run(client,review_queue.apply_attempt,wrong)
    def current():return conn.execute('SELECT box,due_on,last_attempt_id FROM review_items WHERE user_id=%s',(user,)).fetchone()
    assert current()==(1,date(2026,11,19),wrong)
    for box,days in [(2,3),(3,7),(4,16),(5,35),(5,None)]:
        aid=attempt(conn,user,q,True,'2026-11-17 18:31:01+00',context='review')
        run(client,review_queue.apply_attempt,aid)
        expected=(box,date(2026,11,18)+timedelta(days=days) if days else None,aid)
        assert current()==expected
        run(client,review_queue.apply_attempt,aid)
        assert current()==expected
    wrong=attempt(conn,user,q,False,'2026-11-17 18:29:00+00')
    run(client,review_queue.apply_attempt,wrong)
    assert current()==(1,date(2026,11,18),wrong)
    run(client,review_queue.apply_attempt,wrong-1)
    assert current()==(1,date(2026,11,18),wrong)
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==0


def due(conn,user,ids):
    for i,q in enumerate(ids):
        aid=attempt(conn,user,q,False)
        conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result,last_attempt_id) VALUES(%s,'question',%s,%s,1,CURRENT_DATE-%s,false,%s)",(user,q,q,30-i,aid))


def test_review_composition_cap_frozen_replay_focus_and_account_boundaries(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,25);due(conn,user,ids)
    conn.execute("UPDATE question_classifications SET subject_id='mizo',subject_label='Mizo' WHERE question_id=%s",(ids[-1],))
    initial=client.get('/api/me/review-queue',headers=h).json()
    assert initial['due_count']==25
    first=client.get('/api/me/review-queue?limit=5').json()
    second=client.get('/api/me/review-queue?limit=5&offset=5').json()
    assert first['has_more'] and second['due_count']==25
    assert not {i['item_id'] for i in first['items']} & {i['item_id'] for i in second['items']}
    response=client.patch('/api/me/focus-subjects',headers=h,json={'subject_ids':['mizo']})
    assert response.status_code==200,response.text
    assert client.get('/api/me/review-queue').json()['due_count']==25
    assert client.patch('/api/me/focus-subjects',headers=h,json={'subject_ids':['mizo']*2}).status_code==422
    assert client.patch('/api/me/focus-subjects',headers=h,json={'subject_ids':['unknown']}).status_code==422
    body={'request_key':uuid4().hex}
    response=client.post('/api/review-sessions',headers=h,json=body)
    assert response.status_code==200,response.text
    s=response.json();assert s['question_ids']==ids[:20] and s['kind']=='review'
    assert len(s['items'])==20 and 'answer_text' not in str(s['items'])
    conn.execute("UPDATE review_items SET due_on=CURRENT_DATE+1 WHERE user_id=%s",(user,))
    assert client.post('/api/review-sessions',headers=h,json=body).json()['question_ids']==ids[:20]
    assert client.post('/api/review-sessions',headers=h,json={**body,'focus_only':True}).status_code==409
    conn.execute("UPDATE review_items SET due_on=CURRENT_DATE WHERE user_id=%s",(user,))
    f=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex,'focus_only':True})
    assert f.status_code==200 and f.json()['question_ids']==[ids[-1]]
    other,oh=learner(database,actor)
    assert client.get('/api/study-sessions/'+s['id'],headers=oh).status_code==404
    assert client.get('/api/me/review-queue',headers=oh).json()['due_count']==0
    client.cookies.clear()
    assert client.post('/api/review-sessions',json=body).status_code==401
    assert client.get('/api/me/mastery').status_code==401


def test_mastered_requires_delayed_completed_scored_review_and_zero_awards(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,20)
    for q in ids:attempt(conn,user,q)
    ledger=conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]
    run(client,mastery.refresh,user)
    assert row(conn,user)[0]=='proficient'
    conn.execute("UPDATE user_topic_mastery SET proficient_at=now()-interval '15 days' WHERE user_id=%s",(user,))
    aid=attempt(conn,user,ids[0],False)
    run(client,review_queue.apply_attempt,aid)
    conn.execute("UPDATE review_items SET due_on=CURRENT_DATE WHERE user_id=%s",(user,))
    r=client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex})
    assert r.status_code==200,r.text
    s=r.json();url='/api/study-sessions/'+s['id']
    answered=client.post(url+'/answer',headers=h,json={'version':s['version'],'question_id':ids[0],'chosen_index':1,'presentation_hash':s['items'][0]['presentation_hash']})
    assert answered.status_code==200,answered.text
    s=answered.json();assert row(conn,user)[0]=='proficient'
    assert s['results'][ids[0]]['result']['correct']
    finished=client.post(url+'/finish',headers=h,json={'version':s['version']})
    assert finished.status_code==200,finished.text
    assert row(conn,user)[0]=='mastered' and row(conn,user)[4] is not None
    assert conn.execute("SELECT context FROM attempts WHERE id=(SELECT max(id) FROM attempts WHERE user_id=%s)",(user,)).fetchone()[0]=='review'
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==ledger
    conn.execute("UPDATE user_topic_mastery SET last_verified_activity_at=now()-interval '46 days' WHERE user_id=%s",(user,))
    item=client.get('/api/me/mastery').json()['items'][0]
    assert item['rusty'] is True and item['state']=='mastered'


def test_seed_latest_wrong_only_guest_and_inferred_exclusion(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,4)
    attempt(conn,user,ids[0],False);attempt(conn,user,ids[0],True)
    attempt(conn,user,ids[1],False)
    attempt(conn,user,ids[2],False)
    conn.execute("UPDATE canonical_questions SET answer_source='inferred' WHERE id=%s",(ids[2],))
    attempt(conn,user,ids[3],False)
    conn.execute("UPDATE canonical_questions SET key_disputed=true WHERE id=%s",(ids[3],))
    run(client,review_queue.seed,user)
    run(client,review_queue.seed,user)
    assert conn.execute('SELECT canonical_id,box FROM review_items WHERE user_id=%s',(user,)).fetchall()==[(ids[1],1)]
    client.cookies.clear();client.get('/api/auth/session')
    guest=conn.execute('SELECT id FROM users WHERE email IS NULL ORDER BY created_at DESC LIMIT 1').fetchone()[0]
    aid=attempt(conn,guest,ids[1],False)
    run(client,learning_rollups.record,guest,aid)
    assert conn.execute('SELECT count(*) FROM user_topic_mastery WHERE user_id=%s',(guest,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM review_items WHERE user_id=%s',(guest,)).fetchone()[0]==0


def test_mock_snapshot_and_latest_mock_assessment_and_game_correction(client,actor,database):
    from test_scoring_revisions import start_and_finish
    conn=database[1]
    q,_,mid,h,_=start_and_finish(client,actor,database)
    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,taxonomy_version,source,review_status) VALUES(%s,'english','English','mock/test','test','manual','approved')",(q,))
    # Mock attempts intentionally reference the immutable served snapshot instead
    # of duplicating it on attempts.scoring_snapshot.
    assert conn.execute('SELECT scoring_snapshot FROM attempts WHERE mock_id=%s',(mid,)).fetchone()[0] is None
    run(client,mastery.refresh,'owner')
    assert conn.execute("SELECT distinct_correct_latest FROM user_topic_mastery WHERE user_id='owner' AND topic='mock/test'").fetchone()[0]==1
    conn.execute("UPDATE canonical_questions SET answer_text='C' WHERE id=%s",(q,))
    response=client.post('/api/mocks/'+mid+'/reassess',headers=h)
    assert response.status_code==200,response.text
    run(client,mastery.refresh,'owner')
    assert conn.execute("SELECT distinct_correct_latest FROM user_topic_mastery WHERE user_id='owner' AND topic='mock/test'").fetchone()[0]==0
    user,_=learner(database,actor);_,ids=questions(database,1)
    aid=attempt(conn,user,ids[0],True,context='game')
    run(client,mastery.refresh,user)
    assert row(conn,user)[2]==1
    conn.execute("UPDATE canonical_questions SET answer_text='A' WHERE id=%s",(ids[0],))
    run(client,assess_attempt,aid)
    run(client,mastery.refresh,user)
    assert row(conn,user)[2]==0


def test_adopted_attempt_enqueues_account_and_queue_hides_assessed_questions(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,2)
    guest='guest-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)',(guest,guest))
    aid=attempt(conn,guest,ids[0],False)
    run(client,review_queue.seed,guest)
    assert conn.execute('SELECT count(*) FROM review_items WHERE user_id=%s',(guest,)).fetchone()[0]==0
    conn.execute('UPDATE attempts SET user_id=%s WHERE id=%s',(user,aid))
    assert conn.execute('SELECT processed_version<requested_version FROM learning_rollup_jobs WHERE user_id=%s',(user,)).fetchone()[0] is True
    run(client,learning_rollups.cycle)
    conn.execute('UPDATE review_items SET due_on=CURRENT_DATE WHERE user_id=%s',(user,))
    assert run(client,review_queue.queue,user)['due_count']==1
    mid='blocked-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,1200)",(mid,user,[ids[0]]))
    assert run(client,review_queue.queue,user)['due_count']==0
    assert client.post('/api/review-sessions',headers=h,json={'request_key':uuid4().hex}).status_code==422
