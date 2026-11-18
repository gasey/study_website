"""Limits at the real-role ledger boundary; event eligibility stays in writers."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
import psycopg
import pytest
from test_rewards import learner, attempt
from test_learning_habit import questions, due, review


def award(conn,user,pillar,points=2,xp=10,key=None,created=None,kind='study'):
    return conn.execute('''INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at)
      VALUES(%s,%s,%s,%s,%s,'Synthetic ledger boundary test',COALESCE(%s,now()))
      ON CONFLICT DO NOTHING RETURNING xp,points,rule_version''',
      (user,key or pillar+':'+uuid4().hex,kind,xp,points,created)).fetchone()


@pytest.mark.parametrize('pillar,cap',[('question',12),('review',4),('mock',3),('game',4),('daily',1),('quest',10)])
def test_each_pillar_clips_points_but_keeps_xp(client,learner,database,pillar,cap):
    user,_=learner;conn=database[1]
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        first=award(conn,user,pillar,cap,7)
        second=award(conn,user,pillar,2,7)
    assert first==(7,cap,'learning-v2') and second==(7,0,'learning-v2')
    assert client.get('/api/rewards/me').json()['point_budget']['earned']==cap


def test_parallel_global_cap_replay_and_contribution_exemption(client,learner,database):
    user,_=learner;name,conn=database
    def run(i):
        with psycopg.connect('dbname='+name) as c:
            c.execute('SET LOCAL ROLE mpsc')
            return award(c,user,'mastery',5,10,key='mastery:'+user+':'+str(i))
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(run,range(12)))
    assert sum(r[1] for r in rows)==25 and sum(r[0] for r in rows)==120
    before=conn.execute('SELECT xp,points,pillar_points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()
    assert award(conn,user,'mastery',5,10,key='mastery:'+user+':0') is None
    assert conn.execute('SELECT xp,points,pillar_points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()==before
    # Existing independently reviewed contributions/materials keep their separate
    # budget. This tests cap exemption, not the later contribution-amount rewrite.
    assert award(conn,user,'contribution-credit',5,20,kind='contribution')[:2]==(20,5)
    assert award(conn,user,'cms-published',5,20,kind='content')[:2]==(20,5)
    assert conn.execute('SELECT points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()[0]==25
    assert client.get('/api/rewards/me').json()['points']==35


def test_ist_reset_and_shared_partial_xp(client,learner,database):
    user,_=learner;conn=database[1]
    # Two seconds apart on opposite sides of midnight India time.
    for at in [datetime(2020,1,1,18,29,59,tzinfo=timezone.utc),datetime(2020,1,1,18,30,1,tzinfo=timezone.utc)]:
        assert award(conn,user,'question',12,299,created=at)[:2]==(299,12)
        assert award(conn,user,'review',2,20,created=at)[:2]==(1,2)
    assert conn.execute('SELECT count(*),sum(xp),sum(points) FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()==(2,600,28)


def test_cutover_counts_existing_receipts_without_rewriting_them(client,learner,database):
    user,_=learner;conn=database[1]
    # Model pre-migration receipts only in this disposable fixture.
    with conn.transaction():
        conn.execute('ALTER TABLE reward_ledger DISABLE TRIGGER enforce_learning_v2')
        conn.execute('ALTER TABLE reward_ledger DISABLE TRIGGER track_learning_v2')
        for p,pts in [('question',15),('quest',9)]:award(conn,user,p,pts,10)
        conn.execute('ALTER TABLE reward_ledger ENABLE TRIGGER enforce_learning_v2')
        conn.execute('ALTER TABLE reward_ledger ENABLE TRIGGER track_learning_v2')
    old=conn.execute('SELECT id,xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id',(user,)).fetchall()
    assert award(conn,user,'question',1,10)[:2]==(10,0)
    assert award(conn,user,'review',2,20)[:2]==(20,1)
    assert award(conn,user,'quest',5,50)[:2]==(50,0)
    assert conn.execute('SELECT id,xp,points,rule_version FROM reward_ledger WHERE user_id=%s ORDER BY id LIMIT 2',(user,)).fetchall()==old
    assert conn.execute('SELECT points FROM reward_daily_counters WHERE user_id=%s',(user,)).fetchone()[0]==25


def test_real_review_and_quest_receipts_report_clipped_amounts(client,actor,database):
    from test_learning_habit import learner as habit_learner
    user,h=habit_learner(database,actor);conn=database[1];_,ids=questions(database,10)
    # Keep this receipt-clipping case below a mastery threshold.
    conn.execute('UPDATE question_classifications SET topic_id=NULL WHERE question_id=ANY(%s)',(ids[-2:],))
    # Real practice awards hit Learn=10; an unrelated study source uses the rest.
    for q in ids:attempt(conn,user,q)
    award(conn,user,'mastery',14,0)
    due(conn,user,ids[:8]);done=review(client,h,conn,ids[:8],correct=8)
    assert done['summary']['reward']['points']==1 and done['summary']['reward']['xp']==20
    url='/api/rewards/daily-quests/warmup_circuit/claim'
    claimed=client.post(url,headers=h).json()
    assert claimed['points_awarded']==0 and claimed['xp_awarded']==20
    assert client.post(url,headers=h).json()['ledger_id']==claimed['ledger_id']
    assert conn.execute('SELECT points_awarded FROM daily_quest_claims WHERE ledger_id=%s',(claimed['ledger_id'],)).fetchone()[0]==0
    ledger=conn.execute('SELECT points FROM reward_ledger WHERE id=%s',(done['summary']['reward']['receipt_id'],)).fetchone()[0]
    assert ledger==1


def test_dark_catalog_gate_and_read_only_diagnostics(client,actor,database):
    conn=database[1];h=actor('owner')
    offers={r['id']:r for r in client.get('/api/admin/bank/rewards').json()}
    assert (offers['pro-week']['points'],offers['pro-week']['pro_days'],offers['pro-week']['enabled'])==(400,7,False)
    assert (offers['pro-month']['points'],offers['pro-month']['pro_days'],offers['pro-month']['enabled'])==(1500,30,False)
    before=conn.execute('SELECT count(*) FROM reward_daily_counters').fetchone()[0]
    gates=client.get('/api/admin/bank/reward-feature-gates').json()
    assert not gates['catalog_ready'] and not any(c['ready'] for c in gates['checks'] if c['key']!='economy_reconciliation')
    row=offers['pro-month']
    response=client.post('/api/admin/bank/rewards/pro-month',headers=h,json={'version':row['version'],'points':1500,'enabled':True,'reason':'Synthetic blocked launch attempt'})
    assert response.status_code==409
    assert not conn.execute("SELECT enabled FROM reward_catalog WHERE id='pro-month'").fetchone()[0]
    d=client.get('/api/admin/bank/reward-diagnostics').json()
    for key in ['daily_counter_mismatches','missing_daily_counters','v2_point_over_cap_days','v2_pillar_over_cap_days']:assert d[key]==0,(key,d)
    assert conn.execute('SELECT count(*) FROM reward_daily_counters').fetchone()[0]==before
    # Even a misconfigured enabled row cannot bypass the redemption launch gate.
    conn.execute("UPDATE reward_catalog SET enabled=true WHERE id='pro-month'")
    try:
        r=client.post('/api/rewards/redeem',headers={**h,'Idempotency-Key':uuid4().hex},json={'catalog_id':'pro-month','version':row['version']})
        assert r.status_code==409 and 'checklist' in r.text
    finally:conn.execute("UPDATE reward_catalog SET enabled=false WHERE id='pro-month'")
    actor('reviewer1');assert client.get('/api/admin/bank/reward-feature-gates').status_code==403


def test_diagnostics_detect_counter_drift(client,learner,actor,database):
    user,_=learner;conn=database[1];award(conn,user,'question',1)
    conn.execute('UPDATE reward_daily_counters SET points=points+1 WHERE user_id=%s',(user,))
    actor('owner');assert client.get('/api/admin/bank/reward-diagnostics').json()['daily_counter_mismatches']==1
    conn.execute('UPDATE reward_daily_counters SET points=points-1 WHERE user_id=%s',(user,))

